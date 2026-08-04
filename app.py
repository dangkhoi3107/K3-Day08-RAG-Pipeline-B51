"""
RAG Chatbot — University Services (HUST Edition)
Streamlit app kết nối RAG Retrieval (Task 9) và Generation (Task 10).

Chạy:
    streamlit run app.py
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm project root vào sys.path để import các task từ src/
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# PAGE CONFIG & CUSTOM CSS
# =============================================================================

st.set_page_config(
    page_title="HUST Services RAG Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS cho giao diện hiện đại & đẹp mắt
st.markdown("""
<style>
    /* Styling chung */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    
    /* Card nguồn tham khảo */
    .source-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    
    /* Badges */
    .badge-score {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-type {
        background-color: #f3e8ff;
        color: #6b21a8;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-source {
        background-color: #dcfce7;
        color: #166534;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR — INFO & SETTINGS
# =============================================================================

with st.sidebar:
    st.title("🎓 HUST Services RAG")
    st.caption("Trợ lý hỏi đáp quy chế & chính sách Đại học Bách khoa Hà Nội (HUST)")

    st.divider()

    st.subheader("💡 Câu hỏi gợi ý")
    suggestions = [
        "Mức học phí của Đại học Bách Khoa Hà Nội (HUST) là bao nhiêu?",
        "Điều kiện xét nhận học bổng khuyến khích học tập tại HUST?",
        "Quy định về đăng ký học phần và xử lý học tập HUST?",
        "Dịch vụ thư viện và đăng ký phòng học nhóm sinh viên?",
        "Thông tin hỗ trợ chỗ ở và Ký túc xá Bách khoa?",
    ]
    for s in suggestions:
        if st.button(s, use_container_width=True, key=f"sug_{s[:20]}"):
            st.session_state["pending_query"] = s

    st.divider()
    st.subheader("⚙️ Thiết lập Retrieval")
    top_k = st.slider("Số chunks retrieval (top_k)", 3, 10, 5)

    st.divider()
    if st.button("🗑️ Xóa lịch sử hội thoại", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("**Kiến trúc hệ thống:**")
    st.caption("Hybrid Retrieval (Semantic + BM25) → RRF Rerank → PageIndex Fallback → LLM Generation có Citation")
    st.caption("**Model:** `google/gemini-2.5-flash:free` (OpenRouter)")

# =============================================================================
# SESSION STATE
# =============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None

# =============================================================================
# MAIN CHAT AREA
# =============================================================================

st.markdown('<div class="main-title">🎓 HUST Services RAG Chatbot</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Trợ lý thông minh hỏi đáp quy chế, học phí, học bổng & dịch vụ Đại học Bách khoa Hà Nội</div>', unsafe_allow_html=True)

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"], 1):
                    meta = src.get("metadata", {})
                    source_name = meta.get("source", "Unknown")
                    doc_type = meta.get("type", "unknown")
                    score = src.get("score", 0)
                    ret_src = src.get("source", "hybrid")
                    
                    st.markdown(
                        f"**[{i}] {source_name}** | "
                        f"<span class='badge-type'>{doc_type}</span> "
                        f"<span class='badge-score'>score: {score:.4f}</span> "
                        f"<span class='badge-source'>{ret_src}</span>", 
                        unsafe_allow_html=True
                    )
                    st.text(src.get("content", "")[:350] + "...")
                    st.divider()

# =============================================================================
# QUERY HANDLING
# =============================================================================

user_input = st.chat_input("Nhập câu hỏi của bạn về chính sách/dịch vụ HUST...")
query = user_input or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("🔍 Đang tra cứu tài liệu HUST và tổng hợp câu trả lời..."):
            try:
                from src.task10_generation import generate_with_citation
                response = generate_with_citation(query, top_k=top_k)
                answer = response.get("answer", "Chưa thể trả lời.")
                sources = response.get("sources", [])

            except NotImplementedError:
                answer = "⚠️ **Task 10 chưa được implement.** Hãy hoàn thành `src/task10_generation.py` để kết nối pipeline vào UI!"
                sources = []
            except Exception as e:
                answer = f"❌ **Lỗi khi chạy RAG Pipeline:** {e}"
                sources = []

            st.markdown(answer)

            if sources:
                with st.expander(f"📚 Nguồn tham khảo ({len(sources)} chunks)"):
                    for i, src in enumerate(sources, 1):
                        meta = src.get("metadata", {})
                        source_name = meta.get("source", "Unknown")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0)
                        ret_src = src.get("source", "hybrid")
                        
                        st.markdown(
                            f"**[{i}] {source_name}** | "
                            f"<span class='badge-type'>{doc_type}</span> "
                            f"<span class='badge-score'>score: {score:.4f}</span> "
                            f"<span class='badge-source'>{ret_src}</span>", 
                            unsafe_allow_html=True
                        )
                        st.text(src.get("content", "")[:350] + "...")
                        st.divider()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })
