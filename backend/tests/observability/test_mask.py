"""Máscara de datos personales: nombres y fechas fuera de lo exportado (004-C10, I1, C11)."""

from __future__ import annotations

from tests.conftest import FakeLangfuseClient

from story_maker.observability.langfuse_adapter import LangfuseObservability
from story_maker.observability.mask import Mask

RECIPIENT = "Toby"
DATE = "14 de marzo de 2027"


def _emit_a_role_session_naming_the_recipient_and_the_date(
    observability: LangfuseObservability, key: str
) -> None:
    with (
        observability.trace(key) as trace,
        observability.span(
            trace,
            "rol:writer",
            metadata={
                "input": f"{RECIPIENT} cumple años el {DATE}.",
                "output": f"Feliz cumpleaños, {RECIPIENT}, este {DATE}.",
            },
        ) as span,
    ):
        observability.model_call(
            span,
            model="claude-sonnet-5",
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=0,
            cache_write_tokens=0,
            cost_usd=0.02,
            latency_ms=800,
        )
        observability.score(
            trace,
            "rubrica-capitulo",
            4,
            comment=f"A {RECIPIENT} le encantará leerlo el {DATE}.",
            span=span,
        )


# --- C10: sustituye nombres y fechas, sin tocar tokens, coste, latencia ni scores -------------


def test_mask_replaces_the_recipient_name_and_the_date_before_exporting(
    fake_langfuse_client: FakeLangfuseClient,
) -> None:
    observability = LangfuseObservability(fake_langfuse_client)
    observability.add_mask("run:1", Mask(names=(RECIPIENT,), dates=(DATE,)))

    _emit_a_role_session_naming_the_recipient_and_the_date(observability, "run:1")
    observability.flush()

    exported_root = fake_langfuse_client.roots["trace-run:1"]
    exported_span = exported_root.children[0]
    assert exported_span.metadata is not None
    assert exported_span.metadata["input"] == "[NOMBRE_1] cumple años el [FECHA]."
    assert exported_span.metadata["output"] == "Feliz cumpleaños, [NOMBRE_1], este [FECHA]."

    exported_call = exported_span.children[0]
    assert exported_call.usage_details == {
        "input": 100,
        "output": 50,
        "cache_read": 0,
        "cache_write": 0,
    }
    assert exported_call.cost_details == {"total": 0.02}

    (score,) = fake_langfuse_client.scores
    assert score["value"] == 4
    assert score["comment"] == "A [NOMBRE_1] le encantará leerlo el [FECHA]."
