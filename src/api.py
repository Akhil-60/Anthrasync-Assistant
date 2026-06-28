"""
api.py  -  the FastAPI interface (assignment's "API" requirement).

Exposes POST /ask matching the assignment's contract:

    Request:  {"question": "What is the refund policy?"}
    Response: {"answer": "...", "sources": [{"document": "...", "page": 5}], "confidence": 0.91}

Run with:
    uvicorn src.api:app --reload
Then open http://127.0.0.1:8000/docs for an interactive test page.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.pipeline import RAGPipeline

app = FastAPI(title="Anthrasync Enterprise Knowledge Assistant API")

pipeline = RAGPipeline()


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    document: str
    page: int


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    confidence: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    return pipeline.ask(request.question)
