"""`story-maker export-pdf <novela> <v>` (013-C17, 013-C18, 013-I4)."""

from __future__ import annotations

import datetime as dt
import hashlib
import socket
from pathlib import Path

import pytest
from pypdf import PdfReader
from typer.testing import CliRunner

import story_maker.cli as cli_module
import story_maker.settings as settings_module
from story_maker.cli import app
from story_maker.render.pdf_links import check_pdf_links
from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefRecipient,
    ConfirmedBrief,
    create_generation_candidate,
)
from story_maker.store.session import create_schema, make_engine, make_session_factory, unit_of_work
from story_maker.store.versions import publish

NOW = dt.datetime(2026, 9, 24, 11, 0)
runner = CliRunner()


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(settings_module, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def base_env(monkeypatch: pytest.MonkeyPatch, isolated_root: Path) -> Path:
    monkeypatch.setenv("JWT_SECRET", "x" * 32)
    monkeypatch.setenv("FORMAL_VERIFIER", "local")
    monkeypatch.setenv("STORY_MAKER_BASE_URL", f"http://127.0.0.1:{_free_port()}")
    return isolated_root


def _data_dir(base_env: Path) -> Path:
    return base_env / "backend" / "data"


def _db_path(base_env: Path) -> Path:
    return _data_dir(base_env) / "story-maker.db"


def _chapter_hash(title: str, text: str) -> str:
    return hashlib.sha256(f"{title}\n{text}".encode()).hexdigest()


def _seed_published_novel(db_path: Path, *, pdf_path: Path) -> tuple[int, int]:
    """Una novela con una versión publicada, sus 10 capítulos y `pdf_path`, sin pasar por
    010/011/012 (013 no depende de ellas para tener una versión ya publicada)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    session_factory = make_session_factory(engine)

    with unit_of_work(session_factory) as uow:
        user = models.User(email="cliente-a@example.com", password_hash="h", created_at=NOW)
        uow.add(user)
        uow.session.flush()
        novel = models.Novel(user_id=user.id, title=None, embedding_model="m1", created_at=NOW)
        uow.add(novel)
        uow.session.flush()
        novel_id = novel.id

    brief = ConfirmedBrief(recipient=BriefRecipient("Ada", 30, name_element_id=1, traits=()))
    with unit_of_work(session_factory) as uow:
        version_id = create_generation_candidate(uow, novel_id, brief, now=NOW).id

    with unit_of_work(session_factory) as uow:
        for n in range(1, 11):
            title, text = f"Capítulo {n}", f"Texto del capítulo {n}, con Ada."
            uow.add(
                models.Chapter(
                    version_id=version_id,
                    number=n,
                    title=title,
                    text=text,
                    summary=f"Resumen {n}",
                    word_count=1200,
                    content_hash=_chapter_hash(title, text),
                )
            )

    with unit_of_work(session_factory) as uow:
        publish(uow, version_id, pdf_path=str(pdf_path), now=NOW)

    engine.dispose()
    return novel_id, version_id


def _version_row(db_path: Path, version_id: int) -> models.Version:
    engine = make_engine(db_path)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        version = session.get(models.Version, version_id)
        assert version is not None
        session.expunge(version)
    engine.dispose()
    return version


# --- 013-C17: export-pdf regenera el PDF de una versión publicada ------------------------------


def test_export_pdf_regenerates_the_pdf_from_the_version_view(base_env: Path) -> None:
    db_path = _db_path(base_env)
    pdf_path = _data_dir(base_env) / "novela.pdf"  # como la guardaría el gate (013-I4)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 version vieja")
    novel_id, version_id = _seed_published_novel(db_path, pdf_path=pdf_path)
    before = _version_row(db_path, version_id)

    result = runner.invoke(app, ["export-pdf", str(novel_id), "1"])

    assert result.exit_code == 0, result.stdout
    assert result.stdout.strip() == str(pdf_path)
    assert pdf_path.is_relative_to(_data_dir(base_env))  # 013-I4: solo dentro de la data dir
    new_bytes = pdf_path.read_bytes()
    assert new_bytes != b"%PDF-1.4 version vieja"

    link_result = check_pdf_links(new_bytes)
    assert link_result.passed, link_result

    text = "\n".join(page.extract_text() for page in PdfReader(pdf_path).pages)
    for n in range(1, 11):
        assert f"Texto del capítulo {n}, con Ada." in text

    after = _version_row(db_path, version_id)
    assert (before.status, before.number, before.published_at, before.changed_chapters) == (
        after.status,
        after.number,
        after.published_at,
        after.changed_chapters,
    )
    assert after.pdf_path == str(pdf_path)


# --- 013-C18: export-pdf sobre lo que no existe o no está publicado ----------------------------


def test_export_pdf_on_a_nonexistent_novel_writes_no_file(
    base_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _db_path(base_env)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(db_path)
    create_schema(engine)
    engine.dispose()

    def _must_not_render(html: str) -> bytes:
        raise AssertionError("no debe intentar generar el PDF (013-C18)")

    monkeypatch.setattr(cli_module, "render_pdf", _must_not_render)

    result = runner.invoke(app, ["export-pdf", "999999", "1"])

    assert result.exit_code != 0
    assert "999999" in result.stdout


def test_export_pdf_on_an_unpublished_version_writes_no_file(
    base_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _db_path(base_env)
    pdf_path = base_env / "no-debe-cambiar.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 no debe cambiar")
    novel_id, _version_id = _seed_published_novel(db_path, pdf_path=pdf_path)
    original_bytes = pdf_path.read_bytes()

    def _must_not_render(html: str) -> bytes:
        raise AssertionError("no debe intentar generar el PDF (013-C18)")

    monkeypatch.setattr(cli_module, "render_pdf", _must_not_render)

    result = runner.invoke(app, ["export-pdf", str(novel_id), "2"])

    assert result.exit_code != 0
    assert "2" in result.stdout
    assert pdf_path.read_bytes() == original_bytes


# --- 013-I4: el backend solo escribe el PDF de una versión en STORY_MAKER_DATA_DIR -------------


def test_export_pdf_refuses_to_write_outside_story_maker_data_dir(base_env: Path) -> None:
    """Un `pdf_path` fuera de `STORY_MAKER_DATA_DIR` (dato corrupto, o de otro origen) no se
    sobrescribe: sin la comprobación, `export-pdf` escribiría ahí sin más (013-I4)."""
    db_path = _db_path(base_env)
    outside_path = base_env / "fuera-de-la-data-dir.pdf"  # hermano de backend/, no dentro
    outside_path.write_bytes(b"%PDF-1.4 no debe cambiar")
    novel_id, _version_id = _seed_published_novel(db_path, pdf_path=outside_path)

    result = runner.invoke(app, ["export-pdf", str(novel_id), "1"])

    assert result.exit_code != 0
    assert str(outside_path) in result.stdout
    assert outside_path.read_bytes() == b"%PDF-1.4 no debe cambiar"
