import argparse
import json

from .config import settings
from .crawl import crawl_docs
from .process import HTMLProcessor, PDFProcessor
from .index import build_index


def save_chunks(documents, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    written = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for doc in documents:
            row = {
                "url": doc.metadata.get("url", ""),
                "title": doc.metadata.get("title", ""),
                "metadata": doc.metadata,
                "content": doc.page_content,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
    
    print(f"Saved {written} chunks to {output_path}")


def cmd_crawl():
    out_path = settings.RAW_DIR / "pages.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for url, html, title in crawl_docs(
            settings.CRAWL_START_URL,
            max_pages=settings.CRAWL_MAX_PAGES
        ):
            f.write(
                json.dumps(
                    {"url": url, "title": title, "html": html},
                    ensure_ascii=False
                ) + "\n"
            )
            print(url)

    print(f"\nCrawled pages saved to: {out_path}")


def cmd_index(args):
    html_input = settings.RAW_DIR / "pages.jsonl"
    html_chunks = settings.PROCESSED_DIR / "chunks.jsonl"
    
    pdf_input = settings.RAW_DIR / settings.DEFAULT_PDF_NAME
    pdf_chunks = settings.PROCESSED_DIR / "pdf_chunks.jsonl"

    if not args.pdf_only and html_input.exists():
        print("Processing HTML documents...")
        processor = HTMLProcessor()
        docs = list(processor.process(str(html_input)))
        
        if not args.skip_chunks:
            save_chunks(docs, html_chunks)
        
        build_index(
            iter(docs),
            settings.HTML_COLLECTION,
            reset=args.reset
        )
    elif not args.pdf_only:
        print(f"HTML input not found: {html_input}")

    if not args.html_only and pdf_input.exists():
        print("Processing PDF documents...")
        processor = PDFProcessor()
        docs = list(processor.process(str(pdf_input)))
        
        if not args.skip_chunks:
            save_chunks(docs, pdf_chunks)
        
        build_index(
            iter(docs),
            settings.PDF_COLLECTION,
            reset=args.reset and args.pdf_only
        )
    elif not args.html_only:
        print(f"PDF input not found: {pdf_input}")


def main():
    parser = argparse.ArgumentParser(description="Incovar Docs Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("crawl", help="Crawl documentation pages")

    index_parser = subparsers.add_parser("index", help="Build vector indexes")
    index_parser.add_argument("--reset", action="store_true", help="Delete existing indexes")
    index_parser.add_argument("--html-only", action="store_true", help="Only process HTML")
    index_parser.add_argument("--pdf-only", action="store_true", help="Only process PDF")
    index_parser.add_argument("--skip-chunks", action="store_true", help="Skip saving chunks to JSONL")

    args = parser.parse_args()

    if args.command == "crawl":
        cmd_crawl()
    elif args.command == "index":
        cmd_index(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
