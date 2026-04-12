---
name: merge
model: opus
effort: max
description: main 대상 PR을 순차 병합하고 지식 베이스 일관성(중복/교차참조/모순)을 점검·수정한다. "merge", "병합", "PR 합쳐줘" 등의 요청에 반응한다.
argument-hint: "[PR 번호]"
---

# Merge

main 대상 PR을 순차 병합하고 지식 베이스 일관성을 점검·수정하는 skill이다.

## 사용법

```
/merge           # main 대상 모든 열린 PR을 순차 병합
/merge 42        # 특정 PR만 병합
/merge 42 45 48  # 지정된 PR들을 순차 병합
```

## Instructions

### Step 1: 현재 상태 파악

```bash
# 열린 PR 목록 확인
gh pr list --base main --state open

# main 최신화
git fetch origin main
```

인자로 PR 번호가 주어지면 해당 PR만 대상으로 한다. 없으면 main 대상 모든 열린 PR을 대상으로 한다.

### Step 2: 병합 순서 결정

PR이 2개 이상일 때 병합 순서를 결정한다.

1. **파일 겹침 분석**: 각 PR이 수정하는 파일 목록을 비교한다.
   ```bash
   gh pr diff <PR번호> --name-only
   ```
2. **충돌 가능성 평가**: 동일 파일을 수정하는 PR 쌍을 식별한다.
3. **순서 제안**: 충돌 가능성이 낮은 PR부터 병합하는 순서를 제안한다.
4. **사용자 확인**: 제안한 순서를 사용자에게 보여주고 확인을 받는다.

### Step 3: PR별 사전 검토

각 PR에 대해 병합 전 다음을 검토한다:

#### 3-1. diff 분석

```bash
gh pr diff <PR번호>
```

변경된 docs/ 파일 목록과 내용을 파악한다.

#### 3-2. 중복 노드 검색

PR에서 새로 생성하는 docs/ 노드의 id/title을 추출하고, main의 기존 노드와 비교한다:

```bash
# PR이 새로 추가하는 docs/ 파일 확인
gh pr diff <PR번호> --name-only | grep '^docs/'

# 기존 노드에서 유사한 주제 검색
make search Q="<새 노드의 주제>" OPTS="--json"
```

의미적으로 중복될 가능성이 있는 노드 쌍을 식별하여 사용자에게 보고한다.

#### 3-3. Git 충돌 dry-run

```bash
# main에서 임시 브랜치를 만들어 충돌 여부 확인
git checkout -b temp-merge-test origin/main
git merge --no-commit --no-ff origin/<PR-branch>
# 충돌 확인 후 정리
git merge --abort
git checkout -
git branch -D temp-merge-test
```

충돌이 있으면 사용자에게 보고하고 수동 해결이 필요한지 확인한다.

#### 3-4. 문제 발견 시

- **중복 노드 의심**: 사용자에게 보고하고 통합/유지/병기 중 결정을 요청한다.
- **Git 충돌**: 충돌 파일과 내용을 사용자에게 보여주고 해결 방향을 확인한다.
- **문제 없음**: Step 4로 진행한다.

### Step 4: 병합 실행

사용자 확인 후 PR을 병합한다:

```bash
gh pr merge <PR번호> --merge --delete-branch
```

병합 후 로컬 main을 최신화한다:

```bash
git fetch origin main
```

**주의**: 반드시 사용자 확인을 받은 후에만 병합을 실행한다.

### Step 5: 일관성 점검

병합 직후, 새로 추가/수정된 노드를 중심으로 일관성을 점검한다.

#### 5-1. frontmatter 검증

```bash
make validate
```

#### 5-2. 중복 탐지

병합된 PR이 추가한 노드와 기존 노드 간 의미적 중복을 확인한다:

```bash
# 새로 추가된 각 노드에 대해
make search Q="<노드 title/summary>" OPTS="--json"
```

유사도가 높은 노드 쌍을 식별한다.

#### 5-3. 교차 참조 점검

새 노드와 기존 노드 간 누락된 교차 참조를 확인한다:

- 새 노드에서 언급하는 개념이 기존 entity/concept에 이미 있으면 wikilink 추가
- 기존 노드에서 새 노드가 다루는 주제를 언급하고 있으면 wikilink 추가

#### 5-4. wikilink 양방향성

A→B wikilink가 있으면 B의 frontmatter links와 "관련 노드" 섹션에도 A가 있어야 한다:

```bash
# 각 새 노드에 대해 backlink 확인
rg "\[\[<node-id>\]\]" docs/ -l
```

누락된 backlink를 자동 추가한다.

#### 5-5. 관련 노드 섹션

frontmatter `links`에 항목이 있는 노드는 본문 마지막 "관련 노드" 섹션에 links의 모든 항목이 빠짐없이 나열되어야 한다. 누락 시 자동 추가한다.

### Step 6: 모순 탐지

새 노드와 기존 노드 간 내용 모순을 확인한다.

1. 새 노드의 핵심 주장을 파악한다.
2. 관련 기존 노드의 내용을 읽고 비교한다.
3. 핵심 사실관계가 충돌하는 경우 사용자에게 보고한다.

**모순 처리 규칙:**
- Agent는 모순을 발견해도 **절대 독단적으로 기존 내용을 수정하거나 삭제하지 않는다.**
- 사소한 표현 차이는 충돌이 아니다. 핵심 주장이나 사실관계가 다를 때만 사용자에게 보고한다.
- 사용자에게 다음 선택지를 제시한다:
  - **새 정보로 대체**: 기존 노드를 수정
  - **기존 유지**: 새 정보 반영하지 않음
  - **병기**: 두 주장을 출처와 함께 병기
- 병기 시 양쪽 노드의 "관련 노드" 섹션에 상대 노드를 추가하고, 모순/충돌 관계임을 명시한다.

### Step 7: 수정 커밋

Step 5~6에서 자동 수정한 사항이 있으면 커밋한다. 커밋 메시지 본문에는 **어떤 PR들 사이에서 발견된 문제인지**와 **구체적으로 무엇을 수정했는지**를 명시하여 추후 업데이트 추적이 가능하도록 한다.

**자동 수정 가능 항목:**
- 누락된 backlink 추가 (A→B 있으나 B→A 없을 때)
- 관련 노드 섹션 누락/불완전 보완
- frontmatter links ↔ 본문 wikilink 불일치 수정
- updated 날짜 갱신

**사용자 결정 필수 항목:**
- 의미적 중복 노드 처리 (통합/유지/병기)
- 내용 모순 해결 (대체/유지/병기)

### Step 8: 다음 PR

병합할 PR이 남아있으면 Step 3~7을 반복한다.

### Step 9: 최종 점검

모든 PR 병합 및 수정이 완료되면:

```bash
# 전체 검증
make validate

# 인덱스 재구축
make index
```

사용자에게 최종 보고를 한다:

- 병합된 PR 목록
- 자동 수정한 항목 (backlink 추가, 관련 노드 보완 등)
- 사용자 결정으로 처리한 항목 (중복/모순)
- validate 결과
- 인덱스 갱신 결과
