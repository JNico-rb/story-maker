# story-maker — instrucciones para Claude Code

Novelas personalizadas de regalo en un presente alternativo post-IA: una entrevista produce el brief, un harness multi-agente (Claude Agent SDK) escribe 10 capítulos, los validadores —Lean y TLA+ incluidos— deciden si se publica, y se lee en web y en PDF.
Es el proyecto del examen de Harness Engineering; el encargo es [project-constraints.md](project-constraints.md).
Este fichero instruye a Claude Code **en el desarrollo**. El `CLAUDE.md` **de producto**, el que leen los roles en ejecución, es otro: `backend/harness_workspace/CLAUDE.md`, con otro lector y otras reglas (el backend excluye este de las sesiones de rol).

## Cómo se trabaja

@AGENTS.md

Resumen: cinco capas en orden, sin revisiones (ni autorrevisión ni auditor: el integrador escribe y marca spec y plan; `verificador` cierra tras TDD), casos D al final y carriles en paralelo. Arranque: `/orquestar` en el checkout principal (V2); `/carril <X>` en cada worktree.

## Mapa del repo

| Ruta | Qué hay |
|---|---|
| `project-constraints.md` | el encargo |
| `docs/` | fuente de verdad: `definitions`, `domain-knowledge`, `architecture`, `verification`, y `adr/` |
| `specs/` | `000-scaffolding.md` (transversal, la primera); `backend/` y `frontend/`, una spec por feature, `NNN-nombre.md`, numeración global |
| `TODO.md` | tabla de carriles y un bloque de plan por spec |
| `backend/` | FastAPI + harness en `src/story_maker/`, `harness_workspace/`, `tests/` (ver `backend/AGENTS.md`) |
| `frontend/` | SPA Vite + React (ver `frontend/AGENTS.md`) |
| `lean/`, `tla/` | verificación formal de la historia (Lean 4) y del sistema (TLA+) |
| `ejemplos/`, `presentacion/`, `images/` | briefs y novela de ejemplo, deck y vídeo, marca |
| `.env.example` | ajustes y secretos, solo con marcadores |
| `.claude/`, `.mcp.json` | harness de desarrollo: agentes, comandos, hooks, skills, memoria espejo, MCP |

## Comandos canónicos

| Lado | Desde | Comandos |
|---|---|---|
| Backend | `backend/` | `uv sync` · `uv run pytest` · `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy src` |
| Frontend | `frontend/` | `pnpm.cmd install` · `pnpm.cmd lint` · `pnpm.cmd typecheck` · `pnpm.cmd build` · `pnpm.cmd test` |
| Servidor | `backend/` | `uv run story-maker serve` (sin `--reload`) |

«Suite completa» = los cuatro comandos de verificación de cada lado que toque el cambio.

## Leer poco

- `docs/*.md`, las specs y `TODO.md` pesan mucho (`architecture.md` ≈ 36k tokens). Nunca enteros: `grep -n '^## ' <fichero>` para el índice y lee solo la sección que toca, con `offset`/`limit`.
- `TODO.md`: la cabecera, o tu bloque (`sed -n '/^## NNN /,/^## [0-9]/p' TODO.md`); el estado de todas las specs, con `awk -f .claude/scripts/resumen-todo.awk TODO.md`.
- Modelos en el frontmatter de cada agente: opus en `redactor-specs` y `seguridad`; sonnet en `implementador` y `verificador`. El `implementador` de 012 y 014 se lanza con `model: opus`. Roles del producto: `config.json`.

## Harness de desarrollo

| Pieza | Nombres | Para qué |
|---|---|---|
| Subagentes (`.claude/agents/`) | `redactor-specs`, `implementador`, `verificador`, `seguridad` | escribir specs, implementar con TDD, cerrar, auditar la seguridad |
| Comandos (`.claude/commands/`) | `/orquestar`, `/carril`, `/spec`, `/plan`, `/implementar`, `/integrar`, `/estado`, `/log-decision` | integrar, llevar un carril, cada capa del flujo, ver el estado, registrar una decisión |
| Hooks (`.claude/hooks/`) | `guard-secretos`, `guard-plan` | bloquear claves reales en lo escrito; bloquear código sin plan aprobado con pasos pendientes |
| MCP (`.mcp.json`) | `playwright`, `langfuse` | inspeccionar la lectura web en Edge; consultar trazas y prompts |
| Skills (`.claude/skills/`) | ver su `README.md` | FastAPI, FSD, React, SQLAlchemy, verificación |

Cada uso real de un subagente, comando o del browser MCP se registra en `docs/verification.md` §9.

## Modelo de los roles: el login de Claude Code

- 0 € de créditos de API. Los roles del producto usan la sesión de Claude Code de la máquina (suscripción): `LLM_PROVIDER=claude_login` por defecto; `anthropic_compatible` es opcional.
- Las generaciones reales solo corren en una máquina con `claude` con sesión iniciada. Nunca redefinas `CLAUDE_CONFIG_DIR`: el SDK perdería esa sesión.
- Ninguna prueba ni la CI llaman a un modelo: las pruebas T usan el doble falso del puerto de agente. Las demostraciones D con modelo real gastan cuota de la suscripción: agrúpalas al final de cada spec y no las repitas sin motivo.
- Langfuse en plan Hobby y GitHub Free: nada de pago.

## Trampas del entorno (Windows sin admin)

- **Smart App Control en Enforce**: un binario sin firma ni reputación muere sin mensaje (Git Bash: rc=127). Lean no corre aquí: `FORMAL_VERIFIER=github` y `lake build` en GitHub Actions.
- **pnpm 10.x** y en Git Bash siempre `pnpm.cmd`; pnpm 11+ no arranca sin el runtime de VC++.
- **Python 3.12** fijado en `backend/.python-version`: SAC bloquea wheels de 3.14.
- **SAC y lanzadores de uv**: el `.exe` que uv genera para una orden (p. ej. `detect-secrets`) puede morir bloqueado; se invoca como módulo, `uv run python -m <módulo>`.
- **uvicorn sin `--reload`**: rompe los subprocesos del Agent SDK en Windows.
- **`LongPathsEnabled=0`**: Python falla con rutas de más de 260 caracteres → worktrees hermanos con ruta corta (`../sm-<x>`), nunca bajo `.claude/`.
- **Playwright MCP 0.0.82 bloquea `file://`**: un HTML local se inspecciona sirviéndolo en `http://127.0.0.1`.
- **PowerShell en `Restricted`** a propósito: se usan los shims `.cmd`; no cambies la ExecutionPolicy.

## Secretos

- Nunca leas `.env` (denegado en `.claude/settings.json`). Los secretos viven solo ahí; `.env.example` lleva marcadores.
- Un worktree nuevo copia el `.env` del checkout principal con `cp ../story-maker/.env .env`, sin abrirlo ni mostrarlo.
- `guard-secretos` bloquea escribir algo con forma de clave real; en pruebas y docs usa marcadores (`TU_CLAVE_AQUI`).
