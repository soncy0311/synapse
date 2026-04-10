---
name: index
model: sonnet
effort: auto
description: LanceDB 인덱스를 구축하거나 갱신한다. "인덱스 갱신", "인덱싱", "re-index" 등의 요청에 반응한다.
argument-hint: "[--file <path>]"
---

# Index

docs/ 마크다운 파일들로부터 LanceDB semantic search 인덱스를 구축/갱신하는 skill이다.

## 사용법

```
/index                # 전체 재구축
/index --file <path>  # 단일 파일 upsert
```

## Instructions

### 전체 재구축

docs/ 전체를 스캔하여 LanceDB 인덱스를 처음부터 재구축합니다:

```bash
make index
```

**언제 사용:**
- 최초 인덱스 생성
- 여러 파일이 동시에 변경된 후
- 인덱스가 손상되었거나 불일치가 의심될 때

### 단일 파일 upsert

특정 파일만 인덱스에 추가/갱신합니다:

```bash
make index-file FILE=docs/entities/lancedb.md
```

**언제 사용:**
- 수집(Ingest) 워크플로우에서 개별 노드를 추가/수정한 직후
- 전체 재구축이 불필요한 소규모 변경 시

### Ingest 워크플로우에서의 사용

새로운 소스를 수집할 때, 다음 순서로 인덱스를 갱신합니다:

1. docs/ 파일 생성/수정 완료
2. 변경된 각 파일에 대해 upsert 실행:
   ```bash
   make index-file FILE=docs/sources/new-source.md
   make index-file FILE=docs/entities/updated-entity.md
   ```
3. 또는 여러 파일이 변경되었으면 전체 재구축:
   ```bash
   make index
   ```

### 주의사항

- `VECTOR_DB_PROVIDER=gemini` 사용 시 `env/.env`에 `GEMINI_API_KEY` 설정 필요.
- 인덱스 데이터는 `.lancedb/`에 저장되며, Git에서 제외된다.
- 인덱스는 docs/ 파일에서 언제든 재생성 가능하다 (파생 데이터).
- frontmatter가 없는 markdown 파일은 건너뛴다.
