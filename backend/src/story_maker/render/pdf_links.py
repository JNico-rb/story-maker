"""`pdf-enlaces`: el PDF tiene los `CHAPTERS_PER_NOVEL` capítulos y sus enlaces internos (índice,
novedades, ficha) resuelven a un ancla existente en el mismo documento (013-C09, 013-C10, 013-I1).

Chromium descarta sin aviso un enlace interno a un ancla inexistente (`verification.md` §8 H3):
no aparece como anotación en el PDF, así que un enlace roto solo se detecta comparando contra el
esperado — aquí, el ancla que la anotación sí declara (`/Dest`) contra los destinos con nombre que
el propio PDF registra.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from pypdf import PdfReader
from pypdf.generic import IndirectObject

from story_maker.domain.constants import CHAPTERS_PER_NOVEL

CHAPTER_ANCHOR = "cap-{n}"


@dataclass(frozen=True, slots=True)
class EnlaceRoto:
    """Un enlace interno cuyo `/Dest` no resuelve a un ancla del documento."""

    page_index: int
    target: str


@dataclass(frozen=True, slots=True)
class ResultadoPdfEnlaces:
    """Único resultado que envía `pdf-enlaces` (0/1, `architecture.md` §11.2)."""

    passed: bool
    missing_chapters: list[int] = field(default_factory=list)
    broken_links: list[EnlaceRoto] = field(default_factory=list)


def check_pdf_links(
    pdf_bytes: bytes, *, expected_chapters: int = CHAPTERS_PER_NOVEL
) -> ResultadoPdfEnlaces:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    named = reader.named_destinations
    page_ids = {_ref_id(page.indirect_reference): index for index, page in enumerate(reader.pages)}

    missing_chapters = [
        n for n in range(1, expected_chapters + 1) if f"/{CHAPTER_ANCHOR.format(n=n)}" not in named
    ]

    broken_links: list[EnlaceRoto] = []
    for page_index, page in enumerate(reader.pages):
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            if annot.get("/Subtype") != "/Link":
                continue
            target = _internal_target(annot)
            if target is None:
                continue  # enlace externo (http): fuera del alcance de pdf-enlaces
            destination = named.get(target)
            if destination is None or _ref_id(destination["/Page"]) not in page_ids:
                broken_links.append(EnlaceRoto(page_index=page_index, target=target))

    return ResultadoPdfEnlaces(
        passed=not missing_chapters and not broken_links,
        missing_chapters=missing_chapters,
        broken_links=broken_links,
    )


def _internal_target(annot: dict[str, object]) -> str | None:
    dest = annot.get("/Dest")
    if dest is None:
        action = annot.get("/A")
        if isinstance(action, dict) and action.get("/S") == "/GoTo":
            dest = action.get("/D")
    return dest if isinstance(dest, str) else None


def _ref_id(ref: object) -> tuple[int, int] | None:
    """`(idnum, generation)` de una referencia indirecta, o `None` si no lo es."""
    if isinstance(ref, IndirectObject):
        return (ref.idnum, ref.generation)
    resolved = getattr(ref, "indirect_reference", None)
    return _ref_id(resolved) if resolved is not None else None
