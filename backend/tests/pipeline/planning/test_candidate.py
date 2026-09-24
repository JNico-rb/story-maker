"""Arranca la fase `planning`: la candidata nace con el canon del brief (010-C01..C05).

Llama al repositorio real de 009 (`store.brief_canon.create_generation_candidate`, ya en V2):
esto ya no espera a la 009. El brief de referencia es el de
`specs/backend/010-planificacion.md`: Marta (40, sin fecha declarada), Toby (allegado, animal,
5 años) y Rosa (allegada, persona, sin edad); R1 (a los 8, obligatorio), R2 (2010, excluyente
por la partida de Rosa) y R3 (2024); H1 (aceptado, obligatorio) y H2 (aceptado); H3 (aceptado
por el extractor pero rechazado por el cliente) — H4 nunca llega al brief, lo descarta
`citas-verificadas` antes (`definitions.md` HechoExtraido)."""

from __future__ import annotations

import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.pipeline.planning import candidate as candidate_module
from story_maker.pipeline.planning.candidate import start_generation_phase
from story_maker.store.brief_canon import (
    NAME,
    BriefCloseOne,
    BriefExtractedFact,
    BriefRecipient,
    BriefRecollection,
    BriefTrait,
    ConfirmedBrief,
    birth_date,
    recollection_moment,
)
from story_maker.store.models import (
    CanonCard,
    Character,
    Event,
    EventCharacter,
    Fact,
    OutlineChapter,
    Place,
    Run,
    StyleSheet,
    Version,
)

NOW = dt.datetime(2026, 9, 24, 12, 0)


def reference_brief(*, recipient_birth_date: dt.date | None = None) -> ConfirmedBrief:
    return ConfirmedBrief(
        recipient=BriefRecipient(
            name="Marta",
            age=40,
            name_element_id=1,
            traits=(
                BriefTrait("curiosa", element_id=2, mandatory=False),
                BriefTrait("le encanta el mar", element_id=3, mandatory=True),
            ),
            birth_date=recipient_birth_date,
        ),
        close_ones=(
            BriefCloseOne("Toby", "su perro", "animal", element_id=4, mandatory=True, age=5),
            BriefCloseOne("Rosa", "su abuela", "person", element_id=5, mandatory=False),
        ),
        recollections=(
            BriefRecollection(
                "se perdió en la feria de su pueblo",
                "la feria del pueblo",
                element_id=6,
                mandatory=True,
                age=8,
                present=("Rosa",),
            ),
            BriefRecollection(
                "Rosa se fue a vivir para siempre a otro país",
                "el aeropuerto",
                element_id=7,
                mandatory=False,
                year=2010,
                present=("Rosa",),
                excluded="Rosa",
            ),
            BriefRecollection(
                "llevó a Toby a la feria del pueblo",
                "la feria del pueblo",
                element_id=8,
                mandatory=False,
                year=2024,
                present=("Toby",),
            ),
        ),
        extracted_facts=(
            BriefExtractedFact(
                "Marta",
                "hobby",
                "Marta colecciona conchas",
                accepted=True,
                mandatory=True,
                element_id=9,
            ),
            BriefExtractedFact(
                "Rosa",
                "hobby",
                "Rosa cocinaba arroz con leche",
                accepted=True,
                mandatory=False,
                element_id=10,
            ),
            BriefExtractedFact("Marta", "hobby", "H3 rechazado", accepted=False, mandatory=False),
        ),
    )


def _rows(session_factory: sessionmaker[Session], model: type, version_id: int) -> list[object]:
    with session_factory() as session:
        return list(session.scalars(select(model).filter_by(version_id=version_id)).all())


async def test_the_candidate_is_born_with_the_brief_canon(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)

    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.phase, run.candidate_version_id) == (
            "running",
            "planning",
            version.id,
        )
        stored = session.get(Version, version.id)
        assert stored is not None
        assert (stored.status, stored.number, stored.base_version_id) == ("candidate", None, None)

    characters = {c.canonical_name: c for c in _rows(session_factory, Character, version.id)}
    assert {"Marta", "Toby", "Rosa"} == set(characters)
    assert (characters["Marta"].type, characters["Toby"].type, characters["Rosa"].type) == (
        "recipient",
        "close_one",
        "close_one",
    )
    assert characters["Toby"].species == "animal"

    facts = _rows(session_factory, Fact, version.id)
    facts_by_value = {f.value: f for f in facts}
    # Un hecho por rasgo de Marta, uno por recuerdo, la relación de cada allegado, el nombre de
    # cada personaje y los hechos extraídos aceptados (H1, H2); H3 no aceptado no entra.
    assert len(facts) == 12
    assert {"Marta colecciona conchas", "Rosa cocinaba arroz con leche"} <= set(facts_by_value)
    assert "H3 rechazado" not in facts_by_value

    marta_name = next(
        f for f in facts if f.character_id == characters["Marta"].id and f.attribute == NAME
    )
    mar_trait = facts_by_value["le encanta el mar"]
    toby_name = next(
        f for f in facts if f.character_id == characters["Toby"].id and f.attribute == NAME
    )
    h1 = facts_by_value["Marta colecciona conchas"]
    curiosa = facts_by_value["curiosa"]
    rosa_name = next(
        f for f in facts if f.character_id == characters["Rosa"].id and f.attribute == NAME
    )
    h2 = facts_by_value["Rosa cocinaba arroz con leche"]
    assert (marta_name.mandatory, marta_name.personal_element_id) == (True, 1)
    assert (mar_trait.mandatory, mar_trait.personal_element_id) == (True, 3)
    assert (toby_name.mandatory, toby_name.personal_element_id) == (True, 4)
    assert (h1.mandatory, h1.personal_element_id) == (True, 9)
    assert (curiosa.mandatory, curiosa.personal_element_id) == (False, 2)
    assert (rosa_name.mandatory, rosa_name.personal_element_id) == (False, 5)
    assert (h2.mandatory, h2.personal_element_id) == (False, 10)

    events = _rows(session_factory, Event, version.id)
    assert len(events) == 3
    for empty_model in (StyleSheet, OutlineChapter, CanonCard):
        assert _rows(session_factory, empty_model, version.id) == []
    with session_factory() as session:
        from story_maker.store.models import World

        assert session.query(World).filter_by(version_id=version.id).count() == 0


@pytest.mark.parametrize(
    ("age", "declared", "expected"),
    [
        (40, None, dt.date(1986, 1, 1)),  # Marta: sin fecha, 1 de enero de (2026 - 40)
        (5, None, dt.date(2021, 1, 1)),  # Toby: solo tiene edad
        (None, None, None),  # Rosa: sin edad ni fecha
        (None, dt.date(2000, 2, 29), dt.date(2000, 2, 29)),  # declarada
    ],
)
def test_birth_dates_of_the_canon(
    age: int | None, declared: dt.date | None, expected: dt.date | None
) -> None:
    assert birth_date(2026, age, declared) == expected


@pytest.mark.parametrize(
    ("birth", "age", "year", "expected"),
    [
        (dt.date(1986, 1, 1), 8, None, dt.datetime(1994, 1, 1, 12, 0)),  # R1
        (dt.date(1986, 1, 1), None, 2010, dt.datetime(2010, 1, 1, 12, 0)),  # R2
        (dt.date(1986, 1, 1), None, 1986, dt.datetime(1986, 1, 2, 12, 0)),  # año de nacimiento
        (dt.date(2000, 2, 29), 9, None, dt.datetime(2009, 3, 1, 12, 0)),  # 2009 no es bisiesto
        (dt.date(2000, 2, 29), 8, None, dt.datetime(2008, 2, 29, 12, 0)),  # 2008 sí lo es
    ],
)
def test_recollection_moments_of_the_canon(
    birth: dt.date, age: int | None, year: int | None, expected: dt.datetime
) -> None:
    assert recollection_moment(birth, age, year) == expected


async def test_recollections_become_events_and_places(
    session_factory: sessionmaker[Session], run_id: int, novel_id: int
) -> None:
    version = start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)

    events = {e.statement: e for e in _rows(session_factory, Event, version.id)}
    places = {p.canonical_name: p for p in _rows(session_factory, Place, version.id)}
    assert {"la feria del pueblo", "el aeropuerto"} == set(places)

    r1 = events["se perdió en la feria de su pueblo"]
    r2 = events["Rosa se fue a vivir para siempre a otro país"]
    r3 = events["llevó a Toby a la feria del pueblo"]
    assert (r1.chapter, r1.beat, r1.analepsis) == (None, None, True)
    assert (r1.type, r1.excluded_character_id) == ("ordinary", None)
    assert (r2.type, r2.place_id) == ("exclusion", places["el aeropuerto"].id)
    assert (r3.type, r3.place_id) == ("ordinary", places["la feria del pueblo"].id)
    assert r1.place_id == r3.place_id  # mismo nombre de lugar, mismo Lugar

    with session_factory() as session:
        characters = {
            c.canonical_name: c.id
            for c in session.scalars(select(Character).filter_by(version_id=version.id))
        }
        presences = {
            (ec.event_id): ec.character_id
            for ec in session.scalars(select(EventCharacter))
            if ec.event_id in {r1.id, r2.id}
        }
    assert characters["Rosa"] in presences.values()


async def test_creating_the_candidate_is_all_or_nothing_and_the_run_fails_on_a_mid_write_fault(
    session_factory: sessionmaker[Session],
    run_id: int,
    novel_id: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing(uow: object, novel_id_: int, brief: ConfirmedBrief, *, now: dt.datetime) -> Version:
        version = Version(
            novel_id=novel_id_, status="candidate", changed_chapters=[], created_at=now
        )
        uow.add(version)  # type: ignore[attr-defined]
        uow.session.flush()  # type: ignore[attr-defined]
        raise RuntimeError("fallo inyectado a mitad de la escritura")

    monkeypatch.setattr(candidate_module, "create_generation_candidate", failing)

    with pytest.raises(RuntimeError):
        start_generation_phase(session_factory, run_id, novel_id, reference_brief(), now=NOW)

    with session_factory() as session:
        assert session.query(Version).filter_by(novel_id=novel_id).count() == 0
        run = session.get(Run, run_id)
        assert run is not None
        assert (run.status, run.reason) == ("failed", "internal_error")
