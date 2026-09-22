# AGENTS.md — Instructions

**Work only on the V2-test branch.** The project restarted from scratch; other branches are not a valid reference ([ADR 0002](docs/adr/0002-v2-desde-cero.md)).

## Stack

Backend runs through `uv` (lint: Ruff). Frontend runs through `pnpm`, TypeScript strict (lint: ESLint + production build). Full stack: `docs/architecture.md` §9.1.

## Reference docs — `docs/*.md` is the source of truth

Load only the one the task needs. One concern per doc; cross-reference instead of copying.

- [definitions.md](docs/definitions.md) — entities, attributes, class models. **Naming authority: use every term exactly as defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — why the genre works this way. For prompts, rubrics, trope scoring, novum logic.
- [architecture.md](docs/architecture.md) — pipeline, context and memory, quality gates (runtime judges of the novel), config, the agents, stack, API. §10 open decisions, §11 closed.
- [verification.md](docs/verification.md) — how the system is verified in CI: T/A/I/D/U classes (§2), coverage table (§5), accepted risks (§6). For tests, evals, CI, guardrails.
- [adr/](docs/adr/) — the why behind decisions no doc section owns, mostly how the project is built. Load only the one the task needs; when to write one: [process 1](workflow/1-docs.md), step 3.

Entity names and diagram identifiers: ASCII without accents, no spaces (Mermaid).

Language: a file keeps the language it is written in. New files: agent instructions (`AGENTS.md`, `workflow/`) in English; `docs/`, `specs/` and the product in Spanish.

## Specs — `specs/NNN-slug/`, one folder per feature

`specs/` sits at the repo root and is **not** a reference doc: `docs/*.md` states domain truth and design rationale; a spec states a feature's observable behaviour. Each folder holds `spec.md` (what), `plan.md` (steps) and, when needed, `design.md` (how). Tables and external interfaces of the whole backend: [specs/001-base/design.md](specs/001-base/design.md).

## Workflow — layers, always in this order

`docs/*.md` → `spec.md` → `plan.md` → tests → code → document. Each layer is asked for by the one above it; code no plan asks for, a plan no approved spec asks for, or a spec no doc supports, is drift.

### Approval gates

| To do | Required first |
|---|---|
| Change `docs/*.md` | Grill round on the task |
| Write or change a spec | Supporting docs + a grill round **on that spec** |
| Write the plan | That `spec.md`'s approval box `[x]` |
| Write tests or code | That `plan.md`'s approval box `[x]` + a failing test |

**Only the user marks an approval box.** Never mark one, never assume one, never read agreement in conversation as approval. Box unmarked → **stop and ask**.

### Grill (`grill-me` skill)

Run before the first edit to `docs/*.md`, `specs/`, `backend/` or `frontend/`. Once per task, not per file — but **every spec gets its own round**, even mid-task. Grill the task, not the diff: what is asked, which layer owns it, which `definitions.md` terms it uses, which requirements it implies, what is out of scope. Edit once every question is answered. Trivial non-semantic edits (typos, formatting, links) are exempt.

A task too big for one session, with the route still unclear → `/wayfinder` instead: it charts a map of decision tickets in `.scratch/` and grills one ticket per session.

### Processes — read the one for the layer you touch

- Changing `docs/*.md` → [workflow/1-docs.md](workflow/1-docs.md)
- Writing or changing a `spec.md` → [workflow/2-specs.md](workflow/2-specs.md)
- Writing or changing a `plan.md` → [workflow/3-plan.md](workflow/3-plan.md)
- Writing tests or code, fixing a bug, closing a feature → [workflow/4-code.md](workflow/4-code.md)
