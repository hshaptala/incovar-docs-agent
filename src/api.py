from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq

from .config import settings
from .retrieve import Retriever

load_dotenv()


class Question(BaseModel):
    question: str


class Answer(BaseModel):
    answer: str
    sources: list[str] = []


app = FastAPI(title="Incovar Docs Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()
retriever = Retriever()
llm = None


def get_llm():
    global llm
    if llm is None:
        llm = ChatGroq(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE
        )
    return llm


@router.post("/ask", response_model=Answer)
async def ask_question(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    docs = retriever.retrieve(q.question)
    context = "\n\n---\n\n".join(d.page_content for d in docs)

    prompt = f"""Réponds UNIQUEMENT en utilisant le contexte fourni ci-dessous. Si la réponse n'est pas dans le contexte, dis "Je ne trouve pas cette information dans la documentation."

Question: {q.question}

Contexte:
{context}
"""

    resp = get_llm().invoke(prompt)
    sources = retriever.get_sources(docs)

    return Answer(answer=resp.content, sources=sources)


@router.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(router)
