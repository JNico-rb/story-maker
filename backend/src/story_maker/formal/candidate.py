"""Verificación formal de la candidata de una ejecución (`architecture.md` §11.4).

Genera el `FicheroDeCronologia` desde la story bible de la candidata, lo guarda en el directorio
de datos (y solo allí, 007-I7), lo verifica y, si hay resultado, deja su fila en
`chronology_files` con la huella del fichero guardado (007-I12). Sin veredicto no hay fila. La
verificación, que puede durar minutos, corre fuera de toda transacción.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from story_maker.formal.defects import Defect, defects_from
from story_maker.formal.generator import generate_chronology_file
from story_maker.formal.result import ChronologyResult, VerificationOutcome, VerifierInterruption
from story_maker.formal.source import chronology_from
from story_maker.formal.verifier import FormalVerifier
from story_maker.store.chronology_files import record_chronology_file
from story_maker.store.models import Run
from story_maker.store.session import unit_of_work
from story_maker.store.story_bible import read_story_bible

CHRONOLOGY_DIR = "chronology_files"


@dataclass(frozen=True)
class CandidateVerification:
    """La salida para el gate: el resultado del fichero (con cumple sí/no por invariante) o su
    ausencia con el motivo, y los defectos si es `failed`."""

    outcome: VerificationOutcome
    defects: tuple[Defect, ...]
    file_path: Path
    content_hash: str


def chronology_file_path(data_dir: Path, content_hash: str) -> Path:
    """Dónde queda el fichero de una fila de `chronology_files`: se encuentra por su huella."""
    return data_dir / CHRONOLOGY_DIR / f"{content_hash}.lean"


def _detail(result: ChronologyResult) -> dict[str, Any]:
    if result.result == "error":
        return {"reason": result.reason}
    detail: dict[str, Any] = {"holds": dict(result.holds)}
    if result.witnesses:
        detail["witnesses"] = {t: list(w) for t, w in result.witnesses.items()}
    return detail


async def verify_candidate(
    session_factory: sessionmaker[Session],
    verifier: FormalVerifier,
    *,
    run_id: int,
    data_dir: Path,
    now: dt.datetime,
    k: int | None = None,
) -> CandidateVerification:
    with session_factory() as session:
        run = session.get(Run, run_id)
        if run is None or run.candidate_version_id is None:
            raise LookupError(f"la ejecución {run_id} no existe o no tiene candidata")
        bible = read_story_bible(session, run.candidate_version_id)
    content = generate_chronology_file(chronology_from(bible.chronology), k=k).encode("utf-8")
    content_hash = hashlib.sha256(content).hexdigest()
    path = chronology_file_path(data_dir, content_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)

    outcome = await verifier.verify(content.decode("utf-8"))
    if isinstance(outcome, VerifierInterruption):
        return CandidateVerification(outcome, (), path, content_hash)
    with unit_of_work(session_factory) as uow:
        record_chronology_file(
            uow,
            run_id=run_id,
            content_hash=content_hash,
            result=outcome.result,
            detail=_detail(outcome),
            now=now,
        )
    return CandidateVerification(outcome, defects_from(outcome, bible), path, content_hash)
