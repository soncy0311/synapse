---
name: search
model: opus
effort: auto
description: 지식 베이스에서 semantic search를 수행하고 종합 답변한다. 결과가 부족하면 리서치를 제안한다. "검색해줘", "찾아줘", "알려줘", "분석해줘" 등의 요청에 반응한다.
argument-hint: "<검색 쿼리>"
---

# Search

지식 베이스(docs/)에서 LanceDB 기반 semantic search를 수행하고 종합 답변하는 skill이다. 만족스러운 결과가 없으면 리서치를 제안한다.

## 사용법

```
/search 벡터 데이터베이스
/search 인증 시스템 보안 설계
```

## Instructions

### Step 1: 인덱스 상태 확인

```bash
ls .lancedb/nodes.lance 2>/dev/null
```

인덱스가 없으면 먼저 빌드한다:

```bash
make index
```

### Step 2: Semantic search 실행

**항상 `--fanout --json` 옵션을 사용**하여 연결 노드까지 추적하고 구조화된 결과를 받는다:

```bash
make search Q="<검색 쿼리>" OPTS="--fanout --json"
```

필요에 따라 필터를 추가한다:

```bash
make search Q="<쿼리>" OPTS="--type entity --fanout --json"
make search Q="<쿼리>" OPTS="--tag security --fanout --json"
make search Q="<쿼리>" OPTS="--limit 5 --fanout --json"
```

### Step 3: 결과 분석 및 문서 읽기

1. **results**: 의미적으로 유사한 상위 문서들. 각 결과의 `path`로 원본 markdown을 읽는다.
2. **fanout**: 연결된 노드들. 도메인 구조 파악에 활용한다.

### Step 4: 종합 답변

검색 결과와 읽은 문서를 종합하여 답변한다:

- 관련 노드들의 핵심 내용을 종합
- 노드 간 관계(links, fanout)를 활용한 맥락 제공
- 출처 노드의 path를 명시

가치 있는 분석 결과가 나오면 docs/analyses/에 새 페이지로 저장할지 사용자에게 제안한다.

### Step 5: 결과 부족 시 — 리서치 제안

검색 결과가 없거나 사용자의 질문에 충분히 답변할 수 없는 경우:

1. **사용자에게 보고**: "지식 베이스에 관련 내용이 부족합니다. 리서치를 진행할까요?"
2. **사용자가 승인하면**:
   - 웹 검색 등을 통해 주제에 대한 리서치를 수행한다.
   - 리서치 결과를 `raw/agents/`에 저장한다 (파일명: `{날짜}_{주제_slug}.md`).
   - `/ingest`를 호출하여 리서치 결과를 docs/에 노드로 정제한다.
   - 정제된 노드를 기반으로 사용자에게 답변한다.
3. **사용자가 거부하면**: 현재 보유한 정보 범위 내에서 답변한다.
