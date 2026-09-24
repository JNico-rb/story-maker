# story-maker

Novelas personalizadas de regalo, ambientadas en un presente alternativo **post-IA**. El cliente cuenta en una entrevista quién es el destinatario, sus allegados, sus recuerdos, la ocasión y el tono; el sistema escribe una novela de 10 capítulos donde el destinatario es el protagonista, comprueba su coherencia —con verificación formal en Lean 4 de la cronología— y la entrega para leer en web y en PDF. El lector puede pedir un cambio y solo se reescriben los capítulos afectados.

Es el proyecto del examen de Harness Engineering: el encargo está en [project-constraints.md](project-constraints.md) y la spec inicial en [ADR 0006](docs/adr/0006-diseno-lean.md).

## Estado

Diseño escrito (`docs/`) y scaffolding en marcha; el producto se construye spec a spec (tabla en [TODO.md](TODO.md)). Lo marcado *pendiente* abajo llega con la spec que se indica.

## Arranque rápido

Requisitos: Python 3.12 y `uv`; Node 24 y pnpm 10.x (en Windows, `pnpm.cmd`); Microsoft Edge instalado (PDF y revisión visual); Claude Code (`claude`) **con sesión iniciada**: los roles del producto usan ese login, sin claves de pago. Langfuse Cloud (UE) en plan Hobby y GitHub Free (Lean corre en GitHub Actions). Opcional: JDK 21 portable para TLC.

```sh
cp .env.example .env           # rellena los marcadores; no hay claves de pago
cd backend && uv sync
cd ../frontend && pnpm.cmd install && pnpm.cmd build
cd ../backend && uv run story-maker serve     # sin --reload
```

Novela de ejemplo de principio a fin: `uv run story-maker example ../ejemplos/briefs/ejemplo.json` → `ejemplos/novela-ejemplo.pdf` (*pendiente, specs 013 y 020*; el brief de ejemplo se reproducirá aquí).

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
| Informe de seguridad | `docs/security-report.md` (*pendiente, spec 021*) |
| Harness de producto: `CLAUDE.md`, skill y dos hooks | `backend/harness_workspace/`; `docs/architecture.md` §7.3 y §7.5 |
| Verificación formal: Lean 4 · TLA+ | [lean/](lean/) · [tla/](tla/) |
| Novela de ejemplo | `ejemplos/novela-ejemplo.pdf` (*pendiente, spec 013*) |
| Presentación y vídeo de demo | [presentacion/](presentacion/) |
| Claude Code: `CLAUDE.md`, `.claude/` (agentes, comandos, hooks, skills, memoria), `.mcp.json` con browser MCP | [CLAUDE.md](CLAUDE.md), [.claude/](.claude/), [.mcp.json](.mcp.json); su uso, en `docs/verification.md` §9 |
| Sin claves en el repo | [.env.example](.env.example) |

## Correspondencia TLA+ ↔ código

Cada acción de `tla/Harness.tla` corresponde a una transición del orquestador (`docs/architecture.md` §9.1). `tla/Regenerations.tla` modela dos cambios simultáneos sobre la misma novela (invariante `VersionesLineales`).

| Acción TLA+ | Transición del harness | Código |
|---|---|---|
| `Configurar` | brief confirmado → ejecución `queued` | pendiente (spec 011) |
| `Planificar` | `queued` → `running` (`planning`); plan aceptado = punto de control del capítulo 0 | pendiente (spec 011) |
| `EscribirCapitulo` | `writing(n)`: el writer entrega el capítulo n | pendiente (spec 011) |
| `Validar` (pasa / falla) | hook de validación + editor + veredicto por código | pendiente (spec 011) |
| `Reintentar` | defectos bloqueantes con intentos restantes → `rewriting` | pendiente (spec 011) |
| `Caer` | `running` → `interrupted` | pendiente (spec 011) |
| `Reanudar` | `interrupted` → `running` desde el último punto de control | pendiente (spec 011) |
| `Gate` | capítulo 10 aceptado → `gate` | pendiente (spec 011) |
| `Publicar` | gate superado → `published` | pendiente (spec 011) |
| `Fallar` | intentos o ciclos agotados → `failed` | pendiente (spec 011) |
| `PedirCambio` | solicitud de cambio confirmada → ejecución `change_request` en cola | pendiente (spec 011) |
| `Regenerar` | reescritura de los capítulos afectados → gate → nueva versión | pendiente (spec 011) |

## Conectar el servidor MCP

*Pendiente, spec 015.* La plataforma expondrá un servidor MCP en `/mcp` (lectura: `list_novels`, `get_chapter`, `list_versions`, `query_story_bible`, `download_novel`; escritura con confirmación: `request_change`, `confirm_change`), autenticado con el token del usuario. Aquí irán los pasos para conectarlo desde Claude Code, Claude Desktop o MCP Inspector.

Para el desarrollo, `.mcp.json` ya trae Playwright MCP (Edge) y el MCP de Langfuse; este último lee la cabecera de la variable de entorno `LANGFUSE_MCP_AUTH` (`Basic <base64 de public_key:secret_key>`), que se define en el entorno del usuario, nunca en el repo.

## Trabajo en paralelo

El desarrollo va en carriles: un worktree hermano por carril (`../sm-a` … `../sm-e`, rama `carril-<x>`), cada uno con su terminal de Claude Code y sus specs en orden.
El checkout principal (V2) es el integrador: escribe specs y planes por delante, integra con `git merge --no-ff` cada spec cerrada y mantiene la tabla de carriles de `TODO.md`.
Las aprobaciones están delegadas en agentes: `auditor` aprueba specs y planes a gap cero y `verificador` cierra cada spec.
Para empezar, abre Claude Code en el checkout principal y ejecuta `/orquestar`: dice qué terminales abrir y en qué orden (`/orquestar sin-terminales` lo hace con subagentes en segundo plano).
Reglas completas: [AGENTS.md](AGENTS.md), sección *Parallel lanes*.
