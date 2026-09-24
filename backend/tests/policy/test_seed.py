"""005-C18 · Sembrar la lista global no duplica entradas."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from story_maker.domain.banned_terms import normalize_token
from story_maker.domain.global_banned_terms import GLOBAL_BANNED_TERMS
from story_maker.policy.seed import seed_global_banned_terms
from story_maker.store.models import BannedTerm
from story_maker.store.session import unit_of_work


def _global_rows(session_factory: sessionmaker[Session]) -> list[BannedTerm]:
    session = session_factory()
    rows = list(session.execute(select(BannedTerm).where(BannedTerm.level == "global")).scalars())
    session.close()
    return rows


def test_sembrar_la_lista_global_no_duplica_entradas(
    session_factory: sessionmaker[Session],
) -> None:
    with unit_of_work(session_factory) as uow:
        seed_global_banned_terms(uow)

    first_pass = _global_rows(session_factory)
    assert len(first_pass) == len(GLOBAL_BANNED_TERMS)
    assert {row.normalized for row in first_pass} == {
        normalize_token(term) for term in GLOBAL_BANNED_TERMS
    }
    assert all(
        row.type == "word" and row.user_id is None and row.novel_id is None for row in first_pass
    )

    with unit_of_work(session_factory) as uow:
        seed_global_banned_terms(uow)

    second_pass = _global_rows(session_factory)
    assert len(second_pass) == len(first_pass)
    assert {row.id for row in second_pass} == {row.id for row in first_pass}
