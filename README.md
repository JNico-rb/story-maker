# Story Maker

Generator of Spanish-language novels about **what the world will look like after the AI revolution**. The user supplies an idea, and the system turns it into a complete novel: coherent, with every narrative thread tied off, and free of anachronisms.

## Repo layout

```
story-maker/
├── AGENTS.md          # universal rules
├── README.md
├── config.json        # example run config; null marks a value still to be calibrated
├── docs/              # source of truth: domain and design
├── specs/             # one folder per feature, NNN-slug/: spec.md, plan.md, design.md
├── workflow/          # how each layer changes: docs, specs, plans, code
├── backend/           # FastAPI service
├── frontend/          # React + Vite SPA
└── .claude/
```
