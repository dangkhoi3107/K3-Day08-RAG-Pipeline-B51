"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)

Corpus được nạp trực tiếp từ các file Markdown trong data/standardized/ nên module
này hoạt động độc lập, không cần chạy Task 4 (ChromaDB) trước.
"""

import re
from pathlib import Path

import numpy as np

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# Kích thước chunk khi cắt tài liệu để lập chỉ mục BM25 (theo ký tự)
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# Corpus: List of {'content': str, 'metadata': dict}
CORPUS: list[dict] = []
# BM25 index (lazy-init khi gọi lexical_search lần đầu)
_BM25_INDEX = None


def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Cắt văn bản dài thành các chunk có overlap để giữ ngữ cảnh biên."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap
    return [c for c in chunks if c]


def load_corpus() -> list[dict]:
    """
    Nạp corpus từ toàn bộ file .md trong data/standardized/.

    Mỗi file được cắt thành các chunk (size=800, overlap=100). Trả về list of
    {'content': str, 'metadata': {source, type, chunk_index}}.
    """
    corpus: list[dict] = []
    if not STANDARDIZED_DIR.exists():
        return corpus

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        # type = tên thư mục con (legal / news) nếu có
        doc_type = md_file.parent.name if md_file.parent != STANDARDIZED_DIR else "unknown"
        for i, chunk in enumerate(_chunk_text(text)):
            corpus.append({
                "content": chunk,
                "metadata": {
                    "source": md_file.name,
                    "type": doc_type,
                    "chunk_index": i,
                },
            })
    return corpus


def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản: lowercase + tách theo ký tự chữ/số (hỗ trợ Unicode tiếng Việt)."""
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi index đã fit trên corpus đã tokenize.
    """
    from rank_bm25 import BM25Okapi

    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float, # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    global _BM25_INDEX, CORPUS

    # Lazy-load corpus lần đầu
    if not CORPUS:
        CORPUS = load_corpus()

    # Nếu corpus vẫn rỗng (chưa có tài liệu standardized), trả về danh sách rỗng
    if not CORPUS:
        return []

    # Khởi tạo index nếu chưa được dựng trước đó
    if _BM25_INDEX is None:
        _BM25_INDEX = build_bm25_index(CORPUS)

    # Tokenize câu truy vấn
    tokenized_query = _tokenize(query)
    if not tokenized_query:
        return []

    # Tính điểm BM25 cho tất cả các tài liệu
    scores = _BM25_INDEX.get_scores(tokenized_query)

    # Lấy top_k vị trí có điểm cao nhất
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        # Chỉ lấy những tài liệu có điểm > 0 (chứa ít nhất 1 từ khóa trong query)
        if scores[idx] > 0:
            results.append({
                "content": CORPUS[idx]["content"],
                "score": float(scores[idx]),
                "metadata": CORPUS[idx]["metadata"],
            })

    return results


if __name__ == "__main__":
    # Test
    print(f"Corpus size: {len(load_corpus())} chunks")
    results = lexical_search("học phí học kỳ", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] ({r['metadata']['source']}) {r['content'][:100]}...")
