import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
REQUIREMENTS = ROOT / "requirements.txt"


def ensure_project_importable() -> None:
    src_path = str(SRC)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


def ensure_dependencies() -> None:
    """Install runtime dependencies only when they are missing."""
    try:
        import feedparser  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        print("Installing dependencies from requirements.txt...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        )


def open_file(path: Path) -> None:
    try:
        os.startfile(path)  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        print(f"Open the brief here: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch news and create a brief.")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    os.chdir(ROOT)
    ensure_project_importable()
    ensure_dependencies()

    from ai_news_agent.brief import default_brief_path, write_brief
    from ai_news_agent.config import load_sources
    from ai_news_agent.fetcher import fetch_source
    from ai_news_agent.storage import connect, insert_news, list_news, review_all_news

    print("Fetching AI news...")
    sources = load_sources()
    inserted = 0
    fetched = 0

    with connect() as conn:
        for source in sources:
            items, error = fetch_source(source)
            if error:
                print(f"[warn] {source['name']}: {error}")
                continue

            fetched += len(items)
            new_count = 0
            for item in items:
                if insert_news(conn, item):
                    inserted += 1
                    new_count += 1
            print(f"{source['name']}: fetched {len(items)}, new {new_count}")

        reviewed = review_all_news(conn)
        rows = list_news(conn, days=args.days, limit=args.limit)

    output_path = write_brief(rows, default_brief_path())
    print(f"Done. Fetched {fetched}, inserted {inserted}.")
    if reviewed:
        print(f"Reviewed {reviewed} older items.")
    print(f"Brief: {output_path}")

    if not args.no_open:
        open_file(output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
