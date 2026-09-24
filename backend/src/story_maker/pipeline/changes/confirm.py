"""Confirmar una solicitud con su código: un solo uso, caducidad y cola de una ejecución
`change_request` con su versión base (`architecture.md` §10.1, §15.7; 014-C10, 014-C11, 014-I4).

La propiedad (404) la comprueba la ruta, como en el resto de la API (002)."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from hmac import compare_digest

from sqlalchemy.orm import Session, sessionmaker

from story_maker.pipeline.changes.request import hash_code
from story_maker.pipeline.runs import naive
from story_maker.store.models import ChangeRequest, Run
from story_maker.store.session import unit_of_work

NOT_PROPOSED = "not_proposed"
EXPIRED = "expired"
WRONG_CODE = "wrong_code"


@dataclass(frozen=True)
class ConfirmFailure:
    status: int
    detail: str


def confirm_change(
    session_factory: sessionmaker[Session], *, request_id: int, code: str, now: dt.datetime
) -> int | ConfirmFailure:
    """El id de la ejecución encolada, o por qué no se encola nada. Una solicitud es confirmable
    mientras ahora < caducidad; al vencer queda `expired`, aunque el código sea el correcto."""
    with unit_of_work(session_factory) as uow:
        row = uow.session.get_one(ChangeRequest, request_id)
        # Una `proposed` siempre tiene caducidad y código (014-C01).
        if row.status != "proposed" or row.expires_at is None or row.code_hash is None:
            return ConfirmFailure(409, NOT_PROPOSED)
        if naive(now) >= row.expires_at:
            row.status = "expired"
            return ConfirmFailure(409, EXPIRED)
        if not compare_digest(hash_code(code), row.code_hash):
            return ConfirmFailure(422, WRONG_CODE)
        run = Run(
            novel_id=row.novel_id,
            type="change_request",
            status="queued",
            base_version_id=row.base_version_id,
            resumes=0,
            created_at=naive(now),
        )
        uow.add(run)
        uow.session.flush()
        row.run_id = run.id
        row.status = "confirmed"
        return run.id
