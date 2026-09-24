"""`LangfuseObservability`: mismo contrato que el doble nulo, get_prompt real y exportación."""

from __future__ import annotations

from tests.conftest import FakeLangfuseClient

from story_maker.observability.langfuse_adapter import LangfuseObservability

LABEL = "produccion"


# --- C09: al arrancar, cada LlamadaDeModelo enlaza la versión leída por la etiqueta -----------


def test_get_prompt_answers_the_current_version_instead_of_none(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    fake_langfuse_client.register_prompt("writer", LABEL, version=3)
    observability = LangfuseObservability(fake_langfuse_client)

    version = observability.get_prompt("writer", LABEL)

    assert version == "3"


def test_get_prompt_of_a_role_without_a_version_under_that_label_answers_none(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)

    assert observability.get_prompt("writer", LABEL) is None
