# Bài Tập Nhóm — University Services RAG Chatbot

## Mục Tiêu

Sau khi hoàn thành bài cá nhân, nhóm ngồi lại để xây dựng **1 trong 2 sản phẩm**:

---

## Yêu cầu 1: Sản phẩm nhóm RAG Chatbot

Xây dựng chatbot trả lời câu hỏi về dịch vụ và chính sách đại học liên quan.

**Yêu cầu:**
- Giao diện chat (Streamlit / Gradio / Chainlit)
- Trả lời có citation (dựa trên Task 10)
- Hỗ trợ follow-up questions (conversation memory)
- Hiển thị source documents đã dùng

**Stack gợi ý:**
```
Chainlit/Streamlit → Retrieval (Task 9) → Generation (Task 10) → Display
```

---

## Yêu cầu 2: RAG Evaluation Pipeline

Sử dụng **1 trong 3 framework** sau để evaluate pipeline RAG của nhóm:

### Framework lựa chọn

| Framework | Cài đặt | Đặc điểm |
|-----------|---------|-----------|
| [DeepEval](https://github.com/confident-ai/deepeval) | `pip install deepeval` | Nhiều metric built-in, dễ integrate với pytest |
| [RAGAS](https://github.com/explodinggradients/ragas) | `pip install ragas` | Chuẩn industry cho RAG eval, 3 trục chính |
| [TruLens](https://github.com/truera/trulens) | `pip install trulens` | Dashboard UI, feedback functions mạnh |

### Yêu cầu Evaluation

1. **Tạo Golden Dataset** — tối thiểu 15 cặp Q&A (question, expected_answer, expected_context)
2. **Chạy evaluation** trên toàn bộ golden dataset với các metrics sau:
   - **Faithfulness** — câu trả lời có bám đúng context không?
   - **Answer Relevance** — câu trả lời có đúng câu hỏi không?
   - **Context Recall** — retriever có lấy đủ evidence không?
   - **Context Precision** — trong context lấy về, bao nhiêu % thực sự hữu ích?
3. **So sánh A/B** — chạy eval trên ít nhất 2 config khác nhau (ví dụ: có reranking vs không reranking, hoặc hybrid vs dense-only)
4. **Báo cáo** — bảng điểm + phân tích worst performers + đề xuất cải tiến

Xem code mẫu (DeepEval/RAGAS/TruLens) chi tiết trong `README.md` gốc mục "Yêu cầu 2".

### Deliverable Evaluation

- [ ] File `group_project/evaluation/golden_dataset.json` — 15+ cặp Q&A
- [ ] File `group_project/evaluation/eval_pipeline.py` — script chạy evaluation
- [ ] File `group_project/evaluation/results.md` — bảng điểm + phân tích
- [ ] So sánh A/B ít nhất 2 configs

---

## Yêu Cầu Chung

1. **Tích hợp pipeline** từ bài cá nhân của các thành viên
2. **Demo hoạt động được** trong buổi trình bày (chạy local hoặc deploy)
3. **Evaluation pipeline** chạy được và có báo cáo kết quả
4. **Code push lên repository** chung của nhóm
5. **README** mô tả kiến trúc và phân công (điền bên dưới)

---

## Kiến Trúc Hệ Thống

Xem sơ đồ chi tiết (Mermaid flowchart, màu theo người phụ trách) tại [`ARCHITECTURE.md`](../ARCHITECTURE.md).

---

## Phân Công Công Việc

> Đồng bộ với bảng phân công ở `README.md` gốc và `checkpoint_timer.html` (Nhóm 5). CP5 là lúc ghép các module cá nhân lại thành sản phẩm nhóm.

| Thành viên | MSSV | Role | Việc ở CP5 (Chatbot UI + RAGAS) | Việc ở CP6 (Demo) | Trạng thái |
|-----------|------|------|----------------------------------|--------------------|------------|
| Khôi | | Role 1 — Team Leader & Architect | Điều phối ghép code, duyệt `results.md` đủ bảng điểm | Thuyết trình tổng quan kiến trúc, điều phối Q&A | Chưa bắt đầu |
| Trung | | Role 2 — Data & Dense Search Dev | Nối `generate_with_citation()` (Task 10) vào `app.py`, xử lý `sources` cho UI | Giải đáp kỹ thuật ChromaDB/bge-m3/RRF | Chưa bắt đầu |
| Hiển | | Role 3 — Sparse & Rerank Dev | Thêm slider `top_k` ở sidebar, hiển thị kiến trúc Supervisor | Giải thích RRF Rerank + PageIndex fallback | Chưa bắt đầu |
| Đức | | Role 4 — Frontend & Chatbot Dev | Hoàn thiện `st.chat_message`, nút gợi ý câu hỏi mẫu | Trực tiếp thao tác live demo Streamlit | Chưa bắt đầu |
| Sơn | | Role 5 — Evaluation & QA Engineer | Viết 15+ cặp Q&A `golden_dataset.json`, chạy `eval_pipeline.py`, xuất `results.md` (so sánh Hybrid vs Dense-only) | Báo cáo 4 chỉ số RAGAS + phân tích A/B | Chưa bắt đầu |

---

## Hướng Dẫn Chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy app
streamlit run app.py
# hoặc
chainlit run app.py
```

---

## Lưu ý

Hãy giữ lại repo này nếu như bạn học track 3 giai đoạn 2, chúng ta sẽ phát triển tiếp dự án lên knowledge graph để khắc phục các câu hỏi hóc búa khi có các câu hỏi khó.
