"""Lo que git versiona e ignora en el repositorio (spec 000)."""

import json
import re
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


def test_project_settings_register_the_hooks_and_the_permissions() -> None:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))

    (entry,) = settings["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Edit|Write|MultiEdit"
    assert [hook["command"] for hook in entry["hooks"]] == [
        'node "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard-secretos.mjs"',
        'node "${CLAUDE_PROJECT_DIR}/.claude/hooks/guard-plan.mjs"',
    ]
    permissions = settings["permissions"]
    assert sorted(permissions["deny"]) == sorted(
        [
            "Read(.env)",
            "Read(**/.env)",
            "Read(.claude/settings.local.json)",
            "Bash(git push --force*)",
            "Bash(git push -f*)",
        ]
    )
    assert sorted(permissions["allow"]) == sorted(
        [
            "Bash(uv *)",
            "Bash(pnpm.cmd *)",
            "Bash(node *)",
            "Bash(java *)",
            "Bash(git status*)",
            "Bash(git diff*)",
            "Bash(git log*)",
            "Bash(git show*)",
            "Bash(git add*)",
            "Bash(git commit*)",
            "Bash(git branch*)",
            "Bash(git worktree*)",
            "Bash(git merge*)",
            "Bash(git rebase*)",
        ]
    )
    assert not [rule for rule in permissions["allow"] if rule.startswith("Bash(git push")]
    assert permissions["additionalDirectories"] == [f"../sm-{x}" for x in "abcde"]


MEMORY = ROOT / ".claude" / "memory"
LEAKS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"),
    "user profile path": re.compile(r"[A-Za-z]:[\\/]Users[\\/]|/home/|/Users/"),
    "uuid": re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
    "company name": re.compile(r"qaracter", re.I),
}


def test_the_memory_mirror_has_one_file_per_index_entry_and_nothing_else() -> None:
    index = (MEMORY / "MEMORY.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(([^)]+\.md)\)", index))
    files = {p.name for p in MEMORY.glob("*.md")} - {"MEMORY.md", "README.md"}

    assert (MEMORY / "README.md").is_file()
    assert linked
    assert linked == files


@pytest.mark.parametrize("leak", LEAKS)
def test_the_memory_mirror_is_sanitised(leak: str) -> None:
    offenders = [
        p.name for p in MEMORY.glob("*.md") if LEAKS[leak].search(p.read_text(encoding="utf-8"))
    ]

    assert offenders == []


def test_no_versioned_file_holds_a_key_shaped_string() -> None:
    # Same scan as the CI job: every finding must be an audited false positive in the baseline.
    from detect_secrets import SecretsCollection
    from detect_secrets.settings import default_settings

    baseline = json.loads((ROOT / ".secrets.baseline").read_text(encoding="utf-8"))
    audited = {
        (name, item["hashed_secret"])
        for name, items in baseline["results"].items()
        for item in items
        if item.get("is_secret") is False
    }
    skipped = re.compile(baseline["filters_used"][-1]["pattern"][0])
    files = [
        f
        for f in git("ls-files").stdout.splitlines()
        if f != ".secrets.baseline" and not skipped.search(f)
    ]
    secrets = SecretsCollection(root=str(ROOT))
    with default_settings():
        secrets.scan_files(*files)

    found = {(name.replace("\\", "/"), secret.secret_hash) for name, secret in secrets} - audited
    assert found == set()
