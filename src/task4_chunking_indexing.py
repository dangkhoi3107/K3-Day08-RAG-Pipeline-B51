"""
Task 4 — Chunking & Indexing vào Vector Store.

Chunking: RecursiveCharacterTextSplitter, CHUNK_SIZE=800 / CHUNK_OVERLAP=100.
    - 800 ký tự: đủ giữ trọn ý 1 điều khoản/đoạn chính sách mà không loãng ngữ cảnh.
    - Overlap 100: tránh cắt đôi câu quan trọng ngay ranh giới giữa 2 chunk.

Embedding: BAAI/bge-m3 (1024 chiều) — multilingual, tốt cho cả tiếng Việt lẫn tiếng Anh
(corpus HUST có cả 2 ngôn ngữ).

Vector Store: ChromaDB persistent tại chroma_db/, không gian Cosine.

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""

import os
from pathlib import Path

# Một số máy Windows có biến môi trường SSL_CERT_FILE trỏ tới file cacert.pem không
# còn tồn tại (dangling từ 1 cài đặt/conda env cũ) — khiến httpx/huggingface_hub crash
# ngay khi tải model embedding về (FileNotFoundError trong ssl.create_default_context).
# Bỏ qua biến này nếu file không tồn tại, để thư viện tự dùng bộ cert mặc định (certifi)
# — KHÔNG tắt xác thực SSL, chỉ ngừng dùng 1 đường dẫn cert đã hỏng.
if os.environ.get("SSL_CERT_FILE") and not os.path.isfile(os.environ["SSL_CERT_FILE"]):
    del os.environ["SSL_CERT_FILE"]

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION
# =============================================================================

CHUNK_SIZE = 800        # Đủ giữ trọn 1 điều khoản/đoạn chính sách, không loãng ngữ cảnh
CHUNK_OVERLAP = 100      # Tránh cắt đôi câu quan trọng ở ranh giới 2 chunk
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

EMBEDDING_MODEL = "BAAI/bge-m3"  # Multilingual, tốt cho cả tiếng Việt lẫn tiếng Anh
EMBEDDING_DIM = 1024

VECTOR_STORE = "chromadb"  # "chromadb" | "weaviate" | "faiss"
COLLECTION_NAME = "hust_services_docs"


# =============================================================================
# SINGLETONS — Task 5 import lại 2 hàm này để dùng chung đúng 1 model/1 collection
# =============================================================================

_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model():
    """Trả về SentenceTransformer đã load, cache lại (tránh load lại model mỗi lần gọi)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_collection():
    """Trả về ChromaDB collection persistent, tạo mới nếu chưa có."""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        doc_type = md_file.parent.name if md_file.parent != STANDARDIZED_DIR else "unknown"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type},
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn (RecursiveCharacterTextSplitter).

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk.
        metadata giữ nguyên 'source'/'type' từ document gốc + thêm 'chunk_index'.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i},
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    model = get_embedding_model()
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Lưu chunks vào vector store đã chọn (ChromaDB, upsert theo batch)."""
    collection = get_collection()

    BATCH_SIZE = 100
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        ids = [
            f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}"
            for c in batch
        ]
        collection.upsert(
            ids=ids,
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE} -> collection '{COLLECTION_NAME}'")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print(f"✓ Indexed to vector store ({get_collection().count()} items in collection)")


if __name__ == "__main__":
    run_pipeline()
