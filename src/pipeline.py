"""pipeline.py - ties retrieval and generation together. ask() = full response (API); stream_ask() = live UI."""
import time
from src import config
from src.retriever import Retriever
from src.generator import Generator, NOT_FOUND, _unique_sources


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()

    def _relevant(self, question):
        hits = self.retriever.search(question)
        return [h for h in hits if h["score"] >= config.MIN_RELEVANCE_SCORE]

    def ask(self, question: str) -> dict:
        start_time = time.perf_counter()
        question = (question or "").strip()

        if not question:
            return {
                "answer": "Please enter a question.",
                "sources": [],
                "confidence": 0.0,
                "response_time": 0.0,
            }

        relevant = self._relevant(question)
        if not relevant:
            return {
                "answer": NOT_FOUND,
                "sources": [],
                "confidence": 0.0,
                "response_time": round(time.perf_counter() - start_time, 2),
            }

        answer = self.generator.generate(question, relevant)
        if NOT_FOUND.lower() in answer.lower():
            return {
                "answer": NOT_FOUND,
                "sources": [],
                "confidence": round(relevant[0]["score"], 2),
                "response_time": round(time.perf_counter() - start_time, 2),
            }

        elapsed = round(time.perf_counter() - start_time, 2)
        return {
            "answer": answer,
            "sources": _unique_sources(relevant),
            "confidence": round(relevant[0]["score"], 2),
            "response_time": elapsed,
        }

    def stream_ask(self, question: str):
        question = (question or "").strip()
        if not question:
            yield "Please enter a question."
            return

        relevant = self._relevant(question)
        if not relevant:
            yield NOT_FOUND
            return

        yield from self.generator.stream(question, relevant)