"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API

Lưu ý: API `/retrieval` của PageIndex hiện đã deprecated (vẫn hoạt động, nhưng response
có field "deprecation" cảnh báo) và trả kết quả trong "retrieved_nodes" — mỗi node có
"relevant_contents": list[list[{section_title, relevant_content}]]. In response thật ra
(json.dumps(...)) trước khi viết logic parse, đừng đoán schema từ ví dụ code cũ.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


import json
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_FILE = Path(__file__).parent.parent / "pageindex_doc_ids.json"


def _convert_md_to_pdf(md_path: Path) -> Path:
    """Convert .md text to temporary PDF using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    text = md_path.read_text(encoding="utf-8")
    # Clean text to latin1/ascii for fpdf basic compatibility
    clean_text = text.encode("latin-1", errors="replace").decode("latin-1")
    
    for line in clean_text.split("\n"):
        pdf.multi_cell(0, 8, txt=line)
    
    temp_dir = Path(tempfile.gettempdir())
    temp_pdf_path = temp_dir / f"{md_path.stem}.pdf"
    pdf.output(str(temp_pdf_path))
    return temp_pdf_path


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex (convert sang PDF và cache doc_ids).
    """
    if not PAGEINDEX_API_KEY:
        print("⚠ PAGEINDEX_API_KEY chưa được cấu hình.")
        return {}

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached_ids = json.load(f)
                if cached_ids:
                    print(f"  ✓ Cache loaded: {len(cached_ids)} doc_ids từ pageindex_doc_ids.json")
                    return cached_ids
        except Exception:
            pass

    try:
        from pageindex.client import PageIndexClient
    except ImportError:
        print("⚠ Thư viện pageindex chưa được cài đặt.")
        return {}

    client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
    doc_ids = {}

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        try:
            pdf_path = _convert_md_to_pdf(md_file)
            resp = client.submit_document(str(pdf_path))
            doc_id = resp.get("doc_id") or resp.get("id")
            if doc_id:
                doc_ids[md_file.name] = doc_id
                print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")
        except Exception as e:
            print(f"  ❌ Lỗi upload {md_file.name}: {e}")

    if doc_ids:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(doc_ids, f, indent=2)

    return doc_ids


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not PAGEINDEX_API_KEY:
        return []

    try:
        from pageindex.client import PageIndexClient
    except ImportError:
        return []

    try:
        client = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        doc_ids = upload_documents()
        
        target_doc_id = list(doc_ids.values())[0] if doc_ids else None
        
        resp = client.submit_query(doc_id=target_doc_id, query=query) if target_doc_id else client.submit_query(query=query)
        retrieval_id = resp.get("retrieval_id") or resp.get("id")
        if not retrieval_id:
            return []

        import time
        retrieval = client.get_retrieval(retrieval_id)
        while retrieval.get("status") in ["processing", "queued"]:
            time.sleep(1)
            retrieval = client.get_retrieval(retrieval_id)

        results = []
        for node in retrieval.get("retrieved_nodes", []):
            for group in node.get("relevant_contents", []):
                for item in group:
                    results.append({
                        "content": item.get("relevant_content", ""),
                        "score": 0.85,
                        "metadata": {"section": item.get("section_title", "PageIndex Node")},
                        "source": "pageindex",
                    })
        return results[:top_k]
    except Exception as e:
        print(f"⚠ PageIndex search error: {e}")
        return []


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("học phí", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
