"""El MotorDePoliticas nunca invoca un modelo ni el puerto de agente: `policy/` no importa
`agents/` (005-I1, análogo a domain/test_dependency_rule.py)."""

import ast
from pathlib import Path

POLICY = Path(__file__).resolve().parents[2] / "src" / "story_maker" / "policy"


def _imports_agents(source: str) -> bool:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [node.module or ""]
        else:
            continue
        if any(target.split(".")[:2] == ["story_maker", "agents"] for target in targets):
            return True
    return False


def test_policy_no_importa_agents() -> None:
    violations = [
        str(path.relative_to(POLICY.parent))
        for path in POLICY.rglob("*.py")
        if _imports_agents(path.read_text(encoding="utf-8"))
    ]

    assert violations == []
