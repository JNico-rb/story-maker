"""`GET /view/versions/{version_id}` exige el token de vista antes de nada más: nunca revela si
la versión existe (013-C07, 013-I2), y sirve la `VistaDeVersion` de una versión, candidata o
publicada (013-C01 a 013-C05)."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.render.novela_fixture import DEDICATION, TITLE, Novela, build_novela

from story_maker.api.app import create_app
from story_maker.api.auth import create_access_token
from story_maker.api.view_tokens import create_view_token
from story_maker.store.session import create_schema, make_engine, make_session_factory

JWT_SECRET = "x" * 32
SESSION_TIMEOUT_SECONDS = 600
V1 = 1
V2 = 2


class FakeClock:
    def __init__(self, now: dt.datetime) -> None:
        self._now = now

    def __call__(self) -> dt.datetime:
        return self._now

    def set(self, now: dt.datetime) -> None:
        self._now = now


@pytest.fixture
def session_factory(tmp_path: Path) -> Iterator[sessionmaker[Session]]:
    engine = make_engine(tmp_path / "story-maker.db")
    create_schema(engine)
    yield make_session_factory(engine)
    engine.dispose()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC))


@pytest.fixture
def client(session_factory: sessionmaker[Session], clock: FakeClock) -> TestClient:
    app = create_app(session_factory=session_factory, jwt_secret=JWT_SECRET, clock=clock)
    return TestClient(app)


def _valid_v1_token(clock: FakeClock) -> str:
    return create_view_token(V1, JWT_SECRET, SESSION_TIMEOUT_SECONDS, clock())


def test_an_invalid_view_token_answers_401_without_revealing_whether_the_version_exists(
    client: TestClient, clock: FakeClock
) -> None:
    valid_for_v1 = _valid_v1_token(clock)

    presented_for_another_version = client.get(f"/view/versions/{V2}?token={valid_for_v1}")

    access_token_instead_of_view = client.get(
        f"/view/versions/{V1}?token={create_access_token(1, JWT_SECRET, 24, clock())}"
    )

    timeout = dt.timedelta(seconds=SESSION_TIMEOUT_SECONDS)
    clock.set(clock() + timeout)
    used_after_timeout = client.get(f"/view/versions/{V1}?token={valid_for_v1}")
    clock.set(clock() - timeout)

    header_b64, payload_b64, sig_b64 = valid_for_v1.split(".")
    last_char = sig_b64[-1]
    tampered_sig = sig_b64[:-1] + ("A" if last_char != "A" else "B")
    tampered_signature = client.get(
        f"/view/versions/{V1}?token={header_b64}.{payload_b64}.{tampered_sig}"
    )

    missing_token = client.get(f"/view/versions/{V1}")

    responses = [
        presented_for_another_version,
        access_token_instead_of_view,
        used_after_timeout,
        tampered_signature,
        missing_token,
    ]
    for response in responses:
        assert response.status_code == 401, response.text
    bodies = {response.text for response in responses}
    assert len(bodies) == 1


# --- VistaDeVersion: 013-C01 a 013-C05 ----------------------------------------------------------


@pytest.fixture
def novela(session_factory: sessionmaker[Session]) -> Novela:
    return build_novela(session_factory)


def _token(version_id: int, clock: FakeClock) -> str:
    return create_view_token(version_id, JWT_SECRET, SESSION_TIMEOUT_SECONDS, clock())


def _view(client: TestClient, version_id: int, clock: FakeClock) -> str:
    response = client.get(f"/view/versions/{version_id}?token={_token(version_id, clock)}")
    assert response.status_code == 200, response.text
    return response.text


def _li_for(html: str, name: str) -> str:
    """El `<li>...</li>` de la ficha que nombra a `name` (013-C03: sin `<a>` si no aparece)."""
    match = re.search(rf"<li>\s*{re.escape(name)}:.*?</li>", html, re.DOTALL)
    assert match is not None, f"{name} no aparece en la ficha"
    return match.group(0)


def test_c01_cover_index_and_ficha_of_a_version_without_changed_chapters(
    client: TestClient, clock: FakeClock, novela: Novela
) -> None:
    html = _view(client, novela.v1_id, clock)

    assert TITLE in html
    assert "Ada" in html
    assert DEDICATION in html
    assert "novedades" not in html.lower()
    for n in range(1, 11):
        assert f'href="#cap-{n}"' in html
        assert f'id="cap-{n}"' in html
        assert f"Texto del capítulo {n}, con Ada." in html

    assert '<a href="#cap-1">' in _li_for(html, "Ada")
    assert '<a href="#cap-4">' in _li_for(html, "el bosque")


def test_c02_whats_new_page_and_changed_mark(
    client: TestClient, clock: FakeClock, novela: Novela
) -> None:
    html = _view(client, novela.v2_id, clock)

    assert "novedades" in html.lower()
    novedades_start = html.lower().index("novedades")
    novedades_section = html[novedades_start : novedades_start + 500]
    assert 'href="#cap-3"' in novedades_section
    assert 'href="#cap-7"' in novedades_section

    changed_chapters = {
        int(n)
        for n in re.findall(r'href="#cap-(\d+)">\d+\. [^<]*</a>\s*<span class="cambiado">', html)
    }
    assert changed_chapters == {3, 7}
    assert "cambiado en v2" in html


def test_c03_an_entity_without_a_chapter_appears_in_the_ficha_without_links(
    client: TestClient, clock: FakeClock, novela: Novela
) -> None:
    html = _view(client, novela.v1_id, clock)

    simon_li = _li_for(html, "Simón")
    assert "<a" not in simon_li


def test_c04_the_version_view_also_serves_a_candidate(
    client: TestClient, clock: FakeClock, novela: Novela
) -> None:
    html = _view(client, novela.k_id, clock)

    assert TITLE in html
    assert "novedades" not in html.lower()  # K es copia de V2 sin cambios propios todavía
    for n in range(1, 11):
        assert f'href="#cap-{n}"' in html
        assert f'id="cap-{n}"' in html
    assert "Nala" in _li_for(html, "Nala")
    assert "Texto nuevo del capítulo 3, con Nala." in html


def test_c05_two_versions_of_the_same_novel_do_not_mix(
    client: TestClient, clock: FakeClock, novela: Novela
) -> None:
    v1_html = _view(client, novela.v1_id, clock)
    v2_html = _view(client, novela.v2_id, clock)

    assert "Toby" in v1_html
    assert "Nala" not in v1_html
    assert "Nala" in v2_html
    assert "Toby" not in v2_html
    assert "Texto del capítulo 3, con Ada." in v1_html
    assert "Texto nuevo del capítulo 3, con Nala." in v2_html
    assert "Texto nuevo del capítulo 3, con Nala." not in v1_html
    assert "Texto del capítulo 3, con Ada." not in v2_html
