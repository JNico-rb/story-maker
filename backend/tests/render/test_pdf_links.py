"""`pdf-enlaces` valida los enlaces internos (013-C09, 013-C10, 013-I1)."""

from __future__ import annotations

import io

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject

from story_maker.render.pdf import render_pdf
from story_maker.render.pdf_links import check_pdf_links
from story_maker.render.version_view import (
    CapituloVista,
    EntidadFicha,
    VersionViewData,
    render_version_view,
)


def _v2_data() -> VersionViewData:
    """Una versión con página de novedades (capítulos 3 y 7) y ficha con enlaces a capítulos."""
    chapters = [
        CapituloVista(
            number=n,
            title=f"Capítulo {n}",
            text=f"Sucede algo en el capítulo {n}.\n\nY un segundo párrafo.",
        )
        for n in range(1, 11)
    ]
    ficha = [
        EntidadFicha(name="Nala", kind="personaje", chapters=[1, 3]),
        EntidadFicha(name="Casa del bosque", kind="lugar", chapters=[7]),
    ]
    return VersionViewData(
        title="La aventura",
        recipient="Ada",
        dedication="Para Ada.",
        version_number=2,
        chapters=chapters,
        changed_chapters=[3, 7],
        ficha=ficha,
    )


def _break_first_internal_link(pdf_bytes: bytes) -> bytes:
    """No se puede fabricar el enlace roto imprimiendo HTML: Chromium lo descarta sin aviso
    (`verification.md` §8 H3). Se toma un PDF válido y se manipula uno de sus enlaces a mano,
    como pide 013-C10 («fabricado para la prueba»)."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter(clone_from=reader)
    for page in writer.pages:
        for annot_ref in page.get("/Annots") or []:
            annot = annot_ref.get_object()
            if annot.get("/Subtype") == "/Link" and isinstance(annot.get("/Dest"), str):
                annot[NameObject("/Dest")] = NameObject("/no-existe")
                buffer = io.BytesIO()
                writer.write(buffer)
                return buffer.getvalue()
    raise AssertionError("el PDF de prueba no tiene ningún enlace interno que romper")


@pytest.fixture(scope="module")
def v2_pdf_bytes() -> bytes:
    html = render_version_view(_v2_data())
    return render_pdf(html)


def test_pdf_links_passes_for_the_index_novelties_and_ficha_links_of_a_valid_pdf(
    v2_pdf_bytes: bytes,
) -> None:
    result = check_pdf_links(v2_pdf_bytes)

    assert result.passed
    assert result.missing_chapters == []
    assert result.broken_links == []


def test_pdf_links_fails_on_a_link_that_does_not_resolve(v2_pdf_bytes: bytes) -> None:
    broken_pdf = _break_first_internal_link(v2_pdf_bytes)

    result = check_pdf_links(broken_pdf)

    assert not result.passed
    assert any(link.target == "/no-existe" for link in result.broken_links)
