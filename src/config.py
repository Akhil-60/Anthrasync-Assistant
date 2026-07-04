"""
Central configuration for the Enterprise Knowledge Assistant.

Every tunable design decision lives here so it can be changed in one place
and explained easily in the README. Values can be overridden with environment
variables, which keeps secrets (API keys) out of the codebase.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"                 # source PDFs
VECTOR_DIR = BASE_DIR / "chroma_store"       # persisted vector index
COLLECTION_NAME = "enterprise_kb"

# --- Chunking ---
# Sized to fit the embedding model's window. all-MiniLM-L6-v2 truncates anything
# beyond 256 word-piece tokens, so a larger chunk would be silently cut off and
# lose information. We chunk by words (~180 words is comfortably under that limit)
# with a 30-word overlap, so a fact split across a boundary still appears whole in
# at least one chunk.
CHUNK_SIZE_WORDS = 180
CHUNK_OVERLAP_WORDS = 30

# --- Embeddings ---
# all-MiniLM-L6-v2: 384-dim, runs locally, no API key, strong quality/speed
# trade-off. Swap to "BAAI/bge-base-en-v1.5" for higher accuracy.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Retrieval ---
TOP_K = int(os.getenv("TOP_K", "5"))         # chunks fetched per query
# If the best chunk's similarity is below this, treat the answer as "not found"
# instead of forcing the LLM to answer from weak context (hallucination guard).
MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.1"))

# --- LLM ---
# Provider is configurable. We default to Gemini (generous free tier). To use
# OpenAI or Anthropic instead, change LLM_PROVIDER and add the matching key;
# the generator dispatches on this value without any other code change.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_TEMPERATURE = 0.0                        # deterministic, factual answers

# Gemini (free tier). If you ever get a "model not found" error, check the
# current model name at https://ai.google.dev and update this value.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Optional alternative providers
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
