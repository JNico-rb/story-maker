# Process 4 — Changing code (TDD)

Per step of the approved `plan.md`: write the test → run it and watch it fail **for the right reason** → minimum code to pass, no speculative generality → run the **full** suite → refactor green (tests unchanged) → mark the step `[x]`.

- A bug gets a failing test reproducing it before the fix; that test stays.
- Only **class T** becomes a test. **A** → strict typing + static analysis, **I** → review, **D** → demonstration run, **U** → `verification.md` §6.
- Test names state the behaviour, not the function.
- A red test goes green through code. Never disable, skip or weaken a test for a green run.

## Closing a feature

Work through the Closing boxes of its `plan.md`, in order:

1. Full suite green and types clean.
2. Spec: fix it where the code proved it wrong, or confirm it still holds.
3. Docs: fix the owning reference doc where the work contradicted it, or state nothing changed.
4. Process records: add the rows the work produced, all in `verification.md`.
   - An eval, or a TLC or Lean counterexample, that changed code, a prompt or a threshold → the iteration log, §8, with cause and effect.
   - An adversarial case run → its row in the cases table of §4.9.
   - A browser MCP inspection, or a subagent or slash command that produced a result → §9.
   - Eval results → the end of §4.2.
5. Explainer: a course concept this feature applies for the first time gets its short explainer at the head of the section the root `README.md` lists for it.
