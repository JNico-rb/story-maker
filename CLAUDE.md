# CLAUDE.md — Instructions

**Work only on the V2-test branch.** The project restarted from scratch; other branches are not a valid reference ([ADR 0002](docs/adr/0002-v2-desde-cero.md)).

## What is being built

The final exam of a Harness Engineering course: personalized gift novels set after the AI revolution. [project-constraints.md](project-constraints.md) is the brief every doc and spec answers to; the optional items in it are in scope. What was decided and why, before any code: [ADR 0003](docs/adr/0003-pivote-al-encargo.md).

## Two harnesses

This repository builds a harness, and is itself developed inside one:

- **This file** instructs development: you, working on the code, the docs and the specs.
- **`backend/harness_workspace/CLAUDE.md`** instructs the product's roles —interviewer, planner, writer, critic, editor and the rest— at runtime, through the Claude Agent SDK. Its rules bind them, not you; read it to learn what the roles are told.

## Stack

- **Backend:** runs through `uv`; lint with Ruff, types with mypy strict.
- **Frontend:** runs through `pnpm` 10.x; TypeScript strict; lint with ESLint plus the production build.
- **Product roles:** run on the Claude Agent SDK from `backend/harness_workspace/`.

Full stack: `docs/architecture.md` §14.1.

The dev laptop is Windows without admin rights, under Smart App Control. Lean runs only in CI or on GitHub Actions ([ADR 0004](docs/adr/0004-lean-en-github-actions.md)). A tool that exits silently is a blocked or missing DLL before it is a bug.

## Docs — `docs/`

`docs/` holds the four reference docs below, `adr/`, and `relational-matrix.md` —the gap between each plan and `architecture.md` ([process 3](workflow/3-plan.md))—, nothing else. A new file goes there only when strictly necessary —`security-report.md`, which the brief names— or as a working file deleted once its job is done. Load only the one the task needs. One concern per doc; cross-reference instead of copying.

**Reference docs are the source of truth:**

- [definitions.md](docs/definitions.md) — entities, attributes, class models, and their projection to code identifiers (§12). **Naming authority: use every term exactly as defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — why the domain works this way: personalization, novum, contradiction rules, chronology, tropes, readability. For prompts, rubrics and rules.
- [architecture.md](docs/architecture.md) — interview, story bible, planning, memory, harness, chapter loop, runs and versions, validators, guardrails, observability, platform, stack, API. §15 open decisions, §16 closed (the trade-off record).
- [verification.md](docs/verification.md) — how the system is verified in CI: T/A/I/D/U classes (§2), coverage table (§5), accepted risks (§6). For tests, evals, CI, guardrails.
- [adr/](docs/adr/) — the why behind decisions no doc section owns, mostly how the project is built. Load only the one the task needs; when to write one: [process 1](workflow/1-docs.md), step 3.

**Process records** are sections of `verification.md`, next to the method that produces them: eval results (§4.2), red-team cases (§4.9), the iteration log (§8) and Claude Code usage —browser MCP inspections, subagents, commands— (§9). They are the exam's evidence of reasoning: add a row when its event happens; [workflow/4-code.md](workflow/4-code.md) says which event feeds which record. Where every deliverable of the brief lives: the root [README.md](README.md).

Entity names and diagram identifiers: ASCII without accents, no spaces (Mermaid).

Language: a file keeps the language it is written in. New files:

- development instructions (`CLAUDE.md`, `workflow/`, `.claude/`) in English;
- `docs/`, `specs/`, the product's prompts (`backend/harness_workspace/`) and its UI in Spanish;
- code identifiers in English, taken from `definitions.md` §12.

Editing `CLAUDE.md`, `workflow/` or anything in `.claude/` → load the `writing-for-agents` skill first.

## Specs — `specs/NNN-slug/`, one folder per feature

`specs/` sits at the repo root and is **not** a reference doc. `docs/` states domain truth and design rationale; a spec states a feature's observable behaviour.

Each folder holds `spec.md` (what), `plan.md` (steps) and, when needed, `design.md` (how). The SQLite schema diagram is `docs/architecture.md` §14.5; column-level detail and the external interfaces of the whole backend: `specs/001-base/design.md`.

## Workflow — layers, always in this order

`docs/` → `spec.md` → `plan.md` → tests → code → document. Each layer is asked for by the one above it. Code no plan asks for, a plan no approved spec asks for, or a spec no doc supports, is drift.

### Approval gates

| To do | Required first |
|---|---|
| Change a reference doc | Grill round on the task |
| Write or change a spec | Supporting docs + a grill round **on that spec** |
| Write the plan | That `spec.md`'s approval box `[x]` |
| Write tests or code | That `plan.md`'s approval box `[x]` + its gap at zero in `docs/relational-matrix.md` + a failing test |

**Only the user marks an approval box.** Never mark one, never assume one, never read agreement in conversation as approval. Box unmarked → **stop and ask**.

### Grill (`grill-me` skill)

Run before the first edit to a reference doc, `specs/`, `backend/` or `frontend/`. Once per task, not per file — but **every spec gets its own round**, even mid-task.

Grill the task, not the diff:

- what is asked;
- which layer owns it;
- which `definitions.md` terms it uses;
- which requirements it implies;
- what is out of scope.

Edit once every question is answered. Exempt: trivial non-semantic edits (typos, formatting, links) and rows appended to a process record.

A task too big for one session, with the route still unclear → `/wayfinder` instead: it charts a map of decision tickets in `.scratch/` and grills one ticket per session.

### Processes — read the one for the layer you touch

- Changing a reference doc → [workflow/1-docs.md](workflow/1-docs.md)
- Writing or changing a `spec.md` → [workflow/2-specs.md](workflow/2-specs.md)
- Writing or changing a `plan.md` → [workflow/3-plan.md](workflow/3-plan.md)
- Writing tests or code, fixing a bug, closing a feature → [workflow/4-code.md](workflow/4-code.md)
