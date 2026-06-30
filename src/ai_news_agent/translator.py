import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from .models import utc_now_iso


ARGOS_READY_MARKER = Path("data/argos_en_zh.ready")

PROTECTED_TERMS = (
    "Google DeepMind",
    "OpenAI",
    "Anthropic",
    "Claude Code",
    "Claude",
    "ChatGPT",
    "Codex",
    "Cursor",
    "DeepSeek",
    "Qwen",
    "Gemini",
    "Llama",
    "Nvidia",
    "CUDA",
    "Sora",
    "Grok",
    "Copilot",
    "Blackwell",
    "H100",
    "H200",
    "B200",
)

BAD_TERM_TRANSLATIONS = {
    "人择": "Anthropic",
    "人类学": "Anthropic",
    "英伟达": "Nvidia",
    "谷歌DeepMind": "Google DeepMind",
    "谷歌 DeepMind": "Google DeepMind",
}


def translated_at_now() -> str:
    return utc_now_iso()


def get_translation_status() -> dict:
    """Report the cheapest available translation option."""
    if ARGOS_READY_MARKER.exists() and argos_model_files_exist():
        return {
            "configured": True,
            "provider": "argos",
            "label": "离线翻译已就绪",
            "detail": "使用本地 Argos Translate 模型，不按量计费。",
        }
    if ARGOS_READY_MARKER.exists():
        ARGOS_READY_MARKER.unlink(missing_ok=True)

    if os.getenv("LIBRETRANSLATE_URL"):
        return {
            "configured": True,
            "provider": "libretranslate",
            "label": "LibreTranslate 已配置",
            "detail": "使用你配置的 LibreTranslate 服务。",
        }

    if has_google_web_translator():
        return {
            "configured": True,
            "provider": "google-web",
            "label": "免费网页翻译可用",
            "detail": "使用 deep-translator 免费翻译作为兜底方案，可能受网络和频率限制。",
        }

    return {
        "configured": False,
        "provider": "",
        "label": "尚未配置中文翻译",
        "detail": "可以安装离线翻译模型，或安装依赖后使用免费网页翻译。",
    }


def is_translation_configured() -> bool:
    return bool(get_translation_status()["configured"])


def install_offline_translation() -> None:
    """Install Argos Translate and its English-to-Chinese model."""
    ARGOS_READY_MARKER.unlink(missing_ok=True)
    try:
        import argostranslate.package as package
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "argostranslate"])
        import argostranslate.package as package

    remove_broken_argos_packages()
    package.update_package_index()
    available_packages = package.get_available_packages()
    model = next(
        (
            item
            for item in available_packages
            if item.from_code == "en" and item.to_code.startswith("zh")
        ),
        None,
    )
    if model is None:
        raise RuntimeError("没有找到 English -> Chinese 的 Argos Translate 模型。")

    package_path = model.download()
    package.install_from_path(package_path)
    try:
        translation = get_argos_translation()
        if translation is None:
            raise RuntimeError("离线翻译模型安装后仍不可用，请稍后重试。")
        translation.translate("AI news")
    except Exception as exc:
        ARGOS_READY_MARKER.unlink(missing_ok=True)
        raise RuntimeError(
            "离线翻译模型安装后验证失败。程序会继续使用免费网页翻译作为备用。"
        ) from exc
    ARGOS_READY_MARKER.parent.mkdir(parents=True, exist_ok=True)
    ARGOS_READY_MARKER.write_text(translated_at_now(), encoding="utf-8")


def translate_news_item(title: str, summary: str) -> tuple[str, str]:
    """Translate one item with a free/local provider whenever possible."""
    protected_title, title_terms = protect_terms(title)
    protected_summary, summary_terms = protect_terms(summary or "")

    if ARGOS_READY_MARKER.exists() and argos_model_files_exist():
        translation = get_argos_translation()
    else:
        translation = None

    if translation is not None:
        try:
            return (
                restore_terms(translation.translate(protected_title), title_terms),
                restore_terms(translation.translate(protected_summary), summary_terms),
            )
        except Exception as exc:
            ARGOS_READY_MARKER.unlink(missing_ok=True)
            if not has_google_web_translator() and not os.getenv("LIBRETRANSLATE_URL"):
                raise RuntimeError(
                    "本地离线翻译模型损坏或安装不完整，请点击“修复/安装离线翻译”。"
                ) from exc

    if os.getenv("LIBRETRANSLATE_URL"):
        return (
            restore_terms(translate_with_libretranslate(protected_title), title_terms),
            restore_terms(translate_with_libretranslate(protected_summary), summary_terms),
        )

    if has_google_web_translator():
        return (
            restore_terms(translate_with_google_web(protected_title), title_terms),
            restore_terms(translate_with_google_web(protected_summary), summary_terms),
        )

    raise RuntimeError("尚未配置翻译方式。请先安装依赖或配置 LibreTranslate。")


def get_argos_translation():
    try:
        import argostranslate.translate as translate
    except ImportError:
        return None

    try:
        installed_languages = translate.get_installed_languages()
    except Exception:
        return None
    from_lang = next((lang for lang in installed_languages if lang.code == "en"), None)
    to_lang = next((lang for lang in installed_languages if lang.code.startswith("zh")), None)
    if not from_lang or not to_lang:
        return None

    return from_lang.get_translation(to_lang)


def remove_broken_argos_packages() -> None:
    package_root = get_argos_package_root()
    if not package_root.exists():
        return

    for path in package_root.glob("translate-en_zh*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def argos_model_files_exist() -> bool:
    package_root = get_argos_package_root()
    return any(path.exists() for path in package_root.glob("translate-en_zh*/sentencepiece.model"))


def get_argos_package_root() -> Path:
    return Path.home() / ".local" / "share" / "argos-translate" / "packages"


def translate_with_libretranslate(text: str) -> str:
    if not text:
        return ""

    base_url = os.environ["LIBRETRANSLATE_URL"].rstrip("/")
    payload = {
        "q": text,
        "source": "en",
        "target": "zh",
        "format": "text",
    }
    api_key = os.getenv("LIBRETRANSLATE_API_KEY")
    if api_key:
        payload["api_key"] = api_key

    request = Request(
        f"{base_url}/translate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("translatedText", "")).strip()


def has_google_web_translator() -> bool:
    try:
        import deep_translator  # noqa: F401
    except ImportError:
        return False
    return True


def translate_with_google_web(text: str) -> str:
    if not text:
        return ""

    from deep_translator import GoogleTranslator

    safe_text = text[:4500]
    translated = GoogleTranslator(
        source="english",
        target="chinese (simplified)",
    ).translate(safe_text)
    if looks_like_translator_error(translated):
        raise RuntimeError("免费网页翻译暂时不可用，请稍后再试或使用离线翻译。")
    return translated


def protect_terms(text: str) -> tuple[str, dict[str, str]]:
    protected = text or ""
    mapping = {}
    for index, term in enumerate(sorted(PROTECTED_TERMS, key=len, reverse=True)):
        token = f"ZXQTERM{index}QXZ"
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.IGNORECASE)
        if pattern.search(protected):
            protected = pattern.sub(token, protected)
            mapping[token] = term
    return protected, mapping


def restore_terms(text: str, mapping: dict[str, str]) -> str:
    restored = text or ""
    for token, term in mapping.items():
        restored = restored.replace(token, term)
        restored = restored.replace(token.lower(), term)
        restored = restored.replace(token.upper(), term)
        restored = re.sub(r"\s+".join(token), term, restored, flags=re.IGNORECASE)
    for bad, correct in BAD_TERM_TRANSLATIONS.items():
        restored = restored.replace(bad, correct)
    return restored


def looks_like_translator_error(text: str) -> bool:
    lowered = (text or "").lower()
    return any(
        marker in lowered
        for marker in (
            "error 500",
            "server error",
            "that's an error",
            "too many requests",
            "no translation was found",
        )
    )
