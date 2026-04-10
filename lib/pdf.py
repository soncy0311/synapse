"""PDF 파일 파서."""

from pathlib import Path

import pymupdf


def parse(path: str | Path) -> str:
    """PDF 파일에서 텍스트를 추출한다."""
    doc = pymupdf.open(str(path))
    try:
        pages = [page.get_text() for page in doc]
        return "\n".join(pages)
    finally:
        doc.close()
