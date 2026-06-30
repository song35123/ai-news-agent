import feedparser
from urllib.error import URLError
from urllib.request import Request, urlopen

from .parser import parse_entry


USER_AGENT = "ai-news-agent/0.1 (+local CLI RSS reader)"
FETCH_TIMEOUT_SECONDS = 20


def fetch_source(source: dict) -> tuple[list, str | None]:
    """Fetch one RSS source. Returns items and an optional error message."""
    try:
        request = Request(source["url"], headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
            content = response.read()
    except (OSError, URLError) as exc:
        return [], str(exc)

    feed = feedparser.parse(content)

    if feed.get("bozo_exception") and not feed.entries:
        return [], str(feed.bozo_exception)

    items = []
    for entry in feed.entries:
        item = parse_entry(entry, source["name"])
        if item:
            items.append(item)

    return items, None
