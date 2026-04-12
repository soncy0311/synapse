---
name: parse
model: sonnet
description: HWP, DOCX, PDF 등 바이너리 파일에서 텍스트를 추출하여 markdown 파일로 저장한다. "파싱해줘", "텍스트 추출", "parse" 등의 요청에 반응한다.
argument-hint: "<파일 경로>"
---

# Parse

바이너리 파일(HWP, DOCX, PDF)에서 텍스트를 추출하여 동일 위치에 markdown 파일로 저장하는 skill이다.

## 사용법

```
/parse raw/user/report.hwp
/parse raw/user/paper.pdf
/parse raw/agents/research.docx
```

## 지원 형식

| 확장자 | 라이브러리 | 설명 |
|--------|-----------|------|
| `.hwp` | olefile | HWP 5.0 (한글 문서) |
| `.docx` | python-docx | Microsoft Word |
| `.pdf` | pymupdf | PDF 문서 |

## Instructions

### Step 1: 파일 확인

지정된 파일이 존재하는지, 지원하는 확장자(`.hwp`, `.docx`, `.pdf`)인지 확인한다.

### Step 2: 텍스트 추출

lib/ 파서를 사용하여 텍스트를 추출한다:

```bash
make parse FILE=<파일 경로>
```

### Step 3: markdown 파일로 저장

추출된 텍스트를 원본과 동일한 디렉토리에 markdown 파일로 저장한다.

- **파일명**: 원본 파일과 동일한 stem에 `.md` 확장자 (예: `report.hwp` → `report.md`)
- **저장 위치**: 원본 파일과 동일한 디렉토리
- 원본의 의미, 구조, 데이터를 최대한 보존한다 (테이블은 markdown 테이블로, 목록은 목록으로)

### Step 4: 원본 삭제

markdown 파일이 정상적으로 저장되었으면 원본 바이너리 파일을 삭제한다 (raw/ remote 업로드 규칙 준수).

### Step 5: 결과 보고

저장된 markdown 파일 경로를 사용자에게 알려주고, `/ingest`로 지식 노드 정제를 진행할지 제안한다.
