# AGENTS.md — Instructions

**Work only on the V2-test branch. Ignore all other branches** — the project restarted from scratch; nothing before is a valid reference.

## Stack

- **Backend:** Python 3.12+, uv, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite with `sqlite-vec` and FTS5. Lint: Ruff.
- **Frontend:** Vite, React, TypeScript strict, Tailwind, pnpm. Lint: ESLint + production build.
- Full flow is also verified with live evaluators and a manual browser walkthrough.

## Reference docs — `docs/*.md` is the source of truth

Load only the one the task needs. One concern per doc; cross-reference, never duplicate.

- [definitions.md](docs/definitions.md) — entities, attributes, class models. **Naming authority: never invent a synonym for a term defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — why the genre works this way. For prompts, rubrics, trope scoring, novum logic.
- [architecture.md](docs/architecture.md) — pipeline, context and memory, quality gates, config, the agents, API. §10 open decisions, §11 closed.
- [verification.md](docs/verification.md) — T/A/I/D/U classes (§2), coverage table (§5), accepted risks (§6). For tests, evals, CI, guardrails.

[specs/](specs/) sits at the repo root, next to `docs/`, and is **not** one of these reference docs: it is layer 2 of the workflow, one file per feature. `docs/*.md` states domain truth and design rationale; `specs/NNN-nombre.md` states a feature’s observable behaviour.

Entity names and diagram identifiers: no accents, no spaces (Mermaid). Quality gates judge the novel at runtime; `verification.md` covers the system in CI.

When touching `backend/` or `frontend/`, read `backend/AGENTS.md` and `frontend/AGENTS.md` too: it overrides this file on its own specifics, never on the gates or the layer order.

## Workflow — five layers, always in this order

`docs/*.md` → `specs/` → `TODO.md` (implementation plan) → tests → code → document. Never skip upward: code no plan asks for, a plan no approved spec asks for, or a spec no doc supports, is drift.

### Gates

| To do | Required first |
|---|---|
| Change `docs/*.md` | Grill round on the task |
| Write or change a spec | Supporting docs + a grill round **on that spec** |
| Write the plan | That spec's approval box `[x]` |
| Write tests or code | That plan's approval box `[x]` + a failing test |

**Only the user marks an approval box.** Never mark one, never assume one, never read agreement in conversation as approval. Box unmarked → **stop and ask**.

### 0. Grill (`grill-me` skill)

Run before the first edit to `docs/*.md`, `specs/`, `TODO.md`, `backend/` or `frontend/`. Once per task, not per file — but **every spec gets its own round**, even mid-task. Grill the task, not the diff: what is asked, which layer owns it, which `definitions.md` terms it uses, which acceptance cases it implies, what is out of scope. Do not edit while questions are open. Trivial non-semantic edits (typos, formatting, links) are exempt.

### 1. Changing the reference docs (`docs/*.md`)

Source of truth about domain and design, never a description of today's code.

1. Pick the **single owning doc**.
2. New or renamed terms go to `definitions.md` first and nowhere else.
3. Closing a decision = moving it from `architecture.md` §10 to §11 with its reason. Reopening a §11 decision needs a stated reason in the same commit.
4. A new verification method goes to `verification.md` + its row in §5; an accepted risk goes to §6 with name and motive.
5. Before finishing, name every spec, plan block and piece of code the change now contradicts — fix or list them.

A doc change alone changes no behaviour; it must be followed by spec, plan and code.

### 2. Changing `specs/`

One file per feature, `specs/NNN-nombre.md`, `NNN` sequential. Two features = two files.

Required contents: **objective**; **scope** / **out of scope**; **observable behaviour** as concrete cases (input → expected output, including rejections and boundaries); **invariants**, each with its T/A/I/D/U class; **docs referenced**.

- Behaviour only: no file names, signatures or libraries.
- Never contradicts `docs/*.md` — change the doc first (process 1).
- Dependent specs reference each other by name; they never duplicate cases.
- Written → open its `TODO.md` block with both boxes unmarked and **stop**.
- Changing one: grill again, edit the cases, unmark **both** boxes, re-run processes 3 and 4 for what changed. A deleted case means a deleted test.

### 3. The plan — `TODO.md`

Single file at the repo root, one block per spec, newest last. One step per acceptance case, in implementation order. A step names the behaviour it delivers, not the files it touches — if it can't be phrased as a case of the spec, it belongs in the spec first. Written → **stop**. Mark a step `[x]` only when its case goes green, never ahead. If implementation proves the plan wrong, stop and change the plan with the user; never improvise a step.

    ## NNN — <feature name>

    - [ ] Spec `specs/NNN-nombre.md` approved   <- only the user marks this
    - [ ] Plan below approved                   <- only the user marks this

    ### Steps
    - [ ] <case 1, as named in the spec>
    - [ ] <case 2, as named in the spec>

    ### Closing
    - [ ] Full suite green, type checks clean
    - [ ] Spec updated, or confirmed still true
    - [ ] Docs updated, or confirmed still true

### 4. Changing code — TDD

Per step of the approved plan: write the test → run it and watch it fail **for the right reason** → minimum code to pass, no speculative generality → run the **full** suite → refactor green (tests unchanged) → mark the step `[x]`.

- A bug gets a failing test reproducing it before the fix; that test stays.
- Only **class T** becomes a test. **A** → strict typing + static analysis, **I** → review, **D** → demonstration run, **U** → `verification.md` §6.
- Test names state the behaviour, not the function.
- Backend via `uv`, frontend via `pnpm`. Never disable, skip or weaken a test for a green run.

**Closing a feature** (all four, in order): full suite green and types clean → fix the spec if the code proved it wrong → fix the owning doc if the work contradicted `docs/*.md`, or state nothing changed → mark the three closing boxes.
