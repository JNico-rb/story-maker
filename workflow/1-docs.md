# Process 1 — Changing the reference docs (`docs/*.md`)

The docs state the intended domain and design; today's code may lag behind them.

1. Pick the **single owning doc**.
2. New or renamed terms go to `definitions.md` first and nowhere else.
3. Closing a decision = moving it from `architecture.md` §10 to §11, with its reason and the alternatives discarded written in the section that owns it. Reopening a §11 decision needs a stated reason in the same commit.

   A decision goes to an ADR in `docs/adr/` instead only when all four hold:

   1. **Hard to reverse** — changing your mind later has a meaningful cost.
   2. **Surprising without context** — a future reader would wonder why it was done this way.
   3. **A real trade-off** — there were genuine alternatives, and one was picked for specific reasons.
   4. **No section of `docs/*.md` owns it** — typically how the project is built, not what the product does.

   Yes: where decisions live ([ADR 0001](../docs/adr/0001-decisiones-en-architecture.md)). No: "no re-ranking", which `architecture.md` §3.2 owns.

   Format: `docs/adr/NNNN-slug.md`, next free number. One to three sentences — context, decision, why; add Status, Considered options or Consequences only when they carry weight. An accepted ADR is not rewritten: changing your mind is a new ADR, and the old one gets `Status: superseded by NNNN`.
4. A new verification method goes to `verification.md` + its row in §5; an accepted risk goes to §6 with name and motive.
5. Done when every `spec.md`, `plan.md` and piece of code the change now contradicts is named — and fixed or listed.

A doc change alone changes no behaviour; it is followed by spec, plan and code.
