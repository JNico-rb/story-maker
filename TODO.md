# TODO — planes de implementación

Reglas (detalle en `AGENTS.md`, procesos 2–4 y *Parallel lanes*):

1. Un bloque por spec, en orden numérico, con el formato de `AGENTS.md` proceso 3. Ningún código, tampoco el scaffolding, antes de que su spec y su plan estén aprobados.
2. Las casillas de aprobación las marca el integrador, sin revisión (decisión del usuario, 2026-09-24); las de cierre, `verificador`. Los pasos D quedan `[ ]` con `(D, al final)` y no impiden cerrar.
3. Un paso se marca `[x]` solo cuando su caso pasa a verde.
4. Cada carril edita solo los bloques de sus specs; esta cabecera y sus tablas son del integrador (checkout principal, V2).
5. Una spec empieza cuando sus dependencias están cerradas en V2, o en la rama de su propio carril.

## Estado (2026-09-24, etapa 2 en curso)

- **000:** spec y plan aprobados; implementación en V2 (integrador), pasos C01–C05 en verde.
- **001:** spec redactada entera; auditor en curso (spec y plan).
- **006:** auditor ronda 1 con 4 contradicciones en docs; el integrador los corrige y va a ronda 2.
- **Borradores** (sin aprobar, pueden estar incompletos): 002, 003, 007, 008, 009, 010, 011, 012, 014, 015, 016, 017, 018, 019. **Sin redactar:** 004, 005, 013, 020, 021.
- **Borradores de plan:** `specs/.drafts/plan-NNN.md`. **Bloques** en este fichero: 000, 001, 002, 006.
- **Avisos abiertos:**
  - README: la tabla TLA+ contradice §9.1; la corrige 006-C9.
  - `ci.yml` descarga `tla2tools` «latest», contra 000-I1; lo corrige el plan de 000.
  - `.github/workflows/` para 007 en la tabla de propiedad del carril D.
  - 009 ofrece la lectura de la `Cronologia` y la escritura de `chronology_files` (lo pide 007).
  - 012 decide qué hace el gate con el `error` de 007; la propuesta es `failed` con `internal_error`.
  - 014: la propuesta pedida por MCP cuelga de `mcp:request_change` (lo pide 015).
  - Fila U «modelo pequeño» para 006-I11, si 006 no la añadió.
- **Tareas humanas:**
  - `GITHUB_TOKEN` de grano fino para 007-C25.
  - Decidir si V2 pasa a ser la rama por defecto: `workflow_dispatch` necesita el workflow en la rama por defecto.
- **Reglas del usuario (2026-09-24):**
  - Como mucho 2 subagentes a la vez.
  - `auditor` siempre en opus. `redactor-specs`, `verificador` e `implementador` en sonnet, salvo el implementador de 006, 007, 012 y 014 y un fallo que se repite tras 2 intentos, que van en opus.
  - El redactor deja el borrador del plan en `specs/.drafts/plan-NNN.md` y añade sus filas de §18. El auditor hace la spec y, si queda a gap cero, el plan en la misma llamada. Informes de 5 líneas como mucho.
  - Nunca se recorta alcance: si falta cuota, se para.
  - Un solo carril al principio; el segundo, cuando el primero cierre una spec en verde.
- **Siguiente:**
  1. Cerrar 000 (TDD en V2 + `verificador`) y aprobar el plan de 001 → arrancar el carril A.
  2. De dos en dos, por la ruta crítica: terminar y auditar 002, 009, 010, 011…; redactar 004, 005, 013, 020 y 021.
  3. Frontend 022–028 cuando estén aprobadas 002, 008, 011, 013, 014, 018 y 019.

## Carriles

| Carril | Specs en orden | Depende de (fuera del carril) | Worktree | Rama | Estado |
|---|---|---|---|---|---|
| 0 — scaffolding (integrador) | 000 | — | checkout principal | `V2` | spec y plan aprobados; implementación en curso |
| A — núcleo de generación | 001 → 003 → 010 → 011 → 012 → 014 | 004, 009 (B) · 002, 005 (C) · 006, 007 (D) | `../sm-a` | `carril-a` | espera 000 |
| B — plataforma y observabilidad | 009 → 004 → 013 → 015 → 017 | 001, 012, 014 (A) · 002, 008 (C) | `../sm-b` | `carril-b` | espera 000 y 001 |
| C — entrada y política | 005 → 002 → 008 → 018 → 019 | 001, 003, 011, 012 (A) · 004 (B) | `../sm-c` | `carril-c` | espera 000 (luego 005 arranca con lo puro) |
| D — formal y calidad | 006 → 007 → 016 → 020 → 021 | 009, 015 (B) · 012 (A) · 002 (C) | `../sm-d` | `carril-d` | espera 000 (luego 006 y 007 arrancan ya) |
| E — frontend | 022 → 023 → 024 → 025 → 026 → 027 → 028 (`specs/frontend/`) | 002, 008 (C) · 011, 014 (A) · 013 (B) · 018, 019 (C) | `../sm-e` | `carril-e` | specs sin redactar; esperan a las specs de backend de las que dependen |

## Specs

| NNN | Spec | Lado | Carril | Depende de |
|---|---|---|---|---|
| 000 | scaffolding (herramientas, estructura, CI, marca del frontend, hooks de desarrollo) | transversal | 0 | — |
| 001 | base | backend | A | 000 |
| 002 | autenticacion | backend | C | 001 |
| 003 | puerto-de-agente | backend | A | 001 |
| 004 | observabilidad | backend | B | 001 |
| 005 | guardarrailes | backend | C | 001 *parcial*: lo puro no la necesita; el audit log sí |
| 006 | especificacion-tla | backend | D | 000 |
| 007 | validador-lean | backend | D | 009 *parcial*: solo el adaptador a SQLite |
| 008 | brief-y-entrevista | backend | C | 002, 003, 004, 005 |
| 009 | story-bible-y-versiones | backend | B | 001, 002 |
| 010 | planificacion | backend | A | 003, 004, 009 |
| 011 | produccion-de-capitulos | backend | A | 002, 005, 006, 010 |
| 012 | gate-de-publicacion | backend | A | 007, 011 |
| 013 | lectura-y-pdf | backend | B | 009 |
| 014 | cambios-del-lector | backend | A | 012 |
| 015 | servidor-mcp | backend | B | 002, 008, 013, 014 |
| 016 | recuperacion-hibrida | backend | D | 009 |
| 017 | revision-visual | backend | B | 012, 013 |
| 018 | linters-de-prosa | backend | C | 011 |
| 019 | edicion-manual | backend | C | 012, 018 |
| 020 | evals | backend | D | 012 |
| 021 | auditoria-de-seguridad | backend | D | 002, 015 |
| 022 | acceso (registro, inicio de sesión, rutas protegidas, marca común) | frontend | E | 000, 002 |
| 023 | mis-novelas (lista con estado y versión vigente, crear novela, prohibidas de nivel usuario) | frontend | E | 022, 005, 008 |
| 024 | entrevista (chat, panel del brief, textos libres, hechos por aceptar, prohibidas de novela, confirmación) | frontend | E | 023, 008 |
| 025 | progreso (sondeo de la ejecución, reanudar, informe) | frontend | E | 024, 011 |
| 026 | lectura (portada y dedicatoria, índice, capítulos cambiados, ficha con enlaces, versiones, PDF) | frontend | E | 022, 013 |
| 027 | cambio-del-lector (seleccionar, pedir, propuesta y afectados, confirmar, ver la versión nueva) | frontend | E | 026, 025, 014 |
| 028 | edicion-manual (editor con lint en vivo, guardar, versión nueva) | frontend | E | 026, 025, 018, 019 |

Todas dependen de 000. Arranque en paralelo cuando 000 esté cerrada: A (001), C (005, lo puro) y D (006, 007); B cuando 001 esté integrada.

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
- [ ] 000-C15 · Claude Code conecta los servidores de `.mcp.json` (D, al final)
- [ ] 000-C16 · Playwright MCP inspecciona la SPA en Edge: marca, mismo origen y proxy de `/api` (D, al final)
- [ ] 000-C17 · En una sesión real, los hooks y los permisos actúan (D, al final)
- [x] 000-C18 · La primera CI de `V2` sale en verde, con Lean y TLC — CI de 1f4eacd verde: backend, frontend, formal (Lean y TLC), seguridad
- [ ] 000-C19 · La CI se pone en rojo ante defectos sembrados (D, al final)

### Closing
- [x] Full suite green, type checks clean
- [x] Spec updated, or confirmed still true
- [x] Docs updated, or confirmed still true

— verificador 2026-09-24: backend (uv sync, pytest 112 passed, ruff check, ruff format --check, mypy src) verdes; frontend (pnpm lint, typecheck, build, test 5 passed en 2 ficheros) verdes; hooks (node --test .claude/hooks/*.test.mjs) 118 passed. C01–C14 y C20 trazados a pruebas; C15–C19 (D, al final) quedan sin marcar por regla del usuario y no bloquean el cierre.

## 001 — base

- [x] Spec `specs/backend/001-base.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 001-C03 · Ajustes: valores por defecto, rutas desde la raíz y precedencia del entorno
- [ ] 001-C04 · Ajustes obligatorios y condicionales
- [ ] 001-C01 · El `config.json` del repositorio es válido y lleva los valores de §15.4
- [ ] 001-C02 · La config se valida entera y nombra cada clave que falta, sobra o no vale
- [ ] 001-C05 · `.env.example` lista los ajustes sin valores
- [ ] 001-C06 · `init-db` crea la base con el esquema completo
- [ ] 001-C07 · `init-db` no pisa una base existente sin `--reset`
- [ ] 001-C08 · Toda conexión abre la base igual
- [ ] 001-C09 · Ámbito y referencias obligatorias
- [ ] 001-C10 · Enumerados, rangos, unicidades y coherencia
- [ ] 001-C11 · Solo inserción y CanonCards inmutables
- [ ] 001-C12 · El índice FTS5 sigue a las CanonCards, sin acentos
- [ ] 001-C13 · Una unidad de trabajo es todo o nada
- [ ] 001-C14 · `check-env` informa de cada comprobación
- [ ] 001-I1 · Ninguna salida reproduce el valor de un ajuste secreto
- [ ] 001-C15 · `serve` no arranca con config, ajustes o base inválidos
- [ ] 001-C16 · `serve` escucha en `STORY_MAKER_BASE_URL`, en un solo proceso
- [ ] 001-I2 · `init-db`, `check-env` y `serve` solo crean o cambian ficheros dentro del directorio de datos
- [ ] 001-C17 · Salud, esquema OpenAPI y errores de la API
- [ ] 001-C18 · La SPA compilada se sirve en el mismo origen sin tapar la API
- [ ] 001-C19 · El doble nulo captura lo emitido, sin red
- [ ] 001-C20 · Niveles y excepciones de los spans
- [ ] 001-C21 · Prompts, comprobación y vaciado con el doble nulo
- [ ] 001-I3 · Ni el doble nulo ni las órdenes de esta spec abren una conexión fuera de la máquina
- [ ] 001-C22 · Primera generación de los tipos del frontend (D, al final)
- [ ] 001-C23 · Un clon limpio arranca siguiendo el README (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 002 — autenticacion

- [x] Spec `specs/backend/002-autenticacion.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 002-C01 · Registro válido
- [ ] 002-C02 · El email se guarda normalizado
- [ ] 002-C03 · Un email ya registrado no crea otra cuenta
- [ ] 002-C04 · Email sin forma de email
- [ ] 002-C05 · Contraseña en sus límites
- [ ] 002-C06 · Registro con cuerpo incompleto
- [ ] 002-C07 · Acceso válido
- [ ] 002-C08 · Al entrar, el email no distingue mayúsculas
- [ ] 002-C09 · Credenciales incorrectas
- [ ] 002-C10 · Acceso con cuerpo incompleto
- [ ] 002-C11 · Un token válido identifica al cliente
- [ ] 002-C12 · Sin token, o con el token mal presentado, responde 401
- [ ] 002-C13 · Un token manipulado o de otro uso responde 401
- [ ] 002-C14 · La caducidad en su límite
- [ ] 002-C15 · El token se comprueba antes que la propiedad
- [ ] 002-C16 · Lo ajeno responde como inexistente
- [ ] 002-C17 · Un recurso anidado solo existe dentro de su padre
- [ ] 002-C18 · Una entrada global no es de ningún cliente
- [ ] 002-C19 · Un listado solo contiene lo del cliente
- [ ] 002-C20 · Lo ajeno no cambia nada
- [ ] 002-C21 · El propietario de lo creado es el cliente del token
- [ ] 002-I1 · La contraseña nunca queda en claro
- [ ] 002-I2 · Toda ruta de `/api` salvo el registro y el acceso exige un `TokenDeAcceso` válido
- [ ] 002-I3 · Para B, un recurso de A es indistinguible de uno inexistente y no cambia nada
- [ ] 002-I4 · El cliente de una petición sale solo del token

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 003 — puerto-de-agente

- [x] Spec `specs/backend/003-puerto-de-agente.md` approved — integrador 2026-09-24: sin revisión, decisión del usuario
- [x] Plan below approved — integrador 2026-09-24: sin revisión, decisión del usuario

### Steps
- [ ] 003-C28 · El doble recorre el camino del SDK y es determinista
- [ ] 003-I9 · El doble falso es determinista
- [ ] 003-C29 · Una sesión sin guion hace fallar la prueba
- [ ] 003-I6 · Ninguna prueba T llega a un modelo
- [ ] 003-I7 · Solo el puerto de agente usa el Agent SDK
- [ ] 003-C01 · Cada rol abre con su lista blanca y nada más
- [ ] 003-C02 · Unas tools que no cuadran con la lista blanca impiden abrir
- [ ] 003-C03 · La sesión corre aislada en el workspace
- [ ] 003-C04 · Solo el revisor visual declara el browser MCP
- [ ] 003-C05 · Con `claude_login`, la sesión usa el login de la máquina y ninguna clave
- [ ] 003-C06 · Con `anthropic_compatible`, la sesión lleva solo las variables de su endpoint
- [ ] 003-C07 · El schema que recibe la sesión es el derivado del modelo de la tool
- [ ] 003-C08 · Una entrada inválida vuelve al modelo como error y se corrige en la misma sesión
- [ ] 003-C09 · Las entregas quedan en memoria, en orden, y nada se persiste
- [ ] 003-C10 · Una sesión que termina sin entregar no es un error del puerto
- [ ] 003-C11 · Toda llamada a tool pasa antes por la política, y su decisión se aplica
- [ ] 003-C12 · La política recibe como narrativos solo los campos que la tool marca
- [ ] 003-C13 · Si la política falla, la tool no corre
- [ ] 003-I3 · Ninguna tool corre sin una decisión `allow` o `flag` de la política
- [ ] 003-I4 · Las tools entregan, no persisten
- [ ] 003-C14 · Con defectos bloqueantes, el modelo lee los defectos en lugar del acuse
- [ ] 003-C15 · Las comprobaciones corren solo sobre entregas permitidas y válidas, y lo no bloqueante no bloquea
- [ ] 003-C16 · La reserva es la entrada estimada más el crecimiento de los turnos
- [ ] 003-C17 · Se abre hasta llenar el techo exacto; si no cabe, se espera en orden de llegada
- [ ] 003-C18 · La API espera como mucho `api_wait_seconds`; la ejecución, sin límite propio
- [ ] 003-C19 · Una reserva mayor que el techo no espera
- [ ] 003-C20 · La reserva se libera siempre al cerrar
- [ ] 003-I1 · La suma de las reservas abiertas nunca supera `token_ceiling`
- [ ] 003-I2 · Toda reserva se libera exactamente una vez
- [ ] 003-C21 · Agotar los turnos conserva el uso
- [ ] 003-C22 · Pasar de `session_timeout_seconds` interrumpe y desconecta
- [ ] 003-C23 · Un fallo del proveedor es `infrastructure_failure`, no `completed`
- [ ] 003-C24 · Quien abre la sesión puede cortarla
- [ ] 003-C25 · El coste es el uso real por el precio de lista del modelo
- [ ] 003-I5 · El coste de una `SesionDeRol` es su uso × `operation.pricing`, nunca el que declara el SDK
- [ ] 003-C26 · Toda sesión abierta deja su `SesionDeRol`, y solo ellas
- [ ] 003-C27 · Cada sesión y cada llamada a tool dejan su span
- [ ] 003-I8 · Sesiones concurrentes no comparten estado
- [ ] 003-C30 · El login funciona con tools en proceso, hooks y skill (D, al final)
- [ ] 003-C31 · La sesión real no hereda nada del entorno de desarrollo (D, al final)
- [ ] 003-C32 · Los límites reales terminan la sesión sin dejar subprocesos (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 006 — especificacion-tla

- [x] Spec `specs/backend/006-especificacion-tla.md` approved — auditor 2026-09-24: ronda 2; 10 casos (4 A, 4 I, 2 D) e 11 invariantes (6 A, 4 I, 1 U) trazados contra arq §7.6, §8.3–§8.4, §9.1–§9.4, §10.1–§10.3, §11.1–§11.2, §11.5, §16.18, §18, definitions §5, §6, §9, §12.3, verif §2, §3.6, §4.6, §4.10, §5, §6 U30, §8, constraints §5d y 000; las 4 contradicciones de la ronda 1 cerradas en los docs; sin bloqueantes; menores: I9 e I11 citan 011, 012 y 014 donde verif §4.10 y U30 dicen 010, 011, 012, 014 y 019; C10 omite la columna Efecto de verif §8; C7 dice que el push a V2 lo decide el integrador y 000-C18 que el usuario; «Excepción de la 006» debería decir que son términos de definitions §9; la tabla de C9 junta `Gate` y `Publicar` en una fila
- [x] Plan below approved — auditor 2026-09-24: ronda 1; 10 pasos, uno por caso (C1–C10), sin invariantes T, con los nombres de la spec; el orden construye antes de usar (modelo → pasada → cobertura → controles → README → registro → portátil → CI); cierre con el formato de AGENTS.md; sin bloqueantes; menores: ninguno

### Steps
- [ ] C4 — Las transiciones de `Harness.tla` son las de §9.1
- [ ] C1 — `Harness.tla` pasa en el modelo pequeño
- [ ] C5 — Las transiciones de `Regenerations.tla` son las de §10.2
- [ ] C2 — `Regenerations.tla` pasa con dos cambios
- [ ] C3 — Ninguna acción queda sin disparar
- [ ] C6 — Cada config de control da el contraejemplo de su propiedad
- [ ] C9 — El README dice qué transición implementa cada acción
- [ ] C10 — Un contraejemplo real queda registrado con su cambio
- [ ] C8 — En el portátil, el mismo veredicto (D, al final)
- [ ] C7 — La CI decide con las configs de la 006 (D, al final)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
