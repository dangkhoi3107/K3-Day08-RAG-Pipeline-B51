# Nguồn Dữ Liệu — Task 1 (Legal PDFs)

> Briefing cho **Role 2 (Trung) — Data & Dense Search Dev**. Chủ đề: **Đại học Bách Khoa Hà Nội (HUST — hust.edu.vn)**.

---

## ⚠️ Lưu ý quan trọng trước khi làm

Repo hiện tại (`README.md`, docstring trong `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`) đang ghi chủ đề mẫu là **RMIT Vietnam**. Nhóm đã quyết định đổi sang **Bách Khoa Hà Nội** — điều này **an toàn về mặt chấm điểm** (test suite `tests/test_individual.py` chỉ kiểm tra số lượng file/định dạng, không assert nội dung cụ thể phải là RMIT). Nhưng cần:

1. Cả nhóm thống nhất dùng chung 1 trường (tránh Role 2 crawl HUST, Role 3 crawl RMIT).
2. Role 1 (Khôi) cập nhật lại mục "Chủ Đề Dữ Liệu" trong `README.md` gốc cho khớp, tránh nhầm lẫn khi chấm/demo.

---

## 📄 Danh sách PDF cần tải (Task 1 — tối thiểu 3 file)

| # | Chủ đề | Tên file gốc | Tên file nên đặt lại | Link tải |
|---|--------|-------------|----------------------|----------|
| 1 | Học phí | Phụ lục TCHP 2020-2021 | `tuition-fee-appendix-hust.pdf` | [Phu luc TCHP-2020-2021.pdf](https://ctt.hust.edu.vn/Upload/Nguyen%20Quoc%20Dat/files/DTDH_QDQC/Hocphi/Phu%20luc%20TCHP-2020-2021.pdf) |
| 2 | Đăng ký học phần / Quy chế đào tạo | Quy chế đào tạo 2023 | `training-regulation-2023-hust.pdf` | [QCDT-2023-upload.pdf](https://ctt.hust.edu.vn/Upload/Nguyen%20Quoc%20Dat/files/DTDH_QDQC/Hoctap/QCDT-2023-upload.pdf) |
| 3 | Học bổng | Quy trình SV đăng ký học bổng (11/2025) | `scholarship-process-hust.pdf` | [hust-quy-trinh-sinh-vien-dang-ky-hoc-bong.pdf](https://smse.hust.edu.vn/uploads/smse/tuyen-dung-hoc-bong/2025_11/hust-quy-trinh-sinh-vien-dang-ky-hoc-bong.docx.pdf) |
| 4 *(khuyến khích, không bắt buộc)* | Tuyển sinh | QĐ phê duyệt thông tin tuyển sinh 2025 | `admission-info-decision-2025-hust.pdf` | [qd-phe-duyet-thong-tin-tuyen-sinh-nam-2025.pdf](https://www.hust.edu.vn/uploads/sys/tuyen-sinh/2025_06/qd-phe-duyet-thong-tin-tuyen-sinh-nam-2025-10.06.2025_1.pdf) |

**File #1** hơi cũ (niên khoá 2020-2021) — nếu tìm được bản học phí mới hơn trên `ctt.hust.edu.vn` thì ưu tiên thay thế, không bắt buộc vì test chỉ kiểm tra file tồn tại + dung lượng >1KB.

### Không tìm thấy: Quy định ký túc xá dạng PDF

HUST không có 1 file PDF quy chế ký túc xá độc lập công khai — chỉ có trang HTML:
[Đăng ký ở Ký túc xá](https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=35416)

→ Chuyển trang này cho **Hiển (Role 3 — Task 2, crawl bằng Crawl4AI)** thay vì Role 2, vì Task 1 chỉ nhận PDF/DOCX.

---

## ✅ Việc cần làm (Role 2 — Trung)

1. Tải 3-4 file PDF ở bảng trên, đổi tên như cột "Tên file nên đặt lại" (không dấu, rõ nghĩa).
2. Copy vào `data/landing/legal/`.
3. Chạy: `python -m src.task1_collect_legal_docs` (hoặc set up hàm `download_file()` để tự động tải nếu muốn).
4. Kiểm tra nhanh: `pytest tests/test_individual.py -k TestTask1 -v` → phải pass 3/3 test.

---

## 📚 Tham khảo thêm (nếu cần bổ sung nguồn)

- Trang tổng học phí: https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=36860
- Trang quy chế (danh sách đầy đủ): https://ctt.hust.edu.vn/DisplayWeb/DisplayQuyChe?tag=%C4%90T%C4%90H&page=3
- Trang học bổng cao học/NCS: https://ts.hust.edu.vn/p/quy-dinh-xet-duyet-va-cap-hoc-bong-cho-hoc-vien-cao-hoc-nghien-cuu-sinh-ap-dung-tu-nam-2022-2023
