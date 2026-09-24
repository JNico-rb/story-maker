# AGENTS.md — Instructions

**V2 only.** Restarted from scratch; nothing earlier is a valid reference.

## Stack

- **Backend:** Python 3.12+, FastAPI, SQLAlchemy 2, SQLite (`sqlite-vec`, FTS5).
- **Frontend:** Vite, React, TypeScript strict, Tailwind.
- Full flow is also verified with live evaluators and a manual browser walkthrough.

## Reference docs — `docs/*.md` is the source of truth

Load only the doc the task needs; one concern per doc, cross-referenced, never duplicated.

- [definitions.md](docs/definitions.md) — entities, attributes, class models. **Naming authority: never invent a synonym for a term defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — genre rationale: prompts, rubrics, trope scoring, novum logic.
- [architecture.md](docs/architecture.md) — pipeline, context and memory, quality gates, config, agents, API. §17 open decisions, §18 closed.
- [verification.md](docs/verification.md) — T/A/I/D/U classes (§2), coverage table (§5), accepted risks (§6): tests, evals, CI, guardrails.

`specs/` (repo root) is layer 2 below: behaviour, not domain truth. No accents/spaces in entity or diagram names (Mermaid). Quality gates judge the novel at runtime; `verification.md` covers the system in CI.

Touching `backend/` or `frontend/`: read its `AGENTS.md` too — overrides this file on specifics, never on gates or layer order.

## Workflow — five layers, always in this order

`docs/*.md` → `specs/` → `TODO.md` (plan) → tests → code, never skipped upward: code with no plan, a plan with no approved spec, or a spec with no doc behind it, is drift.

**No code before its spec and plan are approved** — scaffolding, tooling, CI, dev hooks included (`specs/000-scaffolding.md`'s territory). Code that slips through stays: write its spec from the docs after the fact, get it approved, verify the code against it like any step — code bends to the spec, never the reverse.

### Gates

| To do | Required first | Box marked by |
|---|---|---|
| Change `docs/*.md` | — | — |
| Write or change a spec | Supporting docs | — |
| Write the plan | Spec's approval box `[x]` | integrator, no review |
| Write tests or code | Plan's approval box `[x]` + a failing test | integrator, no review |
| Close a feature | C cases + kept I invariants green (D, «(recortado)» excepted); full suite green; types clean | `verificador` |

Three user decisions (2026-09-24) still govern closing:

- **No reviews.** No self-review, auditor, or review round, ever. Integrator writes spec + plan from `docs/*.md`, marks both boxes: `— integrador YYYY-MM-DD: sin revisión, decisión del usuario`. TDD still applies; closing is `verificador`'s job (Gates row above). Plan box unmarked → **stop**: no tests, no code (`guard-plan` checks only that box).
- **Class D waits until the end.** No demo or real-model run before the backend closes. A spec closes once every non-D step is `[x]` and the suite is green — D steps stay `[ ]`, tagged `(D, al final)`, batched at the end: backend first, frontend after.
- **Scope cut (overrides class D above).** A spec closes on its C cases plus the I invariants mapped to TLA+ (`ReanudacionSinDuplicarNiPerder`, `ReintentosAcotados`, `VersionAnteriorConservada`, atomicity) or protecting a validator; every other I invariant is tagged `(recortado)`, stays `[ ]`, doesn't block the close — same for any `(recortado)`-tagged spec or step. Out-of-scope and deferred specs: `TODO.md` → *Estado* → *Alcance*.

Escalations only: a persistent `verificador` FAIL, or a human-only task — novel review, demo video, accounts/tokens, final check.

### 1. Changing the reference docs

1. New or renamed terms go to `definitions.md` first, nowhere else.
2. Closing a decision moves it `architecture.md` §17→§18 with its reason; reopening one needs a reason in the same commit.
3. A new verification method goes to `verification.md` + its §5 row; an accepted risk goes to §6 with name and motive.
4. Before finishing, name every spec, plan block and piece of code the change now contradicts, and fix or list them.

### 2. Changing `specs/`

One file per feature: `specs/backend/NNN-nombre.md` or `specs/frontend/NNN-nombre.md`, plus cross-cutting `specs/000-scaffolding.md` at the root. `NNN` global: backend 001–021, frontend from 022.

Required: **objective**; **scope**/**out of scope**; **observable behaviour** as named cases (input → expected output, rejections, boundaries); **invariants** with T/A/I/D/U class; **docs referenced**.

- Behaviour only, no file names, signatures or libraries — except `specs/000-scaffolding.md`, whose behaviour is the commands a developer runs.
- Never contradicts `docs/*.md` (process 1); dependent specs reference each other by name, never duplicating cases.
- An incomplete spec is completed only as far as its plan needs; a design decision closed this way goes to `architecture.md` §18.
- One commit per approved spec (`NNN: spec aprobada`) and plan (`NNN: plan aprobado`), both by the integrator.
- Changing a spec: edit the cases, unmark **both** boxes, re-mark, redo processes 3–4 for what changed — a deleted case means a deleted test.

### 3. The plan — `TODO.md`

Header (lane table, integrator's), then one numbered block per spec — added by the integrator, boxes unmarked — in the format its blocks already use: spec approved, plan approved, steps, closing. One step per acceptance case and class-T invariant, in implementation order, named by behaviour delivered, not files touched — unphraseable as a spec case, it belongs in the spec first. A plan may be drafted outside `TODO.md`; the integrator pastes it in and marks the box. Mark `[x]` only when the case goes green, never ahead — a plan proven wrong stops the work: fix it, integrator re-marks, don't improvise a step.

### 4. Changing code — TDD

Per step: write the test → watch it fail **for the right reason** → minimum code to pass, no speculative generality → run the **full** suite → refactor green (tests unchanged) → mark `[x]`.

- A bug gets a failing test reproducing it first; that test stays.
- Only **class T** becomes a test: **A** → strict typing + static analysis, **I** → review, **D** → demonstration run, **U** → `verification.md` §6.
- Test names state the behaviour, not the function.
- `uv` for backend, `pnpm` (`pnpm.cmd` on this machine) for frontend. Keep every test enabled and at full strength, even for a green run.

**Closing a feature**: every non-D, non-`(recortado)` step `[x]`, full suite green, types clean → fix the spec if the code proved it wrong (integrator re-marks) → fix the owning doc if contradicted, or confirm nothing changed → `verificador` marks the three closing boxes.

## Parallel lanes

- A lane is a sibling worktree `../sm-<x>` on branch `carril-<x>`, from V2: `git worktree add ../sm-<x> -b carril-<x> V2`.
- The lane table in `TODO.md` orders each lane's specs and dependencies. Spec 000, delivered by the integrator on V2, blocks every lane. A spec starts once its dependencies close in V2, or in its own lane when the dependency is the same lane's.
- A lane touches only the modules its specs own (ownership tables in `backend/AGENTS.md`, `frontend/AGENTS.md`); a change to another lane's module goes to the integrator. `git rebase V2` before each spec.
- In `TODO.md` a lane edits only its own specs' blocks; header and lane table are the integrator's — keeps `TODO.md` conflict-free.
- Integration only in the main checkout on V2: `git merge --no-ff` the lane's closing commit, then the full suite. Red → undo the merge, tell the lane.
- `docs/`, `.claude/`, `CLAUDE.md`, `README.md`: one writer, the integrator on V2; a lane sends it what it needs.

## Code style (universal)

- **Small, obvious functions.** A 15-line function with clear names beats a three-class abstraction.
- **No premature abstraction, shims or speculative flags.** Three similar lines beats a badly-named base class; extract at a third caller, not a hypothetical one. Shims and flags only when explicitly asked for.
- **Error handling at boundaries.** Trust internal callers and framework guarantees; validate HTTP input, external APIs, DB writes, untrusted parsing.
- **Comments explain *why*** when non-obvious, never *what*. Remove stale TODOs.
- **Keep files focused.** Prefer small modules.
