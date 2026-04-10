#!/usr/bin/env bash
# docs/ 노드의 YAML frontmatter 유효성을 검증한다.
#
# Usage:
#   bash .claude/skills/ingest/validate.sh docs/entities/lancedb.md
#   bash .claude/skills/ingest/validate.sh docs/  # 디렉토리 전체

set -euo pipefail

REQUIRED_FIELDS=(id title type tags created updated summary status)
VALID_TYPES="source|entity|concept|analysis"
VALID_STATUSES="draft|active|stale|archived"
VALID_RELATIONS="relates_to|depends_on|contradicts|extends|part_of"

total=0
failed=0

validate_file() {
  local file="$1"
  local errors=()

  # frontmatter 존재 확인
  if ! head -1 "$file" | grep -q "^---"; then
    errors+=("frontmatter가 없습니다 (파일이 ---로 시작하지 않음)")
    printf "\nFAIL %s\n" "$file"
    for e in "${errors[@]}"; do printf "  - %s\n" "$e"; done
    return 1
  fi

  # frontmatter 추출 (첫 번째 --- 와 두 번째 --- 사이)
  local fm
  fm=$(sed -n '1,/^---$/!b; /^---$/,/^---$/{ /^---$/d; p }' "$file" | head -100)

  if [ -z "$fm" ]; then
    errors+=("frontmatter가 닫히지 않았습니다")
    printf "\nFAIL %s\n" "$file"
    for e in "${errors[@]}"; do printf "  - %s\n" "$e"; done
    return 1
  fi

  # 필수 필드 확인
  for field in "${REQUIRED_FIELDS[@]}"; do
    if ! echo "$fm" | grep -qE "^${field}:"; then
      errors+=("필수 필드 누락: ${field}")
    fi
  done

  # 필수 필드 없으면 나머지 검증 불가
  if [ ${#errors[@]} -gt 0 ]; then
    printf "\nFAIL %s\n" "$file"
    for e in "${errors[@]}"; do printf "  - %s\n" "$e"; done
    return 1
  fi

  # id: kebab-case
  local id_val
  id_val=$(echo "$fm" | grep -E "^id:" | sed 's/^id: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
  if ! echo "$id_val" | grep -qE "^[a-z0-9]+(-[a-z0-9]+)*$"; then
    errors+=("id가 kebab-case가 아닙니다: '${id_val}'")
  fi

  # type: 유효값
  local type_val
  type_val=$(echo "$fm" | grep -E "^type:" | sed 's/^type: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
  if ! echo "$type_val" | grep -qE "^(${VALID_TYPES})$"; then
    errors+=("잘못된 type: '${type_val}'")
  fi

  # status: 유효값
  local status_val
  status_val=$(echo "$fm" | grep -E "^status:" | sed 's/^status: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
  if ! echo "$status_val" | grep -qE "^(${VALID_STATUSES})$"; then
    errors+=("잘못된 status: '${status_val}'")
  fi

  # tags: 배열 형식, 최소 1개
  local tags_line
  tags_line=$(echo "$fm" | grep -E "^tags:")
  if ! echo "$tags_line" | grep -qE "\[.+\]"; then
    errors+=("tags는 최소 1개 이상의 배열이어야 합니다")
  fi

  # created, updated: YYYY-MM-DD
  for field in created updated; do
    local date_val
    date_val=$(echo "$fm" | grep -E "^${field}:" | sed 's/^[a-z]*: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
    if ! echo "$date_val" | grep -qE "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"; then
      errors+=("${field}가 YYYY-MM-DD 형식이 아닙니다: '${date_val}'")
    fi
  done

  # summary: 비어있지 않은 문자열
  local summary_val
  summary_val=$(echo "$fm" | grep -E "^summary:" | sed 's/^summary: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
  if [ -z "$summary_val" ]; then
    errors+=("summary가 비어있습니다")
  fi

  # links: 존재하면 relation 유효값 확인
  if echo "$fm" | grep -qE "^\s+relation:"; then
    while IFS= read -r rel_line; do
      local rel_val
      rel_val=$(echo "$rel_line" | sed 's/.*relation: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
      if ! echo "$rel_val" | grep -qE "^(${VALID_RELATIONS})$"; then
        errors+=("잘못된 relation: '${rel_val}'")
      fi
    done < <(echo "$fm" | grep -E "^\s+relation:")
  fi

  # 파일명 = id 일치 확인 (Obsidian 호환)
  local file_stem
  file_stem=$(basename "$file" .md)
  if [ "$file_stem" != "$id_val" ]; then
    errors+=("파일명('${file_stem}')과 id('${id_val}')가 불일치 (Obsidian wikilink 해석 불가)")
  fi

  # frontmatter links의 target이 본문에 [[wikilink]]로 존재하는지 확인
  local body
  body=$(sed -n '/^---$/,/^---$/!p' "$file" | tail -n +2)
  if echo "$fm" | grep -qE "^\s+- target:"; then
    while IFS= read -r target_line; do
      local target_val
      target_val=$(echo "$target_line" | sed 's/.*target: *"\{0,1\}//' | sed 's/"\{0,1\} *$//')
      if [ -n "$target_val" ]; then
        if ! echo "$body" | grep -qE "\[\[${target_val}(\|[^]]+)?\]\]"; then
          errors+=("frontmatter link target '${target_val}'에 대한 [[wikilink]]가 본문에 없습니다")
        fi
      fi
    done < <(echo "$fm" | grep -E "^\s+- target:")
  fi

  # "관련 노드" 섹션 존재 확인
  if ! echo "$body" | grep -qE "^## 관련 노드"; then
    errors+=("'## 관련 노드' 섹션이 없습니다 (Obsidian Graph View 호환 필수)")
  fi

  # 결과 출력
  if [ ${#errors[@]} -gt 0 ]; then
    printf "\nFAIL %s\n" "$file"
    for e in "${errors[@]}"; do printf "  - %s\n" "$e"; done
    return 1
  else
    printf "  OK %s\n" "$file"
    return 0
  fi
}

# 대상 결정
target="${1:?usage: validate.sh <파일 또는 디렉토리>}"

if [ -d "$target" ]; then
  files=$(find "$target" -name "*.md" -type f | sort)
elif [ -f "$target" ]; then
  files="$target"
else
  echo "error: $target not found"
  exit 1
fi

for f in $files; do
  total=$((total + 1))
  if ! validate_file "$f"; then
    failed=$((failed + 1))
  fi
done

echo ""
echo "========================================"
echo "total: ${total}, passed: $((total - failed)), failed: ${failed}"

[ "$failed" -eq 0 ] || exit 1
