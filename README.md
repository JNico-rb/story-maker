# Story Maker

Generator of Spanish-language novels about **what the world will look like after the AI revolution**. The user supplies an idea, and the system turns it into a complete novel: coherent, with every narrative thread tied off, and free of anachronisms.

## Repo layout

```
story-maker/
├── AGENTS.md          # this file - universal rules. CLAUDE.md only references it
├── README.md
├── TODO.md            # the implementation plans, one block per spec
├── config.json        # example run config; null marks a value still to be calibrated
├── docs/              # source of truth: domain and design
├── specs/             # layer 2 - one file per feature, NNN-nombre.md
├── backend/           # FastAPI service
├── frontend/          # React + Vite SPA
└── .claude/
```
