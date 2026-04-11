.PHONY: index index-file search install validate validate-file

# 의존성 설치 (poetry >= 2. 호환)
install:
	poetry install --no-root

# 전체 인덱스 재구축
index:
	poetry run python -m scripts.index

# 단일 파일 upsert (사용법: make index-file FILE=docs/entities/lancedb.md)
index-file:
	poetry run python -m scripts.index --file $(FILE)

# Semantic search (사용법: make search Q="검색 쿼리" 또는 추가 옵션)
# 예시:
#   make search Q="벡터 데이터베이스"
#   make search Q="인증 시스템" OPTS="--fanout --json"
#   make search Q="보안" OPTS="--type entity --tag security --fanout --json"
#   make search Q="검색어" OPTS="--mode vector --limit 5"
search:
	poetry run python -m scripts.search "$(Q)" $(OPTS)

# frontmatter 검증 (전체)
validate:
	bash .claude/skills/ingest/validate.sh docs/

# frontmatter 검증 (단일 파일, 사용법: make validate-file FILE=docs/entities/lancedb.md)
validate-file:
	bash .claude/skills/ingest/validate.sh $(FILE)
