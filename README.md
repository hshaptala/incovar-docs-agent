# Incovar Docs Agent

RAG (Retrieval-Augmented Generation) system for Incovar+ French documentation.

## Stack

- **Embeddings**: Ollama nomic-embed-text (local, free)
- **LLM**: Groq llama-3.3-70b-versatile (cloud, free tier)
- **Vector DB**: ChromaDB
- **Processing**: LangChain + BeautifulSoup + Markdownify

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed with `nomic-embed-text`:

  ```bash
  ollama pull nomic-embed-text
  ```

- Groq API key (free at [console.groq.com](https://console.groq.com/keys))

## Setup

1. Clone the repository

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure Groq API:

   ```bash
   cp .env.example .env
   # Edit .env and add: GROQ_API_KEY=your_key_here
   ```

## Usage

### Crawl Documentation

```bash
python -m src.cli crawl
```

### Build Indexes

```bash
python -m src.cli index              # Build indexes for both HTML & PDF
python -m src.cli index --reset      # Full rebuild (deletes existing index)
python -m src.cli index --html-only  # Only HTML docs
python -m src.cli index --pdf-only   # Only PDF guide
```

### Start API Server

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Project Structure

```text
src/
  config.py      - Configuration & settings
  crawl.py       - Web crawler
  process.py     - HTML & PDF processing
  index.py       - Vector database operations
  retrieve.py    - Document retrieval
  api.py         - FastAPI application
  cli.py         - CLI commands
data/
  raw/           - Source documents (HTML, PDF)
  processed/     - Processed chunks (JSONL)
  chroma/        - Vector database
```
