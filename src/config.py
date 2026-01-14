from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from langchain_ollama import OllamaEmbeddings


class Settings(BaseSettings):
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    RAW_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    CHROMA_DIR: Path = DATA_DIR / "chroma"
    
    HTML_COLLECTION: str = "incovar_html"
    PDF_COLLECTION: str = "incovar_pdf"
    
    EMBEDDING_MODEL: str = "nomic-embed-text"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    
    PDF_TOP_K: int = 8
    HTML_TOP_K: int = 6
    MAX_SOURCES: int = 5
    
    GROQ_API_KEY: str = ""
    
    CRAWL_START_URL: str = "https://gta-fcba.incovar.com/Incotec/Incovar/Help/fr-FR/PORTAIL/topics/LOGIN.html"
    CRAWL_MAX_PAGES: int = 200
    
    DEFAULT_PDF_NAME: str = "guide_incovar_salarie_fcba.pdf"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


@lru_cache()
def get_embeddings():
    return OllamaEmbeddings(model=settings.EMBEDDING_MODEL)
