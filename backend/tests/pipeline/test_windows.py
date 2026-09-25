"""Ventanas del writer y del editor ensambladas desde la candidata (011-C07, C08)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed

from story_maker.pipeline.windows import CandidateWindows
from story_maker.store.models import Brief, Chapter, Fact, OutlineChapter

TOP_K = {"writer": 8, "editor": 8}
ORIGIN = {"theme": "el origen del faro", "content": "lo levantó un contrabandista arrepentido"}
CHAPTER4_SECRET = {"theme": "la carta", "content": "la carta era de su abuela"}
ELEMENT = 7


@dataclass
class FixedRetriever:
    """«El recuerdo devuelve»: la respuesta del recuperador (016) es entrada del caso."""

    cards: tuple[str, ...]
    calls: list[tuple[int, int, tuple[str, ...], int]] = field(default_factory=list)

    def __call__(
        self, session: Session, version_id: int, chapter: int, fragments: Sequence[str], top_k: int
    ) -> list[str]:
        self.calls.append((version_id, chapter, tuple(fragments), top_k))
        return list(self.cards)


def chapter_text(number: int, words: int) -> str:
    """Cada palabra lleva su capítulo y su posición: «c3p0701»."""
    tokens = [f"c{number}p{k:04d}" for k in range(1, words + 1)]
    paragraphs = [" ".join(tokens[i : i + 100]) + "." for i in range(0, words, 100)]
    return "\n\n".join(paragraphs)


def beats(chapter: int, revelation: dict[str, str] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "number": b,
            "description": f"beat {b} del capítulo {chapter}",
            "characters": ["Marta"] if chapter == 4 else ["Toby"],
            "facts_used": [],
            "revelation": revelation if b == 2 else None,
            "events": [],
        }
        for b in (1, 2, 3)
    ]


@pytest.fixture
def candidate(session_factory: sessionmaker[Session], seed: Seed) -> Seed:
    """Capítulos 1 a 3 aceptados; revelación en el 4 y en el 6; un elemento obligatorio en el 4."""
    with session_factory() as session:
        brief = session.query(Brief).filter_by(novel_id=seed.novel_id).one()
        brief.content = {"length": "medium"}
        for outline in session.query(OutlineChapter).filter_by(version_id=seed.version_id):
            revelation = {4: CHAPTER4_SECRET, 6: ORIGIN}.get(outline.number)
            outline.beats = beats(outline.number, revelation)
            outline.assigned_elements = [str(ELEMENT)] if outline.number == 4 else []
        session.get_one(Fact, seed.facts["rasgo"]).personal_element_id = ELEMENT
        for number in (1, 2, 3):
            session.add(
                Chapter(
                    version_id=seed.version_id,
                    number=number,
                    title=f"Título {number}",
                    text=chapter_text(number, 1000),
                    summary=f"resumen del capítulo {number}",
                    word_count=1000,
                    content_hash=f"h{number}",
                )
            )
        session.commit()
    return seed


def writer_window(
    session_factory: sessionmaker[Session], version_id: int, chapter: int, retriever: Any
) -> Any:
    windows = CandidateWindows(retriever=retriever, top_k=TOP_K)
    with session_factory() as session:
        return windows.writer(session, version_id, chapter)


def test_the_writer_window_of_chapter_4_has_its_parts_and_nothing_else(
    session_factory: sessionmaker[Session], candidate: Seed
) -> None:
    retriever = FixedRetriever(tuple(f"K{k}" for k in range(1, 9)))

    window = writer_window(session_factory, candidate.version_id, 4, retriever)

    residents = window.residents
    assert set(residents) == {
        "style_sheet",
        "outline",
        "summaries",
        "literal_ending",
        "mandatory_elements",
        "facts",
        "characters",
    }
    assert residents["style_sheet"] == {"narrator": "third"}
    outline = residents["outline"]
    assert outline["titles"] == [f"Capítulo {n}" for n in range(1, 11)]
    assert outline["chapter"]["number"] == 4
    assert outline["chapter"]["beats"] == beats(4, CHAPTER4_SECRET)
    assert outline["future_revelations"] == [{"chapter": 6, "theme": "el origen del faro"}]
    assert residents["summaries"] == [
        {"chapter": n, "summary": f"resumen del capítulo {n}"} for n in (1, 2, 3)
    ]
    ending = residents["literal_ending"]
    assert ending.startswith("c3p0701 ")
    assert ending.endswith("c3p1000.")
    assert "c3p0700" not in ending
    assert ending.count("\n\n") == 2
    assert [f["id"] for f in residents["mandatory_elements"]] == [candidate.facts["rasgo"]]
    assert [c["name"] for c in residents["characters"]] == ["Marta"]
    assert {(f["id"], f["value"]) for f in residents["facts"]} == {
        (candidate.facts["marta"], "Marta"),
        (candidate.facts["rasgo"], "le da miedo el agua fría"),
    }
    assert window.target_words == 1250
    assert window.retrieved == tuple(f"K{k}" for k in range(1, 9))
    assert retriever.calls == [
        (candidate.version_id, 4, tuple(f"beat {b} del capítulo 4" for b in (1, 2, 3)), 8)
    ]
    dumped = json.dumps(residents, ensure_ascii=False)
    assert ORIGIN["content"] not in dumped
    assert "c1p" not in dumped
    assert "c2p" not in dumped


def test_the_writer_window_of_chapter_1_has_no_summaries_nor_literal_ending(
    session_factory: sessionmaker[Session], candidate: Seed
) -> None:
    window = writer_window(session_factory, candidate.version_id, 1, FixedRetriever(()))

    assert window.residents["summaries"] == []
    assert window.residents["literal_ending"] is None


@pytest.mark.parametrize("chapter", [2, 3, 4])
def test_no_writer_window_ever_carries_recovered_prose_older_than_the_immediate_previous_chapter(
    session_factory: sessionmaker[Session], candidate: Seed, chapter: int
) -> None:
    """011-I7: del texto de los capítulos anteriores, la ventana solo lleva el final literal del
    capítulo n-1 (sus últimas 300 palabras); ni una frase de un capítulo más antiguo, ni el resto
    del propio n-1, llegan por ningún otro camino de la ventana (`summaries`, `outline`...)."""
    window = writer_window(session_factory, candidate.version_id, chapter, FixedRetriever(()))
    dumped = json.dumps(window.residents, ensure_ascii=False)

    for earlier in range(1, chapter - 1):  # cualquier capítulo anterior al inmediato precedente
        assert f"c{earlier}p" not in dumped

    previous = chapter - 1
    assert f"c{previous}p0700" not in dumped  # nada del capítulo n-1 antes de sus últimas 300
    assert f"c{previous}p0701" in dumped  # el final literal sí llega
    assert f"c{previous}p1000" in dumped


DELIVERED = "Marta subió al Faro de Cabo Mayor.\n\nToby ladró dos veces."


def test_the_editor_window_has_the_chapter_4_outline_entities_rubric_and_the_delivery(
    session_factory: sessionmaker[Session], candidate: Seed
) -> None:
    retriever = FixedRetriever(tuple(f"R{k}" for k in range(1, 9)))
    windows = CandidateWindows(retriever=retriever, top_k={"writer": 8, "editor": 6})
    with session_factory() as session:
        window = windows.editor(session, candidate.version_id, 4, "La carta", DELIVERED)

    residents = window.residents
    assert set(residents) == {
        "style_sheet",
        "summaries",
        "chapter",
        "mandatory_elements",
        "facts",
        "characters",
        "places",
        "entities",
        "rubric",
    }
    assert residents["style_sheet"] == {"narrator": "third"}
    assert [s["chapter"] for s in residents["summaries"]] == [1, 2, 3]
    assert residents["chapter"]["number"] == 4
    assert residents["chapter"]["beats"] == beats(4, CHAPTER4_SECRET)
    assert [f["id"] for f in residents["mandatory_elements"]] == [candidate.facts["rasgo"]]
    assert residents["characters"] == [{"id": candidate.characters["Marta"], "name": "Marta"}]
    assert {f["id"] for f in residents["facts"]} == {
        candidate.facts["marta"],
        candidate.facts["rasgo"],
    }
    assert residents["entities"] == {
        "characters": [
            {"id": candidate.characters["Marta"], "name": "Marta"},
            {"id": candidate.characters["Toby"], "name": "Toby"},
        ],
        "places": [{"id": candidate.places["Faro de Cabo Mayor"], "name": "Faro de Cabo Mayor"}],
    }
    rubric = {c["criterion"]: c for c in residents["rubric"]}
    assert list(rubric) == [
        "fidelidad-canon",
        "cumple-beats",
        "personalizacion-natural",
        "prosa",
        "tono",
    ]
    assert {c for c, r in rubric.items() if r["blocking"]} == {"fidelidad-canon", "cumple-beats"}
    assert all(r["judges"] for r in rubric.values())
    assert window.retrieved == tuple(f"R{k}" for k in range(1, 9))
    assert retriever.calls == [
        (
            candidate.version_id,
            4,
            ("Marta subió al Faro de Cabo Mayor.", "Toby ladró dos veces."),
            6,
        )
    ]
    dumped = json.dumps(residents, ensure_ascii=False)
    assert "future_revelations" not in dumped
    assert "beat 1 del capítulo 5" not in dumped
    assert "c3p" not in dumped
