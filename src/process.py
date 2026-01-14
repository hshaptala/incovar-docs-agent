import os
import re
from typing import Iterator
from urllib.parse import urljoin
from collections import Counter
import json
import fitz
import ftfy
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from .config import settings


def chunk_text(text, chunk_size=None, chunk_overlap=None, use_headers=False):
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    if use_headers:
        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        )
        docs = header_splitter.split_text(text)
        
        char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        
        result = []
        for d in docs:
            if len(d.page_content) > chunk_size + 300:
                result.extend(char_splitter.split_documents([d]))
            else:
                result.append(d)
        return result
    else:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        return splitter.split_text(text)


class HTMLProcessor:
    @staticmethod
    def absolutize_urls(container, page_url):
        for img in container.select("img[src]"):
            src = img.get("src", "")
            if src and not src.startswith(("http://", "https://", "data:")):
                img["src"] = urljoin(page_url, src)

        for a in container.select("a[href]"):
            href = a.get("href", "")
            if href and not href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                a["href"] = urljoin(page_url, href)

    @staticmethod
    def html_to_md(html, page_url):
        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        topic = soup.find("div", id="topic-content")
        if not topic:
            topic = soup.body or soup

        footer = topic.find("div", id="topic_footer")
        if footer:
            footer.decompose()

        main = topic.select_one("div.main-content") or topic

        HTMLProcessor.absolutize_urls(main, page_url)

        text_md = md(str(main), heading_style="ATX")
        return ftfy.fix_text(text_md)

    def process(self, source_path: str) -> Iterator[Document]:
        with open(source_path, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                url = row["url"]
                title = ftfy.fix_text(row.get("title", ""))
                
                text_md = self.html_to_md(row["html"], url)
                docs = chunk_text(text_md, use_headers=True)
                
                for d in docs:
                    meta = dict(d.metadata or {})
                    meta["source"] = "html"
                    meta["url"] = url
                    meta["title"] = title
                    
                    yield Document(page_content=d.page_content, metadata=meta)


HEADING_NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*[.)-]?\s+\S")


class PDFProcessor:
    @staticmethod
    def _abs_file_url(path: str) -> str:
        abs_path = os.path.abspath(path)
        return "file:///" + abs_path.replace("\\", "/")

    @staticmethod
    def _iter_pdf_lines(doc: fitz.Document, page_index: int):
        page = doc.load_page(page_index)
        d = page.get_text("dict")
        for block in d.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue

                parts = []
                max_size = 0.0
                for span in spans:
                    text = span.get("text") or ""
                    if text:
                        parts.append(text)
                    try:
                        max_size = max(max_size, float(span.get("size") or 0.0))
                    except Exception:
                        pass

                joined = "".join(parts).strip()
                if joined:
                    yield joined, max_size

    @staticmethod
    def _detect_body_font_size(doc: fitz.Document) -> float:
        sizes = []
        for i in range(doc.page_count):
            for text, size in PDFProcessor._iter_pdf_lines(doc, i):
                if not text:
                    continue
                if size >= 25:
                    continue
                if len(text.strip()) <= 3 and text.strip().isdigit():
                    continue
                sizes.append(round(float(size), 1))

        if not sizes:
            return 12.0

        return Counter(sizes).most_common(1)[0][0]

    @staticmethod
    def _is_heading(line_text: str, line_size: float, *, threshold: float):
        text = line_text.strip()
        if not text:
            return False, None

        if text.isdigit() and len(text) <= 3:
            return False, None

        m = HEADING_NUMBER_RE.match(text)
        if m:
            return True, m.group(1)

        if line_size >= threshold and len(text) <= 140:
            return True, None

        return False, None

    @staticmethod
    def extract_sections(pdf_path: str):
        doc = fitz.open(pdf_path)

        body_size = PDFProcessor._detect_body_font_size(doc)
        heading_threshold = max(body_size + 4.0, 15.0)

        sections = []
        current = {
            "section_title": "Front matter",
            "section_number": None,
            "page_start": 1,
            "page_end": 1,
            "text": [],
        }

        for i in range(doc.page_count):
            page_num = i + 1

            for line_text, line_size in PDFProcessor._iter_pdf_lines(doc, i):
                line_text = ftfy.fix_text(line_text)
                is_h, number = PDFProcessor._is_heading(
                    line_text, line_size, threshold=heading_threshold
                )

                if is_h:
                    if "".join(current["text"]).strip():
                        current["page_end"] = page_num
                        sections.append(current)

                    current = {
                        "section_title": line_text.strip(),
                        "section_number": number,
                        "page_start": page_num,
                        "page_end": page_num,
                        "text": [line_text.strip()],
                    }
                    continue

                current["text"].append(line_text)

            current["text"].append("")

        if "".join(current["text"]).strip():
            current["page_end"] = doc.page_count
            sections.append(current)

        return sections

    def process(self, source_path: str) -> Iterator[Document]:
        pdf_name = os.path.basename(source_path)
        pdf_url = self._abs_file_url(source_path)

        sections = self.extract_sections(source_path)

        for section_index, sec in enumerate(sections):
            section_text = "\n".join([t for t in sec["text"] if t is not None]).strip()
            if not section_text:
                continue

            chunks = chunk_text(section_text, use_headers=False)
            for chunk_index, chunk in enumerate(chunks):
                meta = {
                    "source": "pdf",
                    "pdf_name": pdf_name,
                    "url": pdf_url,
                    "title": pdf_name,
                    "page_start": sec["page_start"],
                    "page_end": sec["page_end"],
                    "section_title": sec["section_title"],
                    "section_number": sec.get("section_number"),
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                }

                yield Document(page_content=chunk, metadata=meta)
