# AGENTS.md — Instructions

**Ignore the contents of the other branches entirely.** The project was restarted from scratch, so nothing from before is valid as a reference.

**All work must be done on the V2 branch.**
## Stack

- **Backend:** Python 3.12+, uv, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite.
- **Frontend:** Vite, React, TypeScript strict, Tailwind CSS, pnpm.
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

Five layers, changed in this order: `docs/` (why and what) -> `specs/` (the contract of one feature) -> `TODO.md` (the implementation plan) -> tests -> code. Never skip upward: code that no plan asks for, a plan that no approved spec asks for, or a spec that no doc supports, is drift. Decide which of the four processes below the task belongs to before touching a file.

This is spec-driven development: a task may create one spec, several specs, or modify existing ones alongside the docs, the plan and the code they govern. Whatever the shape, the order of the layers holds.

### Gates — what blocks what

| To do this | You need first | Hard stop |
|---|---|---|
| Change `docs/` | The grill gate of process 0 closed | — |
| Write or change a spec | Docs that support it, and a grill round **on that spec** | Do not write the spec while questions are open |
| Write the implementation plan | That spec's approval box in `TODO.md` marked `[x]` **by the user** | No plan without an approved spec |
| Write tests or production code | That plan's approval box in `TODO.md` marked `[x]` **by the user** | No code without an approved plan, and no production code without a failing test |

Only the user marks an approval box. An agent never marks one, never assumes one, and never treats "the user seemed to agree in the conversation" as approval. If a box is unmarked, the agent **stops and asks**.

### 0. Grill before writing — mandatory gate

Before the first edit to anything in `docs/`, `specs/`, `TODO.md`, `backend/` or `frontend/`, run the `grill-me` skill on the task. It asks in interactive rounds, and the gate is satisfied only by the user's own answers. Its purpose here is to expose misunderstandings of the request before they become files.

- Run it once per task, not once per file. A task that will touch docs, specs, the plan and code is grilled once, up front.
- **Exception — every spec gets its own grill round.** Creating a spec, or changing the case list of an existing one, always reopens the gate for that spec, even mid-task and even if the task was already grilled. Ask about its cases, its boundaries and its rejections until the user's answers leave nothing open.
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
5. Before finishing, name every spec, every plan block and every piece of code the change now contradicts. Fix them or list them explicitly — silent drift is not acceptable.

A doc change alone changes no behaviour. It must be followed by a spec change, a plan and a code change.

### 2. Changing `specs/`

A spec is the layer between prose and tests: what one feature must observably do, concrete enough that its acceptance cases can be transcribed into tests almost literally.

- One file per feature, `specs/NNN-nombre.md`, `NNN` sequential.
- A task may add or change **several** specs at once. One feature per file still holds: if the work covers two features, it is two files, never one file with two objectives. Split by feature, not by convenience.
- Required contents: **objective**; **scope** and **out of scope**; **observable behaviour** as concrete cases (input -> expected output, including rejection and boundary cases); **invariants**, each labelled with its Trust Spec class (T/A/I/D/U, `verification.md` §2); **docs referenced**.
- A spec never contradicts `docs/`. If it needs to, change the doc first (process 1) and then write the spec.
- Specs that depend on each other say so by name; they never duplicate each other's cases.
- A spec describes behaviour, not implementation: no file names, no function signatures, no libraries.
- When the spec is written, open its block in `TODO.md` with the two unmarked approval boxes and **stop**. The user reads the spec and marks the first box. Until then there is no plan and no code.
- Changing an existing spec: grill it again (process 0), edit the case list, then unmark both boxes of its `TODO.md` block so the user re-approves, and re-run processes 3 and 4 for the cases that changed. A deleted case means a deleted test.

### 3. The implementation plan — `TODO.md`

The plan is the layer between an approved spec and the first failing test: the ordered list of what will be built, in checkboxes the user can watch advance. It lives in a single file, `TODO.md` at the repo root, one block per feature, newest last.

- Write the plan **only** after the user has marked that spec's approval box `[x]`.
- One block per spec, headed by its `NNN` and the spec's name. The steps come from the spec's acceptance cases, one step per case, in the order they will be implemented.
- A step names the behaviour it delivers, not the files it touches. If a step cannot be phrased as a case of the spec, it does not belong in the plan — it belongs in the spec first.
- When the plan is written, **stop**. The user reads it and marks the plan's approval box. No test and no production code before that mark.
- While implementing, the agent marks each step `[x]` as its case goes green, and only then. Never mark ahead.
- If implementation proves the plan wrong, stop, say so, and change the plan with the user — never improvise a step that no approved plan contains.

The block format:

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

### 4. Changing code (`backend/`, `frontend/`) — TDD

Work case by case from the approved plan, in a red-green-refactor cycle:

1. Take **one** step from the plan in `TODO.md`, and with it the acceptance case of the spec it came from.
2. Write the test **before** the code. Run it and watch it fail, for the reason it is supposed to fail — a test that has never failed proves nothing.
3. Write the **minimum** code that makes it pass. No speculative generality.
4. Run the full suite, not just the new test.
5. Refactor with the suite green. Tests do not change during a refactor.
6. Mark the step `[x]` in `TODO.md`.
7. Repeat until every step of the plan is done.

Rules:

- No production code without an approved plan, and none without a failing test that demands it.
- A bug is reproduced by a failing test before it is fixed; that test stays in the suite.
- Not everything becomes a test: only **class T** requirements do. **A** -> strict typing and static analysis, **I** -> review, **D** -> a demonstration run, **U** -> written down in `verification.md` §6. Verify each thing with the method `verification.md` assigns to it.
- Test names state the behaviour, not the function under test.
- Backend runs through `uv`, frontend through `pnpm`. Never disable, skip or weaken a test to get a green run.

Closing a feature — the layers are updated back upwards, in this order, before the work is called done:

1. Full suite green and type checks clean.
2. **Spec:** if the code proved the spec wrong or incomplete, fix the spec now. A spec that lies is worse than no spec.
3. **Docs:** if the work contradicted `docs/`, fix the owning doc now (process 1), or state explicitly that nothing in `docs/` changed.
4. Mark the three closing boxes of the block in `TODO.md`.

Done means all four, not just the first.

# Constraints

- **100k tokens is the maximum context window of the agent for any agent.**
