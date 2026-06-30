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
    required_modules = ("flask", "feedparser", "yaml", "deep_translator", "PIL", "reportlab", "pdfplumber")
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        print("Installing dependencies from requirements.txt...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        )


def main() -> int:
    os.chdir(ROOT)
    ensure_project_importable()
    from ai_news_agent.logging_utils import setup_logging

    setup_logging()
    ensure_dependencies()

    from ai_news_agent.web import main as run_web_app

    run_web_app()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        log_dir = ROOT / "logs"
        log_dir.mkdir(exist_ok=True)
        (log_dir / "startup_error.log").write_text(str(exc), encoding="utf-8")
        raise
