# Process 2 — Changing a spec

One folder per feature: `specs/NNN-slug/`, `NNN` sequential in implementation order, `slug` in ASCII without accents. Two features = two folders.

| File | Holds |
|---|---|
| `spec.md` | What: observable behaviour, with its own approval box |
| `plan.md` | Steps, with its own approval box ([process 3](3-plan.md)) |
| `design.md` | How, only when the spec needs it: tables, modules, external interfaces |

`spec.md` contents, in this order:

1. `- [ ] Spec approved   <- only the user marks this`
2. `## Objetivo` — one sentence.
3. `## Alcance` — what it covers and, if anything, what it leaves **fuera de alcance**, with the reason.
4. `## Requisitos` — `RF-<MÓD>-<n>`, each a checkable case: condition → observable result, including rejections and boundaries. Every row carries its priority and its T/A/I/D/U class.
5. `## Requisitos no funcionales` (`RNF-<n>`, with class) and `## Restricciones` (`R<n>`, with origin), when the spec has any.
6. `## Docs de referencia` — the sections of `docs/*.md` it rests on.

Rules:

- Behaviour only: file names, signatures and libraries go to `design.md`. Exception: `001-base` holds the technical constraints of `architecture.md` §6.12 and §14 as checkable requirements.
- Consistent with `docs/*.md`; where they disagree, the doc wins. A spec that needs a doc change waits for [process 1](1-docs.md).
- **Obligatorio** is V1; **Deseable** may be left out without invalidating the delivery.
- Uncalibrated figures (`architecture.md` §15.2) are named as such and given no value.
- Requirements go in the module's logical order. An ID never changes: a new requirement takes the next free number of its module and sits where it belongs, and a retired one leaves its gap. Tests and commits cite IDs, so a renumbering would silently repoint them.
- Dependent specs reference each other by number; each requirement lives in exactly one spec.
- Written → run the gap loop below, then leave its approval box unmarked, with the digest, and **stop**.
- Changing one: edit the requirements, unmark the approval boxes of both `spec.md` and `plan.md`, re-run [process 3](3-plan.md) and [process 4](4-code.md) for what changed. A deleted requirement means a deleted test. Unmark only for a change of behaviour; a wording, link or formatting fix leaves the boxes as they are.

## Gap loop — before asking for approval

The spec answers to the docs and to the brief; `docs/relational-matrix.md` records the gap between them. A requirement is supported by a section of `architecture.md` or `verification.md`, or by an item of `project-constraints.md`.

1. Dispatch the `auditor` subagent on the spec folder.
2. Add each difference it reports to the spec's section of the matrix, open, with the gravedad the auditor gave it.
3. Close each blocking one in one of three ways:
   - fix the spec;
   - fix the doc through [process 1](1-docs.md), grill included;
   - point it to the spec that covers it in the matrix's §1.

   A minor one is closed the same way or left `aceptada`.
4. Repeat from 1 until a pass on the final text reports no blocking difference: that is **gap zero**. Mark the spec's §1 rows reviewed. Three passes at most: if blocking differences remain after the third, notify the user with `PushNotification` and **stop**.
5. Write the approval digest: at most 10 lines, with the decisions a human must own, each with its recommended option, and the auditor's totals.
