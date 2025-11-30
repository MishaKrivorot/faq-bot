from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer, util
import json
import numpy as np
import uvicorn
from typing import List

# ---------- Config ----------
FAQ_PATH = "faqs.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3  # кількість схожих FAQ, які повертаємо

# ---------- FastAPI app ----------
app = FastAPI(title="FAQ Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # в продакшні вкажи свій фронтенд домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class Query(BaseModel):
    question: str

class AnswerItem(BaseModel):
    question: str
    answer: str
    score: float

class ChatResponse(BaseModel):
    reply: str
    sources: List[AnswerItem] = []

# ---------- Load model and faqs ----------
print("Loading embedding model...")
model = SentenceTransformer(EMBEDDING_MODEL)

print("Loading FAQs...")
with open(FAQ_PATH, "r", encoding="utf-8") as f:
    faqs = json.load(f)

faq_texts = [item["question"] for item in faqs]
faq_answers = [item["answer"] for item in faqs]

print("Computing FAQ embeddings...")
faq_embeddings = model.encode(faq_texts, convert_to_tensor=True)

# ---------- Helper: semantic search ----------
def find_best_answers(question: str, top_k: int = TOP_K):
    query_emb = model.encode(question, convert_to_tensor=True)
    hits = util.semantic_search(query_emb, faq_embeddings, top_k=top_k)[0]  # list of {corpus_id, score}
    results = []
    for h in hits:
        idx = h["corpus_id"]
        score = float(h["score"])
        results.append({
            "question": faq_texts[idx],
            "answer": faq_answers[idx],
            "score": score
        })
    return results

# ---------- Simple rule-based fallback for greetings / short queries ----------
GREETINGS = ["привіт", "доброго дня", "добрий", "здрастуйте", "hello", "hi"]
def simple_fallback(q: str):
    ql = q.lower()
    for g in GREETINGS:
        if g in ql:
            return "Привіт! Я — бот довідник. Поставте своє питання щодо вступу або навчання, і я постараюсь допомогти."
    return None

# ---------- Endpoint ----------
@app.post("/chat", response_model=ChatResponse)
def chat(query: Query):
    q = query.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty question")

    # simple fallback first
    s = simple_fallback(q)
    if s:
        return ChatResponse(reply=s, sources=[])

    # semantic search
    results = find_best_answers(q, top_k=TOP_K)

    # decide if top result is confident enough
    top = results[0]
    confidence_threshold = 0.45  # регулюй: 0-1 (моделі all-MiniLM дають scores близько 0.3-0.7)
    if top["score"] >= confidence_threshold:
        reply = top["answer"]
    else:
        # якщо недостатньо впевнено — сформувати комбіновану відповідь
        reply = (
            "Вибач, я не зовсім впевнений. Можливо, допоможе одна з відповідей нижче.\n\n"
            f"1) {results[0]['answer']}\n"
            f"2) {results[1]['answer'] if len(results) > 1 else ''}\n"
        )

    sources = [AnswerItem(question=r["question"], answer=r["answer"], score=r["score"]) for r in results]
    return ChatResponse(reply=reply, sources=sources)

# ---------- health ----------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- Run ----------
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
