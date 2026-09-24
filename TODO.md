# TODO — planes de implementación

Reglas (detalle en `AGENTS.md`, procesos 2–4 y *Parallel lanes*):

1. Un bloque por spec, en orden numérico, con el formato de `AGENTS.md` proceso 3. Ningún código, tampoco el scaffolding, antes de que su spec y su plan estén aprobados.
2. Las casillas de aprobación las marca `auditor` (gap cero, con acta en la misma línea); las de cierre, `verificador`.
3. Un paso se marca `[x]` solo cuando su caso pasa a verde.
4. Cada carril edita solo los bloques de sus specs; esta cabecera y sus tablas son del integrador (checkout principal, V2).
5. Una spec empieza cuando sus dependencias están cerradas en V2, o en la rama de su propio carril.

## Estado (handoff 2026-09-24, corte por cuota)

- **Etapa 1 cortada** por el límite de gasto mensual de la organización (HTTP 429, se reinicia a las 13:00 de Madrid). No queda ningún subagente en marcha.
- **Specs commiteadas como borrador, sin aprobar:** 000 (ronda 2 hecha, falta auditarla), 001, 002, 003, 006, 007, 008, 009, 010, 011, 012, 014, 015, 016, 017, 018, 019. Completas y con informe: 000, 002, 006, 007, 015. Las demás las cortó la cuota: pueden estar incompletas y sin sus decisiones en §18, así que el auditor lo dirá. **Sin redactar:** 004, 005, 013, 020, 021.
- **Borradores de plan** (no se commitean): `specs/.drafts/plan-000.md` y `plan-006.md`. **Bloques** en este fichero: 000 y 002.
- **Docs cambiados** (en el commit de este checkpoint, sin auditar):
  - §18 de architecture.md: decisiones de 000, 002, 006, 007 y 015.
  - architecture.md: §14.4 (`confirm_change(change_request_id, code)`), §15.3, §15.5, §15.7 y §15.8.
  - verification.md: §9.6, U28 y U29.
  - AGENTS.md proceso 2: excepción de 000.
  - backend/AGENTS.md: el audit log pasa a 008.
  - Dependencias nuevas en las tablas: 008 y 009 ← 002 · 011 ← 002 y 006 · 015 ← 008.
- **Antes de auditar 000 (ronda 2):**
  - ampliar §9.6: `deny` de `Bash(git push -f*)`, `allow` de `Bash(git branch*)` y `additionalDirectories` de los worktrees, que ya están en `.claude/settings.json`;
  - decidir si las pruebas de los hooks (`node --test`) entran en el job `frontend` de §4.6;
  - una ronda de redactor sobre 000-C11 y 000-C18.
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
  1. Cerrar §9.6 y la ronda de 000.
  2. `auditor` sobre 000.
  3. De dos en dos: redactar 004, 005, 013, 020 y 021, y auditar el resto. Por cada aprobación, su bloque, su plan y sus commits.
  4. Frontend 022–028 cuando estén aprobadas 002, 008, 011, 013, 014, 018 y 019.
  5. Parar en la tabla final de la etapa 2.

## Carriles

| Carril | Specs en orden | Depende de (fuera del carril) | Worktree | Rama | Estado |
|---|---|---|---|---|---|
| 0 — scaffolding (integrador) | 000 | — | checkout principal | `V2` | código escrito antes de su spec: spec a posteriori y verificar lo existente |
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

- [ ] Spec `specs/000-scaffolding.md` approved
- [ ] Plan below approved

### Steps

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true

## 002 — autenticacion

- [ ] Spec `specs/backend/002-autenticacion.md` approved
- [ ] Plan below approved

### Steps

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
