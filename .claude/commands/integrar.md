---
description: Orchestrator only — verify a lane branch and merge it into V2-test.
argument-hint: <branch>
---

# Integrate $ARGUMENTS into V2-test

1. Dispatch the `verificador` subagent on branch `$ARGUMENTS`. Done when it returns PASS or FAIL with its findings.
2. On FAIL, send the findings to the lane that owns the branch with SendMessage, and stop.
3. On PASS, in the main checkout on V2-test:
   1. Run `git merge --no-ff $ARGUMENTS`.
   2. Resolve each conflict by the ownership table of the spec's `design.md` §1: the owner's side wins, and a regenerated file (lock files, generated clients) is regenerated, never hand-merged.
   3. Run the full suite of each side the merge touched.
4. Push V2-test to origin, and message every active lane to rebase.
5. Append the process records the lane reported, in `docs/verification.md`: an eval result goes to §4.2, a red-team case to §4.9, a TLC, Lean or eval change to the iteration log (§8), a browser MCP inspection to §9.3, and a subagent or command result to §9.4.

Done when V2-test contains the branch, its suite is green in this conversation's output, origin has the push, and the lanes have been told to rebase.
