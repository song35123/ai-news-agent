import argparse
from pathlib import Path

from .brief import default_brief_path, write_brief
from .config import DEFAULT_CONFIG_PATH, load_sources
from .fetcher import fetch_source
from .storage import DEFAULT_DB_PATH, connect, insert_news, list_news, review_all_news


def cmd_fetch(args: argparse.Namespace) -> int:
    sources = load_sources(args.config)
    if not sources:
        print("No enabled sources found.")
        return 1

    inserted = 0
    seen = 0
    with connect(args.db) as conn:
        for source in sources:
            items, error = fetch_source(source)
            if error:
                print(f"[warn] {source['name']}: {error}")
                continue

            seen += len(items)
            source_inserted = 0
            for item in items:
                if insert_news(conn, item):
                    inserted += 1
                    source_inserted += 1
            print(f"{source['name']}: fetched {len(items)}, new {source_inserted}")
        reviewed = review_all_news(conn)

    print(f"Done. Fetched {seen}, inserted {inserted}, reviewed {reviewed}.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with connect(args.db) as conn:
        rows = list_news(conn, limit=args.limit)

    for row in rows:
        print(f"- [{row['source']}] {row['title']} ({row['url']})")
    print(f"Total: {len(rows)}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    output = args.output or default_brief_path()
    with connect(args.db) as conn:
        rows = list_news(conn, days=args.days, limit=args.limit)

    write_brief(rows, output)
    print(f"Wrote {len(rows)} items to {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai-news")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)

    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch RSS news")
    fetch_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    fetch_parser.set_defaults(func=cmd_fetch)

    list_parser = subparsers.add_parser("list", help="List saved news")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.set_defaults(func=cmd_list)

    brief_parser = subparsers.add_parser("brief", help="Generate Markdown brief")
    brief_parser.add_argument("--days", type=int, default=1)
    brief_parser.add_argument("--limit", type=int, default=50)
    brief_parser.add_argument("--output", type=Path)
    brief_parser.set_defaults(func=cmd_brief)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)
