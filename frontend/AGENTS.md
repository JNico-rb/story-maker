# frontend/AGENTS.md

Overrides the root `AGENTS.md` on frontend specifics only — never on the gates or the layer order.

## Stack

Vite, React, TypeScript strict, Tailwind, ESLint, Vitest, pnpm **10.x**. Always `pnpm.cmd` on this machine (Git Bash's shims fail; pnpm 11+ does not start without the VC++ runtime). Every dependency is declared up front in `package.json` (spec 000), so lanes never collide on `pnpm-lock.yaml`: a missing one goes to the integrator.

## Commands (from `frontend/`)

    pnpm.cmd install      # first time in each worktree
    pnpm.cmd lint
    pnpm.cmd typecheck
    pnpm.cmd build        # production build; FastAPI serves it (STORY_MAKER_FRONTEND_DIST, default frontend/dist)
    pnpm.cmd test         # Vitest

In development Vite proxies `/api` to the backend (`uv run story-maker serve`, never `--reload`).

## Organization — Feature-Sliced Design, pages-first

Load the `feature-sliced-design` skill before deciding where code goes.

| Layer | Holds |
|---|---|
| `src/app/` | entry, providers, router, global styles and brand tokens |
| `src/pages/<page>/` | one slice per screen; the page owns its UI, state and API calls until a second page needs them |
| `src/shared/` | `api/` (generated types + thin client), `ui/` (branded primitives), `lib/`, `config/` |

- Imports go downward only: `app` → `pages` → `shared`. Slices of one layer never import each other; each slice exposes its public API through `index.ts`.
- Open `features/` or `entities/` only when two pages share a stable responsibility; no `widgets/`.
- Screens come from specs, never from here (`docs/architecture.md` §14.1).

## API types

`pnpm.cmd gen:api` (`openapi-typescript`, with the backend serving on `127.0.0.1:8000`) generates `src/shared/api/schema.d.ts` from the backend's OpenAPI schema; the output is committed. Regenerate it whenever the API changes; never edit it by hand. There is no drift job: a stale type shows up as a `typecheck` failure against the regenerated file.

## Brand

The corporate brand (logo `images/qaracter-logo.png`, palette, typography) is defined once as Tailwind theme tokens in `src/app/` by spec 000. Components use the tokens, never raw hex values or ad-hoc fonts; the logo is imported from `shared/`, not copied per page.

## Tests

- Vitest; names state the behaviour. No test reaches a real backend: API calls are stubbed at the `shared/api` boundary.
- The visual walkthrough with Playwright MCP is class D and is logged in `docs/verification.md` §9.3.

## Module ownership by spec

Lane E owns `frontend/`. Frontend specs start at 022 in `specs/frontend/`; the integrator adds one row per spec when it is approved. Within `frontend/`, a spec touches only its own page slices and adds files to `shared/`; a change to another spec's files goes through the integrator.

| Spec | Lane | Slices it may touch |
|---|---|---|
| 000 scaffolding | integrator (V2) | tooling, `package.json`, `pnpm-lock.yaml`, `src/app/` skeleton and brand tokens, `src/shared/ui/` primitives |
| 022 acceso | E | `src/pages/` (register, login), `src/shared/api/` (client with the session header, 401 handling), `src/shared/lib/` (stored session), `src/app/` (router and protected routes) |
| 023 mis-novelas | E | `src/pages/` (novels list, user-level banned terms) |
| 024 entrevista | E | `src/pages/` (interview: chat, brief panel, free texts, facts, novel-level banned terms, confirmation) |
| 025 progreso | E | `src/pages/` (run progress: polling, resume, report) |
| 026 lectura | E | `src/pages/` (reading: cover, index, changed chapters, chapters, cast sheet, versions, PDF) |
| 027+ | E | rows added as frontend specs are approved |
