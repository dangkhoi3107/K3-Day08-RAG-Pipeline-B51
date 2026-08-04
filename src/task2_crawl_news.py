"""
Task 2 — Crawl bài viết/thông báo về dịch vụ đại học.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài viết từ trang công khai của một trường đại học.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
    playwright install chromium   # bắt buộc — pip install crawl4ai KHÔNG tự tải browser binary,
                                   # thiếu bước này sẽ báo lỗi
                                   # "BrowserType.launch: Executable doesn't exist"

Gợi ý chủ đề: thông báo tuyển sinh, sự kiện, dịch vụ thư viện, hỗ trợ sinh viên, học bổng.
"""

import asyncio
import json
import unicodedata
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# Các trang công khai chính thức của Đại học Bách khoa Hà Nội.
ARTICLE_URLS = [
    "https://library.hust.edu.vn/vi/node/1362",  # Dịch vụ phòng học nhóm
    "https://library.hust.edu.vn/vi/node/1363",  # Quy trình đăng ký phòng học nhóm
    "https://library.hust.edu.vn/vi/node/50",  # Câu hỏi thường gặp về thư viện
    "https://library.hust.edu.vn/vi/node/832",  # Lời khuyên cho tân sinh viên
    (
        "https://www.hust.edu.vn/vi/news/hoat-dong-chung/"
        "tieng-noi-sinh-vien-tro-thanh-dong-luc-phat-trien-"
        "cua-dai-hoc-bach-khoa-ha-noi-655741.html"
    ),
    "https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet?baiviet=35416",  # Ký túc xá
]


def _crawl_article_with_requests(url: str) -> dict:
    """Fallback crawler cho môi trường chưa cài Crawl4AI/Chromium."""
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(
        url,
        timeout=(10, 90),
        headers={"User-Agent": "HUST-RAG-Student-Project/1.0"},
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else "Unknown"

    for tag in soup.select("script, style, noscript, svg, nav, header, footer, form"):
        tag.decompose()
    content_root = (
        soup.select_one("article, main, [role='main'], div.col-md-9.col-xs-12")
        or soup.body
        or soup
    )
    heading = content_root.select_one("h1, h2, h3")
    title = heading.get_text(" ", strip=True) if heading else page_title
    lines = [line.strip() for line in content_root.get_text("\n").splitlines()]
    content = unicodedata.normalize(
        "NFC", "\n\n".join(line for line in lines if line)
    )
    if not content:
        raise RuntimeError(f"Trang {url} không có nội dung văn bản")

    return {
        "url": url,
        "title": unicodedata.normalize("NFC", title),
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": content,
    }


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài viết và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        return await asyncio.to_thread(_crawl_article_with_requests, url)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

    if not result.success:
        error = result.error_message or "Unknown crawl error"
        raise RuntimeError(f"Không thể crawl {url}: {error}")

    # Crawl4AI mới trả về MarkdownGenerationResult; các bản cũ trả về str.
    markdown = result.markdown
    if hasattr(markdown, "raw_markdown"):
        markdown = markdown.raw_markdown
    elif markdown is not None and not isinstance(markdown, str):
        markdown = str(markdown)

    if not markdown or not markdown.strip():
        raise RuntimeError(f"Trang {url} không có nội dung markdown")

    metadata = result.metadata or {}
    return {
        "url": url,
        "title": unicodedata.normalize("NFC", metadata.get("title") or "Unknown"),
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": unicodedata.normalize("NFC", markdown),
    }


async def crawl_all():
    """Crawl toàn bộ bài viết trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        try:
            article = await crawl_article(url)
        except Exception as error:
            print(f"  ✗ Skipped: {error}")
            continue

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(
            json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  ✓ Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm trang thông báo/sự kiện trên trang chính thức của trường đại học")
    else:
        asyncio.run(crawl_all())
