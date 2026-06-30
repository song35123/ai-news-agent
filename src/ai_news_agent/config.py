from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path("config/sources.yaml")


def load_sources(config_path: Path = DEFAULT_CONFIG_PATH) -> list[dict]:
    """Load enabled RSS sources from a small YAML config file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    sources = []
    for source in data.get("sources", []):
        if not source.get("enabled", True):
            continue
        name = str(source.get("name", "")).strip()
        url = str(source.get("url", "")).strip()
        if name and url:
            sources.append({"name": name, "url": url})

    return sources

