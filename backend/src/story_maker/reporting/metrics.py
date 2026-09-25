"""Agrega `role_sessions` y `validator_results` en el Markdown de `report metrics` (030)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from story_maker.store.models import RoleSession, Run, ValidatorResult

SIN_EJECUCIONES = "No hay ejecuciones.\n"
HUECO = "hueco"

_NUMERIC_FIELDS: tuple[str, ...] = (
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cost_usd",
    "latency_ms",
)

_NUMERIC_HEADERS: tuple[str, ...] = (
    "tokens entrada",
    "tokens salida",
    "tokens caché lectura",
    "tokens caché escritura",
    "coste USD",
    "latencia ms",
)


def _format_number(field_name: str, value: float) -> str:
    return f"{value:.4f}" if field_name == "cost_usd" else str(int(value))


@dataclass
class _Accumulator:
    """Suma de los campos numéricos de un grupo de sesiones; hueco si alguna falta (030-C06)."""

    count: int = 0
    sums: dict[str, float] = field(default_factory=lambda: dict.fromkeys(_NUMERIC_FIELDS, 0.0))
    gaps: set[str] = field(default_factory=set)

    def add(self, role_session: RoleSession) -> None:
        self.count += 1
        for name in _NUMERIC_FIELDS:
            value = getattr(role_session, name)
            if value is None:
                self.gaps.add(name)
            else:
                self.sums[name] += value

    def cell(self, field_name: str) -> str:
        if field_name in self.gaps:
            return HUECO
        return _format_number(field_name, self.sums[field_name])

    def sort_value(self, field_name: str) -> float:
        """0 para una celda hueco: solo para ordenar filas, nunca para mostrarlas."""
        return 0.0 if field_name in self.gaps else self.sums[field_name]

    def cells(self) -> list[str]:
        return [self.cell(name) for name in _NUMERIC_FIELDS]


def _table(headers: Sequence[str], rows: Iterable[Sequence[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def _novel_section(sessions: list[RoleSession]) -> str:
    accumulators: dict[int, _Accumulator] = defaultdict(_Accumulator)
    runs: dict[int, set[int]] = defaultdict(set)
    for role_session in sessions:
        accumulators[role_session.novel_id].add(role_session)
        if role_session.run_id is not None:
            runs[role_session.novel_id].add(role_session.run_id)

    rows = [
        [str(novel_id), str(len(runs.get(novel_id, ()))), *accumulators[novel_id].cells()]
        for novel_id in sorted(accumulators)
    ]
    headers = ["novela", "ejecuciones", *_NUMERIC_HEADERS]
    return "## Por novela\n\n" + _table(headers, rows)


def _chapter_section(sessions: list[RoleSession]) -> str:
    accumulators: dict[tuple[int, int], _Accumulator] = defaultdict(_Accumulator)
    for role_session in sessions:
        if role_session.chapter is None:
            continue
        accumulators[(role_session.novel_id, role_session.chapter)].add(role_session)

    rows = [
        [str(novel_id), str(chapter), *accumulators[(novel_id, chapter)].cells()]
        for novel_id, chapter in sorted(accumulators)
    ]
    headers = ["novela", "capítulo", *_NUMERIC_HEADERS]
    return "## Por capítulo\n\n" + _table(headers, rows)


def _role_section(sessions: list[RoleSession]) -> str:
    accumulators: dict[str, _Accumulator] = defaultdict(_Accumulator)
    for role_session in sessions:
        accumulators[role_session.role].add(role_session)

    total_cost = sum(acc.sort_value("cost_usd") for acc in accumulators.values())

    def _sort_key(role: str) -> tuple[float, str]:
        return (-accumulators[role].sort_value("cost_usd"), role)

    roles = sorted(accumulators, key=_sort_key)

    rows = []
    for role in roles:
        acc = accumulators[role]
        if "cost_usd" in acc.gaps or total_cost == 0:
            percent = HUECO if "cost_usd" in acc.gaps else "0.0%"
        else:
            percent = f"{acc.sums['cost_usd'] / total_cost * 100:.1f}%"
        rows.append([role, str(acc.count), *acc.cells(), percent])

    headers = ["rol", "sesiones", *_NUMERIC_HEADERS, "% coste"]
    return "## Por rol\n\n" + _table(headers, rows)


def _score_cell(value: float | None) -> str:
    return HUECO if value is None else f"{value:.4f}"


def _validator_section(results: list[ValidatorResult], run_novel: dict[int, int]) -> str:
    groups: dict[tuple[int, str], list[ValidatorResult]] = defaultdict(list)
    for result in results:
        groups[(run_novel[result.run_id], result.validator)].append(result)

    rows = []
    for novel_id, validator in sorted(groups):
        items = groups[(novel_id, validator)]
        scores = [item.score for item in items if item.score is not None]
        avg = sum(scores) / len(scores) if scores else None
        lo = min(scores) if scores else None
        hi = max(scores) if scores else None
        rows.append(
            [
                str(novel_id),
                validator,
                str(len(items)),
                str(sum(1 for item in items if item.passed)),
                _score_cell(avg),
                _score_cell(lo),
                _score_cell(hi),
            ]
        )

    headers = [
        "novela",
        "validador",
        "resultados",
        "pasan",
        "score medio",
        "score mínimo",
        "score máximo",
    ]
    return "## Scores por validador y novela\n\n" + _table(headers, rows)


def _prompt_version_section(sessions: list[RoleSession]) -> str:
    groups: dict[tuple[int, str], set[str]] = defaultdict(set)
    for role_session in sessions:
        if role_session.run_id is None:
            continue
        version = role_session.prompt_version if role_session.prompt_version is not None else HUECO
        groups[(role_session.run_id, role_session.role)].add(version)

    rows = [
        [str(run_id), role, ", ".join(sorted(groups[(run_id, role)]))]
        for run_id, role in sorted(groups)
    ]
    headers = ["ejecución", "rol", "versiones"]
    return "## Versiones de prompt\n\n" + _table(headers, rows)


def build_report(session: Session) -> str:
    """Markdown determinista con lo que hay en `role_sessions` y `validator_results` (I1)."""
    sessions = list(session.scalars(select(RoleSession)))
    results = list(session.scalars(select(ValidatorResult)))

    if not sessions and not results:
        return SIN_EJECUCIONES

    run_novel: dict[int, int] = dict(session.execute(select(Run.id, Run.novel_id)).tuples().all())

    sections = [
        _novel_section(sessions),
        _chapter_section(sessions),
        _role_section(sessions),
        _validator_section(results, run_novel),
        _prompt_version_section(sessions),
    ]
    return "\n\n".join(sections) + "\n"
