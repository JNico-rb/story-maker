# Process 3 — The plan (`plan.md`)

One `plan.md` per spec, in the spec's folder. One step per requirement, in implementation order, citing the ID it delivers and, when it is not T, its class: `(RF-CFG-2 · clase A)`. A step names the behaviour it delivers, not the files it touches — if it can't be phrased as a requirement of the spec, it belongs in the spec first. The one exception: a demonstration that `verification.md` §5 assigns to the spec is a step of its own, citing that row. Written → run the gap loop below.

No step invents a figure: the ones in `architecture.md` §15.2 are read from config and fail actionably if missing.

Mark a step `[x]` only when its case goes green. If implementation proves the plan wrong, stop and change the plan with the user; every step comes from the plan.

    # NNN — <MÓD> · Plan

    - [ ] Plan approved   <- only the user marks this

    Spec: [spec.md](spec.md). Verificación: <método> (`docs/verification.md` §5).

    ### Steps
    - [ ] <requirement, as stated in the spec> (<ID> · clase <X>)

    ### Closing
    - [ ] Full suite green, type checks clean
    - [ ] Spec updated, or confirmed still true
    - [ ] Docs updated, or confirmed still true
    - [ ] Process records and explainers added, or none produced

## Gap loop — before asking for approval

The plan, with its spec, answers to `docs/architecture.md`; `docs/relational-matrix.md` records the gap between them. The loop runs under a `/goal`, in a chat of its own:

1. Dispatch the `auditor` subagent on the spec folder.
2. Add each difference it reports to the spec's section of the matrix, open, with the gravedad the auditor gave it.
3. Close each blocking one: fix the plan; fix the doc through [process 1](1-docs.md), grill included; or point it to the spec that covers it in the matrix's §1. A minor one is closed the same way or left `aceptada`.
4. Repeat from 1 until a pass on the final version reports no blocking difference: that is **gap zero**. Mark the spec's §1 rows reviewed. Three passes at most: if blocking differences remain after the third, notify the user with `PushNotification` and **stop**.
5. Hand off: write the code chat's line to `.scratch/v1/prompts/NNN-codigo.md`, show it in the final message, notify the user with `PushNotification`, and **stop**. The user marks the plan's box, commits on `V2-test` —the code chat branches from its last commit— and opens that chat.

The code chat's line, on one line because `/goal` takes one:

    /goal Implement specs/NNN-slug/plan.md following CLAUDE.md and workflow/4-code.md, with the mattpocock-skills:tdd skill. First check, in the last commit of V2-test, that plan.md's approval box is marked and that section NNN-slug of docs/relational-matrix.md has no open blocking difference; if either fails, stop and tell me. Then run `git worktree add -b v2-test-NNN .claude/worktrees/NNN V2-test`, enter that worktree with EnterWorktree and work only there, committing each step as it goes green. Done when every step and Closing box of plan.md is marked, the full suite, Ruff and mypy are green in this conversation's output, the worktree has nothing uncommitted, and you have notified me with PushNotification.
