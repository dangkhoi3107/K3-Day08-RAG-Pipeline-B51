"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, doc_type, chunk_index
        }
        Sorted by score descending.
    """
    if not isinstance(query, str):
        raise TypeError("query phải là chuỗi")
    if not isinstance(top_k, int):
        raise TypeError("top_k phải là số nguyên")
    if not query.strip() or top_k <= 0:
        return []

    # Task 4 sở hữu model và Chroma collection để bảo đảm indexing/query dùng
    # đúng cùng embedding model. Import lazy giúp module vẫn import được trước
    # khi Task 4 khởi tạo xong.
    try:
        from .task4_chunking_indexing import (
            get_collection,
            get_embedding_model,
        )
    except ImportError:
        return []

    collection = get_collection()
    collection_size = collection.count()
    if collection_size == 0:
        return []

    model = get_embedding_model()
    query_embedding = model.encode(query.strip())
    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    n_results = min(top_k, collection_size)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    output = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        if document is None or distance is None:
            continue
        score = max(0.0, 1.0 - float(distance))
        output.append(
            {
                "content": document,
                "score": round(score, 4),
                "metadata": metadata or {},
            }
        )

    output.sort(key=lambda item: item["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("what is the tuition fee", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
