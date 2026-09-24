"""Solo el puerto de agente usa el Agent SDK: fuera de `agents/` nadie lo importa (003-I7)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[2] / "src" / "story_maker"
SDK = "claude_agent_sdk"


def sdk_imports(source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            targets = [node.module or ""]
        else:
            continue
        found += [f"línea {node.lineno}: {t}" for t in targets if t.split(".")[0] == SDK]
    return found


@pytest.mark.parametrize(
    "source",
    [
        "import claude_agent_sdk",
        "from claude_agent_sdk import query",
        "import claude_agent_sdk.types",
    ],
)
def test_the_rule_detects_every_form_of_importing_the_sdk(source: str) -> None:
    assert sdk_imports(source) != []


@pytest.mark.parametrize("source", ["import claude", "from story_maker.agents import port"])
def test_the_rule_ignores_other_imports(source: str) -> None:
    assert sdk_imports(source) == []


def test_no_module_outside_the_agent_port_imports_the_sdk() -> None:
    violations = [
        f"{path.relative_to(PACKAGE)} {violation}"
        for path in PACKAGE.rglob("*.py")
        if path.relative_to(PACKAGE).parts[0] != "agents"
        for violation in sdk_imports(path.read_text(encoding="utf-8"))
    ]

    assert violations == []
