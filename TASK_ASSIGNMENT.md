# Phân Công Chi Tiết — Task 1-10 + Bài Nhóm

> Soạn dựa trên đọc trực tiếp toàn bộ `src/*.py`, `app.py`, `tests/test_individual.py`, `group_project/evaluation/*` hiện có trong repo (không suy đoán). Vai trò theo `checkpoint_timer.html` (Nhóm 5).
> Chủ đề dữ liệu: **Đại học Bách Khoa Hà Nội** (xem `data/landing/legal/SOURCES.md` cho nguồn crawl).

**Thứ tự phụ thuộc bắt buộc** (không thể làm tắt):
`Task 1,2 → Task 3 → Task 4 → (Task 5 ‖ Task 6) → Task 7 → Task 8 (độc lập, chạy song song được) → Task 9 (cần 5+6+7+8) → Task 10 (cần 9) → app.py (cần 10) → group_project/evaluation (cần app.py chạy được)`

**3 điểm đã code sẵn trong starter — KHỎI cần làm lại** (tránh nhóm phí thời gian):
- `app.py` dòng 122-125 **đã gọi thật** `generate_with_citation()` từ Task 10 (không phải chỉ là code mẫu comment) — Task 10 xong là app chạy được ngay, không cần sửa gì thêm ở phần gọi hàm.
- `app.py` dòng 57 **đã có sẵn** slider `top_k` trong sidebar.
- `app.py` dòng 79-92, 134-145 **đã có sẵn** render lịch sử chat + expander hiển thị nguồn/score.
- `group_project/evaluation/results.md` **đã có sẵn khung bảng** (metric table, A/B section, worst performers, recommendations) — chỉ cần điền số, không cần dựng lại cấu trúc.

---

## 🔴 Role 1 — Khôi (Team Leader & Architect)

Không sở hữu file code riêng — vai trò là duyệt config dùng chung để 4 người kia không lệch nhau (lệch 1 trong các giá trị dưới đây là cả pipeline gãy ở chỗ nối).

| Việc | Vì sao quan trọng |
|---|---|
| Chốt `CHUNK_SIZE=800, CHUNK_OVERLAP=100` trong `src/task4_chunking_indexing.py` (dòng 44-45) | Code mặc định hiện là **500/50**, khác với con số 800/100 đã ghi trong README/checkpoint_timer — Trung phải sửa lại 2 hằng số này, Khôi cần nhắc |
| Chốt `COLLECTION_NAME` trong task4 (dòng 54) khớp chủ đề mới (đang để `"university_services_docs"` — có thể giữ hoặc đổi `"hust_services_docs"`, miễn cả nhóm dùng chung 1 tên) | Tên lệch → mỗi người query vào 1 collection khác nhau, tưởng bug nhưng thực ra do đặt tên khác |
| Sau khi đổi corpus từ RMIT → HUST, nhắc Trung **xoá `chroma_db/` cũ** trước khi index lại | Ghi rõ trong comment task4 dòng 28-30: không xoá → chunk cũ (RMIT) và mới (HUST) lẫn lộn, retrieval trả rác |
| Duyệt `SCORE_THRESHOLD` Hiển tự đo ở Task 9 (không cho copy nguyên 0.48 từ ví dụ) | 0.48 là số đo trên corpus/embedding cũ trong ví dụ — corpus HUST sẽ ra khoảng điểm khác |
| Cập nhật mục "Chủ Đề Dữ Liệu" trong `README.md` (đang ghi RMIT Vietnam) | Tránh cả nhóm/giám khảo hiểu nhầm |
| Cuối CP4: chạy `pytest tests/test_individual.py -v`, xác nhận `35 passed` | Mốc 50đ cá nhân |
| CP5: chọn code Task 9-10 tốt nhất, gộp vào `app.py` nếu có nhiều bản khác nhau | `app.py` hiện chỉ import 1 pipeline duy nhất — nếu ai sửa riêng bản của mình phải hợp nhất trước |
| CP6: thuyết trình tổng quan kiến trúc, điều phối Q&A | — |

---

## 🔵 Role 2 — Trung (Data & Dense Search Dev)

### Task 1 — `src/task1_collect_legal_docs.py`
- **Trạng thái:** chỉ có `setup_directory()`; phần tải file 100% để trống (comment gợi ý dùng `requests`).
- **Cần làm:** tải 3-4 PDF theo `data/landing/legal/SOURCES.md` đã soạn sẵn (đủ link), đổi tên không dấu, bỏ vào `data/landing/legal/`. Không bắt buộc viết code — có thể tải tay. Nếu muốn tự động, thêm hàm `download_file(url, filename)` bằng `requests.get()` như comment gợi ý dòng 40-47.
- **Test:** `pytest tests/test_individual.py -k TestTask1 -v` (3 test: thư mục tồn tại, ≥3 file, mỗi file >1KB).

### Task 4 — `src/task4_chunking_indexing.py`
- **Trạng thái:** 4 hàm đều `raise NotImplementedError`, code mẫu đầy đủ nằm sẵn trong comment (chỉ cần bỏ comment + chỉnh).
- **Cần sửa:**
  1. `load_documents()` (dòng 61-78) — đọc toàn bộ `.md` trong `data/standardized/` bằng `STANDARDIZED_DIR.rglob("*.md")`, gán `metadata.type = "legal"` hoặc `"news"` theo đường dẫn.
  2. `chunk_documents()` (dòng 81-107) — dùng `RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)`.
  3. `embed_chunks()` (dòng 110-128) — `SentenceTransformer(EMBEDDING_MODEL)` rồi `.encode()`.
  4. `index_to_vectorstore()` (dòng 131-154) — `chromadb.PersistentClient(path=CHROMA_DIR)`, `metadata={"hnsw:space": "cosine"}`, `collection.upsert(...)`.
- **⚠️ Sửa trước khi làm gì khác:** dòng 44-45, đổi `CHUNK_SIZE = 500` → `800`, `CHUNK_OVERLAP = 50` → `100` (xem bảng Role 1).
- **Gợi ý thêm (Role 5/6 sẽ cần):** viết luôn `get_collection()` / `get_embedding_model()` dạng singleton (load model 1 lần, cache lại) — Task 5 sẽ `import` lại 2 hàm này (xem comment task5 dòng 36-38: `from .task4_chunking_indexing import get_collection, get_embedding_model`), nếu Trung không tạo 2 hàm này thì Hiển không có gì để import ở Task 5.
- **Test:** `pytest tests/test_individual.py -k TestTask4 -v` (4 test — cần chạy `python -m src.task4_chunking_indexing` trước để sinh `chroma_db/`).

### Task 7 — `src/task7_reranking.py` (phần bắt buộc)
- **Cần sửa:** `rerank_rrf()` (dòng 113-150) — công thức đã viết sẵn nguyên khối trong comment, chỉ cần bỏ comment: `rrf_scores[key] += 1/(k+rank)` cho mỗi ranked list, sort giảm dần, trả `top_k`.
- **Không cần đụng:** `rerank()` dispatcher (dòng 157-184) đã hoàn chỉnh, nhánh `"rrf"` cố ý `raise NotImplementedError` để bắt gọi `rerank_rrf()` trực tiếp — đây là thiết kế đúng, không phải bug.
- **Test:** `pytest tests/test_individual.py -k TestTask7 -v` (dùng dummy data, không phụ thuộc corpus thật nên làm được ngay cả khi Task 4 chưa xong).

### Task 9 — `src/task9_retrieval_pipeline.py` (phần hybrid, phối hợp với Hiển)
- **Cần sửa:** hàm `retrieve()` (dòng 46-106) — code mẫu đầy đủ trong comment dòng 80-105: chạy song song `semantic_search`/`lexical_search` (lấy dư `top_k*2`), merge bằng `rerank_rrf([dense_results, sparse_results], top_k=top_k*2)`, gắn `item["source"]="hybrid"`, rerank lại bằng `rerank()`.
- **Phần threshold/fallback (dòng 97-103) để Hiển tinh chỉnh** — Trung dựng khung, Hiển điền ngưỡng.
- **Test:** `pytest tests/test_individual.py -k TestTask9 -v` (4 test).

### CP5 — tích hợp vào `app.py`
- App **đã gọi sẵn** `generate_with_citation()` (xem ghi chú đầu file) — việc còn lại chỉ là: chạy thử `streamlit run app.py`, xử lý trường hợp lỗi cụ thể hơn ở khối `except Exception as e` (dòng 130-132) nếu muốn UX tốt hơn, và cân nhắc thêm `@st.cache_resource` quanh phần khởi tạo embedding model/ChromaDB client bên trong Task 4/9 nếu thấy mỗi lần chat bị chậm do load lại model.

---

## 🟣 Role 3 — Hiển (Sparse & Rerank Dev)

### Task 2 — `src/task2_crawl_news.py`
- **Trạng thái:** `ARTICLE_URLS = []` (rỗng), `crawl_article()` raise `NotImplementedError`, `crawl_all()` **đã viết xong** (không cần sửa).
- **Cần sửa:**
  1. Điền `ARTICLE_URLS` (dòng 33-37) — danh sách 6 link HUST đã xác minh sẵn trong `data/landing/news/SOURCES.md`, cần ≥5 URL.
  2. Implement `crawl_article()` (dòng 40-63) — bỏ comment code mẫu dùng `AsyncWebCrawler`.
- **Cài trước:** `pip install crawl4ai` **và** `playwright install chromium` (thiếu bước 2 → lỗi `BrowserType.launch: Executable doesn't exist`).
- **Test:** `pytest tests/test_individual.py -k TestTask2 -v` (4 test: ≥5 file, có nội dung, JSON có field `url`).

### Task 5 — `src/task5_semantic_search.py`
- **Trạng thái:** 100% TODO, code mẫu đầy đủ trong comment dòng 35-56.
- **Cần sửa:** `semantic_search()` — embed query bằng model đã dùng ở Task 4 (`from .task4_chunking_indexing import get_collection, get_embedding_model` — **báo Trung tạo sẵn 2 hàm này**, xem mục Role 2), query `collection.query(query_embeddings=..., n_results=top_k)`, convert `score = max(0.0, 1.0 - distance)`, sort giảm dần.
- **Bonus (+5đ, không bắt buộc):** viết thêm HyDE — hàm `_generate_hypothetical_doc(query)` gọi LLM sinh câu trả lời giả định, rồi embed câu đó thay vì embed query gốc. README liệt kê đây là 1 trong 2 lựa chọn bonus "hỗ trợ Semantic Search".
- **Test:** `pytest tests/test_individual.py -k TestTask5 -v` (4 test — cần `chroma_db/` có data từ Task 4, nếu chưa có sẽ tự skip chứ không fail).

### Task 7 — `src/task7_reranking.py` (phần mở rộng, không bắt buộc)
- **Cần sửa (nếu còn thời gian):** `rerank_cross_encoder()` (dòng 20-57) — gọi Jina Reranker API, cần `JINA_API_KEY` trong `.env`. **Không có key thì bỏ qua**, RRF của Trung đã đáp ứng đủ yêu cầu chấm điểm Task 7 — phần này chỉ để hiểu sâu/so sánh lúc demo, không nằm trong bảng điểm bonus cụ thể.
- **Test:** không có test riêng bắt buộc cho cross-encoder trong `test_individual.py`.

### Task 9 — `src/task9_retrieval_pipeline.py` (phần threshold, phối hợp với Trung)
- **Cần sửa:** hằng số `SCORE_THRESHOLD` (dòng 41, hiện = `0.3`) và đảm bảo logic dòng 97-103 dùng **`dense_results[0]["score"]`** (điểm cosine gốc từ Task 5) để so sánh — **KHÔNG** dùng điểm sau `rerank_rrf` (luôn ≈0.016 bất kể liên quan hay không, đã cảnh báo 3 chỗ trong code: task7 dòng 11-14, task9 dòng 14-25, và README).
- **Cách tự đo ngưỡng cho corpus HUST:** chạy vài query chắc chắn liên quan (vd "học phí Bách Khoa Hà Nội") và vài query rác (vd "xyzabc123nonsense") thẳng qua `semantic_search()`, xem khoảng điểm 2 nhóm, chọn ngưỡng nằm giữa. Đừng copy nguyên `0.48` — đó là số đo trên corpus/embedding khác.
- **Test:** `pytest tests/test_individual.py -k TestTask9 -v`, đặc biệt `test_fallback_logic_exists`.

### CP5 — `app.py`
- Slider `top_k` **đã có sẵn** (dòng 57) — không cần làm lại. Nếu còn thời gian: bổ sung hiển thị thông tin kiến trúc chi tiết hơn dòng 60-61, hoặc giúp Sơn chạy RAGAS (việc UI ở đây đã gần xong sẵn trong starter).

---

## 🟢 Role 4 — Đức (Frontend & Chatbot Dev)

### Task 6 — `src/task6_lexical_search.py`
- **Trạng thái:** `CORPUS = []` (rỗng), `build_bm25_index()` và `lexical_search()` đều TODO, code mẫu đầy đủ trong comment.
- **Cần sửa:**
  1. Nạp `CORPUS` (dòng 21) — tái dùng `load_documents()`/chunks từ Task 4 thay vì đọc lại từ đầu.
  2. `build_bm25_index()` (dòng 24-39) — `BM25Okapi(tokenized_corpus)`, tokenize đơn giản `content.lower().split()`.
  3. `lexical_search()` (dòng 42-76) — `bm25.get_scores(tokenized_query)`, lấy top_k bằng `np.argsort(scores)[::-1]`.
- **⚠️ Gotcha:** tokenize `CORPUS` lúc build index phải **giống hệt cách tokenize query** lúc search (cùng lowercase/split), lệch cách tokenize → BM25 lệch điểm không báo lỗi.
- **Bonus (+5đ):** thêm `TfidfVectorizer` (sklearn) song song BM25 và giải thích được cơ chế lúc demo.
- **Test:** `pytest tests/test_individual.py -k TestTask6 -v` (4 test).

### Task 8 — `src/task8_pageindex_vectorless.py`
- **Cần sửa:**
  1. `upload_documents()` (dòng 35-53) — đọc `.md` từ `data/standardized/`, **PageIndex chỉ nhận PDF** (không nhận .md trực tiếp) → convert tạm bằng `fpdf2` trước khi `client.submit_document()`. Nên cache `doc_id` trả về vào 1 file JSON (vd `pageindex_doc_ids.json`) để không upload lại mỗi lần chạy.
  2. `pageindex_search()` (dòng 56-96) — `submit_query()`, poll `get_retrieval()` tới khi `status == "completed"`, parse `retrieval["retrieved_nodes"][i]["relevant_contents"]`.
- **⚠️ Gotcha quan trọng (ghi ngay trong file dòng 19-22):** API `/retrieval` đã deprecated nhưng vẫn hoạt động — **phải `print(json.dumps(response))` xem schema thật trước khi viết code parse**, đừng đoán theo code mẫu cũ trong comment vì response thật có thể khác.
- **Cần:** đăng ký `PAGEINDEX_API_KEY` tại pageindex.ai, điền vào `.env`.
- **Test:** `pytest tests/test_individual.py -k TestTask8 -v` (2 test, tự skip nếu key lỗi/chưa có — không chặn điểm các task khác).

### Task 10 — `src/task10_generation.py`
- **Trạng thái:** `SYSTEM_PROMPT`, `TOP_K=5`, `TOP_P=0.9`, `TEMPERATURE=0.3` **đã viết sẵn kèm giải thích** — không cần sửa trừ khi muốn tinh chỉnh.
- **Cần sửa 3 hàm:**
  1. `reorder_for_llm()` (dòng 63-88) — công thức có sẵn trong comment: `front = chunks[::2]; back = chunks[1::2]; return front + back[::-1]`.
  2. `format_context()` (dòng 95-117) — mỗi chunk format kèm `[Document i | Source: ... | Type: ...]` để LLM cite được.
  3. `generate_with_citation()` (dòng 124-183) — `retrieve()` (Task 9) → `reorder_for_llm()` → `format_context()` → build prompt → gọi OpenRouter qua `OpenAI(api_key=..., base_url="https://openrouter.ai/api/v1")`.
- **Cần chọn:** `LLM_MODEL` (dòng 41, hiện để `"openai/gpt-4o-mini"` — trả phí) — đổi sang model `:free` trên OpenRouter nếu chưa có credit, vd `inclusionai/ling-3.0-flash:free` (gợi ý trong `checkpoint_timer.html`). Free tier giới hạn 50 request/ngày **cho cả tài khoản**.
- **Test:** `pytest tests/test_individual.py -k TestTask10 -v` (3 test — test cuối tự skip nếu thiếu API key, không chặn điểm).

### CP5 — `app.py` (đã có sẵn phần lớn UI)
- **Đã xong sẵn, không cần làm lại:** sidebar, slider `top_k`, render lịch sử chat, expander nguồn tham khảo kèm score (xem ghi chú đầu file).
- **Việc thật sự cần làm:**
  1. Cập nhật `suggestions` (dòng 44-50) — hiện là câu hỏi mẫu RMIT ("Học phí tại RMIT Vietnam...", "Cách đăng ký học phần qua myRMIT?"...) → đổi sang câu hỏi thật về HUST.
  2. Test toàn bộ luồng chat bằng `streamlit run app.py` sau khi Task 10 xong.
  3. Nếu còn thời gian: polish thêm (nút xoá lịch sử chat, loading state đẹp hơn) — phần này tính vào bonus "UI/UX chất lượng" (+3đ).
- **CP6:** trực tiếp thao tác live demo trên máy chiếu — chuẩn bị sẵn 3-4 câu hỏi demo hay nhất.

---

## 🟡 Role 5 — Sơn (Evaluation & QA Engineer)

### Task 3 — `src/task3_convert_markdown.py`
- **Cần sửa:** `convert_legal_docs()` (dòng 28-44) và `convert_news_articles()` (dòng 47-68) — cả 2 đều có code mẫu đầy đủ trong comment, chỉ cần bỏ comment: `MarkItDown().convert(str(filepath))`, lưu `result.text_content` vào `.md`; với news thì đọc JSON, ghép header (title/url/date_crawled) + `content_markdown`.
- **Cài trước:** `pip install "markitdown[pdf]"` — thiếu extra `[pdf]` sẽ lỗi `MissingDependencyException` khi convert PDF (JSON vẫn convert bình thường).
- **Test:** `pytest tests/test_individual.py -k TestTask3 -v` (4 test).

### QA xuyên suốt CP2-CP4
Sau mỗi checkpoint, chạy test tương ứng để chặn lỗi sớm thay vì dồn tới CP4 mới phát hiện:
```bash
pytest tests/test_individual.py -k "TestTask4 or TestTask5 or TestTask6" -v   # cuối CP2
pytest tests/test_individual.py -k "TestTask7 or TestTask8" -v               # cuối CP3
pytest tests/test_individual.py -v                                           # cuối CP4 — kỳ vọng 35 passed
```

### CP5 — `group_project/evaluation/`
- **`golden_dataset.json`:** hiện chỉ có **3 câu mẫu về RMIT** (không dùng được vì đổi corpus sang HUST) — cần viết lại **≥15 câu** theo đúng schema đang dùng (`question`, `expected_answer`, `expected_context`), nội dung bám sát PDF/bài viết thật đã thu thập ở Task 1-2 để `expected_context` chính xác.
- **`eval_pipeline.py`:** `load_golden_dataset()` **đã xong**, cần sửa 3 hàm còn lại:
  1. Chọn 1 trong `evaluate_with_deepeval()` / `evaluate_with_ragas()` / `evaluate_with_trulens()` (dòng 39-151) — khuyến nghị **RAGAS** vì đã có sẵn trong `requirements.txt` (`ragas==0.1.21`), 2 framework kia phải tự cài thêm.
  2. `compare_configs()` (dòng 158-181) — so sánh ≥2 config, gợi ý có sẵn trong comment: `hybrid+rerank` vs `dense_only`.
  3. `export_results()` (dòng 188-204) — ghi kết quả vào `results.md` (đã có khung sẵn, xem dưới).
- **⚠️ Gotcha (ghi ngay trong file dòng 14-19):** RAGAS gọi LLM **rất nhiều lần** (nhiều lần/metric/câu hỏi, không phải 1 lần/câu) — OpenRouter free tier giới hạn **50 request/ngày cho cả tài khoản** (đổi model free khác hay tạo key mới KHÔNG reset quota). Nếu chạy full 15+ câu bị 429 giữa chừng, giảm xuống 5 câu để test trước khi chạy full.
- **`results.md`:** **đã có sẵn khung đầy đủ** (bảng metric, A/B comparison, worst performers, recommendations) — chỉ cần điền số thật vào, không cần dựng lại cấu trúc.

### CP6
- Báo cáo bảng điểm RAGAS + phân tích A/B (Hybrid vs Dense-only) trước lớp.

---

## Checklist chạy test theo từng checkpoint

```bash
# CP1 — cuối buổi thu thập data
pytest tests/test_individual.py -k "TestTask1 or TestTask2 or TestTask3" -v

# CP2 — chunking/indexing/search cơ bản
pytest tests/test_individual.py -k "TestTask4 or TestTask5 or TestTask6" -v

# CP3 — reranking/fallback
pytest tests/test_individual.py -k "TestTask7 or TestTask8" -v

# CP4 — mốc 50đ cá nhân, bắt buộc 35/35 passed
pytest tests/test_individual.py -v
```
