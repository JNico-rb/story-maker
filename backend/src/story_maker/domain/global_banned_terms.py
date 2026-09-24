"""Lista global de insultos y términos ofensivos, sembrada en `banned_terms` (arq. §12.1).

Curada a mano, corta y ampliable sin tocar el motor de políticas: cada entrada es un único
término de tipo `word`, en minúsculas y sin acentos (la normalización cubre las variantes)."""

GLOBAL_BANNED_TERMS: tuple[str, ...] = (
    "idiota",
    "imbecil",
    "estupido",
    "gilipollas",
    "cabron",
    "capullo",
    "subnormal",
    "zorra",
    "puta",
    "mierda",
)
