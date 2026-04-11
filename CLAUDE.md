# Synapse — AI Agent 기반 지식 관리 시스템

Synapse는 AI Agent가 작성하고 유지하는 개인 지식 베이스이다. 사용자가 소스를 제공하면 Agent가 읽고, 정제하고, 기존 지식과 통합한다. 지식은 상호 연결된 markdown 노드로 관리되며, 한 번 컴파일된 후 점진적으로 갱신된다.

---

## 아키텍처

```
docs/ (markdown 노드) ─── 진실의 원천
      │
      ├──→ LanceDB (vector + metadata)  ─── 파생 인덱스
      │         │
      │         ├── semantic search (BM25 + vector hybrid)
      │         └── metadata 기반 관계 탐색 (links fan-out)
      │
      └──→ ripgrep ─── 정확한 키워드/패턴 매칭 (보조)
```

LanceDB를 검색 + 관계 탐색의 단일 엔진으로 사용한다. Semantic search로 seed 문서를 찾고, metadata의 links로 fan-out하여 도메인을 빠르게 파악한다. ripgrep은 정확한 키워드 매칭이 필요한 경우에만 보조적으로 사용한다.

---

## 디렉토리 구조

```
synapse/
├── CLAUDE.md          # 이 파일. 스키마 및 운영 규칙
├── raw/               # 원시 소스
│   ├── user/          # 사용자가 제공한 소스 (Agent 수정 금지)
│   └── agents/        # Agent가 리서치하여 수집한 소스
├── docs/              # 정제된 지식 노드 (Agent가 소유)
│   ├── sources/       # 소스별 요약 페이지
│   ├── entities/      # 엔티티(도구, 프로젝트, 사람 등) 페이지
│   ├── concepts/      # 개념 페이지
│   └── analyses/      # 질의 결과, 비교, 종합 페이지
├── lib/               # 파일 파서 라이브러리 (HWP, DOCX, PDF)
├── scripts/           # 유틸리티 스크립트 (인덱싱, 검색 등)
└── .lancedb/          # LanceDB 데이터 디렉토리 (.gitignore)
```

### raw/ — 원시 소스

**raw/user/**: 사용자가 직접 제공한 소스. Agent는 읽기만 하며 **절대 수정하지 않는다.**

**raw/agents/**: Agent가 리서치를 통해 수집한 소스. Agent가 자유롭게 추가할 수 있다.

**공통 규칙:**
- 파일명 형식: `{날짜}_{제목_slug}.{확장자}` (예: `2026-04-10_node-graph-architecture.md`)
- 서브디렉토리로 추가 분류 가능: `raw/agents/articles/`, `raw/user/notes/` 등

### docs/ — 정제된 지식 노드

Agent가 raw 소스로부터 정제하여 작성한 markdown 파일들. Agent가 이 계층을 완전히 소유한다.

### .lancedb/ — 검색 인덱스

LanceDB의 데이터 디렉토리. docs/ 파일에서 파생되므로 Git에 포함하지 않는다 (.gitignore). 언제든 docs/에서 재구축 가능하다.

---

## Skills

- `/search <쿼리>` — semantic search + fan-out. 결과 부족 시 리서치를 제안한다.
- `/ingest <raw 파일 경로>` — raw/ 소스를 읽고 docs/에 지식 노드를 생성/업데이트한다.
- `/parse <파일 경로>` — HWP, DOCX, PDF 등 바이너리 파일에서 텍스트를 추출한다.
- `/index` — docs/ 파일들로부터 LanceDB 인덱스를 구축/갱신한다. docs/ 문서가 생성/수정/삭제되거나 git pull 후 docs/ 변경이 있으면 반드시 실행한다.
- `/update` — docs/ 폴더 및 파일 구조를 점검하고, 새로운 폴더나 파일 구조가 필요한지 파악하여 업데이트한다.
- `/lint` — 지식 베이스의 건강 상태를 점검하고 문제를 수정한다.

---

## 핵심 원칙

1. **파일이 진실의 원천**: LanceDB 인덱스는 docs/ 파일에서 파생된다. 인덱스가 깨져도 원본에서 재생성 가능하다.
2. **raw/user는 불변**: Agent는 raw/user/ 파일을 절대 수정하지 않는다. raw/agents/에는 자유롭게 추가할 수 있다.
3. **점진적 통합**: 새 소스는 기존 지식과 통합된다. 고립된 요약이 아니라, 위키 전체가 업데이트된다.
4. **모순은 사용자가 결정**: 충돌 발견 시 Agent가 임의로 판단하지 않고, 반드시 사용자에게 보고하여 결정을 받는다.
5. **복리 성장**: 질의 결과도 위키에 저장하여 지식이 축적된다.
6. **메타데이터 일관성**: frontmatter 스키마를 엄격히 지킨다. 웹 시각화에 활용된다.
7. **로그는 Git**: 별도 로그 파일을 유지하지 않는다. 모든 변경 이력은 Git 커밋으로 추적한다.
8. **커밋 메시지**: 제목은 영어로 간결하게(50자 이내), 본문은 한국어로 변경 내용을 구체적으로 설명하여 업데이트 노트로 활용할 수 있도록 작성한다.
