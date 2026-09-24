"""Perfil de cada rol: lista blanca por modo, etiqueta y límites (`definitions.md` §12.2).

La lista blanca es la de `policy/`, la misma que aplica el hook de policy (§12.3)."""

from __future__ import annotations

from dataclasses import dataclass

from story_maker.config import Config
from story_maker.policy.whitelist import ROLE_TOOLS

SKILL = "Skill"
MODES: dict[str, tuple[str, ...]] = {
    "planner": ("plan", "change"),
    "writer": ("write", "rewrite", "revise"),
}
# Las tools de la lista del rol que solo tiene uno de sus modos: el planner en modo `change`
# solo tiene `propose_change` (definitions.md §12.2).
_MODE_ONLY = {"submit_plan": "plan", "propose_change": "change"}

LABELS = {
    "interviewer": "entrevistador",
    "extractor": "extractor",
    "planner": "planner",
    "writer": "writer",
    "editor": "editor",
    "judge": "juez",
    "visual_reviewer": "revisor-visual",
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
        return tuple(t for t in self.whitelist if t != SKILL and not is_browser_tool(t))

    @property
    def browser_tools(self) -> tuple[str, ...]:
        return tuple(t for t in self.whitelist if is_browser_tool(t))

    @property
    def uses_skill(self) -> bool:
        return SKILL in self.whitelist

    def check_tools(self, declared: list[str]) -> None:
        extra = [tool for tool in declared if tool not in self.own_tools]
        missing = [tool for tool in self.own_tools if tool not in declared]
        if extra or missing:
            raise ToolsMismatch(self.role, self.mode, extra, missing)


def is_browser_tool(tool: str) -> bool:
    return tool.startswith("browser_")


def whitelist(role: str, mode: str | None) -> tuple[str, ...]:
    if mode not in MODES.get(role, (None,)):
        raise ValueError(f"el rol {role} no tiene el modo {mode}")
    return tuple(sorted(t for t in ROLE_TOOLS[role] if _MODE_ONLY.get(t, mode) == mode))


def role_profile(config: Config, role: str, mode: str | None) -> RoleProfile:
    limits = config.roles[role]
    return RoleProfile(
        role=role,
        mode=mode,
        label=LABELS[role],
        model=limits.model,
        max_turns=limits.max_turns,
        max_output_tokens=limits.max_output_tokens,
        whitelist=whitelist(role, mode),
    )
