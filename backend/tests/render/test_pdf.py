"""El PDF se genera desde la `VistaDeVersion` con sus 10 capítulos (013-C08)."""

from __future__ import annotations

import io

from pypdf import PdfReader

from story_maker.render.pdf import render_pdf
from story_maker.render.version_view import CapituloVista, VersionViewData, render_version_view


def _version_view_data() -> VersionViewData:
    chapters = [
        CapituloVista(
            number=n,
            title=f"Capítulo {n} de la aventura",
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
        ficha=[],
    )


def test_the_pdf_is_generated_from_the_version_view_with_its_ten_chapters() -> None:
    data = _version_view_data()
    html = render_version_view(data)

    pdf_bytes = render_pdf(html)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert reader.trailer["/Root"]["/MarkInfo"]["/Marked"]  # etiquetado (tagged)
    assert reader.outline  # marcadores (outline)

    named_anchors = set(reader.named_destinations)
    assert {f"/cap-{n}" for n in range(1, 11)} <= named_anchors

    text = "\n".join(page.extract_text() for page in reader.pages)
    for chapter in data.chapters:
        assert chapter.title in text
        first_paragraph = chapter.text.split("\n\n")[0]
        assert first_paragraph in text
