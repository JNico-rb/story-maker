import subprocess
import sys
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

import pytest
from typer.testing import CliRunner

from story_maker.cli import app

MODULES = [
    "domain",
    "store",
    "agents",
    "policy",
    "observability",
    "interview",
    "pipeline",
    "retrieval",
    "validators",
    "formal",
    "lint",
    "render",
    "api",
]


@pytest.mark.parametrize("module", MODULES)
def test_every_module_of_the_package_imports(module: str) -> None:
    assert import_module(f"story_maker.{module}").__doc__


def test_version_flag_prints_the_installed_version() -> None:
    result = CliRunner().invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == version("story-maker")


def test_the_environment_runs_python_3_12() -> None:
    assert sys.version_info[:2] == (3, 12)


STACK = [
    "fastapi",
    "uvicorn",
    "pydantic",
    "sqlalchemy",
    "sqlite_vec",
    "fastembed",
    "claude_agent_sdk",
    "langfuse",
    "fastmcp",
    "playwright",
    "pypdf",
    "jinja2",
    "bcrypt",
    "jwt",
    "typer",
    "pytest_asyncio",
    "hypothesis",
]


@pytest.mark.parametrize("module", STACK)
def test_every_stack_dependency_imports(module: str) -> None:
    import_module(module)


@pytest.mark.parametrize(
    ("distribution", "major"), [("pydantic", 2), ("sqlalchemy", 2), ("langfuse", 4)]
)
def test_stack_dependencies_have_the_expected_major_version(distribution: str, major: int) -> None:
    assert int(version(distribution).split(".")[0]) == major


# Como módulos: Smart App Control puede bloquear el lanzador .exe que uv genera para cada orden.
@pytest.mark.parametrize("module", ["detect_secrets", "pip_audit"])
def test_security_tools_answer_their_version(module: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", module, "--version"], capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    assert result.stdout.strip()


@pytest.mark.parametrize("module", MODULES)
def test_tests_have_a_folder_per_module(module: str) -> None:
    assert (Path(__file__).parent / module).is_dir()
