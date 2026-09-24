# 001 — Base

> Carril: A · Depende de: 000 · Estado: borrador

## Objetivo

Dar a los demás carriles la base común del backend: la config y los ajustes del servidor, validados al arrancar; el **esquema SQLite completo**, que es el contrato de datos entre carriles; la API mínima, que sirve también la SPA compilada; las órdenes `serve`, `init-db` y `check-env`; las constantes del encargo; y el **puerto de observabilidad con su doble nulo**. Son los dos contratos que `architecture.md` §15.9 hace nacer en esta spec. Nada de esto genera una novela ni llama a un modelo.

`.env.example` existe desde antes que esta spec: se verifica contra C5 y se corrige lo que no cumpla.

Excepción declarada: `config.json`, `.env`, `.env.example`, las órdenes de `story-maker`, las rutas HTTP y las tablas y columnas de SQLite son la interfaz del producto con quien lo instala y con los demás carriles (`architecture.md` §15.4–§15.8), así que se nombran. `architecture.md` §15.6 deja a esta spec el detalle por columna.

## Alcance

- **Config**: `config.json` en la raíz del repositorio (ruta en `STORY_MAKER_CONFIG`), con las claves y los valores de `architecture.md` §15.4, validada entera al arrancar (`definitions.md` §11.1).
- **Ajustes del servidor** (`definitions.md` §11.3, `architecture.md` §15.5): lectura del entorno y del `.env` de la raíz, valores por defecto, ajustes obligatorios y condicionales, y `.env.example`.
- **Esquema SQLite completo** (`architecture.md` §15.6): las 31 tablas con sus columnas (tabla de C6), referencias, enumerados, unicidades, tablas de solo inserción, el índice FTS5 de las CanonCards y el canal denso de vectores disponible en cada conexión, y la unidad de trabajo transaccional.
- **Órdenes** `init-db`, `check-env` y `serve` (`architecture.md` §15.8).
- **API mínima**: salud en `GET /health` y esquema OpenAPI en `GET /openapi.json` (los dos fuera de `/api`, sin token, para que `gen:api` los lea sin credenciales), forma de los errores de `/api` y la SPA compilada en el mismo origen (`architecture.md` §14.8, §15.7).
- **Puerto de observabilidad y doble nulo** (`architecture.md` §13, §15.9): lo que se puede emitir (trazas, spans, llamadas de modelo, scores, prompts versionados, comprobación y vaciado) y lo que el doble captura.
- **Constantes del encargo** (`definitions.md` §11.2): 10 capítulos, de 1.000 a 1.500 palabras por capítulo y 100.000 tokens concurrentes. Además, los identificadores que valida la config: los siete roles (`definitions.md` §12.2), los criterios de las dos rúbricas (§6) y las `FranjaDeEdad` (§12.4).
- **README**: la sección de arranque (`.env`, `config.json`, `init-db`, `check-env`, `serve`). La escribe el integrador con el texto que le entrega el carril.
- **Primera generación** de los tipos del frontend con `gen:api` (000-scaffolding, fuera de alcance).

## Fuera de alcance

- `--version`, subpaquetes y regla de dependencias de `domain` → 000-scaffolding (000-C03, 000-C05).
- Registro, acceso, `TokenDeAcceso`, el 401 sin token y el 404 de lo ajeno → 002-autenticacion.
- Puerto de agente y su doble falso; `TechoDeTokens` (reserva, espera, 503, `infeasible_config`); entorno del CLI de Claude Code (traducción de `OPENROUTER_API_KEY`, `CLAUDE_CODE_DISABLE_*`, sin redefinir `CLAUDE_CONFIG_DIR`) → 003-puerto-de-agente.
- Adaptador de Langfuse, `auth_check()` real en el arranque y en `check-env`, `Mascara`, `prompts push`, nombres de trazas, spans y scores, y cuándo se usa el adaptador en vez del doble nulo (con lo que eso exija de las variables de Langfuse) → 004-observabilidad.
- Siembra de la lista global de prohibidas, forma normalizada, `MotorDePoliticas` y escritura del `AuditLog` → 005-guardarrailes.
- Catálogos y reglas del brief (objetivo de palabras de cada `Extension`, `FranjaDeEdad` según la edad, C1–C6, vocabulario de atributos) → 008-brief-y-entrevista.
- Repositorios de la story bible, copia de versión e inmutabilidad de la versión publicada → 009-story-bible-y-versiones.
- Los 3–6 beats por capítulo y las 2–4 consecuencias → 010-planificacion.
- Cola, worker, `running` → `interrupted` al arrancar el servidor, reanudación y rutas de ejecuciones → 011-produccion-de-capitulos.
- Qué juzga cada criterio y cuáles bloquean → 011-produccion-de-capitulos (rúbrica de capítulo) y 012-gate-de-publicacion (rúbrica de novela, `CatalogoDeTropos`).
- `/view` y el PDF → 013-lectura-y-pdf; `/mcp` → 015-servidor-mcp; BM25, denso y RRF sobre el índice y los vectores → 016-recuperacion-hibrida.
- Resto de órdenes: `example` y `export-pdf` → 013; `resume` → 011; `evals` → 020; `prompts push` → 004.
- Regenerar los tipos del frontend tras cada cambio de la API → `/integrar`.

## Comportamiento observable

Un caso es **T** si una prueba lo decide sola, con ajustes de fixture, la base en un directorio temporal y el doble nulo; es **D** si necesita pnpm, un clon limpio o una persona. `<raíz>` es la raíz del repositorio.

### Config y ajustes

#### C1 — El `config.json` del repositorio es válido y lleva los valores de §15.4 (T)

- **Entrada:** el `config.json` de la raíz.
- **Salida:** pasa la validación de C2 y sus valores son los de `architecture.md` §15.4: `operation.token_ceiling` 100000; `api_wait_seconds` 30; `max_retries` 3 (`chapter`), 2 (`plan`), 2 (`gate_cycles`) y 2 (`change`); `max_resumes` 3; `session_timeout_seconds` 600; `verifier_timeout_seconds` 900; `max_mandatory_elements` 8; `access_token_hours` 24; `confirmation_minutes` 15; `claude-sonnet-5` en `planner`, `writer` y `judge`, y `claude-haiku-4-5` en `interviewer`, `extractor`, `editor` y `visual_reviewer`; `max_turns` y `max_output_tokens` de cada rol según §15.4 (`interviewer`: 4 y 2000); los precios de los dos modelos; umbral 3 en cada criterio; los objetivos de legibilidad de cada franja según §15.4 (`children`: 12 y 80); `retrieval.top_k` 8 y 8; y un `retrieval.embedding_model`.
- Los criterios son los diez identificadores de `definitions.md` §6. `tono` y `personalizacion-natural` están en las dos rúbricas y tienen un solo umbral.

#### C2 — La config se valida entera y nombra cada clave que falta, sobra o no vale (T)

| Config (la de C1 salvo lo indicado) | Resultado |
|---|---|
| Sin cambios | válida |
| `operation.token_ceiling` = 100000 | válida |
| `operation.token_ceiling` = 100001 | rechazo: nombra `operation.token_ceiling` y el máximo 100000 |
| `operation.token_ceiling` = 5000 | válida: las pruebas usan techos menores (`architecture.md` §1.3) |
| `operation.token_ceiling` = 0 | rechazo |
| Sin `operation.roles.judge` | rechazo: nombra la clave que falta |
| Con `operation.roles.narrator`, que no es uno de los siete roles | rechazo: clave desconocida |
| `operation.roles.writer.model` con un modelo sin entrada en `operation.pricing` | rechazo: nombra el modelo sin precio |
| Precio de un modelo que ningún rol usa | válida |
| Un precio sin `cache_write`, o con un valor negativo | rechazo |
| Un precio con `input` = 0 | válida: 0 no es negativo |
| Sin `quality.thresholds.continuidad` | rechazo |
| `quality.thresholds.tono` = 1 o 5 | válida |
| `quality.thresholds.tono` = 0 o 6 | rechazo: el umbral va de 1 a 5 |
| Sin `quality.readability_targets.teen` | rechazo |
| `quality.readability_targets.children.sentence_length` = 0, o `.fernandez_huerta` = 0 | rechazo |
| `operation.max_retries.chapter` = 0 | válida |
| `operation.max_retries.chapter` = −1 | rechazo |
| `operation.max_resumes` = 0 | válida |
| `operation.max_resumes` = −1 | rechazo |
| `operation.roles.editor.max_turns` = 0, o `max_output_tokens` = 0 | rechazo |
| `api_wait_seconds`, `session_timeout_seconds`, `verifier_timeout_seconds`, `access_token_hours`, `confirmation_minutes`, `max_mandatory_elements` o un `retrieval.top_k` a 0 | rechazo |
| `retrieval.embedding_model` vacío | rechazo |
| Una clave desconocida (`operation.max_retry`) | rechazo: la nombra |
| Un fichero que no es JSON | rechazo con la ruta y la posición del error |
| `STORY_MAKER_CONFIG` apunta a un fichero que no existe | rechazo con la ruta |
| Varios errores a la vez | todos en el mismo informe, uno por clave |

#### C3 — Ajustes: valores por defecto, rutas desde la raíz y precedencia del entorno (T)

| Entrada | Salida |
|---|---|
| Solo `JWT_SECRET` (32 caracteres) y `FORMAL_VERIFIER=local`, con el directorio actual en `<raíz>` | directorio de datos `<raíz>/backend/data`; config `<raíz>/config.json`; URL base `http://127.0.0.1:8000`; compilado del frontend `<raíz>/frontend/dist`; `LLM_PROVIDER` = `claude_login` |
| Lo mismo con el directorio actual en `<raíz>/backend` | el mismo resultado |
| `STORY_MAKER_DATA_DIR=tmp/datos` | `<raíz>/tmp/datos`; una ruta absoluta se toma tal cual (igual `STORY_MAKER_CONFIG` y `STORY_MAKER_FRONTEND_DIST`) |
| Una variable presente pero vacía (`STORY_MAKER_CONFIG=`) | cuenta como ausente: se usa su valor por defecto |
| `.env` de la raíz con `JWT_SECRET=<A>` y el entorno con `JWT_SECRET=<B>` | vale `<B>`: el entorno prevalece |
| Sin `.env` | se leen solo las variables del entorno |

#### C4 — Ajustes obligatorios y condicionales (T)

Partiendo de la entrada válida de C3:

| Entorno | Resultado |
|---|---|
| Sin `JWT_SECRET` | rechazo: nombra `JWT_SECRET` |
| `JWT_SECRET` de 31 caracteres | rechazo: nombra `JWT_SECRET` y el mínimo de 32, sin mostrar el valor |
| `JWT_SECRET` de 32 caracteres | válido |
| Sin `FORMAL_VERIFIER` | rechazo: no tiene valor por defecto |
| `FORMAL_VERIFIER` con otro valor | rechazo con los admitidos, `local` y `github` |
| `FORMAL_VERIFIER=github` sin alguno de `GITHUB_REPOSITORY`, `LEAN_WORKFLOW` o `GITHUB_TOKEN` | rechazo: nombra cada uno que falta |
| `FORMAL_VERIFIER=github` con los tres | válido |
| `FORMAL_VERIFIER=local` sin ninguno de los tres | válido |
| `LLM_PROVIDER` con otro valor | rechazo con los admitidos, `claude_login` y `anthropic_compatible` |
| `LLM_PROVIDER=anthropic_compatible` sin `ANTHROPIC_BASE_URL` y `ANTHROPIC_AUTH_TOKEN` ni `OPENROUTER_API_KEY` | rechazo: nombra las dos formas de dar credenciales |
| `LLM_PROVIDER=anthropic_compatible` con `ANTHROPIC_BASE_URL` y `ANTHROPIC_AUTH_TOKEN` | válido |
| `LLM_PROVIDER=anthropic_compatible` solo con `OPENROUTER_API_KEY` | válido |
| `LLM_PROVIDER=claude_login`, o sin la variable, sin credenciales de proveedor | válido: `CLAUDE_CODE_OAUTH_TOKEN` es opcional |
| `STORY_MAKER_BASE_URL` que no es `http://` con host y puerto (`ftp://x`, `http://127.0.0.1`) | rechazo |
| Sin ninguna variable de Langfuse | válido |

#### C5 — `.env.example` lista los ajustes sin valores (T)

- **Entrada:** el `.env.example` de la raíz.
- **Salida:** cada una de las 18 variables de `architecture.md` §15.5 que lee el backend aparece una vez, y ninguna más: `STORY_MAKER_DATA_DIR`, `STORY_MAKER_CONFIG`, `STORY_MAKER_BASE_URL`, `STORY_MAKER_FRONTEND_DIST`, `JWT_SECRET`, `LLM_PROVIDER`, `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `OPENROUTER_API_KEY`, `FORMAL_VERIFIER`, `GITHUB_REPOSITORY`, `LEAN_WORKFLOW`, `GITHUB_TOKEN`, `LANGFUSE_PROMPT_LABEL`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_PUBLIC_KEY` y `LANGFUSE_BASE_URL`. Son exactamente los nombres que leen los ajustes: la prueba compara las dos listas.
- Todas van vacías. Un comentario da el valor por defecto de las que lo tienen.
- `LANGFUSE_MCP_AUTH` aparece solo en un comentario, que dice que es de Claude Code en el desarrollo, que va en el entorno del usuario y que el backend no la lee.
- Copiado a `.env`, y con solo `JWT_SECRET` y `FORMAL_VERIFIER=local` rellenos, los ajustes son válidos (C3, C4).

### Esquema

#### C6 — `init-db` crea la base con el esquema completo (T)

- **Entrada:** `init-db` con un directorio de datos que no existe.
- **Salida:** crea el directorio y, dentro, un único fichero SQLite con las 31 tablas de abajo, con esos nombres y esas columnas y sin filas. Escribe la ruta del fichero y sale con 0.
- Cada tabla tiene además su `id` entero. `?` marca las columnas que admiten vacío. Las marcas de tiempo del sistema (`created_at`, `published_at`, `expires_at`, `finished_at`) van en UTC; las fechas de la ficción (`moment`, `birth_date`, `novum_date`) son de calendario, sin zona. `(JSON)` es un valor estructurado.
- Lo que `definitions.md` declara derivado o no guardado no tiene columna ni tabla: el estado de la `Novela`, `DatoFaltante`, `Contradiccion`, `InformeDeEjecucion`, `VentanaDeContexto`, la posición en la cola y el coste acumulado de una ejecución.

| Tabla | Ámbito (`architecture.md` §15.6) | Columnas |
|---|---|---|
| `users` | usuario | `email`, `password_hash`, `created_at` |
| `novels` | usuario | `user_id`, `title?`, `embedding_model`, `created_at` |
| `banned_terms` | global, usuario o novela | `level`, `user_id?`, `novel_id?`, `term`, `type`, `keywords?` (JSON), `normalized` |
| `audit_log` | usuario | `user_id`, `novel_id?`, `run_id?`, `role?`, `tool?`, `origin`, `decision`, `rule`, `detail` (JSON), `created_at` |
| `interviews` | novela | `novel_id`, `created_at` |
| `interview_messages` | novela, por su entrevista | `interview_id`, `author`, `text`, `created_at` |
| `briefs` | novela | `novel_id`, `content` (JSON), `status` |
| `free_texts` | novela | `novel_id`, `content`, `discarded_instructions` (JSON), `created_at` |
| `extracted_facts` | novela, por su texto libre | `free_text_id`, `subject`, `attribute`, `value`, `quote`, `verified`, `accepted?` (vacío mientras el cliente no decide), `mandatory` |
| `change_requests` | novela | `novel_id`, `base_version_id`, `selection_type`, `selection` (JSON), `request`, `proposal?` (JSON), `affected_chapters?` (JSON), `code_hash?`, `expires_at?`, `status`, `run_id?`, `created_at` |
| `manual_edits` | novela | `novel_id`, `base_version_id`, `chapter`, `text`, `status`, `run_id?`, `created_at` |
| `versions` | novela | `novel_id`, `status`, `number?`, `base_version_id?`, `changed_chapters` (JSON), `pdf_path?`, `created_at`, `published_at?` |
| `worlds` | versión | `version_id`, `novum_description`, `novum_scope`, `novum_date`, `consequences` (JSON) |
| `characters` | versión | `version_id`, `type`, `species`, `canonical_name`, `birth_date?`, `origin` |
| `places` | versión | `version_id`, `canonical_name`, `description`, `origin` |
| `facts` | versión | `version_id`, `subject_type`, `character_id?`, `place_id?`, `attribute`, `value`, `origin`, `mandatory`, `personal_element_id?` |
| `fact_usages` | versión, por su hecho | `fact_id`, `chapter` |
| `events` | versión | `version_id`, `statement`, `moment`, `place_id`, `type`, `excluded_character_id?`, `analepsis`, `origin`, `chapter?`, `beat?` |
| `event_characters` | versión, por su evento | `event_id`, `character_id`, `declared_age?` |
| `outline_chapters` | versión | `version_id`, `number`, `title`, `arc_function`, `beats` (JSON), `assigned_elements` (JSON) |
| `style_sheets` | versión | `version_id`, `content` (JSON) |
| `chapters` | versión | `version_id`, `number`, `title`, `text`, `summary`, `word_count`, `content_hash` |
| `canon_cards` | versión | `version_id`, `entity_type`, `character_id?`, `place_id?`, `from_chapter`, `text`, `content_hash` |
| `canon_cards_fts` | versión, por su tarjeta | índice FTS5 del `text` de `canon_cards`, con el tokenizador `unicode61 remove_diacritics 2` (`architecture.md` §6.3) |
| `embeddings` | global | `content_hash`, `model`, `vector` |
| `runs` | ejecución | `novel_id`, `type`, `status`, `phase?`, `chapter?`, `base_version_id?`, `candidate_version_id?`, `resumes`, `reason?`, `reason_detail?`, `created_at`, `finished_at?` |
| `attempts` | ejecución | `run_id?`, `change_request_id?`, `evaluable`, `chapter?`, `gate_cycle?`, `number`, `outcome?` |
| `checkpoints` | ejecución | `run_id`, `chapter`, `created_at` |
| `role_sessions` | ejecución, o novela fuera de ella | `novel_id`, `run_id?`, `role`, `chapter?`, `model`, `prompt_version?`, `reserved_tokens` (la reserva del `TechoDeTokens` al abrir la sesión, `architecture.md` §6.5.1; la calcula 003, esta spec solo declara la columna), `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `cost_usd`, `sdk_cost_usd?` (el `total_cost_usd` del SDK, solo como contraste, `architecture.md` §13.2), `latency_ms`, `outcome`, `trace_id?` |
| `validator_results` | ejecución | `run_id`, `version_id`, `validator`, `chapter?`, `passed`, `score?`, `detail` (JSON), `created_at` |
| `chronology_files` | ejecución | `run_id`, `content_hash`, `result`, `detail?` (JSON: invariante violado y testigo), `created_at` |

**Enumerados.** Cada columna de esta lista solo admite los valores del enumerado de `definitions.md` §12.4 que proyecta: `banned_terms.level` (nivel de `ListaProhibida`) y `.type` (tipo de `EntradaProhibida`); `briefs.status`; `worlds.novum_scope`; `facts.subject_type` y `canon_cards.entity_type`; `characters.type`, `.species` y `.origin`; `places.origin`; `facts.origin`; `events.type` y `.origin`; `versions.status`; `role_sessions.outcome`; `runs.type`, `.status` y `.phase`; `runs.reason` (motivo de fallo o de interrupción); `attempts.evaluable` y `.outcome`; `change_requests.selection_type` y `.status`; `manual_edits.status`; `audit_log.origin` y `.decision`; `chronology_files.result`. Además, `role_sessions.role` y `audit_log.role` solo admiten los identificadores de rol de §12.2, e `interview_messages.author` solo `user` (el `Cliente`) o `interviewer`.

#### C7 — `init-db` no pisa una base existente sin `--reset` (T)

| Entrada | Salida |
|---|---|
| `init-db` con la base ya creada | sale con 1 sin tocarla (la huella del fichero no cambia); el mensaje da la ruta y la opción `--reset` |
| `init-db --reset` con la base con filas | la borra y la crea de nuevo, con el esquema de C6 y sin filas; sale con 0 |

#### C8 — Toda conexión abre la base igual (T)

- **Entrada:** cualquier conexión a la base que abre el backend (desde `init-db`, desde `serve` o desde una prueba).
- **Salida:** diario en modo WAL, claves ajenas activas y una espera de 5 s ante una base ocupada. El canal denso está disponible: la distancia coseno entre (1, 0) y (0, 1) es 1, y la de (1, 0) consigo misma, 0. Con una escritura abierta en una conexión, otra lee el último estado confirmado sin error.
- Si el canal denso no se puede cargar, `check-env` y `serve` lo dicen (C14, C15).

#### C9 — Ámbito y referencias obligatorias (T)

| Entrada | Salida |
|---|---|
| Una fila de `novels` sin `user_id` | rechazo: una novela es siempre de su cliente (`verification.md` §5 O.16) |
| Una fila de `audit_log` sin `user_id` | rechazo |
| Una fila de ámbito versión con referencia directa (un personaje, un capítulo) sin `version_id` | rechazo |
| Un capítulo de una versión que no existe | rechazo por la clave ajena |
| Un `fact_usages` de un hecho que no existe, o un `event_characters` de un personaje que no existe | rechazo |
| Un `attempts` con `run_id` y `change_request_id` a la vez, o sin ninguno de los dos | rechazo |
| Una fila de `role_sessions` sin `novel_id` | rechazo |
| Una fila de `role_sessions` sin `run_id` | se admite: la entrevista, la extracción y la propuesta de un cambio no son ejecuciones |

#### C10 — Enumerados, rangos, unicidades y coherencia (T)

| Regla | Se rechaza | Se admite |
|---|---|---|
| Enumerados de C6 | `runs.status` = `paused`; `audit_log.decision` = `block`; `versions.status` = `draft`; `interview_messages.author` = `system`; `role_sessions.role` = `narrator` | cada valor de su enumerado |
| Número de capítulo de 1 a 10 (`chapters.number`, `outline_chapters.number`, `fact_usages.chapter`, `manual_edits.chapter`, `events.chapter`, `runs.chapter`, `attempts.chapter`, `role_sessions.chapter`, `validator_results.chapter`) | 0 y 11 | 1 y 10 |
| Punto de control de 0 (el plan) a 10 (`checkpoints.chapter`) | −1 y 11 | 0 y 10 |
| `canon_cards.from_chapter` ≥ 1; `attempts.number` ≥ 1; `runs.resumes` ≥ 0 | 0; 0; −1 | 1; 1; 0 |
| Una sola fila por clave: `users.email`; `briefs.novel_id` e `interviews.novel_id`; `worlds.version_id` y `style_sheets.version_id`; (versión, número) en `chapters` y en `outline_chapters`; (novela, número) en `versions`; (ejecución, capítulo) en `checkpoints`; (hecho, capítulo) en `fact_usages`; (evento, personaje) en `event_characters`; (versión, entidad, `from_chapter`) en `canon_cards`; (huella, modelo) en `embeddings`; `runs.candidate_version_id`; `change_requests.run_id`; `manual_edits.run_id` (una ejecución encola como mucho una solicitud de cambio o una edición manual, `architecture.md` §15.6, diagrama `|o--o|`) | la segunda fila con la misma clave | varias versiones `candidate` sin número en la misma novela |
| `versions`: número y fecha de publicación si y solo si está `published` | `published` sin número; `candidate` con número | `published` con número y fecha |
| `banned_terms` según su nivel | `user` sin usuario o con novela; `novel` sin novela o con usuario; `global` con usuario o con novela | los tres bien formados |
| Sujeto de `facts` y entidad de `canon_cards` según su tipo | `character` sin personaje o con lugar; `place` sin lugar; `world` con personaje o lugar | los tres bien formados |
| `events`: personaje excluido si y solo si es `exclusion` | `exclusion` sin excluido; `ordinary` con excluido | los dos bien formados |
| `runs.reason` | `stale` | `stale_base`, `crash` o vacío |

#### C11 — Solo inserción y CanonCards inmutables (T)

El rechazo lo decide el código, en la misma unidad de trabajo de C13, antes de tocar SQLite: ninguna regla de esta tabla depende de un disparador del motor (`architecture.md` §18 «Solo inserción y sincronía del índice FTS5»).

| Entrada | Salida |
|---|---|
| Modificar o borrar una fila de `audit_log`, `checkpoints` o `embeddings` | rechazo; la fila queda igual (`definitions.md` §5 `PuntoDeControl`, §7 `AuditLog`; `architecture.md` §15.6) |
| Insertar en esas tablas | se admite |
| Modificar una fila de `canon_cards` | rechazo: la tarjeta no se edita, se sucede (`architecture.md` §6.3) |
| Borrar una fila de `canon_cards` | se admite: volver a aceptar un capítulo sustituye sus sucesoras (`definitions.md` §4) |

#### C12 — El índice FTS5 sigue a las CanonCards, sin acentos (T)

| Entrada | Salida |
|---|---|
| Se añade una tarjeta con el texto «La canción de Toby» y se busca `cancion` en `canon_cards_fts` | la devuelve; también con `Canción` y con `CANCION` |
| Se borra esa tarjeta | la búsqueda ya no la devuelve |
| Una transacción añade una tarjeta y se deshace | no existen ni la tarjeta ni su entrada del índice: el índice y la story bible nunca discrepan (`architecture.md` §6.4) |

La sincronía la mantiene el código, dentro de la misma unidad de trabajo de C13 que escribe `canon_cards`: no hay disparadores del motor que la mantengan por su cuenta.

#### C13 — Una unidad de trabajo es todo o nada (T)

| Entrada | Salida |
|---|---|
| Una unidad de trabajo inserta un usuario y una novela suya, y falla antes de confirmar | no queda ninguna de las dos filas |
| La misma unidad sin fallo | quedan las dos |

### Órdenes y API

#### C14 — `check-env` informa de cada comprobación (T)

`check-env` escribe una línea por comprobación (ajustes, config, base de datos y observabilidad), con `ok` o con el fallo y su motivo. Hace también las comprobaciones que no dependen de una que ha fallado.

| Situación | Salida | Código |
|---|---|---|
| Ajustes de C3, config de C1 y base recién creada | las cuatro líneas en `ok`; la de observabilidad dice que es el doble nulo, sin Langfuse | 0 |
| `JWT_SECRET` de 31 caracteres | fallo de ajustes que nombra `JWT_SECRET` y su mínimo, sin su valor | 1 |
| Config con `operation.token_ceiling` = 150000 | fallo de config que nombra la clave y el máximo | 1 |
| Sin base en el directorio de datos | fallo de base de datos con la ruta y la orden `init-db` | 1 |
| Una base a la que le falta, o le sobra, una tabla o una columna del esquema de C6 | fallo de base de datos que las nombra y pide `init-db --reset` | 1 |
| El canal denso no carga | fallo de base de datos que lo dice | 1 |
| Varios fallos a la vez | todos, cada uno en su línea | 1 |

#### C15 — `serve` no arranca con config, ajustes o base inválidos (T)

- **Entrada:** `serve` en cualquiera de las situaciones de fallo de C14, o con una config o unos ajustes que C2 o C4 rechazan.
- **Salida:** escribe los mismos motivos que `check-env`, sale con 1 y no abre el puerto.

#### C16 — `serve` escucha en `STORY_MAKER_BASE_URL`, en un solo proceso (T)

| Entrada | Salida |
|---|---|
| Ajustes, config y base válidos, con `STORY_MAKER_BASE_URL=http://127.0.0.1:<puerto libre>` | escucha en ese host y ese puerto; `GET /health` responde como en C17 |
| Se para el servidor | vacía el puerto de observabilidad una sola vez y sale con 0 |
| `serve --reload` o `serve --workers 2` | error de opción desconocida, sin arrancar: un solo proceso y sin recarga (`architecture.md` §1.4, §15.3) |

#### C17 — Salud, esquema OpenAPI y errores de la API (T)

| Petición | Respuesta |
|---|---|
| `GET /health`, sin token | 200 `{"status": "ok", "version": "<versión del paquete>"}`, la misma versión que `--version`; fuera de `/api`, no exige `TokenDeAcceso` (002-I2 solo alcanza a `/api`) |
| `GET /openapi.json`, sin token | 200 con el esquema OpenAPI de toda la aplicación (un único proceso, `architecture.md` §1.4), que incluye `/health` aunque ninguno de los dos lleve el prefijo `/api`; así lo lee `gen:api` sin credenciales |
| `GET /api/no-existe` | 404 en JSON con `detail`, nunca el `index.html` de la SPA |

Todo error de la API es JSON con un campo `detail`, que es la forma que heredan los códigos 401, 404, 409, 422 y 503 de `architecture.md` §15.7.

#### C18 — La SPA compilada se sirve en el mismo origen sin tapar la API (T)

Con `STORY_MAKER_FRONTEND_DIST` apuntando a un compilado de prueba con `index.html` y `assets/app.js`:

| Petición | Respuesta |
|---|---|
| `GET /` | 200 con `index.html` |
| `GET /assets/app.js` | 200 con ese fichero |
| `GET /novelas/3`, una ruta del cliente que no es un fichero | 200 con `index.html` |
| `GET /api/x`, `GET /view/x` o `GET /mcp/x`, sin nada montado en esa ruta | 404, nunca `index.html`: `/view` es de 013-lectura-y-pdf y `/mcp`, de 015-servidor-mcp |
| Cualquier ruta, con `STORY_MAKER_FRONTEND_DIST` apuntando a un directorio que no existe | el servidor arranca; `GET /health` da 200; `GET /` da 404 |

### Puerto de observabilidad

#### C19 — El doble nulo captura lo emitido, sin red (T)

| Se emite por el puerto | El doble nulo captura |
|---|---|
| Una `Traza` con nombre y con la `Sesion` = id de la novela | la traza, con su nombre y su sesión |
| Una traza sin sesión (una llamada MCP que toca varias novelas, `architecture.md` §13.5) | la traza, sin sesión |
| Un `Span` dentro de la traza y otro dentro de ese, con metadatos (el capítulo) | cada span con su nombre, su padre y sus metadatos |
| Una `LlamadaDeModelo` dentro de un span, con modelo, versión de prompt, tokens de entrada, de salida, de lectura de caché y de escritura de caché, coste en USD y latencia | todos esos campos, sin cambios |
| Un `Score` con nombre, valor y comentario, asociado a la traza y, si se da, a un span | el score, con su traza y su span |
| La traza del mismo objeto dos veces (la misma ejecución, la misma entrevista) | una sola traza: lo emitido la segunda vez se añade a la primera, así que la ejecución reanudada conserva la suya (`architecture.md` §9.2, §13.1) |
| Trazas de dos objetos distintos, o dos trazas sin objeto | trazas distintas |

Todo queda en el orden de emisión y la prueba lo puede leer. El doble no usa la red ni lee credenciales ni variables de Langfuse (I3).

#### C20 — Niveles y excepciones de los spans (T)

| Se emite | El doble nulo captura |
|---|---|
| Un span con nivel WARNING y un motivo (una tool denegada, `architecture.md` §13.1) | nivel WARNING y el motivo |
| Un span sin nivel | el nivel normal |
| Un span cuyo bloque lanza una excepción | el span cerrado, con nivel ERROR y el mensaje de la excepción; la excepción llega intacta a quien abrió el span |

#### C21 — Prompts, comprobación y vaciado con el doble nulo (T)

| Operación | Resultado con el doble nulo |
|---|---|
| Pedir el `PromptVersionado` de un rol con una etiqueta | responde que no hay versión remota; qué hace entonces quien lo pide lo fijan 003-puerto-de-agente y 004-observabilidad |
| Comprobar la conexión | correcta, sin red |
| Vaciar | sin efecto, pero queda contado (lo mira C16) |
| El servidor de esta spec | usa siempre el doble nulo: arranca y opera sin variables de Langfuse (`architecture.md` §13.6) |

### Demostraciones

#### C22 — Primera generación de los tipos del frontend (D)

- **Entrada:** `serve` escuchando en `http://127.0.0.1:8000` y `pnpm.cmd gen:api` desde `frontend/`.
- **Salida:** se escriben los tipos de la API a partir de `/openapi.json`, que a estas alturas documenta únicamente `/health`; `pnpm.cmd typecheck` sale con 0. Los commitea el integrador en `/integrar` (`architecture.md` §14.8).

#### C23 — Un clon limpio arranca siguiendo el README (D)

- **Entrada:** un clon limpio de `V2` en una ruta hermana corta, sin `.env`, y solo los pasos de la sección de arranque del README: copiar `.env.example` a `.env`, rellenar `JWT_SECRET` y `FORMAL_VERIFIER`, `uv sync`, `init-db`, `check-env`, compilar el frontend y `serve`.
- **Salida:** `check-env` sale con todo en `ok`; `GET /health` da 200; `/` muestra la cabecera de marca de la SPA (000-C07); fuera del directorio de datos solo cambia lo que git ignora. Es la parte de 001 de `verification.md` §5 R.2.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| I1 | Ninguna salida de `init-db`, `check-env` o `serve`, ni ningún rechazo de la config o de los ajustes, reproduce el valor de un ajuste secreto: `JWT_SECRET`, `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_AUTH_TOKEN`, `OPENROUTER_API_KEY`, `GITHUB_TOKEN`, `LANGFUSE_SECRET_KEY` y `LANGFUSE_PUBLIC_KEY` | T | Prueba parametrizada: cada secreto con un valor marcador reconocible, en una situación de fallo de C14; la salida no contiene el marcador |
| I2 | `init-db`, `check-env` y `serve` solo crean o cambian ficheros dentro del directorio de datos (`architecture.md` §12.6), sin contar las cachés del intérprete | T | La prueba compara el árbol de fuera del directorio de datos antes y después |
| I3 | Ni el doble nulo ni las órdenes de esta spec abren una conexión fuera de la máquina | T | Las pruebas de la spec corren con la red saliente bloqueada, salvo `127.0.0.1` |
| I4 | La config y los ajustes solo se leen a través de sus modelos tipados, validados en el borde | A | mypy estricto (000-I6); `verification.md` §3.1 |
| I5 | Las constantes del encargo y los identificadores que valida la config (roles, criterios, franjas) se definen una sola vez, en `domain`; el esquema y la config no repiten sus literales | I | `verificador` al cerrar |
| I6 | La config no se ve ni se edita desde la API ni desde MCP (`definitions.md` §11.1) | I | `verificador`, sobre las rutas montadas |
| I7 | Tablas y columnas usan los identificadores de `definitions.md` §12 y los de la tabla de C6, sin sinónimos | I | `verificador` |
| I8 | Ninguna prueba lee el `.env` real: los ajustes salen de fixtures | I | `verificador`; además, 000-C03 corre sin `.env` |

## Docs referenciados

- `architecture.md` §1.3 (constantes frente a config), §1.4 (un proceso), §6.3 (FTS5 con `unicode61 remove_diacritics 2`, vectores en una tabla normal, tarjetas que se suceden), §6.4 (índice en la misma transacción), §9.2 (la ejecución reanudada conserva su traza), §12.6 (solo el directorio de datos), §13.1, §13.2, §13.5 y §13.6 (trazas, spans, uso, doble nulo), §14.8 (SPA en el mismo origen, `openapi-typescript`), §15.1 (WAL, `foreign_keys`, `busy_timeout`, `create_all`), §15.3 (sin `--reload`), §15.4 (config), §15.5 (ajustes), §15.6 (esquema), §15.7 (API y códigos), §15.8 (CLI), §15.9 (organización y contratos que nacen en 001), §18 (Migraciones: `create_all`).
- `definitions.md` §3 (`Novela`: estado derivado; `Version`: número al publicar), §4 (`CanonCard`, `VentanaDeContexto`), §5 (`SesionDeRol`, `Ejecucion`, `Intento`, `PuntoDeControl`, `SolicitudDeCambio`, `EdicionManual`, componentes de código), §6 (`Criterio`, `ResultadoDeValidador`), §7 (`DecisionDePolitica`, `AuditLog`), §8 (`Sesion`, `Traza`, `Span`, `LlamadaDeModelo`, `PromptVersionado`), §9 (`FicheroDeCronologia`), §11.1–§11.3 (config, constantes, ajustes), §12 (identificadores y enumerados).
- `verification.md` §2 (clases), §3.1 (tipos en el borde), §3.3 (doble nulo que captura sin red), §4.1 (`check-env` contra el fallo silencioso), §4.3 (una config con `token_ceiling` > 100.000 no arranca), §5 (filas 7.8, O.16 y R.2).
- `project-constraints.md`: «Sin API keys en ningún repo. Usar `.env.example`»; el máximo de 100.000 tokens concurrentes; «cada novela, configuración y entrada del audit log queda asociada al usuario propietario».
- `specs/000-scaffolding.md` (000-C03, 000-C05, 000-C07, 000-I6 y lo que deja a 001) y `backend/AGENTS.md` (propiedad de la 001).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué entrega la 001? | Config, ajustes, esquema completo, sesión, API mínima, las tres órdenes, constantes del encargo, puerto de observabilidad y doble nulo | `architecture.md` §15.6, §15.9; `backend/AGENTS.md`; 000 (fuera de alcance) |
| ¿Hasta dónde llega el detalle del esquema? | Columnas, referencias, enumerados y unicidades aquí: es el contrato entre carriles | `architecture.md` §15.6 («detalle por columna, de la 001»); `definitions.md` §12 |
| ¿Cómo se garantiza el solo inserción y la sincronía del índice FTS5? | En código, no en la base: toda escritura de `audit_log`, `checkpoints`, `embeddings`, `canon_cards` y de su entrada en `canon_cards_fts` pasa por la unidad de trabajo del backend (C13), que decide el rechazo antes de tocar SQLite; sin disparadores del motor, para todos los carriles a la vez | `architecture.md` §6.4, §18 («Solo inserción y sincronía del índice FTS5») |
| ¿Qué ajustes son obligatorios? | `JWT_SECRET` (≥ 32), `FORMAL_VERIFIER` (sin valor por defecto; `github` exige sus tres variables), `LLM_PROVIDER` por defecto `claude_login` (`anthropic_compatible` exige credenciales); Langfuse, lo fija 004 | `definitions.md` §11.3; decisión, para §18 |
| ¿Directorio de datos, rutas relativas y `.env`? | Por defecto `<raíz>/backend/data` (no `<raíz>/data`: así lo fija §15.5, y es lo que 000-C01 ya ignora como `backend/data/`); las demás rutas relativas, desde la raíz, sin depender del directorio actual; el `.env` de la raíz, y el entorno prevalece | `architecture.md` §15.5; `specs/000-scaffolding.md` 000-C01; decisión, para §18. Corregido en esta ronda: un `<raíz>/data` anterior era incorrecto |
| ¿Umbral por criterio, si `tono` y `personalizacion-natural` están en las dos rúbricas? | Una clave por identificador: diez umbrales | `architecture.md` §15.4 (`quality.thresholds.<criterio>`); decisión, para §18 |
| ¿Valores que §15.4 no da? | Los `max_turns` y `max_output_tokens` de los seis roles sin ejemplo, y los objetivos de `teen` y `adult`, son «provisionales» (`architecture.md` §17.1): se calibran en la iteración de tuning, ninguna spec los fija. C1 solo exige los valores que §15.4 sí da (`token_ceiling`, `interviewer`, `children`, precios, umbrales); C2 exige que los demás sean positivos, sin asertar una cifra | `architecture.md` §15.4, §17.1. Ya no es hueco: resuelto sin tocar el doc |
| ¿Salud sin token? | `GET /health`, fuera de `/api` y sin token, para comprobar el arranque y para la primera generación de tipos; al no estar bajo `/api`, no contradice 002-I2 (todo `/api` salvo registro y acceso exige token) | `architecture.md` §15.7 (ya la lista, «fuera de /api»); decisión, para §18. Resuelve el aviso al integrador de 002 |
| ¿`check-env` en la 001? | Las mismas comprobaciones que el arranque; `auth_check()` lo añade 004 | `verification.md` §4.1; `architecture.md` §15.9 |
| ¿Qué pasa con una base desfasada o existente? | `serve` y `check-env` la detectan y piden recrearla; `init-db` no la pisa sin `--reset` | `architecture.md` §15.6 («la base se recrea»); decisión, para §18 |
| ¿Dónde escucha `serve`? | En el host y el puerto de `STORY_MAKER_BASE_URL`, que es el mismo origen que navega el revisor visual | `architecture.md` §12.3, §14.2; decisión, para §18 |
| ¿Continuidad de la traza reanudada sin columna en `runs`? | Abrir la traza del mismo objeto la continúa | `architecture.md` §9.2, §15.6; decisión, para §18 |
| ¿`LANGFUSE_MCP_AUTH` en `.env.example`? | Solo en un comentario: va en el entorno del usuario y el backend no la lee | `architecture.md` §15.5; README («nunca en el repo») |
| ¿Vuelve `config.json`? | Sí: los docs lo dan por existente (`TODO.md` lo tenía como hueco) | `architecture.md` §15.4; `definitions.md` §11.1 |
| ¿Dónde vive el esquema OpenAPI y qué documenta? | En `GET /openapi.json`, fuera de `/api` y sin token, igual que `/health`: `gen:api` (C22) lo necesita sin credenciales. Un solo proceso (§1.4) documenta toda la aplicación, `/health` incluida, aunque ninguna de las dos rutas lleve el prefijo `/api` | `architecture.md` §1.4, §15.7, §15.9; decisión, para §18 |
