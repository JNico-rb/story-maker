# AGENTS.md — Instructions

**Work only on the V2 branch. Ignore all other branches** — the project restarted from scratch; nothing before is a valid reference.

## Stack

- **Backend:** Python 3.12+, uv, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite with `sqlite-vec` and FTS5. Lint: Ruff.
- **Frontend:** Vite, React, TypeScript strict, Tailwind, pnpm. Lint: ESLint + production build.
- Full flow is also verified with live evaluators and a manual browser walkthrough.

## Reference docs — `docs/*.md` is the source of truth

Load only the one the task needs. One concern per doc; cross-reference, never duplicate.

- [definitions.md](docs/definitions.md) — entities, attributes, class models. **Naming authority: never invent a synonym for a term defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — why the genre works this way. For prompts, rubrics, trope scoring, novum logic.
- [architecture.md](docs/architecture.md) — pipeline, context and memory, quality gates, config, the agents, API. §17 open decisions, §18 closed.
- [verification.md](docs/verification.md) — T/A/I/D/U classes (§2), coverage table (§5), accepted risks (§6). For tests, evals, CI, guardrails.

[specs/](specs/) sits at the repo root, next to `docs/`, and is **not** one of these reference docs: it is layer 2 of the workflow, one file per feature. `docs/*.md` states domain truth and design rationale; `specs/000-scaffolding.md` (cross-cutting), `specs/backend/NNN-nombre.md` and `specs/frontend/NNN-nombre.md` state a feature’s observable behaviour.

Entity names and diagram identifiers: no accents, no spaces (Mermaid). Quality gates judge the novel at runtime; `verification.md` covers the system in CI.

When touching `backend/` or `frontend/`, read `backend/AGENTS.md` and `frontend/AGENTS.md` too: it overrides this file on its own specifics, never on the gates or the layer order.

## Workflow — five layers, always in this order

`docs/*.md` → `specs/` → `TODO.md` (plan) → tests → code. Never skip upward: code no plan asks for, a plan no approved spec asks for, or a spec no doc supports, is drift.

**No code is written before its spec and its plan are approved — scaffolding, tooling, CI and dev hooks included** (they belong to `specs/000-scaffolding.md`). If code slips through, it is not deleted: its spec is written after the fact, audited and approved, and the existing code is verified against it like any other step. That spec is written from the docs, never from the code: the code is fixed to match the spec, never the spec bent to fit the code.

### Gates

| To do | Required first | Box marked by |
|---|---|---|
| Change `docs/*.md` | Self-review round on the task (process 0) | — |
| Write or change a spec | Supporting docs + a self-review round **on that spec** | — |
| Write the plan | That spec's approval box `[x]` | `auditor`, at gap zero |
| Write tests or code | That plan's approval box `[x]` + a failing test | `auditor`, at gap zero |
| Close a feature | Full suite green, types clean | `verificador` |

**Approvals are delegated to agents; the one who writes a thing never approves it.** `auditor` marks a spec or plan box only at gap zero and ends that same line with its record: `— auditor YYYY-MM-DD: <one line>`. `verificador` marks the three closing boxes. No other agent or session marks a box. Box unmarked → **stop**: run the auditor, never work around it. Three audit rounds without gap zero → escalate to the user with the remaining gaps.

The user steps in only on escalations and on human-only tasks: the human review of a novel, the demo video, accounts and tokens, the final check.

### 0. Self-review

Run before the first edit to `docs/*.md`, `specs/`, `TODO.md`, `backend/` or `frontend/`. Once per task, not per file — but **every spec gets its own round**, even mid-task. The writer lists its open questions about the task, not the diff: what is asked, which layer owns it, which `definitions.md` terms it uses, which acceptance cases it implies, what is out of scope. It answers each from the docs and the simplicity maxim — *as easy as possible, as hard as necessary* — and records every design decision it closes in `architecture.md` §18. Only questions that truly belong to the user (money, external accounts, scope of the assignment) go to the user, in one batch. Do not edit while questions are open. Trivial non-semantic edits (typos, formatting, links) are exempt.

### 1. Changing the reference docs (`docs/*.md`)

Source of truth about domain and design, never a description of today's code.

1. Pick the **single owning doc**.
2. New or renamed terms go to `definitions.md` first and nowhere else.
3. Closing a decision = moving it from `architecture.md` §17 to §18 with its reason. Reopening a §18 decision needs a stated reason in the same commit.
4. A new verification method goes to `verification.md` + its row in §5; an accepted risk goes to §6 with name and motive.
5. Before finishing, name every spec, plan block and piece of code the change now contradicts — fix or list them.

A doc change alone changes no behaviour; it must be followed by spec, plan and code.

### 2. Changing `specs/`

One file per feature: `specs/backend/NNN-nombre.md` or `specs/frontend/NNN-nombre.md`; the one cross-cutting spec, `specs/000-scaffolding.md`, sits at the root of `specs/`. `NNN` is global and sequential across both folders (backend 001–021, frontend from 022). Two features = two files.

Required contents: **objective**; **scope** / **out of scope**; **observable behaviour** as concrete, named cases (input → expected output, including rejections and boundaries); **invariants**, each with its T/A/I/D/U class; **docs referenced**.

- Behaviour only: no file names, signatures or libraries. The one exception is `specs/000-scaffolding.md`: its observable behaviour is the commands a developer runs and what they produce, so it names commands, paths and tools.
- Never contradicts `docs/*.md` — change the doc first (process 1).
- Dependent specs reference each other by name; they never duplicate cases.
- Specs are drafted in parallel, one `redactor-specs` per spec. Writers never edit `TODO.md`: the integrator (main checkout, V2) adds each block, one at a time, with every box unmarked, and then runs `auditor` until gap zero.
- One commit per approved spec (`NNN: spec aprobada`) and one per approved plan (`NNN: plan aprobado`), both by the integrator.
- Changing one: self-review again, edit the cases, unmark **both** boxes, re-audit, re-run processes 3 and 4 for what changed. A deleted case means a deleted test.

### 3. The plan — `TODO.md`

Single file at the repo root: a header with the lane table (owned by the integrator), then one block per spec in numeric order. One step per acceptance case and one per class-T invariant, in implementation order. A step names the behaviour it delivers, not the files it touches — if it can't be phrased as a case of the spec, it belongs in the spec first. The writer may draft the plan outside `TODO.md`; the integrator pastes it into the block. Written → run `auditor` on it. Mark a step `[x]` only when its case goes green, never ahead. If implementation proves the plan wrong, stop, change the plan and get it re-audited; never improvise a step.

    ## NNN — <feature name>

    - [ ] Spec `specs/<side>/NNN-nombre.md` approved               <- auditor, at gap zero, with its record
    - [ ] Plan below approved                                      <- auditor, at gap zero, with its record

    ### Steps
    - [ ] <case 1, as named in the spec>
    - [ ] <case 2, as named in the spec>

    ### Closing                                                    <- verificador
    - [ ] Full suite green, type checks clean
    - [ ] Spec updated, or confirmed still true
    - [ ] Docs updated, or confirmed still true

A marked box reads, for example: `- [x] Plan below approved — auditor 2026-09-24: 9 steps, one per case, gap zero`.

### 4. Changing code — TDD

Per step of the approved plan: write the test → run it and watch it fail **for the right reason** → minimum code to pass, no speculative generality → run the **full** suite → refactor green (tests unchanged) → mark the step `[x]`.

- A bug gets a failing test reproducing it before the fix; that test stays.
- Only **class T** becomes a test. **A** → strict typing + static analysis, **I** → review, **D** → demonstration run, **U** → `verification.md` §6.
- Test names state the behaviour, not the function.
- Backend via `uv`, frontend via `pnpm` (`pnpm.cmd` on this machine). Never disable, skip or weaken a test for a green run.

**Closing a feature** (all four, in order): full suite green and types clean → fix the spec if the code proved it wrong (and get it re-audited) → fix the owning doc if the work contradicted `docs/*.md`, or state nothing changed → `verificador` marks the three closing boxes.

## Parallel lanes

- A lane is a sibling worktree `../sm-<x>` on branch `carril-<x>`, created from V2 with `git worktree add ../sm-<x> -b carril-<x> V2`. Paths stay short: long paths are disabled on this machine.
- The lane table in `TODO.md` gives each lane its specs in order and their dependencies. Spec 000 comes first and blocks every lane; the integrator delivers it on V2. A spec starts when every dependency is closed in V2, or in the lane's own branch when it is the same lane's.
- A lane touches only the modules its specs own (ownership tables in `backend/AGENTS.md` and `frontend/AGENTS.md`). A change another lane's module needs goes to the integrator.
- `git rebase V2` before starting each spec.
- In `TODO.md` a lane edits only the blocks of its own specs; the header and the lane table belong to the integrator. Editing only your own blocks is what keeps `TODO.md` free of merge conflicts.
- Integration happens only in the main checkout on V2: `git merge --no-ff` of the lane's closing commit, then the full suite. Red → undo the merge and tell the lane.
- `docs/`, `.claude/`, `CLAUDE.md` and `README.md` have one writer, the integrator on V2; a lane sends it what they need.

## Code style (universal)

- **Small, obvious functions.** A 15-line function with clear names beats a three-class abstraction.
- **No premature abstraction.** Three similar lines is better than a badly-named base class. Extract when there's a third caller, not a hypothetical one.
- **No error handling for cases that can't happen.** Trust internal callers and framework guarantees. Validate only at boundaries: HTTP input, external APIs, DB writes, untrusted parsing.
- **No backwards-compat shims** unless explicitly asked for.
- **No feature flags** added speculatively.
- **Comments:** explain *why* when non-obvious, never *what*. Remove stale TODOs.
- **Keep files focused.** Prefer small modules.
