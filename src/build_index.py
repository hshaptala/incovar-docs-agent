import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

CHUNKS_PATH = "data/processed/chunks.jsonl"
PERSIST_DIR = "data/chroma"
COLLECTION = "incovar"


def load_docs():
    docs = []
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            meta = {"url": row["url"], "title": row.get("title", "")}
            meta.update(row.get("metadata") or {})
            docs.append(Document(page_content=row["content"], metadata=meta))
    return docs


if __name__ == "__main__":
    docs = load_docs()
    emb = OllamaEmbeddings(model="nomic-embed-text")

    Chroma.from_documents(
        documents=docs,
        embedding=emb,
        collection_name=COLLECTION,
        persist_directory=PERSIST_DIR,
    )

    print(f"Indexed {len(docs)} chunks into {PERSIST_DIR}")
