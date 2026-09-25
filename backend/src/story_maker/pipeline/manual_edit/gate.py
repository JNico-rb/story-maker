"""El capítulo editado en el gate (`architecture.md` §10.3; 019-C23, 019-C25, 019-I7): un
bloqueante que se le atribuye rechaza la edición, porque reescribirlo tocaría lo que dejó la
persona. La excepción es un fallo de datos de `revision-visual`: se corrige volviendo a
registrarlo, sin tocar su texto."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Session, sessionmaker

from story_maker.formal.defects import Defect
from story_maker.pipeline.gate.precedence import PassVerdict
from story_maker.store.models import ManualEdit

VISUAL_REVIEW = "revision-visual"


def edited_chapter(session_factory: sessionmaker[Session], run_id: int) -> int | None:
    """El capítulo de la edición manual de la ejecución, o ninguno si no es una edición."""
    with session_factory() as session:
        edit = session.query(ManualEdit).filter(ManualEdit.run_id == run_id).one_or_none()
        return edit.chapter if edit is not None else None


def edit_rejection(
    edited: int | None, verdict: PassVerdict, defects: Sequence[Defect]
) -> str | None:
    """El detalle de `edit_rejected` si la pasada reescribiría o agotaría sus ciclos con algún
    bloqueante atribuido al capítulo editado que no sea de `revision-visual`."""
    if edited is None:
        return None
    if verdict.outcome != "rewrite" and verdict.reason != "retries_exhausted":
        return None
    blocking = [
        d.message
        for d in defects
        if d.blocking and d.chapter == edited and d.validator != VISUAL_REVIEW
    ]
    if not blocking:
        return None
    return f"capítulo {edited} editado: " + "; ".join(blocking)
