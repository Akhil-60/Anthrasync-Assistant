"""ingest.py - the Reader. Builds the index from files in data/ (.pdf and .txt). Run: python -m src.ingest"""

import sys
from pathlib import Path

from pypdf import PdfReader

from src import config


def load_pdf_pages(path: Path):
    reader = PdfReader(str(path))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((page_number, text))
    return pages


def chunk_text(text, size=config.CHUNK_SIZE_WORDS, overlap=config.CHUNK_OVERLAP_WORDS):
    words = text.split()
    if not words:
        return []
    step = size - overlap
    out = []
    for start in range(0, len(words), step):
        out.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return out


def build_chunks(data_dir):
    records = []
    files = sorted(Path(data_dir).glob("*.pdf")) + sorted(Path(data_dir).glob("*.txt"))
    if not files:
        sys.exit(f"No .pdf or .txt files found in {data_dir}.")
    for path in files:
        try:
            if path.suffix.lower() == ".pdf":
                pages = load_pdf_pages(path)
            else:
                text = path.read_text(encoding="utf-8", errors="ignore").strip()
                pages = [(1, text)] if text else []
        except Exception as exc:
            print(f"  ! skipped {path.name}: {exc}")
            continue
        for page_number, text in pages:
            for chunk_index, chunk in enumerate(chunk_text(text)):
                records.append({
                    "id": f"{path.name}-p{page_number}-c{chunk_index}",
                    "text": chunk,
                    "metadata": {"document": path.name, "page": page_number},
                })
        print(f"  - {path.name}: {len(pages)} page(s)")
    return records


def main():
    import chromadb
    from sentence_transformers import SentenceTransformer

    print("1/4  Loading and chunking documents...")
    records = build_chunks(config.DATA_DIR)
    if not records:
        sys.exit("No text could be extracted.")
    print(f"     built {len(records)} chunks")

    print(f"2/4  Loading embedding model ({config.EMBEDDING_MODEL})...")
    model = SentenceTransformer(config.EMBEDDING_MODEL)

    print("3/4  Embedding chunks...")
    texts = [r["text"] for r in records]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True).tolist()

    print("4/4  Storing in Chroma...")
    client = chromadb.PersistentClient(path=str(config.VECTOR_DIR))
    try:
        client.delete_collection(config.COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(name=config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    collection.add(
        ids=[r["id"] for r in records], documents=texts,
        embeddings=embeddings, metadatas=[r["metadata"] for r in records],
    )
    print(f"Done. Indexed {collection.count()} chunks into '{config.COLLECTION_NAME}'.")


if __name__ == "__main__":
    main()
