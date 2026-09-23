# Skills del proyecto

Varias de estas skills son copias de skills publicadas por otros proyectos. Se vendorizan
aquí para que cualquiera que clone el repositorio las tenga; actualízalas volviendo a copiar
desde el origen.

| Skill | Origen | Licencia | Commit copiado |
|---|---|---|---|
| `fastapi` | `fastapi/fastapi`, ruta `fastapi/.agents/skills/fastapi` | MIT | `50113da` |
| `react-expert` | `reactjs/react.dev`, ruta `.claude/skills/react-expert` | MIT | `b011783` |
| `sqlalchemy-code-review` | `existential-birds/beagle`, ruta `plugins/beagle-python/skills/sqlalchemy-code-review` | Apache-2.0 | `d1a7489` |
| `review-verification-protocol` | `existential-birds/beagle`, ruta `plugins/beagle-python/skills/review-verification-protocol` | Apache-2.0 | `d1a7489` |
| `feature-sliced-design` | `feature-sliced/skills`, ruta `feature-sliced-design` | MIT | `fd71da4` |
| `wayfinder` | `mattpocock/skills`, ruta `skills/engineering/wayfinder` | MIT | `959a8e9` — **adaptada**, ver abajo |
| `writing-for-agents` | `mattpocock/skills`, ruta `skills/productivity/writing-for-agents` | MIT | `959a8e9` (plugin `mattpocock-skills` 1.2.3) |
| `tdd` | `mattpocock/skills`, ruta `skills/engineering/tdd` | MIT | plugin `mattpocock-skills` 1.2.3; la usan los chats de código (`.claude/commands/codigo.md`) |
| `sqlalchemy-sqlite` | propia del proyecto | — | **no escrita**: bloqueada a propósito, ver abajo |

## Notas

`react-expert` no es una skill de buenas prácticas de React: es una skill de investigación
que consulta el código fuente y los tests de React en lugar de fiarse del conocimiento del
modelo. Clona `react/react` en `.claude/react` y lanza seis agentes en paralelo. Dos de
ellos usan la CLI `gh`, que no está instalada en este entorno: esos dos fallarán y los otros
cuatro seguirán funcionando.

`.claude/react` debe quedar fuera del control de versiones.

`sqlalchemy-code-review` revisa código ya escrito (ciclo de vida de la sesión, N+1, sintaxis
2.0 `select()`, migraciones reversibles de Alembic). No enseña a escribirlo. Sus puertas
dependen de `review-verification-protocol`, que se copia con ella por la referencia cruzada
`../review-verification-protocol/SKILL.md`; sin esa hermana el enlace queda roto. Ambas son
solo Markdown: no traen scripts ni ejecutan nada.

`wayfinder`, a diferencia del resto, **no es una copia literal**: está adaptada a este repo.
Llama a `grill-me` en vez de a `grilling`, fija el tracker en markdown local (`.scratch/`,
versionado) y añade una sección *Repo overrides* que remite a `workflow/` para el glosario, las
decisiones y el paso a specs. Volver a copiarla desde el origen borra esas adaptaciones: hay que
reaplicarlas. `research`, `prototype` y `domain-modeling` no se copian porque no se han usado:
los transcripts de Claude Code de este repo no registran ninguna invocación a 2026-09-23. Solo
las nombra `wayfinder`, como `mattpocock-skills:<nombre>`, para resolver sus tickets; ejecutar
`wayfinder` exige tener instalado el plugin `mattpocock-skills`.

`writing-for-agents` es copia literal: `CLAUDE.md` obliga a cargarla antes de editar
`CLAUDE.md`, `workflow/` o `.claude/`, y vendorizada esa regla funciona sin el plugin. Se copian
`SKILL.md` y `SKILL-MECHANICS.md` más el `LICENSE` del repositorio de origen, que la MIT exige
acompañar a la copia; como en `wayfinder`, se omite `agents/openai.yaml`, metadatos de interfaz
para Codex que Claude Code no lee. Es solo Markdown.

### `sqlalchemy-sqlite` — decidida, no escrita

No existe skill oficial de SQLite ni de SQLAlchemy para *escribir* persistencia. Se acordó
el 2026-09-21 que habrá una skill propia, y **se decidió no escribirla todavía**.

**Por qué no ahora.** El esquema ya está redactado en `specs/001-base/design.md`, pero sin
aprobar, y `backend/` aún no tiene código. Una skill que dicte cómo persistir, escrita antes de
que se apruebe ese esquema, fija decisiones que nadie ha aprobado: es la deriva que `CLAUDE.md`
prohíbe, solo que una capa más arriba. Se escribe cuando se apruebe ese esquema, no antes.

**Qué será, cuando toque.** Una skill *del proyecto*, no de la librería — deliberadamente
**no** una gemela de `fastapi`. Lo genérico de SQLAlchemy (sesiones, N+1, `select()` 2.0,
Alembic) ya lo verifica `sqlalchemy-code-review`; repetirlo en modo imperativo sería duplicar.
Cubrirá lo que ninguna skill genérica puede saber, que sale de `docs/architecture.md` §9.1 y
§14.4:

- **Concurrencia.** El proceso de una ejecución escribe un punto de control por capítulo
  mientras la API lee su estado. En SQLite por defecto eso es `database is locked`:
  WAL, `busy_timeout` y un único escritor por novela son decisiones, no detalles.
- **Async es medio espejismo.** SQLAlchemy async sobre `aiosqlite` funciona, pero SQLite no
  tiene concurrencia de escritura real. La arquitectura ya fija SQLAlchemy síncrono dentro
  del worker (§14.4); la skill lo aplica, no lo decide.
- **Afinidad de tipos.** SQLite no tiene JSON, UUID ni `datetime` con zona nativos. Un
  `EstadoDelMundo` versionado por capítulo acaba casi seguro en columna JSON, y eso condiciona
  cómo se consulta.
- **`PRAGMA foreign_keys=ON`** no está activo por defecto: hay que fijarlo por conexión o las
  claves ajenas son decorativas.
- **Append-only de verdad.** El audit log, las versiones publicadas y el índice solo admiten
  inserciones (`architecture.md` §6.6, §9.3, §11.4): un trigger que rechace `UPDATE` y
  `DELETE` lo hace comprobable.
- **Los nombres los manda `definitions.md`.** El esquema usa la proyección de su §12 y no
  inventa sinónimos de `EstadoDelMundo`, `Hecho`, `Version` ni del resto de términos.

`feature-sliced-design` es la skill oficial de Feature-Sliced Design v2.1: enseña la jerarquía
de capas (`app`, `pages`, `widgets`, `features`, `entities`, `shared`), las reglas de importación
y dónde colocar cada pieza. Su sesgo declarado es *pages-first*: empezar con `app/`, `pages/` y
`shared/`, y abrir `features/` o `entities/` solo cuando una responsabilidad compartida y estable
lo justifique; `widgets/` está desaconsejada. Ese sesgo encaja con un frontend organizado por
página —acceso, novelas, entrevista, progreso, lectura, cambio—, pero la skill enseña FSD en
general: la forma que adopta aquí la fija `architecture.md` §14.2 (`app`, `pages` y `shared`;
`entities` y `features` cuando aparezca reutilización real; `widgets` descartada).

Es solo Markdown más un JSON: no trae scripts ni ejecuta nada. Se copia entera, incluida
`evals/`, para que reactualizarla sea un `cp` desde el origen; esas evals no se pueden correr
aquí porque dependen de la CLI `agent-skills-eval`, que no está instalada. El repositorio de
origen no incluye fichero `LICENSE`: declara MIT únicamente en su `README.md`.

`verification` y `review-verification-protocol` comparten la palabra y nada más: la primera
**escribe** el plan de verificación (tablas `V<n>` / `P<n>` / `U<n>`, una letra T/A/I/D/U por
elemento); la segunda son puertas anti-falso-positivo que se aplican **al revisar** código ya
escrito, y la carga `sqlalchemy-code-review`. No se fusionan: disparan en momentos distintos
del ciclo y no comparten ningún concepto.

`verification/references/taxonomia.md` lleva, además de las 18 técnicas y el marco T/A/I/D/U,
la fuente canónica de cada una y la sección de `docs/verification.md` que la razona para este
proyecto —incluidas las cuatro descartadas con motivo escrito—. Las URLs se verificaron una a
una el 2026-09-21. La fuente de verdad sobre *qué se hace aquí* sigue siendo el documento: si
divergen, la skill está desactualizada.

## Skills descartadas

| Candidata | Motivo del descarte |
|---|---|
| `SecureSkills-io/sqlite-skill` | **Rechazada por seguridad.** Ver abajo. |
| `sqlite-vec` (`existential-birds/beagle`) | Ya no existe en el repo de origen. El proyecto sí usa `sqlite-vec` (`docs/architecture.md` §6.12): el descarte se sostiene solo por lo primero. |

### Por qué se rechaza `SecureSkills-io/sqlite-skill`

Auditada leyendo su fuente el 2026-09-21 (repo `master`, commit único de 2026-02-02):

1. **Inyección SQL por interpolación de identificadores**, en cuatro sitios de `sqlite.js`.
   Los *valores* del `INSERT` sí van parametrizados con `?`, pero los nombres de tabla y de
   columna se concatenan en crudo: `PRAGMA table_info(${table})`, `name='${table}'`,
   `SELECT * FROM ${t}`, `INSERT INTO ${table} (${columns})`.
2. **El caso `import` es el grave:** los nombres de tabla y columna salen del propio fichero
   JSON importado. Un `backup.json` de origen ajeno ejecuta SQL arbitrario.
3. **En SQLite eso no se queda en la base de datos.** La CLI `sqlite3` trae `readfile()` y
   `writefile()`, y admite `ATTACH DATABASE`: SQL arbitrario equivale a lectura y escritura
   arbitraria de ficheros con los permisos del usuario. Leer `.env` o escribir en un fichero
   de arranque entra dentro de lo alcanzable.
4. **Su `AUDIT_REPORT.md` es una autoauditoría que miente sobre su propio código.** Se firma
   «Auditor: SecureSkills (Self-Audit)», se pone «8.7/10 — Trust Level: HIGH — APPROVED», y
   afirma cosas que no están en el fichero: «Line 45-78: proper credential handling with 600
   permissions» (esas líneas son el manejador de stdout de `executeQuery`; no hay manejo de
   credenciales en ninguna parte), «Line 80-115: clean API request wrapper» (no hay código de
   red), «file permissions checked and set correctly» (nunca se llama a `chmod`). Parece una
   plantilla de otra skill pegada sin revisar. Un documento de confianza con datos falsos
   sobre su propio código es peor señal que la ausencia de documento.
5. **Ni siquiera cargaría aquí:** su `SKILL.md` no tiene *frontmatter* YAML, así que no es una
   skill válida de Claude Code. Está escrita para otro runtime («OpenClaw/Clawd»), en
   JavaScript, con rutas `/root/...`, contra un proyecto que persiste con SQLAlchemy 2 en
   Python.
6. **Procedencia nula:** 1 commit, 1 estrella, 0 forks, sin tocar desde su publicación, de una
   organización cuyo nombre es en sí mismo la afirmación de confianza.

No se detectó inyección de *prompt* en su `SKILL.md`: el riesgo es el código y el documento
de confianza falso, no texto oculto dirigido al agente.
