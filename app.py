from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import util
import json
import numpy as np
import uvicorn
from typing import List

FAQ_PATH = "faqs.json"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-albert-small-v2"
TOP_K = 3

app = FastAPI(title="FAQ Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy load
model = None
faq_texts = None
faq_answers = None
faq_embeddings = None


def load_model_and_data():
    global model, faq_texts, faq_answers, faq_embeddings

    if model is None:
        print("Loading model...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)

    if faq_texts is None:
        print("Loading FAQ...")
        with open(FAQ_PATH, "r", encoding="utf-8") as f:
            faqs = json.load(f)

        faq_texts = [item["question"] for item in faqs]
        faq_answers = [item["answer"] for item in faqs]

        print("Encoding embeddings...")
        emb = model.encode(faq_texts, convert_to_tensor=False, batch_size=4)
        faq_embeddings = np.array(emb)

    return model, faq_texts, faq_answers, faq_embeddings


class Query(BaseModel):
    question: str


class AnswerItem(BaseModel):
    question: str
    answer: str
    score: float


class ChatResponse(BaseModel):
    reply: str
    sources: List[AnswerItem] = []


GREETINGS = ["привіт", "доброго", "добрий", "hello", "hi", "здрастуйте"]


def simple_fallback(q: str):
    ql = q.lower()
    for g in GREETINGS:
        if g in ql:
            return "Привіт! Я бот-помічник. Запитайте мене щось про вступ або навчання!"
    return None


def find_best_answers(question: str, top_k: int = TOP_K):
    model, faq_texts, faq_answers, faq_embeddings = load_model_and_data()

    query_emb = model.encode(question, convert_to_tensor=False)
    hits = util.semantic_search(query_emb, faq_embeddings, top_k=top_k)[0]

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


@app.post("/chat", response_model=ChatResponse)
@app.post("/chat/", response_model=ChatResponse)
def chat(query: Query):
    q = query.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Empty question")

    fb = simple_fallback(q)
    if fb:
        return ChatResponse(reply=fb, sources=[])

    results = find_best_answers(q)
    top = results[0]

    if top["score"] >= 0.45:
        reply = top["answer"]
    else:
        reply = (
            "Я не повністю впевнений, але ось можливі відповіді:\n\n"
            f"1) {results[0]['answer']}\n"
            f"2) {results[1]['answer'] if len(results) > 1 else ''}"
        )

    sources = [AnswerItem(**r) for r in results]
    return ChatResponse(reply=reply, sources=sources)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
