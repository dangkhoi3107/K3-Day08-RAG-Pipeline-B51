# Kiến Trúc Hệ Thống — RAG Pipeline v2 (HUST)

> Vẽ từ code thật trong `src/*.py` + `app.py` + `group_project/evaluation/*` (không phải sơ đồ mẫu chung chung). Màu block = người phụ trách, khớp `TASK_ASSIGNMENT.md`.

```mermaid
flowchart TD
    Q(["🙋 User Query"])

    subgraph DATA["📥 CP1 — Thu thập &amp; Chuẩn hoá dữ liệu"]
        T1["Task 1<br/>task1_collect_legal_docs.py<br/>Tải PDF chính sách HUST"]
        T2["Task 2<br/>task2_crawl_news.py<br/>Crawl4AI — bài viết/thông báo"]
        T3["Task 3<br/>task3_convert_markdown.py<br/>MarkItDown → Markdown"]
        L1[("data/landing/legal/*.pdf")]
        L2[("data/landing/news/*.json")]
        S1[("data/standardized/*.md")]
        T1 --> L1 --> T3
        T2 --> L2 --> T3
        T3 --> S1
    end

    subgraph INDEX["🗂️ CP2 — Indexing (Task 4)"]
        T4["Task 4<br/>task4_chunking_indexing.py<br/>RecursiveCharacterTextSplitter<br/>size=800 / overlap=100<br/>Embed: BAAI/bge-m3 (1024-dim)"]
        CDB[("ChromaDB<br/>chroma_db/<br/>cosine similarity")]
        S1 --> T4 --> CDB
    end

    subgraph RETR["🔍 CP2-4 — Hybrid Retrieval (Task 5-9)"]
        T5["Task 5<br/>semantic_search()<br/>+ HyDE (bonus)"]
        T6["Task 6<br/>lexical_search()<br/>BM25Okapi"]
        T7["Task 7<br/>rerank_rrf()<br/>RRF(d) = Σ 1/(60+rank), k=60"]
        DEC{"dense_results[0]['score']<br/>&lt; SCORE_THRESHOLD ?<br/>(điểm Cosine GỐC, KHÔNG phải điểm RRF)"}
        T8["Task 8<br/>pageindex_search()<br/>Vectorless — đọc theo cây Mục Lục"]
        HYBRID["source = 'hybrid'"]
        FALLB["source = 'pageindex'"]

        Q --> T5
        Q --> T6
        CDB -.->|query| T5
        T5 -->|dense_results| T7
        T6 -->|sparse_results| T7
        T5 -->|top-1 score| DEC
        T7 --> HYBRID
        DEC -->|"score thấp: fallback"| T8
        DEC -->|score đủ tốt| HYBRID
        S1 -.->|convert PDF tạm, fpdf2| T8
        T8 --> FALLB
    end

    subgraph GEN["✍️ CP4 — Generation có Citation (Task 10)"]
        T10A["reorder_for_llm()<br/>front + back[::-1]<br/>tránh Lost-in-the-Middle"]
        T10B["format_context()<br/>gắn nhãn nguồn từng chunk"]
        T10C["LLM — OpenRouter<br/>SYSTEM_PROMPT: bắt buộc citation<br/>temperature=0.3 / top_p=0.9"]
        ANSW(["✅ answer + [Nguồn, Năm] + sources[]"])
        HYBRID --> T10A
        FALLB --> T10A
        T10A --> T10B --> T10C --> ANSW
    end

    subgraph APP["💬 CP5 — Application (app.py)"]
        UI["Streamlit Chat UI<br/>top_k slider, gợi ý câu hỏi,<br/>expander nguồn tham khảo"]
        ANSW --> UI
    end

    subgraph EVAL["📊 CP5 — Evaluation (group_project/)"]
        GOLD[("golden_dataset.json<br/>tối thiểu 15 Q&amp;A")]
        RAGASN["eval_pipeline.py<br/>RAGAS: Faithfulness, Relevancy,<br/>Context Recall, Context Precision"]
        RES[("results.md<br/>A/B: Hybrid vs Dense-only")]
        GOLD --> RAGASN
        UI -.->|gọi generate_with_citation mỗi câu hỏi| RAGASN
        RAGASN --> RES
    end

    classDef trung fill:#3b82f6,color:#fff,stroke:#1d4ed8,stroke-width:1px
    classDef hien fill:#a855f7,color:#fff,stroke:#7e22ce,stroke-width:1px
    classDef duc fill:#10b981,color:#fff,stroke:#047857,stroke-width:1px
    classDef son fill:#f59e0b,color:#111,stroke:#b45309,stroke-width:1px
    classDef store fill:#1e293b,color:#e2e8f0,stroke:#475569,stroke-width:1px
    classDef decision fill:#ef4444,color:#fff,stroke:#b91c1c,stroke-width:1px

    class T1,T4,T7 trung
    class T2,T5 hien
    class T6,T8,T10A,T10B,T10C,UI duc
    class T3,GOLD,RAGASN,RES son
    class L1,L2,S1,CDB,HYBRID,FALLB store
    class DEC decision
```

**Chú giải màu (khớp `TASK_ASSIGNMENT.md`):** 🔵 Trung · 🟣 Hiển · 🟢 Đức · 🟡 Sơn · ⬛ Data store · 🔴 Điểm quyết định (fallback)
Khôi (Role 1) không có block riêng — vai trò là duyệt config xuyên toàn bộ pipeline (xem mục 4 bên dưới), không sở hữu 1 stage cụ thể.

---

## 1. Luồng đi từng bước

1. **Thu thập (Task 1-3):** Trung tải PDF chính sách (`data/landing/legal/`), Hiển crawl bài viết/thông báo (`data/landing/news/`), Sơn gộp cả hai qua MarkItDown thành `.md` chuẩn hoá trong `data/standardized/`.
2. **Indexing (Task 4):** Trung cắt `.md` thành chunk 800 ký tự/overlap 100, embed bằng `BAAI/bge-m3` (1024 chiều), lưu vào ChromaDB persistent (`chroma_db/`, không gian cosine).
3. **Truy vấn song song (Task 5+6):** Query chạy đồng thời qua Hiển's `semantic_search()` (dense, cosine trên ChromaDB) và Đức's `lexical_search()` (BM25 trên toàn corpus).
4. **Gộp thứ hạng (Task 7):** Trung's `rerank_rrf()` gộp 2 danh sách theo `RRF(d) = Σ 1/(60+rank)` → không cộng điểm trực tiếp, chỉ dựa thứ hạng.
5. **Quyết định fallback (Task 9, Trung+Hiển phối hợp):** So `dense_results[0]['score']` (cosine gốc, **không phải** điểm RRF ~0.016) với `SCORE_THRESHOLD` Hiển tự đo trên corpus HUST. Thấp → nhảy sang Task 8.
6. **Vectorless fallback (Task 8, Đức):** Khi hybrid không đủ tin cậy, `pageindex_search()` đọc tài liệu theo cấu trúc cây mục lục (không qua chunk) — dùng cho câu hỏi tổng hợp cả chương/mục.
7. **Sinh câu trả lời (Task 10, Đức):** Dù đến từ nhánh nào, kết quả đều qua `reorder_for_llm()` (front + back đảo ngược, chống Lost-in-the-Middle) → `format_context()` gắn nhãn nguồn → gọi LLM qua OpenRouter với `SYSTEM_PROMPT` ép buộc trích dẫn `[Nguồn, Năm]`.
8. **Hiển thị (app.py):** Streamlit render câu trả lời + expander liệt kê từng chunk nguồn kèm score.
9. **Đánh giá (group_project/, Sơn):** `golden_dataset.json` (≥15 câu) chạy qua `generate_with_citation()`, RAGAS đo 4 chỉ số, so sánh A/B (Hybrid+rerank vs Dense-only) → `results.md`.

## 2. 2 nhánh fallback — khi nào đi nhánh nào

| | Hybrid (nhánh chính) | PageIndex (fallback) |
|---|---|---|
| Kích hoạt khi | `dense_results[0].score ≥ SCORE_THRESHOLD` | `dense_results[0].score < SCORE_THRESHOLD` |
| Cơ chế | Semantic + BM25 → RRF | Đọc cấu trúc mục lục, không chunk |
| Phù hợp với | Câu hỏi cụ thể, có từ khoá/khái niệm rõ | Câu hỏi tổng hợp cả tài liệu, hoặc corpus không có đoạn nào thật sự liên quan |
| `source` field | `"hybrid"` | `"pageindex"` |

## 3. Bẫy đã biết (đừng lặp lại)

- **RRF score ≠ độ liên quan.** Top-1 sau RRF luôn ≈ 1/61 ≈ 0.016 bất kể nội dung có khớp câu hỏi hay không — quyết định fallback ở bước 5 phải dùng điểm cosine gốc từ Task 5, tách riêng khỏi điểm dùng để sắp thứ tự cuối cùng.
- **`SCORE_THRESHOLD` không copy nguyên mẫu.** Số 0.48 trong tài liệu gốc đo trên corpus/embedding khác (RMIT) — corpus HUST phải tự đo lại (xem `TASK_ASSIGNMENT.md`, mục Role 3).
- **Đổi corpus phải xoá `chroma_db/` cũ** trước khi index lại, nếu không chunk cũ/mới lẫn lộn.

## 4. Config dùng chung (Khôi duyệt trước mỗi checkpoint)

| Tham số | Giá trị | File |
|---|---|---|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 800 / 100 | `src/task4_chunking_indexing.py` |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` (1024-dim) | `src/task4_chunking_indexing.py` |
| RRF `k` | 60 | `src/task7_reranking.py` |
| `SCORE_THRESHOLD` | tự đo trên corpus HUST | `src/task9_retrieval_pipeline.py` |
| `TEMPERATURE` / `TOP_P` | 0.3 / 0.9 | `src/task10_generation.py` |
