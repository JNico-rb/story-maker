"""`domain` no importa nada del proyecto fuera de sí mismo (architecture.md §15.9, regla 1)."""

import ast
from pathlib import Path

import pytest

DOMAIN = Path(__file__).resolve().parents[2] / "src" / "story_maker" / "domain"


def forbidden_imports(source: str, module: str) -> list[str]:
    """Importaciones de `source` (el módulo `module`, dentro de `domain`) que salen de `domain`."""
    package = module.rsplit(".", 1)[0]
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = package.split(".")[: len(package.split(".")) - node.level + 1]
                base = ".".join([*parts, base] if base else parts)
            targets = [
                f"{base}.{alias.name}" if base == "story_maker" else base for alias in node.names
            ]
        else:
            continue
        found += [
            f"línea {node.lineno}: {target}"
            for target in targets
            if target.split(".")[0] == "story_maker"
            and target != "story_maker.domain"
            and not target.startswith("story_maker.domain.")
        ]
    return found


@pytest.mark.parametrize(
    "source",
    [
        "from story_maker.store import X",
        "import story_maker.store",
        "from story_maker import config",
        "from ..store import X",
    ],
)
def test_the_rule_rejects_imports_leaving_domain(source: str) -> None:
    assert forbidden_imports(source, "story_maker.domain.x") != []


@pytest.mark.parametrize(
    "source",
    [
        "import unicodedata",
        "from pydantic import BaseModel",
        "from story_maker.domain.rules import X",
        "from .rules import X",
    ],
)
def test_the_rule_accepts_the_standard_library_third_parties_and_domain(source: str) -> None:
    assert forbidden_imports(source, "story_maker.domain.x") == []


def test_the_rule_names_file_and_import() -> None:
    assert forbidden_imports(
        "import os\nfrom story_maker.store import X", "story_maker.domain.x"
    ) == ["línea 2: story_maker.store"]


def test_the_real_domain_imports_nothing_else_of_the_project() -> None:
    violations = [
        f"{path.relative_to(DOMAIN.parent)} {violation}"
        for path in DOMAIN.rglob("*.py")
        for violation in forbidden_imports(
            path.read_text(encoding="utf-8"),
            ".".join(["story_maker", *path.relative_to(DOMAIN.parent).with_suffix("").parts]),
        )
    ]

    assert violations == []
