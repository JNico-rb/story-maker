"""Con los mismos datos de versión, la `VistaDeVersion` y el PDF que produce son iguales
(013-I5): genera dos veces la vista de V1 y compara el HTML; genera dos veces su PDF y compara
el resultado de `pdf-enlaces` y el número de capítulos."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import build_novela

from story_maker.render.pdf import render_pdf
from story_maker.render.pdf_links import check_pdf_links
from story_maker.render.version_view import render_version_view
from story_maker.render.view_data import load_version_view_data
from story_maker.store.models import Version
from story_maker.store.session import create_schema, make_engine, make_session_factory


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


def test_the_same_version_data_yields_the_same_version_view_and_pdf(
    session_factory: sessionmaker[Session],
) -> None:
    novela = build_novela(session_factory)
    with session_factory() as session:
        version = session.get(Version, novela.v1_id)
        assert version is not None
        data = load_version_view_data(session, version)

    html_first = render_version_view(data)
    html_second = render_version_view(data)
    assert html_first == html_second

    pdf_first = render_pdf(html_first)
    pdf_second = render_pdf(html_second)
    result_first = check_pdf_links(pdf_first)
    result_second = check_pdf_links(pdf_second)

    assert result_first.passed
    assert result_second.passed
    assert result_first == result_second
    assert len(data.chapters) == 10
