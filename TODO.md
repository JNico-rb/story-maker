# TODO — planes de implementación

Reglas (detalle en `AGENTS.md`, procesos 2–4 y *Parallel lanes*):

1. Un bloque por spec, en orden numérico, con el formato de `AGENTS.md` proceso 3. Ningún código, tampoco el scaffolding, antes de que su spec y su plan estén aprobados.
2. Las casillas de aprobación las marca `auditor` (gap cero, con acta en la misma línea); las de cierre, `verificador`.
3. Un paso se marca `[x]` solo cuando su caso pasa a verde.
4. Cada carril edita solo los bloques de sus specs; esta cabecera y sus tablas son del integrador (checkout principal, V2).
5. Una spec empieza cuando sus dependencias están cerradas en V2, o en la rama de su propio carril.

## Carriles

| Carril | Specs en orden | Depende de (fuera del carril) | Worktree | Rama | Estado |
|---|---|---|---|---|---|
| 0 — scaffolding (integrador) | 000 | — | checkout principal | `V2` | código escrito antes de su spec: spec a posteriori y verificar lo existente |
| A — núcleo de generación | 001 → 003 → 010 → 011 → 012 → 014 | 004, 009 (B) · 005 (C) · 007 (D) | `../sm-a` | `carril-a` | espera 000 |
| B — plataforma y observabilidad | 009 → 004 → 013 → 015 → 017 | 001, 012, 014 (A) · 002 (C) | `../sm-b` | `carril-b` | espera 000 y 001 |
| C — entrada y política | 005 → 002 → 008 → 018 → 019 | 001, 003, 011, 012 (A) · 004 (B) | `../sm-c` | `carril-c` | espera 000 (luego 005 arranca con lo puro) |
| D — formal y calidad | 006 → 007 → 016 → 020 → 021 | 009, 015 (B) · 012 (A) · 002 (C) | `../sm-d` | `carril-d` | espera 000 (luego 006 y 007 arrancan ya) |
| E — frontend | 022 → 023 → 024 → 025 → 026 → 027 → 028 (`specs/frontend/`) | 002, 008 (C) · 011, 014 (A) · 013 (B) · 018, 019 (C) | `../sm-e` | `carril-e` | specs en redacción (un redactor por spec); espera 000 |

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
| 008 | brief-y-entrevista | backend | C | 003, 004, 005 |
| 009 | story-bible-y-versiones | backend | B | 001 |
| 010 | planificacion | backend | A | 003, 004, 009 |
| 011 | produccion-de-capitulos | backend | A | 005, 010 |
| 012 | gate-de-publicacion | backend | A | 007, 011 |
| 013 | lectura-y-pdf | backend | B | 009 |
| 014 | cambios-del-lector | backend | A | 012 |
| 015 | servidor-mcp | backend | B | 002, 013, 014 |
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
