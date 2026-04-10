"""Synapse LanceDB 테이블 스키마 정의."""

from lancedb.pydantic import LanceModel, Vector

from scripts.embedding import get_embedder

embedder = get_embedder()


class Node(LanceModel):
    """docs/ 마크다운 노드의 LanceDB 스키마."""

    # embedding 대상: summary (의미 검색, 비용 절감)
    summary: str = embedder.SourceField()
    vector: Vector(embedder.ndims()) = embedder.VectorField()  # type: ignore[reportInvalidTypeForm]

    # BM25 full-text 검색 대상: summary + 본문 (키워드 매칭)
    text: str

    # frontmatter metadata
    id: str
    title: str
    type: str  # source | entity | concept | analysis
    tags: str  # JSON 배열 문자열 (LanceDB 필터링용)
    links: str  # JSON 배열 문자열 (fan-out용)
    relations: str  # JSON 배열 문자열 (links와 1:1 대응)
    sources: str  # JSON 배열 문자열
    path: str  # docs/ 내 파일 경로
    status: str  # draft | active | stale | archived
    created: str
    updated: str
