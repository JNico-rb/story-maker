# story-maker

Novelas personalizadas de regalo, ambientadas en un presente alternativo **post-IA**. El cliente cuenta en una entrevista quién es el destinatario, sus allegados, sus recuerdos, la ocasión y el tono; el sistema escribe una novela de 10 capítulos donde el destinatario es el protagonista, comprueba su coherencia —con verificación formal en Lean 4 de la cronología— y la entrega para leer en web y en PDF. El lector puede pedir un cambio y solo se reescriben los capítulos afectados.

Es el proyecto del examen de Harness Engineering: el encargo está en [project-constraints.md](project-constraints.md) y la spec inicial en [ADR 0006](docs/adr/0006-diseno-lean.md).

## Estado

El producto se construye spec a spec (estado en [TODO.md](TODO.md) → *Estado*). Alcance de la entrega: web mínima (entrar, leer, versiones y pedir un cambio) y configuración por la CLI (`docs/architecture.md` §18, «Alcance del frontend»). Lo marcado *pendiente* abajo llega con la spec que se indica; lo marcado *fuera de alcance* es opcional en el encargo y no se entrega.

## Arranque rápido

Requisitos: Python 3.12 y `uv`; Node 24 y pnpm 10.x (en Windows, `pnpm.cmd`); Microsoft Edge instalado (PDF); Claude Code (`claude`) **con sesión iniciada**: los roles del producto usan ese login, sin claves de pago. Langfuse Cloud (UE) en plan Hobby y GitHub Free (Lean corre en GitHub Actions). Opcional: JDK 21 portable para TLC.

```sh
cp .env.example .env           # JWT_SECRET (32 caracteres o más) y FORMAL_VERIFIER (local | github); no hay claves de pago
cd backend && uv sync
uv run story-maker init-db     # crea la base en el directorio de datos; no pisa una existente sin --reset
uv run story-maker check-env   # informa de cada comprobación de config, ajustes y base
cd ../frontend && pnpm.cmd install && pnpm.cmd build
cd ../backend && uv run story-maker serve     # sin --reload; escucha en STORY_MAKER_BASE_URL
```

Novela de ejemplo de principio a fin: `uv run story-maker example ../ejemplos/briefs/ejemplo.json` → `ejemplos/novela-ejemplo.pdf` (*pendiente, spec 020*; el brief de ejemplo se reproducirá aquí).

## Mapa de entregables del encargo

| Entregable | Dónde vive |
|---|---|
| Spec inicial | [docs/adr/0006-diseno-lean.md](docs/adr/0006-diseno-lean.md) |
| Trade-offs (opciones, criterio, elección) | [docs/architecture.md](docs/architecture.md) §18 |
| Explainers, uno por concepto del curso | `docs/architecture.md` §16 |
| Diagramas: arquitectura del harness · máquina de estados · esquema SQLite · validadores con su punto de ejecución | `docs/architecture.md` §1.4 · §9.1 (y `tla/`) · §15.6 · §11.2 |
| Evals con resultados medibles | [docs/verification.md](docs/verification.md) §4.2 |
| Registro de iteraciones | `docs/verification.md` §8 |
| Red-team log | `docs/verification.md` §4.9 |
| Informe de seguridad | *fuera de alcance* (opcional en el encargo, spec 021) |
| Harness de producto: `CLAUDE.md`, skill y dos hooks | `backend/harness_workspace/`; `docs/architecture.md` §7.3 y §7.5 |
| Verificación formal: Lean 4 · TLA+ | [lean/](lean/) · [tla/](tla/) |
| Novela de ejemplo | `ejemplos/novela-ejemplo.pdf` (*pendiente, spec 020*) |
| Presentación y vídeo de demo | [presentacion/](presentacion/) |
| Claude Code: `CLAUDE.md`, `.claude/` (agentes, comandos, hooks, skills, memoria), `.mcp.json` con browser MCP | [CLAUDE.md](CLAUDE.md), [.claude/](.claude/), [.mcp.json](.mcp.json); su uso, en `docs/verification.md` §9 |
| Sin claves en el repo | [.env.example](.env.example) |

## Correspondencia TLA+ ↔ código

Cada acción de `tla/Harness.tla` corresponde a una transición del orquestador o de la API (`docs/architecture.md` §9.1). `tla/Regenerations.tla` usa las mismas acciones —`PedirCambio`, `Regenerar` (con la revalidación de la base de §10.2), `Fallar` (también `stale_base`), `Publicar`, `Caer` y `Reanudar`— y remite a sus filas; su invariante es `VersionesLineales`. La columna Código se rellena al cerrar cada spec implementadora y la revisa el `verificador` (`docs/verification.md` §4.10).

| Acción TLA+ | Transición (§9.1, como la modela la 006) | Quién la dispara | Spec del código | Código |
|---|---|---|---|---|
| `Configurar` | → `queued` (generation, candidata vacía) | API: `POST /api/novels/{id}/runs` con el brief confirmado | 011 (API de ejecuciones) | `pipeline/queue.py:enqueue_generation`, `api/runs.py:launch_generation` |
| `Planificar` | `queued` → `running`, `planning`; relanzada: → `writing` (capítulo k+1) o `gate` | Worker: toma la primera de la cola y abre el planner o sigue desde el punto de control | 011 (worker), 010 (planner) | pendiente, arranque (011-C33) |
| `Regenerar` | `queued` → `running`, `writing` del primer afectado, con la candidata copiada de la base revalidada; relanzada: como `Planificar`, revalidando la base | Worker | 014 (cambio) | pendiente, 014 |
| `EscribirCapitulo` | `writing` o `rewriting`: entrega del capítulo en curso | Orquestador, sesión del writer (en un fallo de datos del gate, el editor vuelve a registrar sin writer) | 011; en `rewriting`, 012 | pendiente, arranque (011-C33) |
| `Validar` | pasa: plan aplicado (punto de control 0), capítulo aceptado (con punto de control en `writing`) o gate superado; falla: defectos, o `gate` → `rewriting` con los capítulos atribuidos | Validador `outline`; hooks, editor y veredicto; validadores del gate | 010 (`outline`), 011, 012 (gate) | pendiente, arranque (011-C33) |
| `Reintentar` | defectos → nuevo intento del mismo evaluable; `rewriting` → `gate` con los atribuidos aceptados | Orquestador, con la guarda de `max_retries.*` | 010, 011, 012 | pendiente, arranque (011-C33) |
| `Gate` | `writing` → `gate`, sin capítulos por escribir | Orquestador | 012 | pendiente, arranque (011-C33) |
| `Publicar` | `gate` superado → `published`; versión siguiente; solicitud o edición `applied` | Transacción de publicación (§9.3) | 012 | pendiente, arranque (011-C33); la vía por solicitud o edición además necesita 014 |
| `Fallar` | `running` (o `queued` con base obsoleta, en `Regenerations.tla`) → `failed`; candidata `discarded`; solicitud o edición `rejected` | Límite agotado, fallo no atribuible, `edit_rejected`, `stale_base`, caída con `max_resumes` agotado | 010, 011, 012, 014, según el motivo | pendiente, arranque (011-C33); `edit_rejected` y `stale_base` además necesitan 014 |
| `Caer` | `running` → `interrupted` | Error del proveedor, verificador inalcanzable o agotado, arranque con la ejecución en `running` | 011 (caída y arranque), 012 (verificador) | pendiente, arranque (011-C33) |
| `Reanudar` | `interrupted` → `queued`, en su puesto original | `POST /api/runs/{id}/resume` o `story-maker resume` | 011 (API y CLI) | `pipeline/runs.py:resume_run`, `api/runs.py:resume`, `cli.py:resume_command` |
| `PedirCambio` | → `queued` (change_request o manual_edit, con la vigente como base) | API: confirmar un cambio con su código (la edición manual, 019, queda fuera de alcance) | 014 | pendiente, 014 |

## Servidores MCP

El servidor MCP de la plataforma (spec 015) es opcional en el encargo y queda *fuera de alcance*.

Para el desarrollo, `.mcp.json` ya trae Playwright MCP (Edge) y el MCP de Langfuse; este último lee la cabecera de la variable de entorno `LANGFUSE_MCP_AUTH` (`Basic <base64 de public_key:secret_key>`), que se define en el entorno del usuario, nunca en el repo.

## Trabajo en paralelo

El desarrollo va en carriles: un worktree hermano por carril (`../sm-<x>`, rama `carril-<x>`), cada uno con su terminal de Claude Code y sus specs en orden.
El checkout principal (V2) es el integrador: escribe specs y planes por delante, integra con `git merge --no-ff` cada spec cerrada y mantiene la tabla de carriles de `TODO.md`.
Sin revisiones (decisión del usuario, 2026-09-24): el integrador escribe y marca specs y planes, y `verificador` cierra cada spec.
Para empezar, abre Claude Code en el checkout principal y ejecuta `/orquestar`: dice qué terminales abrir y en qué orden (`/orquestar sin-terminales` lo hace con subagentes en segundo plano).
Reglas completas: [AGENTS.md](AGENTS.md), sección *Parallel lanes*.
