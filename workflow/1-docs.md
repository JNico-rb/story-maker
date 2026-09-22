# Process 1 — Changing the reference docs (`docs/*.md`)

The docs state the intended domain and design; today's code may lag behind them.

1. Pick the **single owning doc**.
2. New or renamed terms go to `definitions.md` first and nowhere else.
3. Closing a decision = moving it from `architecture.md` §10 to §11 with its reason. Reopening a §11 decision needs a stated reason in the same commit.
4. A new verification method goes to `verification.md` + its row in §5; an accepted risk goes to §6 with name and motive.
5. Done when every `spec.md`, `plan.md` and piece of code the change now contradicts is named — and fixed or listed.

A doc change alone changes no behaviour; it is followed by spec, plan and code.
