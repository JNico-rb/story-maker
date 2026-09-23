# Process 3 — The plan (`plan.md`)

One `plan.md` per spec, in the spec's folder. It has one step per requirement, in implementation order. Each step gives the requirement's ID, its class when it is not T, and a label of a few words: `- [ ] RF-CFG-2 · clase A — config rejected at startup`. The requirement's text lives only in `spec.md`. A step that no requirement of the spec names belongs in the spec first. The one exception: a demonstration that `verification.md` §5 assigns to the spec is a step of its own, citing that row.

With parallel lanes, the plan has one section per lane. Each section gives:

- its branch, `v2-test-NNN-<lane>`;
- the paths it owns, from `design.md` §1;
- its steps;
- its milestones: the points where it rebases on V2-test and reports.

No step invents a figure: the ones in `architecture.md` §15.2 are read from config and fail actionably if missing.

Mark a step `[x]` only when its case goes green. If implementation proves the plan wrong, stop and change the plan with the user; every step comes from the plan.

    # NNN — <MÓD> · Plan

    - [ ] Plan approved   <- only the user marks this

    Spec: [spec.md](spec.md). Verificación: <método> (`docs/verification.md` §5).

    ### Steps
    - [ ] <ID> · clase <X> — <label>

    ### Closing
    - [ ] Full suite green, type checks clean
    - [ ] Spec updated, or confirmed still true
    - [ ] Docs updated, or confirmed still true
    - [ ] Process records and explainers added, or none produced

Written → check that every RF and RNF of the spec appears in exactly one step with the spec's class. Write a digest of at most 10 lines, leave the box unmarked and **stop**. The user marks it and commits on V2-test, and every code chat branches from that commit.

## Code chats

A code chat, or each lane of a parallel plan, works from [.claude/commands/codigo.md](../.claude/commands/codigo.md). `/goal` cannot run a command, so the orchestrator hands the user a `/goal` line that points to it:

    /goal Follow .claude/commands/codigo.md with spec NNN and lane <lane>. Done when every step of your lane is [x], the full suite and its checks are green in this conversation's output, the worktree has nothing uncommitted, and story-maker-9b has your closing summary.

The `guard` hook (`scripts/dev/guard.mjs`) holds the gate. It lets a code chat edit `backend/` or `frontend/` only when:

- the spec and the plan are approved in V2-test;
- the spec's section of `docs/relational-matrix.md` has no open blocking difference.
