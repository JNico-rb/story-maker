# AGENTS.md — Instructions

**Ignore the contents of the other branches entirely.** The project was restarted from scratch, so nothing from before is valid as a reference.

All work must be done on the V2 branch.

## Stack

- **Backend:** Python 3.12+, uv, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite.
- **Frontend:** Frontend: Vite, React, TypeScript strict, Tailwind CSS, pnpm.
- Verification: Ruff for backend; TypeScript, ESLint, production build, explicit live evaluators, and a manual browser walkthrough for the complete flow.
- VAT checks: local EU structure/checksum validation with `python-stdnum`; no live VIES claim.

## Reference docs

`docs/` is the source of truth. Load only the one the task needs.

- [definitions.md](docs/definitions.md) — entities, attributes, class models. **Naming authority: never invent a synonym for a term defined here.**
- [domain-knowledge.md](docs/domain-knowledge.md) — why the genre works this way. Read it for prompts, rubrics, trope scoring, novum logic.
- [architecture.md](docs/architecture.md) — pipeline, quality gates, config, the five agents, API. §10 = open decisions, §11 = closed, do not reopen without a stated reason.
- [verification.md](docs/verification.md) — how to verify the system: methods classified T/A/I/D/U, coverage table (§5), accepted risks (§6). Read it for tests, evals, CI or guardrails.

Rules: one concern per doc, cross-reference instead of duplicating. Entity names and diagram identifiers go without accents or spaces (Mermaid). Quality gates judge the novel at runtime; `verification.md` covers the system in CI.

## Workflows

Four layers, changed in this order: `docs/` (why and what) -> `specs/` (the contract of one feature) -> tests -> code. Never skip upward: code that no spec asks for, or a spec that no doc supports, is drift. Decide which of the three processes below the task belongs to before touching a file.

This is spec-driven development: a task may create one spec, several specs, or modify existing ones alongside the docs and the code they govern. Whatever the shape, the order of the layers holds.

### 0. Grill before writing — mandatory gate

Before the first edit to anything in `docs/`, `specs/`, `backend/` or `frontend/`, run the `mattpocock-skills:grilling` skill **interactively** on the task. Its purpose here is to expose misunderstandings of the request before they become files.

- Run it once per task, not once per file. A task that will touch docs, specs and code is grilled once, up front.
- Grill the **task**, not the diff: what is being asked, which layer owns it, which terms in `definitions.md` it uses, which acceptance cases it implies, what is out of scope.
- Do not start editing while questions are still open. Answer them with the user, then write.
- The gate ends when the user and the agent agree on the same understanding. Carry that agreement into the spec's case list.
- Trivial, non-semantic edits (typos, formatting, broken links) do not need the gate.

### 1. Changing `docs/`

`docs/` is the source of truth about the domain and the design, never a description of how today's code happens to be written.

1. Pick the **single owning doc** — definitions / domain-knowledge / architecture / verification. One concern per doc; cross-reference, never duplicate.
2. New or renamed terms go to `definitions.md` **first**, and nowhere else. No synonyms for an existing term.
3. Design decisions: `architecture.md` §10 is open, §11 is closed. Closing a decision means moving it from §10 to §11 with its reason. Reopening a §11 decision requires a stated reason in the same commit.
4. A new or changed verification method goes to `verification.md`, and the coverage table (§5) is updated with it; an accepted risk goes to §6 with a name and a motive.
5. Before finishing, name every spec and every piece of code the change now contradicts. Fix them or list them explicitly — silent drift is not acceptable.

A doc change alone changes no behaviour. It must be followed by a spec change and a code change.

### 2. Changing `specs/`

A spec is the layer between prose and tests: what one feature must observably do, concrete enough that its acceptance cases can be transcribed into tests almost literally.

- One file per feature, `specs/NNN-nombre.md`, `NNN` sequential.
- A task may add or change **several** specs at once. One feature per file still holds: if the work covers two features, it is two files, never one file with two objectives. Split by feature, not by convenience.
- Required contents: **objective**; **scope** and **out of scope**; **observable behaviour** as concrete cases (input -> expected output, including rejection and boundary cases); **invariants**, each labelled with its Trust Spec class (T/A/I/D/U, `verification.md` §2); **docs referenced**.
- A spec never contradicts `docs/`. If it needs to, change the doc first (process 1) and then write the spec.
- Specs that depend on each other say so by name; they never duplicate each other's cases.
- A spec describes behaviour, not implementation: no file names, no function signatures, no libraries.
- The spec is agreed **before** code is written. Once code exists, the spec is kept in sync with it — a spec that lies is worse than no spec.
- Changing an existing spec: edit the case list, then re-run process 3 for the cases that changed. A deleted case means a deleted test.

### 3. Changing code (`backend/`, `frontend/`) — TDD

Work case by case from the spec, in a red-green-refactor cycle:

1. Take **one** acceptance case from the spec.
2. Write the test **before** the code. Run it and watch it fail, for the reason it is supposed to fail — a test that has never failed proves nothing.
3. Write the **minimum** code that makes it pass. No speculative generality.
4. Run the full suite, not just the new test.
5. Refactor with the suite green. Tests do not change during a refactor.
6. Repeat until every case of the spec is covered.

Rules:

- No production code without a failing test that demands it.
- A bug is reproduced by a failing test before it is fixed; that test stays in the suite.
- Not everything becomes a test: only **class T** requirements do. **A** -> strict typing and static analysis, **I** -> review, **D** -> a demonstration run, **U** -> written down in `verification.md` §6. Verify each thing with the method `verification.md` assigns to it.
- Test names state the behaviour, not the function under test.
- Backend runs through `uv`, frontend through `pnpm`. Never disable, skip or weaken a test to get a green run.
- Done means: full suite green, type checks clean, and the spec updated if the work proved the spec wrong.

## Verification policy

- Keep verification proportional and demo-oriented: verify locked installs on the starter; as code is added, lint the backend, type-check/lint/build the frontend, exercise the fictional corpus evaluators when cloud usage is intended, and manually walk through the user story in the browser.
- Keep deterministic business rules and provider boundaries explicit and easy to inspect even though they are not backed by a committed unit-test suite.

# Constraints

- 100k tokens is the maximum context window.
