"""`InformeDeEjecucion`: se calcula de lo guardado cada vez que se pide, nunca se guarda
(`architecture.md` §8.2, §15.7; `definitions.md` §6; 011-C30)."""

from __future__ import annotations

from typing import Any, cast

from sqlalchemy import func
from sqlalchemy.orm import Session

from story_maker.store.models import Attempt, AuditLog, RoleSession, Run, ValidatorResult


def run_cost(session: Session, run_id: int) -> float:
    """La suma en USD del coste de las `SesionDeRol` de la ejecución."""
    total = session.query(func.sum(RoleSession.cost_usd)).filter(RoleSession.run_id == run_id)
    return float(total.scalar() or 0.0)


def _validators(session: Session, run_id: int) -> list[dict[str, Any]]:
    rows = session.query(ValidatorResult).filter(ValidatorResult.run_id == run_id)
    return [
        {
            "chapter": r.chapter,
            "attempt": cast(dict[str, Any], r.detail).get("attempt"),
            "validator": r.validator,
            "passed": r.passed,
            "defects": cast(dict[str, Any], r.detail).get("defects", []),
        }
        for r in rows.order_by(ValidatorResult.id)
    ]


def _unresolved(validators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Los defectos del último intento de cada capítulo: los no bloqueantes de uno aceptado, o
    los que dejó el intento en que se agotó."""
    last: dict[int, int] = {}
    for v in validators:
        if v["chapter"] is not None and v["attempt"] is not None:
            last[v["chapter"]] = max(last.get(v["chapter"], 0), v["attempt"])
    return [
        {"chapter": v["chapter"], "attempt": v["attempt"], **d}
        for v in sorted(validators, key=lambda v: v["chapter"] or 0)
        if v["chapter"] in last and v["attempt"] == last[v["chapter"]]
        for d in v["defects"]
    ]


def build_report(session: Session, run: Run) -> dict[str, Any]:
    validators = _validators(session, run.id)
    attempts = session.query(Attempt).filter(Attempt.run_id == run.id)
    decisions = session.query(AuditLog).filter(AuditLog.run_id == run.id)
    return {
        "run_id": run.id,
        "type": run.type,
        "status": run.status,
        "reason": run.reason,
        "reason_detail": run.reason_detail,
        "resumes": run.resumes,
        "cost_usd": run_cost(session, run.id),
        "attempts": [
            {
                "evaluable": a.evaluable,
                "chapter": a.chapter,
                "gate_cycle": a.gate_cycle,
                "number": a.number,
                "outcome": a.outcome,
            }
            for a in attempts.order_by(Attempt.chapter, Attempt.number, Attempt.id)
        ],
        "validators": [
            {k: v[k] for k in ("chapter", "attempt", "validator", "passed")} for v in validators
        ],
        "unresolved": _unresolved(validators),
        "policy_decisions": [
            {
                "role": d.role,
                "tool": d.tool,
                "origin": d.origin,
                "decision": d.decision,
                "rule": d.rule,
                "detail": d.detail,
            }
            for d in decisions.order_by(AuditLog.id)
        ],
    }
