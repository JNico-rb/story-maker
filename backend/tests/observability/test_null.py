"""Doble nulo del puerto de observabilidad: trazas, spans, niveles y prompts (001-C19..C21)."""

from __future__ import annotations

import pytest

from story_maker.observability.null import NullObservability


@pytest.fixture
def obs() -> NullObservability:
    return NullObservability()


def test_a_trace_with_name_and_session_is_captured(obs: NullObservability) -> None:
    with obs.trace("run:1", name="generacion", session="novel:7"):
        pass

    assert obs.traces["run:1"].name == "generacion"
    assert obs.traces["run:1"].session == "novel:7"


def test_a_trace_without_session_is_captured_without_one(obs: NullObservability) -> None:
    with obs.trace("mcp:list_novels", name="mcp:list_novels"):
        pass

    assert obs.traces["mcp:list_novels"].session is None


def test_nested_spans_capture_name_parent_and_metadata(obs: NullObservability) -> None:
    with (
        obs.trace("run:1") as trace,
        obs.span(trace, "capitulo-1", metadata={"chapter": 1}) as outer,
        obs.span(trace, "rol:writer", parent=outer),
    ):
        pass

    assert trace.spans[0].name == "capitulo-1"
    assert trace.spans[0].metadata == {"chapter": 1}
    assert trace.spans[0].children[0].name == "rol:writer"
    assert trace.spans[0].children[0].parent is trace.spans[0]


def test_a_model_call_inside_a_span_keeps_every_field(obs: NullObservability) -> None:
    with obs.trace("run:1") as trace, obs.span(trace, "rol:writer") as span:
        obs.model_call(
            span,
            model="claude-sonnet-5",
            prompt_version="v3",
            input_tokens=100,
            output_tokens=200,
            cache_read_tokens=10,
            cache_write_tokens=5,
            cost_usd=0.5,
            latency_ms=1200,
        )

    (call,) = span.model_calls
    assert call.model == "claude-sonnet-5"
    assert call.prompt_version == "v3"
    assert call.input_tokens == 100
    assert call.output_tokens == 200
    assert call.cache_read_tokens == 10
    assert call.cache_write_tokens == 5
    assert call.cost_usd == 0.5
    assert call.latency_ms == 1200


def test_a_score_with_name_value_and_comment_is_captured(obs: NullObservability) -> None:
    with obs.trace("run:1") as trace, obs.span(trace, "capitulo-1") as span:
        obs.score(trace, "rubrica-capitulo", 4, comment="bien", span=span)

    (score,) = trace.scores
    assert score.name == "rubrica-capitulo"
    assert score.value == 4
    assert score.comment == "bien"
    assert score.span is span


def test_emitting_the_same_object_twice_keeps_a_single_trace(obs: NullObservability) -> None:
    with obs.trace("run:1", name="generacion") as first:
        obs.score(first, "a", 1)

    with obs.trace("run:1", name="generacion") as second:
        obs.score(second, "b", 1)

    assert len(obs.traces) == 1
    assert [s.name for s in obs.traces["run:1"].scores] == ["a", "b"]


def test_traces_of_two_different_objects_are_distinct(obs: NullObservability) -> None:
    with obs.trace("run:1"):
        pass
    with obs.trace("run:2"):
        pass
    with obs.trace(""):
        pass
    with obs.trace(" "):
        pass

    assert len(obs.traces) == 4


def test_a_span_with_warning_level_captures_it_with_its_reason(obs: NullObservability) -> None:
    with (
        obs.trace("run:1") as trace,
        obs.span(trace, "tool:browser_navigate", level="WARNING", reason="tool denegada"),
    ):
        pass

    assert trace.spans[0].level == "WARNING"
    assert trace.spans[0].status_message == "tool denegada"


def test_a_span_without_a_level_gets_the_normal_level(obs: NullObservability) -> None:
    with obs.trace("run:1") as trace, obs.span(trace, "tool:submit_chapter"):
        pass

    assert trace.spans[0].level == "DEFAULT"


def test_a_span_whose_block_raises_closes_with_error_and_propagates(
    obs: NullObservability,
) -> None:
    with (
        pytest.raises(ValueError, match="boom"),
        obs.trace("run:1") as trace,
        obs.span(trace, "rol:writer"),
    ):
        raise ValueError("boom")

    assert trace.spans[0].level == "ERROR"
    assert trace.spans[0].status_message == "boom"


def test_getting_a_versioned_prompt_answers_there_is_no_remote_version(
    obs: NullObservability,
) -> None:
    assert obs.get_prompt("writer", "production") is None


def test_checking_the_connection_is_correct_without_network(obs: NullObservability) -> None:
    assert obs.check() is True


def test_flushing_has_no_effect_but_is_counted(obs: NullObservability) -> None:
    obs.flush()
    obs.flush()

    assert obs.flush_count == 2
