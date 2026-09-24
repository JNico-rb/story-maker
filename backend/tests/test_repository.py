"""Lo que git versiona e ignora en el repositorio (spec 000)."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def git(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=False
    )


IGNORED = [
    "backend/.venv/pyvenv.cfg",
    "frontend/node_modules/react/index.js",
    "frontend/dist/index.html",
    "lean/.lake/build/lib/x.olean",
    "backend/data/story-maker.db",
    ".playwright-mcp/page.png",
    "__pycache__/x.pyc",
    "backend/src/story_maker/deep/__pycache__/x.cpython-312.pyc",
    ".pytest_cache/README.md",
    "backend/.pytest_cache/README.md",
    ".mypy_cache/3.12/x.json",
    "backend/.mypy_cache/3.12/x.json",
    ".ruff_cache/CACHEDIR.TAG",
    "backend/.ruff_cache/CACHEDIR.TAG",
    ".hypothesis/examples/x",
    "backend/tests/.hypothesis/examples/x",
    "tla/states/24-09-26-10-00-00/x.st",
    "tla/Harness_TTrace_1234.tla",
    "tla/tla2tools.jar",
    ".env",
    "backend/.env",
    ".claude/settings.local.json",
]

VERSIONED = [
    ".env.example",
    ".mcp.json",
    ".gitattributes",
    ".claude/settings.json",
    ".claude/hooks/guard-plan.mjs",
    ".claude/agents/auditor.md",
    ".claude/commands/orquestar.md",
    ".claude/skills/README.md",
    ".claude/memory/MEMORY.md",
    "backend/uv.lock",
    "backend/.python-version",
    "frontend/pnpm-lock.yaml",
    "frontend/src/shared/api/schema.d.ts",
    "backend/tests/data/brief.json",
    "images/qaracter-logo.png",
    "ejemplos/briefs/brief-1.json",
    "ejemplos/novela-ejemplo.pdf",
    "presentacion/deck.pptx",
    "presentacion/deck.pdf",
    "presentacion/demo.mp4",
]


@pytest.mark.parametrize("path", IGNORED)
def test_git_ignores_generated_files_and_secrets(path: str) -> None:
    assert git("check-ignore", "--no-index", "-q", path).returncode == 0, path


@pytest.mark.parametrize("path", VERSIONED)
def test_git_versions_what_is_delivered(path: str) -> None:
    assert git("check-ignore", "--no-index", "-q", path).returncode == 1, path


def test_no_text_file_in_the_index_has_crlf() -> None:
    lines = git("ls-files", "--eol").stdout.splitlines()

    assert lines
    assert [line for line in lines if line.startswith("i/crlf")] == []


def test_the_logo_is_stored_as_binary() -> None:
    (line,) = git("ls-files", "--eol", "images/qaracter-logo.png").stdout.splitlines()

    assert line.startswith("i/-text")


def test_a_crlf_file_enters_the_index_with_lf_and_without_warnings(tmp_path: Path) -> None:
    git("init", "-q", cwd=tmp_path)
    git("config", "core.autocrlf", "true", cwd=tmp_path)
    (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    (tmp_path / "crlf.txt").write_bytes(b"uno\r\ndos\r\n")
    (tmp_path / "lf.txt").write_bytes(b"uno\ndos\n")

    added = git("add", ".", cwd=tmp_path)
    eols = git("ls-files", "--eol", "crlf.txt", "lf.txt", cwd=tmp_path).stdout.splitlines()

    assert added.returncode == 0
    assert "LF will be replaced by CRLF" not in added.stderr
    assert [line.split()[0] for line in eols] == ["i/lf", "i/lf"]
