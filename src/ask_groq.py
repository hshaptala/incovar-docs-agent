from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

PERSIST_DIR = "data/chroma"
PDF_COLLECTION = "incovar_pdf"
HTML_COLLECTION = "incovar_html"

emb = OllamaEmbeddings(model="nomic-embed-text")

vs_pdf = Chroma(
    collection_name=PDF_COLLECTION, embedding_function=emb, persist_directory=PERSIST_DIR
)
vs_html = Chroma(
    collection_name=HTML_COLLECTION, embedding_function=emb, persist_directory=PERSIST_DIR
)
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str] = []


@app.post("/ask", response_model=Answer)
async def ask_question(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Prefer the company PDF guide first; if nothing comes back, fall back to HTML docs.
    pdf_docs = vs_pdf.similarity_search(q.question, k=8)
    if pdf_docs:
        html_docs = vs_html.similarity_search(q.question, k=6)
        docs = pdf_docs + html_docs
    else:
        docs = vs_html.similarity_search(q.question, k=8)

    context = "\n\n---\n\n".join(d.page_content for d in docs)

    prompt = f"""Réponds UNIQUEMENT en utilisant le contexte fourni ci-dessous. Si la réponse n'est pas dans le contexte, dis "Je ne trouve pas cette information dans la documentation."

Question: {q.question}

Contexte:
{context}
"""

    resp = llm.invoke(prompt)
    sources = []
    for d in docs:
        url = d.metadata.get("url", "N/A")
        if d.metadata.get("source") == "pdf" and d.metadata.get("page_start"):
            url = f"{url}#page={d.metadata.get('page_start')}"
        if url not in sources:
            sources.append(url)
        if len(sources) >= 5:
            break

    return Answer(answer=resp.content, sources=sources)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
