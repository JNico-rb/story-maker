"""DetectorDeInyeccion: marca por patrones ES/EN, nunca deniega (architecture.md §12.4, 005-I5)."""

from story_maker.domain.injection_patterns import INJECTION_PATTERNS


def find_injection_phrases(text: str) -> list[str]:
    """Frases de `text` que coinciden con un patrón de inyección conocido."""
    return [match.group(0) for pattern in INJECTION_PATTERNS for match in pattern.finditer(text)]
