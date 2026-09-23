---
description: Write or change a spec — grill, write, audit to gap zero, stop at its approval box.
argument-hint: <spec NNN or new slug>
---

# Spec $ARGUMENTS

1. Grill the user on this spec with the `grill-me` skill: what is asked, which layer owns it, the `definitions.md` terms, the requirements it implies, what is out of scope. Done when every question has an answer.
2. Write or change `specs/$ARGUMENTS*/spec.md` by [workflow/2-specs.md](../../workflow/2-specs.md).
3. Run the gap loop of [workflow/2-specs.md](../../workflow/2-specs.md) with the `auditor` subagent until a pass on the final text reports no blocking difference.
4. Write the approval digest: at most 10 lines, listing only the decisions a human must own, each with its recommended option, and the auditor's totals.

Done when the spec is at gap zero, its box is unmarked, and the digest is in your final message.
