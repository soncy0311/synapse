# Synapse

[![License: MIT + Commons Clause](https://img.shields.io/badge/License-MIT%20%2B%20Commons%20Clause-blue.svg)](./LICENSE)

AI Agent가 작성하고 유지하는 개인 지식 베이스.

소스를 제공하면 Agent가 읽고, 정제하고, 기존 지식과 통합한다. 지식은 상호 연결된 markdown 노드로 관리되며, LanceDB 기반 semantic search로 빠르게 탐색한다.

## 기술 스택

| 구성 요소 | 기술 |
|----------|------|
| Runtime | Python 3.13 |
| 패키지 관리 | Poetry |
| 검색 엔진 | LanceDB (BM25 + vector hybrid search) |
| 임베딩 (local) | intfloat/multilingual-e5-small (384차원) |
| 임베딩 (cloud) | Gemini Embedding 2 |
| 파서 | HWP, DOCX, PDF (lib/) |
| 인터페이스 | Claude Code Skills |

## 설치

```bash
# Python 3.13 필요
make install

# 환경 변수 설정
cp env/.env.example env/.env
# env/.env 파일을 열어 필요한 값을 설정
```

### Embedding Provider

`env/.env`의 `VECTOR_DB_PROVIDER`로 선택:

| Provider | 모델 | 비용 | 설정 |
|----------|------|------|------|
| `local` (기본) | intfloat/multilingual-e5-small | 무료 | 없음 (첫 실행 시 ~470MB 모델 다운로드) |
| `gemini` | gemini-embedding-2-preview | API 과금 | `GEMINI_API_KEY` 필요 |

## 사용법

Claude Code에서 slash command로 사용한다.

### `/ingest <raw 파일 경로>` — 소스 수집

raw/ 소스를 읽고 docs/{sources,entities,concepts,analyses}/에 지식 노드를 생성/업데이트한다. 기존 지식과 통합하고, 모순 발견 시 사용자에게 보고한다. 바이너리 파일은 자동으로 `/parse`를 거친 후 수집한다.

```
/ingest raw/user/article.md          # 사용자가 제공한 소스 수집
/ingest raw/agents/2026-04-10_research.md   # Agent가 리서치한 소스 수집
```

### `/ideation [주제 slug]` — 아이디에이션 정리

사용자와의 탐색적 대화를 보존한다. 대화 원본을 `raw/agents/`에 저장하고, 결정·제약·열린 질문을 정제하여 `docs/note/`에 아이디에이션 노트로 남긴다. LanceDB에 인덱싱되어 `/search`로 검색된다. **기존 지식 그래프 노드는 수정하지 않고 참조만 한다.**

`/ingest`와의 차이: `/ingest`는 객관적 지식을 그래프에 편입하고 기존 노드를 수정/확장, `/ideation`은 주관적 탐색을 단방향 참조로만 연결.

```
/ideation                              # 현재 대화를 자동 주제 추출로 정리
/ideation 2d-pixel-topdown-pipeline    # 주제 slug 지정
```

### `/search <쿼리>` — 지식 검색

LanceDB semantic search + 연결 노드 fan-out으로 종합 답변한다. 지식 베이스에 관련 내용이 부족하면 웹 리서치를 제안한다.

```
/search 벡터 데이터베이스           # 개념 검색
/search 인증 시스템 보안 설계       # 주제 탐색
```

### `/parse <파일 경로>` — 바이너리 파싱

HWP, DOCX, PDF에서 텍스트를 추출하여 동일 위치에 markdown으로 저장하고, 원본 바이너리를 삭제한다.

```
/parse raw/user/report.hwp      # HWP → report.md
/parse raw/user/paper.pdf       # PDF → paper.md
/parse raw/agents/research.docx # DOCX → research.md
```

### `/index [--file <path>]` — 인덱스 갱신

docs/ 파일로부터 LanceDB 검색 인덱스를 구축/갱신한다. 인자 없이 실행하면 전체 재구축, `--file`로 단일 파일만 upsert할 수 있다.

```
/index                              # 전체 재구축
/index --file docs/entities/lancedb.md   # 단일 파일 upsert
```

### `/update` — 구조 점검

docs/ 폴더 및 파일 구조를 점검하고, 카테고리 포화·빈 디렉토리·파일명 불일치 등 필요한 구조 변경을 제안/실행한다.

```
/update
```

### `/merge [PR 번호...]` — PR 병합

main 대상 PR을 순차 병합하고, 병합 후 지식 베이스 일관성(중복 노드·교차참조 누락·내용 모순)을 점검·수정한다.

```
/merge              # 열린 PR 전체를 순차 병합
/merge 42           # 특정 PR만 병합
/merge 42 45 48     # 지정된 PR들을 순차 병합
```

### `/lint` — 건강 점검

지식 베이스 전반을 점검한다. 모순, stale/고아 노드, 누락된 교차 참조, 인덱스 불일치 등을 발견하고 자동 수정 가능한 항목은 수정, 판단이 필요한 항목은 사용자에게 보고한다.

```
/lint
```


## 디렉토리 구조

```
synapse/
├── raw/           # 원시 소스
│   ├── user/      # 사용자 제공 (불변)
│   └── agents/    # Agent 수집 + 대화 기록
├── docs/          # 정제된 지식 노드 (모두 LanceDB 인덱싱)
│   ├── sources/   # 소스 요약
│   ├── entities/  # 엔티티 (도구, 프로젝트 등)
│   ├── concepts/  # 개념
│   ├── analyses/  # 비교 분석, 종합
│   └── note/      # 아이디에이션 노트 (탐색 단계 기록)
├── lib/           # 파일 파서
├── scripts/       # 인덱싱, 검색 스크립트
└── .lancedb/      # 검색 인덱스 (.gitignore)
```

## Roadmap

- [ ] Codex 연동 지원 (Codex를 사용하게 되면 업데이트할 예정)

## License

이 프로젝트는 [MIT + Commons Clause](./LICENSE) 라이선스로 배포됩니다. 자유롭게 사용, 수정, 배포할 수 있지만, 이 소프트웨어를 판매하거나 유료 서비스의 핵심 기능으로 제공하여 수익을 창출하는 것은 금지됩니다.
