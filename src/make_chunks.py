import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import ftfy
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def absolutize_urls(container, page_url):
    for img in container.select("img[src]"):
        src = img.get("src", "")
        if src and not src.startswith(("http://", "https://", "data:")):
            img["src"] = urljoin(page_url, src)

    for a in container.select("a[href]"):
        href = a.get("href", "")
        if href and not href.startswith(
            ("http://", "https://", "mailto:", "tel:", "#")
        ):
            a["href"] = urljoin(page_url, href)


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

    absolutize_urls(main, page_url)

    text_md = md(str(main), heading_style="ATX")
    return ftfy.fix_text(text_md)


header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
)

char_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,
    chunk_overlap=200,
    length_function=len,
)

IN_PATH = "data/raw/pages.jsonl"
OUT_PATH = "data/processed/chunks.jsonl"

with open(IN_PATH, "r", encoding="utf-8") as f_in, open(
    OUT_PATH, "w", encoding="utf-8"
) as f_out:
    for line in f_in:
        row = json.loads(line)

        url = row["url"]
        title = ftfy.fix_text(row.get("title", ""))

        text_md = html_to_md(row["html"], url)

        docs = header_splitter.split_text(text_md)

        for d in docs:
            if len(d.page_content) > 1800:
                sub_docs = char_splitter.split_documents([d])
                for sub_d in sub_docs:
                    meta = dict(sub_d.metadata or {})
                    meta["source"] = "html"
                    out = {
                        "url": url,
                        "title": title,
                        "metadata": meta,
                        "content": sub_d.page_content,
                    }
                    f_out.write(json.dumps(out, ensure_ascii=False) + "\n")
            else:
                meta = dict(d.metadata or {})
                meta["source"] = "html"
                out = {
                    "url": url,
                    "title": title,
                    "metadata": meta,
                    "content": d.page_content,
                }
                f_out.write(json.dumps(out, ensure_ascii=False) + "\n")
