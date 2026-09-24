"""Lista blanca de tools por rol (definitions.md §12.2)."""

ROLE_TOOLS: dict[str, set[str]] = {
    "interviewer": {"update_brief"},
    "extractor": {"submit_facts"},
    "planner": {"submit_plan", "propose_change"},
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


def is_tool_allowed(role: str, tool: str) -> bool:
    return tool in ROLE_TOOLS.get(role, set())
