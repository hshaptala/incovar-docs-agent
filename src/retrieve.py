from typing import List
from langchain_core.documents import Document

from .config import settings
from .index import get_vector_store


class Retriever:
    def __init__(self):
        self.pdf_store = None
        self.html_store = None

    def _ensure_stores(self):
        if self.pdf_store is None:
            self.pdf_store = get_vector_store(settings.PDF_COLLECTION)
        if self.html_store is None:
            self.html_store = get_vector_store(settings.HTML_COLLECTION)

    def retrieve(self, query: str) -> List[Document]:
        self._ensure_stores()

        pdf_docs = self.pdf_store.similarity_search(query, k=settings.PDF_TOP_K)
        
        if pdf_docs:
            html_docs = self.html_store.similarity_search(query, k=settings.HTML_TOP_K)
            return pdf_docs + html_docs
        else:
            return self.html_store.similarity_search(query, k=settings.PDF_TOP_K)

    def get_sources(self, documents: List[Document]) -> List[str]:
        sources = []
        for d in documents:
            url = d.metadata.get("url", "N/A")
            if d.metadata.get("source") == "pdf" and d.metadata.get("page_start"):
                url = f"{url}#page={d.metadata.get('page_start')}"
            if url not in sources:
                sources.append(url)
            if len(sources) >= settings.MAX_SOURCES:
                break
        return sources
