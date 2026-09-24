"""Origen de navegación del revisor visual: solo el de STORY_MAKER_BASE_URL (arq. §12.3)."""

from urllib.parse import urlsplit


def is_own_origin(base_url: str, url: str) -> bool:
    base = urlsplit(base_url)
    target = urlsplit(url)
    return (base.scheme, base.hostname, base.port) == (
        target.scheme,
        target.hostname,
        target.port,
    )
