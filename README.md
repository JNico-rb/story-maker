# story-maker

Novelas personalizadas de regalo, ambientadas en un presente alternativo **post-IA**. El cliente cuenta en una entrevista quién es el destinatario, sus allegados, sus recuerdos, la ocasión y el tono; el sistema escribe una novela de 10 capítulos donde el destinatario es el protagonista, comprueba su coherencia —con verificación formal en Lean 4 de la cronología— y la entrega para leer en web y en PDF. El lector puede pedir un cambio y solo se reescriben los capítulos afectados.

Es el proyecto del examen de Harness Engineering: el encargo está en [project-constraints.md](project-constraints.md) y la spec inicial en [ADR 0006](docs/adr/0006-diseno-lean.md).

## Cómo se usa

- **Configuración:** entrevista por la CLI (`interview`), con texto libre del que se extraen hechos, detección de datos que faltan y contradicciones, y un brief validado con schema.
- **Generación:** tras confirmar el brief, la web muestra el progreso capítulo a capítulo hasta el gate.
- **Lectura:** web (entrar, índice, ficha de personajes y lugares, versiones, pedir un cambio, editar un capítulo a mano) y PDF interactivo con portada, dedicatoria, índice y ficha enlazados.
- El desarrollo va spec a spec; el estado, en [TODO.md](TODO.md) → *Estado*.

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

Las órdenes que crean novelas reciben `--email` de un cliente ya registrado (en la web, `POST /api/auth/register`), que es su propietario.

### Brief de ejemplo reproducible

[ejemplos/briefs/01-ejemplo.json](ejemplos/briefs/01-ejemplo.json) → novela publicada → PDF (desde `backend/`, con el servidor parado: la orden monta su propio worker sobre la misma base):

```sh
uv run story-maker example ../ejemplos/briefs/01-ejemplo.json --email <cliente registrado>   # → ejemplos/novela-ejemplo.pdf (o --out <ruta>)
```

Una novela completa tarda del orden de 1–1,5 h con el login de Claude Code.

### Entrevista con el cliente

```sh
uv run story-maker interview --email <cliente registrado> [--novel <id>]
```

`--novel` retoma una entrevista guardada propia; sin él, empieza una novela nueva.

Cada línea es un turno. `/texto <fichero>` manda una carta o anécdota al extractor (contenido no confiable); `/hechos`, `/aceptar`, `/rechazar` y `/obligatorio` gobiernan los hechos extraídos; `/confirmar` cierra el brief y, con una segunda confirmación, lanza la generación; `/salir` termina.

### Pruebas y verificación formal

| Qué | Orden |
|---|---|
| Backend (desde `backend/`) | `uv run pytest` · `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy src` |
| Frontend (desde `frontend/`) | `pnpm.cmd lint` · `pnpm.cmd typecheck` · `pnpm.cmd test` · `pnpm.cmd build` |
| TLA+ con TLC (modelo pequeño: 5 capítulos, 2 reintentos) | `bash tla/verificar.sh` — configs en [tla/](tla/), instrucciones en [tla/README.md](tla/README.md) |
| Lean 4 (cronología, T1–T5) | en GitHub Actions: `.github/workflows/ci.yml` y `verificar-cronologia.yml`; detalle en [lean/README.md](lean/README.md) |

Los contraejemplos de TLC encontrados en el desarrollo y el cambio que provocaron están en `docs/verification.md` §8.

### Langfuse

En `.env`: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (Cloud UE) y `LANGFUSE_PROMPT_LABEL`. Una sesión por novela (entrevista, generación y regeneraciones); spans por rol, tool, validador y capítulo; los validadores, como scores de la traza. Los prompts versionados se suben con `uv run story-maker prompts push`.

### Órdenes de la CLI

| Orden | Qué hace |
|---|---|
| `init-db [--reset]` | Crea la base con el esquema completo; sin `--reset` no toca una existente |
| `check-env` | Una línea por comprobación: ajustes, config, base y observabilidad |
| `serve` | La API, la SPA compilada y el worker de la cola, en un proceso (sin `--reload`) |
| `interview --email <e> [--novel <id>]` | La entrevista por terminal, con confirmación explícita del brief y de la generación; `--novel` retoma una guardada propia |
| `resume <run_id>` | Vuelve a encolar una ejecución `interrupted` en su puesto |
| `export-pdf <novel> <v>` | Regenera el PDF de una versión publicada |
| `example <brief.json> --email <e> [--out <ruta>]` | Brief → novela publicada → su PDF |
| `change <novel_id> <petición> --email <e> [--fact <id> \| --chapter <n> --fragment <cita>]` | Propone un cambio del lector sobre un hecho o un fragmento y, tras confirmarlo, lo encola |
| `evals run --email <e>` | Importa los 5 briefs de `ejemplos/briefs/`, una novela y una ejecución por brief, y procesa la cola; no repite un brief que ya tiene novela del cliente; nunca en CI |
| `evals table` | La tabla brief × validador y el resumen por brief, desde SQLite |
| `prompts push` | Sube a Langfuse el prompt de cada rol cuya huella cambió, con la etiqueta `LANGFUSE_PROMPT_LABEL` |
| `report metrics [--out <ruta>]` | Agrega `role_sessions` y `validator_results` en un Markdown determinista y sin red; por defecto `docs/metrics.md` |

## Cómo verificar esta entrega

Cada afirmación del proyecto tiene un sitio donde comprobarla. Sin modelo ni cuota: todo lo de esta tabla corre en local o está en el repo.

| Requisito del encargo | Evidencia | Cómo se comprueba |
|---|---|---|
| Harness: planner, writer, editor, juez; tools con schema; reintentos acotados | `backend/src/story_maker/pipeline/`, `agents/`; `config.json` → `max_retries` | `cd backend && uv run pytest` (la suite usa el doble falso del puerto de agente) |
| `CLAUDE.md` de producto, skill y dos hooks (validación y policy) | [backend/harness_workspace/](backend/harness_workspace/) | `docs/architecture.md` §7.3 y §7.5 |
| Story bible en SQLite con uso de hechos por capítulo y cronología | `backend/src/story_maker/store/models.py` | `docs/architecture.md` §15.6 (esquema) |
| Palabras prohibidas en tres niveles, normalizadas (acentos, plurales, leetspeak) | `domain/banned_terms.py`, `policy/engine.py` | `uv run pytest tests/domain/test_banned_terms.py tests/policy` |
| Texto libre no confiable e inyección | `interview/free_text.py`, `policy/injection.py` | `uv run pytest tests/api/test_free_text_injection.py`; caso real: 3 flags del brief 4 (`docs/verification.md` §4.9, RT1) |
| Audit log del policy engine | `policy/audit.py` | `uv run pytest tests/policy/test_audit_log.py` |
| Validador formal de la historia (Lean 4, T1–T5 con demostraciones generales) | [lean/](lean/) | CI: `.github/workflows/verificar-cronologia.yml`; caso real en [ejemplos/cronologias/](ejemplos/cronologias/) y `docs/verification.md` §4.2 (e) |
| Validador formal del sistema (TLA+, TLC con 5 capítulos y 2 reintentos) | [tla/](tla/) | `bash tla/verificar.sh`; correspondencia acción ↔ código en [la tabla de abajo](#correspondencia-tla--código) |
| Cinco briefs de evals (adversarial y temporal incluidos) y su tabla | [ejemplos/briefs/](ejemplos/briefs/) | `uv run story-maker evals table` (lee SQLite); capturada en `docs/verification.md` §4.2 (a) y (b) |
| Iteración de tuning con antes y después | prompts `writer` v1 → v2 → v3 en Langfuse | `docs/verification.md` §4.2 (c) y §8 |
| Tokens, coste y latencia por novela (Langfuse) | `observability/` | `docs/verification.md` §4.2 (b): 3,25–4,83 USD por novela; pico de 21,7k–28,2k tokens concurrentes, bajo el techo de 100k |
| Login con SQLite y aislamiento entre clientes (opcional) | `api/auth.py` | `uv run pytest tests/api/test_ownership.py tests/api/test_auth.py` |
| Proceso: specs, plan, TDD, carriles | [specs/](specs/), [TODO.md](TODO.md), [AGENTS.md](AGENTS.md) | `awk -f .claude/scripts/resumen-todo.awk TODO.md` |

**Estado de la generación real.** Cuatro de las cinco evals escriben los 10 capítulos y llegan al gate de publicación; la quinta agota los reintentos de un capítulo antes. El gate no ha publicado ninguna todavía: Lean o el juez encuentran una incoherencia que las reescrituras no resuelven dentro del límite, y el sistema se detiene en lugar de entregar una novela que se contradice. La novela de ejemplo es la candidata de la ejecución 16; el detalle y la siguiente iteración, en `docs/verification.md` §4.2 (b).

## Mapa de entregables del encargo

| Entregable | Dónde vive |
|---|---|
| Spec inicial | [docs/adr/0006-diseno-lean.md](docs/adr/0006-diseno-lean.md) |
| Trade-offs (opciones, criterio, elección) | [docs/architecture.md](docs/architecture.md) §18 |
| Explainers, uno por concepto del curso | `docs/architecture.md` §16 |
| Diagramas: arquitectura del harness · máquina de estados · esquema SQLite · validadores con su punto de ejecución | `docs/architecture.md` §1.4 · §9.1 (y `tla/`) · §15.6 · §11.2 |
| Evals con resultados medibles | [docs/verification.md](docs/verification.md) §4.2 |
| Registro de iteraciones | `docs/verification.md` §8 |
| Cinco briefs de prueba (adversarial y temporal incluidos) | [ejemplos/briefs/](ejemplos/briefs/) |
| Red-team log | `docs/verification.md` §4.9 |
| Harness de producto: `CLAUDE.md`, skill y dos hooks | `backend/harness_workspace/`; `docs/architecture.md` §7.3 y §7.5 |
| Verificación formal: Lean 4 · TLA+ | [lean/](lean/) · [tla/](tla/) |
| Novela de ejemplo | [ejemplos/novela-ejemplo.pdf](ejemplos/novela-ejemplo.pdf): los 10 capítulos generados con el brief de ejemplo (ejecución real 16), candidata que el gate no llegó a publicar (`docs/verification.md` §4.2 b); candidatas de los briefs 2 y 3 en [ejemplos/novela/](ejemplos/novela/) |
| Lean detecta lo que los demás no | [ejemplos/cronologias/](ejemplos/cronologias/): los ficheros reales que generó el gate — el brief 1 falla T2, el editor reescribe y la segunda cronología pasa T1–T5; análisis en `docs/verification.md` §4.2 |
| Revisión humana frente al juez | [ejemplos/revision-humana-brief1.md](ejemplos/revision-humana-brief1.md), misma rúbrica que `juez-novela`; la comparación, en `docs/verification.md` §4.2 (d) |
| Presentación y vídeo de demo | [presentacion/](presentacion/) |
| Claude Code: `CLAUDE.md`, `.claude/` (agentes, comandos, hooks, skills, memoria), `.mcp.json` con browser MCP | [CLAUDE.md](CLAUDE.md), [.claude/](.claude/), [.mcp.json](.mcp.json); su uso, en `docs/verification.md` §9 |
| Sin claves en el repo | [.env.example](.env.example); la CI pasa `detect-secrets`, `pip-audit` y `pnpm audit` |

### Opcionales del encargo entregados

| Opcional | Qué hay | Evidencia |
|---|---|---|
| Login de usuarios con SQLite | Registro e inicio de sesión con bcrypt y JWT; cada novela, brief y entrada del audit log tiene propietario; lo ajeno responde 404 | spec 002; `backend/tests/api/test_ownership.py`, `test_auth.py`, `test_audit_log.py` |
| Invariantes adicionales en Lean y demostraciones generales | Cinco invariantes (T1–T5, tres más de los exigidos) y teoremas que prueban cada comprobación correcta y completa **para cualquier cronología** | [lean/Chronology.lean](lean/Chronology.lean), [lean/README.md](lean/README.md) |
| TLA+ de la concurrencia entre regeneraciones | `Regenerations.tla`: cambios del lector simultáneos sobre la misma novela, invariante `VersionesLineales` | [tla/Regenerations.tla](tla/Regenerations.tla), su prueba en `backend/tests/pipeline/changes/test_change_stale_base.py` |
| Linters de prosa | Repetición y muletillas, legibilidad según el tono, estilo típico de IA y consistencia de narrador y tiempo verbal; conectados al bucle de escritura y a la edición manual | `backend/src/story_maker/lint/`, `pipeline/production.py:ChapterProducer._lint`, `pipeline/manual_edit/live_lint.py` (spec 018) |
| Servidor MCP, de lectura y de escritura | Siete tools en `/mcp` (§*Servidores MCP*): cinco de lectura y dos de escritura (proponer y confirmar un cambio del lector), con la misma identidad JWT que `/api` y una fila de traza por llamada | [backend/src/story_maker/api/mcp/](backend/src/story_maker/api/mcp/) (spec 015) |
| Linter propio para la edición manual | El editor de capítulos de la web señala en vivo palabras prohibidas, formas no canónicas y avisos de los linters de prosa; un guardado que cambia un hecho actualiza la story bible y repasa los validadores (Lean incluido) antes de publicar | `pipeline/manual_edit/`, `frontend/src/pages/chapter-editor` (specs 019 y 028) |
| Seguridad con agentes (parcial) | Subagente `seguridad` definido; `detect-secrets`, `pip-audit` y `pnpm audit` en cada push. El informe `docs/security-report.md` lo genera la spec 021, pendiente | [.claude/agents/seguridad.md](.claude/agents/seguridad.md), `.github/workflows/ci.yml` |

### Límites del encargo, en código

- **100.000 tokens concurrentes:** `token_ceiling` en `config.json`, con un techo de reservas y una cola FIFO para las sesiones de rol (`backend/src/story_maker/agents/ceiling.py`); un valor por encima se rechaza al arrancar. El pico medido por ejecución sale en `evals table` (entre 11,7k y 28,2k en las evals reales).
- **Reintentos acotados:** `max_retries` por capítulo, plan, ciclos del gate y cambio, y `max_resumes`; al agotarlos la ejecución termina en `failed` con su motivo (invariante `ReintentosAcotados` de TLA+).

## Correspondencia TLA+ ↔ código

Cada acción de `tla/Harness.tla` corresponde a una transición del orquestador o de la API (`docs/architecture.md` §9.1). `tla/Regenerations.tla` usa las mismas acciones —`PedirCambio`, `Regenerar` (con la revalidación de la base de §10.2), `Fallar` (también `stale_base`), `Publicar`, `Caer` y `Reanudar`— y remite a sus filas; su invariante es `VersionesLineales`. La columna Código se rellena al cerrar cada spec implementadora y la revisa el `verificador` (`docs/verification.md` §4.10).

| Acción TLA+ | Transición (§9.1, como la modela la 006) | Quién la dispara | Spec del código | Código |
|---|---|---|---|---|
| `Configurar` | → `queued` (generation, candidata vacía) | API: `POST /api/novels/{id}/runs` con el brief confirmado | 011 (API de ejecuciones) | `pipeline/queue.py:enqueue_generation`, `api/runs.py:launch_generation` |
| `Planificar` | `queued` → `running`, `planning`; relanzada: → `writing` (capítulo k+1) o `gate` | Worker: toma la primera de la cola y abre el planner o sigue desde el punto de control | 011 (worker), 010 (planner) | `composition.py:build_worker` (031: el worker que monta `serve`), `pipeline/worker.py:Worker.run_forever`, `pipeline/worker.py:Worker._take_first`, `pipeline/orchestrator.py:Orchestrator._advance`, `pipeline/planning/phase.py:run_plan_phase`, `pipeline/planning_seam.py` (031: brief confirmado → entrada del planner) |
| `Regenerar` | `queued` → `running`, `writing` del primer afectado, con la candidata copiada de la base revalidada; relanzada: como `Planificar`, revalidando la base | Worker | 014 (cambio) | `pipeline/orchestrator.py:Orchestrator._change`, `pipeline/changes/run.py:revalidate_base`, `pipeline/changes/run.py:start_change` (candidata copiada de la base en una transacción), `pipeline/changes/run.py:revise_affected` |
| `EscribirCapitulo` | `writing` o `rewriting`: entrega del capítulo en curso | Orquestador, sesión del writer (en un fallo de datos del gate, el editor vuelve a registrar sin writer) | 011; en `rewriting`, 012 | `pipeline/production.py:ChapterProducer._write`, `pipeline/production.py:ChapterProducer._accept`, `pipeline/gate/phase.py:Gate._rewrite`; el re-registro del editor sin writer, que dispara un fallo de datos de `revision-visual` (017): `pipeline/gate/phase.py:Gate._reregister`, `pipeline/gate/reregister.py:reregister_chapter` |
| `Validar` | pasa: plan aplicado (punto de control 0), capítulo aceptado (con punto de control en `writing`) o gate superado; falla: defectos, o `gate` → `rewriting` con los capítulos atribuidos | Validador `outline`; hooks, editor y veredicto; validadores del gate | 010 (`outline`), 011, 012 (gate) | `pipeline/planning/apply.py:apply_accepted_plan`, `pipeline/acceptance.py:accept_chapter`, `pipeline/gate/precedence.py:gate_precedence` |
| `Reintentar` | defectos → nuevo intento del mismo evaluable; `rewriting` → `gate` con los atribuidos aceptados | Orquestador, con la guarda de `max_retries.*` | 010, 011, 012 | `pipeline/planning/phase.py:run_plan_phase`, `pipeline/production.py:ChapterProducer.produce_chapter`, `pipeline/gate/phase.py:Gate.__call__` |
| `Gate` | `writing` → `gate`, sin capítulos por escribir | Orquestador | 012 | `pipeline/orchestrator.py:Orchestrator._advance`, `pipeline/gate/phase.py:Gate._start_pass` |
| `Publicar` | `gate` superado → `published`; versión siguiente; solicitud o edición `applied` | Transacción de publicación (§9.3) | 012 | `pipeline/gate/phase.py:Gate._publish`, `pipeline/gate/publication.py:publish_candidate`; la solicitud `applied`: `pipeline/gate/publication.py:mark_applied`, también para la edición manual (019) |
| `Fallar` | `running` (o `queued` con base obsoleta, en `Regenerations.tla`) → `failed`; candidata `discarded`; solicitud o edición `rejected` | Límite agotado, fallo no atribuible, `edit_rejected`, `stale_base`, caída con `max_resumes` agotado | 010, 011, 012, 014, según el motivo | `pipeline/runs.py:fail_run`, `pipeline/planning/phase.py:run_plan_phase`, `pipeline/production.py:ChapterProducer.produce_chapter`, `pipeline/gate/phase.py:Gate.__call__`; `stale_base`: `pipeline/changes/run.py:revalidate_base`, y la solicitud `rejected` en `pipeline/runs.py:fail_run`; `edit_rejected` (019): `pipeline/manual_edit/gate.py:edit_rejection` |
| `Caer` | `running` → `interrupted` | Error del proveedor, verificador inalcanzable o agotado, arranque con la ejecución en `running` | 011 (caída y arranque), 012 (verificador) | `pipeline/runs.py:interrupt_run`, `pipeline/runs.py:interrupt_running_at_startup` (vía `pipeline/worker.py:Worker.recover`, al arrancar el worker de `composition.py:build_app`, 031), `pipeline/runs.py:stop_run` |
| `Reanudar` | `interrupted` → `queued`, en su puesto original | `POST /api/runs/{id}/resume` o `story-maker resume` | 011 (API y CLI) | `pipeline/runs.py:resume_run`, `api/runs.py:resume`, `cli.py:resume_command` |
| `PedirCambio` | → `queued` (change_request o manual_edit, con la vigente como base) | API: confirmar un cambio con su código, o guardar una edición manual | 014, 019 | `pipeline/changes/confirm.py:confirm_change`, `api/change_requests.py:post_confirm`; `pipeline/manual_edit/save.py:save_edit`, `api/manual_edit.py:put_chapter` |

## Servidores MCP

**Del producto (spec 015).** `story-maker serve` monta un servidor MCP propio en `/mcp` con siete tools: cinco de lectura (`list_novels`, `list_versions`, `get_chapter`, `query_story_bible`, `download_novel`) y dos de escritura, para pedir un cambio del lector desde un cliente MCP (`request_change`, que solo propone, y `confirm_change`, que lo encola con el código de la propuesta). Se conecta como un servidor `http` (streamable-http), con la misma identidad que `/api`: la cabecera `Authorization: Bearer <token>` de `POST /api/auth/login`, sin la cual la petición recibe 401 antes de llegar al protocolo MCP. Cada llamada deja una traza `mcp:<tool>` en Langfuse; las de escritura, además, una fila de auditoría.

**Para el desarrollo**, `.mcp.json` ya trae Playwright MCP (Edge) y el MCP de Langfuse; este último lee la cabecera de la variable de entorno `LANGFUSE_MCP_AUTH` (`Basic <base64 de public_key:secret_key>`), que se define en el entorno del usuario, nunca en el repo. El mismo Playwright MCP (Edge) lo usa en tiempo de ejecución el validador `revision-visual` del gate (spec 017): sin Edge instalado, esa etapa interrumpe la ejecución en vez de fallar en silencio.

## Trabajo en paralelo

El desarrollo va en carriles: un worktree hermano por carril (`../sm-<x>`, rama `carril-<x>`), cada uno con su terminal de Claude Code y sus specs en orden.
El checkout principal (V2) es el integrador: escribe specs y planes por delante, integra con `git merge --no-ff` cada spec cerrada y mantiene la tabla de carriles de `TODO.md`.
Sin revisiones (decisión del usuario, 2026-09-24): el integrador escribe y marca specs y planes, y `verificador` cierra cada spec.
Para empezar, abre Claude Code en el checkout principal y ejecuta `/orquestar`: dice qué terminales abrir y en qué orden (`/orquestar sin-terminales` lo hace con subagentes en segundo plano).
Reglas completas: [AGENTS.md](AGENTS.md), sección *Parallel lanes*.
