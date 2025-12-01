from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import util
import json
import uvicorn
from typing import List

# ----------------------------
# НАЛАШТУВАННЯ
# ----------------------------
FAQ_PATH = "faqs.json"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L3-v2"  # легша модель
TOP_K = 3

# ----------------------------
# FASTAPI APP
# ----------------------------
app = FastAPI(title="FAQ Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=".*",
)

# ----------------------------
# Pydantic Models
# ----------------------------
class Query(BaseModel):
    question: str

class AnswerItem(BaseModel):
    question: str
    answer: str
    score: float

class ChatResponse(BaseModel):
    reply: str
    sources: List[AnswerItem] = []

# ----------------------------
# ЛІНИВЕ ЗАВАНТАЖЕННЯ МОДЕЛІ
# ----------------------------
model = None
faq_texts = None
faq_answers = None
faq_embeddings = None

def load_model_and_data():
    """Lazy loading моделі + FAQ"""
    global model, faq_texts, faq_answers, faq_embeddings

    if model is None:
        print("Loading model (lazy)...")
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)

    if faq_texts is None:
        print("Loading FAQs...")
        with open(FAQ_PATH, "r", encoding="utf-8") as f:
            faqs = json.load(f)

        faq_texts = [item["question"] for item in faqs]
        faq_answers = [item["answer"] for item in faqs]

        print("Encoding FAQ embeddings...")
        faq_embeddings = model.encode(faq_texts, convert_to_tensor=True)

    return model, faq_texts, faq_answers, faq_embeddings

# ----------------------------
# ПОШУК
# ----------------------------
def find_best_answers(question: str, top_k: int = TOP_K):
    model, faq_texts, faq_answers, faq_embeddings = load_model_and_data()

    query_emb = model.encode(question, convert_to_tensor=True)
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

# ----------------------------
# РЕАКЦІЯ НА ПРИВІТАННЯ
# ----------------------------
GREETINGS = ["привіт", "доброго", "добрий", "hello", "hi", "здрастуйте"]

def simple_fallback(q: str):
    ql = q.lower()
    for g in GREETINGS:
        if g in ql:
            return "Привіт! Я бот-помічник. Запитайте мене щось про вступ або навчання!"
    return None

# ----------------------------
# API ENDPOINT
# ----------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(query: Query):
    q = query.question.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Порожнє питання")

    # Привітання
    fb = simple_fallback(q)
    if fb:
        return ChatResponse(reply=fb, sources=[])

    # Основний пошук
    results = find_best_answers(q, top_k=TOP_K)
    top = results[0]

    if top["score"] >= 0.45:
        reply = top["answer"]
    else:
        reply = (
            "Вибач, я не зовсім впевнений. Але ось можливі варіанти:\n\n"
            f"1) {results[0]['answer']}\n"
            f"2) {results[1]['answer'] if len(results) > 1 else ''}"
        )

    sources = [AnswerItem(**r) for r in results]

    return ChatResponse(reply=reply, sources=sources)

# ----------------------------
# Health Check
# ----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ----------------------------
# Local Run
# ----------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

