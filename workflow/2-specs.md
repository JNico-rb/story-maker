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
- Requirements go in the module's logical order. A new one is inserted where it belongs and renumbers the ones after it; the renumbering reaches its `plan.md` in the same commit. A retired one leaves its gap.
- Dependent specs reference each other by number; each requirement lives in exactly one spec.
- Written → leave its approval box unmarked and **stop**.
- Changing one: edit the requirements, unmark the approval boxes of both `spec.md` and `plan.md`, re-run [process 3](3-plan.md) and [process 4](4-code.md) for what changed. A deleted requirement means a deleted test.
