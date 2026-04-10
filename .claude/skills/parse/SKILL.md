---
name: parse
model: sonnet
description: HWP, DOCX, PDF 등 바이너리 파일에서 텍스트를 추출한다. "파싱해줘", "텍스트 추출", "parse" 등의 요청에 반응한다.
argument-hint: "<파일 경로>"
---

# Parse

바이너리 파일(HWP, DOCX, PDF)에서 텍스트를 추출하는 skill이다. 추출된 텍스트는 그대로 출력하거나, markdown 파일로 저장하여 `/ingest` 워크플로우에 연결할 수 있다.

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

지정된 파일이 존재하는지, 지원하는 확장자인지 확인한다.

```bash
ls -la <파일 경로>
```

### Step 2: 텍스트 추출

lib/ 파서를 사용하여 텍스트를 추출한다:

```bash
poetry run python -c "from lib import parse; print(parse('<파일 경로>'))"
```

### Step 3: 결과 처리

추출된 텍스트를 사용자에게 출력한다.

사용자가 저장을 원하면 raw/ 디렉토리에 markdown 파일로 저장한다:

- 파일명 형식: `{날짜}_{원본파일명_slug}.md`
- 저장 위치: 원본이 `raw/user/`에 있으면 같은 디렉토리에, `raw/agents/`에 있으면 같은 디렉토리에 저장
- 저장 후 `/ingest`로 연결하여 지식 노드로 정제할지 사용자에게 제안

### Step 4: Ingest 연결 (선택)

사용자가 원하면 추출된 텍스트를 바로 ingest 워크플로우로 연결한다:

```
/ingest <저장된 markdown 파일 경로>
```
