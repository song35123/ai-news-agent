import subprocess
import sys
import webbrowser
import logging
import os
import secrets
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for

from .brief import default_brief_path, write_brief
from .company_logos import company_badges
from .config import load_sources
from .diagnostics import app_diagnostics
from .fetcher import fetch_source
from .pdf_report import build_pdf_report, default_pdf_path
from .security import get_action_token, parse_int, require_action_token
from .storage import (
    connect,
    count_news,
    insert_news,
    list_news,
    list_untranslated_news,
    review_all_news,
    update_translation,
)
from .translator import (
    get_translation_status,
    install_offline_translation,
    is_translation_configured,
    translate_news_item,
    translated_at_now,
)


app = Flask(__name__)
app.secret_key = os.getenv("AI_NEWS_SECRET_KEY", secrets.token_hex(32))
logger = logging.getLogger(__name__)


def require_post_token() -> None:
    require_action_token(request.form.get("action_token"))


def fetch_all_sources() -> dict:
    """Fetch configured sources and store reviewed items."""
    result = {"fetched": 0, "inserted": 0, "reviewed": 0, "warnings": []}
    sources = load_sources()
    with connect() as conn:
        for source in sources:
            items, error = fetch_source(source)
            if error:
                logger.warning("fetch failed for %s: %s", source["name"], error)
                result["warnings"].append(f"{source['name']}: {error}")
                continue

            result["fetched"] += len(items)
            for item in items:
                if insert_news(conn, item):
                    result["inserted"] += 1

        result["reviewed"] = review_all_news(conn)
    return result


def translate_latest(limit: int) -> dict:
    result = {"translated": 0, "error": ""}
    if not is_translation_configured():
        result["error"] = "尚未配置翻译方式，请先安装离线翻译模型。"
        return result

    with connect() as conn:
        rows = list_untranslated_news(conn, limit=limit)
        for row in rows:
            title_zh, summary_zh = translate_news_item(row["title"], row["summary"] or "")
            update_translation(
                conn,
                row["id"],
                title_zh=title_zh,
                summary_zh=summary_zh,
                translated_at=translated_at_now(),
            )
            result["translated"] += 1
    return result


def translate_rows_if_needed(rows) -> int:
    if not is_translation_configured():
        return 0

    translated = 0
    with connect() as conn:
        for row in rows:
            if row["title_zh"]:
                continue
            try:
                title_zh, summary_zh = translate_news_item(row["title"], row["summary"] or "")
                update_translation(
                    conn,
                    row["id"],
                    title_zh=title_zh,
                    summary_zh=summary_zh,
                    translated_at=translated_at_now(),
                )
                translated += 1
            except Exception:
                continue
    return translated


def prepare_rows(rows) -> list[dict]:
    prepared = []
    for row in rows:
        item = dict(row)
        item["company_badges"] = company_badges(item.get("companies"))
        prepared.append(item)
    return prepared


@app.get("/")
def index():
    days = parse_int(request.args.get("days"), default=1, minimum=1, maximum=30)
    limit = parse_int(request.args.get("limit"), default=30, minimum=5, maximum=100)
    scope = request.args.get("scope", "relevant")
    message = request.args.get("message", "")
    error = request.args.get("error", "")

    with connect() as conn:
        reviewed = review_all_news(conn)
        rows = list_news(conn, days=days, limit=limit, relevant_only=scope != "all")
        stats = count_news(conn)

    if reviewed and not message:
        message = f"已自动审查 {reviewed} 条历史新闻。"

    return render_template(
        "index.html",
        rows=prepare_rows(rows),
        days=days,
        limit=limit,
        scope=scope,
        stats=stats,
        message=message,
        error=error,
        translation_configured=is_translation_configured(),
        translation_status=get_translation_status(),
        action_token=get_action_token(),
    )


@app.post("/refresh")
def refresh():
    require_post_token()
    result = fetch_all_sources()
    message = f"抓取完成：读取 {result['fetched']} 条，新增 {result['inserted']} 条。"
    if result["warnings"]:
        message += " 部分来源暂时不可用。"
    return redirect(url_for("index", message=message))


@app.post("/update-today")
def update_today():
    require_post_token()
    try:
        fetch_result = fetch_all_sources()
        translate_result = translate_latest(10)
        with connect() as conn:
            rows = list_news(conn, days=1, limit=10, relevant_only=True)
            stats = count_news(conn)
        markdown_path = write_brief(rows, default_brief_path())
        pdf_path = build_pdf_report(
            [dict(row) for row in rows],
            stats,
            get_translation_status(),
            default_pdf_path(),
        )
    except Exception as exc:
        logger.exception("one-click update failed")
        return redirect(url_for("index", error=f"一键更新失败：{exc}"))

    message = (
        f"今日简报已更新：读取 {fetch_result['fetched']} 条，"
        f"新增 {fetch_result['inserted']} 条，翻译 {translate_result['translated']} 条。"
        f" Markdown：{markdown_path}；PDF：{pdf_path}"
    )
    return redirect(url_for("index", message=message))


@app.post("/refresh-translate")
def refresh_translate():
    require_post_token()
    try:
        fetch_result = fetch_all_sources()
        translate_result = translate_latest(20)
    except Exception as exc:
        logger.exception("refresh and translate failed")
        return redirect(url_for("index", error=f"刷新并翻译失败：{exc}"))

    if translate_result["error"]:
        return redirect(url_for("index", error=translate_result["error"]))

    message = (
        f"刷新并翻译完成：读取 {fetch_result['fetched']} 条，"
        f"新增 {fetch_result['inserted']} 条，翻译 {translate_result['translated']} 条。"
    )
    return redirect(url_for("index", message=message))


@app.post("/setup-translation")
def setup_translation():
    require_post_token()
    try:
        install_offline_translation()
    except Exception as exc:
        logger.exception("offline translation setup failed")
        if is_translation_configured():
            return redirect(
                url_for(
                    "index",
                    message=f"离线翻译暂时不可用，已改用低成本备用翻译：{exc}",
                )
            )
        return redirect(url_for("index", error=f"离线翻译安装失败：{exc}"))
    return redirect(url_for("index", message="离线翻译模型安装完成，可以开始翻译新闻。"))


@app.post("/translate")
def translate():
    require_post_token()
    limit = parse_int(request.form.get("limit"), default=10, minimum=1, maximum=50)
    try:
        result = translate_latest(limit)
    except Exception as exc:
        logger.exception("translation failed")
        return redirect(url_for("index", error=f"翻译失败：{exc}"))

    if result["error"]:
        return redirect(url_for("index", error=result["error"]))
    return redirect(url_for("index", message=f"已翻译 {result['translated']} 条新闻。"))


@app.post("/brief")
def brief():
    require_post_token()
    days = parse_int(request.form.get("days"), default=1, minimum=1, maximum=30)
    limit = parse_int(request.form.get("limit"), default=30, minimum=5, maximum=100)
    scope = request.form.get("scope", "relevant")
    with connect() as conn:
        rows = list_news(conn, days=days, limit=limit, relevant_only=scope != "all")
    path = write_brief(rows, default_brief_path())
    return redirect(url_for("index", message=f"已生成简报：{path}"))


@app.post("/download-pdf")
def download_pdf():
    require_post_token()
    days = parse_int(request.form.get("days"), default=1, minimum=1, maximum=30)
    scope = request.form.get("scope", "relevant")

    try:
        with connect() as conn:
            rows = list_news(conn, days=days, limit=10, relevant_only=scope != "all")

        translate_rows_if_needed(rows)

        with connect() as conn:
            rows = list_news(conn, days=days, limit=10, relevant_only=scope != "all")
            stats = count_news(conn)

        pdf_path = build_pdf_report(
            [dict(row) for row in rows],
            stats,
            get_translation_status(),
            default_pdf_path(),
        )
    except Exception as exc:
        logger.exception("pdf generation failed")
        return redirect(url_for("index", error=f"PDF 生成失败：{exc}"))

    return send_file(pdf_path.resolve(), as_attachment=True, download_name=pdf_path.name)


@app.get("/diagnostics")
def diagnostics():
    return render_template(
        "diagnostics.html",
        diagnostics=app_diagnostics(),
        action_token=get_action_token(),
    )


def ensure_dependencies() -> None:
    requirements = Path("requirements.txt")
    try:
        import flask  # noqa: F401
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements)]
        )


def main() -> None:
    url = "http://127.0.0.1:5000"
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=5000, debug=False)


if __name__ == "__main__":
    ensure_dependencies()
    main()
