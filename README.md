# Incovar Docs Agent

RAG (Retrieval-Augmented Generation) system for Incovar+ French documentation.

## Stack

- **Embeddings**: Ollama nomic-embed-text (local, free)
- **LLM**: Groq llama-3.1-8b-instant (cloud, free tier)
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

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Groq API:
   ```bash
   cp .env.example .env
   # Edit .env and add: GROQ_API_KEY=your_key_here
   ```

## Usage

### Build Index (one-time or after doc updates)

```bash
python src/make_chunks.py      # Process HTML to chunks
python src/build_index.py      # Create vector index
```

### Ask Questions

```bash
python src/ask_groq.py
```

## Project Structure

```
src/
  crawl.py          - Web crawler (for doc updates)
  make_chunks.py    - HTML→Markdown→chunks (1500 chars, 200 overlap)
  build_index.py    - Build ChromaDB vector index
  ask_groq.py       - Interactive Q&A with Groq
data/
  raw/              - Crawled HTML pages
  processed/        - Processed chunks
  chroma/           - Vector database
test_questions.txt  - Test questions
```

## How It Works

1. **Crawl**: Fetch HelpNDoc documentation pages
2. **Chunk**: Extract `<div class="main-content">`, convert to Markdown, split by headers
3. **Index**: Embed chunks with Ollama, store in ChromaDB
4. **Query**: Retrieve top 8 relevant chunks, send to Groq with French prompt
