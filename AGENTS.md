# AGENTS.md — Instructions

**Ignore the contents of the other branches entirely.** The project was restarted from scratch, so nothing from before is valid as a reference.

All work must be done on the V2 branch.

## Stack

- **Backend:** Python with FastAPI. Use `uv` as the package manager.
- **Frontend:** TypeScript with React, built with Vite. Use `pnpm` as the package manager.

## Reference docs

The `docs/` folder is the source of truth for the design. Given the context limit, **load only the document the task actually needs** — they are deliberately split so you never have to read all of them at once.

| Document | What it holds | Read it when |
|---|---|---|
| [docs/definitions.md](docs/definitions.md) | The domain vocabulary: what entities exist (Novum, Consecuencia, Escena, Compromiso, Criterio, Defecto…), their attributes, relations and class models. | You are naming a class, a field, an endpoint payload or a DB table, or you are unsure what a term means in this project. **This is the naming authority — do not invent a synonym for something already defined here.** |
| [docs/domain-knowledge.md](docs/domain-knowledge.md) | Why the domain behaves the way it does: speculative coherence, the causal graph rooted in the novum, the saturated trope space of the post-AI subgenre, epistemic state and narrative drift. | You need to judge whether a behaviour is *correct for the genre*, not just correct as code — writing prompts, quality rubrics, trope scoring or novum derivation logic. It explains rationale, never structure. |
| [docs/architecture.md](docs/architecture.md) | The design decisions: layer separation, context management, the four quality gates, config families, the five agents, API contract, stack, and the open/closed decision log. | You are implementing or changing anything in the pipeline, the config schema, the agent system or the API. §10 lists what is still undecided; §11 lists what must not be reopened without cause. |
| [docs/verification.md](docs/verification.md) | How we verify *the system* (not the novel): the 18 verification methods — types, SAST, symbolic execution, property-based and mutation testing, contract tests, tracing, evals, guardrails, multi-agent verification, model checking… — each classified T/A/I/D/U (Trust Spec), plus the coverage table, the accepted risks and the adoption order. | You are writing tests, evals, CI steps or guardrails, or deciding *how* to gain confidence in a component. §5 says which method covers which piece of the design; §6 lists what is deliberately left unverified. |
Writing rules for these docs:

- **One concern per document.** Vocabulary goes in `definitions.md`, rationale in `domain-knowledge.md`, decisions in `architecture.md`, verification methods in `verification.md`. Do not duplicate a definition across files — cross-reference it instead.
- **Quality gates vs. verification.** The four gates (`architecture.md` §4) judge the generated novel at runtime; `verification.md` covers how we gain confidence in the system itself. If the failure shows up in a run report it belongs to the gates; if it shows up in CI it belongs to `verification.md`.
- Identifiers in diagrams and entity names go **without accents or spaces**, so Mermaid renders anywhere.
- A decision recorded in `architecture.md` §11 is closed; reopening it needs an explicit reason stated in the change.

# Constraints
- 100k tokens is the maximum context window.
