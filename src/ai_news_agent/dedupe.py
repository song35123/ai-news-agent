from hashlib import sha256


def normalize_url(url: str) -> str:
    """Keep URL normalization intentionally small for the first version."""
    return url.strip()


def url_hash(url: str) -> str:
    return sha256(normalize_url(url).encode("utf-8")).hexdigest()

