# 000 — Scaffolding

> Carril: 0 (integrador, `V2`) · Depende de: — · Estado: borrador

## Objetivo

Dejar el repositorio listo para que los carriles trabajen en paralelo sin chocar: toolchains de backend y frontend que se instalan desde sus locks y pasan en verde con las órdenes canónicas, esqueleto de módulos, marca corporativa del frontend, proyectos Lean y TLA+ vacíos que construyen, CI, lo que git versiona e ignora, y el harness de desarrollo de Claude Code (hooks, permisos, `.mcp.json` con el browser MCP, espejo de la memoria). Cubre las viñetas del encargo sobre el repositorio: sin API keys, `.claude/` commiteada, browser MCP e imagen corporativa.

El scaffolding se escribió antes que esta spec (desviación detectada por el usuario, que decidió no borrarlo): esta spec dice lo que debe cumplir; el plan verifica lo existente caso a caso y corrige lo que falle.

## Alcance

- **Backend:** Python 3.12 fijado; uv con `uv.lock`; todas las dependencias del stack declaradas de una vez (`architecture.md` §15.1); paquete `story_maker` con un subpaquete vacío por módulo de §15.9 y `tests/` en espejo; Ruff (con reglas `S`), mypy estricto y pytest configurados; la orden `story-maker` instalada, solo con `--version` (sus subórdenes llegan con sus specs).
- **Frontend:** Vite, React, TypeScript estricto, Tailwind, ESLint, Vitest, pnpm 10.x con `pnpm-lock.yaml`; `openapi-typescript` con la orden `gen:api` declarada; FSD pages-first (`app`, `pages`, `shared`); en desarrollo, proxy de `/api` a `http://127.0.0.1:8000`.
- **Marca corporativa**, definida una sola vez como tokens del tema y aplicada por la cabecera de la aplicación (logotipo y nombre «Qaracter · Story Maker»), que la ruta raíz muestra mientras no haya pantallas. Logotipo: `images/qaracter-logo.png`. Tipografías instaladas como paquetes, sin CDN. Tokens (`architecture.md` §18, «Valores de la marca»):

| Token | Valor | Uso |
|---|---|---|
| Primario | `#ff7932` | naranja del símbolo del logotipo |
| Secundario | `#233441` | pizarra del logotipo |
| Fondo | `#faf8f5` | papel de la lectura |
| Texto | `#233441` | texto corrido |
| Acento | `#ffe8da` | tinte del primario: resaltados y marca «cambiado en vN» |
| Tipografía de interfaz | Inter Tight | interfaz |
| Tipografía de lectura | Literata | capítulos y portada |

- **Formal:** `lean/`, proyecto Lake mínimo con su toolchain fijada, que compila en la CI (Lean no corre en el portátil, ADR 0004); `tla/`, carpeta de las especificaciones, con TLC en versión fijada sobre Temurin, en el portátil (Temurin portable) y en la CI (`verification.md` §4.10).
- **CI** de GitHub Actions con las comprobaciones de `verification.md` §4.6 sobre lo que existe hoy.
- **Git:** `.gitignore` y `.gitattributes` (finales LF) de la raíz.
- **Estructura raíz** de §15.9: `lean/`, `tla/`, `ejemplos/briefs/`, `presentacion/`, `images/`, `frontend/`.
- **Harness de desarrollo:** hooks `guard-secretos` y `guard-plan` con sus pruebas por entrada estándar; `.claude/settings.json` versionado con los hooks y los permisos de `verification.md` §9.6; `.mcp.json` con `playwright` y `langfuse`; espejo saneado de la memoria en `.claude/memory/`.

## Fuera de alcance

- `config.json`, ajustes del servidor y contenido de `.env.example`, esquema SQLite (con la carga de `sqlite-vec` y FTS5), API mínima, subórdenes `serve`, `init-db` y `check-env`, y README → 001-base.
- Primera generación de tipos con `gen:api`, que necesita la API → 001-base; su regeneración, en `/integrar`.
- Especificaciones TLA+, sus `.cfg` y las configs de control → 006-especificacion-tla.
- Biblioteca Lean T1–T5, auditoría de axiomas, ficheros negativos y workflow `workflow_dispatch` del `VerificadorFormal` → 007-validador-lean.
- Contenido de `backend/harness_workspace/`: 003-puerto-de-agente solo lleva el mecanismo (`agents/`, el `WorkspaceDelHarness` como mecanismo); el `CLAUDE.md` de producto, la skill y los prompts de writer y editor son de 011-produccion-de-capitulos; el prompt de cada rol restante es de su propia spec (008-brief-y-entrevista, 010-planificacion, 012-gate-de-publicacion, 014-cambios-del-lector, 017-revision-visual). Los hooks del producto (de policy y de validación de capítulo) no son los hooks de desarrollo de esta spec → 003, 005, 011.
- Navegadores de Playwright para el PDF en la CI → 013-lectura-y-pdf. Los cinco briefs de `ejemplos/briefs/` → 020-evals.
- Pantallas del producto (acceso, mis novelas, entrevista, progreso, lectura) → specs de frontend 022+.
- Escaneo del historial, triage de `pip-audit` y `pnpm audit`, `docs/security-report.md` → 021-auditoria-de-seguridad.
- Subagentes, comandos y skills de `.claude/`: proceso (`verification.md` §9.1, §9.4), sin spec; aquí solo se exige que git los versione.

## Comportamiento observable

Excepción de la 000 (`AGENTS.md`, proceso 2): el comportamiento observable son las órdenes que ejecuta un desarrollador y lo que producen, así que se nombran órdenes, rutas y herramientas.

Clases, según `verification.md` §2 (T ejecuta el sistema con entradas concretas y es lo único que se convierte en prueba; D observa el funcionamiento en un escenario realista): un caso es **T** si una prueba de la suite o un job de la CI lo ejecuta con entradas fijas y decide solo; es **D** si lo ejecuta y lo observa una persona o una sesión, fuera de la suite: un push, una sesión real de Claude Code, un navegador, o una siembra de defectos o un clon hechos a mano que ninguna prueba automatiza.

### 000-C01 · Git ignora lo generado y los secretos, y versiona lo que se entrega (T)
- **Dado** el repositorio con su `.gitignore` de la raíz
- **Cuando** una prueba pregunta a git (`git check-ignore`) por cada ruta de abajo, exista o no
- **Entonces** están ignoradas: `backend/.venv/`, `frontend/node_modules/`, `frontend/dist/`, `lean/.lake/`, `backend/data/` (el directorio de datos sin `STORY_MAKER_DATA_DIR`, `architecture.md` §15.5), `.playwright-mcp/`, las cachés de Python (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.hypothesis/`) a cualquier profundidad, lo que genera TLC en `tla/` (directorio de estados, trazas y el `tla2tools.jar` descargado), `.env`, `backend/.env` y `.claude/settings.local.json`
- **Y no** están ignoradas: `.env.example`, `.mcp.json`, `.gitattributes`, `.claude/settings.json`, `.claude/hooks/`, `.claude/agents/`, `.claude/commands/`, `.claude/skills/`, `.claude/memory/`, `backend/uv.lock`, `backend/.python-version`, `frontend/pnpm-lock.yaml`, `frontend/src/shared/api/schema.d.ts` (generado, pero se versiona), `backend/tests/data/` (un `data` que no es el directorio de datos), `images/qaracter-logo.png`, `ejemplos/briefs/`, `ejemplos/novela-ejemplo.pdf` y los ficheros de `presentacion/` (ningún patrón ignora PDF ni presentaciones)

### 000-C02 · Git guarda los ficheros de texto con LF y no convierte los binarios (T)
- **Dado** el repositorio con un `.gitattributes` que declara `* text=auto eol=lf` (`architecture.md` §15.3)
- **Cuando** una prueba lista los finales de línea del índice (`git ls-files --eol`) y, en un repositorio temporal con ese `.gitattributes` y `core.autocrlf=true` (como en Windows), añade un fichero de texto escrito con CRLF y otro con LF
- **Entonces** ningún fichero de texto del índice tiene CRLF; el fichero escrito con CRLF entra en el índice con LF; `git add` no avisa de conversiones LF→CRLF; `images/qaracter-logo.png` figura como binario, sin conversión

### 000-C03 · El backend se instala desde su lock y su verificación pasa sin credenciales (T)
- **Dado** un clon sin `.env`, sin variables de proveedor ni de Langfuse y sin sesión de Claude Code, como la CI
- **Cuando**, desde `backend/`, se ejecuta `uv sync` (en la CI, `uv sync --frozen`) y después `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .` y `uv run mypy src`
- **Entonces** `uv.lock` no cambia; el entorno usa Python 3.12.x (una prueba lo comprueba); `uv run story-maker --version` imprime la versión declarada del paquete y sale con 0; pytest recoge al menos una prueba y pasa; las otras tres órdenes salen con 0

### 000-C04 · Cada dependencia del stack del backend se importa en el entorno instalado (T)
- **Dado** el entorno de 000-C03, en el portátil Windows y en la CI Linux
- **Cuando** una prueba importa `fastapi`, `uvicorn`, `pydantic`, `sqlalchemy`, `sqlite_vec`, `fastembed`, `claude_agent_sdk`, `langfuse`, `fastmcp`, `playwright`, `pypdf`, `jinja2`, `bcrypt`, `jwt` (PyJWT), `typer`, `pytest_asyncio` e `hypothesis`, y se piden sus versiones a `detect-secrets` y `pip-audit` como módulos del entorno (`uv run python -m detect_secrets --version`, `uv run python -m pip_audit --version`; Smart App Control puede bloquear el lanzador `.exe` que uv genera para cada orden)
- **Entonces** todo se importa y responde; `pydantic` y `sqlalchemy` son de la versión mayor 2 y `langfuse` de la 4; en Windows, `fastembed` se importa con el runtime de C++ que declara el proyecto (`architecture.md` §15.3), sin pasos fuera de `uv sync`

### 000-C05 · El paquete tiene un subpaquete por módulo y `domain` no importa el resto (T)
- **Dado** el paquete `story_maker` instalado
- **Cuando** una prueba importa `story_maker.<módulo>` para cada módulo de `architecture.md` §15.9 (`domain`, `store`, `agents`, `policy`, `observability`, `interview`, `pipeline`, `retrieval`, `validators`, `formal`, `lint`, `render`, `api`), y la prueba de la regla de dependencias (`verification.md` §3.3) analiza textos de ejemplo y los ficheros reales de `domain`
- **Entonces** los trece se importan y `backend/tests/` tiene una carpeta por módulo; la regla (`domain` no importa nada del proyecto, `architecture.md` §15.9 regla 1) rechaza, nombrando fichero e importación, `from story_maker.store import X`, `import story_maker.store`, `from story_maker import config` y `from ..store import X`; acepta `import unicodedata`, `from pydantic import BaseModel`, `from story_maker.domain.rules import X` y `from .rules import X`; sobre el `domain` real (hoy vacío) pasa

### 000-C06 · El frontend se instala desde su lock y su verificación pasa (T)
- **Dado** un clon con Node y pnpm 10.x (`pnpm.cmd` en Windows)
- **Cuando**, desde `frontend/`, se ejecuta `pnpm.cmd install` (en la CI, `pnpm install --frozen-lockfile`) y después `pnpm.cmd lint`, `pnpm.cmd typecheck`, `pnpm.cmd build` y `pnpm.cmd test`
- **Entonces** `pnpm-lock.yaml` no cambia; lint y typecheck salen con 0; build deja `frontend/dist/index.html` con sus recursos, incluidas las dos tipografías de marca; `pnpm.cmd test` ejecuta Vitest una sola vez, sin modo vigilancia, recoge al menos una prueba, pasa y termina

### 000-C07 · La SPA muestra la cabecera de marca en la ruta raíz (T)
- **Dado** el frontend, todavía sin pantallas del producto
- **Cuando** una prueba de Vitest renderiza la aplicación en `/`
- **Entonces** se ve una imagen con texto alternativo «Qaracter» y el nombre «Qaracter · Story Maker» como encabezado

### 000-C08 · El tema define la marca y el logotipo es el de `images/` (T)
- **Dado** el tema del frontend y `frontend/src/`
- **Cuando** una prueba lee la definición de tokens y busca los ficheros de logotipo
- **Entonces** existen los siete tokens de la tabla de Alcance con esos valores exactos; las dos tipografías se cargan desde paquetes instalados, no desde una URL; hay un único fichero de logotipo en `frontend/src/` y es idéntico, byte a byte, a `images/qaracter-logo.png`

### 000-C09 · `guard-secretos` decide por la forma del texto nuevo (T)
- **Dado** el hook recibiendo por su entrada estándar la carga JSON de una tool `Write`, `Edit` o `MultiEdit`, como la envía Claude Code
- **Cuando** el texto nuevo (`content` de `Write`; `new_string` de `Edit` y de cada edición de `MultiEdit`) es el de la tabla
- **Entonces** responde lo de la tabla. *Deniega* = sale con código 2 y un motivo en la salida de error que nombra el tipo de clave y el fichero de destino y **nunca reproduce la clave**; *deja pasar* = sale con código 0. Un prefijo «empieza palabra» si va al inicio del texto o tras un carácter que no es letra, dígito ni `_`.

| Texto nuevo | Resultado |
|---|---|
| Cualquiera de los seis prefijos de clave de `verification.md` §9.6 (secreta y pública de Langfuse, OpenRouter, Anthropic, token clásico y token de grano fino de GitHub), empezando palabra, seguido de 20 caracteres de `[A-Za-z0-9_-]` | Deniega |
| El mismo prefijo seguido de 19 caracteres | Deja pasar |
| El prefijo solo, citado en un doc | Deja pasar |
| El prefijo pegado a una letra anterior (dentro de otra palabra) y seguido de 20 caracteres | Deja pasar |
| `Basic ` seguido de 40 caracteres de base64 | Deniega |
| `Basic ` seguido de 39 caracteres de base64 | Deja pasar |
| `LANGFUSE_SECRET_KEY=` vacío, o con el marcador `TU_CLAVE_AQUI` | Deja pasar |
| Una clave con forma real solo en la segunda edición de un `MultiEdit` | Deniega |
| Un `Edit` cuyo `old_string` tiene la clave y cuyo `new_string` es un marcador (limpiar una fuga) | Deja pasar |
| Una clave con forma real con destino `.env` | Deniega: tampoco ahí escribe Claude secretos |
| Texto sin claves | Deja pasar |

Las claves de las pruebas son falsas, llevan un marcador de prueba evidente y se construyen al ejecutarse (000-I4).

### 000-C10 · `guard-plan` bloquea pruebas y código sin plan aprobado con pasos pendientes (T)
- **Dado** el hook con la carga JSON de `Write`, `Edit` o `MultiEdit` y el `TODO.md` de la raíz del proyecto que le indica Claude Code
- **Cuando** la ruta de destino y el estado de `TODO.md` son los de la tabla
- **Entonces** responde lo de la tabla: *deniega* con código 2 y un motivo que nombra la ruta y lo que falta; *deja pasar* con código 0. Rutas guardadas (`verification.md` §9.6), la puerta «Write tests or code» de `AGENTS.md`: `backend/src/**`, `backend/tests/**`, `frontend/src/**`, `frontend/tests/**`, `lean/**`, `tla/**` y `.github/workflows/**`. Un bloque va de su `## NNN — <nombre>` al siguiente `## `; tiene el plan aprobado si contiene la línea `- [x] Plan below approved`, con o sin sufijo; un paso pendiente es un `- [ ]` bajo su `### Steps`, nunca bajo `### Closing`.

| Ruta de destino | `TODO.md` | Resultado |
|---|---|---|
| `backend/tests/test_x.py` | ningún bloque con el plan aprobado | Deniega (hoy pasa: rechazo explícito) |
| `backend/src/story_maker/domain/x.py`, `frontend/src/app/x.tsx`, `frontend/tests/x.test.ts`, `lean/X.lean`, `tla/Harness.tla`, `.github/workflows/ci.yml` | ningún bloque con el plan aprobado | Deniega |
| Cualquier ruta guardada | no existe | Deniega |
| `backend/src/…` | un bloque con `- [ ] Plan below approved` y pasos `- [ ]` | Deniega |
| `backend/src/…` | un bloque con el plan marcado y todos sus pasos `- [x]`; solo el cierre pendiente | Deniega |
| `backend/src/…` | un bloque con `- [x] Plan below approved — auditor 2026-09-25: <acta>` y al menos un `- [ ]` en `### Steps` | Deja pasar |
| `docs/…`, `specs/…`, `TODO.md`, `README.md`, `.claude/…`, `backend/pyproject.toml`, `frontend/package.json`, `backend/harness_workspace/…` (fuera de la puerta por `verification.md` §9.6), una ruta fuera del proyecto | cualquiera | Deja pasar |
| Ruta absoluta de Windows con `\` y letra de unidad en minúscula (`c:\…\backend\tests\…`) | ningún bloque con el plan aprobado | Deniega, igual que la relativa |

### 000-C11 · Los ajustes del proyecto registran los hooks y las denegaciones (T)
- **Dado** `.claude/settings.json` versionado
- **Cuando** una prueba lo lee
- **Entonces** registra `guard-secretos` y `guard-plan` en `PreToolUse` con el matcher `Edit|Write|MultiEdit`, cada uno como una orden `node` sobre su script de `.claude/hooks/` con la ruta tomada de `${CLAUDE_PROJECT_DIR}` (no relativa al directorio actual); y, según `verification.md` §9.6:
  - `permissions.deny` es exactamente `Read(.env)`, `Read(**/.env)`, `Read(.claude/settings.local.json)`, `Bash(git push --force*)` y `Bash(git push -f*)`;
  - `permissions.allow` es exactamente `Bash(uv *)`, `Bash(pnpm.cmd *)`, `Bash(node *)`, `Bash(java *)`; git de lectura: `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git show*)`; commit: `Bash(git add*)`, `Bash(git commit*)`; `Bash(git worktree*)`, `Bash(git merge*)`, `Bash(git rebase*)` y `Bash(git branch*)`. Ninguna entrada de `allow` cubre `git push`, así que otras formas de forzar (`+rama`, la opción tras el remoto) piden permiso;
  - `permissions.additionalDirectories` es exactamente `../sm-a`, `../sm-b`, `../sm-c`, `../sm-d` y `../sm-e`

### 000-C12 · El espejo de memoria está completo y saneado (T)
- **Dado** `.claude/memory/`
- **Cuando** una prueba lo recorre
- **Entonces** tiene un README que explica el espejo, su índice (`MEMORY.md`, como el original) y un fichero por entrada del índice, sin ficheros sin entrada ni entradas sin fichero; ningún fichero contiene una dirección de correo, una ruta de perfil de usuario (`C:\Users\…`, `/home/…`, `/Users/…`), un identificador con forma de UUID ni el nombre de la empresa. Que las entradas coinciden con la memoria original lo revisa el `verificador` (000-I10)

### 000-C13 · Cada herramienta falla ante su defecto sembrado (D)
- **Dado** el scaffolding en verde
- **Cuando** se siembra en local, de uno en uno y sin commit, cada defecto de la tabla y se ejecuta su orden
- **Entonces** cada orden falla por ese defecto y, al retirarlo, vuelve a salir con 0

| Defecto sembrado | Orden | Falla por |
|---|---|---|
| Una función sin anotaciones en `backend/src/` | `uv run mypy src` | mypy estricto |
| `eval()` sobre una entrada en `backend/src/` | `uv run ruff check .` | una regla `S` de Ruff |
| Un módulo de `domain` que importa `story_maker.store` | `uv run pytest` | la regla de 000-C05 |
| Un parámetro sin tipo en un componente | `pnpm.cmd typecheck` | TypeScript estricto |
| Una variable declarada y sin usar en un componente | `pnpm.cmd lint` | ESLint |
| `#ff0000` en un componente | `pnpm.cmd test` | 000-I3 |

### 000-C14 · Un clon limpio funciona en el portátil (D)
- **Dado** un `git clone` local de `V2` en una ruta hermana corta (`../sm-limpio`, por `LongPathsEnabled=0`), sin `.env`
- **Cuando** se ejecutan las órdenes de 000-C03 y 000-C06 y las pruebas de los hooks (`node --test`, sin instalar nada para ellas)
- **Entonces** todo sale en verde con `pnpm.cmd` y Python 3.12, sin pasos fuera de esas órdenes; ni la raíz, ni `.claude/`, ni `.claude/hooks/` (donde Node buscaría paquetes para los hooks) tienen `package.json` ni `node_modules`; el clon tiene `lean/`, `tla/`, `ejemplos/briefs/`, `presentacion/`, `images/qaracter-logo.png`, `frontend/` y el esqueleto del backend; ninguna orden avisa de conversiones LF→CRLF; después, `git status --porcelain` no lista nada. El clon se borra al terminar

### 000-C15 · Claude Code conecta los servidores de `.mcp.json` (D)
- **Dado** `.mcp.json` en la raíz con `playwright` (`@playwright/mcp@0.0.82`, `--browser msedge`, `--output-dir .playwright-mcp`) y `langfuse` (el servidor MCP de Langfuse Cloud UE por HTTP, con la cabecera de autorización tomada de la variable `LANGFUSE_MCP_AUTH`)
- **Cuando** se abre Claude Code en la raíz, se aprueban los servidores del proyecto en `/mcp` y el usuario tiene en su entorno un `LANGFUSE_MCP_AUTH` válido
- **Entonces** `/mcp` lista los dos conectados y `langfuse` responde a una consulta (por ejemplo, listar prompts); sin la variable o con una inválida, `langfuse` falla con un error de autorización y `playwright` sigue disponible. Resultado en `verification.md` §9.2, columna «Verificado»

### 000-C16 · Playwright MCP inspecciona la SPA en Edge: marca, mismo origen y proxy de `/api` (D)
- **Dado** el servidor de desarrollo de Vite escuchando en `http://127.0.0.1:5173` y un servidor HTTP de prueba en `127.0.0.1:8000` que responde a `/api/ping`
- **Cuando** Claude Code abre `http://127.0.0.1:5173/` con Playwright MCP, toma la instantánea, lee los estilos calculados y las peticiones de red, navega a `/api/ping` y después intenta abrir la página por `file://`
- **Entonces** abre en Edge; la instantánea muestra la imagen «Qaracter» y el encabezado «Qaracter · Story Maker»; el título de la pestaña es «Qaracter · Story Maker»; el fondo calculado es `#faf8f5`, el color del texto `#233441` y la familia tipográfica Inter Tight; todas las peticiones van a `127.0.0.1`; `/api/ping` devuelve la respuesta del servidor de prueba; `file://` se rechaza; lo que guarda la inspección queda en `.playwright-mcp/`. Fila en `verification.md` §9.3

### 000-C17 · En una sesión real, los hooks y los permisos actúan (D)
- **Dado** `.claude/settings.json` activo, una sesión nueva de Claude Code abierta en la raíz del proyecto y un worktree temporal en una ruta hermana corta (`../sm-guard`), de una rama desechable, cuyo `TODO.md` no tiene ningún plan aprobado con pasos pendientes
- **Cuando** a la sesión de la raíz se le pide, por turnos: leer `.env`; escribir en un fichero de prueba fuera de las rutas guardadas una clave falsa con la forma de 000-C09 y un marcador de prueba evidente (por ejemplo, «TEST» repetido); lo mismo tras `cd backend`; `git push --force --dry-run`; `uv run pytest` desde `backend/`. Después, en una segunda sesión nueva abierta en la raíz del worktree temporal (desde la raíz del proyecto sería una ruta de fuera, que 000-C10 deja pasar), se le pide escribir en `backend/tests/` de ese worktree
- **Entonces** la lectura de `.env` se deniega sin mostrar nada de su contenido; las dos escrituras con la clave se bloquean con el motivo de 000-C09; `git push --force` se deniega sin ejecutarse; `uv run pytest` corre sin pedir permiso; la escritura de la segunda sesión se bloquea con el motivo de 000-C10, leído del `TODO.md` del worktree. Se borran el worktree y la rama; resultado en `verification.md` §9.6

### 000-C18 · La primera CI de `V2` sale en verde, con Lean y TLC (D)
- **Dado** el repositorio en GitHub (GitHub Free) con el workflow de CI, y un push a `V2` que decide el usuario
- **Cuando** corre la CI
- **Entonces** terminan en verde, en Linux, los jobs de `verification.md` §4.6: `backend` (`uv sync --frozen`, `ruff check`, `ruff format --check`, `mypy src`, `pytest`); `frontend` (`pnpm install --frozen-lockfile`, typecheck, lint, test, build, y además `node --test` de los hooks de desarrollo de 000-C09 y 000-C10, sin paso de instalación aparte); un único job `formal` (`lake build --wfail` de `lean/` con su toolchain fijada; `tla2tools.jar` de una versión fijada, nunca «latest», sobre Temurin: TLC arranca e informa de su versión y, con `tla/` sin especificaciones, lo dice en el registro y no falla); y `seguridad` (`detect-secrets` sin hallazgos, bloqueante; `pip-audit` y `pnpm audit` informan sin cambiar el resultado del job). Ningún job usa secretos del repositorio

### 000-C19 · La CI se pone en rojo ante defectos sembrados (D)
- **Dado** una PR a `V2` desde una rama desechable, que decide el usuario, con una prueba de pytest que falla, una de Vitest que falla y un texto que `detect-secrets` marca como secreto (falso, con marcador de prueba)
- **Cuando** corre la CI
- **Entonces** `backend`, `frontend` y `seguridad` terminan en rojo, cada uno por su defecto, y la PR queda marcada como fallida; se cierra sin fusionar y se borra la rama: `V2` no cambia

### 000-C20 · TLC arranca en el portátil sobre Temurin portable (D)
- **Dado** el portátil Windows sin administrador, con un Temurin portable (descomprimido, sin instalador) de la versión fijada y, en `tla/`, el `tla2tools.jar` de la versión fijada, la misma que usa la CI (000-C18)
- **Cuando** se ejecuta `java -version` con el `java` de ese Temurin y después se arranca TLC con él sobre ese jar
- **Entonces** `java -version` informa de Temurin en la versión fijada; TLC arranca sin que Smart App Control lo bloquee ni pida administrador e informa de su versión, que es la fijada; el jar no aparece en `git status` (000-C01)

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 000-I1 | Toda herramienta se obtiene en una versión fijada: Python 3.12 (`.python-version`), dependencias por `uv.lock` y `pnpm-lock.yaml`, pnpm 10.x, toolchain de Lean en `lean/`, `tla2tools.jar` y Temurin en el portátil y en la CI (la misma versión en los dos), `@playwright/mcp@0.0.82`; nada se instala como «latest» | I | `verificador`: workflow, `.mcp.json` y ficheros de toolchain; Python 3.12, además, en 000-C03; TLC y Temurin, en 000-C18 y 000-C20 |
| 000-I2 | Las dependencias del stack se declaran todas en la 000; un carril no edita `pyproject.toml`, `uv.lock`, `package.json` ni `pnpm-lock.yaml`: lo que falte lo añade el integrador | I | `/integrar` revisa el diff de cada carril |
| 000-I3 | Fuera de la definición de tokens, ningún fichero de `frontend/src/` contiene un color hexadecimal ni declara una familia tipográfica | T | Prueba que recorre `frontend/src/`; que puede fallar, 000-C13 |
| 000-I4 | Ningún fichero versionado contiene una cadena con forma de clave: las pruebas de `guard-secretos` construyen sus claves falsas al ejecutarse y `.mcp.json` solo nombra `LANGFUSE_MCP_AUTH` | T | `detect-secrets` sobre los ficheros versionados, en local y bloqueante en la CI (000-C18, 000-C19); `guard-secretos` en cada escritura |
| 000-I5 | Los hooks deciden igual con el directorio actual en un subdirectorio | T | Las tablas de 000-C09 y 000-C10 repetidas con el directorio actual en `backend/` |
| 000-I6 | mypy estricto sobre `src/`, Ruff con reglas `S`, TypeScript estricto y ESLint cubren todo el código | A | Las herramientas en 000-C03 y 000-C06; que no pasan en vacío, 000-C13 |
| 000-I7 | La SPA no pide tipografías, estilos ni scripts a otros orígenes | D | 000-C16 |
| 000-I8 | En el frontend, importaciones solo hacia abajo (`app` → `pages` → `shared`) y cada slice expone su `index.ts`; en el backend, la regla de dependencias más allá de `domain` | I | `verificador` al cerrar cada spec (`verification.md` §3.3, §3.7) |
| 000-I9 | La CI corre en cada push y PR a `V2` con las comprobaciones de `verification.md` §4.6, sin secretos del repositorio y sin llamar a un modelo ni a Langfuse | I | Revisión del workflow; demostrada en 000-C18 y 000-C19 |
| 000-I10 | El espejo de `.claude/memory/` lista los mismos ficheros que la memoria automática del proyecto | I | `verificador` en cada cierre (`verification.md` §9.5) |
| 000-I11 | Los hooks y sus pruebas usan solo la biblioteca estándar de Node: no hay nada que instalar para ellos | D | 000-C14: `node --test` pasa en un clon limpio sin instalar nada para ellos, sin `package.json` ni `node_modules` en la raíz ni en `.claude/` |

## Scores y trazas

No aplica: la 000 no ejecuta validadores del producto ni emite trazas.

## Docs referenciados

- `architecture.md` §14.8 (frontend, marca, proxy, tipos generados), §15.1 (stack), §15.3 (entorno Windows; LF en el índice), §15.5 (directorio de datos por defecto `backend/data/`; `LANGFUSE_MCP_AUTH`, solo desarrollo), §15.9 (organización del backend y regla de dependencias), §16.20 (Claude Code en el desarrollo), §18 (organización del frontend, cliente de la API, dónde corre Lean, valores de la marca, forma de clave de `guard-secretos` — 000-C09); ADR 0004.
- `verification.md` §2 (clases), §3.1–§3.3 (tipos, análisis estático, regla de dependencias), §3.7 (sin contratos de importación), §4.6 (CI, un job `formal`), §4.10 (TLC en el portátil y en la CI), §5 (filas R.2 —clon limpio, 000-C14—, R.10, R.12, R.13, P.1), §6 (U28), §9.2 (servidores MCP), §9.3 (log del browser MCP), §9.5 (espejo de memoria), §9.6 (hooks, rutas guardadas y permisos).
- `definitions.md` §11.3 (ajustes del servidor; `LANGFUSE_MCP_AUTH` no es del producto).
- `AGENTS.md` (proceso 2, excepción de la 000; puerta «Write tests or code»; formato de `TODO.md` y del acta del `auditor`), `CLAUDE.md` raíz (órdenes canónicas, trampas del entorno, secretos), `backend/AGENTS.md` y `frontend/AGENTS.md` (stack, órdenes, módulos, propiedad de la 000, marca).
- `project-constraints.md`, «Los repositorios deben incluir»: sin API keys (000-C01, 000-C09, 000-I4), `.claude/` commiteada con la memoria (000-C01, 000-C12), config MCP con un browser MCP (000-C15, 000-C16); «Presentación»: imagen corporativa con `images/qaracter-logo.png` (000-C07, 000-C08, 000-C16); §5c y §5d: `lake build` y TLC con la config en el repo, como herramienta (000-C18, 000-C20).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué posee la 000? | Manifiestos y locks, esqueleto del paquete, config de herramientas, CI, `src/app/` y `shared/ui/` del frontend, hooks, `.mcp.json` y espejo | `backend/AGENTS.md`, `frontend/AGENTS.md` (propiedad) |
| ¿Cuándo es T un caso y cuándo D? | T: una prueba de la suite o un job de la CI lo decide solo; D: lo ejecuta y lo observa una persona o una sesión (push, sesión real, navegador, siembra o clon a mano) | `verification.md` §2, §4.6 (la CI es T) |
| ¿Qué valores tiene la marca? | Los de la tabla de Alcance: primario y secundario del logotipo; fondo, texto y acento derivados; Inter Tight y Literata | `architecture.md` §18, «Valores de la marca» |
| ¿Tipografías por CDN? | No: empaquetadas; ningún tercero ve al lector y la SPA no depende de red externa | `architecture.md` §18, «Valores de la marca» |
| ¿Página de inicio? | No hay pantalla de inicio en los docs: la ruta raíz muestra la cabecera de marca de la aplicación, que reutilizarán las pantallas; la 000 no posee slices de `pages/` | `architecture.md` §14.8, §18 («Valores de la marca»), `frontend/AGENTS.md` |
| ¿Qué rutas guarda `guard-plan`? | Las siete de la puerta «Write tests or code»: `backend/src`, `backend/tests`, `frontend/src`, `frontend/tests`, `lean`, `tla`, `.github/workflows` | `verification.md` §9.6, `AGENTS.md` |
| ¿Y los manifiestos, `backend/harness_workspace/` y `.claude/`? | Sin guardar: los escribe solo el integrador y los revisan `/integrar` y el `verificador` | `verification.md` §9.6 |
| ¿Qué es el «cuerpo» de una clave? | 20 o más caracteres de `[A-Za-z0-9_-]` tras un prefijo que empieza palabra; `Basic ` + 40 o más de base64 | `architecture.md` §18, fila «Forma de clave de `guard-secretos`» |
| ¿Qué entradas son «git de lectura» y «commit» en `allow`? | Lectura: `status`, `diff`, `log`, `show`; commit: `add` y `commit`; nada que publique (`push`) | Decisión sobre `verification.md` §9.6: lo mínimo que usan los carriles |
| ¿Desde qué sesión se demuestra `guard-plan` en un worktree? | Una sesión nueva abierta en la raíz del worktree: el hook lee el `TODO.md` de la raíz de su sesión y trata lo demás como ruta de fuera | 000-C10, `verification.md` §9.6 |
| ¿Con qué se verifica que los hooks no dependen de paquetes? | Con el clon limpio de 000-C14 (D), invariante aparte de la independencia del directorio actual (T) | `verification.md` §2 |
| ¿Excepción para escribir en `.env`? | No: los secretos los escribe el usuario a mano | `verification.md` §9.6, `CLAUDE.md` (Secretos) |
| ¿Y si el hook falla? | Claude Code solo bloquea con código 2; otro fallo deja pasar la tool. Por eso, sin `TODO.md`, `guard-plan` deniega | Contrato de los hooks `PreToolUse` |
| ¿Corren en la CI las pruebas de los hooks? | Sí: además de en local, `node --test` corre en el job `frontend`, que ya trae Node y no necesita paso de instalación aparte (000-C18) | `verification.md` §4.6, §9.6 |
| ¿TLA+ sin especificaciones? | La CI trae TLC fijado y lo arranca; especificaciones, `.cfg` y config de control, 006 | `verification.md` §4.10 |
| ¿Dónde corre TLC? | En el portátil, sobre Temurin portable (000-C20), y en la CI (000-C18), con la misma versión fijada | `verification.md` §4.10 |
| ¿Uno o dos jobs formales? | Uno: `formal`, con Lean y TLC | `verification.md` §4.6 |
| ¿Directorio de datos por defecto? | `backend/data/`, ignorado por git; 001 lo usa | `architecture.md` §15.5 |
| ¿Proxy de `/mcp` en desarrollo? | No: la SPA solo habla con `/api` | `architecture.md` §14.8 |
| ¿`fastembed` en Windows? | Se importa tras `uv sync`, con `msvc-runtime` y su directorio de DLL; el mecanismo, en el plan | `architecture.md` §15.3 |
| ¿Dependencias que los docs no nombran (cargador de `.env`, cliente HTTP de pruebas)? | No se inventan; el integrador las añade cuando una spec las pida | `backend/AGENTS.md` |
| ¿Finales de línea? | LF en el índice; binarios sin conversión | `architecture.md` §15.3 |
| ¿Cubre `Bash(git push --force*)` también `-f` y `+rama`? | `-f` sí: `permissions.deny` añade `Bash(git push -f*)`. `+rama` y la opción tras el remoto no tienen patrón de permiso que las cubra, así que piden permiso en la sesión (ni deniegan ni permiten solas) | `verification.md` §9.6 |
| ¿Escrituras por Bash (`node -e`, redirecciones)? | No pasan por `guard-secretos`: riesgo aceptado; las caza `detect-secrets` en la CI | `verification.md` §6 U28 |
