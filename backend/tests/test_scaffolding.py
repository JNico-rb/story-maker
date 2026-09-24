from importlib import import_module
from importlib.metadata import version

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
