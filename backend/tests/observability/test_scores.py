"""Scores exportados con su nombre canónico; TLC nunca envía score (004-C12, C13)."""

from __future__ import annotations

from tests.conftest import FakeLangfuseClient

from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.scores import export_validator_score, is_scoreable

# --- C12: cada resultado de validador se exporta como Score con su nombre canónico ------------


def test_a_programmatic_validator_result_is_exported_with_its_canonical_name_at_trace_level(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)
    with observability.trace("run:1") as trace:
        export_validator_score(observability, trace, "palabras-prohibidas", 1, "sin coincidencias")
    observability.flush()

    (score,) = fake_langfuse_client.scores
    assert score["name"] == "palabras-prohibidas"
    assert score["value"] == 1
    assert score["comment"] == "sin coincidencias"
    assert score["trace_id"] == "trace-run:1"
    assert score["observation_id"] is None


def test_a_semantic_chapter_validator_result_is_linked_to_its_chapter_span(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)
    with (
        observability.trace("run:1") as trace,
        observability.span(trace, "capitulo-3") as span,
    ):
        export_validator_score(
            observability, trace, "rubrica-capitulo", 4, "cumple ritmo y tono", span=span
        )
    observability.flush()

    (score,) = fake_langfuse_client.scores
    assert score["name"] == "rubrica-capitulo"
    exported_span = fake_langfuse_client.roots["trace-run:1"].children[0]
    assert exported_span.name == "capitulo-3"
    assert score["observation_id"] == exported_span.id


# --- C13: TLC no envía score --------------------------------------------------------------------


def test_harness_tla_is_not_scoreable() -> None:
    assert is_scoreable("harness-tla") is False


def test_a_regular_validator_is_scoreable() -> None:
    assert is_scoreable("cronologia-lean") is True
    assert is_scoreable("rubrica-capitulo") is True
