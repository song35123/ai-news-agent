import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .dedupe import url_hash
from .models import NewsItem
from .reviewer import REVIEW_RULE_VERSION, review_news


DEFAULT_DB_PATH = Path("data/news.db")


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create and lightly migrate the local news table."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            url_hash TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            summary TEXT,
            published_at TEXT,
            fetched_at TEXT NOT NULL
        )
        """
    )
    ensure_column(conn, "title_zh", "TEXT")
    ensure_column(conn, "summary_zh", "TEXT")
    ensure_column(conn, "translated_at", "TEXT")
    ensure_column(conn, "is_relevant", "INTEGER DEFAULT 0")
    ensure_column(conn, "relevance_score", "INTEGER DEFAULT 0")
    ensure_column(conn, "companies", "TEXT")
    ensure_column(conn, "regions", "TEXT")
    ensure_column(conn, "content_type", "TEXT")
    ensure_column(conn, "review_reason", "TEXT")
    ensure_column(conn, "reviewed_at", "TEXT")
    ensure_column(conn, "review_version", "TEXT")
    conn.commit()


def ensure_column(conn: sqlite3.Connection, column_name: str, column_type: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(news)")}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE news ADD COLUMN {column_name} {column_type}")


def insert_news(conn: sqlite3.Connection, item: NewsItem) -> bool:
    review = review_news(item.title, item.summary, item.source)
    result = conn.execute(
        """
        INSERT OR IGNORE INTO news
            (
                title, url, url_hash, source, summary, published_at, fetched_at,
                is_relevant, relevance_score, companies, regions, content_type, review_reason, reviewed_at
                , review_version
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item.title,
            item.url,
            url_hash(item.url),
            item.source,
            item.summary,
            item.published_at,
            item.fetched_at,
            review["is_relevant"],
            review["relevance_score"],
            review["companies"],
            review["regions"],
            review["content_type"],
            review["review_reason"],
            review["reviewed_at"],
            review["review_version"],
        ),
    )
    conn.commit()
    return result.rowcount == 1


def list_news(
    conn: sqlite3.Connection,
    *,
    days: int | None = None,
    limit: int = 50,
    relevant_only: bool = True,
) -> list[sqlite3.Row]:
    filters = []
    params: list[object] = []
    if days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        filters.append("fetched_at >= ?")
        params.append(cutoff.replace(microsecond=0).isoformat())
    if relevant_only:
        filters.append("is_relevant = 1")

    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    params.append(limit)
    return conn.execute(
        f"""
        SELECT title, url, source, summary, published_at, fetched_at
             , id, title_zh, summary_zh, translated_at
             , is_relevant, relevance_score, companies, regions, content_type, review_reason, reviewed_at
        FROM news
        {where}
        ORDER BY COALESCE(NULLIF(published_at, ''), fetched_at) DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def list_untranslated_news(conn: sqlite3.Connection, *, limit: int = 10) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT id, title, summary
        FROM news
        WHERE is_relevant = 1
          AND (title_zh IS NULL OR title_zh = '')
        ORDER BY COALESCE(NULLIF(published_at, ''), fetched_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def update_translation(
    conn: sqlite3.Connection,
    news_id: int,
    *,
    title_zh: str,
    summary_zh: str,
    translated_at: str,
) -> None:
    conn.execute(
        """
        UPDATE news
        SET title_zh = ?, summary_zh = ?, translated_at = ?
        WHERE id = ?
        """,
        (title_zh, summary_zh, translated_at, news_id),
    )
    conn.commit()


def review_all_news(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT id, title, summary, source
        FROM news
        WHERE reviewed_at IS NULL OR reviewed_at = ''
           OR review_version IS NULL OR review_version != ?
        """
        ,
        (REVIEW_RULE_VERSION,),
    ).fetchall()

    for row in rows:
        review = review_news(row["title"], row["summary"] or "", row["source"])
        conn.execute(
            """
            UPDATE news
            SET is_relevant = ?, relevance_score = ?, companies = ?, regions = ?,
                content_type = ?, review_reason = ?, reviewed_at = ?
                , review_version = ?
            WHERE id = ?
            """,
            (
                review["is_relevant"],
                review["relevance_score"],
                review["companies"],
                review["regions"],
                review["content_type"],
                review["review_reason"],
                review["reviewed_at"],
                review["review_version"],
                row["id"],
            ),
        )

    conn.commit()
    return len(rows)


def count_news(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN is_relevant = 1 THEN 1 ELSE 0 END) AS relevant,
            SUM(CASE WHEN title_zh IS NOT NULL AND title_zh != '' THEN 1 ELSE 0 END) AS translated
        FROM news
        """
    ).fetchone()
    return {
        "total": int(row["total"] or 0),
        "relevant": int(row["relevant"] or 0),
        "translated": int(row["translated"] or 0),
    }
