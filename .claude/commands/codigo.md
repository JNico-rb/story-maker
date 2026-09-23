---
description: Lane work on an approved plan — TDD in the lane's worktree, reporting to the orchestrator.
argument-hint: <spec NNN> <lane>
---

# Lane work: spec $1, lane $2

You are one lane of a parallel delivery. The orchestrator is the Claude Code session `story-maker-9b`. It is the single writer of `docs/`, `workflow/`, `.claude/`, `CLAUDE.md` and `README.md`, and the only session that merges into V2-test.

1. Read `CLAUDE.md` and, in `specs/$1-*/`, `spec.md`, `design.md` (§1, ownership, and every contract your lane touches) and `plan.md` (your lane's section, with its branch name). Done when you can name each of your steps, the paths you own and the contracts you consume from other lanes.
2. Create the worktree — `git worktree add -b <branch> .claude/worktrees/<branch> V2-test` — or, if it exists, rebase it on V2-test. Enter it with EnterWorktree and work only there.
3. For each step of your lane, in plan order, run the `tdd` skill loop: red for the right reason, green, full suite, refactor. Each test carries its requirement ID: `@pytest.mark.rf("RF-…")` in Python, the ID at the start of the test name in Vitest. Then commit with the ID in the message and mark the step `[x]`.
   - Your paths are the ones design §1 gives your lane. A change to a shared file or a contract goes to the orchestrator by SendMessage; meanwhile, continue with the next step that does not need it.
   - Split independent modules of a step across subagents when that is faster; you integrate and run the suite.
4. At each milestone of `plan.md`, and at least every two hours:
   1. Rebase on V2-test and get the full suite green.
   2. Send `story-maker-9b` a message with the steps done, the head commit, what you need from other lanes, and every finding for the process records: a TLC or Lean counterexample, an eval result, a browser MCP inspection, a subagent's result.
5. A denial from the `guard` hook is the gate working: report it to the orchestrator and go on with work the gate allows.

Done when every step of your lane is `[x]`, the full suite and its linters and type checks are green in this conversation's output, the worktree has nothing uncommitted, and `story-maker-9b` has your closing summary. If a missing secret or a decision only the user can make blocks you, notify the user with PushNotification and stop.
