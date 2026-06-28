# Enterprise Knowledge Assistant

A production-oriented Retrieval Augmented Generation (RAG) system that answers
natural-language questions from a collection of internal documents and cites the
exact source (document + page) for every answer. It refuses to answer when the
documents don't contain the information, instead of hallucinating.

> **Assumption:** No document set was provided with the assignment, so this repo
> ships with a representative sample knowledge base under `data/`, covering all
> six categories in the brief (HR policy, product docs, customer FAQ, technical
> guide, compliance guidelines, process docs). The pipeline works with **any**
> PDF dropped into `data/` — nothing is hard-coded to these files.

## Architecture

RAG runs in two phases:

1. **Ingestion (one-time)** — `src/ingest.py` loads each PDF page by page, splits
   pages into overlapping chunks, embeds them locally, and stores the vectors +
   metadata (document, page) in a persistent Chroma collection.
2. **Query (per question)** — `src/retriever.py` embeds the question and finds the
   most similar chunks; `src/generator.py` asks the LLM to answer using only those
   chunks; `src/pipeline.py` ties them together, adds citations, and applies the
   hallucination guards.

```
Ingestion:  PDFs -> load+chunk (pypdf) -> embed (MiniLM) -> Chroma
Query:      question -> retrieve top-k <- Chroma -> grounded prompt -> LLM -> answer + sources
```

## Setup

```bash
pip install -r requirements.txt

cp .env.example .env            # then add your GEMINI_API_KEY
python -m src.ingest            # build the index from data/ (run once)

streamlit run app.py            # launch the UI
# or expose the API:
uvicorn src.api:app --reload    # then open http://127.0.0.1:8000/docs
```

Get a free Gemini key at https://aistudio.google.com (Get API key).

## Technology choices

| Component | Choice | Why |
|-----------|--------|-----|
| Language | Python | Mature AI/ML ecosystem |
| PDF parsing | pypdf | Reliable text + per-page extraction (needed for citations) |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` | Local, free, no API key, good quality/speed |
| Vector store | ChromaDB | Persistent, metadata filtering, zero-setup |
| LLM | Gemini `gemini-2.0-flash` (configurable) | Free tier; OpenAI/Anthropic swappable via config |
| UI | Streamlit | Fast, clean interface |
| API | FastAPI | Typed `POST /ask` endpoint |

## Design decisions

- **Chunking:** ~180-word chunks with 30-word overlap. The size is kept under the
  embedding model's 256-token limit so no text is silently truncated; the overlap
  keeps a fact from being lost across a chunk boundary.
- **Metadata:** every chunk stores `document` and `page`, which is how citations
  are produced.
- **Hallucination prevention (two guards):**
  1. If no retrieved chunk clears the relevance threshold, the system answers
     "not found" *without calling the LLM* at all.
  2. The prompt forbids outside knowledge and instructs the model to return a
     fixed "not found" sentence when the context lacks the answer; if it does,
     sources are dropped.
- **Configurable provider:** `LLM_PROVIDER` switches between Gemini, OpenAI, and
  Anthropic with no other code change. All parameters live in `src/config.py`.
- **Confidence** is the retrieval similarity of the best matching chunk.

## Evaluation

`eval/test_cases.json` holds a gold question set spanning in-scope questions,
ambiguous phrasings, and out-of-scope questions. `python -m eval.evaluate` runs
each through the pipeline and reports:

- **Answer accuracy** — does the answer contain the expected fact?
- **Citation accuracy** — is the expected source document cited?
- **Not-found handling** — are out-of-scope questions correctly refused?

The check is keyword-based for simplicity; an LLM-as-judge or semantic-similarity
scorer would be a natural upgrade.

## Known limitations

- PDF text only; scanned/image-only pages need OCR (not included).
- Keyword-based evaluation is coarse and can miss correct paraphrases.
- The relevance threshold is a single global value and may need per-corpus tuning.
- No authentication or multi-user session handling.
- Single-language (English) tuning.

## Future improvements

- Hybrid search (keyword + semantic) and a re-ranking step for better retrieval.
- Conversation memory for follow-up questions.
- Query rewriting for vague questions.
- LLM-as-judge evaluation and a labelled regression set.
- Containerised deployment (Docker) and authentication.
