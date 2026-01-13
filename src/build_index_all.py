import argparse
import json
import os
import shutil
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


HTML_CHUNKS_PATH = "data/processed/chunks.jsonl"
PDF_CHUNKS_PATH = "data/processed/pdf_chunks.jsonl"
PERSIST_DIR = "data/chroma"

HTML_COLLECTION = "incovar_html"
PDF_COLLECTION = "incovar_pdf"


def load_docs(jsonl_path: str):
    docs = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            meta = {"url": row.get("url", ""), "title": row.get("title", "")}
            meta.update(row.get("metadata") or {})
            docs.append(Document(page_content=row["content"], metadata=meta))
    return docs


def main():
    parser = argparse.ArgumentParser(description="Build Chroma indexes for HTML docs and PDF guide (PDF-first retrieval).")
    parser.add_argument("--reset", action="store_true", help="Delete data/chroma before indexing (full rebuild).")
    args = parser.parse_args()

    if args.reset and os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)

    emb = OllamaEmbeddings(model="nomic-embed-text")

    if os.path.exists(HTML_CHUNKS_PATH):
        html_docs = load_docs(HTML_CHUNKS_PATH)
        Chroma.from_documents(
            documents=html_docs,
            embedding=emb,
            collection_name=HTML_COLLECTION,
            persist_directory=PERSIST_DIR,
        )
        print(f"Indexed HTML: {len(html_docs)} chunks into collection '{HTML_COLLECTION}'")
    else:
        print(f"Missing HTML chunks file: {HTML_CHUNKS_PATH}")

    if os.path.exists(PDF_CHUNKS_PATH):
        pdf_docs = load_docs(PDF_CHUNKS_PATH)
        Chroma.from_documents(
            documents=pdf_docs,
            embedding=emb,
            collection_name=PDF_COLLECTION,
            persist_directory=PERSIST_DIR,
        )
        print(f"Indexed PDF: {len(pdf_docs)} chunks into collection '{PDF_COLLECTION}'")
    else:
        print(f"Missing PDF chunks file: {PDF_CHUNKS_PATH}")


if __name__ == "__main__":
    main()
