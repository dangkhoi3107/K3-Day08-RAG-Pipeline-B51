# Script Thuyết Trình — RAG Pipeline v2 (HUST)

> Dùng cho buổi demo cuối (CP6) và các lượt "gọi ngẫu nhiên demo" ở cuối mỗi checkpoint (xem `checkpoint_timer.html`). Vai trò: Khôi (Leader), Trung (Role 2), Hiển (Role 3), Đức (Role 4), Sơn (Role 5) — chi tiết kỹ thuật tra thêm ở `TASK_ASSIGNMENT.md`, sơ đồ ở `ARCHITECTURE.md`.
> Chỗ nào ghi `[...]` là số liệu thật, điền khi demo xong — đừng đọc số mẫu trong file này khi thuyết trình thật.

---

## CP0 — Setup (0:00–0:10)

**Pass criteria:** cả 5 người cài xong venv + `requirements.txt`, `.env` có `OPENROUTER_API_KEY`, import không lỗi.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Cả 5 người | `python -m venv .venv`, `pip install -r requirements.txt`, copy `.env.example` → `.env` | Môi trường chạy được | `streamlit run app.py` mở lên không lỗi import |

*Không cần script — checkpoint kỹ thuật thuần, không demo trước lớp.*

---

## CP1 — Thu thập & Chuẩn hoá dữ liệu (0:10–0:35)

**Pass criteria:** ≥3 PDF trong `data/landing/legal/`, ≥5 bài trong `data/landing/news/`, convert xong sang `.md`.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Trung | Task 1 — tải PDF chính sách HUST (`SOURCES.md`) | 4 file PDF trong `data/landing/legal/` | `pytest tests/test_individual.py -k TestTask1 -v` → 3/3 |
| Hiển | Task 2 — crawl bài viết HUST (Crawl4AI) | ≥5 file JSON trong `data/landing/news/` | `pytest tests/test_individual.py -k TestTask2 -v` → 4/4 |
| Sơn | Task 3 — convert toàn bộ sang Markdown (MarkItDown) | `.md` trong `data/standardized/legal/` + `news/` | `pytest tests/test_individual.py -k TestTask3 -v` → 4/4 |
| Khôi | Điều phối nguồn (tránh trùng), duyệt file `.md` sinh ra | — | đọc thử 1-2 file `.md`, không lỗi encoding |

**Script gợi ý (nếu bị gọi demo ngẫu nhiên cuối CP1):**
> "Nhóm em chọn chủ đề dịch vụ đại học của **Đại học Bách Khoa Hà Nội**. Bọn em thu thập [X] văn bản chính sách PDF thật từ hust.edu.vn — học phí, quy chế đào tạo, quy trình học bổng — và [Y] bài viết về thư viện, sự kiện, học bổng từ crawl4ai. Toàn bộ convert sang Markdown bằng MarkItDown để giữ cấu trúc heading sạch cho bước chunking sau."

---

## CP2 — Chunking, Indexing & Search Cơ Bản (0:35–1:00)

**Pass criteria:** `chroma_db/` có data; pytest Task 4-6 passed.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Trung | Task 4 — chunk 800/overlap 100, embed `BAAI/bge-m3`, index ChromaDB | `chroma_db/` có collection | `pytest -k TestTask4 -v` → 4/4 |
| Hiển | Task 5 — `semantic_search()` (+ HyDE nếu kịp) | Hàm trả kết quả cosine sorted | `pytest -k TestTask5 -v` → 4/4 |
| Đức | Task 6 — `lexical_search()` BM25 | Hàm trả kết quả BM25 sorted | `pytest -k TestTask6 -v` → 4/4 |
| Khôi | Duyệt `CHUNK_SIZE=800/OVERLAP=100`, `COLLECTION_NAME` khớp cả nhóm | — | đọc `task4_chunking_indexing.py` dòng 44-54 |

**Script gợi ý (nếu bị gọi demo so sánh Semantic vs BM25):**
> "Em thử query `[câu hỏi ví dụ]`. Semantic search trả về `[kết quả]` với score `[X]` vì hiểu ngữ nghĩa dù không trùng từ khoá. BM25 trả về `[kết quả]` — mạnh hơn khi câu hỏi có mã số/từ khoá chính xác như tên chương trình học hoặc mã quyết định. Đây chính là lý do bọn em kết hợp cả hai ở Task 7 thay vì chỉ dùng 1."

---

## CP3 — Reranking & PageIndex Fallback (1:00–1:20)

**Pass criteria:** RRF gộp thành công 2 ranker; PageIndex trả kết quả cho câu hỏi cấu trúc.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Trung | Task 7 — `rerank_rrf()`, công thức Σ1/(60+rank) | Hàm gộp rank | `pytest -k TestTask7 -v` → 3/3 |
| Hiển | Task 7 mở rộng — cross-encoder Jina (nếu có key) | (tuỳ chọn) | thử query so sánh trước/sau rerank |
| Đức | Task 8 — `pageindex_search()` vectorless | Hàm trả `source='pageindex'` | `pytest -k TestTask8 -v` → 2/2 |
| Sơn | Thử query ngoài domain, xem fallback có kích hoạt | — | quan sát log `⚠ Semantic best score < threshold` |

**Script gợi ý:**
> "RRF gộp thứ hạng thay vì cộng điểm trực tiếp, vì thang điểm Cosine `[0,1]` và BM25 `[0,∞)` không thể cộng thẳng — công thức `RRF(d) = Σ 1/(60+rank)` chỉ quan tâm thứ hạng, không quan tâm độ chênh điểm tuyệt đối. Khi câu hỏi mang tính tổng hợp cả tài liệu — ví dụ `[câu hỏi ví dụ]` — hệ thống tự chuyển sang PageIndex, đọc theo cấu trúc mục lục thay vì từng đoạn 800 ký tự rời rạc."

---

## CP4 — Pipeline Hoàn Chỉnh & Generation (1:20–1:45) — mốc 50đ cá nhân

**Pass criteria:** `pytest tests/test_individual.py -v` → **35/35 passed**.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Trung | Task 9 — nối Semantic + BM25 + RRF thành `retrieve()` | `source='hybrid'` | `pytest -k TestTask9 -v` |
| Hiển | Task 9 — canh `SCORE_THRESHOLD` (đo thật trên corpus HUST, không copy 0.48) | ngưỡng fallback đúng | test `xyzabc123nonsense` → trả `pageindex` |
| Đức | Task 10 — `reorder_for_llm()` + `format_context()` + gọi LLM có citation | answer kèm `[Nguồn, Năm]` | `pytest -k TestTask10 -v` |
| Sơn + Khôi | Chạy full suite, xác nhận điểm cá nhân | — | `pytest tests/test_individual.py -v` |

**Script gợi ý:**
> "Tới đây, cả 5 thành viên đã hoàn thành 35/35 test tự động, tương đương 50 điểm bài cá nhân. Điểm quan trọng nhất ở Task 9 là logic fallback: bọn em **so sánh điểm Cosine gốc** từ Task 5, chứ không dùng điểm RRF đã gộp — vì điểm RRF top-1 luôn xấp xỉ 0.016 bất kể nội dung có liên quan hay không, nếu so nhầm thì fallback sẽ không bao giờ kích hoạt được."

---

## CP5 — Chatbot UI & Đánh Giá RAGAS (1:45–2:15)

**Pass criteria:** `app.py` chạy mượt kèm citation; `results.md` có đủ bảng điểm RAGAS A/B.

| Người | Việc làm | Output | Cách kiểm tra |
|---|---|---|---|
| Đức | Hoàn thiện UI (câu hỏi gợi ý, polish) | `app.py` chạy mượt | `streamlit run app.py`, thử hỏi thật |
| Trung / Hiển | Rà lại phần tích hợp `generate_with_citation()` vào `app.py` (đã có sẵn trong starter) | — | chat thử, xem có citation |
| Sơn | `golden_dataset.json` (≥15 câu HUST) + chạy `eval_pipeline.py` | `results.md` có số liệu thật | `python -m group_project.evaluation.eval_pipeline` |
| Khôi | Duyệt `results.md` đủ 4 chỉ số + so sánh A/B | — | đọc `results.md` |

**Script gợi ý:**
> "Chatbot tụi em xây trên Streamlit, có thanh chọn `top_k`, hiển thị nguồn tham khảo kèm score cho từng câu trả lời. Về đánh giá, tụi em dùng RAGAS trên `[15+]` câu hỏi thật, so sánh 2 cấu hình: **Hybrid + Rerank** đạt Faithfulness `[X]`, Context Precision `[Y]`; **Dense-only** đạt `[X']`, `[Y']` — chênh lệch `[Z]` điểm, chứng minh việc kết hợp BM25 + RRF thực sự cải thiện chất lượng."

---

## CP6 — Thuyết Trình Demo Live (2:15–3:00, 45 phút)

**Pass criteria:** demo live trước lớp + push code lên GitHub.

### Thứ tự trình bày (gợi ý ~8-9 phút/người)

**1. Khôi — Mở đầu & Kiến trúc tổng quan (~8 phút)**
> "Chào thầy/cô và cả lớp. Nhóm em xây dựng RAG Pipeline v2 cho chủ đề dịch vụ Đại học Bách Khoa Hà Nội — học phí, học bổng, ký túc xá, đăng ký học phần, thư viện. Pipeline gồm 3 tầng chính: **thu thập & chuẩn hoá dữ liệu**, **hybrid retrieval** kết hợp Semantic Search và BM25 gộp bằng RRF, và **generation có citation** để tránh AI bịa đặt thông tin. Khi hybrid search không đủ tin cậy, hệ thống tự động chuyển sang PageIndex — đọc tài liệu theo cấu trúc mục lục thay vì vector."
> *(chiếu sơ đồ `ARCHITECTURE.md`)*
> "Nhóm gồm 5 người: em phụ trách kiến trúc & điều phối; Trung — Dense Search & Indexing; Hiển — Sparse Search & Rerank; Đức — Frontend & Generation; Sơn — Data & Evaluation."

**2. Trung — Kỹ thuật Indexing & Dense Search (~7 phút)**
> "Em phụ trách tầng lưu trữ vector. Dữ liệu sau chuẩn hoá được chunk 800 ký tự, overlap 100 — đủ ngắn để tránh loãng ngữ cảnh nhưng overlap đảm bảo không cắt đôi câu quan trọng ở ranh giới đoạn. Embedding dùng `BAAI/bge-m3`, 1024 chiều, vì hỗ trợ tốt cả tiếng Việt lẫn tiếng Anh — phù hợp vì tài liệu HUST có cả 2 ngôn ngữ. Lưu vào ChromaDB, không gian Cosine, truy vấn trong vài mili-giây."
> *(demo: chạy 1 câu hỏi qua `semantic_search()`, chỉ ra score)*

**3. Hiển — RRF Rerank & Fallback Logic (~7 phút)**
> "Em phụ trách gộp kết quả và xử lý fallback. BM25 giỏi từ khoá chính xác (mã quyết định, mã chương trình), Semantic giỏi diễn giải theo nghĩa. Hai loại điểm này không cùng thang đo nên không cộng trực tiếp được — em dùng RRF: `RRF(d) = Σ 1/(60+rank)`, chỉ dựa thứ hạng. Về fallback: khi điểm Cosine gốc tốt nhất dưới ngưỡng đã đo — nghĩa là corpus không có đoạn nào thực sự liên quan — hệ thống chuyển sang PageIndex thay vì ép LLM trả lời từ dữ liệu rác."
> *(demo: 1 câu hỏi trong domain qua hybrid, 1 câu hỏi lạc đề kích hoạt fallback)*

**4. Đức — Live Demo Chatbot (~10 phút)**
> "Em demo trực tiếp ứng dụng." *(mở `app.py` trên máy chiếu)*
> - Câu 1 (trong domain, dễ): `[câu hỏi ví dụ, có trong corpus]` → chỉ ra citation `[Nguồn, Năm]` trong câu trả lời + expander nguồn tham khảo kèm score.
> - Câu 2 (đòi hỏi tổng hợp, kích hoạt PageIndex): `[câu hỏi tổng hợp ví dụ]`.
> - Câu 3 (ngoài domain): cho thấy hệ thống từ chối bịa đặt — trả lời "Tôi không thể xác minh thông tin này".
> "Việc sắp xếp lại context trước khi đưa vào LLM — đặt đoạn quan trọng nhất ở đầu và cuối — dựa trên nghiên cứu Lost in the Middle của Liu et al. 2023: LLM nhớ tốt đầu/cuối prompt, hay bỏ sót thông tin ở giữa."

**5. Sơn — Kết quả Đánh giá RAGAS (~7 phút)**
> "Em phụ trách đo chất lượng hệ thống bằng RAGAS trên `[15+]` câu hỏi thật, đo 4 chỉ số: Faithfulness, Answer Relevancy, Context Recall, Context Precision. So sánh 2 cấu hình — Hybrid+Rerank vs Dense-only — cho thấy `[nêu con số + phân tích thật]`. Điểm thấp nhất rơi vào nhóm câu hỏi `[loại câu hỏi yếu nhất]`, nguyên nhân `[phân tích]`, hướng cải thiện đề xuất là `[đề xuất]`."
> *(chiếu bảng trong `group_project/evaluation/results.md`)*

**6. Cả nhóm — Q&A**

---

## Câu hỏi Coach/Giảng viên hay hỏi — chuẩn bị sẵn câu trả lời

| Câu hỏi | Ai trả lời | Ý chính |
|---|---|---|
| "Tại sao chunk 800, không phải 500 hay 1000?" | Trung | 800 đủ giữ trọn ý 1 điều khoản chính sách, không quá dài gây loãng ngữ cảnh; overlap 100 tránh cắt đôi câu ở ranh giới |
| "RRF khác gì cộng điểm trung bình 2 ranker?" | Hiển | Cosine `[0,1]` và BM25 `[0,∞)` lệch thang đo — cộng thẳng sẽ để 1 ranker lấn át; RRF chỉ dùng rank nên công bằng |
| "Sao biết ngưỡng fallback 0.X là đúng?" | Hiển | Đo thực nghiệm: chạy câu hỏi chắc chắn liên quan và câu hỏi rác qua `semantic_search()`, lấy ngưỡng nằm giữa 2 nhóm điểm — không copy số mẫu vì mỗi corpus/embedding cho khoảng điểm khác nhau |
| "Vì sao cần reorder trước khi đưa LLM?" | Đức | Lost in the Middle (Liu et al. 2023) — LLM nhớ tốt đầu/cuối, bỏ sót giữa; xếp `front + back[::-1]` để đoạn quan trọng nhất nằm ở 2 đầu |
| "PageIndex khác ChromaDB thế nào?" | Trung/Đức | ChromaDB tìm theo similarity từng đoạn nhỏ (vector); PageIndex đọc cấu trúc cây mục lục toàn tài liệu, không chunking — hợp với câu hỏi tổng hợp |
| "Hybrid tốt hơn Dense-only bao nhiêu?" | Sơn | Nêu số liệu thật trong `results.md` — Faithfulness/Precision chênh bao nhiêu điểm, vì sao (BM25 vớt được các câu hỏi có mã/từ khoá riêng mà Dense bỏ sót) |
| "Nếu LLM không có context phù hợp thì sao?" | Đức | SYSTEM_PROMPT ép trả lời "Tôi không thể xác minh thông tin này" thay vì bịa — có thể demo trực tiếp bằng câu hỏi ngoài domain |

---

## Checklist trước khi lên trình bày

- [ ] `pytest tests/test_individual.py -v` → 35/35 passed (chụp màn hình làm bằng chứng)
- [ ] `streamlit run app.py` test trước ít nhất 1 lần với mạng thật (tránh lỗi live)
- [ ] `results.md` đã điền số liệu thật, không còn để trống
- [ ] Đã chuẩn bị sẵn 3 câu hỏi demo (1 dễ, 1 kích hoạt fallback, 1 ngoài domain)
- [ ] Code đã push lên `origin/main`, không còn branch riêng lẻ chưa merge
- [ ] Mỗi người đọc trước phần Q&A dự kiến của vai trò mình
