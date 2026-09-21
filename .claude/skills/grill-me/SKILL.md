---
name: grill-me
description: Grill the user relentlessly about a plan, decision, or idea, asking every round as interactive multiple choice. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Put the whole frontier to the user as one `AskUserQuestion` call, and wait for their answers before the next round.

## Every round is one AskUserQuestion call

Every question you put to the user goes through the `AskUserQuestion` tool, whether it is a full round or one loose end you noticed mid-thought. The tool halts the turn until the user picks, and that halt is the point: your recommendation travels as an option to choose, never as a decision already taken.

Each question in the round:

- `header`: a label of at most 12 characters.
- `question`: the question in full, ending in a question mark.
- Options: 2 to 4 real, mutually exclusive answers. The one you recommend goes first and its `label` ends in `(Recommended)`. Its `description` says what choosing it commits to and what it gives up, rather than restating the label.
- `preview`: include one when the options land better seen than described, such as two output shapes, two file skeletons, a before and after. Single-select questions only.
- `multiSelect: true` when the options do not exclude each other.
- The tool adds the "Other" option itself, so leave it out.

If you cannot name 2 to 4 plausible answers, you have not thought the question through yet. Arrive with hypotheses, not with a blank. "Other" catches what you failed to foresee; it is not a licence to skip the thinking.

A round carries at most 4 questions, so a wider frontier is asked across consecutive rounds, most consequential first.

Call the tool with no preamble. When the answers come back, state in one line what is now settled, then open the next round.

## Between rounds

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

## Done

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. If the frontier looks empty after one round, you have not walked the failure branches yet: what gets rejected, what happens at the boundaries, what is explicitly out of scope.

Then write the shared understanding out, decision by decision, and close with one last `AskUserQuestion` offering to confirm it, to revisit a decision, or to keep grilling. Do not act on the plan until that confirmation arrives.
