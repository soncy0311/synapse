"""HWP 5.0 파일 파서."""

import struct
import zlib
from pathlib import Path

import olefile

HWPTAG_PARA_TEXT = 67

# 컨트롤 문자 분류 (HWP 5.0 스펙)
# Char 타입: 1 WCHAR (2 bytes)
# Inline/Extended 타입: 8 WCHARs (16 bytes)
_INLINE_CONTROLS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 19, 20}
_EXTENDED_CONTROLS = {11, 12, 14, 15, 16, 17, 18, 21, 22, 23}


def parse(path: str | Path) -> str:
    """HWP 파일에서 텍스트를 추출한다."""
    ole = olefile.OleFileIO(str(path))
    try:
        header = ole.openstream("FileHeader").read()
        flags = struct.unpack_from("<I", header, 36)[0]
        compressed = bool(flags & 0x01)

        texts: list[str] = []
        section = 0
        while ole.exists(f"BodyText/Section{section}"):
            raw = ole.openstream(f"BodyText/Section{section}").read()
            if compressed:
                raw = zlib.decompress(raw, -15)
            texts.extend(_extract_text_from_records(raw))
            section += 1

        return "\n".join(texts)
    finally:
        ole.close()


def _extract_text_from_records(data: bytes) -> list[str]:
    """바이너리 레코드 스트림에서 PARA_TEXT 레코드의 텍스트를 추출한다."""
    texts: list[str] = []
    pos = 0
    while pos + 4 <= len(data):
        header = struct.unpack_from("<I", data, pos)[0]
        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        pos += 4

        if size == 0xFFF:
            if pos + 4 > len(data):
                break
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4

        if pos + size > len(data):
            break

        if tag_id == HWPTAG_PARA_TEXT:
            text = _decode_para_text(data[pos : pos + size])
            if text.strip():
                texts.append(text)

        pos += size

    return texts


def _decode_para_text(data: bytes) -> str:
    """HWPTAG_PARA_TEXT 레코드의 바이너리 데이터를 텍스트로 디코딩한다."""
    chars: list[str] = []
    i = 0
    while i + 1 < len(data):
        code = struct.unpack_from("<H", data, i)[0]
        i += 2

        if code in _INLINE_CONTROLS or code in _EXTENDED_CONTROLS:
            # 8 WCHARs 중 첫 번째는 이미 읽음, 나머지 7개(14바이트) 건너뛰기
            if code == 9:
                chars.append("\t")
            i += 14
        elif code == 10:
            chars.append("\n")
        elif code == 13:
            chars.append("\n")
        elif code == 24:
            chars.append("-")
        elif code in (30, 31):
            chars.append(" ")
        elif code < 32:
            pass
        else:
            chars.append(chr(code))

    return "".join(chars)
