# backend/AGENTS.md

Overrides the root `AGENTS.md` on backend specifics only — never on the gates or the layer order.

## Stack and commands

Python 3.12 (pinned in `.python-version`), uv, FastAPI + uvicorn in **one process** (the worker is an asyncio task; global FIFO queue, one active run), Pydantic v2, SQLAlchemy 2 sync with `create_all` (no Alembic: the dev DB is recreated), SQLite WAL + `foreign_keys=ON` + `busy_timeout`, FTS5, `sqlite-vec`, `fastembed`, `claude-agent-sdk` (default `LLM_PROVIDER=claude_login`, the machine's Claude Code login; `anthropic_compatible` optional), `langfuse` v4, `fastmcp` at `/mcp`, `playwright` on the installed Edge, `pypdf`, Jinja2, bcrypt, PyJWT, typer. Quality: Ruff, mypy strict on `src/`, pytest + pytest-asyncio + hypothesis. Every dependency is declared up front in `pyproject.toml` (spec 000) so lanes never collide on `uv.lock`: a lane edits neither file, and a missing dependency goes to the integrator.

Commands from `backend/`, as listed in the root `CLAUDE.md`: `uv sync` once per worktree, then `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`. `uv run story-maker serve` never takes `--reload`: it breaks the Agent SDK subprocesses on Windows.

## Modules — `src/story_maker/`

- `domain/` — pure models, brief rules and contradictions C1–C6, banned-term normalization, assignment constants, rubrics and criteria, trope catalog. No I/O.
- `store/` — SQLAlchemy models (full schema), session, repositories, version copy.
- `agents/` — agent port (Agent SDK + deterministic fake), workspace, tools with schema, hook mechanism, token ceiling, limits, usage and cost.
- `policy/` — policy engine, banned terms, injection detector, audit log.
- `observability/` — observability port with null double, Langfuse adapter, mask, versioned prompts, scores.
- `interview/` — interviewer, extractor, brief.
- `pipeline/` — orchestrator (state machine), queue, worker, planning, production, gate, changes, manual edit, resume.
- `retrieval/` — CanonCards, BM25, dense, RRF.
- `validators/` — programmatic and semantic validators (judge), visual review.
- `formal/` — Lean file generator and `formal_verifier` (local | github).
- `lint/` — prose linters. `render/` — `version_view` (Jinja2) and PDF.
- `api/` — FastAPI routers, auth, dependencies; MCP server.
- `cli.py` typer CLI · `settings.py` `.env` settings · `config.py` `config.json` validation.

**Dependency rule:** `domain` imports nothing from the project; `pipeline` orchestrates and is the only module that calls several others; `api` composes. Everything that calls a model goes through the agent port; everything that emits telemetry, through the observability port.

## Tests — `backend/tests/<module>/`, mirroring `src`

- **Doubles are mandatory: no class-T test calls a real model or real Langfuse.** Roles run on the deterministic fake of the agent port, telemetry on the null double; no network, no `.env` (settings come from fixtures). Shared fixtures (fake role double, fictional briefs) live under `tests/`.
- Class-D demonstrations with a real model run once at the end of a spec, grouped: they spend the subscription's quota.

## Module ownership by spec

A spec touches only its modules and their `tests/<module>/`. In a shared module it adds its own files; another spec's files change only through the integrator. Spec 000 (integrator, on V2) owns `pyproject.toml`, `uv.lock`, `.python-version`, the package skeleton, tool config and CI.

| Spec | Lane | Modules it may touch |
|---|---|---|
| 001 base | A | `config.py`, `settings.py`, `cli.py` (`serve`, `init-db`, `check-env`), `store/` (full schema, session), `api/` (app, health), `observability/` (port + null double), `domain/` (assignment constants) |
| 002 autenticacion | C | `api/` (auth, current-user dependency, ownership), `store/` (user repository) |
| 003 puerto-de-agente | A | `agents/` |
| 004 observabilidad | B | `observability/` (Langfuse adapter, mask, prompts, scores), `cli.py` (`prompts push`) |
| 005 guardarrailes | C | `policy/`, `domain/` (banned-term normalization) |
| 006 especificacion-tla | D | `tla/` (repo root) |
| 007 validador-lean | D | `formal/`, `lean/` (repo root) |
| 008 brief-y-entrevista | C | `interview/`, `domain/` (brief rules, C1–C6), `api/` (novels, interview, free texts, brief, banned terms) |
| 009 story-bible-y-versiones | B | `store/` (story bible and version-copy repositories), `api/` (story bible) |
| 010 planificacion | A | `pipeline/` (planning), `validators/` (`outline`), planner prompt |
| 011 produccion-de-capitulos | A | `pipeline/` (queue, worker, production, resume), `validators/` (chapter), `harness_workspace/` (product `CLAUDE.md`, skill, writer and editor prompts), `api/` (runs), `cli.py` (`resume`) |
| 012 gate-de-publicacion | A | `pipeline/` (gate, publication), `validators/` (novel, judge), `domain/` (novel rubric, trope catalog), judge prompt |
| 013 lectura-y-pdf | B | `render/`, `api/` (versions, PDF, `/view`), `cli.py` (`example`, `export-pdf`), `ejemplos/novela-ejemplo.pdf` |
| 014 cambios-del-lector | A | `pipeline/` (changes), `api/` (change requests), planner change-mode prompt |
| 015 servidor-mcp | B | `api/` (MCP server) |
| 016 recuperacion-hibrida | D | `retrieval/` |
| 017 revision-visual | B | `validators/` (visual review), visual reviewer prompt |
| 018 linters-de-prosa | C | `lint/`, `api/` (chapter lint) |
| 019 edicion-manual | C | `pipeline/` (manual edit), `api/` (chapter save) |
| 020 evals | D | `cli.py` (`evals run\|table`), `ejemplos/briefs/` |
| 021 auditoria-de-seguridad | D | `docs/security-report.md` via the `seguridad` subagent; fixes go to the owning lane |
