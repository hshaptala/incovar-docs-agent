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

PERSIST_DIR = "./data/chroma"
COLLECTION = "incovar"
emb = OllamaEmbeddings(model="nomic-embed-text")
vs = Chroma(
    collection_name=COLLECTION, embedding_function=emb, persist_directory=PERSIST_DIR
)
retriever = vs.as_retriever(search_kwargs={"k": 8})
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

    docs = retriever.invoke(q.question)
    context = "\n\n---\n\n".join(d.page_content for d in docs)

    prompt = f"""Réponds UNIQUEMENT en utilisant le contexte fourni ci-dessous. Si la réponse n'est pas dans le contexte, dis "Je ne trouve pas cette information dans la documentation."

Question: {q.question}

Contexte:
{context}
"""

    resp = llm.invoke(prompt)
    sources = [d.metadata.get("url", "N/A") for d in docs[:3]]

    return Answer(answer=resp.content, sources=sources)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
