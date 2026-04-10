"""docs/ 마크다운 파일들로부터 LanceDB 인덱스를 구축/갱신한다.

Usage:
    poetry run python -m scripts.index                  # 전체 재구축
    poetry run python -m scripts.index --file docs/entities/lancedb.md  # 단일 파일 upsert
"""

import argparse
import json
import sys
from pathlib import Path

import lancedb
import yaml

from dotenv import load_dotenv
from pathlib import Path as _Path

load_dotenv(_Path(__file__).resolve().parent.parent / "env" / ".env")

from scripts.schema import Node  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DB_PATH = PROJECT_ROOT / ".lancedb"
TABLE_NAME = "nodes"


def parse_frontmatter(filepath: Path) -> dict | None:
    """마크다운 파일에서 YAML frontmatter와 본문을 파싱한다."""
    content = filepath.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None

    if not meta or "id" not in meta:
        return None

    body = parts[2].strip()
    return {**meta, "body": body}


def node_to_record(meta: dict, filepath: Path) -> dict:
    """파싱된 frontmatter + 본문을 LanceDB 레코드로 변환한다."""
    links_raw = meta.get("links", []) or []
    link_targets = [l["target"] for l in links_raw if isinstance(l, dict)]
    link_relations = [l.get("relation", "relates_to") for l in links_raw if isinstance(l, dict)]

    rel_path = str(filepath.relative_to(PROJECT_ROOT))

    summary = meta.get("summary", "")
    body = meta.get("body", "")

    # embedding 대상: summary (의미 검색용, 비용 절감)
    # BM25 full-text 검색은 text 필드 전체를 사용하므로 본문 키워드도 검색 가능
    text = f"{summary}\n\n{body}" if summary else body

    return {
        "text": text,
        "id": meta["id"],
        "title": meta.get("title", ""),
        "type": meta.get("type", ""),
        "tags": json.dumps(meta.get("tags", []), ensure_ascii=False),
        "links": json.dumps(link_targets, ensure_ascii=False),
        "relations": json.dumps(link_relations, ensure_ascii=False),
        "sources": json.dumps(meta.get("sources", []), ensure_ascii=False),
        "path": rel_path,
        "summary": summary,
        "status": meta.get("status", "draft"),
        "created": meta.get("created", ""),
        "updated": meta.get("updated", ""),
    }


def collect_docs(target: Path | None = None) -> list[dict]:
    """docs/ 하위 마크다운 파일들을 수집하여 레코드 리스트로 변환한다."""
    records = []

    if target:
        files = [target]
    else:
        files = sorted(DOCS_DIR.rglob("*.md"))

    for f in files:
        # index.md는 카탈로그이므로 제외
        if f.name == "index.md":
            continue
        meta = parse_frontmatter(f)
        if meta is None:
            print(f"  skip (no frontmatter): {f.relative_to(PROJECT_ROOT)}")
            continue
        records.append(node_to_record(meta, f))
        print(f"  parsed: {f.relative_to(PROJECT_ROOT)}")

    return records


def build_full(db: lancedb.DBConnection, records: list[dict]):
    """전체 인덱스를 재구축한다."""
    if TABLE_NAME in db.list_tables().tables:
        db.drop_table(TABLE_NAME)

    table = db.create_table(TABLE_NAME, schema=Node, mode="overwrite")
    table.add(records)

    # Full-text search 인덱스 생성 (하이브리드 검색용)
    table.create_fts_index("text", replace=True)

    print(f"\nindex built: {len(records)} nodes")
    return table


def upsert_file(db: lancedb.DBConnection, record: dict):
    """단일 파일을 upsert한다."""
    table = db.open_table(TABLE_NAME)

    # 기존 레코드 삭제 후 추가 (LanceDB upsert 패턴)
    try:
        table.delete(f"id = '{record['id']}'")
    except Exception:
        pass

    table.add([record])

    # FTS 인덱스 재생성
    table.create_fts_index("text", replace=True)

    print(f"\nupserted: {record['id']}")


def main():
    parser = argparse.ArgumentParser(description="Synapse LanceDB 인덱스 구축")
    parser.add_argument("--file", type=str, help="단일 파일 upsert (예: docs/entities/lancedb.md)")
    args = parser.parse_args()

    db = lancedb.connect(str(DB_PATH))

    if args.file:
        target = PROJECT_ROOT / args.file
        if not target.exists():
            print(f"error: {args.file} not found")
            sys.exit(1)
        records = collect_docs(target)
        if not records:
            print("error: no valid frontmatter found")
            sys.exit(1)
        upsert_file(db, records[0])
    else:
        print("collecting docs/...")
        records = collect_docs()
        if not records:
            print("error: no documents found")
            sys.exit(1)
        build_full(db, records)


if __name__ == "__main__":
    main()
