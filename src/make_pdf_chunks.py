import argparse
import json
import os
import re
from collections import Counter

import fitz  # PyMuPDF
import ftfy
from langchain_text_splitters import RecursiveCharacterTextSplitter


HEADING_NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*[.)-]?\s+\S")


def _abs_file_url(path: str) -> str:
    abs_path = os.path.abspath(path)
    # Keep it simple for citations: file:///C:/.../file.pdf
    return "file:///" + abs_path.replace("\\", "/")


def _iter_pdf_lines(doc: fitz.Document, page_index: int):
    """Yield (text, max_font_size) for each logical line on the page."""
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
                text = (span.get("text") or "")
                if text:
                    parts.append(text)
                try:
                    max_size = max(max_size, float(span.get("size") or 0.0))
                except Exception:
                    pass

            joined = "".join(parts).strip()
            if joined:
                yield joined, max_size


def _detect_body_font_size(doc: fitz.Document) -> float:
    sizes = []
    for i in range(doc.page_count):
        for text, size in _iter_pdf_lines(doc, i):
            if not text:
                continue
            # Ignore giant cover/title fonts
            if size >= 25:
                continue
            # Ignore very short lines (page numbers, etc.)
            if len(text.strip()) <= 3 and text.strip().isdigit():
                continue
            sizes.append(round(float(size), 1))

    if not sizes:
        return 12.0

    return Counter(sizes).most_common(1)[0][0]


def _is_heading(line_text: str, line_size: float, *, threshold: float) -> tuple[bool, str | None]:
    text = line_text.strip()
    if not text:
        return False, None

    # Skip lines that are only page numbers
    if text.isdigit() and len(text) <= 3:
        return False, None

    m = HEADING_NUMBER_RE.match(text)
    if m:
        return True, m.group(1)

    # Font-size based heading detection (works well for this PDF: body ~11, headings ~16+)
    if line_size >= threshold and len(text) <= 140:
        return True, None

    return False, None


def extract_sections(pdf_path: str):
    doc = fitz.open(pdf_path)

    body_size = _detect_body_font_size(doc)
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

        for line_text, line_size in _iter_pdf_lines(doc, i):
            line_text = ftfy.fix_text(line_text)
            is_h, number = _is_heading(line_text, line_size, threshold=heading_threshold)

            if is_h:
                # Close previous section if it has meaningful content
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

            # Normal line
            current["text"].append(line_text)

        current["text"].append("")  # page break marker

    if "".join(current["text"]).strip():
        current["page_end"] = doc.page_count
        sections.append(current)

    return sections


def main():
    parser = argparse.ArgumentParser(description="Extract and chunk a PDF guide into JSONL for indexing.")
    parser.add_argument("--pdf", default="data/raw/guide_incovar_salarie_fcba.pdf", help="Path to PDF")
    parser.add_argument("--out", default="data/processed/pdf_chunks.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    pdf_path = args.pdf
    if not os.path.exists(pdf_path):
        raise SystemExit(f"PDF not found: {pdf_path}")

    pdf_name = os.path.basename(pdf_path)
    pdf_url = _abs_file_url(pdf_path)

    sections = extract_sections(pdf_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        length_function=len,
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    written = 0
    with open(args.out, "w", encoding="utf-8") as f_out:
        for section_index, sec in enumerate(sections):
            section_text = "\n".join([t for t in sec["text"] if t is not None]).strip()
            if not section_text:
                continue

            chunks = splitter.split_text(section_text)
            for chunk_index, chunk in enumerate(chunks):
                meta = {
                    "source": "pdf",
                    "pdf_name": pdf_name,
                    "page_start": sec["page_start"],
                    "page_end": sec["page_end"],
                    "section_title": sec["section_title"],
                    "section_number": sec.get("section_number"),
                    "section_index": section_index,
                    "chunk_index": chunk_index,
                }

                row = {
                    "url": pdf_url,
                    "title": pdf_name,
                    "metadata": meta,
                    "content": chunk,
                }
                f_out.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1

    print(f"Wrote {written} PDF chunks to {args.out}")


if __name__ == "__main__":
    main()
