"""El lint en vivo de la edición manual (019-C01 a 019-C09)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import seed_novel
from tests.pipeline.manual_edit.conftest import CADIZ, INSULT, N, chapter_text, headers

from story_maker.store.models import AuditLog, Base


def lint(client: TestClient, n: N, chapter: int, text: str, user: int | None = None) -> Any:
    return client.post(
        f"/api/novels/{n.novel_id}/chapters/{chapter}/lint",
        json={"text": text},
        headers=headers(n.user_a if user is None else user),
    )


def diagnostics(client: TestClient, n: N, chapter: int, text: str) -> list[dict[str, Any]]:
    response = lint(client, n, chapter, text)
    assert response.status_code == 200, response.text
    return list(response.json()["diagnostics"])


def test_a_text_with_nothing_to_warn_about_gives_an_empty_list(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    text = chapter_text(session_factory, n.v1_id, 3)

    assert diagnostics(client, n, 3, text) == []


def with_lead(session_factory: sessionmaker[Session], n: N, lead: str, chapter: int = 3) -> str:
    """El texto vigente del capítulo con `lead` delante, como un párrafo propio."""
    return f"{lead}\n\n{chapter_text(session_factory, n.v1_id, chapter)}"


def test_a_non_canonical_form_of_a_character_is_marked_as_blocking(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    lead = "Luego Tobi corrió. Ayer TOBY durmió."
    text = with_lead(session_factory, n, lead)

    found = [d for d in diagnostics(client, n, 3, text) if d["type"] == "forma_no_canonica"]

    assert [(d["position"], d["canonical"], d["blocking"]) for d in found] == [
        ({"start": 6, "end": 10}, "Toby", True),
        ({"start": 24, "end": 28}, "Toby", True),
    ]
    assert text[6:10] == "Tobi"
    assert text[24:28] == "TOBY"


def test_an_unknown_capitalized_word_is_an_unknown_character_that_does_not_block(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    lead = "Luego cuando Pepe llamó a la puerta la IA calló. Entonces Rosa sonrió."
    text = with_lead(session_factory, n, lead)

    found = [d for d in diagnostics(client, n, 3, text) if d["type"] == "personaje_desconocido"]

    assert [(d["word"], d["position"], d["blocking"]) for d in found] == [
        ("Pepe", {"start": 13, "end": 17}, False)
    ]


def of_type(found: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [d for d in found if d["type"] == kind]


def test_a_nominal_fact_the_chapter_used_and_no_longer_appears_is_warned(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    renamed = chapter_text(session_factory, n.v1_id, 3).replace("Toby", "Nala")
    kept = f"Ayer Toby volvió.\n\n{renamed}"
    without_cadiz = chapter_text(session_factory, n.v1_id, 3)
    assert CADIZ not in without_cadiz

    found = diagnostics(client, n, 3, renamed)

    (fact,) = of_type(found, "hecho")
    assert "position" not in fact
    assert fact["blocking"] is False
    assert (fact["subject"], fact["attribute"], fact["value"]) == ("Toby", "name", "Toby")
    assert "story bible" in fact["message"]
    assert [d["word"] for d in of_type(found, "personaje_desconocido")] == ["Nala"]
    assert of_type(diagnostics(client, n, 3, kept), "hecho") == []
    assert of_type(diagnostics(client, n, 3, without_cadiz), "hecho") == []


def audit_rows(session_factory: sessionmaker[Session]) -> int:
    with session_factory() as session:
        return session.query(AuditLog).count()


def test_banned_terms_of_the_three_levels_are_marked_as_blocking(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    lead = f"Luego vio Tabacos y Jórge junto al {INSULT} del mar."
    text = with_lead(session_factory, n, lead)
    before = audit_rows(session_factory)

    found = of_type(diagnostics(client, n, 3, text), "prohibida")

    assert [(d["term"], d["level"], d["variant"], d["blocking"]) for d in found] == [
        ("tabaco", "user", "Tabacos", True),
        ("Jorge", "novel", "Jórge", True),
        (INSULT, "global", INSULT, True),
    ]
    assert [text[d["position"]["start"] : d["position"]["end"]] for d in found] == [
        "Tabacos",
        "Jórge",
        INSULT,
    ]
    assert audit_rows(session_factory) == before


def test_prose_linter_warnings_come_with_their_linter_metric_and_threshold(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    lead = "Luego la ventana crujió. La ventana cayó. La ventana calló. Sin lugar a dudas llovía."
    text = with_lead(session_factory, n, lead)

    found = of_type(diagnostics(client, n, 3, text), "linter")

    assert [(d["linter"], d["blocking"]) for d in found] == [
        ("linter-repeticion", False),
        ("linter-estilo-ia", False),
    ]
    repetition, cliche = found
    assert repetition["message"] == '"ventana" 3 veces en el párrafo 1'
    assert repetition["metric"] == 1
    assert "3 veces" in repetition["threshold"]
    assert "sin lugar a dudas" in cliche["message"]
    assert cliche["threshold"].startswith("umbral 6 por 1.000")


def test_a_character_reappearing_after_an_exclusion_event_is_warned(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    lead = "Luego Rosa vio a Luis con Ana y Pablo. Ayer Rosa volvió."
    third = with_lead(session_factory, n, lead)
    flashback = with_lead(session_factory, n, "Luego Rosa volvió a casa.", chapter=8)

    found = of_type(diagnostics(client, n, 3, third), "cronologia")

    assert [(d["character"], d["position"], d["blocking"]) for d in found] == [
        ("Rosa", {"start": 6, "end": 10}, False),
        ("Luis", {"start": 17, "end": 21}, False),
    ]
    assert (found[0]["event"]["origin"], found[0]["event"]["chapter"]) == ("brief", None)
    assert (found[1]["event"]["origin"], found[1]["event"]["chapter"]) == ("recorded", 2)
    assert of_type(diagnostics(client, n, 8, flashback), "cronologia") == []


AGES = (
    "Luego Marta tenía 35 años. Ayer Marta, de treinta y cinco años, cenó. "
    "Pronto Marta tenía 36 años. Allí Marta cumplió cuarenta años. "
    "Después Marta recordó lo que pasó hace 40 años. Luego Toby tenía 3 años."
)


def test_a_written_age_that_does_not_fit_the_birth_date_is_warned(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    third = with_lead(session_factory, n, AGES)
    ninth = with_lead(session_factory, n, "Luego Marta tenía 36 años.", chapter=9)

    found = of_type(diagnostics(client, n, 3, third), "cronologia")

    assert [
        (third[d["position"]["start"] : d["position"]["end"]], d["written_age"], d["expected"])
        for d in found
    ] == [("36", 36, [35]), ("cuarenta", 40, [35])]
    assert all(d["blocking"] is False for d in found)
    assert of_type(diagnostics(client, n, 9, ninth), "cronologia") == []


def table_counts(session_factory: sessionmaker[Session]) -> dict[str, int]:
    with session_factory() as session:
        return {
            table.name: session.execute(select(func.count()).select_from(table)).scalar_one()
            for table in Base.metadata.sorted_tables
        }


def test_lint_rejections_change_nothing(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    with session_factory() as session:
        unpublished = seed_novel(session, n.user_a).id
        session.commit()
    before = table_counts(session_factory)
    url = f"/api/novels/{n.novel_id}/chapters/3/lint"

    assert client.post(url, json={"text": "hola"}).status_code == 401
    foreign = lint(client, n, 3, "hola", user=n.user_b)
    missing = client.post(
        "/api/novels/9999/chapters/3/lint", json={"text": "hola"}, headers=headers(n.user_b)
    )
    assert (foreign.status_code, missing.status_code) == (404, 404)
    assert foreign.json() == missing.json()
    no_version = client.post(
        f"/api/novels/{unpublished}/chapters/3/lint",
        json={"text": "hola"},
        headers=headers(n.user_a),
    )
    assert no_version.status_code == 409
    assert lint(client, n, 0, "hola").status_code == 422
    assert lint(client, n, 11, "hola").status_code == 422
    assert client.post(url, json={}, headers=headers(n.user_a)).status_code == 422
    assert table_counts(session_factory) == before
