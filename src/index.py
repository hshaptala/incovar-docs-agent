import shutil
from typing import Iterator
from functools import lru_cache
from langchain_core.documents import Document
from langchain_chroma import Chroma

from .config import settings, get_embeddings


@lru_cache(maxsize=10)
def get_vector_store(collection_name: str):
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(settings.CHROMA_DIR),
    )


def build_index(
    documents: Iterator[Document],
    collection_name: str,
    reset: bool = False,
):
    if reset and settings.CHROMA_DIR.exists():
        shutil.rmtree(settings.CHROMA_DIR)
        settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    docs_list = list(documents)
    
    if not docs_list:
        print(f"No documents to index for collection '{collection_name}'")
        return

    Chroma.from_documents(
        documents=docs_list,
        embedding=get_embeddings(),
        collection_name=collection_name,
        persist_directory=str(settings.CHROMA_DIR),
    )

    print(f"Indexed {len(docs_list)} chunks into collection '{collection_name}'")
