"""Perfil de cada rol: lista blanca por modo, etiqueta y límites (`definitions.md` §12.2)."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.config import Config

SKILL = "Skill"
BROWSER_TOOLS = ("browser_navigate", "browser_snapshot", "browser_click")

LABELS = {
    "interviewer": "entrevistador",
    "extractor": "extractor",
    "planner": "planner",
    "writer": "writer",
    "editor": "editor",
    "judge": "juez",
    "visual_reviewer": "revisor-visual",
}

_WRITER = ("submit_chapter", SKILL)

WHITELIST: dict[tuple[str, str | None], tuple[str, ...]] = {
    ("interviewer", None): ("update_brief",),
    ("extractor", None): ("submit_facts",),
    ("planner", "plan"): ("submit_plan",),
    ("planner", "change"): ("propose_change",),
    ("writer", "write"): _WRITER,
    ("writer", "rewrite"): _WRITER,
    ("writer", "revise"): _WRITER,
    ("editor", None): ("submit_review", SKILL),
    ("judge", None): ("submit_evaluation",),
    ("visual_reviewer", None): ("submit_visual_review", *BROWSER_TOOLS),
}


class ToolsMismatch(ValueError):
    """Las tools propias declaradas no cuadran con la lista blanca del rol y modo."""

    def __init__(self, role: str, mode: str | None, extra: list[str], missing: list[str]) -> None:
        self.extra = extra
        self.missing = missing
        super().__init__(
            f"las tools de {role} en modo {mode} no cuadran con su lista blanca: "
            f"sobran {extra or 'ninguna'}; faltan {missing or 'ninguna'}"
        )


@dataclass(frozen=True)
class RoleProfile:
    role: str
    mode: str | None
    label: str
    model: str
    max_turns: int
    max_output_tokens: int
    whitelist: tuple[str, ...]

    @property
    def own_tools(self) -> tuple[str, ...]:
        """Las de la lista blanca que no son `Skill` ni del browser MCP."""
        return tuple(t for t in self.whitelist if t != SKILL and t not in BROWSER_TOOLS)

    @property
    def uses_skill(self) -> bool:
        return SKILL in self.whitelist

    def check_tools(self, declared: list[str]) -> None:
        extra = [tool for tool in declared if tool not in self.own_tools]
        missing = [tool for tool in self.own_tools if tool not in declared]
        if extra or missing:
            raise ToolsMismatch(self.role, self.mode, extra, missing)


def role_profile(config: Config, role: str, mode: str | None) -> RoleProfile:
    limits = config.roles[role]
    return RoleProfile(
        role=role,
        mode=mode,
        label=LABELS[role],
        model=limits.model,
        max_turns=limits.max_turns,
        max_output_tokens=limits.max_output_tokens,
        whitelist=WHITELIST[(role, mode)],
    )
