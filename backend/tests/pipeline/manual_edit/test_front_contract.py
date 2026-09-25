"""El contrato que consume la pantalla de edición (028, congelada): `Diagnostic` en
`frontend/src/shared/api/manualEdit.ts` y los estados de `ChapterEditorPage.tsx`. Cada
diagnóstico del lint y del 422 del guardado trae un `type` que el front conoce, `message`,
`blocking` y, si la trae, una `position` que recorta el texto enviado; el 202 trae `run_id` y el
409 basta con su estado."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.manual_edit.conftest import N, chapter_text
from tests.pipeline.manual_edit.test_live_lint import lint, with_lead
from tests.pipeline.manual_edit.test_save import renamed_text, save, sized_text

FRONT_TYPES = {
    "forma_no_canonica",
    "personaje_desconocido",
    "hecho",
    "prohibida",
    "linter",
    "cronologia",
}


def assert_front_diagnostic(diagnostic: dict[str, Any], text: str) -> None:
    assert diagnostic["type"] in FRONT_TYPES, diagnostic
    assert isinstance(diagnostic["message"], str)
    assert diagnostic["message"]
    assert isinstance(diagnostic["blocking"], bool)
    if "position" in diagnostic:
        start, end = diagnostic["position"]["start"], diagnostic["position"]["end"]
        assert isinstance(start, int)
        assert isinstance(end, int)
        assert 0 <= start < end <= len(text)


def test_every_lint_diagnostic_has_a_type_and_fields_the_editor_page_knows(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    texts = [
        with_lead(session_factory, n, "Luego Tobi y Pepe compraron tabaco. Rosa volvió allí."),
        renamed_text(session_factory, n),
        chapter_text(session_factory, n.v1_id, 3).replace("Luego", "Dijo: «Luego»"),
    ]
    seen: set[str] = set()
    for text in texts:
        response = lint(client, n, 3, text)
        assert response.status_code == 200, response.text
        for diagnostic in response.json()["diagnostics"]:
            assert_front_diagnostic(diagnostic, text)
            seen.add(diagnostic["type"])
    assert {"forma_no_canonica", "personaje_desconocido", "prohibida", "hecho"} <= seen


def test_the_save_answers_have_the_shapes_the_editor_page_reads(
    client: TestClient, n: N, session_factory: sessionmaker[Session]
) -> None:
    rejected_text = "Luego Tobi vio Tabacos.\n\n" + sized_text(995)
    rejected = save(client, n, 3, rejected_text)
    assert rejected.status_code == 422, rejected.text
    found = rejected.json()["detail"]["diagnostics"]
    assert len(found) == 3
    for diagnostic in found:
        assert_front_diagnostic(diagnostic, rejected_text)
        assert diagnostic["blocking"] is True

    accepted = save(client, n, 3, renamed_text(session_factory, n))
    assert accepted.status_code == 202, accepted.text
    assert isinstance(accepted.json()["run_id"], int)

    stale = save(client, n, 3, renamed_text(session_factory, n), base=2)
    assert stale.status_code == 409
    assert isinstance(stale.json()["detail"], str)
