# 001 — BAS · Diseño

Cómo se construye la base: versiones fijadas, módulos, config y ajustes, el esquema SQLite por columna de todas las tablas de `architecture.md` §14.5 y las interfaces externas de todo el backend. Qué hace el sistema está en [spec.md](spec.md) y en la spec de cada feature. Este fichero es la referencia de columnas y de librerías para todas las specs: la que cambie una tabla o una interfaz añade su migración y lo actualiza en el mismo cambio.

Las marcas **unsure** son hechos de librería sin medir todavía; los confirma la orden de comprobaciones de entorno (RF-BAS-41) o el plan de la spec que se cita.

## 1. Versiones fijadas

Las de `architecture.md` §14.1, verificadas el 2026-09-23, y las que fija el entorno de desarrollo. El resto —FastAPI, uvicorn, Pydantic, pydantic-settings, SQLAlchemy, Alembic, `sqlite-vec`, `fastembed`, `msvc-runtime`, bcrypt, PyJWT, pypdf, httpx, pytest, Hypothesis, mutmut, `import-linter`, `detect-secrets`, `pip-audit`, Ruff y mypy; Vite, React, TypeScript, Tailwind CSS, ESLint, `steiger`, `openapi-typescript` y `openapi-fetch`— las fijan `backend/uv.lock` y `frontend/pnpm-lock.yaml` al instalarlas por primera vez. CI instala con `uv sync --locked` y `pnpm install --frozen-lockfile`.

| Pieza | Versión | Motivo |
|---|---|---|
| Python | 3.12, fijado en `backend/.python-version` | `uv` elige el más nuevo instalado (3.14), y Smart App Control bloquea el wheel de spaCy para 3.14 |
| `claude-agent-sdk` | 0.2.158, con el CLI 2.1.280 empaquetado | §14.1; los hechos de §5.1 se midieron con esta versión |
| `langfuse` | 4.15.4 | §14.1 |
| `fastmcp` | 4.0.5 | §14.1 |
| `playwright` (Python) | 1.63.0 | §14.1 |
| `@playwright/mcp` | 0.0.82 | La misma en `.mcp.json` y en el revisor visual (`verification.md` §9.2) |
| spaCy | 3.8.16 | Carga bajo Smart App Control con Python 3.12 y `msvc-runtime` |
| `leanprover/lean-action` | v1.6.0 | §14.1; workflow de Lean |
| Lean | v4.34.0 | §14.1; `lean-toolchain` de `lean/` |
| Node | 24, portable en el perfil del usuario | Entorno de desarrollo |
| `pnpm` | 10.x | La 11 no arranca sin el Visual C++ Redistributable |
| JDK | Temurin 21 portable | Trae sus propias DLL de Visual C++; lo usa TLC (006) |

## 2. Módulos

### 2.1 Backend

```
backend/
  pyproject.toml  uv.lock  .python-version  alembic.ini  openapi.json
  harness_workspace/
    CLAUDE.md                                 reglas de producto de los roles (011)
    .claude/skills/personalizacion-natural/   la skill del producto (011)
    prompts/<etiqueta-del-rol>.md             prompt versionado de cada rol (004)
  src/story_maker/
    domain/        catálogo de criterios, constantes, modelo de la config, reglas puras
    store/         tablas SQLAlchemy, migraciones Alembic, repositorios, transacciones
    platform/      agent_port (SDK y doble), sqlite (conexión y extensiones), embedding, paths,
                   langfuse (004), formal_verifier (009), browser y pdf (013, 014)
    harness/       tools y hooks de los roles, guardián y ensamblado de ventana (008)
    lint/          linters de prosa (012)
    phases/        interview/ planning/ chapter_production/ publication/ change/
    execution/     app FastAPI, ajustes, carga de la config, CLI, worker (007), servidor MCP (016);
                   sus pruebas incluyen las de extremo a extremo
.github/workflows/  ci.yml, mutation.yml, lean-smoke.yml (RF-BAS-43); tlc (006), lean-verify.yml (009)
```

Las pruebas de cada slice van en `src/story_maker/<slice>/tests/`; las de extremo a extremo, en las de `execution`, que es quien compone el sistema.

**Contratos de `import-linter`**, en `pyproject.toml`:

| Contrato | Tipo | Regla |
|---|---|---|
| Fases independientes | `independence` | `phases.interview`, `phases.planning`, `phases.chapter_production`, `phases.publication` y `phases.change` no se importan entre sí |
| Fases sin `execution` | `forbidden` | `phases` no importa `execution` |
| `domain` puro | `forbidden` | `domain` no importa ningún otro módulo del proyecto, ni `sqlalchemy`, `sqlite3`, `fastapi`, `httpx`, `claude_agent_sdk`, `langfuse`, `fastembed`, `sqlite_vec`, `playwright` ni `pypdf` (`include_external_packages = true`) |
| `platform` sin dominio | `forbidden` | `platform` no importa `domain`, `store`, `harness`, `lint`, `phases` ni `execution` |
| `store` solo sobre `domain` | `forbidden` | `store` no importa `platform`, `harness`, `lint`, `phases` ni `execution` |
| `lint` solo sobre `domain` | `forbidden` | `lint` no importa `store`, `platform`, `harness`, `phases` ni `execution` |
| `harness` bajo las fases | `forbidden` | `harness` no importa `phases`, `execution` ni `lint` |
| El SDK solo en `platform` | `forbidden` | Ningún módulo salvo `platform` importa `claude_agent_sdk` |

`store` no importa `platform`: la conexión con sus extensiones la crea `platform.sqlite`, y `execution` se la pasa al store al construir la aplicación o el worker. `execution` importa las fases y `platform` sin contrato que lo impida: es la excepción declarada y la raíz de composición (`architecture.md` §14.2).

### 2.2 Frontend

```
frontend/
  package.json  pnpm-lock.yaml  vite.config.ts  tsconfig.json  eslint.config.js  steiger.config.ts
  src/
    app/       providers, router, tema corporativo (tokens de Tailwind), estilos globales
    pages/     login/ novels/ interview/ progress/ reader/ change/ preview/ print/   (una por spec)
    shared/
      api/     cliente generado del esquema OpenAPI (commiteado)
      ui/      componentes base con los tokens del tema
      lib/     utilidades sin dominio
      config/  rutas y constantes del cliente
```

- **Proxy de desarrollo.** `vite.config.ts` reenvía `/api` a `http://127.0.0.1:<puerto del backend>`.
- **Cliente generado.** `openapi-typescript` genera los tipos desde `backend/openapi.json`, y el cliente usa `openapi-fetch`. CI regenera los dos ficheros y falla con `git diff --exit-code`.
- **Tema.** Los tokens —colores primario y secundario, neutros, familias tipográficas de títulos y de texto— salen del logo de `images/` y viven en la configuración de Tailwind. Los consumen `shared/ui` y `app`; ninguna página define colores propios.
- **`steiger`** aplica sus reglas de FSD con la configuración por defecto de v2.1.

## 3. Ajustes, config y rutas

### 3.1 Ajustes del servidor

Un `BaseSettings` de `pydantic-settings` en `execution`, con las variables de `definitions.md` §11. Lee el entorno, y `.env` solo si existe. Se valida al arrancar la aplicación, el worker y la CLI. Ni los ajustes ni la config salen por ningún endpoint.

| Variable | Tipo | Regla |
|---|---|---|
| `STORY_MAKER_DATA_DIR` | ruta | Obligatoria; se crea si no existe y debe poder escribirse |
| `STORY_MAKER_CONFIG` | ruta | Obligatoria; el fichero debe existir |
| `FORMAL_VERIFIER` | `Literal["local", "github"]` | Obligatoria |
| `JWT_SECRET` | texto, `min_length=32` | Obligatorio |
| `GITHUB_REPOSITORY`, `LEAN_WORKFLOW`, `GITHUB_TOKEN` | texto | Obligatorias con `FORMAL_VERIFIER=github` |
| `LANGFUSE_PROMPT_LABEL` | texto | Obligatoria |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` | texto, URL | Obligatorias |
| `OPENROUTER_API_KEY` | texto | Obligatoria |

### 3.2 Config

El modelo de la config vive en `domain`, porque es política pura, y lo carga `execution`. Todos sus modelos llevan `extra="forbid"` y ningún campo tiene valor por defecto. Una cifra sin calibrar se tipa `T | None`, y su lectura pasa por `require("operation.max_retries")`, que devuelve el valor o lanza `UncalibratedFigureError` con la clave: `config: operation.max_retries sin calibrar (architecture.md §15.2); dale valor en config.json`.

- `retrieval.quotas`: mapa consumidor → colección → entero ≥ 0 o `null`. Consumidores: `writer`, `critic`, `editor`, `repetition_linter`. Colecciones: `canon_cards`, `prose`. Deben estar los ocho pares; `prose` distinto de 0 solo en `editor` y `repetition_linter`.
- `operation.roles`: exactamente los nueve roles de `definitions.md` §12, cada uno con `model`, `max_output` y `max_turns`.
- `operation.pricing`: mapa modelo → `{input, output, cache_read, cache_write}` en USD por millón de tokens.
- `operation.window_ceiling`: entero entre 1 y 100.000.
- `quality.readability_targets`: mapa franja (`children`, `teen`, `adult`) → `{sentence_length, fernandez_huerta}`.
- `quality.active_criteria` y `quality.thresholds`: un validador del modelo raíz los comprueba contra el catálogo de criterios de `domain`.

**Huella de la config**: SHA-256 del JSON canónico —claves ordenadas, sin espacios— del modelo validado. La guarda cada tramo (`run_segments`) y la lleva cada traza (004).

### 3.3 Rutas bajo el directorio de datos

`platform.paths` resuelve cada ruta como `data_dir / relativa` y la comprueba con `Path.resolve().is_relative_to(data_dir)`; una que sale, por `..` o por ser absoluta, lanza un error. Ningún otro código compone rutas de escritura.

| Uso | Ruta |
|---|---|
| Base de datos | `story_maker.sqlite3`, con sus `-wal` y `-shm` |
| Configuración del CLI del SDK (`CLAUDE_CONFIG_DIR`) | `claude/` |
| Cachés de modelos: `fastembed` (`cache_dir`) y HuggingFace (`HF_HOME`) | `models/` |
| Salida de Playwright MCP del revisor visual | `playwright-mcp/` |
| PDF de las versiones publicadas | `pdf/<novel_id>/<número>.pdf`; `versions.pdf_path` guarda la ruta relativa |
| Área de trabajo del verificador local | `lean/` (009) |

En el portátil, `LongPathsEnabled = 0` y Python no abre rutas de más de 260 caracteres: el directorio de datos va en una ruta corta, como `C:\sm-data`.

## 4. Esquema SQLite

### 4.1 Convenciones

- **Nombres:** tablas en plural con el identificador de `definitions.md` §12, salvo los incontables (`traceability`, `audit_log`); columnas en inglés, en `snake_case`. Las tablas de unión nombran sus dos lados. Este esquema es la proyección de los atributos de `definitions.md` a columnas, como declara su §12.
- **Claves:** en las tablas de ámbito versión, `PRIMARY KEY (version_id, id)`. Una candidata copia las filas de la vigente con sus mismos ids (014), así que un personaje, un hecho o un evento tienen el mismo id en todas las versiones de su novela, y un `{hecho}` seleccionado en una versión es el mismo id en la candidata. Una fila nueva toma un id que no usa ninguna versión de esa tabla: el mayor más uno. Dentro de una versión, las claves ajenas son compuestas, `(version_id, <x>_id)`. En el resto de tablas, `id INTEGER PRIMARY KEY`. Los ids de las filas son los identificadores que usa el `FicheroDeCronologia` (009).
- **Momentos del sistema:** `TEXT` en ISO 8601 UTC (`2026-09-23T17:30:00Z`).
- **Momentos de la ficción:** `TEXT` `YYYY-MM-DDTHH:MM`; fechas de nacimiento, `YYYY-MM-DD`, y el nacimiento es a las 00:00.
- **Booleanos:** `INTEGER` con `CHECK (col IN (0, 1))`.
- **Enumerados:** `TEXT` con `CHECK` sobre los valores de `definitions.md` §12.
- **JSON:** `TEXT` con `CHECK (json_valid(col))`; su forma la fija el modelo Pydantic de la spec que lo escribe.
- **Números de capítulo:** `INTEGER` con `CHECK` de 1 a 10; de 0 a 10 donde se admite el canon anterior al capítulo 1 (`since_chapter`, `checkpoints`); de 0 a 11 en `canon_cards.since_chapter`, porque la tarjeta nacida al aceptar el capítulo 10 rige desde el 11 (§6.6).
- **`recorded_chapter`:** en las filas que escribe el registro de un capítulo, su número; `NULL` en las del brief, la planificación o un cambio. Es lo que el reemplazo de §8.3 usa para saber qué escribió cada registro.
- **Lo derivado no se guarda:** el estado de la novela, su título y su versión vigente; la posición en la cola; el número de reanudaciones; el coste acumulado de una entrevista o de una ejecución; el estado de un arco.

### 4.2 Cuentas, entrada y peticiones

**`users`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `email` | TEXT | no | `UNIQUE COLLATE NOCASE` |
| `password_hash` | TEXT | no | bcrypt |
| `created_at` | TEXT | no | Fecha de alta |

**`novels`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | Es también el `session_id` de Langfuse |
| `user_id` | INTEGER | no | FK `users` |
| `created_at` | TEXT | no | Fecha de creación: fija el año presente y la regla C4 |
| `embedding_model` | TEXT | no | Copia de `retrieval.embedding_model` al crear la novela (§6.9) |

**`interviews`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels`, `UNIQUE` |
| `status` | TEXT | no | `open`, `confirmed` |
| `trace_id` | TEXT | sí | Traza de Langfuse de la entrevista |
| `created_at` | TEXT | no | |

**`interview_messages`** · solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `interview_id` | INTEGER | no | FK `interviews` |
| `ordinal` | INTEGER | no | `UNIQUE (interview_id, ordinal)` |
| `user_text` | TEXT | no | Mensaje del cliente |
| `reply_text` | TEXT | no | Respuesta del entrevistador |
| `role_session_id` | INTEGER | no | FK `role_sessions`: la sesión que produjo el turno |
| `created_at` | TEXT | no | |

**`briefs`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels`, `UNIQUE` |
| `status` | TEXT | no | `draft`, `confirmed` |
| `content` | TEXT | no | JSON del brief: `recipient`, `close_ones`, `occasion`, `recollections`, `genre`, `tone`, `length`, `dedication`, `banned_asked`, `plot_wishes`. Cada allegado lleva una clave estable, `key`, que no cambia aunque cambie su nombre; cada rasgo, recuerdo y allegado, su marca `mandatory`; cada deseo de trama, su `statement` y su `frame` opcional (`simulation`, `dream`, `story_within_story`) |
| `confirmed_at` | TEXT | sí | |

Las entradas prohibidas de nivel novela van en `banned_terms`; los textos libres y sus hechos, en `free_texts` y `extracted_facts`.

**`free_texts`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `brief_id` | INTEGER | no | FK `briefs` |
| `content` | TEXT | no | Contenido no confiable: solo lo recibe el extractor |
| `discarded_instructions` | TEXT | no | JSON: las frases que el extractor declaró instrucciones |
| `flagged_sentences` | TEXT | no | JSON: las frases que marcó el detector de inyección, con su desplazamiento |
| `created_at` | TEXT | no | |

**`extracted_facts`** · solo los verificados

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `free_text_id` | INTEGER | no | FK `free_texts` |
| `subject_key` | TEXT | no | `recipient` o la `key` de un allegado del brief |
| `attribute` | TEXT | no | |
| `value` | TEXT | no | |
| `quote` | TEXT | no | Cita literal verificada |
| `accepted` | INTEGER | sí | `NULL` pendiente, 1 aceptado, 0 rechazado |
| `mandatory` | INTEGER | no | Por defecto 0 |

**`personal_elements`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `brief_id` | INTEGER | no | FK `briefs` |
| `origin` | TEXT | no | `brief_field`, `extracted_fact` |
| `field` | TEXT | sí | Ruta del campo del brief (`recipient.name`, `recipient.traits[1]`, `recollections[0]`, `close_ones[<key>]`) cuando `origin = brief_field` |
| `extracted_fact_id` | INTEGER | sí | FK `extracted_facts`, `UNIQUE`, cuando `origin = extracted_fact` |
| `mandatory` | INTEGER | no | |

`CHECK`: exactamente uno de `field` y `extracted_fact_id`.

**`banned_terms`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `level` | TEXT | no | `global`, `user`, `novel` |
| `user_id` | INTEGER | sí | FK `users`; solo en `user` |
| `novel_id` | INTEGER | sí | FK `novels`; solo en `novel` |
| `term` | TEXT | no | Tal como lo escribió quien lo dio de alta |
| `normalized` | TEXT | no | Forma normalizada (003) |
| `type` | TEXT | no | `word`, `topic` |
| `created_at` | TEXT | no | |

`CHECK`: `global` sin `user_id` ni `novel_id`; `user` con `user_id` y sin `novel_id`; `novel` con `novel_id` y sin `user_id`.

**`audit_log`** · solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `created_at` | TEXT | no | Momento |
| `user_id` | INTEGER | no | FK `users`: siempre |
| `novel_id` | INTEGER | sí | FK `novels` |
| `run_id` | INTEGER | sí | FK `runs` |
| `role` | TEXT | sí | Identificador del rol |
| `tool` | TEXT | sí | Identificador de la tool |
| `origin` | TEXT | no | `policy_hook`, `free_text`, `change_request`, `manual_edit`, `publication_gate`, `mcp_write` |
| `decision` | TEXT | no | `allow`, `deny`, `flag` |
| `reason_code` | TEXT | no | |
| `detail` | TEXT | no | JSON: las coincidencias, con su nivel y la variante encontrada, o las frases marcadas |

**`change_requests`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels` |
| `base_version_id` | INTEGER | no | FK `versions`: la que vio el lector |
| `selection` | TEXT | no | JSON: `{version, chapter, quote}` o `{fact}` |
| `request` | TEXT | no | Petición: texto no confiable |
| `proposal` | TEXT | sí | JSON de la propuesta; `NULL` si se rechazó antes de proponer |
| `code_hash` | TEXT | sí | Hash del código de confirmación; el código no se guarda en claro |
| `code_expires_at` | TEXT | sí | |
| `status` | TEXT | no | `proposed`, `confirmed`, `rejected`, `expired`, `applied` |
| `reason` | TEXT | sí | Motivo del rechazo |
| `trace_id` | TEXT | sí | Traza de la interpretación |
| `created_at` | TEXT | no | |

La ejecución de una solicitud es la de `runs.change_request_id`; su versión resultante, la candidata de esa ejecución una vez publicada.

**`manual_edits`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels` |
| `base_version_id` | INTEGER | no | FK `versions` |
| `chapter_number` | INTEGER | no | 1–10 |
| `text` | TEXT | no | Texto nuevo del capítulo |
| `changed_facts` | TEXT | sí | JSON: los hechos que cambió, según el registrador |
| `status` | TEXT | no | `queued`, `applied`, `rejected` |
| `reason` | TEXT | sí | |
| `created_at` | TEXT | no | |

### 4.3 Una versión: story bible, artefacto e índice

Todas estas tablas, salvo `versions` y `embeddings`, son de ámbito versión: llevan `version_id` (FK `versions`, no nulo), también las hijas —`outline_chapters`, `beats`, `arcs`, `element_assignments`— y las de unión, y su clave es `(version_id, id)`, o `(version_id, <lado_1>_id, <lado_2>_id)` en las de unión. Una candidata las copia de la vigente en una sola transacción (014): cada tabla con un `INSERT … SELECT` que solo cambia `version_id`, sin remapear ninguna clave ajena.

**`versions`** · ámbito novela

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | Identifica a una candidata, que no tiene número |
| `novel_id` | INTEGER | no | FK `novels` |
| `run_id` | INTEGER | no | FK `runs`: la ejecución que la produjo |
| `number` | INTEGER | sí | Al publicar; `UNIQUE (novel_id, number)` |
| `status` | TEXT | no | `candidate`, `published`, `rejected` |
| `changed_chapters` | TEXT | sí | JSON: números de capítulo; se guarda al publicar |
| `published_at` | TEXT | sí | |
| `pdf_path` | TEXT | sí | Relativa al directorio de datos |

**`worlds`** · una por versión; el `Novum` va aquí

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | Sujeto de los hechos de tipo `world` |
| `version_id` | INTEGER | no | `UNIQUE` |
| `novum_statement` | TEXT | no | |
| `novum_scope` | TEXT | no | `technological`, `social`, `cognitive` |
| `novum_date` | TEXT | no | Fecha de aparición, anterior al año presente |

**`consequences`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `world_id` | INTEGER | no | FK `worlds` |
| `parent_id` | INTEGER | sí | FK `consequences`; `NULL` si deriva del novum |
| `statement` | TEXT | no | |
| `depth` | INTEGER | no | El orden: 1–3 |
| `scope` | TEXT | no | `technology`, `government`, `economy`, `social_norm`, `artificial_entity` |

**`constraints`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `world_id` | INTEGER | no | FK `worlds` |
| `consequence_id` | INTEGER | sí | FK `consequences`; `NULL` si la define el novum |
| `statement` | TEXT | no | |
| `detectable` | INTEGER | no | |
| `predicate` | TEXT | sí | `immutable`, `forbidden`, `required`; no nulo si `detectable = 1` |
| `subject_type` | TEXT | sí | `character`, `place`, `world` |
| `subject_id` | INTEGER | sí | Solo en `required`, que nombra un sujeto concreto |
| `attribute` | TEXT | sí | |
| `value` | TEXT | sí | En `forbidden` y `required` |

**`characters`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `type` | TEXT | no | `recipient`, `close_one`, `invented` |
| `species` | TEXT | no | `person`, `animal`, `artificial` |
| `name` | TEXT | no | Forma canónica: copia del valor del hecho de nombre vigente, escrita en la misma transacción que él |
| `traits` | TEXT | no | JSON |
| `birth_date` | TEXT | sí | Sin ella, fuera de T2 y T5 |
| `origin` | TEXT | no | `brief`, `invented` |
| `since_chapter` | INTEGER | no | 0–10 |
| `recorded_chapter` | INTEGER | sí | |

**`places`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `name` | TEXT | no | Forma canónica |
| `type` | TEXT | no | |
| `description` | TEXT | no | |
| `origin` | TEXT | no | `brief`, `invented` |
| `since_chapter` | INTEGER | no | 0–10 |
| `recorded_chapter` | INTEGER | sí | |

**`facts`** · solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `subject_type` | TEXT | no | `character`, `place`, `world` |
| `subject_id` | INTEGER | no | Id en `characters`, `places` o `worlds` |
| `attribute` | TEXT | no | En los de origen `brief`, del vocabulario cerrado de `domain` (§4.1) |
| `value` | TEXT | no | |
| `origin` | TEXT | no | `brief`, `free_text`, `invented` |
| `since_chapter` | INTEGER | no | 0–10 |
| `supersedes_id` | INTEGER | sí | FK `facts`: el hecho al que sucede |
| `personal_element_id` | INTEGER | sí | FK `personal_elements`: el elemento que representa |
| `recorded_chapter` | INTEGER | sí | |

Una cadena de sucesión la forman un hecho y sus sucesores por `supersedes_id`. La regla de cuál rige en el capítulo *n* es la de `definitions.md` §2 (`Hecho`): con estas columnas, el de mayor `since_chapter` ≤ *n* y, si empatan, el de mayor `id`.

**`fact_usages`**: `id`, `version_id`, `fact_id` (FK `facts`), `chapter_number`; `UNIQUE (version_id, fact_id, chapter_number)`.

**`events`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `statement` | TEXT | no | |
| `moment` | TEXT | no | `YYYY-MM-DDTHH:MM` |
| `place_id` | INTEGER | sí | FK `places` |
| `type` | TEXT | no | `ordinary`, `exclusion` |
| `excluded_character_id` | INTEGER | sí | FK `characters`; no nulo si y solo si `type = exclusion` |
| `declared_ages` | TEXT | no | JSON: id de personaje → edad, cuando la fuente la fija |
| `chapter_number` | INTEGER | sí | Capítulo que lo narra; `NULL` en el trasfondo |
| `beat_number` | INTEGER | sí | Beat que lo narra |
| `flashback` | INTEGER | no | Analepsis |
| `narrates_event_id` | INTEGER | sí | FK `events`: el evento de trasfondo que narra |
| `origin` | TEXT | no | `brief`, `planned`, `recorded` |
| `recorded_chapter` | INTEGER | sí | |

Uniones: **`event_characters`** (`event_id`, `character_id`), los personajes presentes; **`event_consequences`** (`event_id`, `consequence_id`), las consecuencias de las que depende.

**`outlines`**: `id`, `version_id` (`UNIQUE`), `novel_title`, `frozen`.

**`outline_chapters`**: `id`, `outline_id`, `number` (1–10, `UNIQUE (outline_id, number)`), `title`, `arc_function`, `planned_tension_in` (1–5), `planned_tension_out` (1–5).

**`beats`**: `id`, `outline_chapter_id`, `number` (1–6, `UNIQUE (outline_chapter_id, number)`), `description`, `event_id` (FK `events`, `UNIQUE`: su evento planificado), `frame` (`simulation`, `dream`, `story_within_story`), `revelation_topic` (nulo), `revelation_content` (nulo). `CHECK`: exactamente uno de `event_id` y `frame` no es nulo, porque un beat dentro de un marco no tiene evento (`architecture.md` §4.3). Unión **`beat_facts`** (`beat_id`, `fact_id`): los hechos que usa.

**`arcs`**: `id`, `outline_id`, `name`, `type` (`character`, `plot`, `theme`), `setup_chapter` (1–10), `resolution_chapter` (1–10). Unión **`arc_characters`** (`arc_id`, `character_id`): quién lo protagoniza.

**`element_assignments`**: `id`, `outline_id`, `personal_element_id` (FK `personal_elements`), `chapter_number`; `UNIQUE (outline_id, personal_element_id, chapter_number)`.

**`style_sheets`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | `UNIQUE` |
| `narrator` | TEXT | no | `first_person`, `third_person` |
| `tense` | TEXT | no | `past`, `present` |
| `address` | TEXT | no | JSON: par de ids de personaje → `tu` \| `usted` |
| `register` | TEXT | no | Sale de la franja de edad del destinatario |
| `tone` | TEXT | no | Valores de `Tono` |
| `genre` | TEXT | no | Valores de `Genero` |
| `avoid_lexicon` | TEXT | no | JSON; incluye los temas prohibidos |

**`chapters`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `version_id` | INTEGER | no | |
| `number` | INTEGER | no | 1–10; `UNIQUE (version_id, number)` |
| `title` | TEXT | no | Copiado del outline |
| `text` | TEXT | no | Texto plano; párrafos separados por una línea en blanco |
| `fingerprint` | TEXT | no | SHA-256 del título y el texto |
| `summary` | TEXT | no | El `ResumenDeCapitulo` |
| `tension_in` | INTEGER | no | Medida por el crítico, 1–5 |
| `tension_out` | INTEGER | no | Medida por el crítico, 1–5 |

**`paragraphs`**: `id`, `version_id`, `chapter_number`, `ordinal`, `text`; `UNIQUE (version_id, chapter_number, ordinal)`.

**`state_deltas`**: `id`, `version_id`, `chapter_number`, `beat_number`, `type` (`declared`, `real`), `content` (JSON: cambios, eventos, hechos usados, hechos nuevos y arcos resueltos); `UNIQUE (version_id, chapter_number, beat_number, type)`.

**`world_states`**: `id`, `version_id`, `chapter_number` (`UNIQUE (version_id, chapter_number)`), `content` (JSON: el momento; por personaje, su último lugar, si está excluido y los hechos que cambió algún delta real; el estado de los arcos).

**`traceability`**: `id`, `version_id`, `chapter_number`, `type` (`fact`, `canon_card`, `mandatory_element`), `reference_id`.

**`canon_cards`** · solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | Estable entre versiones, como el resto de ids de ámbito versión |
| `version_id` | INTEGER | no | |
| `entity_type` | TEXT | no | `character`, `place`, `consequence`, `constraint`, `novum` |
| `entity_id` | INTEGER | no | |
| `content` | TEXT | no | |
| `fingerprint` | TEXT | no | SHA-256 del contenido: la clave de su vector |
| `since_chapter` | INTEGER | no | 0–11: el `desde_capitulo` de la tarjeta |
| `recorded_chapter` | INTEGER | sí | |

`hasta_capitulo` no se guarda: es el `since_chapter` de la tarjeta sucesora de la misma `(entity_type, entity_id)` en la versión.

**`canon_cards_fts`**: tabla virtual FTS5 `(content, version_id UNINDEXED, card_id UNINDEXED)` con `tokenize = 'unicode61 remove_diacritics 2'`. Tiene su propio `rowid`, porque el id de una tarjeta se repite entre versiones; la fila de la tarjeta es la de `(version_id, card_id)`.

**`paragraphs_fts`**: tabla virtual FTS5 `(text, version_id UNINDEXED, paragraph_id UNINDEXED, chapter_number UNINDEXED)` con el mismo tokenizador y su propio `rowid`. La prosa no tiene vectores.

**`embeddings`** · ámbito global, solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `fingerprint` | TEXT | no | Huella del contenido incrustado |
| `model` | TEXT | no | Identificador del modelo de incrustación |
| `dimensions` | INTEGER | no | |
| `vector` | BLOB | no | float32, en el formato de `sqlite-vec` |

Clave primaria `(fingerprint, model)`. El vector de una tarjeta es el de `(canon_cards.fingerprint, novels.embedding_model)`.

### 4.4 Ejecuciones y calidad

**`runs`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels` |
| `type` | TEXT | no | `generation`, `change_request`, `manual_edit` |
| `status` | TEXT | no | `created`, `running`, `finished`, `blocked`, `cancelled`, `interrupted` |
| `phase` | TEXT | sí | `planning`, `chapter_production`, `revalidation`, `editing`, `recording`, `propagation`, `publication` |
| `current_chapter` | INTEGER | sí | |
| `base_version_id` | INTEGER | sí | FK `versions`; `NULL` en una generación |
| `change_request_id` | INTEGER | sí | FK `change_requests`, `UNIQUE` |
| `manual_edit_id` | INTEGER | sí | FK `manual_edits`, `UNIQUE` |
| `block_reason` | TEXT | sí | `retries_exhausted`, `budget_exceeded`, `infeasible_config`, `render_failure`, `banned_content`, `internal_error` |
| `cancel_requested` | INTEGER | no | Marca de cancelación; por defecto 0 |
| `worker_pid` | INTEGER | sí | |
| `worker_started_at` | TEXT | sí | Hora de arranque del proceso del worker |
| `trace_id` | TEXT | sí | La conserva al reanudar |
| `created_at` | TEXT | no | Orden de llegada a la cola |
| `started_at` | TEXT | sí | |
| `ended_at` | TEXT | sí | |

La candidata de una ejecución es la versión con su `run_id`. La posición en la cola es el número de ejecuciones `created` con `(created_at, id)` menor.

**`run_segments`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `run_id` | INTEGER | no | FK `runs` |
| `ordinal` | INTEGER | no | `UNIQUE (run_id, ordinal)`; 1 al arrancar, uno más por reanudación |
| `config` | TEXT | no | JSON: copia de la config validada |
| `config_fingerprint` | TEXT | no | §3.2 |
| `banned_lists` | TEXT | no | JSON: copia de las tres listas vigentes —global, del cliente y de la novela— |
| `commit` | TEXT | no | Commit del código |
| `started_at` | TEXT | no | |

**`attempts`**: `id`, `run_segment_id` (FK `run_segments`), `evaluable` (`chapter`, `fallback_regeneration`, `outline`, `gate_cycle`, `change_interpretation`), `reference` (nulo; el número de capítulo en `chapter` y `fallback_regeneration`), `ordinal`, `failed`, `reason` (nulo), `created_at`. Una fila por intento.

**`checkpoints`** · solo inserción: `id`, `run_id`, `chapter_number` (0–10; 0 es el outline congelado con el canon inicial), `created_at`.

**`previews`**: `id`, `run_id`, `version_id` (la candidata), `token_hash` (`UNIQUE`), `revoked`, `created_at`.

**`chronology_files`** · solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `run_id` | INTEGER | no | FK `runs` |
| `version_id` | INTEGER | no | FK `versions` |
| `chronology` | TEXT | no | `planned`, `recorded` |
| `content` | TEXT | no | El fichero Lean, seudonimizado |
| `year_offset` | INTEGER | no | Desplazamiento de los años: un múltiplo de 400 distinto de cero (009) |
| `verifier_mode` | TEXT | no | `local`, `github` |
| `passed` | INTEGER | no | |
| `result` | TEXT | no | JSON del comprobador: el invariante violado y su primer testigo |
| `created_at` | TEXT | no | |

**`role_sessions`** · ámbito ejecución, o novela fuera de una ejecución

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels` |
| `role` | TEXT | no | Identificador del rol |
| `run_id` | INTEGER | sí | FK `runs` |
| `interview_id` | INTEGER | sí | FK `interviews` |
| `change_request_id` | INTEGER | sí | FK `change_requests`: la interpretación |
| `evaluable` | TEXT | sí | |
| `attempt_id` | INTEGER | sí | FK `attempts` |
| `chapter_number` | INTEGER | sí | El capítulo, si la sesión es de uno |
| `model` | TEXT | no | |
| `prompt_name` | TEXT | no | `rol/<etiqueta>` |
| `prompt_version` | INTEGER | no | Versión de Langfuse que se leyó por etiqueta |
| `outcome` | TEXT | no | Desenlace del puerto: `completed`, `turns_exhausted`, `time_exhausted`, `cut`, `infrastructure_failure` |
| `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens` | INTEGER | no | Uso exacto de la sesión |
| `estimated_input_tokens` | INTEGER | sí | Suma estimada de la entrada de sus turnos (008) |
| `cost_usd` | REAL | no | Uso exacto por `operation.pricing` (004) |
| `duration_ms` | INTEGER | no | |
| `generation_ids` | TEXT | no | JSON: ids `gen-…` de OpenRouter |
| `trace_id` | TEXT | no | |
| `observation_id` | TEXT | no | La observación de generación |
| `started_at`, `ended_at` | TEXT | no | |

Una sesión de la importación de un brief solo lleva `novel_id`.

**`context_windows`**: `id`, `role_session_id` (FK, `UNIQUE`), `consumer` (nulo fuera de los consumidores), `chapter_number` (nulo), `residents`, `call_inputs`, `retrieved` (por colección), `denied` (todos JSON), `input_quota`, `input_tokens`.

**`verdicts`**: `id`, `run_id`, `evaluable`, `reference` (nulo), `attempt_id` (nulo), `action` (`accept`, `correct`, `regenerate`, `re_record`, `block`, `escalate`), `created_at`.

**`defects`**

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `run_id` | INTEGER | no | FK `runs` |
| `verdict_id` | INTEGER | sí | FK `verdicts` |
| `criterion` | TEXT | sí | Id del catálogo; nulo en una causa raíz sin criterio |
| `validator` | TEXT | sí | Nombre del validador que lo encontró |
| `location` | TEXT | no | JSON: capítulo, beat, párrafo o desplazamiento |
| `root_cause` | TEXT | no | Valores de `Causa raíz` |
| `required_action` | TEXT | sí | `correct`, `regenerate`, `re_record`, `block` |
| `blocking` | INTEGER | no | |
| `detail` | TEXT | no | |
| `created_at` | TEXT | no | |

**`scores`** · ámbito novela, solo inserción

| Columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `id` | INTEGER | no | |
| `novel_id` | INTEGER | no | FK `novels` |
| `run_id` | INTEGER | sí | FK `runs` |
| `name` | TEXT | no | `<validador>` o `<validador>/<criterio>` |
| `value` | REAL | no | |
| `data_type` | TEXT | no | El tipo de score de Langfuse: `BOOLEAN` (0/1) o `NUMERIC` (1–5) |
| `comment` | TEXT | no | Los motivos |
| `trace_id` | TEXT | no | |
| `observation_id` | TEXT | sí | El span del capítulo, si es de capítulo |
| `chapter_number` | INTEGER | sí | |
| `created_at` | TEXT | no | |

### 4.5 Solo inserción

Tablas: `audit_log`, `interview_messages`, `facts`, `canon_cards`, `embeddings`, `checkpoints`, `chronology_files` y `scores`. Cada una lleva dos disparadores:

```sql
CREATE TRIGGER <tabla>_no_update BEFORE UPDATE ON <tabla>
BEGIN SELECT RAISE(ABORT, '<tabla> es de solo inserción'); END;

CREATE TRIGGER <tabla>_no_delete BEFORE DELETE ON <tabla>
BEGIN SELECT RAISE(ABORT, '<tabla> es de solo inserción'); END;
```

En `facts` y `canon_cards`, el de borrado lleva la excepción del reemplazo de §8.3:

```sql
CREATE TRIGGER facts_no_delete BEFORE DELETE ON facts
WHEN NOT (OLD.recorded_chapter IS NOT NULL
          AND (SELECT status FROM versions WHERE id = OLD.version_id) = 'candidate')
BEGIN SELECT RAISE(ABORT, 'facts es de solo inserción'); END;
```

La base garantiza que solo se borra lo que escribió un registro en una candidata. Que el reemplazo toque solo las filas del registro anterior del mismo capítulo lo garantiza la transacción de aceptación (011).

### 4.6 Conexión y migraciones

`platform.sqlite` crea cada conexión con

```
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```

y carga `sqlite-vec` (`conn.enable_load_extension(True)`, `sqlite_vec.load(conn)`, `conn.enable_load_extension(False)`). SQLAlchemy 2, síncrono, la recibe por el evento `connect` del engine. Alembic usa la misma fábrica: las tablas FTS5 y los disparadores se crean con `op.execute`, y `include_object` deja fuera de la comparación las tablas `*_fts` y sus tablas sombra. CI ejecuta `alembic check` sobre una base vacía para detectar la deriva entre los modelos y las migraciones.

## 5. Interfaces externas

### 5.1 Claude Agent SDK

Medido con 0.2.158 contra OpenRouter el 2026-09-23 (`verification.md` §8, filas 11–14). El puerto de agente (`platform.agent_port`) es el único código que lo toca.

**Opciones de cada sesión** (`ClaudeAgentOptions`):

| Opción | Valor | Por qué |
|---|---|---|
| `cwd` | `backend/harness_workspace/` | §7.3 |
| `setting_sources` | `["project"]` | Carga el `CLAUDE.md` y las skills del workspace |
| `settings` | `{"claudeMdExcludes": [<rutas de los CLAUDE.md de los padres>]}` | Con `project`, el CLI carga el `CLAUDE.md` y el `.claude/CLAUDE.md` de todos los directorios padre del `cwd`, también `~/.claude/CLAUDE.md`. `CLAUDE_CONFIG_DIR` no lo evita. Los `.claude/settings.json` de los padres no se aplican |
| `strict_mcp_config` | `True` | Sin él, el CLI arranca también los servidores del `.mcp.json` de la raíz |
| `mcp_servers` | Los de la sesión: el servidor en proceso de sus tools y, en el revisor visual, Playwright MCP | §11.2 |
| `tools` | `[]`, o `["Skill"]` en el writer y el editor | `tools=[]` retira también `Skill`, aunque esté en `allowed_tools` (003) |
| `allowed_tools` | La lista blanca del rol (003) | |
| `permission_mode` | El modo que deniega lo no preaprobado sin preguntar (003) | unsure: el nombre del modo en 0.2.158, probablemente `dontAsk`; se fija en el plan de 003 |
| `hooks` | `PreToolUse` y `PostToolUse` como funciones de Python | §7.5 |
| `max_turns` | `roles.<rol>.max_turns` | |
| `system_prompt` | El prompt versionado leído de Langfuse (004) | |
| `model` | `roles.<rol>.model` | |
| `env` | Ver abajo | |

**Entorno de cada sesión** (`env`):

| Variable | Valor |
|---|---|
| `ANTHROPIC_BASE_URL` | `https://openrouter.ai/api` |
| `ANTHROPIC_AUTH_TOKEN` | El valor de `OPENROUTER_API_KEY` |
| `ANTHROPIC_API_KEY` | `""`, vacía a propósito |
| `CLAUDE_CONFIG_DIR` | `<datos>/claude/` |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | `1`: apaga la telemetría, activa por defecto (`analytics_disabled: False`) |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY` | `1`: apaga la memoria automática, activa por defecto |

La salida máxima (`roles.<rol>.max_output`) llega al CLI por su variable de entorno de tokens de salida máximos (unsure: el nombre exacto; lo comprueba RF-BAS-41).

**Tools en proceso.** Cada tool se declara con `@tool` y un modelo Pydantic, cuyo `model_json_schema()` es su `input_schema`, y se agrupa en un servidor en proceso (`create_sdk_mcp_server`). El SDK la expone como `mcp__<servidor>__<tool>`: ese es el nombre que va en `allowed_tools` y el que ve el hook. El span (`tool:<identificador>`) y el audit log usan el identificador sin ese prefijo. El manejador valida con el modelo antes de ejecutar nada; si falla, devuelve el error como contenido de la tool con `is_error`.

**Hooks.** `PreToolUse` deniega con `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": <motivo>}}`, y el modelo recibe el motivo. `PostToolUse` no puede bloquear una tool ya ejecutada: solo añade contexto o sustituye su salida con `updatedToolOutput` (unsure: el nombre del campo para las tools MCP; lo comprueba RF-BAS-41).

**Desenlaces**, tal como los traduce el puerto:

| Desenlace | Cómo lo ve el SDK |
|---|---|
| `completed` | `ResultMessage` con `subtype` de éxito |
| `turns_exhausted` | `ResultMessage` y, después, `ResultError` lanzada por `query()` al agotar `max_turns`. El puerto guarda el uso del `ResultMessage` antes de la excepción |
| `time_exhausted` | El puerto llama a `ClaudeSDKClient.interrupt()` al pasar `max_agent_seconds` —el SDK no tiene tiempo máximo— y después a `disconnect()` |
| `cut` | Igual, a petición de quien abrió la sesión |
| `infrastructure_failure` | Error de conexión o del proveedor tras los reintentos del SDK |

`interrupt()` corta el turno en unos 0,02 s (`error_during_execution`, `terminal_reason=aborted_streaming`), pero deja vivo el subproceso hasta `disconnect()`, unos 0,5 s después, sin huérfanos.

**Uso.** Por OpenRouter, `AssistantMessage.usage` llega a cero en todos los turnos. El uso exacto de la sesión entera es el de `ResultMessage.usage` —`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`—, que coincide al token con OpenRouter. `total_cost_usd` es una estimación con precios de Anthropic, unas 250 veces por encima del real con modelos que no conoce: no se usa (004). El `message_id` de cada `AssistantMessage` es el id de generación de OpenRouter, `gen-…`.

**Skills.** Con `Skill` activa, un rol puede cargar las skills que trae el CLI empaquetado; el hook de policy deniega toda llamada que no pida `personalizacion-natural` (003). El SDK admite además `skills=[<nombres>]`, que rechaza las demás; no se usa, porque la política la aplica el hook.

**Windows.** uvicorn con `--reload` usa el bucle `Selector` de asyncio, que no lanza subprocesos: el SDK falla con `CLIConnectionError('Failed to start Claude Code: ')`. El servidor arranca siempre sin `--reload`.

**Doble.** `platform.agent_port` expone un protocolo (`AgentPort`) con dos implementaciones: el adaptador del SDK y `ScriptedAgent`, que recorre un guion de pasos —llamada a tool con su entrada, mensaje final, desenlace— pasando cada llamada por los mismos hooks y manejadores, en el orden `PreToolUse`, manejador y `PostToolUse`, y devuelve el uso y los ids que fije el guion.

### 5.2 OpenRouter

- Base del Agent SDK: `https://openrouter.ai/api`, con `ANTHROPIC_AUTH_TOKEN`.
- Coste facturado de una generación: `GET https://openrouter.ai/api/v1/generation?id=<gen-…>`, con la clave como `Bearer`. Responde 404 hasta que procesa la generación, así que quien la consulta reintenta con espera.
- Con modelos que no son de Anthropic, OpenRouter avisa de que Claude Code puede fallar.

### 5.3 Langfuse (SDK de Python v4)

- Cliente: `Langfuse(public_key, secret_key, base_url, mask=<función de la novela>)`. `mask` es el parámetro heredado; `mask_otel_spans`, la alternativa del v4 (004 elige).
- Arranque: `auth_check()` lanza una excepción si las claves no valen. Con claves inválidas el exportador falla en silencio: registra un 401 y el proceso termina bien.
- Spans: `start_as_current_observation(as_type="span" | "generation", name=…)`. Sesión y nombre de traza: `propagate_attributes(session_id=…, trace_name=…)`, con valores ASCII de 200 caracteres como mucho.
- Generación: `usage_details` y `cost_details`; el coste ingerido tiene prioridad sobre el que infiere Langfuse.
- Scores: `create_score(name, value, data_type, trace_id, observation_id, comment)`.
- Prompts: `create_prompt(name, prompt, labels=[])` crea una versión nueva; `get_prompt(name, label=…)` la lee por etiqueta; mover la etiqueta es actualizar las etiquetas de una versión (unsure: `update_prompt(name=…, version=…, new_labels=…)`; se confirma en el plan de 004). Langfuse pone la etiqueta `latest` a la última versión, y con ella corren las evals antes de promover (unsure: que la mueva solo). `get_prompt` guarda una caché y puede servir una versión vieja si Langfuse falla; para que un Langfuse caído no abra sesiones (§12.4), se lee sin caché ni respaldo (unsure: `cache_ttl_seconds=0` y sin `fallback`).
- Lectura de vuelta: `GET /api/public/v2/observations`. La API heredada de trazas responde 410 para esta organización. La ingesta tarda de 15 a 30 s.
- Colas de anotación y configuraciones de score, por API (017).
- Plan Hobby: 50.000 unidades al mes, 30 peticiones por minuto y una cola de anotación.

### 5.4 GitHub Actions (demostración en RF-BAS-43; verificador remoto de Lean en 009)

- Disparo: `POST /repos/{GITHUB_REPOSITORY}/actions/workflows/{LEAN_WORKFLOW}/dispatches` con `ref`, `inputs` y `return_run_details: true`, que devuelve el id de la ejecución del workflow.
- Cabeceras: `Authorization: Bearer <GITHUB_TOKEN>` y `X-GitHub-Api-Version` fijada (unsure: la fecha vigente; se fija con RF-BAS-43).
- Inputs: 65.535 caracteres en total, así que el fichero va en gzip y base64.
- Espera: `GET /repos/{…}/actions/runs/{id}` hasta `status = completed`; el resultado sale de un artefacto. Las descargas de logs y artefactos redirigen a URL que caducan en 1 minuto.
- Token de grano fino, limitado al repositorio: Actions de lectura y escritura, y Metadata de lectura.
- El job tiene solo `permissions: contents: read`, y los inputs llegan a los pasos por variables de entorno.
- La demostración de 001 usa un workflow mínimo, `lean-smoke.yml`, que compila un fichero trivial con `leanprover/lean-action`; 009 lo sustituye por `lean-verify.yml`.

### 5.5 FastMCP 4 (016)

- `mcp.http_app()` montada en FastAPI en `/mcp`, con su lifespan pasado a la aplicación: es obligatorio.
- Identidad: `JWTVerifier` con HS256, el mismo secreto, `aud` e `iss` que la API; cada tool la lee con `get_access_token()`.
- `File(format="pdf")` devuelve el PDF como recurso incrustado.

### 5.6 Playwright y Playwright MCP (013, 014)

- PDF: `page.pdf(outline=True, tagged=True)`, disponible desde la 1.42, con `channel="msedge"` sin interfaz; no se descargan navegadores.
- Al imprimir, Chromium descarta sin aviso un enlace a un ancla inexistente: de ahí `pdf-enlaces` con pypdf.
- Playwright MCP 0.0.82: `npx -y @playwright/mcp@0.0.82 --browser msedge --output-dir <dir>`. Un `--browser` inválido cae en silencio a Chrome. Bloquea `file://` por defecto. Para que el revisor visual no salga del origen de la vista previa tampoco por un clic o una redirección (003), se arranca además con su opción de orígenes permitidos (unsure: `--allowed-origins`; se comprueba en el plan de 003). En el revisor visual, `--output-dir` es `<datos>/playwright-mcp/`; en Claude Code, `.playwright-mcp/`, ignorada por git.

### 5.7 Índice: `sqlite-vec`, FTS5 y `fastembed`

- `sqlite-vec`: extensión cargable (§4.6). Distancia: `vec_distance_cosine(a, b)` sobre BLOB float32 (`sqlite_vec.serialize_float32`).
- FTS5 viene en el SQLite de CPython para Windows. Solo da candidatos (`MATCH`); BM25 se calcula en código (008).
- `fastembed`: `TextEmbedding(model_name=…, cache_dir=<datos>/models/)`. En Windows sin Visual C++ Redistributable necesita `msvc-runtime` en el venv y sus DLL en el camino de búsqueda de `onnxruntime`: un `.pth` con `import os, sys; os.add_dll_directory(sys.prefix)`. La caché de HuggingFace no puede crear enlaces simbólicos (`WinError 1314`); se desactivan por variable de entorno (unsure: la variable exacta de `huggingface_hub`; la comprueba RF-BAS-41).

### 5.8 spaCy (012)

3.8.16 con el modelo de español; con Python 3.12 carga bajo Smart App Control si las DLL de `msvc-runtime` están en el camino de búsqueda. La reputación de Smart App Control va por hash de fichero: cada versión nueva de un paquete compilado se vuelve a probar con la orden de comprobaciones.

### 5.9 Autenticación (002)

- bcrypt para la contraseña. bcrypt solo usa los 72 primeros bytes, y la 5.x lanza `ValueError` con más (unsure; lo comprueba el plan de 002). Si es así, la contraseña pasa antes por SHA-256 en base64, para que una larga funcione sin error (RF-AUT-1).
- El email se compara sin distinguir mayúsculas (`COLLATE NOCASE`, RF-AUT-3).
- PyJWT: HS256 con `JWT_SECRET`; `exp` a `access_token_hours`; `aud = "story-maker"`, `iss = "story-maker-api"`; `sub` es el id del usuario.

### 5.10 API HTTP

El contrato está en `architecture.md` §14.3. La aplicación monta los routers bajo `/api`, el servidor MCP en `/mcp` y, al final, los ficheros del frontend compilado, con la página de entrada como respuesta de toda ruta que no sea un fichero. El esquema OpenAPI se exporta con `app.openapi()` a `backend/openapi.json` desde una orden de la CLI, sin arrancar uvicorn.
