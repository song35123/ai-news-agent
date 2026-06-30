from collections import defaultdict
from datetime import datetime
from pathlib import Path


DEFAULT_BRIEF_DIR = Path("briefs")


def default_brief_path() -> Path:
    return DEFAULT_BRIEF_DIR / f"{datetime.now().date().isoformat()}.md"


def write_brief(rows: list, output_path: Path) -> Path:
    """Write a compact Markdown digest grouped by source."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grouped = defaultdict(list)
    for row in rows:
        grouped[row["source"]].append(row)

    lines = [
        f"# AI News Brief - {datetime.now().date().isoformat()}",
        "",
        f"Total items: {len(rows)}",
        "",
    ]

    for source, items in sorted(grouped.items()):
        lines.append(f"## {source}")
        lines.append("")
        for item in items:
            published = item["published_at"] or item["fetched_at"]
            title = item["title_zh"] or item["title"]
            summary = item["summary_zh"] or item["summary"]
            lines.append(f"- [{title}]({item['url']})")
            lines.append(f"  - Published: {published}")
            if item["companies"]:
                lines.append(f"  - Companies: {item['companies']}")
            if item["regions"]:
                lines.append(f"  - Regions: {item['regions']}")
            if item["review_reason"]:
                lines.append(f"  - Review: {item['review_reason']}")
            if summary:
                lines.append(f"  - Summary: {summary}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
