---
name: ingest
model: opus
effort: max
description: raw/ 소스를 읽고 docs/에 정제된 지식 노드를 생성/업데이트한다. "수집해줘", "ingest", "이 문서 정리해줘" 등의 요청에 반응한다.
argument-hint: "<raw 파일 경로 또는 주제>"
---

# Ingest

raw/ 소스를 읽고 docs/에 정제된 지식 노드를 생성/업데이트하는 skill이다.

## 사용법

```
/ingest raw/agents/2026-04-10_research.md
/ingest raw/user/article.md
```

## Instructions

### Step 1: 소스 읽기

지정된 raw 파일을 읽고 핵심 내용을 파악한다.

**바이너리 파일(.hwp, .docx, .pdf)인 경우** lib/ 파서를 사용하여 텍스트를 추출한다:

```bash
poetry run python -c "from lib import parse; print(parse('<파일 경로>'))"
```

### Step 2: 기존 지식 확인

```bash
make search Q="<소스의 핵심 주제>" OPTS="--fanout --json"
```

기존에 관련 노드가 있는지 확인한다.

### Step 3: 노드 생성/업데이트

#### 노드 형식

모든 docs/ 파일은 다음 YAML frontmatter를 포함해야 한다:

```yaml
---
id: "고유 식별자 (kebab-case)"
title: "페이지 제목"
type: "source | entity | concept | analysis"
tags: ["태그1", "태그2"]
links:
  - target: "연결된 노드 id"
    relation: "relates_to | depends_on | contradicts | extends | part_of"
sources:
  - "raw/파일경로"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
summary: "한 줄 요약 (embedding 대상 및 검색에 사용)"
status: "draft | active | stale | archived"
---
```

#### 필드 규칙

| 필드 | 필수 | 설명 |
|------|------|------|
| `id` | Y | 전역 고유. kebab-case. 파일명과 동일해야 함. 변경 시 모든 참조 업데이트 필요 |
| `title` | Y | 사람이 읽을 수 있는 제목 |
| `type` | Y | `source`, `entity`, `concept`, `analysis` 중 하나 |
| `tags` | Y | 분류 태그 배열. 최소 1개 |
| `links` | N | 관련 노드. target은 대상 노드의 id, relation은 관계 유형 |
| `sources` | N | 이 노드의 근거가 되는 raw/ 파일 경로 |
| `created` | Y | 생성일 |
| `updated` | Y | 최종 수정일 |
| `summary` | Y | 한 줄 요약. embedding 대상 및 검색에 사용 |
| `status` | Y | 노드 상태 |

#### 파일명 규칙

- 파일명(확장자 제외)은 반드시 frontmatter `id`와 동일해야 한다.
  - 예: `id: "world-model"` → `docs/concepts/world-model.md`
  - Obsidian이 `[[wikilink]]`를 파일명으로 resolve하므로, 이 일치가 필수이다.

#### 본문 규칙

- 다른 노드를 참조할 때 `[[node-id]]` wikilink 문법을 사용한다.
- 별칭이 필요하면 `[[node-id|표시 텍스트]]` 형식을 사용한다.
- wikilink와 frontmatter links는 **양방향 일관성**을 유지해야 한다:
  - frontmatter `links`에 있는 모든 target은 본문에 `[[target]]` wikilink가 존재해야 한다.
  - 본문에 `[[node-id]]`가 있으면 frontmatter `links`에도 해당 target이 존재해야 한다.
- 본문 내 인용은 `> 출처: raw/파일경로` 형식으로 표기한다.
- 본문 **마지막에 "관련 노드" 섹션**을 반드시 포함한다. frontmatter links의 모든 target을 wikilink로 나열한다:
  ```markdown
  ## 관련 노드

  - [[target-id]] — 한 줄 설명
  ```
  - 본문 중간에 이미 inline으로 참조한 노드도 "관련 노드" 섹션에 중복 나열한다.
  - 이 섹션은 Obsidian Graph View와 Backlinks의 신뢰성을 보장한다.

#### 노드 타입별 가이드

- **source**: raw/ 파일 하나에 대응하는 요약 페이지. 핵심 주장, 데이터, 인사이트를 정리한다.
- **entity**: 구체적 대상(도구, 라이브러리, 프로젝트, 사람, 조직 등)에 대한 페이지.
- **concept**: 추상적 개념, 패턴, 원칙에 대한 페이지.
- **analysis**: 질의 결과, 비교 분석, 종합 등 Agent가 생성한 파생 지식.

### Step 4: 수집 절차

1. docs/sources/에 소스 요약 페이지를 생성한다 (frontmatter 포함, 파일명 = id).
2. 본문에서 언급된 엔티티/개념을 식별한다.
3. 기존 엔티티/개념 페이지가 있으면 새 정보로 **업데이트**한다.
4. 없으면 새 페이지를 **생성**한다 (파일명 = id).
5. 새로운 정보가 기존 주장과 **모순**되면 → 아래 "모순 및 충돌 처리" 절차를 따른다.
6. 모든 관련 페이지에 wikilink와 frontmatter links를 추가한다.
7. 모든 생성/수정 페이지의 **마지막에 "관련 노드" 섹션**이 있는지 확인하고, 없으면 추가한다.

### Step 5: frontmatter 검증

생성/수정한 모든 노드의 frontmatter가 유효한지 **반드시** 검증한다. 검증을 통과하지 못하면 오류를 수정한 후 다시 검증한다:

```bash
# 단일 파일 검증
make validate-file FILE=docs/sources/new-source.md

# 전체 검증
make validate
```

### Step 6: 인덱스 갱신

검증을 통과한 노드를 LanceDB에 반영한다:

```bash
# 개별 파일 upsert
make index-file FILE=docs/sources/new-source.md
make index-file FILE=docs/entities/updated-entity.md

# 또는 여러 파일이 변경되었으면 전체 재구축
make index
```

## 모순 및 충돌 처리

새로운 정보가 기존 노드의 주장과 충돌하는 경우, **Agent가 임의로 판단하지 않는다.** 반드시 사용자에게 질문하여 사용자의 결정을 통해 정리한다.

### 절차

1. **충돌 발견**: 기존 노드와 모순되는 정보를 발견한다.
2. **사용자에게 보고**: 다음 정보를 명확히 제시한다:
   - 기존 주장: 어떤 노드에서 무엇을 주장하고 있는지
   - 새로운 주장: 새 소스가 무엇을 주장하는지
   - 충돌 지점: 구체적으로 어디가 다른지
3. **사용자 결정 요청**: 다음 중 하나를 선택하도록 요청한다:
   - **새 정보로 대체**: 기존 노드를 수정하고, 이전 주장은 삭제한다
   - **기존 유지**: 새 정보를 반영하지 않는다
   - **병기**: 두 주장을 모두 남기고 출처와 함께 병기한다
4. **결정 반영**: 사용자의 결정에 따라 노드를 수정한다.

### 규칙

- Agent는 모순을 발견해도 **절대 독단적으로 기존 내용을 수정하거나 삭제하지 않는다.**
- 사소한 표현 차이는 충돌이 아니다. 핵심 주장이나 사실관계가 다를 때만 이 절차를 따른다.
- 사용자가 병기를 선택한 경우 frontmatter links에 `contradicts` relation으로 기록한다.
