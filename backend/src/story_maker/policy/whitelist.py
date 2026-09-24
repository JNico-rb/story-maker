"""Lista blanca de tools por rol y modo (definitions.md §12.2)."""

ROLE_TOOLS: dict[str, set[str]] = {
    "interviewer": {"update_brief"},
    "extractor": {"submit_facts"},
    "writer": {"submit_chapter", "Skill"},
    "editor": {"submit_review", "Skill"},
    "judge": {"submit_evaluation"},
    "visual_reviewer": {
        "browser_navigate",
        "browser_snapshot",
        "browser_click",
        "submit_visual_review",
    },
}

ALLOWED_SKILL = "personalizacion-natural"


# Roles cuyas tools dependen del modo: el planner en modo cambio solo tiene `propose_change`
# (RT4, verification.md §4.9). Sin un modo válido no tienen ninguna tool.
MODE_TOOLS: dict[tuple[str, str], set[str]] = {
    ("planner", "plan"): {"submit_plan"},
    ("planner", "change"): {"propose_change"},
}


def role_tools(role: str, mode: str | None = None) -> set[str]:
    if mode is not None and (role, mode) in MODE_TOOLS:
        return MODE_TOOLS[(role, mode)]
    return ROLE_TOOLS.get(role, set())


def is_tool_allowed(role: str, tool: str, mode: str | None = None) -> bool:
    return tool in role_tools(role, mode)
