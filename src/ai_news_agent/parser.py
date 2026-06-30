from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import calendar
import re

from .models import NewsItem, utc_now_iso


TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str | None) -> str:
    """Turn short RSS HTML snippets into plain text for Markdown output."""
    if not value:
        return ""
    text = TAG_RE.sub("", value)
    return " ".join(unescape(text).split())


def parse_time(entry: dict) -> str:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        dt = datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc)
        return dt.replace(microsecond=0).isoformat()

    raw_date = entry.get("published") or entry.get("updated")
    if raw_date:
        try:
            dt = parsedate_to_datetime(raw_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
        except (TypeError, ValueError):
            return ""

    return ""


def parse_entry(entry: dict, source_name: str) -> NewsItem | None:
    title = clean_text(entry.get("title"))
    url = str(entry.get("link", "")).strip()
    if not title or not url:
        return None

    summary = clean_text(entry.get("summary") or entry.get("description"))
    return NewsItem(
        title=title,
        url=url,
        source=source_name,
        summary=summary,
        published_at=parse_time(entry),
        fetched_at=utc_now_iso(),
    )
