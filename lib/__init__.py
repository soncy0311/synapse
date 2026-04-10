"""파일 파서 라이브러리."""

from pathlib import Path

from lib.hwp import parse as parse_hwp
from lib.docx import parse as parse_docx
from lib.pdf import parse as parse_pdf

PARSERS = {
    ".hwp": parse_hwp,
    ".docx": parse_docx,
    ".pdf": parse_pdf,
}


def parse(path: str | Path) -> str:
    """파일 확장자에 따라 적절한 파서를 선택하여 텍스트를 추출한다."""
    ext = Path(path).suffix.lower()
    parser = PARSERS.get(ext)
    if parser is None:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")
    return parser(path)
