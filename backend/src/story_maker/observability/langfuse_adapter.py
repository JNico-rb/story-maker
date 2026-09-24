"""Adaptador real del puerto de observabilidad: exporta a Langfuse Cloud UE (`architecture.md` §13).

Cumple el mismo contrato que `NullObservability` (001-C19..C21): delega en ella el registro de
trazas, spans, llamadas de modelo y scores, y en `flush()` exporta lo acumulado al cliente de
Langfuse, con la máscara aplicada antes de exportar (§13.5)."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from story_maker.observability.langfuse_client import LangfuseClientPort
from story_maker.observability.mask import Mask
from story_maker.observability.null import NullObservability
from story_maker.observability.port import ModelCall, Score, Span, Trace
from story_maker.observability.roles import ROLE_LABELS


class LangfuseObservability:
    """Doble el `flush()`: registra igual que el doble nulo y, además, exporta de verdad."""

    def __init__(self, client: LangfuseClientPort) -> None:
        self._client = client
        self._null = NullObservability()
        self._masks: dict[str, Mask] = {}

    # --- mismo contrato que NullObservability (001-C19..C21) ----------------------------------

    @contextmanager
    def trace(
        self, key: str, name: str | None = None, session: str | None = None
    ) -> Iterator[Trace]:
        with self._null.trace(key, name=name, session=session) as trace:
            yield trace

    @contextmanager
    def span(
        self,
        trace: Trace,
        name: str,
        parent: Span | None = None,
        metadata: dict[str, object] | None = None,
        level: str = "DEFAULT",
        reason: str | None = None,
    ) -> Iterator[Span]:
        with self._null.span(
            trace, name, parent=parent, metadata=metadata, level=level, reason=reason
        ) as span:
            yield span

    def model_call(
        self,
        span: Span,
        *,
        model: str,
        prompt_version: str | None = None,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: int = 0,
        sdk_cost_usd: float | None = None,
    ) -> ModelCall:
        return self._null.model_call(
            span,
            model=model,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            sdk_cost_usd=sdk_cost_usd,
        )

    def score(
        self,
        trace: Trace,
        name: str,
        value: float,
        comment: str | None = None,
        span: Span | None = None,
    ) -> Score:
        return self._null.score(trace, name, value, comment=comment, span=span)

    def get_prompt(self, role: str, label: str) -> str | None:
        try:
            handle = self._client.get_prompt(role, label=label)
        except Exception:
            return None
        return str(handle.version)

    def check(self) -> bool:
        try:
            return self._client.auth_check()
        except Exception:
            return False

    # --- máscara por novela, unida cuando una traza toca varias (004-C11) -------------------

    def add_mask(self, key: str, mask: Mask) -> None:
        self._masks[key] = self._masks.get(key, Mask.empty()) | mask

    # --- exportación real, con la máscara aplicada antes de salir (004-C10, 004-I1) ---------

    def flush(self) -> None:
        for trace in self._null.traces.values():
            self._export_trace(trace)
        self._client.flush()
        self._null.flush()

    def _export_trace(self, trace: Trace) -> None:
        mask = self._masks.get(trace.key, Mask.empty())
        trace_id = self._client.create_trace_id(seed=trace.key)
        observation_ids: dict[int, str] = {}
        metadata: dict[str, object] | None = {"session": trace.session} if trace.session else None
        with self._client.start_as_current_observation(
            trace_context={"trace_id": trace_id},
            name=trace.name or trace.key,
            as_type="span",
            metadata=metadata,
        ) as root:
            for span in trace.spans:
                self._export_span(root, span, mask, observation_ids)
        for trace_score in trace.scores:
            self._export_score(trace_id, trace_score, mask, observation_ids)

    def _export_span(
        self,
        parent: object,
        span: Span,
        mask: Mask,
        observation_ids: dict[int, str],
    ) -> None:
        with parent.start_as_current_observation(  # type: ignore[attr-defined]
            name=span.name,
            as_type="span",
            metadata=mask.apply_to_value(span.metadata),
            level=span.level,
            status_message=mask.apply(span.status_message) if span.status_message else None,
        ) as handle:
            observation_ids[id(span)] = handle.id
            for call in span.model_calls:
                self._export_model_call(handle, call)
            for child in span.children:
                self._export_span(handle, child, mask, observation_ids)

    def _export_model_call(self, parent: object, call: ModelCall) -> None:
        with parent.start_as_current_observation(  # type: ignore[attr-defined]
            name=f"llamada:{call.model}",
            as_type="generation",
            model=call.model,
            usage_details={
                "input": call.input_tokens,
                "output": call.output_tokens,
                "cache_read": call.cache_read_tokens,
                "cache_write": call.cache_write_tokens,
            },
            cost_details={"total": call.cost_usd},
            metadata={
                "prompt_version": call.prompt_version,
                "latency_ms": call.latency_ms,
                "sdk_cost_usd": call.sdk_cost_usd,
            },
        ):
            pass

    def _export_score(
        self,
        trace_id: str,
        score: Score,
        mask: Mask,
        observation_ids: dict[int, str],
    ) -> None:
        observation_id = observation_ids.get(id(score.span)) if score.span is not None else None
        self._client.create_score(
            name=score.name,
            value=score.value,
            comment=mask.apply(score.comment) if score.comment else score.comment,
            trace_id=trace_id,
            observation_id=observation_id,
        )


def auth_check(client: LangfuseClientPort, label: str, prompts_dir: Path) -> str | None:
    """Credenciales válidas y prompt vigente por rol; nunca falla en silencio (004-I3).

    Solo exige prompt a los roles con fichero en `prompts_dir`, los mismos que sube
    `prompts push` (004-bug): un rol sin fichero en el workspace, como `visual_reviewer`
    (017, fuera de alcance), no bloquea `check-env` ni `serve`."""
    try:
        ok = client.auth_check()
    except Exception as exc:
        return f"Langfuse: credenciales inválidas ({exc})"
    if not ok:
        return "Langfuse: credenciales inválidas"
    for identifier, role_label in ROLE_LABELS.items():
        if not (prompts_dir / f"{identifier}.md").is_file():
            continue
        try:
            client.get_prompt(role_label, label=label)
        except Exception:
            return f"Langfuse: falta el prompt vigente del rol '{identifier}'"
    return None
