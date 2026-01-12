from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

PERSIST_DIR = "./data/chroma"
COLLECTION = "incovar"

emb = OllamaEmbeddings(model="nomic-embed-text")
vs = Chroma(
    collection_name=COLLECTION, embedding_function=emb, persist_directory=PERSIST_DIR
)

retriever = vs.as_retriever(search_kwargs={"k": 8})

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

q = input("Question: ")
docs = retriever.invoke(q)

context = "\n\n---\n\n".join(d.page_content for d in docs)
prompt = f"""Réponds UNIQUEMENT en utilisant le contexte fourni ci-dessous. Si la réponse n'est pas dans le contexte, dis "Je ne trouve pas cette information dans la documentation."

Question: {q}

Contexte:
{context}
"""

print("\n💬 Answer:\n")
resp = llm.invoke(prompt)
print(resp.content)

print("\nSources:")
for d in docs:
    print("-", d.metadata.get("url"))

