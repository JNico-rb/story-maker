"""Estados de una `Version`: candidata → publicada | descartada; el número, los capítulos cambiados
y la versión vigente (`architecture.md` §9.3; 009-C17 a 009-C22).

Cuándo se publica o se descarta lo deciden 012 y 011; aquí solo el cambio de estado y sus guardas.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from story_maker.store.models import Chapter, Version
from story_maker.store.session import UnitOfWork


def current_version(session: Session, novel_id: int) -> Version | None:
    """La versión vigente: la publicada de número más alto, o ninguna."""
    return (
        session.query(Version)
        .filter(Version.novel_id == novel_id, Version.status == "published")
        .order_by(Version.number.desc())
        .first()
    )


def publish(uow: UnitOfWork, version: Version, *, pdf_path: str, now: dt.datetime) -> Version:
    """Publica la candidata con el número siguiente al de la vigente."""
    current = current_version(uow.session, version.novel_id)
    version.status = "published"
    version.number = current.number + 1 if current and current.number else 1
    version.published_at = now
    version.pdf_path = pdf_path
    version.changed_chapters = changed_chapters(uow.session, version)
    uow.session.flush()
    return version


def discard(uow: UnitOfWork, version: Version) -> Version:
    """Descarta la candidata: queda sin número y no admite más escrituras."""
    version.status = "discarded"
    uow.session.flush()
    return version


def changed_chapters(session: Session, version: Version) -> list[int]:
    """Los capítulos cuya huella difiere de la de su versión base; vacía sin base
    (`definitions.md` §3 Version, capítulo cambiado)."""
    if version.base_version_id is None:
        return []
    base = _hashes(session, version.base_version_id)
    return sorted(n for n, h in _hashes(session, version.id).items() if base.get(n) != h)


def _hashes(session: Session, version_id: int) -> dict[int, str]:
    chapters = session.query(Chapter).filter(Chapter.version_id == version_id)
    return {c.number: c.content_hash for c in chapters}
