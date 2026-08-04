# RAG Evaluation Results

> ⏳ **Trạng thái:** File này được `eval_pipeline.py` tự động sinh khi chạy đánh giá.
> Bảng điểm bên dưới sẽ được điền số liệu thật sau khi pipeline hoàn chỉnh (Task 5, 7, 8,
> 9, 10 của các Role khác đã xong) và lệnh `python -m group_project.evaluation.eval_pipeline`
> chạy thành công. Hiện tại đây là bản kế hoạch đánh giá (evaluation plan).

## Framework sử dụng

**RAGAS** (`ragas==0.1.21`).
- LLM judge: `openai/gpt-4o-mini` qua OpenRouter (cấu hình bằng `EVAL_JUDGE_MODEL`).
- Embeddings: `BAAI/bge-m3` chạy local (không tốn request LLM).
- Số câu hỏi trong `golden_dataset.json`: **19** (18 in-domain + 1 lạc đề để test fallback).

---

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ (A−B) |
|--------|---------------------------|----------------------|---------|
| Faithfulness | _pending_ | _pending_ | |
| Answer Relevance | _pending_ | _pending_ | |
| Context Recall | _pending_ | _pending_ | |
| Context Precision | _pending_ | _pending_ | |
| **Average** | _pending_ | _pending_ | |

---

## A/B Comparison Analysis

**Config A:** Hybrid retrieval (semantic + BM25) → RRF merge → reranking
(`retrieve(query, use_reranking=True)`).

**Config B:** Dense-only — chỉ semantic search, không reranking
(`retrieve(query, use_reranking=False)`).

**Giả thuyết:** Config A thắng ở **context_precision** vì BM25 bắt đúng các từ khóa/số
hiệu đặc thù (ví dụ "TCHP", "1 TCHT = 2,5 TCHP", "qldt.hust.edu.vn") mà dense search
dễ bỏ sót; đổi lại tốn thêm chi phí tính toán. Kết luận cuối cùng điền sau khi có số liệu.

---

## Worst Performers (Bottom 3 — Config A)

| # | Question | Faithfulness | Relevance | Recall | Precision |
|---|----------|-------------|-----------|--------|-----------|
| 1 | _pending_ | | | | |
| 2 | _pending_ | | | | |
| 3 | _pending_ | | | | |

---

## Recommendations

### Cải tiến 1 — Chunking
**Action:** Thử giảm `CHUNK_SIZE` (800→500) + tăng overlap để giảm nhiễu trong context.
**Expected impact:** Context_precision & faithfulness tăng.

### Cải tiến 2 — Reranking
**Action:** Dùng cross-encoder rerank cho top-k cuối thay/kết hợp với RRF.
**Expected impact:** Đưa đúng chunk liên quan lên đầu → context_recall tăng.

### Cải tiến 3 — Query expansion
**Action:** Thêm HyDE / multi-query cho các câu hỏi có điểm thấp ở bảng trên.
**Expected impact:** Bắt được tài liệu mà truy vấn gốc bỏ lỡ → recall tăng.
