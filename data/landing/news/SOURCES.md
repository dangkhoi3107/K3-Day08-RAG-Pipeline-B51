# Nguồn Dữ Liệu — Task 2 (Crawl News)

> Briefing cho **Role 3 (Hiển) — Sparse & Rerank Dev**. Chủ đề: **Đại học Bách Khoa Hà Nội (HUST — hust.edu.vn)**.
> Đồng bộ với `data/landing/legal/SOURCES.md` (Task 1, Trung đã làm xong — xem `TASK_ASSIGNMENT.md`).

---

## 📄 Danh sách bài viết cần crawl (Task 2 — tối thiểu 5 bài)

| # | Chủ đề | Tiêu đề | Link |
|---|--------|--------|------|
| 1 | Hỗ trợ sinh viên / Ký túc xá | Đăng ký ở Ký túc xá | [ctt.hust.edu.vn/.../baiviet=35416](https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=35416) |
| 2 | Thư viện | Giới thiệu Thư viện Tạ Quang Bửu | [library.hust.edu.vn/vi/node/312](https://library.hust.edu.vn/vi/node/312) |
| 3 | Thư viện | Quy trình sử dụng phòng đọc | [library.hust.edu.vn/vi/node/471](https://library.hust.edu.vn/vi/node/471) |
| 4 | Sự kiện | Mời tham dự Lễ tốt nghiệp tháng 5/2026 | [hust.edu.vn/.../moi-tham-du-le-tot-nghiep-thang-5-2026](https://hust.edu.vn/vi/su-kien-noi-bat/thong-bao-chung/moi-tham-du-le-tot-nghiep-thang-5-2026-654811.html) |
| 5 | Học bổng | Học bổng trao đổi sinh viên kỳ Thu 2026 — ĐH Ulsan (Hàn Quốc) | [hust.edu.vn/.../hoc-bong-trao-doi-sinh-vien-ky-thu-2026-tai-dai-hoc-ulsan](https://hust.edu.vn/vi/hop-tac-doi-ngoai/tin-tuc-hoc-bong/thong-bao-hoc-bong-trao-doi-sinh-vien-ky-thu-2026-tai-dai-hoc-ulsan-han-quoc-653432.html) |
| 6 *(dự phòng)* | Học bổng | Chương trình giới thiệu Học bổng INTENSE (Đài Loan) 2026 | [hust.edu.vn/.../hoc-bong-intense-dai-loan-2026](https://hust.edu.vn/vi/hop-tac-doi-ngoai/tin-tuc-hoc-bong/thong-bao-chuong-trinh-gioi-thieu-hoc-bong-intense-dai-loan-2026-653419.html) |

Đủ 4 mảng chủ đề lab gợi ý: sự kiện, thư viện, hỗ trợ sinh viên, học bổng. Lấy 5/6, giữ link #6 dự phòng nếu 1 link nào lỗi lúc crawl.

⚠️ **Sửa trong `TASK_ASSIGNMENT.md` trước đó có lỗi:** bản nháp đầu ghi nhầm gợi ý "Library news / Book a study room" là nguồn HUST — thực ra 2 link đó là của **RMIT Vietnam** (còn sót lại từ lúc research chủ đề cũ trước khi đổi sang HUST). Đã sửa, dùng bảng trên làm chuẩn.

---

## ✅ Việc cần làm (Role 3 — Hiển)

1. Điền 5-6 URL trên vào `ARTICLE_URLS` trong `src/task2_crawl_news.py` (dòng 33-37).
2. Cài: `pip install crawl4ai` rồi **bắt buộc** `playwright install chromium` (thiếu bước này → lỗi `BrowserType.launch: Executable doesn't exist`).
3. Implement `crawl_article()` (comment mẫu có sẵn dòng 40-63 trong file) — dùng `AsyncWebCrawler`, trả về `{url, title, date_crawled, content_markdown}`.
4. Chạy: `python -m src.task2_crawl_news` → sinh file `article_01.json` ... trong `data/landing/news/`.
5. Kiểm tra: `pytest tests/test_individual.py -k TestTask2 -v` → phải pass 4/4 test.
