"""
retriever.py  -  the "Finder" of the system.

Given a user question, it:
  1. turns the question into a vector with the SAME embedding model used at ingest,
  2. asks Chroma for the most similar chunks (semantic search),
  3. returns them as clean records (text + document + page + score),
  4. offers a relevance check so the caller can refuse to answer when nothing
     in the documents is a good match (this is a key hallucination guard).

The embedding model and the Chroma collection are loaded ONCE when the Retriever
is created, then reused for every question -- loading them per query would be slow.
"""

from src import config


def _format_hits(result: dict):
    """Flatten Chroma's nested query result into a simple list of dicts.

    Chroma returns each field wrapped in an extra list (one per query); we only
    send one query, so we read index [0]. Cosine distance is converted to a
    similarity score (higher = more relevant) for easier reading.
    """
    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    hits = []
    for text, meta, distance in zip(documents, metadatas, distances):
        hits.append({
            "text": text,
            "document": meta.get("document", "Unknown"),
            "page": meta.get("page", "-"),
            "score": round(1 - distance, 3),
            "chunk_id": meta.get("chunk_id", ""),
        })
    return hits


class Retriever:
    def __init__(self):
        import chromadb
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        client = chromadb.PersistentClient(path=str(config.VECTOR_DIR))
        try:
            self.collection = client.get_collection(config.COLLECTION_NAME)
        except Exception:
            raise RuntimeError(
                f"Collection '{config.COLLECTION_NAME}' not found. "
                "Run `python -m src.ingest` first to build the index."
            )

    def search(self, question: str, top_k: int = None):
        """Return the top_k most similar chunks for `question`, best first."""
        if top_k is None:
            top_k = config.TOP_K

        query_embedding = self.model.encode(
            [question],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )
        return _format_hits(result)

    @staticmethod
    def is_relevant(hits: list) -> bool:
        """True only if the best hit clears the relevance threshold.

        If this is False, the caller should answer 'not found in the documents'
        WITHOUT calling the LLM -- there is nothing trustworthy to ground on.
        """
        return bool(hits) and hits[0]["score"] >= config.MIN_RELEVANCE_SCORE


if __name__ == "__main__":
    # Quick manual check: python -m src.retriever "what is the leave policy?"
    import sys

    question = " ".join(sys.argv[1:]) or "What is the employee leave policy?"
    retriever = Retriever()
    hits = retriever.search(question)

    print(f"Question: {question}")
    print(f"Relevant: {Retriever.is_relevant(hits)}\n")

    for i, h in enumerate(hits, 1):
        print(f"{i}. [{h['score']}] {h['document']} p{h['page']}")
        print(f"   {h['text'][:120]}...\n")