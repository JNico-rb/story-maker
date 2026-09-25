"""Presentación impresa de la `VistaDeVersion` (013-C20 a 013-C23, carril R 2026-09-25): portada
sola en la primera página, índice sin número duplicado, cada bloque en su propia página y números
de página al pie salvo en la portada."""

from __future__ import annotations

import io
import re

import pytest
from pypdf import PdfReader

from story_maker.render.pdf import render_pdf
from story_maker.render.version_view import (
    CapituloVista,
    EntidadFicha,
    VersionViewData,
    render_version_view,
)


def _v1_data() -> VersionViewData:
    """V1: sin capítulos cambiados, sin página de novedades (misma convención que la spec)."""
    chapters = [
        CapituloVista(
            number=n,
            title=f"El día {n}",
            text=(
                f"Ada vive el suceso número {n} de su aventura personal.\n\n"
                f"Un segundo párrafo cierra el capítulo {n}."
            ),
        )
        for n in range(1, 11)
    ]
    return VersionViewData(
        title="La aventura de Ada",
        recipient="Ada",
        dedication="Para Ada, con todo el cariño.",
        version_number=1,
        chapters=chapters,
        changed_chapters=[],
        ficha=[
            EntidadFicha(name="Ada", kind="personaje", chapters=list(range(1, 11))),
            EntidadFicha(name="el bosque", kind="lugar", chapters=[4]),
        ],
    )


def _v2_data() -> VersionViewData:
    """V2: con página de novedades (capítulos 3 y 7 cambiados)."""
    data = _v1_data()
    return VersionViewData(
        title=data.title,
        recipient=data.recipient,
        dedication=data.dedication,
        version_number=2,
        chapters=data.chapters,
        changed_chapters=[3, 7],
        ficha=data.ficha,
    )


@pytest.fixture(scope="module")
def v1_pdf_pages() -> list[str]:
    html = render_version_view(_v1_data())
    pdf_bytes = render_pdf(html)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [page.extract_text() for page in reader.pages]


@pytest.fixture(scope="module")
def v2_pdf_pages() -> list[str]:
    html = render_version_view(_v2_data())
    pdf_bytes = render_pdf(html)
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [page.extract_text() for page in reader.pages]


def test_the_cover_page_alone_fills_the_first_page(v1_pdf_pages: list[str]) -> None:
    data = _v1_data()
    cover_text = v1_pdf_pages[0]

    assert data.title in cover_text
    assert f"Para {data.recipient}" in cover_text
    assert data.dedication in cover_text
    assert "Índice" not in cover_text
    assert "Novedades" not in cover_text
    for chapter in data.chapters:
        assert chapter.title not in cover_text


def test_the_index_shows_each_chapter_number_once(v1_pdf_pages: list[str]) -> None:
    html = render_version_view(_v1_data())

    assert "1. 1." not in html
    assert not re.search(r"\b(\d+)\.\s*\1\.", html)

    full_text = "\n".join(v1_pdf_pages)
    assert "1. 1." not in full_text
    assert not re.search(r"\b(\d+)\.\s*\1\.", full_text)

    index_page = next(page for page in v1_pdf_pages if "Índice" in page)
    for chapter in _v1_data().chapters:
        assert index_page.count(f"{chapter.number}. {chapter.title}") == 1


def test_novelties_index_each_chapter_and_ficha_start_on_their_own_page(
    v2_pdf_pages: list[str],
) -> None:
    data = _v2_data()

    def has_novedades(text: str) -> bool:
        return "Novedades" in text

    def has_indice(text: str) -> bool:
        return "Índice" in text

    def has_ficha(text: str) -> bool:
        return "Ficha de personajes" in text

    def has_chapter(text: str, n: int) -> bool:
        # El propio cuerpo del capítulo (no una simple mención, como la de la página de
        # novedades enlazando "Capítulo 3"): el primer párrafo solo vive en su artículo.
        return f"suceso número {n} de su aventura" in text

    for page_text in v2_pdf_pages:
        blocks_present = [has_novedades(page_text), has_indice(page_text), has_ficha(page_text)] + [
            has_chapter(page_text, n) for n in range(1, 11)
        ]
        assert sum(1 for present in blocks_present if present) <= 1, page_text

    chapter_page = next(page for page in v2_pdf_pages if has_chapter(page, 1))
    assert data.chapters[0].title in chapter_page
    number_pos = re.search(r"Cap[íi]tulo 1(?!\d)", chapter_page)
    title_pos = chapter_page.find(data.chapters[0].title)
    assert number_pos is not None
    assert number_pos.start() < title_pos


def test_every_page_but_the_cover_shows_its_page_number_at_the_foot(
    v1_pdf_pages: list[str],
) -> None:
    """Los números de página van en la caja de margen `@bottom-center` de `@page` (que Chromium
    respeta): pypdf extrae ese texto como una línea aislada; no importa su posición en el orden
    de extracción, solo que la portada no tenga ninguna y el resto sí, una por página."""

    def page_number_line(text: str) -> str | None:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return next((line for line in lines if line.isdigit()), None)

    assert page_number_line(v1_pdf_pages[0]) is None

    for index, page_text in enumerate(v1_pdf_pages[1:], start=2):
        assert page_number_line(page_text) == str(index), page_text
