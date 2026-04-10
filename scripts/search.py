"""LanceDB 기반 semantic search CLI.

Usage:
    poetry run python -m scripts.search "검색 쿼리"
    poetry run python -m scripts.search "검색 쿼리" --limit 5
    poetry run python -m scripts.search "검색 쿼리" --type concept
    poetry run python -m scripts.search "검색 쿼리" --tag security
    poetry run python -m scripts.search "검색 쿼리" --fanout
    poetry run python -m scripts.search "검색 쿼리" --mode hybrid
    poetry run python -m scripts.search "검색 쿼리" --json
"""

import argparse
import json
import sys
from pathlib import Path

import lancedb
from lancedb.rerankers import RRFReranker

from dotenv import load_dotenv
from pathlib import Path as _Path

load_dotenv(_Path(__file__).resolve().parent.parent / "env" / ".env")

# embedding 모듈을 import하여 커스텀 EmbeddingFunction 등록
import scripts.embedding  # noqa: F401, E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / ".lancedb"
TABLE_NAME = "nodes"


def search(
    query: str,
    limit: int = 10,
    node_type: str | None = None,
    tag: str | None = None,
    status: str = "active",
    mode: str = "hybrid",
    fanout: bool = False,
    output_json: bool = False,
):
    db = lancedb.connect(str(DB_PATH))

    if TABLE_NAME not in db.list_tables().tables:
        print("error: index not found. run `poetry run python -m scripts.index` first.")
        sys.exit(1)

    table = db.open_table(TABLE_NAME)

    # 필터 조건 구성
    filters = []
    if status:
        filters.append(f"status = '{status}'")
    if node_type:
        filters.append(f"type = '{node_type}'")
    if tag:
        filters.append(f"tags LIKE '%\"{tag}\"%'")

    where_clause = " AND ".join(filters) if filters else None

    # 검색 실행
    if mode == "hybrid":
        builder = table.search(query, query_type="hybrid")
        builder = builder.rerank(RRFReranker())
    elif mode == "vector":
        builder = table.search(query, query_type="vector")
    elif mode == "fts":
        builder = table.search(query, query_type="fts")
    else:
        print(f"error: unknown mode '{mode}'. use: hybrid, vector, fts")
        sys.exit(1)

    if where_clause:
        builder = builder.where(where_clause)

    results = builder.limit(limit).to_list()

    # fan-out: seed 결과의 links에서 연결된 노드 추가 확보
    fanout_results = []
    if fanout and results:
        linked_ids = set()
        for doc in results:
            try:
                ids = json.loads(doc.get("links", "[]"))
                linked_ids.update(ids)
            except (json.JSONDecodeError, TypeError):
                pass

        # seed에 이미 포함된 ID 제외
        seed_ids = {doc["id"] for doc in results}
        linked_ids -= seed_ids

        if linked_ids:
            id_filter = ", ".join(f"'{i}'" for i in linked_ids)
            fanout_results = table.search().where(f"id IN ({id_filter})").limit(100).to_list()

    # 출력
    if output_json:
        output = {
            "query": query,
            "mode": mode,
            "results": [format_result(r) for r in results],
        }
        if fanout:
            output["fanout"] = [format_result(r) for r in fanout_results]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_results(query, mode, results, fanout_results if fanout else None)


def format_result(doc: dict) -> dict:
    return {
        "id": doc.get("id", ""),
        "title": doc.get("title", ""),
        "type": doc.get("type", ""),
        "path": doc.get("path", ""),
        "summary": doc.get("summary", ""),
        "tags": json.loads(doc.get("tags", "[]")),
        "links": json.loads(doc.get("links", "[]")),
        "status": doc.get("status", ""),
        "score": doc.get("_distance", doc.get("_score", None)),
    }


def print_results(
    query: str,
    mode: str,
    results: list[dict],
    fanout_results: list[dict] | None,
):
    print(f"\n{'='*60}")
    print(f"query: {query}")
    print(f"mode:  {mode}")
    print(f"{'='*60}")

    if not results:
        print("\nno results found.")
        return

    for i, doc in enumerate(results, 1):
        score = doc.get("_distance", doc.get("_score", ""))
        score_str = f" (score: {score:.4f})" if isinstance(score, float) else ""
        print(f"\n[{i}] {doc.get('title', 'untitled')}{score_str}")
        print(f"    id:      {doc.get('id', '')}")
        print(f"    type:    {doc.get('type', '')}")
        print(f"    path:    {doc.get('path', '')}")
        print(f"    summary: {doc.get('summary', '')}")
        tags = doc.get("tags", "[]")
        print(f"    tags:    {tags}")

    if fanout_results:
        print(f"\n{'─'*60}")
        print(f"fan-out: {len(fanout_results)} linked nodes")
        print(f"{'─'*60}")
        for doc in fanout_results:
            print(f"  - [{doc.get('type', '')}] {doc.get('title', '')} ({doc.get('id', '')})")


def main():
    parser = argparse.ArgumentParser(description="Synapse semantic search")
    parser.add_argument("query", type=str, help="검색 쿼리")
    parser.add_argument("--limit", "-n", type=int, default=10, help="결과 수 (기본: 10)")
    parser.add_argument("--type", "-t", dest="node_type", type=str, help="노드 타입 필터 (source|entity|concept|analysis)")
    parser.add_argument("--tag", type=str, help="태그 필터")
    parser.add_argument("--status", "-s", type=str, default="active", help="상태 필터 (기본: active)")
    parser.add_argument("--mode", "-m", type=str, default="hybrid", choices=["hybrid", "vector", "fts"], help="검색 모드 (기본: hybrid)")
    parser.add_argument("--fanout", "-f", action="store_true", help="연결 노드 fan-out")
    parser.add_argument("--json", "-j", dest="output_json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    search(
        query=args.query,
        limit=args.limit,
        node_type=args.node_type,
        tag=args.tag,
        status=args.status,
        mode=args.mode,
        fanout=args.fanout,
        output_json=args.output_json,
    )


if __name__ == "__main__":
    main()
