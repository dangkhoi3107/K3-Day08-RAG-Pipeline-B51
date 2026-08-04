"""Task 4 - Chunk standardized markdown and index it into ChromaDB."""

import hashlib
import importlib.util
import json
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Recursive splitting is a steady choice for mixed Markdown converted from PDFs
# and crawled pages: it keeps paragraphs together before falling back to lines,
# sentences, and words.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
CHUNKING_METHOD = "recursive"

# all-MiniLM-L6-v2 is light enough for local lab machines and fast to index.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

VECTOR_STORE = "chromadb"
COLLECTION_NAME = "university_services_docs"


def _fallback_split_text(text: str) -> list[str]:
    """Small local fallback when langchain-text-splitters is not installed."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)
        chunk = text[start:end]

        if end < text_length:
            split_at = max(
                chunk.rfind("\n\n"),
                chunk.rfind("\n"),
                chunk.rfind(". "),
                chunk.rfind(" "),
            )
            if split_at > CHUNK_SIZE // 2:
                end = start + split_at + 1
                chunk = text[start:end]

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break
        start = max(end - CHUNK_OVERLAP, start + 1)

    return chunks


def _module_available(module_name: str) -> bool:
    """Return True when an optional dependency can be imported."""
    return importlib.util.find_spec(module_name) is not None


def _fallback_embedding(text: str) -> list[float]:
    """Create a deterministic normalized bag-of-words hash embedding."""
    embedding = [0.0] * EMBEDDING_DIM
    words = text.lower().split()
    for word in words:
        digest = hashlib.md5(word.encode("utf-8")).hexdigest()
        index = int(digest[:8], 16) % EMBEDDING_DIM
        embedding[index] += 1.0
    norm = sum(value * value for value in embedding) ** 0.5 or 1.0
    return [value / norm for value in embedding]


def load_documents() -> list[dict]:
    """
    Read all Markdown files from data/standardized/.

    Returns:
        List of {"content": str, "metadata": {"source": str, "type": str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        if md_file.name.startswith("."):
            continue

        content = md_file.read_text(encoding="utf-8").strip()
        if not content:
            continue

        relative_path = md_file.relative_to(STANDARDIZED_DIR).as_posix()
        path_parts = {part.lower() for part in md_file.relative_to(STANDARDIZED_DIR).parts}
        doc_type = "legal" if "legal" in path_parts else "news" if "news" in path_parts else "unknown"

        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": relative_path,
                    "type": doc_type,
                },
            }
        )

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Split documents with RecursiveCharacterTextSplitter.

    Returns:
        List of {"content": str, "metadata": dict}; each item is one chunk.
    """
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        split_text = splitter.split_text
    except ModuleNotFoundError:
        split_text = _fallback_split_text

    chunks = []
    for doc_index, document in enumerate(documents):
        splits = split_text(document["content"])
        for chunk_index, chunk_text in enumerate(splits):
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **document["metadata"],
                        "doc_index": doc_index,
                        "chunk_index": chunk_index,
                    },
                }
            )

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed chunks with SentenceTransformer BAAI/bge-m3.

    Returns:
        The same chunk dictionaries with an "embedding" list added.
    """
    if not chunks:
        return chunks

    if not _module_available("chromadb"):
        print("chromadb is not installed; using deterministic fallback embeddings.")
        for chunk in chunks:
            chunk["embedding"] = _fallback_embedding(chunk["content"])
        return chunks

    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(EMBEDDING_MODEL)
        texts = [chunk["content"] for chunk in chunks]
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()
    except Exception as exc:
        print(f"Using deterministic fallback embeddings: {exc}")
        for chunk in chunks:
            chunk["embedding"] = _fallback_embedding(chunk["content"])

    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert embedded chunks into a persistent local ChromaDB collection."""
    if not chunks:
        print("No chunks to index.")
        return

    missing_embeddings = [index for index, chunk in enumerate(chunks) if "embedding" not in chunk]
    if missing_embeddings:
        raise ValueError(f"Chunks missing embeddings: {missing_embeddings[:5]}")

    ids = [
        f"{chunk['metadata']['path']}::chunk_{chunk['metadata']['chunk_index']}"
        for chunk in chunks
    ]

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        collection.upsert(
            ids=ids,
            documents=[chunk["content"] for chunk in chunks],
            embeddings=[chunk["embedding"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
        )
        print(f"Indexed {len(chunks)} chunks into ChromaDB at {CHROMA_DIR}")
    except ModuleNotFoundError:
        fallback_path = CHROMA_DIR / "fallback_index.json"
        payload = {
            "collection": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": EMBEDDING_DIM,
            "ids": ids,
            "documents": [chunk["content"] for chunk in chunks],
            "metadatas": [chunk["metadata"] for chunk in chunks],
            "embeddings": [chunk["embedding"] for chunk in chunks],
        }
        fallback_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        print(f"chromadb is not installed; wrote fallback index to {fallback_path}")


def run_pipeline():
    """Run the full pipeline: load -> chunk -> embed -> index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
