---
description: Delivery status derived from the files — plan steps per lane, lane branches, gates.
argument-hint: <spec NNN>
---

# Status of spec $ARGUMENTS

Derive every figure from the repository, never from memory, so the board cannot drift:

1. Plan: in `specs/$ARGUMENTS-*/plan.md`, the steps marked `[x]` and the total, per lane section, read from V2-test and from each lane branch.
2. Branches: for each `v2-test-$ARGUMENTS-*`, the commits ahead of and behind V2-test, and the subject of its last commit.
3. Gates: the approval boxes of `spec.md` and `plan.md` in V2-test, and the open blocking rows of the spec's section in `docs/relational-matrix.md`.
4. Pending: what the lanes asked the orchestrator for and what is still unanswered.

Report one table of at most 15 lines, then the next action per lane.
