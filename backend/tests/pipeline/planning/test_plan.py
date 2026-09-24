"""Schema de `submit_plan` (010-C08).

El mecanismo genérico de recuperación en la misma sesión (el error vuelve al modelo, el
intento se cierra con `rewrite`) ya lo prueba 003 (`tests/agents/test_port.py`,
`test_an_invalid_input_returns_to_the_model_as_an_error_and_is_fixed_in_the_same_session`).
Aquí solo se prueban los límites propios del schema de 010: el número de consecuencias del
mundo y el ámbito del novum. `ToolSpec.validate` es la vía real por la que el puerto de
agente valida una entrega (`agents/tools.py`)."""

from __future__ import annotations

import datetime as dt
from typing import Any

from story_maker.agents.tools import ToolSpec
from story_maker.pipeline.planning.plan import PlanSubmission

SUBMIT_PLAN = ToolSpec(name="submit_plan", model=PlanSubmission)


def _plan(*, consequences: list[str], novum_scope: str = "technological") -> dict[str, Any]:
    return {
        "world": {
            "novum_description": "Las IA razonan sobre sus propios límites éticos.",
            "novum_scope": novum_scope,
            "novum_date": "2021-05-01",
            "consequences": consequences,
        },
        "characters": [{"name": "Nia", "species": "artificial"}],
        "places": [{"name": "el puerto nuevo"}],
        "facts": [],
        "chapters": [
            {
                "number": 1,
                "title": "Capítulo 1",
                "arc_function": "arranque",
                "beats": [{"number": 1, "description": "Marta despierta."}],
            }
        ],
        "style_sheet": {
            "narrator": "third",
            "tense": "past",
            "default_treatment": "tu",
        },
        "title": "El verano de Marta",
    }


def test_a_world_with_one_consequence_does_not_pass_the_schema() -> None:
    value, errors = SUBMIT_PLAN.validate(_plan(consequences=["Una consecuencia."]))

    assert value is None
    assert errors


def test_a_world_with_five_consequences_does_not_pass_the_schema() -> None:
    value, errors = SUBMIT_PLAN.validate(
        _plan(consequences=[f"Consecuencia {i}." for i in range(5)])
    )

    assert value is None
    assert errors


def test_a_novum_scope_outside_the_three_allowed_does_not_pass_the_schema() -> None:
    value, errors = SUBMIT_PLAN.validate(
        _plan(consequences=["Una.", "Dos."], novum_scope="economic")
    )

    assert value is None
    assert errors


def test_a_world_with_two_consequences_passes_the_schema() -> None:
    value, errors = SUBMIT_PLAN.validate(_plan(consequences=["Una.", "Dos."]))

    assert value is not None
    assert errors == ()
    assert value.world.novum_date == dt.date(2021, 5, 1)


def test_a_world_with_four_consequences_passes_the_schema() -> None:
    value, errors = SUBMIT_PLAN.validate(_plan(consequences=["Una.", "Dos.", "Tres.", "Cuatro."]))

    assert value is not None
    assert errors == ()


def test_the_number_of_chapters_and_beats_is_not_rejected_by_the_schema() -> None:
    """El número de capítulos y de beats no los rechaza el schema, sino `outline` (010-C11)."""
    plan = _plan(consequences=["Una.", "Dos."])
    plan["chapters"] = [
        {
            "number": n,
            "title": f"Capítulo {n}",
            "arc_function": "función",
            "beats": [{"number": 1, "description": "Beat único."}],
        }
        for n in range(1, 3)
    ]

    value, errors = SUBMIT_PLAN.validate(plan)

    assert value is not None
    assert errors == ()
    assert len(value.chapters) == 2
