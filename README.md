# Story Maker

Personalized gift novels, set in the world after the AI revolution. A buyer is interviewed about the recipient —name, age, traits, memories, genre, tone, length, what must not appear— and an agentic harness writes a 10-chapter novel the recipient can recognise themselves in, then keeps it alive: the reader can ask for a change from the web reader, and only the affected chapters are regenerated into a new version.

The brief this project answers is [project-constraints.md](project-constraints.md); what was decided and why, before any code, is [ADR 0003](docs/adr/0003-pivote-al-encargo.md).

> Status: design and specs. The example brief, the MCP connection guide, the TLA+ ↔ code mapping and the example novel land here as their specs are implemented.

## Repo layout

```
story-maker/
├── CLAUDE.md              # rules for every agent working here
├── project-constraints.md # the exam brief
├── config.json            # example server policy; null marks a figure still to calibrate
├── .env.example           # credentials and server settings the backend reads (placeholders only)
├── docs/                  # the four reference docs and adr/
├── specs/                 # one folder per feature, NNN-slug/: spec.md, plan.md, design.md
├── workflow/              # how each layer changes: docs, specs, plans, code
├── backend/               # FastAPI service and the harness (roles on the Claude Agent SDK)
├── frontend/              # React + Vite web reader
├── images/                # corporate identity used by the frontend
├── presentation/          # the brief's /presentacion/: deck, annexes, demo video
└── .claude/               # Claude Code skills and settings
```

Planned, created by the spec that needs them: `lean/` (formal story validator), `tla/` (formal harness spec) and `ejemplos/` (example brief and `novela-ejemplo.pdf`).

## Where each deliverable lives

`docs/` holds four reference docs —[definitions](docs/definitions.md), [domain-knowledge](docs/domain-knowledge.md), [architecture](docs/architecture.md), [verification](docs/verification.md)— and [adr/](docs/adr/). The process documentation the brief asks for is kept inside them, next to what it documents:

| The brief asks for | Where |
|---|---|
| Initial spec: what was decided and why | [ADR 0003](docs/adr/0003-pivote-al-encargo.md) |
| Trade-offs: options, criteria, choice | [architecture.md §16](docs/architecture.md#16-decisiones-cerradas) and [docs/adr/](docs/adr/) |
| Explainers, one per course concept applied | A short block at the head of the section that applies the concept (list below), written when the concept is implemented |
| Harness architecture diagram | [architecture.md §2, §8.1, §9.5](docs/architecture.md#2-premisas-de-operación) |
| TLA+ state machine diagram | [architecture.md §9.1](docs/architecture.md#91-estados-de-una-ejecución) for now; the full diagram lands in [§10.6](docs/architecture.md#106-validador-formal-del-sistema-tla) with spec 006, and the spec itself in `tla/` |
| SQLite schema diagram | [architecture.md §14.5](docs/architecture.md#145-esquema-sqlite) |
| Validators with their execution point | [architecture.md §10.2](docs/architecture.md#102-los-validadores) |
| Iteration log | [verification.md §8](docs/verification.md#8-registro-de-iteraciones) |
| Red-team log | [verification.md §4.9](docs/verification.md#49-red-teaming--clase-t) |
| Evals with measurable results | [verification.md §4.2](docs/verification.md#42-evals--clase-t-i-o-d-según-el-método-de-puntuación) |
| Browser MCP usage, skills, subagents, commands, memory | [verification.md §9](docs/verification.md#9-claude-code-en-el-desarrollo) |
| Security report | `docs/security-report.md`, written by the security audit |

### Explainers

| Concept | Section |
|---|---|
| Harness and roles: why nine roles and not one agent | `architecture.md` §7.2 |
| Context and memory: hybrid RAG without re-ranking, residents, the 100k ceiling | `architecture.md` §6.1 |
| Tools with validated schemas | `architecture.md` §7.4 |
| Hooks: chapter validation and policy | `architecture.md` §7.5 |
| Skills and `CLAUDE.md`: the harness workspace vs the development one | `architecture.md` §7.3 |
| Retries and limits: why no loop is unbounded | `architecture.md` §7.6 |
| Guardrails and the policy engine | `architecture.md` §11 |
| Untrusted text and prompt injection | `architecture.md` §3.3 |
| LLM-as-judge and rubrics | `architecture.md` §10.3 |
| Human evaluation vs the judge | `architecture.md` §10.7 |
| Observability with Langfuse and versioned prompts | `architecture.md` §12 |
| Formal verification of the story with Lean 4 | `architecture.md` §10.5 |
| Formal verification of the system with TLA+ | `architecture.md` §10.6 |
| MCP: the platform server and the browser MCP | `architecture.md` §13.2 |
| Spec-driven development: docs → spec → plan → tests → code | `verification.md` §9 |
