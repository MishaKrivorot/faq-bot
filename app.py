from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastembed import TextEmbedding
import json
from typing import List
import numpy as np

FAQ_PATH = "faqs_expanded.json"
TOP_K = 3

app = FastAPI(title="FAQ Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

class AnswerItem(BaseModel):
    question: str
    answer: str
    score: float

class ChatResponse(BaseModel):
    reply: str
    sources: List[AnswerItem] = []

# ---------- FastEmbed ----------
embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

faq_texts = []
faq_answers = []
faq_embeddings = None

def load_faq():
    global faq_texts, faq_answers, faq_embeddings
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        faqs = json.load(f)

    faq_texts = [item["question"] for item in faqs]
    faq_answers = [item["answer"] for item in faqs]

    faq_embeddings = list(embedder.embed(faq_texts))
    faq_embeddings = np.array(faq_embeddings, dtype=np.float32)

load_faq()

def find_best_answers(question: str, k=TOP_K):
    q_emb = np.array(list(embedder.embed([question]))[0], dtype=np.float32)

    scores = faq_embeddings @ q_emb
    idxs = np.argsort(scores)[::-1][:k]

    results = []
    for i in idxs:
        results.append({
            "question": faq_texts[i],
            "answer": faq_answers[i],
            "score": float(scores[i])
        })
    return results

GREETINGS = ["привіт", "доброго", "добрий", "hello", "hi"]

def simple_fallback(q:str):
    q = q.lower()
    for g in GREETINGS:
        if g in q:
            return "Привіт! Я бот-асистент. Що хочеш дізнатися про вступ чи навчання?"
    return None

@app.post("/chat", response_model=ChatResponse)
def chat(query: Query):
    text = query.question.strip()
    if not text:
        raise HTTPException(400, "Порожнє питання")

    g = simple_fallback(text)
    if g:
        return ChatResponse(reply=g)

    results = find_best_answers(text)

    reply = results[0]["answer"]

    sources = [AnswerItem(**r) for r in results]
    return ChatResponse(reply=reply, sources=sources)

@app.get("/health")
def health():
    return {"status": "ok"}
