from dataclasses import dataclass
from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    summary: str = ""
    published_at: str = ""
    fetched_at: str = ""

