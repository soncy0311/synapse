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

| 명령 | 설명 |
|------|------|
| `/ingest <raw 파일 경로>` | 소스를 읽고 지식 노드를 생성/업데이트 |
| `/search <쿼리>` | 지식 베이스에서 semantic search |
| `/parse <파일 경로>` | HWP, DOCX, PDF에서 텍스트 추출 |
| `/index` | LanceDB 인덱스 구축/갱신 |
| `/update` | docs/ 폴더 및 파일 구조 점검/업데이트 |
| `/lint` | 지식 베이스 건강 상태 점검 및 수정 |

## 디렉토리 구조

```
synapse/
├── raw/           # 원시 소스
│   ├── user/      # 사용자 제공 (불변)
│   └── agents/    # Agent 수집
├── docs/          # 정제된 지식 노드
│   ├── sources/   # 소스 요약
│   ├── entities/  # 엔티티 (도구, 프로젝트 등)
│   ├── concepts/  # 개념
│   └── analyses/  # 비교 분석, 종합
├── lib/           # 파일 파서
├── scripts/       # 인덱싱, 검색 스크립트
└── .lancedb/      # 검색 인덱스 (.gitignore)
```

## Roadmap

- [ ] Codex 연동 지원 (Codex를 사용하게 되면 업데이트할 예정)

## License

이 프로젝트는 [MIT + Commons Clause](./LICENSE) 라이선스로 배포됩니다. 자유롭게 사용, 수정, 배포할 수 있지만, 이 소프트웨어를 판매하거나 유료 서비스의 핵심 기능으로 제공하여 수익을 창출하는 것은 금지됩니다.
