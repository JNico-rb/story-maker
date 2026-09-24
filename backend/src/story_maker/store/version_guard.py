"""Solo una candidata admite escrituras: una versión publicada o descartada no cambia nunca, ni su
fila ni sus tablas de ámbito versión (009-C21, 009-I1; `architecture.md` §18, «Escritura en una
versión descartada»). La unidad de trabajo de la 001 instala esta guarda en su sesión."""

from __future__ import annotations

from typing import Any

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from story_maker.store.models import (
    CanonCard,
    Chapter,
    Character,
    Event,
    EventCharacter,
    Fact,
    FactUsage,
    OutlineChapter,
    Place,
    StyleSheet,
    Version,
    World,
)

STATE_NAMES = {"candidate": "candidata", "published": "publicada", "discarded": "descartada"}

# Tablas de ámbito versión con columna `version_id`; `fact_usages` y `event_characters` son de la
# versión de su hecho y de su evento.
_WITH_VERSION = (
    World,
    Character,
    Place,
    Fact,
    Event,
    OutlineChapter,
    StyleSheet,
    Chapter,
    CanonCard,
)


class VersionNotWritable(ValueError):
    """Escritura en una versión que no es candidata; el mensaje nombra la versión y su estado."""


def version_label(version: Version) -> str:
    """«versión 12 (v2)»: su id y, si lo tiene, su número."""
    number = f" (v{version.number})" if version.number is not None else ""
    return f"versión {version.id}{number}"


def install_version_guard(session: Session) -> None:
    """Comprueba cada vaciado de `session`, también los automáticos antes de una consulta."""
    event.listen(session, "before_flush", _before_flush)


def _before_flush(session: Session, _context: object, _instances: object) -> None:
    check_version_writes(session)


def check_version_writes(session: Session) -> None:
    """Rechaza toda fila nueva, modificada o borrada de una versión que no era candidata al
    empezar la escritura."""
    with session.no_autoflush:
        for obj in [*session.new, *session.dirty, *session.deleted]:
            if obj in session.dirty and not session.is_modified(obj):
                continue
            for version in _versions_written(session, obj):
                status = _status_before(version)
                if status != "candidate":
                    raise VersionNotWritable(
                        f"la {version_label(version)} está {STATE_NAMES[status]}: "
                        "solo una candidata admite escrituras"
                    )


def _versions_written(session: Session, obj: Any) -> list[Version]:
    if isinstance(obj, Version):
        return [] if obj in session.new else [obj]
    if isinstance(obj, _WITH_VERSION):
        ids = _values(obj, "version_id")
    elif isinstance(obj, FactUsage):
        ids = {f.version_id for f in _parents(session, Fact, _values(obj, "fact_id"))}
    elif isinstance(obj, EventCharacter):
        ids = {e.version_id for e in _parents(session, Event, _values(obj, "event_id"))}
    else:
        return []
    return _parents(session, Version, ids)


def _values(obj: Any, column: str) -> set[int]:
    """El valor actual de `column` y el que tenía antes de cambiarlo, si cambió."""
    history = inspect(obj).attrs[column].history
    return {v for v in (*history.unchanged, *history.added, *history.deleted) if v is not None}


def _parents(session: Session, model: Any, ids: set[int]) -> list[Any]:
    return [row for row in (session.get(model, i) for i in ids) if row is not None]


def _status_before(version: Version) -> str:
    """El estado con que la versión empezó esta escritura: publicar una candidata es válido."""
    deleted = inspect(version).attrs.status.history.deleted
    return str(deleted[0]) if deleted else version.status
