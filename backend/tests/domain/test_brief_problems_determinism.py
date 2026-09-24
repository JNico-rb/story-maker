"""Las comprobaciones son deterministas y solo dependen del brief, de las tres listas, de la
fecha de creación de la novela y de `max_mandatory_elements` (008-I2)."""

from __future__ import annotations

import datetime as dt
import inspect

from hypothesis import given, settings
from hypothesis import strategies as st

from story_maker.domain import brief as brief_module
from story_maker.domain.brief import (
    AcceptedFact,
    BannedEntry,
    BriefContent,
    CloseOne,
    PlotWish,
    Recipient,
    Recollection,
    Trait,
    brief_problems,
)

_WORDS = st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=15)
_NAMES = st.sampled_from(["Marta", "Toby", "Luis", "Pedro", "Ana", ""])

_traits = st.lists(st.builds(Trait, statement=_WORDS, mandatory=st.booleans()), max_size=3)
_close_ones = st.lists(
    st.builds(
        CloseOne,
        name=_NAMES,
        relation=_WORDS,
        species=st.one_of(st.none(), st.sampled_from(["person", "animal"])),
        age=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
        birth_date=st.none(),
        mandatory=st.booleans(),
    ),
    max_size=3,
)
_recollections = st.lists(
    st.builds(
        Recollection,
        statement=_WORDS,
        age=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
        year=st.one_of(st.none(), st.integers(min_value=1900, max_value=2100)),
        place=_WORDS,
        present=st.just(()),
        excluded=st.none(),
        mandatory=st.booleans(),
    ),
    max_size=3,
)
_plot_wishes = st.lists(st.builds(PlotWish, statement=_WORDS), max_size=2)

_content = st.builds(
    BriefContent,
    recipient=st.builds(
        Recipient,
        name=_NAMES,
        age=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
        birth_date=st.none(),
        traits=_traits,
        relation=st.none(),
    ),
    close_ones=_close_ones,
    recollections=_recollections,
    occasion=st.one_of(
        st.none(), st.sampled_from(["birthday", "wedding", "anniversary", "retirement", "other"])
    ),
    genre=st.one_of(
        st.none(),
        st.sampled_from(["adventure", "humor", "romance", "mystery", "drama", "fable"]),
    ),
    tone=st.one_of(
        st.none(),
        st.sampled_from(["tender", "funny", "exciting", "nostalgic", "epic", "unsettling"]),
    ),
    length=st.one_of(st.none(), st.sampled_from(["short", "medium", "long"])),
    dedication=_WORDS,
    banned_asked=st.booleans(),
    plot_wishes=_plot_wishes,
)

_banned_entries = st.lists(
    st.builds(
        BannedEntry,
        term=_NAMES.filter(lambda w: w != ""),
        type=st.sampled_from(["word", "topic"]),
        level=st.sampled_from(["global", "user", "novel"]),
        keywords=st.just(()),
    ),
    max_size=4,
)

_accepted_facts = st.lists(
    st.builds(
        AcceptedFact,
        id=st.integers(min_value=1, max_value=1000),
        subject=_NAMES,
        value=_WORDS,
        mandatory=st.booleans(),
    ),
    max_size=3,
)

_dates = st.dates(min_value=dt.date(2000, 1, 1), max_value=dt.date(2100, 1, 1))


@settings(max_examples=60, deadline=None)
@given(
    content=_content,
    created_at=_dates,
    banned_entries=_banned_entries,
    accepted_facts=_accepted_facts,
    max_mandatory=st.integers(min_value=0, max_value=20),
)
def test_brief_problems_is_deterministic_and_ignores_banned_entries_order(
    content: BriefContent,
    created_at: dt.date,
    banned_entries: list[BannedEntry],
    accepted_facts: list[AcceptedFact],
    max_mandatory: int,
) -> None:
    first = brief_problems(content, created_at, banned_entries, accepted_facts, max_mandatory)
    second = brief_problems(content, created_at, banned_entries, accepted_facts, max_mandatory)
    assert first == second  # deterministas: misma entrada, misma salida

    reordered = brief_problems(
        content, created_at, list(reversed(banned_entries)), accepted_facts, max_mandatory
    )
    assert reordered == first  # no dependen del orden de la lista de prohibidas


def test_no_domain_check_reads_the_wall_clock() -> None:
    """La única fecha que entra es `created_at`, explícita en cada llamada: ninguna función de
    `domain.brief` lee el reloj del sistema (`dt.date.today` / `dt.datetime.now`), así que la
    misma novela evaluada en días distintos da el mismo resultado (008-I2)."""
    source = inspect.getsource(brief_module)
    assert "date.today(" not in source
    assert "datetime.now(" not in source
    assert ".utcnow(" not in source
