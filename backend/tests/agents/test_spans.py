"""Cada sesión y cada llamada a tool dejan su span (003-C27)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from story_maker.agents.ceiling import TokenCeiling
from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.policy_port import PolicyDecision, PolicyRequest
from story_maker.agents.port import AgentPort, Defect, SessionRequest
from story_maker.agents.profiles import role_profile
from story_maker.agents.sdk import SdkAgent
from story_maker.agents.usage import Usage
from story_maker.config import Config
from story_maker.observability.null import NullObservability
from story_maker.observability.port import Span, Trace
from story_maker.settings import Settings

USAGE = Usage(input_tokens=120, output_tokens=80, cache_read_tokens=30, cache_write_tokens=10)
BLOCKED = "Defectos bloqueantes:\n- [longitud-capitulo] demasiado corto"


class SpyObservability(NullObservability):
    """El doble nulo, anotando cuándo se abre y se cierra cada span."""

    def __init__(self, events: list[str]) -> None:
        super().__init__()
        self.events = events
        self.open: set[int] = set()

    @contextmanager
    def span(self, trace: Trace, name: str, *args: Any, **kwargs: Any) -> Iterator[Span]:
        with super().span(trace, name, *args, **kwargs) as span:
            self.open.add(id(span))
            self.events.append(f"abre {name}")
            try:
                yield span
            finally:
                self.open.discard(id(span))
                self.events.append(f"cierra {name}")


def children(span: Span) -> list[tuple[str, str, str | None]]:
    return [(c.name, c.level, c.status_message) for c in span.children]


async def test_each_session_and_each_tool_call_leave_their_span(
    config: Config,
    fake: FakeAgent,
    policy: Any,
    session_factory: Any,
    workspace: Path,
    make_request: Callable[..., SessionRequest],
) -> None:
    events: list[str] = []
    telemetry = SpyObservability(events)

    def rule(request: PolicyRequest) -> PolicyDecision:
        events.append(f"decide {request.tool}")
        text = {f.path: f.value for f in request.fields}.get("text")
        if text == "prohibido":
            return PolicyDecision("deny", "término prohibido")
        return PolicyDecision("allow")

    policy.rule = rule
    results = iter([[Defect("longitud-capitulo", "demasiado corto", True)], []])

    def checks(value: BaseModel) -> list[Defect]:
        return next(results)

    fake.script(
        "writer",
        "write",
        Script(
            steps=(
                Call("Skill", {"skill": "personalizacion-natural"}),
                Call("submit_chapter", {"title": "Uno", "text": "prohibido"}),
                Call("submit_chapter", {"title": "Uno"}),
                Call("submit_chapter", {"title": "Uno", "text": "corto"}),
                Call("submit_chapter", {"title": "Uno", "text": "largo"}),
                Say("fin"),
            ),
            usage=USAGE,
            sdk_cost_usd=20.0,
        ),
    )
    port = AgentPort(
        agent=fake,
        config=config,
        ceiling=TokenCeiling(config.token_ceiling),
        policy=policy,
        telemetry=telemetry,
        session_factory=session_factory,
        workspace=workspace,
    )
    trace = Trace(key="run:1")
    with telemetry.span(trace, "capitulo-4") as chapter_span:
        request = make_request(
            "writer",
            "write",
            trace=trace,
            parent_span=chapter_span,
            chapter=4,
            chapter_checks=checks,
        )
        result = await port.run(request)

    (role_span,) = chapter_span.children
    assert role_span.name == "rol:writer"
    assert role_span.parent is chapter_span
    assert role_span.metadata["chapter"] == 4
    (call,) = role_span.model_calls
    assert (call.model, call.prompt_version) == (config.roles["writer"].model, "v1")
    assert (call.input_tokens, call.output_tokens) == (120, 80)
    assert (call.cache_read_tokens, call.cache_write_tokens) == (30, 10)
    assert call.cost_usd == result.cost_usd
    assert call.latency_ms == result.latency_ms
    assert children(role_span) == [
        ("tool:Skill", "DEFAULT", None),
        ("tool:submit_chapter", "WARNING", "término prohibido"),
        ("tool:submit_chapter", "WARNING", "text: Field required"),
        ("tool:submit_chapter", "WARNING", BLOCKED),
        ("tool:submit_chapter", "DEFAULT", None),
    ]
    scores = [(s.value, s.span) for s in trace.scores if s.name == "schema-salida"]
    tool_spans = role_span.children
    assert scores == [(0, tool_spans[2]), (1, tool_spans[3]), (1, tool_spans[4])]
    # tool:Skill lo abre el hook de policy y lo cierra el de observabilidad
    skill = events.index("abre tool:Skill")
    assert events[skill - 1] == "decide Skill"
    assert events[skill + 1] == "cierra tool:Skill"
    assert telemetry.open == set()


@pytest.mark.parametrize(
    ("role", "mode", "label"),
    [
        ("interviewer", None, "rol:entrevistador"),
        ("extractor", None, "rol:extractor"),
        ("planner", "change", "rol:planner"),
        ("editor", None, "rol:editor"),
        ("judge", None, "rol:juez"),
        ("visual_reviewer", None, "rol:revisor-visual"),
    ],
)
async def test_role_spans_carry_the_role_label(
    role: str,
    mode: str | None,
    label: str,
    port: AgentPort,
    fake: FakeAgent,
    make_request: Callable[..., SessionRequest],
) -> None:
    fake.script(role, mode, Script(steps=(Say("fin"),), usage=USAGE))
    request = make_request(role, mode)

    await port.run(request)

    assert [span.name for span in request.trace.spans] == [label]


class RecordingHooks:
    def __init__(self, reason: str | None = None, replacement: str | None = None) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.reason = reason
        self.replacement = replacement
        self.stopping = False

    def before_tool(self, call_id: str, tool: str, tool_input: dict[str, Any]) -> str | None:
        self.calls.append(("before", call_id, tool))
        return self.reason

    def run_tool(self, tool: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
        return "ok", False

    def after_tool(self, call_id: str, tool: str) -> str | None:
        self.calls.append(("after", call_id, tool))
        return self.replacement


def sdk_hooks(
    config: Config,
    workspace: Path,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
    hooks: RecordingHooks,
) -> Any:
    options = SdkAgent(make_settings(), workspace=workspace).session_options(
        make_request("writer", "write"), role_profile(config, "writer", "write"), hooks
    )
    assert options.hooks is not None
    (pre,) = options.hooks["PreToolUse"]
    (post,) = options.hooks["PostToolUse"]
    return pre.hooks[0], post.hooks[0]


def pre_input(tool: str, call_id: str) -> dict[str, Any]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": tool,
        "tool_input": {"title": "Uno", "text": "x"},
        "tool_use_id": call_id,
    }


def post_input(tool: str, call_id: str) -> dict[str, Any]:
    return {**pre_input(tool, call_id), "hook_event_name": "PostToolUse", "tool_response": "ok"}


async def test_the_sdk_hooks_delegate_in_the_session_hooks_with_the_bare_tool_name(
    config: Config,
    workspace: Path,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
) -> None:
    hooks = RecordingHooks()
    pre, post = sdk_hooks(config, workspace, make_settings, make_request, hooks)

    allowed = await pre(pre_input("mcp__harness__submit_chapter", "t1"), "t1", {"signal": None})
    kept = await post(post_input("Skill", "t2"), "t2", {"signal": None})

    assert hooks.calls == [("before", "t1", "submit_chapter"), ("after", "t2", "Skill")]
    # permitir no decide nada: manda la lista blanca de la configuración (se aplica dos veces)
    assert allowed == {}
    assert kept == {}


async def test_the_sdk_hooks_deny_with_the_reason_and_replace_what_the_model_reads(
    config: Config,
    workspace: Path,
    make_settings: Callable[..., Settings],
    make_request: Callable[..., SessionRequest],
) -> None:
    hooks = RecordingHooks(reason="término prohibido", replacement=BLOCKED)
    pre, post = sdk_hooks(config, workspace, make_settings, make_request, hooks)
    tool = "mcp__harness__submit_chapter"

    denied = await pre(pre_input(tool, "t1"), "t1", {"signal": None})
    replaced = await post(post_input(tool, "t1"), "t1", {"signal": None})

    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert denied["hookSpecificOutput"]["permissionDecisionReason"] == "término prohibido"
    output = replaced["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    assert output["updatedMCPToolOutput"] == [{"type": "text", "text": BLOCKED}]
