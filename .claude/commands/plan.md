---
description: Write the plan of an approved spec — ordered requirement IDs, lanes when parallel, stop at its approval box.
argument-hint: <spec NNN>
---

# Plan of spec $ARGUMENTS

1. Check that `specs/$ARGUMENTS-*/spec.md` has its approval box marked in V2-test; unmarked → stop and tell the user.
2. Write `plan.md` by [workflow/3-plan.md](../../workflow/3-plan.md). With parallel lanes, give each lane a section with its branch name, the paths it owns (from `design.md` §1) and its milestones.
3. Check coverage: every RF and RNF of the spec appears in exactly one step, with the spec's class. Done when a scan of both files finds no ID missing or repeated.
4. Write the approval digest: at most 10 lines, covering the order, the lanes and anything the plan could not place.

Done when the coverage check passes, the box is unmarked, and the digest is in your final message.
