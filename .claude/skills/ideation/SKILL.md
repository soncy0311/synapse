---
name: ideation
model: opus
effort: max
description: 사용자와의 대화를 raw/agents/에 저장하고, 핵심 결정·제약·열린 질문을 docs/note/에 아이디에이션 노트로 정리한다. sources/entities/concepts/analyses는 생성하지 않는다. "아이디에이션 정리해줘", "ideation", "지금 대화 노트로 남겨줘" 등의 요청에 반응한다.
argument-hint: "<주제 slug (선택)>"
---

# Ideation

사용자와의 **탐색적 대화**를 보존하는 경량 skill이다. `/ingest`와 달리 지식 그래프(sources/entities/concepts/analyses)를 건드리지 않고, 대화 원본을 `raw/agents/`에, 정제된 아이디에이션 노트를 `docs/note/`에만 남긴다. 생성된 노트는 LanceDB에 인덱싱되어 `/search` 대상이 된다.

## 언제 사용하나

- 사용자가 **결정을 확정하지 않은 탐색 단계**의 대화를 보존할 때
- `/ingest`로 올리기엔 아직 **지식 그래프에 편입하기 이른** 주관적/잠정적 내용일 때
- **사용자의 제약, 선택, 열린 질문**이 향후 리서치·설계의 맥락이 될 때

**`/ingest`와의 차이**:

| 관점 | `/ideation` | `/ingest` |
|------|------------|-----------|
| 성격 | 주관적 탐색, 결정 중 | 객관적 지식, 정제됨 |
| 출력 | `raw/agents/` + `docs/note/` | `raw/` + `docs/{sources,entities,concepts,analyses}/` |
| 기존 노드 | 참조만 (읽기 전용) | 수정/확장 |
| 인덱싱 | LanceDB 포함 | LanceDB 필수 |
| 충돌 처리 | 사용자 의견으로 기록 | 지식 모순 보고 절차 |

## 사용법

```
/ideation                              # 현재 대화 전체를 자동 주제 추출로 정리
/ideation 2d-pixel-topdown-pipeline    # 주제 slug 지정
```

## Instructions

### Step 1: 주제 slug 결정

- 인자로 주어지면 그대로 사용
- 없으면 대화의 핵심 주제를 kebab-case로 도출 (예: `2d-pixel-topdown-pipeline`, `character-chat-monetization`)
- 파일명에 사용되므로 **영문 kebab-case 필수**

### Step 2: 대화 원본을 raw/agents/에 저장

경로: `raw/agents/YYYY-MM-DD_{topic-slug}-dialogue.md`

**내용 구성**:
- 메타: 날짜, 주제, 형태("사용자-Agent 대화 기록")
- **대화 흐름**: 각 유저 질문(Q1, Q2 …)과 Agent 답변 요약을 순서대로 기록
  - 사용자 발언은 원문 인용
  - Agent 답변은 핵심만 압축 (표/코드 블록은 보존)
- **추출된 사용자 의사결정**: 번호 매긴 리스트
- **열린 질문**: 사용자가 아직 결정하지 못한 항목

raw 파일은 **불변 기록**이다. 이후 생각이 바뀌어도 원본은 남긴다.

### Step 3: docs/note/에 아이디에이션 노트 생성

경로: `docs/note/{topic-slug}.md`

#### Frontmatter 스키마

```yaml
---
id: "주제-slug (파일명과 동일)"
title: "사람이 읽는 제목 — 아이디에이션"
type: "ideation"
group: "note/{카테고리}"
tags: ["태그1", "태그2", ...]
dialogue: "raw/agents/YYYY-MM-DD_{topic-slug}-dialogue.md"
links:
  - "[[기존-노드-id-1]]"
  - "[[기존-노드-id-2]]"
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
status: "exploring | decided | archived"
summary: "한 줄 요약"
---
```

**주의사항**:
- `type`은 **항상 `"ideation"`**
- `group`은 `note/{카테고리}` 형식 (예: `note/gamedev`, `note/infra`) — 검색/시각화 그룹화용
- `dialogue` 필드는 Step 2에서 생성한 raw 파일 경로
- `links`는 기존 지식 노드를 참조 (다른 노드 타입과 동일한 wikilink 배열 — fan-out에서 traversal됨)
- `status`는 `exploring`(탐색 중) / `decided`(결정 완료) / `archived`(보류)

#### 본문 구조

다음 5개 섹션을 순서대로 작성한다.

```markdown
# {제목}

## 목표

사용자가 왜 이 주제를 탐색하는지, 무엇을 달성하려 하는지 한두 단락으로.

## 핵심 아이디어

대화에서 도출된 모든 사고를 담는 섹션. 다음을 포함한다:
- **현재 선택 / 파이프라인**: 이미 채택한 도구, 구조, 방법
- **선택 사항 (옵션 비교)**: 검토한 대안과 트레이드오프
- **비범한 발상 / 메타 통찰**: 단축 경로, 우회 전략, 일반론을 깨는 관점
- **구현 전략**: Phase 분할, 점진적 확장 계획, 핵심 알고리즘 스케치
- **참조 패턴**: 차용한 외부 사례·표준 (예: RPG Maker A2 quadrant 방식)

자유롭게 하위 ### 헤딩으로 분할하되, 모든 사고가 이 섹션 안에 모이도록 한다.

## 주요 결정 및 제약

각 결정마다:
- **결정**: 무엇을 선택했는지
- **이유**: 왜 그 결정을 내렸는지
- **트레이드오프**: 알려진 장단점
- **대응 전략**: 단점을 어떻게 보완하는지

## 추가 과제

체크박스 리스트. 아직 결정·구현되지 않은 항목, 다음 세션에서 다룰 후속 작업.

## 관련 노드

- [[node-id]] — 이 아이디에이션과의 관계 (한 줄 설명)

frontmatter `links`와 본문 `[[wikilink]]`는 **양방향 일관성** 유지 (validator가 체크).
```

### Step 4: 기존 노드는 수정하지 않는다

- `/ingest`와 달리 **기존 sources/entities/concepts/analyses 파일을 편집하지 않는다**
- `links` 필드로 참조만 하고, 대상 노드에는 backlink를 추가하지 않는다 (단방향 참조)
- 단, 아이디에이션이 `decided` 상태로 전환되어 지식화가 필요해지면 그때 `/ingest`를 별도로 실행

### Step 5: 검증

```bash
make validate-file FILE=docs/note/{topic-slug}.md
```

확인 항목:
- `id` = 파일명 (확장자 제외)
- `type` = `"ideation"`
- `status` ∈ `exploring | decided | archived`
- frontmatter `links`의 모든 target이 본문 `[[wikilink]]`에 존재
- 본문에 `## 관련 노드` 섹션 존재

### Step 6: LanceDB 인덱싱

```bash
make index-file FILE=docs/note/{topic-slug}.md
```

이로써 `/search`로 아이디에이션 노트도 검색되고, fan-out으로 연결된 지식 노드까지 탐색 가능.

## 아이디에이션 상태 전이

```
exploring ──(결정 확정)──▶ decided ──(지식화 완료)──▶ archived
                                 │
                                 └─(/ingest로 지식 그래프 편입)
```

- **exploring**: 기본 상태. 결정이 유동적
- **decided**: 주요 결정이 확정됨. 이제 `/ingest`로 지식화 가능
- **archived**: 보류되거나 방향이 바뀌어 더 이상 추적하지 않음

## 산출물 요약

`/ideation` 실행 후:

1. `raw/agents/YYYY-MM-DD_{topic}-dialogue.md` — 대화 원본 (불변)
2. `docs/note/{topic}.md` — 정제된 아이디에이션 노트 (LanceDB 인덱싱, 업데이트 가능)

**건드리지 않는 것**: `docs/sources/`, `docs/entities/`, `docs/concepts/`, `docs/analyses/`
