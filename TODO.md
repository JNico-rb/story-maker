# TODO — planes de implementación

Reglas (detalle en `AGENTS.md`, procesos 2–4 y *Parallel lanes*):

1. Un bloque por spec, en orden numérico, con el formato de `AGENTS.md` proceso 3. Ningún código, tampoco el scaffolding, antes de que su spec y su plan estén aprobados.
2. Las casillas de aprobación las marca el integrador, sin revisión (decisión del usuario, 2026-09-24); las de cierre, `verificador`. Los pasos D quedan `[ ]` con `(D, al final)` y no impiden cerrar.
3. Un paso se marca `[x]` solo cuando su caso pasa a verde.
4. Cada carril edita solo los bloques de sus specs; esta cabecera y sus tablas son del integrador (checkout principal, V2).
5. Una spec empieza cuando sus dependencias están cerradas en V2, o en la rama de su propio carril.

## Estado (2026-09-25)

**Integradas en V2:** 012 (gate), carril W (workspace de producto), 020 parcial (C01, C02, C05, I1), 029 (cli, cerrada recortada), 000 (D al final), 026 (frontend, lectura), presentación (esqueleto del deck en Marp, `presentacion/deck.md`), 001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 013, 020 parcial (C06–C09, I2), 016 (cerrada recortada) y 022 (frontend).

### Alcance

- **N1 · MVP:** 008, 010, 016 (cerrada recortada), 011, 012 (sin la etapa de revisión visual, recortado), 020, 014, 029-cli; frontend mínimo: 022 (cerrada), 026 y 027. La configuración va por la CLI (`architecture.md` §18, «Alcance del frontend»).
- **Recortes de casos C:** 011 ninguno (todos hechos; I1, I5, I7, I9, I10, I11 recortados). 012: C6, C8, C12 recortados. 029: C02, C03, C04, C09, C10, C11, C12, C13, C14, I1, I2, I3 recortados (el cambio va por la web). 026: I1, I3, I4, I5 recortados. 027: I1, I2, I3, I5 recortados.
- **Fuera de N1:** N2 (018 C18–C23, después 017); N3 (019, 015, 021, el resto de 016, 023, 024, 025, 028); congelado 030 (patch en `~/sm-archivo/030-carril-j.patch`).
- **Alcance completo (usuario, 2026-09-25, segunda decisión: «corregir todos los errores, huecos y puntos a medias»; importa sobre todo poder modificar la novela donde se quiera):** entran N2 y N3 — 018 C18–C23, 019, 028, 023 completa, 024, 025, 015, 017, 021 y 030 — y los errores hallados en la tanda D. Orden: edición manual (018→019→028) y web completa (023→024→025) primero; después 015→021, 017, 030. Los «(recortado)» de specs cerradas vuelven por carriles sin conflicto: 029 (C, CLI de entrevista y de cambio), las I T de 010, 011 y 014 (I); 012 C6, C8, C12 tras integrar F y Q. El frontend queda congelado (usuario, 2026-09-25): nadie toca `frontend/`.

**Pasos D del lote final:** 020-C16 y 004-C14 (hito primera novela); después 000-C15, 000-C16 (Playwright MCP en Edge, registrado en `docs/verification.md` §9.3), y 020-C10 a C14. El resto de pasos D queda sin marcar.

**Arranque de la tanda D (decisión del usuario, 2026-09-25, por velocidad):** empieza en cuanto 031 y 020-C03, C04, C15 estén en V2, sin esperar a 014 parte B. El cambio del lector (020-C14, 014-C20) y el tuning (020-C11) van cuando llegue la parte B.

**Aceleración (usuario, 2026-09-25, plazo < 10 h):** 5 generaciones completas en total; la novela de ejemplo es la del brief 1 de las evals (020-C16), que se genera primero. En cuanto se publica, en paralelo a los briefs 2–5: recorridos de Playwright (026-C14, 000-C15/C16) sobre una copia de la base (un segundo `serve` sobre la misma base tomaría la cola y marcaría `interrupted` la ejecución en curso) y la plantilla de revisión humana lista. Durante un paso, el implementador corre solo las pruebas de su módulo; la suite completa, una vez antes de cada commit, nunca se salta. Reintentos, umbrales y rúbricas no se tocan.

**Modelos:** implementador sonnet por defecto, opus en 012 y 014; verificador sonnet.

**Protocolo de integración:** verificador PASS → commit en el carril → `git merge --no-ff` en V2 → suite completa → `git push origin V2`. Rojo → `git reset --merge ORIG_HEAD`.

**Paralelo:** un worktree por carril, cada uno solo en sus módulos propios; dentro de un worktree, los subagentes en serie.

**Un chat por tarea.** Termina con una línea `LISTO <rama> <NNN> <hash> [parcial|cerrada]` o `BLOQUEADO <motivo>`.

**Tareas humanas:** revisión humana del brief 1 (020-C12, en la tanda D), vídeo, MyFactory, email de entrega (borrador del integrador al final), deck y su PDF. Hechas: `GITHUB_TOKEN` en `.env`, MCP de Langfuse conectado.

## Carriles

| Carril | Specs en orden | Depende de (fuera del carril) | Worktree | Rama | Estado |
|---|---|---|---|---|---|
| 0 — integrador | 000 | — | checkout principal | `V2` | cerrada (D al final) |
| A | 014 parte A (C01–C11, I1–I4, I6, I11) | 012 | `../sm-a` | `carril-a` | parte A cerrada e integrada |
| B | 014 parte B (C12–C19 y sus I no recortadas), en paralelo a la A desde `carril-a`. Toca `pipeline/changes/`, `orchestrator.py`, `production.py`, `runs.py`, `windows.py` y sus pruebas; nunca `store/models.py`, `composition.py`, `cli.py`, `api/app.py`, `agents/`, `planning_seam.py` | — | `../sm-b` | `carril-b` | cerrada e integrada (C20 D) |
| D | 020 (C01, C02, C05, I1 integrados; C03, C04 y C15 pasan al carril X, tras el arranque) | — | `../sm-d` | `carril-d` | parcial integrada |
| X | 031 (C01–C04, I2). Toca `composition.py`, `cli.py`, `api/app.py`, `agents/port.py`, `planning_seam.py` | 012 | `../sm-x` | `carril-x` | C01–C05, I2 hechos; cierre en curso |
| V | 020-C03 (con el arreglo de D2), C04, C15 y C17, desde `carril-x`: el camino a la tanda D. Toca `cli.py`, `composition.py`, `store/models.py` (el brief de eval de la novela) y las pruebas de evals | 031 | `../sm-v` | `carril-v` | cerrada e integrada (pasos no D) |
| T | bug de 020 hallado en la tanda D: `evals table` busca los validadores con el nombre de fila entre comillas invertidas y espera un `detail` distinto del que escriben 011/012, así que da `n/a` con resultados reales. Toca solo `cli.py` (tabla de evals) y `tests/test_cli_evals*.py` | 020 | `../sm-t` | `carril-t` | cerrado e integrado |
| U | 020-C18, hueco hallado en la tanda D: las prohibidas de nivel user de un brief de evals se filtraban a los demás briefs del mismo cliente. Toca solo `cli.py` (importación de evals y `example`) y `tests/test_cli_evals*.py` | 020 | `../sm-u` | `carril-u` | parado sin commits: C18 aplazado por el usuario |
| Y | 031-C05 (adaptador de incrustaciones, solo `retrieval/`) | — | `../sm-y` | `carril-y` | cerrada e integrada |
| E | 026 → 027 (027 con la API simulada según 014) | — | `../sm-e` | `carril-e` | 026 y 027 cerradas e integradas (027-C15 D) |
| I | 012 (con el WIP de la rama `wip-012-gate`) | 007, 011 | `../sm-i` | `carril-i` | cerrada e integrada |
| K | 029 (C01, C05–C08); 004-C16 (check-env solo exige los roles con fichero de prompt) | — | `../sm-k` | `carril-k` | cerrada e integrada |
| W | workspace de producto: 010-I8, 011-I12–I14 (solo `backend/harness_workspace/`) | — | `../sm-w` | `carril-w` | cerrada e integrada |
| P | presentación (solo `presentacion/`) | — | `../sm-p` | `carril-p` | cerrado: el deck y su PDF los rellena el usuario con los datos de la tanda D |
| R | 013 C20–C23 (presentación impresa), 023 mínima, 026 C15 | — | `../sm-r` | `carril-r` | cerrado e integrado (2026-09-25) |
| F | 018 C18–C23 (linters en el bucle) → 019 (edición manual, backend). Toca `pipeline/` (producción, cambios), `api/` (rutas de edición), `store/` si 019 lo pide | 012, 014, 018 | `../sm-f` | `carril-f` | en curso |
| N | 023 completa → 024 → 025 (API real de 008/011; ruta de progreso `/novelas/:novelId/progreso`, de entrevista `/novelas/:novelId/entrevista`) | 022, 008, 011 | `../sm-n` | `carril-n` | en curso |
| G | 028 (edición manual, frontend, con la API simulada según 019; tras guardar, a `/novelas/:novelId/progreso`) | 026 | `../sm-g` | `carril-g` | en curso |
| M | 015 (servidor MCP) → 030 (report metrics, desde el patch archivado) | 013, 014 | `../sm-m` | `carril-m` | en curso |
| Q | 017 (revisión visual en el gate). Toca `pipeline/gate/`, `composition.py` (la etapa 3), un módulo propio del revisor | 012, 013 | `../sm-q` | `carril-q` | en curso |
| C | 029 sin recortes: seguir la entrevista guardada, `change` por la CLI (C02–C04, C09–C14, I1–I3). Toca solo los comandos `interview` y `change` de `cli.py` y sus pruebas | 008, 014 | `../sm-c` | `carril-c` | en curso |
| I | invariantes T recortadas de 010 (I1, I2), 011 (I1, I5, I7, I9–I11) y 014 (I9, I12): pruebas; código solo si una invariante no se cumple | 010, 011, 014 | `../sm-i2` | `carril-i2` | en curso |
| Z | errores de la tanda D: `nombres-exactos` marca «Cómo» como variante de «Cobo»; `runs.reason_detail` repite el comentario del juez; 020-C18 (desde `carril-u`) | 012, 020 | `../sm-z` | `carril-z` | en curso |

Los carriles B, C, F, G, H y J de la primera tanda están cerrados y sus ramas borradas; los nombres F y G se reusan en la segunda.

## Specs

| NNN | Spec | Lado | Carril | Depende de |
|---|---|---|---|---|
| 000 | scaffolding (herramientas, estructura, CI, marca del frontend, hooks de desarrollo) | transversal | 0 | — |
| 001 | base | backend | A | 000 |
| 002 | autenticacion | backend | A | 001 |
| 003 | puerto-de-agente | backend | B | 001 |
| 004 | observabilidad | backend | D | 001 |
| 005 | guardarrailes | backend | C | 001 *parcial*: lo puro no la necesita; el audit log sí |
| 006 | especificacion-tla | backend | D | 000 |
| 007 | validador-lean | backend | C | 009 *parcial*: solo el adaptador a SQLite |
| 008 | brief-y-entrevista | backend | B | 002, 003, 004, 005 |
| 009 | story-bible-y-versiones | backend | A | 001, 002 |
| 010 | planificacion | backend | G | 003, 004, 009 *parcial*: lo que no usa la 009 empieza antes |
| 011 | produccion-de-capitulos | backend | A | 002, 005, 006, 010 |
| 012 | gate-de-publicacion | backend | I | 007, 011 |
| 013 | lectura-y-pdf | backend | D | 009 *parcial*: el token de vista, el PDF y `pdf-enlaces` empiezan antes |
| 014 | cambios-del-lector | backend | A | 012 |
| 015 | servidor-mcp | backend | A | 002, 008, 013, 014 |
| 016 | recuperacion-hibrida | backend | H | 009 *parcial*: lo que no usa la 009 empieza antes |
| 017 | revision-visual | backend | B | 012, 013 |
| 018 | linters-de-prosa | backend | F | 011 *parcial*: los linters puros no la necesitan; el punto de ejecución en el bucle (C18–C23) sí |
| 019 | edicion-manual | backend | C | 012, 018 |
| 020 | evals | backend | D | 012 |
| 021 | auditoria-de-seguridad | backend | A | 002, 015 |
| 022 | acceso (registro, inicio de sesión, rutas protegidas, marca común) | frontend | E | 000, 002 |
| 023 | mis-novelas (lista con estado y versión vigente, crear novela, prohibidas de nivel usuario) | frontend | E | 022, 005, 008 |
| 024 | entrevista (chat, panel del brief, textos libres, hechos por aceptar, prohibidas de novela, confirmación) | frontend | E | 023, 008 |
| 025 | progreso (sondeo de la ejecución, reanudar, informe) | frontend | E | 024, 011 |
| 026 | lectura (portada y dedicatoria, índice, capítulos cambiados, ficha con enlaces, versiones, PDF) | frontend | E | 022, 013 |
| 027 | cambio-del-lector (seleccionar, pedir, propuesta y afectados, confirmar, ver la versión nueva) | frontend | E | 026, 014 |
| 028 | edicion-manual (editor con lint en vivo, guardar, versión nueva) | frontend | E | 026, 025, 018, 019 |
| 029 | cli (`interview` sobre 008 y `change` sobre 014, con confirmación) | backend | A | 008, 011, 014 |
| 030 | report-metrics (`report metrics`: agregados de SQLite a `docs/metrics.md`) | backend | J | 001, 004 |
| 031 | arranque (montaje único de `serve`, `example` y `evals run`: API completa, worker, prompts, incrustaciones) | backend | X (C05: Y) | 002, 008, 011, 012, 013, 016 |

## 000 — scaffolding

- [x] Spec `specs/000-scaffolding.md` approved — auditor 2026-09-24: ronda 2; 20 casos (12 T, 8 D) y 11 invariantes trazados contra arch §14.8, §15.1–§15.9, §18, verif §2–§4.10, §5, §6, §9 y backend/frontend AGENTS; los 2 huecos de la ronda 1 (1 contradicción, 1 deriva) cerrados; gap cero
- [x] Plan below approved — auditor 2026-09-24: ronda 1; 23 pasos, uno por caso (20) y por invariante T (I3, I4, I5), con los nombres de la spec, en orden de construcción; cierre con el formato de AGENTS.md; gap cero

### Steps
- [x] 000-C01 · Git ignora lo generado y los secretos, y versiona lo que se entrega
- [x] 000-C02 · Git guarda los ficheros de texto con LF y no convierte los binarios
- [x] 000-C03 · El backend se instala desde su lock y su verificación pasa sin credenciales
- [x] 000-C04 · Cada dependencia del stack del backend se importa en el entorno instalado
- [x] 000-C05 · El paquete tiene un subpaquete por módulo y `domain` no importa el resto
- [x] 000-C06 · El frontend se instala desde su lock y su verificación pasa
- [x] 000-C07 · La SPA muestra la cabecera de marca en la ruta raíz
- [x] 000-C08 · El tema define la marca y el logotipo es el de `images/`
- [x] 000-I3 · Fuera de la definición de tokens, ningún fichero de `frontend/src/` contiene un color hexadecimal ni declara una familia tipográfica
- [x] 000-C09 · `guard-secretos` decide por la forma del texto nuevo
- [x] 000-C10 · `guard-plan` bloquea pruebas y código sin plan aprobado con pasos pendientes
- [x] 000-I5 · Los hooks deciden igual con el directorio actual en un subdirectorio
- [x] 000-C11 · Los ajustes del proyecto registran los hooks y las denegaciones
- [x] 000-C12 · El espejo de memoria está completo y saneado
- [x] 000-I4 · Ningún fichero versionado contiene una cadena con forma de clave
- [x] 000-C13 · Cada herramienta falla ante su defecto sembrado
- [x] 000-C14 · Un clon limpio funciona en el portátil
- [x] 000-C20 · TLC arranca en el portátil sobre Temurin portable
- [x] 000-C15 · Claude Code conecta los servidores de `.mcp.json` (D; 2026-09-25, `verification.md` §9.2; el caso sin `LANGFUSE_MCP_AUTH` no se probó)
- [x] 000-C16 · Playwright MCP inspecciona la SPA en Edge: marca, mismo origen y proxy de `/api` (D; 2026-09-25, `verification.md` §9.3)
- [ ] 000-C17 · En una sesión real, los hooks y los permisos actúan (D, al final)
- [x] 000-C18 · La primera CI de `V2` sale en verde, con Lean y TLC — CI de 1f4eacd verde: backend, frontend, formal (Lean y TLC), seguridad
- [ ] 000-C19 · La CI se pone en rojo ante defectos sembrados (D, al final)

### Closing
- [x] Full suite green, type checks clean
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

— verificador 2026-09-24: backend (uv sync, pytest 112 passed, ruff check, ruff format --check, mypy src) verdes; frontend (pnpm lint, typecheck, build, test 5 passed en 2 ficheros) verdes; hooks (node --test .claude/hooks/*.test.mjs) 118 passed. C01–C14 y C20 trazados a pruebas; C15–C19 (D, al final) quedan sin marcar por regla del usuario y no bloquean el cierre.

## 001 — base

- [x] Spec `specs/backend/001-base.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; C6 corregido: uso y coste de `role_sessions` vacíos sin resultado final (§18, hallazgo de 003)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado 2026-09-25 (integrador: sin revisión, decisión del usuario), sin pasos nuevos

### Steps
- [x] 001-C03 · Ajustes: valores por defecto, rutas desde la raíz y precedencia del entorno
- [x] 001-C04 · Ajustes obligatorios y condicionales
- [x] 001-C01 · El `config.json` del repositorio es válido y lleva los valores de §15.4
- [x] 001-C02 · La config se valida entera y nombra cada clave que falta, sobra o no vale
- [x] 001-C05 · `.env.example` lista los ajustes sin valores
- [x] 001-C06 · `init-db` crea la base con el esquema completo
- [x] 001-C07 · `init-db` no pisa una base existente sin `--reset`
- [x] 001-C08 · Toda conexión abre la base igual
- [x] 001-C09 · Ámbito y referencias obligatorias
- [x] 001-C10 · Enumerados, rangos, unicidades y coherencia
- [x] 001-C11 · Solo inserción y CanonCards inmutables
- [x] 001-C12 · El índice FTS5 sigue a las CanonCards, sin acentos
- [x] 001-C13 · Una unidad de trabajo es todo o nada
- [x] 001-C14 · `check-env` informa de cada comprobación
- [x] 001-I1 · Ninguna salida reproduce el valor de un ajuste secreto
- [x] 001-C15 · `serve` no arranca con config, ajustes o base inválidos
- [x] 001-C16 · `serve` escucha en `STORY_MAKER_BASE_URL`, en un solo proceso
- [x] 001-I2 · `init-db`, `check-env` y `serve` solo crean o cambian ficheros dentro del directorio de datos
- [x] 001-C17 · Salud, esquema OpenAPI y errores de la API
- [x] 001-C18 · La SPA compilada se sirve en el mismo origen sin tapar la API
- [x] 001-C19 · El doble nulo captura lo emitido, sin red
- [x] 001-C20 · Niveles y excepciones de los spans
- [x] 001-C21 · Prompts, comprobación y vaciado con el doble nulo
- [x] 001-I3 · Ni el doble nulo ni las órdenes de esta spec abren una conexión fuera de la máquina
- [ ] 001-C22 · Primera generación de los tipos del frontend (D, al final)
- [ ] 001-C23 · Un clon limpio arranca siguiendo el README (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 278 passed; `uv run ruff check .` All checks passed; `uv run ruff format --check .` 38 files already formatted; `uv run mypy src` Success, no issues found in 23 source files
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 002 — autenticacion

- [x] Spec `specs/backend/002-autenticacion.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 002-C01 · Registro válido
- [x] 002-C02 · El email se guarda normalizado
- [x] 002-C03 · Un email ya registrado no crea otra cuenta
- [x] 002-C04 · Email sin forma de email
- [x] 002-C05 · Contraseña en sus límites
- [x] 002-C06 · Registro con cuerpo incompleto
- [x] 002-C07 · Acceso válido
- [x] 002-C08 · Al entrar, el email no distingue mayúsculas
- [x] 002-C09 · Credenciales incorrectas
- [x] 002-C10 · Acceso con cuerpo incompleto
- [x] 002-C11 · Un token válido identifica al cliente
- [x] 002-C12 · Sin token, o con el token mal presentado, responde 401
- [x] 002-C13 · Un token manipulado o de otro uso responde 401
- [x] 002-C14 · La caducidad en su límite
- [x] 002-C15 · El token se comprueba antes que la propiedad
- [x] 002-C16 · Lo ajeno responde como inexistente
- [x] 002-C17 · Un recurso anidado solo existe dentro de su padre
- [x] 002-C18 · Una entrada global no es de ningún cliente
- [x] 002-C19 · Un listado solo contiene lo del cliente
- [x] 002-C20 · Lo ajeno no cambia nada
- [x] 002-C21 · El propietario de lo creado es el cliente del token
- [x] 002-I1 · La contraseña nunca queda en claro
- [x] 002-I2 · Toda ruta de `/api` salvo el registro y el acceso exige un `TokenDeAcceso` válido
- [x] 002-I3 · Para B, un recurso de A es indistinguible de uno inexistente y no cambia nada
- [x] 002-I4 · El cliente de una petición sale solo del token

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 338 passed; `uv run ruff check .` all checks passed; `uv run ruff format --check .` 47 files already formatted; `uv run mypy src` no issues in 28 source files
- [x] Spec updated, or confirmed still true — verificador 2026-09-24: confirmada sin cambios
- [x] Docs updated, or confirmed still true — verificador 2026-09-24: confirmada sin cambios (la forma única del 422 ya está en `architecture.md` §18, commit 1bbb4a4 en V2)

## 003 — puerto-de-agente

- [x] Spec `specs/backend/003-puerto-de-agente.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; C13 corregido: desenlace `infrastructure_failure` (§18)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 003-C28 · El doble recorre el camino del SDK y es determinista
- [x] 003-I9 · El doble falso es determinista
- [x] 003-C29 · Una sesión sin guion hace fallar la prueba
- [x] 003-I6 · Ninguna prueba T llega a un modelo
- [x] 003-I7 · Solo el puerto de agente usa el Agent SDK
- [x] 003-C01 · Cada rol abre con su lista blanca y nada más
- [x] 003-C02 · Unas tools que no cuadran con la lista blanca impiden abrir
- [x] 003-C03 · La sesión corre aislada en el workspace
- [x] 003-C04 · Solo el revisor visual declara el browser MCP
- [x] 003-C05 · Con `claude_login`, la sesión usa el login de la máquina y ninguna clave
- [x] 003-C06 · Con `anthropic_compatible`, la sesión lleva solo las variables de su endpoint
- [x] 003-C07 · El schema que recibe la sesión es el derivado del modelo de la tool
- [x] 003-C08 · Una entrada inválida vuelve al modelo como error y se corrige en la misma sesión
- [x] 003-C09 · Las entregas quedan en memoria, en orden, y nada se persiste
- [x] 003-C10 · Una sesión que termina sin entregar no es un error del puerto
- [x] 003-C11 · Toda llamada a tool pasa antes por la política, y su decisión se aplica
- [x] 003-C12 · La política recibe como narrativos solo los campos que la tool marca
- [x] 003-C13 · Si la política falla, la tool no corre
- [x] 003-I3 · Ninguna tool corre sin una decisión `allow` o `flag` de la política
- [x] 003-I4 · Las tools entregan, no persisten
- [x] 003-C14 · Con defectos bloqueantes, el modelo lee los defectos en lugar del acuse
- [x] 003-C15 · Las comprobaciones corren solo sobre entregas permitidas y válidas, y lo no bloqueante no bloquea
- [x] 003-C16 · La reserva es la entrada estimada más el crecimiento de los turnos
- [x] 003-C17 · Se abre hasta llenar el techo exacto; si no cabe, se espera en orden de llegada
- [x] 003-C18 · La API espera como mucho `api_wait_seconds`; la ejecución, sin límite propio
- [x] 003-C19 · Una reserva mayor que el techo no espera
- [x] 003-C20 · La reserva se libera siempre al cerrar
- [x] 003-I1 · La suma de las reservas abiertas nunca supera `token_ceiling`
- [x] 003-I2 · Toda reserva se libera exactamente una vez
- [x] 003-C21 · Agotar los turnos conserva el uso
- [x] 003-C22 · Pasar de `session_timeout_seconds` interrumpe y desconecta
- [x] 003-C23 · Un fallo del proveedor es `infrastructure_failure`, no `completed`
- [x] 003-C24 · Quien abre la sesión puede cortarla
- [x] 003-C25 · El coste es el uso real por el precio de lista del modelo
- [x] 003-I5 · El coste de una `SesionDeRol` es su uso × `operation.pricing`, nunca el que declara el SDK
- [x] 003-C26 · Toda sesión abierta deja su `SesionDeRol`, y solo ellas
- [x] 003-C27 · Cada sesión y cada llamada a tool dejan su span
- [x] 003-I8 · Sesiones concurrentes no comparten estado
- [ ] 003-C30 · El login funciona con tools en proceso, hooks y skill (D, al final)
- [ ] 003-C31 · La sesión real no hereda nada del entorno de desarrollo (D, al final)
- [ ] 003-C32 · Los límites reales terminan la sesión sin dejar subprocesos (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: uv sync; uv run pytest (520 passed); uv run ruff check . (All checks passed!); uv run ruff format --check . (97 files already formatted); uv run mypy src (no issues found in 52 source files)
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 004 — observabilidad

- [x] Spec `specs/backend/004-observabilidad.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 004-C01 · Con las cuatro variables de Langfuse, se usa el adaptador real
- [x] 004-C02 · Sin alguna variable de Langfuse, se usa el doble nulo
- [x] 004-I2 · Con alguna variable ausente, el puerto usa siempre el doble nulo
- [x] 004-C03 · `check-env` informa «ok» con credenciales válidas y prompts vigentes
- [x] 004-C04 · `check-env` falla si las credenciales de Langfuse no son válidas
- [x] 004-C05 · `check-env` falla si a un rol le falta el prompt con la etiqueta vigente
- [x] 004-I3 · `auth_check()` nunca falla en silencio
- [x] 004-C06 · `serve` no arranca en las mismas situaciones que `check-env`
- [x] 004-C07 · `prompts push` sube una versión nueva si cambia la huella del fichero
- [x] 004-C08 · `prompts push` no sube si la huella no cambió
- [x] 004-I4 · Sube si y solo si cambia la huella
- [x] 004-C09 · Al arrancar, cada `LlamadaDeModelo` enlaza la versión de prompt leída por la etiqueta
- [x] 004-C10 · La máscara sustituye nombres y fechas sin tocar tokens, coste, latencia ni scores
- [x] 004-I1 · Todo texto exportado pasa antes por la máscara
- [x] 004-C11 · La máscara de una llamada MCP con varias novelas es la unión de sus máscaras
- [x] 004-C12 · Cada resultado de validador se exporta como Score con su nombre canónico
- [x] 004-C13 · TLC no envía score
- [x] 004-I7 · Ninguna llamada real a modelo o Langfuse en una prueba T
- [ ] 004-C14 · Una ejecución real vista en Langfuse (D, al final)
- [ ] 004-C15 · Iteración de tuning con antes y después de un prompt cambiado (D, al final)
- [x] 004-C16 · check-env no exige prompt a un rol sin fichero en el workspace

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: `uv run pytest` 1528 passed; `uv run ruff check .` all checks passed; `uv run ruff format --check .` 352 files already formatted; `uv run mypy src` no issues found in 145 source files
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 005 — guardarrailes

- [x] Spec `specs/backend/005-guardarrailes.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 005-C09 · Sin coincidencia, permite
- [x] 005-C01 · Una entrada de nivel global deniega
- [x] 005-C02 · Una entrada de nivel user deniega solo para su cliente
- [x] 005-C03 · Una entrada de nivel novel deniega solo para su novela
- [x] 005-C04 · Una variante de acento coincide
- [x] 005-C05 · Una variante de plural coincide
- [x] 005-C06 · Letras repetidas y leetspeak simple coinciden
- [x] 005-C07 · La coincidencia va por tokens, no por subcadena
- [x] 005-C08 · Un tema coincide por cualquiera de sus palabras clave
- [x] 005-C10 · La política nunca escanea un campo no marcado como narrativo (cubre 005-I4)
- [x] 005-I3 · Normalización idempotente y coincidencia por tokens (propiedad hypothesis)
- [x] 005-C11 · Una tool fuera de la lista blanca del rol deniega
- [x] 005-C12 · Una tool de la lista blanca del rol, sin más causa, permite
- [x] 005-C13 · Solo personalizacion-natural se admite como skill
- [x] 005-C14 · El revisor visual solo navega el origen de la vista
- [x] 005-C15 · Una frase dirigida al sistema en español se marca, no deniega
- [x] 005-C16 · Una frase dirigida al sistema en inglés se marca
- [x] 005-C17 · Un texto sin patrón de inyección no se marca
- [x] 005-I1 · policy/ no importa agents/
- [x] 005-I5 · El detector de inyección nunca deniega por sí solo
- [x] 005-I6 · Cada coincidencia lleva término, nivel y variante en su detalle
- [x] 005-C18 · Sembrar la lista global no duplica entradas
- [x] 005-C19 · Toda decisión deja una fila en el audit log
- [x] 005-C20 · El origen de cada decisión es uno de los seis declarados
- [x] 005-I2 · Toda petición decidida deja exactamente una fila en audit_log

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: uv run pytest 310 passed · ruff check All checks passed · ruff format --check 54 files already formatted · mypy src Success, no issues in 33 files
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 006 — especificacion-tla

- [x] Spec `specs/backend/006-especificacion-tla.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; C4 (fila `Validar`) corregido tras el contraejemplo de TLC de C10
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado con el cambio de C4

### Steps
- [x] C4 — Las transiciones de `Harness.tla` son las de §9.1 — modelo con el cambio de C10 (en `gate`, solo el ciclo fallido cuenta un intento); fila `Validar` de C4 y §9.2/§9.4 por actualizar (integrador)
- [x] C1 — `Harness.tla` pasa en el modelo pequeño — TLC: sin error, 862.143 estados distintos, 193 s en el portátil (12 núcleos)
- [x] C5 — Las transiciones de `Regenerations.tla` son las de §10.2
- [x] C2 — `Regenerations.tla` pasa con dos cambios — TLC: sin error, 155 estados distintos, 1 s
- [x] C3 — Ninguna acción queda sin disparar — `tla/verificar.sh`: las 12 acciones de `Harness.tla` y las 6 de `Regenerations.tla`, disparadas; probado el rechazo (acción muerta → la nombra)
- [x] C6 — Cada config de control da el contraejemplo de su propiedad — TLC: los 6 controles dan el contraejemplo de su propiedad con la traza de la tabla; `TerminaSiempre` por ser la única propiedad temporal de su config (TLC 2.19 no la nombra); probado el rechazo (defecto desactivado → sin contraejemplo; sintaxis → otra causa)
- [x] C9 — El README dice qué transición implementa cada acción — README raíz (V2 6c09383): 12 filas, una por acción de `Harness.tla`, con transición de C4, quién la dispara y spec del código; `Regenerations.tla` remite a ellas y a §10.2; columna Código pendiente hasta cerrar cada spec
- [x] C10 — Un contraejemplo real queda registrado con su cambio — `verification.md` §8 fila 3 (TLC, ciclos del gate); primero `architecture.md` §9.2 y §18, después el modelo; tras el cambio `Harness.cfg` pasa (862.143 estados)
- [ ] C8 — En el portátil, el mismo veredicto (D, al final)
- [ ] C7 — La CI decide con las configs de la 006 (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `bash tla/verificar.sh` (Temurin portable, tla2tools 1.7.4): 8/8 configs OK — Harness.cfg (862.143 estados, 285s) y sus 5 controles, cada uno con el contraejemplo nombrado; Regenerations.cfg (155 estados) y su control 6; `uv run pytest` backend: 278 passed
- [x] Spec updated, or confirmed still true — verificador 2026-09-24: sin cambios; C4/C5 contra `tla/Harness.tla` y `tla/Regenerations.tla` coinciden
- [x] Docs updated, or confirmed still true — verificador 2026-09-24: `architecture.md` §9.2/§9.4/§18 y `verification.md` §8 fila 3 ya reflejan el cambio de C10; README raíz con las 12 filas de C9

## 007 — validador-lean

- [x] Spec `specs/backend/007-validador-lean.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; C16 corregido (el límite exacto no existe con base64)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 007-C01 · El fichero lleva la cronología registrada de la versión y nada más
- [x] 007-C02 · Los ids son los de las filas y las fechas se desplazan 400·k años
- [x] 007-C03 · k se elige al azar en cada fichero, entre 1 y 10
- [x] 007-C04 · La misma cronología y el mismo k dan el mismo fichero
- [x] 007-C05 · El 29 de febrero y las edades se conservan al desplazar
- [x] 007-C06 · Solo entra la versión que se verifica
- [x] 007-C07 · Un testigo con eventos narrados da un defecto por capítulo
- [x] 007-C08 · Un testigo solo con eventos del brief da un defecto sin capítulo
- [x] 007-C09 · Una verificación que pasa deja su fichero y su fila
- [x] 007-C10 · Un invariante violado deja la fila `failed` y devuelve los defectos
- [x] 007-C11 · Un fichero que no compila por otra causa es `error` y nunca `passed`
- [x] 007-C12 · Sin veredicto no hay fila
- [x] 007-C13 · El modo local compila en el directorio de datos e interpreta la salida
- [x] 007-C14 · El modo github envía el fichero comprimido por `workflow_dispatch`
- [x] 007-C15 · El modo github sondea la ejecución y lee el resultado del artefacto
- [x] 007-C16 · El input cabe en el límite de 65.535 caracteres o no se envía
- [x] 007-C17 · Un GitHub inalcanzable o lento interrumpe sin reintentar
- [x] 007-C18 · El modo github sin sus ajustes no se construye
- [x] 007-C19 · El doble del `VerificadorFormal` devuelve lo programado sin red ni Lean
- [x] 007-C20 · El fichero dorado compila y cumple T1–T5
- [x] 007-C21 · Un fichero negativo por invariante falla con ese invariante y su primer testigo
- [x] 007-C22 · Los límites de cada invariante
- [x] 007-C23 · Cada comprobador decide su invariante para cualquier cronología
- [x] 007-C24 · La auditoría de axiomas no pasa en vacío
- [x] 007-I2 · Solo es `passed` lo que compila, pasa la auditoría y cumple los cinco invariantes
- [x] 007-I3 · El `FicheroDeCronologia` no lleva datos personales
- [x] 007-I4 · La seudonimización no cambia el resultado de ningún comprobador
- [x] 007-I6 · El fichero solo contiene filas de la versión que se verifica
- [x] 007-I7 · El verificador solo escribe en `STORY_MAKER_DATA_DIR`
- [x] 007-I8 · `GITHUB_TOKEN` nunca aparece en el fichero, el input, el resultado, la fila, un mensaje de error ni un registro
- [x] 007-I12 · La fila de `chronology_files` solo existe con un resultado (`passed`, `failed` o `error`), y su huella es la del fichero guardado
- [ ] 007-C25 · Una verificación real por GitHub Actions responde a tiempo (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 793 passed; `uv run ruff check .` sin avisos; `uv run ruff format --check .` 140 ficheros formateados; `uv run mypy src` sin problemas en 71 ficheros; C20–C24 (Lean) verdes en la CI (ejecución 36003381493)
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 008 — brief-y-entrevista

- [x] Spec `specs/backend/008-brief-y-entrevista.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (C02: id de la ejecución más reciente)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (C02: id de la ejecución más reciente)

### Steps
- [x] 008-C02b · La novela lleva el id de su ejecución más reciente, vacío sin ninguna (carril Z; lo usa 025-C00)
- [x] 008-C01 · Crear una novela para entrevistarla
- [x] 008-C02 · Lista y detalle de las novelas con su estado derivado
- [x] 008-C03 · Un turno aplica lo que entrega el entrevistador
- [x] 008-C04 · `update_brief` actúa como parche del borrador
- [x] 008-C05 · `update_brief` no alcanza lo que decide el cliente
- [x] 008-C06 · Una dedicatoria con una prohibida no entra por `update_brief`
- [x] 008-C07 · Un turno fallido no se guarda
- [x] 008-C08 · Mensaje rechazado antes de abrir la sesión
- [x] 008-C09 · Datos faltantes, uno por campo
- [x] 008-C10 · Contradicciones C1–C5, por tabla
- [x] 008-C11 · Contradicción C6, por nivel, lugar y variante
- [x] 008-C12 · Cota de elementos obligatorios
- [x] 008-C13 · Comprobación de schema: forma y referencias internas
- [x] 008-C14 · Las comprobaciones se recalculan en cada lectura
- [x] 008-C15 · Confirmar un brief válido
- [x] 008-C16 · Confirmación rechazada
- [x] 008-C17 · Un brief confirmado es inmutable
- [x] 008-C18 · Extraer hechos de un texto libre
- [x] 008-C19 · `citas-verificadas`, regla por regla
- [x] 008-C20 · Inyección en el texto libre (RT1)
- [x] 008-C21 · Hecho inventado o exfiltrado por el extractor (RT2)
- [x] 008-C22 · El texto libre solo llega al extractor
- [x] 008-C23 · Texto libre rechazado o con la sesión fallida
- [x] 008-C24 · Aceptar, rechazar y marcar obligatorio un hecho extraído
- [x] 008-C25 · Lista prohibida de nivel `novel`
- [x] 008-C26 · Lista prohibida de nivel `user`
- [x] 008-C27 · Audit log de la novela
- [x] 008-C28 · Importar un brief válido
- [x] 008-C29 · Importación rechazada antes de extraer
- [x] 008-C30 · Importación con una extracción fallida
- [x] 008-C31 · Trazas y scores de la entrevista y de la importación
- [x] 008-I1 · Importar y confirmar deciden igual
- [x] 008-I2 · Las comprobaciones son deterministas y solo dependen del brief, de las tres listas, de la fecha de creación de la novela y de `max_mandat…
- [x] 008-I3 · Un hecho sin verificar no sale nunca
- [ ] 008-I4 · Toda ruta de esta spec exige `TokenDeAcceso` (401) y trata como inexistente (404) la novela, el hecho o la entrada prohibida de otro cliente (recortado)
- [x] 008-I5 · Un turno, una extracción, una confirmación y una importación se guardan enteros o no se guardan
- [ ] 008-C32 · Entrevista real con el login de Claude Code (D, al final)
- [ ] 008-C33 · Extracción real de una carta con inyección (D, al final)

### Closing
- [x] Full suite green, type checks clean; re-verificado 2026-09-25 (carril Z): `uv run pytest` 1680 passed, `ruff check .` y `ruff format --check .` limpios (399 ficheros), `mypy src` sin incidencias en 158 ficheros
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

— verificador 2026-09-24: backend (uv run pytest 1190 passed, ruff check clean, ruff format --check clean, mypy src clean) verdes.

## 009 — story-bible-y-versiones

- [x] Spec `specs/backend/009-story-bible-y-versiones.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 009-C01 · La candidata de generación nace con el canon del brief
- [x] 009-C02 · El destinatario y los allegados pasan a personajes con su hecho de nombre
- [x] 009-C03 · La fecha de nacimiento es la declarada, la derivada de la edad o ninguna
- [x] 009-C04 · Los rasgos, las relaciones y los hechos extraídos aceptados pasan a hechos
- [x] 009-C05 · Cada recuerdo da su hecho, su evento fechado y su lugar
- [x] 009-C06 · Un recuerdo excluyente nombra a su excluido
- [x] 009-C07 · Hay un lugar del brief por cada nombre de lugar exacto
- [x] 009-C08 · El fechado respeta los límites del calendario
- [x] 009-C09 · Cada elemento personal queda representado y los obligatorios, marcados
- [x] 009-I7 · Todo ElementoPersonal del brief tiene al menos un hecho que lo representa, y el de uno obligatorio es obligatorio
- [x] 009-C10 · Crear la candidata de generación es todo o nada
- [x] 009-C11 · La copia reproduce la base entera con identificadores nuevos
- [x] 009-C12 · La copia no vuelve a incrustar: comparte los vectores
- [x] 009-C13 · La base no cambia al copiarla ni al trabajar la candidata
- [x] 009-C14 · Copiar es todo o nada
- [x] 009-I4 · Crear una candidata, de generación o por copia, es todo o nada
- [x] 009-I2 · Cada versión es autocontenida
- [x] 009-C15 · Cambiar el valor de un hecho de la candidata
- [x] 009-C16 · Cambiar un hecho de nombre cambia a la vez el nombre canónico
- [x] 009-I6 · El nombre canónico de cada personaje es el valor de su hecho de nombre
- [x] 009-C17 · Publicar la primera versión
- [x] 009-C18 · Publicar una copia: número siguiente y capítulos cambiados por huella
- [x] 009-C19 · Descartar una candidata
- [x] 009-C20 · Las transiciones que no salen de una candidata válida se rechazan
- [x] 009-C21 · Solo una candidata admite escrituras
- [x] 009-I1 · Solo una candidata admite escrituras; una publicada o descartada no cambia nunca
- [x] 009-C22 · La versión vigente es la publicada de número más alto
- [x] 009-I5 · La historia de versiones es lineal
- [x] 009-C23 · La cronología registrada de una versión
- [x] 009-C24 · La story bible de una versión, por su identificador
- [x] 009-I3 · Una lectura de una versión nunca devuelve filas de otra versión ni de otra novela
- [x] 009-C25 · La API devuelve la story bible de la versión vigente
- [x] 009-C26 · La API devuelve la story bible de una versión anterior
- [x] 009-C27 · La API rechaza lo que no existe, lo mal formado, lo anónimo y lo ajeno
- [x] 009 · Escritura de la fila de `chronology_files` para la 007 (alcance de la spec; paso añadido por el integrador, prueba en tests/store/story_bible/test_chronology_files.py)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: uv run pytest (464 passed), uv run ruff check . (all checks passed), uv run ruff format --check . (81 files formatted), uv run mypy src (no issues, 45 files)
- [x] Spec updated, or confirmed still true — verificador 2026-09-24: confirmada, sin cambios
- [x] Docs updated, or confirmed still true — verificador 2026-09-24: confirmados, sin cambios (architecture.md §18 ya trae las filas «spec 009»)

## 010 — planificacion

- [x] Spec `specs/backend/010-planificacion.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 010-C01 · La candidata nace con el canon del brief
- [x] 010-C02 · Fechas de nacimiento del canon
- [x] 010-C03 · Fechado de los recuerdos
- [x] 010-C04 · Eventos y lugares de los recuerdos
- [x] 010-C05 · Hechos extraídos en el canon
- [x] 010-C06 · Ventana del planner
- [x] 010-C07 · Catálogo de tropos curado
- [x] 010-C08 · Schema de `submit_plan`
- [x] 010-C09 · Policy sobre la entrega del plan
- [x] 010-C10 · Un plan válido pasa
- [x] 010-C11 · Capítulos y beats
- [x] 010-C12 · Elementos obligatorios asignados
- [x] 010-C13 · Momentos de los eventos y año presente
- [x] 010-C14 · Referencias y tipo de evento
- [x] 010-C15 · Fecha del novum
- [x] 010-C16 · `outline` no juzga la cronología
- [x] 010-C17 · Replanificación con los defectos
- [x] 010-C18 · Una sesión sin entrega cuenta como intento
- [x] 010-C19 · Intentos agotados
- [x] 010-C20 · El plan aceptado se aplica en una transacción
- [x] 010-C21 · StyleSheet
- [x] 010-C22 · CanonCards iniciales
- [x] 010-C23 · La transacción de aplicación falla
- [x] 010-C24 · Relanzar antes del punto de control 0
- [x] 010-C25 · Relanzar tras el punto de control 0
- [x] 010-C26 · Fallo del proveedor
- [x] 010-C27 · Reserva inviable en el techo
- [x] 010-C28 · Una generación nueva tras un fallo tiene su propia candidata
- [x] 010-C29 · Resultado y score de `outline`
- [ ] 010-I1 · Ninguna ventana del planner contiene el contenido de un `TextoLibre` ni la cita de un `HechoExtraido`
- [ ] 010-I2 · Planificar no modifica ni borra nada de origen brief o free_text
- [x] 010-I3 · Una entrega rechazada (schema, policy, `outline` o sin entrega) no deja nada en la candidata
- [x] 010-I4 · Los intentos del evaluable `plan` nunca superan 1 + `max_retries.plan`, contando los de antes de una reanudación; el cortado por una caíd…
- [x] 010-I5 · El punto de control 0 existe si y solo si el plan está aplicado, se escribe una sola vez, y relanzar con él nunca abre el planner
- [x] 010-I6 · `outline` es determinista y exhaustivo
- [x] 010-I8 · El prompt del planner en modo `plan` (entrega tardía, carril W; lo lee el `verificador`) — `backend/harness_workspace/prompts/planner.md`
- [ ] 010-C30 · Planificación con el modelo real (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 902 passed; `uv run ruff check .` OK; `uv run ruff format --check .` OK (185 files); `uv run mypy src` OK (91 files). 010-I1/I2 recortados; 010-C30 (D) queda al final.
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 011 — produccion-de-capitulos

- [x] Spec `specs/backend/011-produccion-de-capitulos.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; C33–C34 añadidos y movidos a 031-arranque; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (C12: palabra corriente en minúscula no es variante)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; C33–C34 movidos a 031; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (paso 011-C12b)

### Steps
- [x] 011-C01 · Lanzar la generación la encola
- [x] 011-C02 · Solo se lanza una generación desde una novela lista
- [x] 011-C03 · Una sola ejecución activa en una cola FIFO global
- [x] 011-C04 · El progreso se consulta por sondeo
- [x] 011-C05 · De la planificación a la escritura
- [x] 011-C06 · Fallar descarta la candidata y libera la cola
- [x] 011-C07 · Ventana del writer
- [x] 011-C08 · Ventana del editor
- [x] 011-C09 · Cada sesión reserva en el techo, y una que no cabe nunca hace fallar
- [x] 011-C10 · Una entrega que pasa los hooks llega al editor
- [x] 011-C11 · `longitud-capitulo` en sus límites
- [x] 011-C12 · `nombres-exactos` sobre el título y el texto
- [x] 011-C12b · Una palabra con mayúscula que el texto escribe también en minúscula no es variante (bug de la tanda D: «Como» por «Cobo»)
- [x] 011-C13 · Qué cuenta como intento en la sesión del writer
- [x] 011-C14 · Una sesión del writer que termina sin entrega válida es un intento fallido
- [x] 011-C15 · La revisión del editor tiene schema y solo cita lo que existe
- [x] 011-C16 · El veredicto lo decide el código
- [x] 011-C17 · Reescribir es una sesión nueva con los defectos
- [x] 011-C18 · Los intentos de un capítulo se agotan con motivo
- [x] 011-C19 · Aceptar un capítulo es una transacción
- [x] 011-C20 · Los usos son los declarados más la coincidencia literal de los hechos nominales
- [x] 011-C21 · Si la transacción de aceptación falla, no queda nada del capítulo
- [x] 011-C22 · Volver a aceptar un capítulo reemplaza lo que dejó su aceptación anterior
- [x] 011-C23 · Tras el décimo capítulo, el gate
- [x] 011-C24 · Un error del proveedor interrumpe y no cuenta como intento
- [x] 011-C25 · Al arrancar el servidor, lo que estaba en curso se interrumpe
- [x] 011-C26 · Reanudar vuelve a encolar la ejecución en su puesto
- [x] 011-C27 · Reanudar sigue tras el último punto de control
- [x] 011-C28 · Caer con las reanudaciones agotadas es fallar
- [x] 011-C29 · Un error imprevisto del worker falla con `internal_error`
- [x] 011-C30 · El informe de la ejecución se calcula al pedirlo
- [x] 011-C31 · Trazas, spans y scores de la producción
- [ ] 011-I1 · Hay como mucho una ejecución `running` en el servidor, y las `queued` salen en orden de fecha de creación
- [x] 011-I2 · `ReanudacionSinDuplicarNiPerder`
- [x] 011-I3 · `ReintentosAcotados`
- [x] 011-I4 · La aceptación es atómica
- [ ] 011-I5 · Ningún rol escribe canon
- [x] 011-I6 · Ningún capítulo aceptado tiene un defecto bloqueante
- [ ] 011-I7 · El writer nunca recibe prosa recuperada
- [x] 011-I8 · Writer y editor son sesiones distintas
- [ ] 011-I9 · Las ventanas solo llevan datos de la candidata de su novela, nunca de otra novela del mismo cliente ni de otro cliente
- [ ] 011-I10 · El tamaño estimado de la ventana entra en la reserva de su sesión
- [ ] 011-I11 · Los usos y los eventos registrados solo citan hechos y entidades de la candidata
- [x] 011-I12 · El `CLAUDE.md` de producto (entrega tardía, carril W; lo lee el `verificador`) — `backend/harness_workspace/CLAUDE.md`
- [x] 011-I13 · La skill `personalizacion-natural` (entrega tardía, carril W) — `backend/harness_workspace/.claude/skills/personalizacion-natural/SKILL.md`
- [x] 011-I14 · Los prompts del writer (`write`, `rewrite`) y del editor (entrega tardía, carril W) — `backend/harness_workspace/prompts/writer.md`, `editor.md`
- [ ] 011-C32 · Una producción real con el login de Claude Code llega al gate y se reanuda (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: pytest 1342 passed, ruff check clean, ruff format clean, mypy 128 files clean
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 012 — gate-de-publicacion

- [x] Spec `specs/backend/012-gate-de-publicacion.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada tras el recorte de casos C (usuario, 2026-09-24)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada tras el recorte de casos C (usuario, 2026-09-24)

### Steps
- [x] 012-C1 · La candidata entra al gate con sus 10 capítulos aceptados
- [x] 012-C2 · Una pasada limpia recorre las cuatro etapas en orden y publica
- [x] 012-C3 · Un elemento obligatorio sin uso se atribuye a los capítulos que el outline le asignó
- [x] 012-C4 · Un nombre no canónico en un capítulo se atribuye a ese capítulo — necesita la regla de variantes de 011 (fuera de alcance de la spec 012, no en V2 todavía)
- [x] 012-C5 · Una prohibida en un capítulo se atribuye a ese capítulo
- [ ] 012-C6 · Una prohibida en la portada o en la ficha hace fallar la ejecución (recortado)
- [x] 012-C7 · Una etapa que falla corta la pasada
- [ ] 012-C8 · Lean y el juez corren a la vez (recortado)
- [x] 012-C9 · Un invariante Lean violado se atribuye a los capítulos de los eventos del testigo
- [x] 012-C10 · Un testigo Lean sin capítulo hace fallar la ejecución
- [x] 012-C11 · Un `FicheroDeCronologia` que no compila hace fallar la ejecución
- [ ] 012-C12 · Una interrupción en la etapa 2 no gasta la pasada (recortado)
- [x] 012-C13 · Un criterio bloqueante del juez bajo su umbral se atribuye a los capítulos que cita
- [x] 012-C14 · Ningún criterio compensa a otro
- [x] 012-C15 · Una entrega inválida del juez se corrige en su sesión, y sin entrega válida la pasada falla
- [x] 012-C16 · El juez recibe la novela entera y solo lo que necesita
- [x] 012-C17 · Dentro de una pasada, lo no atribuible manda sobre la interrupción, y esta sobre lo atribuible
- [x] 012-C18 · El PDF de la candidata es la última etapa
- [x] 012-C19 · La reescritura dirigida rehace solo los capítulos atribuidos y repite el gate
- [x] 012-C20 · Cada capítulo reescrito tiene sus intentos en cada ciclo
- [x] 012-C21 · Agotados los ciclos del gate, la ejecución falla
- [x] 012-C22 · Reanudar en `gate` o en `rewriting` repasa el gate sobre la candidata tal como quedó
- [x] 012-C23 · La publicación es una transacción
- [x] 012-C24 · Cada validador del gate deja su resultado y su score
- [x] 012-C25 · La rúbrica de novela es una constante del dominio
- [x] 012-C26 · El `CatalogoDeTropos` trae los tropos curados del género
- [x] 012-I1 · Ninguna versión se publica sin que la última pasada sobre esa candidata haya superado las cuatro etapas, y la candidata no cambia entre e…
- [x] 012-I2 · Las pasadas contadas de una ejecución nunca superan 1 + `max_retries.gate_cycles`, ni los intentos de un capítulo en un ciclo, 1 + `max_r…
- [x] 012-I3 · La publicación es atómica
- [x] 012-I4 · Publicar no modifica ninguna otra versión (`VersionAnteriorConservada`)
- [x] 012-I5 · El veredicto y la atribución los calcula el código solo con campos estructurados
- [ ] 012-C27 · Una sesión real del juez entrega una evaluación válida (D, al final)

- [x] 012-bug-D1 · Una ejecución que falla por el gate guarda en su motivo el comentario de cada validador una sola vez (tanda D: la 16 repetía seis veces el del juez)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 1523 passed; `uv run ruff check .` all checks passed; `uv run ruff format --check .` 345 files already formatted; `uv run mypy src` no issues in 144 source files; re-verificado 2026-09-25 (carril Z): `uv run pytest` 1680 passed, `ruff check .` y `ruff format --check .` limpios (399 ficheros), `mypy src` sin incidencias en 158 ficheros
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 013 — lectura-y-pdf

- [x] Spec `specs/backend/013-lectura-y-pdf.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; `example` (C16, C19) movido a 020; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (carril R: presentación impresa, C20–C24)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (C20–C24)

### Steps
- [x] 013-C01 · Portada, índice y ficha de una versión sin capítulos cambiados
- [x] 013-C02 · Página de novedades y marca de cambio
- [x] 013-C03 · Una entidad sin capítulo aparece en la ficha sin enlaces
- [x] 013-C04 · La VistaDeVersion sirve también una candidata
- [x] 013-C05 · Dos versiones de la misma novela no se mezclan
- [x] 013-I3 · La VistaDeVersion y el detalle de la API de una versión no muestran nada de otra versión ni de otra novela
- [x] 013-C06 · El token de vista se emite firmado y con sus reclamaciones
- [x] 013-C07 · Un token de vista inválido responde 401
- [x] 013-I2 · El token de vista solo vale para la versión a la que se emitió, nunca como TokenDeAcceso, y caduca con operation.session_timeout_seconds
- [x] 013-C08 · El PDF se genera desde la VistaDeVersion con sus 10 capítulos
- [x] 013-C09 · pdf-enlaces valida los enlaces internos
- [x] 013-C10 · pdf-enlaces falla ante un enlace que no resuelve
- [x] 013-I1 · Todo enlace interno del PDF y de la VistaDeVersion resuelve a un ancla que existe en el mismo documento
- [x] 013-C11 · El PDF se guarda por versión y se sirve tal cual
- [x] 013-C12 · Sin PDF guardado, la ruta responde 404
- [x] 013-I4 · El backend solo escribe el PDF de una versión en STORY_MAKER_DATA_DIR, salvo example
- [x] 013-C13 · Listado de versiones publicadas
- [x] 013-C14 · Detalle de una versión publicada
- [x] 013-C15 · Lo que no existe, lo ajeno y lo mal formado
- [x] 013-C17 · export-pdf regenera el PDF de una versión publicada
- [x] 013-C18 · export-pdf sobre lo que no existe o no está publicado
- [x] 013-I5 · Con los mismos datos de versión, la VistaDeVersion y el PDF que produce son iguales
- [x] 013-C20 · La portada ocupa sola la primera página
- [x] 013-C21 · El índice muestra el número de cada capítulo una sola vez
- [x] 013-C22 · Novedades, índice, cada capítulo y la ficha empiezan en página nueva
- [x] 013-C23 · Números de página al pie, salvo en la portada
- [ ] 013-C24 · El aspecto del PDF es el de un libro (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: `uv run pytest` 1672 passed; `uv run ruff check .` all checks passed; `uv run ruff format --check .` 399 files already formatted; `uv run mypy src` no issues in 158 source files; frontend `pnpm.cmd lint`, `pnpm.cmd typecheck`, `pnpm.cmd build` limpios, `pnpm.cmd test` 62 passed
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 014 — cambios-del-lector

- [x] Spec `specs/backend/014-cambios-del-lector.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada 2026-09-25 (integrador: sin revisión, decisión del usuario): I18 e I19 con su fila de §6; C19 enlaza la propuesta por su traza
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 014-C01 · Una petición sobre un hecho devuelve la propuesta, los afectados y el código
- [x] 014-C02 · Los afectados son los usos, más el valor antiguo literal, más el capítulo del fragmento
- [x] 014-C03 · Lo que no admite una petición se rechaza antes de la policy
- [x] 014-C04 · Una prohibida en la petición la deniega sin abrir el planner
- [x] 014-C05 · Una inyección en la petición se marca y no deniega (RT3)
- [x] 014-C06 · El código valida la propuesta y una inválida vuelve al planner con sus defectos (RT4)
- [x] 014-C07 · Agotados los intentos, la solicitud queda `rejected`
- [x] 014-C08 · El planner en modo cambio solo tiene `propose_change` (RT4)
- [x] 014-C09 · Sin proveedor, sin sitio en el techo o con la sesión agotada, no queda solicitud
- [x] 014-C10 · Confirmar con el código encola una ejecución de cambio con su versión base
- [x] 014-C11 · La confirmación exige el código vigente de una solicitud propia en estado `proposed`
- [x] 014-C12 · Si al arrancar la versión vigente ya no es su base, la ejecución falla con `stale_base`
- [x] 014-C13 · La candidata copia la base y aplica el cambio en una sola transacción
- [x] 014-C14 · Solo los afectados pasan por el writer, en orden y en modo revisión
- [x] 014-C15 · Superado el gate, se publica la versión nueva y la solicitud pasa a `applied`
- [x] 014-C16 · La reescritura dirigida del gate puede tocar un capítulo no afectado
- [x] 014-C17 · Si la ejecución de cambio falla, la solicitud queda `rejected` y la base intacta
- [x] 014-C18 · Reanudar una ejecución de cambio revalida la base y sigue por el siguiente afectado
- [x] 014-C19 · Cada propuesta y cada ejecución de cambio dejan su traza
- [x] 014-I1 · El código calcula los capítulos afectados desde la versión base
- [x] 014-I2 · Receptor único
- [x] 014-I3 · Ningún rol escribe canon
- [x] 014-I4 · Sin un código válido no se encola nada
- [x] 014-I6 · Una petición tiene como mucho 1 + `max_retries.change` intentos (`ReintentosAcotados`)
- [x] 014-I7 · Un cambio no modifica la versión base ni ninguna otra versión publicada, tanto si publica como si falla (`VersionAnteriorConservada`)
- [x] 014-I8 · Historia lineal
- [ ] 014-I9 · En la fase `writing` de una ejecución de cambio, solo los afectados pasan por el writer, en orden ascendente
- [x] 014-I10 · Los puntos de control de una ejecución de cambio son el 0 y un prefijo de sus afectados en orden, sin huecos ni duplicados
- [x] 014-I11 · Toda decisión del motor sobre la petición y sobre los valores nuevos queda en el audit log con origen `change_request`
- [ ] 014-I12 · Los capítulos cambiados de la versión nueva son exactamente los de huella distinta de su base
- [ ] 014-C20 · Un cambio real propagado sobre la novela del brief 1 (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: `uv run python -m pytest -q` 1666 passed; `ruff check .` y `ruff format --check .` limpios; `mypy src` sin incidencias
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 015 — servidor-mcp

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/backend/015-servidor-mcp.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 015-C01 · El servidor responde en `/mcp` y publica exactamente sus siete tools
- [ ] 015-C02 · Sin un `TokenDeAcceso` válido, `/mcp` responde 401 y no ejecuta nada
- [ ] 015-C03 · La identidad es la del token de cada petición
- [ ] 015-C04 · `list_novels` devuelve las novelas del cliente con su estado y su versión vigente
- [ ] 015-C05 · `list_versions` da el historial publicado con sus capítulos cambiados
- [ ] 015-C06 · `get_chapter` devuelve un capítulo de una versión publicada
- [ ] 015-C07 · `query_story_bible` devuelve la story bible de una versión
- [ ] 015-C08 · `download_novel` devuelve el PDF guardado como recurso incrustado
- [ ] 015-C09 · Lo ajeno responde como inexistente en las siete tools
- [ ] 015-C10 · Una entrada fuera de schema es un error sin efecto
- [ ] 015-C11 · `request_change` hace la misma interpretación que la web y solo propone
- [ ] 015-C12 · Una propuesta rechazada llega con el código de la API
- [ ] 015-C13 · `confirm_change` con el código encola la ejecución de cambio
- [ ] 015-C14 · Una confirmación inválida se rechaza sin efecto
- [ ] 015-C15 · Un cambio pedido y confirmado por MCP publica versión y PDF nuevos, y conserva la anterior
- [ ] 015-C16 · Cada llamada a una tool deja exactamente una traza `mcp:<tool>`
- [ ] 015-C17 · Las trazas pasan por la máscara y nunca llevan el código de confirmación ni el PDF
- [ ] 015-I1 · Las cinco tools de lectura no modifican nada
- [ ] 015-I2 · Las tools de escritura solo proponen o encolan
- [ ] 015-I3 · La identidad es la del `TokenDeAcceso` de cada petición, verificada en el mismo punto que la API
- [ ] 015-I4 · Por MCP solo se ven versiones publicadas
- [ ] 015-I5 · Hay exactamente siete tools
- [ ] 015-I6 · Para el mismo cliente y los mismos argumentos, cada tool de lectura devuelve lo mismo que su endpoint de la API, y las de escritura recor…
- [ ] 015-I7 · Cada llamada a una tool deja exactamente una traza `mcp:<tool>` (O.4)
- [ ] 015-I8 · Cada llamada a una tool de escritura que supera el schema deja exactamente una fila `mcp_write`
- [ ] 015-I9 · El código de confirmación solo sale en claro en la respuesta de `request_change`
- [ ] 015-I10 · Nada de un brief llega a Langfuse sin pasar por la máscara
- [ ] 015-C18 · Siguiendo el README, un cliente real se conecta y pide un cambio (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 016 — recuperacion-hibrida

**Recortada** (usuario, 2026-09-24): cierra con los pasos ya `[x]` en carril-h; el resto, «(recortado)».

- [x] Spec `specs/backend/016-recuperacion-hibrida.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 016-C1 · Tarjetas iniciales al aplicar el plan
- [x] 016-C2 · Qué dice una tarjeta
- [x] 016-C3 · Aceptar un capítulo crea sucesoras solo donde algo cambia
- [x] 016-C4 · Una entidad aparece antes de lo planeado
- [x] 016-C5 · Volver a aceptar un capítulo
- [x] 016-C6 · Un hecho cambiado reconstruye las tarjetas de su entidad
- [x] 016-C7 · Vectores por huella y modelo
- [x] 016-C8 · El modelo es el de la novela, no el de la config
- [x] 016-C9 · Todo o nada con la transacción del llamante
- [x] 016-C10 · Corte temporal
- [x] 016-C11 · El canal léxico compara palabras, sin mayúsculas ni acentos
- [x] 016-C12 · BM25 con las estadísticas de la versión en el capítulo *n
- [x] 016-C13 · Consultas con signos de búsqueda o sin palabras
- [x] 016-C14 · El canal denso compara por fragmentos
- [x] 016-C15 · Fusión RRF con k = 60
- [x] 016-C16 · Desempate estable
- [x] 016-C17 · Consulta prospectiva del writer
- [x] 016-C18 · La consulta retrospectiva del editor tiene otro punto ciego
- [x] 016-C19 · `top_k` por rol y escasez
- [x] 016-C20 · Sin modelo no hay recuperación a medias
- [x] 016-I1 · Determinista
- [x] 016-I2 · Corte temporal
- [x] 016-I3 · Solo la versión pedida — verificado: test_the_lexical_ranking_and_scores_use_only_the_eligible_cards_of_the_version (test_bm25.py, ya existía) y test_syncing_a_version_never_touches_the_cards_or_vectors_of_another_version (test_cards.py, nueva)
- [x] 016-I4 · Las CanonCards son función de la story bible — verificado: pruebas de cadena y aceptación en orden de test_cards.py, test_syncing_a_copy_writes_nothing_and_a_known_text_never_calls_the_model_again (test_vectors.py, sincronizar dos veces) y test_the_same_content_loaded_in_another_order_and_with_other_ids_gives_the_same_cards (test_cards.py, nueva)
- [x] 016-I5 · Solo tarjetas de entidades — verificado: test_a_card_says_what_the_story_bible_knows_before_its_chapter (test_cards.py, ya existía) y test_a_synced_card_never_carries_a_chapters_text_or_summary (test_properties.py, nueva, propiedad con texto y resumen al azar)
- [x] 016-I7 · Un vector por (huella, modelo), solo inserción — verificado: test_vectors.py (reutiliza sin llamar al modelo, un embed por huella nueva, ningún vector se modifica ni se borra al retirar una tarjeta, secuencia de sincronizaciones con copia y cambio de hecho)
- [x] 016-I8 · No degrada en silencio (`architecture.md` §2, premisa 5) — verificado: test_model_failure.py (fallo al recuperar y al escribir una tarjeta) y test_syncing_the_story_bible_without_the_model_leaves_no_card_and_no_vector (nueva, fallo dentro de `sync_canon_cards` con la story bible completa)
- [ ] 016-C21 · El modelo real carga en el portátil (D, al final)
- [ ] 016-C22 · Línea base dorada con el modelo real (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: `uv run pytest` 867 passed; `uv run ruff check .` sin hallazgos; `uv run ruff format --check .` 176 ficheros formateados; `uv run mypy src` sin incidencias (88 ficheros).
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 017 — revision-visual

**N2** (usuario, 2026-09-24): tras el MVP.

**Diferida** (usuario, 2026-09-24): solo si sobran tokens tras 029.

- [x] Spec `specs/backend/017-revision-visual.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 017-C01 · La estructura esperada sale de la candidata
- [ ] 017-C02 · El revisor recibe la dirección de la vista y la forma de lo que entrega, no los valores
- [ ] 017-C03 · La sesión del revisor solo navega la vista
- [ ] 017-C04 · Una revisión que coincide pasa
- [ ] 017-C05 · La comparación tolera espacios y mayúsculas, no letras
- [ ] 017-C06 · Una portada que no muestra lo suyo es fallo de render
- [ ] 017-C07 · Un índice que no lleva a sus capítulos es fallo de render
- [ ] 017-C08 · Un capítulo que no se ve entero es fallo de render
- [ ] 017-C09 · Una ficha que no enlaza lo que debe es fallo de render
- [ ] 017-C10 · Una entidad sin capítulo cuyo nombre sale en el texto es un fallo de datos atribuido, y no se abre el revisor
- [ ] 017-C11 · Una entidad sin capítulo que ningún capítulo nombra es un defecto no atribuible
- [ ] 017-C12 · Una entrega fuera de schema vuelve al revisor
- [ ] 017-C13 · Una vista vacía o con error es fallo de render en las cuatro partes
- [ ] 017-C14 · Una sesión sin entrega válida es un ciclo fallido, no un defecto de la novela
- [ ] 017-C15 · Sin navegador, la ejecución se interrumpe y no publica
- [ ] 017-C16 · Cada revisión deja su resultado, su span y sus scores
- [ ] 017-C17 · Integración: un fallo de datos vuelve al editor y el ciclo siguiente publica
- [ ] 017-C18 · Integración: un fallo de render hace fallar la ejecución
- [ ] 017-C19 · La revisión visual corre en el gate de un cambio y de una edición manual
- [ ] 017-I1 · El resultado lo decide el código
- [ ] 017-I2 · El revisor nunca recibe los valores que el código compara (título, nombre del destinatario, dedicatoria, títulos y textos de capítulo, no…
- [ ] 017-I3 · `revision-visual` no escribe canon ni capítulos
- [ ] 017-I4 · Todo defecto de `revision-visual` es de datos o de render
- [ ] 017-I5 · Si en un ciclo `revision-visual` no pasa (por datos, render, sin entrega o sin navegador), en ese ciclo no se genera el PDF ni se publica
- [ ] 017-I6 · La sesión del revisor visual solo tiene sus cuatro tools y el servidor Playwright MCP, sin `Skill`, solo navega el origen de la vista y s…
- [ ] 017-C20 · Sonda de la vista con el browser MCP de desarrollo (D, al final)
- [ ] 017-C21 · El revisor real aprueba una vista correcta (D, al final)
- [ ] 017-C22 · El revisor real caza un enlace de la ficha sembrado roto (D, al final)
- [ ] 017-C23 · En la primera generación real, la etapa corre en el gate (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 018 — linters-de-prosa

**N2** (usuario, 2026-09-24): tras el MVP.

**Diferida** (usuario, 2026-09-24): C18–C23, solo si sobran tokens tras 029.

- [x] Spec `specs/backend/018-linters-de-prosa.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 018-C1 · `linter-repeticion`: una palabra repetida en un párrafo
- [x] 018-C2 · `linter-repeticion`: una muletilla repetida en un párrafo
- [x] 018-C3 · `linter-legibilidad`: medidas e índice
- [x] 018-C4 · `linter-legibilidad`: la longitud media de frase en su límite
- [x] 018-C5 · `linter-legibilidad`: el índice en su límite
- [x] 018-C6 · `linter-legibilidad`: la franja del destinatario elige el objetivo
- [x] 018-C7 · Recuento de sílabas
- [x] 018-C8 · Recuento de frases
- [x] 018-C9 · `linter-estilo-ia`: la densidad de adverbios en -mente en su límite
- [x] 018-C10 · `linter-estilo-ia`: palabras en -mente que no son adverbios
- [x] 018-C11 · `linter-estilo-ia`: clichés y giros de texto generado
- [x] 018-C12 · `linter-consistencia`: narrador en tercera persona
- [x] 018-C13 · `linter-consistencia`: narrador en primera persona
- [x] 018-C14 · `linter-consistencia`: tratamiento sin excepciones
- [x] 018-C15 · `linter-consistencia`: tratamiento con excepciones y mezcla
- [x] 018-C16 · Capítulo limpio
- [x] 018-C17 · Texto sin palabras
- [ ] 018-C18 · Corren tras los hooks y antes del editor, que recibe sus avisos
- [ ] 018-C19 · Una entrega que no pasa los hooks no llega a los linters
- [ ] 018-C20 · Con solo avisos, el capítulo se acepta
- [ ] 018-C21 · En una reescritura por otra causa, el writer recibe los avisos
- [ ] 018-C22 · Con la aceptación: un resultado por linter en SQLite y en el informe
- [ ] 018-C23 · Tras el commit: un score por linter en Langfuse
- [x] 018-I1 · Todo aviso es un `Defecto` no bloqueante, sin criterio de rúbrica, con su capítulo y un mensaje que nombra lo detectado y su párrafo (o e…
- [x] 018-I2 · Los linters son deterministas

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 019 — edicion-manual

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/backend/019-edicion-manual.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 019-C01 · Texto sin nada que avisar
- [ ] 019-C02 · Forma no canónica de un personaje
- [ ] 019-C03 · Personaje desconocido
- [ ] 019-C04 · Hecho nominal que el capítulo usaba y ya no aparece
- [ ] 019-C05 · Prohibidas de los tres niveles
- [ ] 019-C06 · Avisos de los linters de prosa
- [ ] 019-C07 · Reaparición tras un evento excluyente
- [ ] 019-C08 · Edad escrita que no cuadra con la fecha de nacimiento
- [ ] 019-C09 · Rechazos del lint
- [ ] 019-C10 · Un guardado que pasa encola la edición
- [ ] 019-C11 · Una base que ya no es la vigente da 409
- [ ] 019-C12 · Una prohibida da 422
- [ ] 019-C13 · Una longitud fuera de rango da 422
- [ ] 019-C14 · Una forma no canónica da 422, también al renombrar a una variante
- [ ] 019-C15 · Varios bloqueantes a la vez
- [ ] 019-C16 · Una inyección en el texto se marca y no bloquea
- [ ] 019-C17 · Rechazos de acceso y de forma
- [ ] 019-C18 · Edición sin hechos cambiados
- [ ] 019-C19 · Una edición que cambia un hecho nominal se propaga
- [ ] 019-C20 · Las puntuaciones del editor no bloquean en el capítulo editado
- [ ] 019-C21 · Los hechos cambiados inválidos vuelven al editor
- [ ] 019-C22 · Un validador determinista bloquea en la ejecución
- [ ] 019-C23 · Un fallo del gate atribuido al capítulo editado rechaza la edición
- [ ] 019-C24 · Un fallo del gate atribuido solo a otros capítulos
- [ ] 019-C25 · Un fallo de datos de la ficha en el capítulo editado se vuelve a registrar
- [ ] 019-C26 · Una base obsoleta al arrancar
- [ ] 019-C27 · Reanudar una edición
- [ ] 019-C28 · Una inyección en el texto editado que el editor obedece (RT16)
- [ ] 019-I1 · El capítulo editado se publica como lo dejó la persona
- [ ] 019-I2 · El lint en vivo no escribe nada y es determinista
- [ ] 019-I3 · Lo que el lint marca como bloqueante es lo que bloquea el guardado
- [ ] 019-I4 · Un guardado rechazado no crea nada
- [ ] 019-I5 · Toda decisión sobre el texto de una edición queda en el audit log con origen `manual_edit`
- [ ] 019-I6 · Ninguna edición se publica sin el gate completo con `cronologia-lean`
- [ ] 019-I7 · En el capítulo editado bloquean los validadores deterministas y el gate, nunca el editor
- [ ] 019-I8 · El texto editado solo lo interpreta el editor
- [ ] 019-I10 · Solo cambian el capítulo editado y los afectados
- [ ] 019-I11 · La `EdicionManual` sigue a su ejecución
- [ ] 019-I12 · La historia de versiones es lineal
- [ ] 019-C29 · Edición manual real con Lean (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 020 — evals

- [x] Spec `specs/backend/020-evals.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; recibe `example` desde 013 (C15, C16); re-marcada 2026-09-25 (integrador: sin revisión, decisión del usuario) con C17, la identidad del brief de eval, C16 servida por la ejecución del brief 1 y C18 (prohibidas de nivel user de un brief, a nivel novela)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; pasos C15 y C16 añadidos; re-marcado 2026-09-25 (integrador: sin revisión, decisión del usuario) con C17, C16 servida por el brief 1 y C18

### Steps
- [x] 020-C01 · Los cinco briefs del repositorio son válidos
- [x] 020-C02 · Sin un cliente registrado no se crea nada
- [x] 020-C03 · Una novela y una ejecución por brief, del cliente dado
- [x] 020-C04 · Un brief que no pasa no para a los demás
- [x] 020-C05 · `evals run` no corre en la CI
- [x] 020-C06 · Celdas de la tabla brief × validador
- [x] 020-C07 · Resumen por brief
- [x] 020-C08 · La tabla sale solo de SQLite
- [x] 020-C09 · Sin ejecuciones de evals, la tabla lo dice
- [x] 020-I1 · Ninguna prueba de esta spec llama a un modelo ni a Langfuse
- [x] 020-I2 · `evals table` es determinista
- [x] 020-C15 · `example` produce la novela y su PDF (movido desde 013)
- [x] 020-C17 · Un brief que ya tiene novela del cliente no se repite (añadido 2026-09-25; también identifica la novela de `example` como la de su brief)
- [x] 020-C18 · Las prohibidas de nivel user de un brief no alcanzan a los demás briefs (añadido 2026-09-25, tras la ejecución 11; aplazado por el usuario y retomado en la segunda tanda, carril Z)
- [x] 020-C06 (bug de la tanda D) · la tabla lee los nombres y el detail reales de los validadores y la última ejecución de cada brief
- [ ] 020-C10 · Cinco briefs reales llenan (a) y (b) (D, al final)
- [ ] 020-C11 · Una iteración de tuning con antes y después (D, al final)
- [ ] 020-C12 · Juez frente a revisión humana (D, al final)
- [ ] 020-C13 · El caso que solo detecta Lean (D, al final)
- [ ] 020-C14 · Un cambio del lector propagado y su coste (D, al final)
- [ ] 020-C16 · La novela de ejemplo real: el PDF de la ejecución del brief 1 de 020-C10 (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: pasos no D cerrados (C01–C09, C15, C17, I1, I2; C10–C14 y C16 quedan `(D, al final)`); `uv run python -m pytest -q` 1636 passed, `uv run python -m ruff check .` y `uv run python -m ruff format --check .` limpios, `uv run python -m mypy src` sin incidencias; re-verificado 2026-09-25 (carril Z): `uv run pytest` 1680 passed, `ruff check .` y `ruff format --check .` limpios (399 ficheros), `mypy src` sin incidencias en 158 ficheros
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 021 — auditoria-de-seguridad

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/backend/021-auditoria-de-seguridad.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 021-C05 · El informe dice qué se hizo con cada hallazgo (I, al final)
- [ ] 021-C01 · Inyección de prompts por cada vía de texto no confiable (D, al final)
- [ ] 021-C02 · Exfiltración entre clientes y novelas (D, al final)
- [ ] 021-C03 · Dependencias con vulnerabilidades conocidas (D, al final)
- [ ] 021-C04 · Secretos en todo el historial (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 022 — acceso

- [x] Spec `specs/frontend/022-acceso.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 022-C01 · Registro válido lleva a la pantalla de acceso
- [x] 022-C02 · Registro con un email ya usado
- [x] 022-C03 · Errores de datos inválidos, campo a campo
- [x] 022-C04 · Acceso válido guarda la sesión y entra
- [x] 022-C05 · Credenciales incorrectas
- [x] 022-C06 · Cada petición a una pantalla protegida envía la sesión guardada
- [x] 022-C07 · Sin sesión guardada, una pantalla protegida redirige a acceso
- [x] 022-C08 · Una sesión rechazada por el servidor redirige a acceso
- [x] 022-C09 · Cerrar sesión borra la sesión guardada sin avisar al servidor
- [x] 022-I1 · El token de la sesión solo viaja en la cabecera de autorización de cada petición
- [x] 022-I2 · Ninguna contraseña escrita en un formulario queda guardada ni se vuelve a mostrar tras enviarse, la petición salga bien o mal
- [x] 022-I3 · Una sesión guardada sobrevive a volver a cargar la pantalla, hasta que se cierra sesión o el servidor la rechaza
- [x] 022-I4 · Una pantalla protegida nunca pide datos a la API antes de comprobar que hay una sesión guardada
- [ ] 022-C10 · El recorrido completo se observa en el navegador (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: front lint 0 errores · typecheck limpio · build OK · vitest 3 ficheros, 26 pruebas verdes; 022-C10 (D, al final)
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 023 — mis-novelas

**Alcance completo** (usuario, 2026-09-25, segunda decisión): vuelven crear novela, las prohibidas `user` y sus I; C09 enlaza también a la entrevista y al progreso (`architecture.md` §18, «Alcance del frontend»).

- [x] Spec `specs/frontend/023-mis-novelas.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (N1 mínima, C09 reescrito, C17 nuevo); re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (alcance completo; C09 con entrevista y progreso)
- [x] Plan below approved — integrador 2026-09-25: sin revisión, decisión del usuario

### Steps
- [x] 023-C01 · Lista vacía
- [x] 023-C02 · Cada estado derivado tiene una etiqueta propia
- [x] 023-C03 · Versión vigente, con número o vacía
- [x] 023-C04 · Novela sin título todavía
- [x] 023-C05 · La lista respeta el orden que entrega la API
- [x] 023-C06 · Fallo al cargar la lista
- [x] 023-C09 · El destino depende del estado y de la versión vigente
- [x] 023-C17 · El acceso lleva a «mis novelas»
- [x] 023-C07 · Crear una novela lleva a su entrevista
- [x] 023-C08 · Fallo al crear una novela
- [x] 023-C10 · Ver la lista prohibida de nivel `user`
- [x] 023-C11 · Añadir una palabra
- [x] 023-C12 · Añadir un tema con sus palabras clave
- [x] 023-C13 · Alta rechazada
- [x] 023-C14 · Alta de un término repetido
- [x] 023-C15 · Borrar una entrada
- [x] 023-I1 · Los cuatro estados derivados de `definitions.md` §3 tienen cada uno su etiqueta, y ningún otro valor cae en un caso por defecto silencioso
- [x] 023-I3 · Ninguna llamada de esta pantalla a la API real
- [x] 023-I4 · Un error de cualquier llamada de esta pantalla (lista, alta o borrado prohibido, crear novela) siempre se muestra; nunca se descarta en s…
- [ ] 023-C16 · Recorrido real de «mis novelas» (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: frontend (pnpm.cmd lint, pnpm.cmd typecheck, pnpm.cmd test 117 passed, pnpm.cmd build) verdes.
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 024 — entrevista

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/frontend/024-entrevista.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (C17 ofrece escribir la novela; C21 nuevo)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (C17 ofrece escribir la novela; C21 nuevo)

### Steps
- [x] 024-C21 · Escribir la novela desde el brief confirmado
- [x] 024-C01 · Historial vacío al entrar en una entrevista nueva
- [x] 024-C02 · Enviar un mensaje añade la respuesta del entrevistador
- [x] 024-C03 · Fallo al enviar un mensaje
- [x] 024-C04 · Rechazo de un mensaje vacío antes de enviarlo
- [x] 024-C05 · El panel muestra lo fijado, lo que falta y las contradicciones
- [x] 024-C06 · Cota de obligatorios
- [x] 024-C07 · Enviar un texto libre y ver sus hechos verificados
- [x] 024-C08 · Aceptar y rechazar un hecho
- [x] 024-C09 · Marcar un hecho obligatorio
- [x] 024-C10 · Fallo al enviar un texto libre
- [x] 024-C11 · Texto libre vacío no se envía
- [x] 024-C12 · Ver la lista prohibida de nivel `novel`
- [x] 024-C13 · Añadir una palabra o un tema
- [x] 024-C14 · Alta rechazada o repetida
- [x] 024-C15 · Borrar una entrada prohibida
- [x] 024-C16 · Confirmar disponible solo sin problemas
- [x] 024-C17 · Confirmar un brief válido ofrece escribir la novela
- [x] 024-C18 · Confirmación rechazada
- [x] 024-C19 · Entrada en una novela con el brief ya confirmado
- [x] 024-I2 · Ninguna llamada de esta pantalla a la API real fuera de 024-C20
- [x] 024-I3 · Un error de cualquier llamada de esta pantalla (mensaje, texto libre, aceptar o rechazar un hecho, alta o borrado prohibido, confirmar) s…
- [x] 024-I5 · Con el brief confirmado, ninguna acción de escritura de esta pantalla (mensaje, texto libre, hecho, prohibida) queda disponible
- [ ] 024-C20 · Recorrido real de la entrevista (D, al final)

### Closing
- [x] Full suite green, type checks clean
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 025 — progreso

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/frontend/025-progreso.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (C00 nuevo)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (C00 nuevo)

### Steps
- [x] 025-C00 · La pantalla sigue la ejecución más reciente de la novela
- [x] 025-C01 · El sondeo refleja fase y capítulo mientras la ejecución avanza
- [x] 025-C02 · En cola, se muestra la posición sin fase ni capítulo
- [x] 025-C03 · Un fallo al sondear se muestra sin detener el sondeo
- [x] 025-C04 · Publicada, el sondeo se detiene y navega a la lectura
- [x] 025-C05 · Fallida, el sondeo se detiene y muestra el informe
- [x] 025-C06 · Fallo al pedir el informe
- [x] 025-C07 · Interrumpida, se ofrece reanudar con su motivo
- [x] 025-C08 · Reanudar vuelve a mostrar el progreso en curso
- [x] 025-C09 · Reanudar rechazada
- [x] 025-C10 · Ejecución ajena o inexistente
- [x] 025-I1 · El sondeo pide `GET /api/runs/{id}` al mismo intervalo fijo mientras la ejecución no está en un estado terminal, y nunca deja de pedirlo…
- [x] 025-I2 · Tras `published` o `failed`, la pantalla no vuelve a pedir `GET /api/runs/{id}`
- [x] 025-I3 · La pantalla nunca reanuda una ejecución sin que la persona pulse el botón
- [x] 025-I4 · Un error de cualquier llamada de esta pantalla (sondeo, informe, reanudar) siempre se muestra; nunca se descarta en silencio ni deja la p…
- [ ] 025-C11 · Recorrido real de una ejecución hasta publicar o fallar (D, al final)

### Closing
- [x] Full suite green, type checks clean
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 026 — lectura

**N1** (usuario, 2026-09-24): web mínima, lectura y cambio del lector (`architecture.md` §18, «Alcance del frontend»); sus I, recortadas.

- [x] Spec `specs/frontend/026-lectura.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada — integrador 2026-09-25: sin revisión, decisión del usuario (carril R: C15, C16)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado — integrador 2026-09-25: sin revisión, decisión del usuario (C15, C16)

### Steps
- [x] 026-C01 · Sin versión indicada, se muestra la vigente
- [x] 026-C02 · Portada con dedicatoria
- [x] 026-C03 · Índice navegable a los capítulos
- [x] 026-C04 · Página de novedades y marca de cambio
- [x] 026-C05 · Sin capítulos cambiados, no hay página de novedades
- [x] 026-C06 · Ficha con enlaces a los capítulos donde aparece cada entidad
- [x] 026-C07 · Una entidad sin capítulos aparece en la ficha sin enlaces
- [x] 026-C08 · El selector lista las versiones publicadas, en el orden que entrega la API
- [x] 026-C09 · Cambiar de versión recarga todo el contenido con el de la versión elegida
- [x] 026-C10 · Descargar el PDF de la versión que se está viendo
- [x] 026-C11 · El PDF aún no está disponible
- [x] 026-C12 · Fallo al cargar la lista de versiones
- [x] 026-C13 · Fallo al cargar el detalle de una versión
- [x] 026-C15 · Mientras carga, la pantalla lo indica
- [ ] 026-C16 · La lectura se presenta como un libro, en escritorio y en móvil (D, al final)
- [ ] 026-I1 · Lo mostrado (portada, novedades, índice, capítulos, ficha) es siempre de una sola versión, la que marca el selector; nunca mezcla datos d… (recortado)
- [ ] 026-I3 · Todo enlace interno de la página de novedades, del índice y de la ficha lleva al capítulo correcto dentro de la propia pantalla (recortado)
- [ ] 026-I4 · Un error de cualquier llamada de esta pantalla (lista de versiones, detalle, PDF) siempre se muestra; nunca se descarta en silencio ni de… (recortado)
- [ ] 026-I5 · Ninguna llamada de esta pantalla a la API real (recortado)
- [ ] 026-C14 · El recorrido completo se observa en el navegador (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: `uv run pytest` 1672 passed; `uv run ruff check .` all checks passed; `uv run ruff format --check .` 399 files already formatted; `uv run mypy src` no issues in 158 source files; frontend `pnpm.cmd lint`, `pnpm.cmd typecheck`, `pnpm.cmd build` limpios, `pnpm.cmd test` 62 passed
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 027 — cambio-del-lector

**N1** (usuario, 2026-09-24): web mínima, lectura y cambio del lector (`architecture.md` §18, «Alcance del frontend»); sus I, recortadas.

**Carril R** (integrador 2026-09-25): pulido visual del panel de cambio sin comportamiento nuevo, bajo 026-C16 (que lo incluye); 027-C01 a C14 siguen verdes, nada que re-marcar.

- [x] Spec `specs/frontend/027-cambio-del-lector.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada sin 025-progreso (C09 reescrito)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcado con C09 nuevo

### Steps
- [x] 027-C01 · Seleccionar un fragmento o un hecho abre el formulario de petición
- [x] 027-C02 · La petición vacía no se puede enviar
- [x] 027-C03 · Enviar la petición muestra la propuesta, los afectados y la caducidad
- [x] 027-C04 · Una propuesta sin afectados se muestra igual
- [x] 027-C05 · Petición rechazada por la policy o por la propuesta
- [x] 027-C06 · Petición sobre una selección que ya no vale
- [x] 027-C07 · Fallo del servidor al pedir el cambio
- [x] 027-C08 · Enviar deshabilita la acción mientras está en curso
- [x] 027-C09 · Confirmar encola la ejecución y lo indica en la lectura
- [x] 027-C10 · Descartar no confirma nada
- [x] 027-C11 · Confirmar o descartar deshabilita las dos acciones mientras está en curso
- [x] 027-C12 · La propuesta caduca sin confirmar
- [x] 027-C13 · Confirmar una propuesta que el servidor ya considera caducada
- [x] 027-C14 · Fallo del servidor al confirmar
- [ ] 027-I1 · El código de confirmación nunca se muestra en la pantalla (recortado)
- [ ] 027-I2 · Confirmar nunca se dispara sin que la persona pulse «confirmar»; ningún temporizador ni sondeo la confirma por su cuenta (recortado)
- [ ] 027-I3 · Un error de cualquier llamada de esta pantalla (pedir, confirmar) siempre se muestra; nunca se descarta en silencio ni deja la pantalla c… (recortado)
- [ ] 027-I5 · La petición nunca se envía sin una selección previa de fragmento o hecho (recortado)
- [ ] 027-C15 · Recorrido real: pedir, confirmar y ver la versión nueva (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: lint, typecheck, build y test (6 ficheros, 53 pruebas) verdes en `frontend/`; contrato de la API simulada (rutas, 201/409/422/202, `expires_at`, `Selection`, campos de confirmar) coincide con 014 ya en V2
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 028 — edicion-manual

**N3** (usuario, 2026-09-24): tras el MVP.

**Dentro del alcance** (usuario, 2026-09-25, segunda decisión): se implementa en la segunda tanda.

- [x] Spec `specs/frontend/028-edicion-manual.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 028-C01 · Abrir el editor precarga el texto vigente del capítulo
- [x] 028-C02 · El editor solo se ofrece en la versión vigente
- [x] 028-C03 · Fallo al cargar el capítulo
- [x] 028-C04 · Los diagnósticos llegan tras una pausa de escritura, no en cada pulsación
- [x] 028-C05 · Los diagnósticos con posición se resaltan en el texto
- [x] 028-C06 · Los diagnósticos sin posición se muestran aparte
- [x] 028-C07 · Diagnósticos no bloqueantes se distinguen de los que bloquean
- [x] 028-C08 · Cada respuesta de lint sustituye a la anterior, aunque lleguen desordenadas
- [x] 028-C09 · Un fallo del lint no impide seguir editando
- [x] 028-C10 · Ningún diagnóstico bloquea la escritura
- [x] 028-C11 · Guardar aceptado lleva al seguimiento de la ejecución
- [x] 028-C12 · Guardar rechazado por diagnósticos bloqueantes
- [x] 028-C13 · Guardar con la base obsoleta
- [x] 028-C14 · Fallo de red al guardar
- [x] 028-I1 · El texto que se envía al guardar es exactamente el que hay en el editor en ese momento, sin que la pantalla lo transforme
- [x] 028-I2 · Los diagnósticos mostrados corresponden siempre a la última petición de lint enviada, nunca a una respuesta anterior que llega tarde
- [x] 028-I3 · Ningún diagnóstico del lint impide escribir en el editor; solo el guardado queda sujeto a lo que la API rechace
- [x] 028-I5 · Un error de cualquier llamada de esta pantalla (cargar el capítulo, lint, guardar) siempre se muestra; nunca se descarta en silencio ni d…
- [x] 028-I6 · Ninguna llamada de esta pantalla a la API real
- [ ] 028-C15 · El recorrido completo se observa en el navegador (D, al final)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: lint, typecheck, test (76 pasan, 8 ficheros), build, todos verdes
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 029 — cli

- [x] Spec `specs/backend/029-cli.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada tras el recorte de casos C (usuario, 2026-09-24)
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario; re-marcada tras el recorte de casos C (usuario, 2026-09-24)

### Steps
- [x] 029-C01 · Entrevistar una novela nueva
- [ ] 029-C02 · Seguir una entrevista guardada
- [ ] 029-C03 · Cliente o novela ajenos
- [ ] 029-C04 · Un turno fallido no se guarda
- [x] 029-C05 · Texto libre desde un fichero
- [x] 029-C06 · Aceptar, rechazar y marcar obligatorio un hecho
- [x] 029-C07 · Confirmar el brief pide un sí explícito
- [x] 029-C08 · Lanzar la generación pide un sí explícito
- [ ] 029-C09 · Pedir un cambio sobre un hecho y confirmarlo
- [ ] 029-C10 · Pedir un cambio sobre un fragmento
- [ ] 029-C11 · Sin un sí, nada se encola
- [ ] 029-C12 · Petición denegada o rechazada
- [ ] 029-C13 · Sin proveedor o sin sitio en el techo
- [ ] 029-C14 · Novela ajena, inexistente o sin versión publicada
- [ ] 029-I1 · La CLI decide como la API
- [ ] 029-I2 · Nada se confirma ni se encola sin una respuesta `s`
- [ ] 029-I3 · El código de confirmación del cambio no aparece nunca en la salida

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-24: uv run pytest (1475 passed), ruff check ., ruff format --check . (324 files), mypy src (0 issues)
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

## 030 — report-metrics

- [x] Spec `specs/backend/030-report-metrics.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 030-C07 · Sin ejecuciones, el informe lo dice
- [ ] 030-C08 · Ruta de salida
- [ ] 030-C01 · Coste, tokens y latencia por novela
- [ ] 030-C02 · Por capítulo
- [ ] 030-C03 · Por rol
- [ ] 030-C04 · Scores por validador y novela
- [ ] 030-C05 · Versiones de prompt
- [ ] 030-C06 · Un dato que falta es un hueco, nunca una estimación
- [ ] 030-I1 · El informe es determinista
- [ ] 030-I2 · Ninguna prueba ni la orden llaman a un modelo, a Langfuse ni a la red
- [ ] 030-I3 · El fichero no contiene texto de capítulos, prompts, briefs ni el detalle JSON de los validadores

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 031 — arranque

- [x] Spec `specs/backend/031-arranque.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [x] 031-C05 · El adaptador de incrustaciones (carril Y)
- [x] 031-C01 · `serve` monta la API completa
- [x] 031-C04 · Una novela nueva usa el modelo de incrustación real (tras C05 en V2)
- [x] 031-C02 · Arrancar el servidor pone el worker a tomar la cola
- [x] 031-C03 · Parar el servidor apaga el worker sin perder nada
- [x] 031-I2 · Ninguna prueba de esta spec llama a un modelo, a Langfuse ni a GitHub
- [ ] 031-I1 · El montaje es uno (lo lee el `verificador`) (recortado)

### Closing
- [x] Full suite green, type checks clean — verificador 2026-09-25: `uv run pytest` 1536 passed; `uv run ruff check .` OK; `uv run ruff format --check .` OK (356 files); `uv run mypy src` OK (147 files). 031-I1 (recortado): class I, no mapeado a TLA+ ni protege un validador, no bloquea el cierre; `pipeline/planning_seam.py` cubierto por la propiedad ampliada de 031 (`backend/AGENTS.md`, integrador 2026-09-25, a031009).
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true
