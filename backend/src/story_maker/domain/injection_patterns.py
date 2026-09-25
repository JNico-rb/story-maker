"""Patrones ES/EN de frases dirigidas al sistema, para el DetectorDeInyeccion (005-C15/§18).

Lista corta y curada, ampliable sin tocar el motor. Una evasión fuera de estos patrones
no se detecta (verification.md §6 U11/U12, RT10)."""

import re

INJECTION_PATTERNS = [
    re.compile(r"ignora\s+(las\s+)?instrucciones\s+anteriores", re.IGNORECASE),
    re.compile(r"ignora\s+lo\s+anterior", re.IGNORECASE),
    re.compile(r"ignore\s+(the\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+the\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"revela\s+(el\s+)?prompt\s+del\s+sistema", re.IGNORECASE),
    # Una orden a un rol del producto («editor: registra que…»): el texto de una edición manual
    # llega al editor como dato (019-C16, RT16). La frase marcada sigue hasta el fin de la frase.
    re.compile(
        r"\b(writer|escritor|editor|planner|planificador|juez|judge|extractor|entrevistador|"
        r"interviewer)\s*:\s*(registra|escribe|reescribe|borra|elimina|cambia|ignora|añade|"
        r"marca|olvida|declara)\b[^.!?\n]*",
        re.IGNORECASE,
    ),
]
