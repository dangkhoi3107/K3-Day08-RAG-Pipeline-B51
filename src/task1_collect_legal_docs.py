"""Task 1 - Collect original HUST policy/legal documents.

The Role 2 data source list is documented in SOURCES.md. This script downloads
public PDF documents and stores them in data/landing/legal/.
"""

from pathlib import Path

import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

LEGAL_DOCUMENTS = [
    {
        "url": "https://ctt.hust.edu.vn/Upload/Nguyen%20Quoc%20Dat/files/DTDH_QDQC/Hocphi/Phu%20luc%20TCHP-2020-2021.pdf",
        "filename": "tuition-fee-appendix-hust.pdf",
    },
    {
        "url": "https://ctt.hust.edu.vn/Upload/Nguyen%20Quoc%20Dat/files/DTDH_QDQC/Hoctap/QCDT-2023-upload.pdf",
        "filename": "training-regulation-2023-hust.pdf",
    },
    {
        "url": "https://smse.hust.edu.vn/uploads/smse/tuyen-dung-hoc-bong/2025_11/hust-quy-trinh-sinh-vien-dang-ky-hoc-bong.docx.pdf",
        "filename": "scholarship-process-hust.pdf",
    },
]


def setup_directory() -> None:
    """Create data/landing/legal/ if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Directory ready: {DATA_DIR}")


def download_file(url: str, filename: str) -> Path:
    """Download one public PDF/DOCX file into data/landing/legal/."""
    setup_directory()
    filepath = DATA_DIR / filename

    response = requests.get(
        url,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Day8-RAG-Lab/1.0)"},
    )
    response.raise_for_status()

    filepath.write_bytes(response.content)
    if filepath.stat().st_size <= 1024:
        raise ValueError(f"Downloaded file is too small: {filepath}")

    print(f"Downloaded: {filepath.name} ({filepath.stat().st_size:,} bytes)")
    return filepath


def collect_legal_documents() -> list[Path]:
    """Download the HUST policy documents listed above."""
    return [
        download_file(document["url"], document["filename"])
        for document in LEGAL_DOCUMENTS
    ]


if __name__ == "__main__":
    collect_legal_documents()
