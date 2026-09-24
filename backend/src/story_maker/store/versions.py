"""Estados de una `Version`: candidata → publicada | descartada; el número, los capítulos cambiados
y la versión vigente (`architecture.md` §9.3; 009-C17 a 009-C22).

Cuándo se publica o se descarta lo deciden 012 y 011; aquí solo el cambio de estado y sus guardas.
"""

from __future__ import annotations

import datetime as dt
from typing import NoReturn

from sqlalchemy.orm import Session

from story_maker.store.models import Chapter, Version
from story_maker.store.session import UnitOfWork
from story_maker.store.version_guard import STATE_NAMES, version_label


class VersionTransitionRejected(ValueError):
    """Una publicación o un descarte que no sale de una candidata válida (009-C20)."""


def current_version(session: Session, novel_id: int) -> Version | None:
    """La versión vigente: la publicada de número más alto, o ninguna."""
    return (
        session.query(Version)
        .filter(Version.novel_id == novel_id, Version.status == "published")
        .order_by(Version.number.desc())
        .first()
    )


def published_version(session: Session, novel_id: int, number: int) -> Version | None:
    """La versión publicada `number` de la novela, o ninguna."""
    return (
        session.query(Version)
        .filter(
            Version.novel_id == novel_id, Version.status == "published", Version.number == number
        )
        .one_or_none()
    )


def publish(uow: UnitOfWork, version_id: int, *, pdf_path: str, now: dt.datetime) -> Version:
    """Publica la candidata con el número siguiente al de la vigente. Exige que su base sea la
    vigente; la de generación, que no haya ninguna publicada (historia lineal, 009-I5)."""
    version = _version(uow.session, version_id)
    if version.status == "published":
        _reject(version, "ya está publicada")
    if version.status == "discarded":
        _reject(version, "está descartada")
    current = current_version(uow.session, version.novel_id)
    if version.base_version_id is None and current is not None:
        _reject(version, "ya hay una versión publicada")
    if version.base_version_id is not None and (
        current is None or current.id != version.base_version_id
    ):
        _reject(version, "su versión base no es la vigente")
    # Todo se lee antes de escribir: tras el primer vaciado la versión ya está publicada y la
    # guarda rechazaría el resto (009-I1).
    changed = changed_chapters(uow.session, version)
    version.status = "published"
    version.number = current.number + 1 if current and current.number else 1
    version.published_at = now
    version.pdf_path = pdf_path
    version.changed_chapters = changed
    uow.session.flush()
    return version


def discard(uow: UnitOfWork, version_id: int) -> Version:
    """Descarta la candidata: queda sin número y no admite más escrituras."""
    version = _version(uow.session, version_id)
    if version.status != "candidate":
        _reject(version, f"está {STATE_NAMES[version.status]}")
    version.status = "discarded"
    uow.session.flush()
    return version


def _version(session: Session, version_id: int) -> Version:
    version = session.get(Version, version_id)
    if version is None:
        raise LookupError(f"no existe la versión {version_id}")
    return version


def _reject(version: Version, reason: str) -> NoReturn:
    raise VersionTransitionRejected(f"la {version_label(version)} {reason}")


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
