import importlib.util
from pathlib import Path

from .storage import connect, count_news
from .translator import get_translation_status


RUNTIME_MODULES = {
    "feedparser": "feedparser",
    "PyYAML": "yaml",
    "Flask": "flask",
    "deep-translator": "deep_translator",
    "Pillow": "PIL",
    "reportlab": "reportlab",
    "pdfplumber": "pdfplumber",
}


def dependency_status() -> list[dict]:
    return [
        {"name": name, "ok": importlib.util.find_spec(module) is not None}
        for name, module in RUNTIME_MODULES.items()
    ]


def app_diagnostics() -> dict:
    with connect() as conn:
        stats = count_news(conn)
    return {
        "database_exists": Path("data/news.db").exists(),
        "stats": stats,
        "translation": get_translation_status(),
        "dependencies": dependency_status(),
    }

