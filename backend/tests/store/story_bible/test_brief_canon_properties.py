"""009-I7: todo `ElementoPersonal` del brief tiene al menos un hecho que lo representa, y el de uno
obligatorio es obligatorio (prueba basada en propiedades, `verification.md` §3.4)."""

from __future__ import annotations

from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from story_maker.store import models
from story_maker.store.brief_canon import (
    BriefCloseOne,
    BriefExtractedFact,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
)


@st.composite
def confirmed_briefs(draw: st.DrawFn) -> tuple[ConfirmedBrief, dict[int, bool]]:
    """Un brief confirmado al azar y sus elementos personales (id → obligatorio)."""
    ids = iter(range(1, 1000))
    elements: dict[int, bool] = {}

    def element(mandatory: bool) -> int:
        element_id = next(ids)
        elements[element_id] = mandatory
        return element_id

    age = draw(st.integers(min_value=1, max_value=90))
    traits = tuple(
        BriefTrait(f"rasgo {i}", element_id=element(m), mandatory=m)
        for i, m in enumerate(draw(st.lists(st.booleans(), min_size=1, max_size=3)))
    )
    recipient = BriefRecipient("Marta", age, name_element_id=element(True), traits=traits)
    close_ones = tuple(
        BriefCloseOne(f"Allegado{i}", "amigo", "person", element_id=element(m), mandatory=m)
        for i, m in enumerate(draw(st.lists(st.booleans(), max_size=4)))
    )
    names = [c.name for c in close_ones]
    recollections = []
    for i in range(draw(st.integers(min_value=1, max_value=4))):
        mandatory = draw(st.booleans())
        present = tuple(draw(st.lists(st.sampled_from(names), unique=True))) if names else ()
        excluded = draw(st.sampled_from([None, *present]))
        by_age = draw(st.booleans())
        recollections.append(
            BriefRecollection(
                f"recuerdo {i}",
                draw(st.sampled_from(["la feria", "la playa", "la estación"])),
                element_id=element(mandatory),
                mandatory=mandatory,
                age=draw(st.integers(0, age)) if by_age else None,
                year=None if by_age else draw(st.integers(2026 - age, 2026)),
                present=present,
                excluded=excluded,
            )
        )
    extracted = []
    for i in range(draw(st.integers(min_value=0, max_value=3))):
        accepted = draw(st.booleans())
        mandatory = accepted and draw(st.booleans())
        extracted.append(
            BriefExtractedFact(
                draw(st.sampled_from(["Marta", *names])),
                f"atributo {i}",
                f"valor {i}",
                accepted=accepted,
                mandatory=mandatory,
                element_id=element(mandatory) if accepted else None,
            )
        )
    brief = ConfirmedBrief(recipient, close_ones, tuple(recollections), tuple(extracted))
    return brief, elements


@settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(case=confirmed_briefs())
def test_every_personal_element_has_a_fact_and_a_mandatory_one_a_mandatory_fact(
    store: Any, case: tuple[ConfirmedBrief, dict[int, bool]]
) -> None:
    brief, elements = case

    version_id = store.generation(store.new_novel(), brief)

    with store.session() as session:
        facts = session.query(models.Fact).filter_by(version_id=version_id).all()
    for element_id, mandatory in elements.items():
        representing = [f for f in facts if f.personal_element_id == element_id]
        assert representing, element_id
        assert all(f.mandatory == mandatory for f in representing), element_id
    assert {f.personal_element_id for f in facts} - {None} == set(elements)
    assert all(f.personal_element_id is not None for f in facts if f.mandatory)
