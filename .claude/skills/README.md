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
| `grill-me` | propia del proyecto (el fichero no declara otro origen) | — | — |
| `verification` | propia del proyecto | — | — |
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

### `sqlalchemy-sqlite` — decidida, no escrita

No existe skill oficial de SQLite ni de SQLAlchemy para *escribir* persistencia. Se acordó
el 2026-09-21 que habrá una skill propia, y **se decidió no escribirla todavía**.

**Por qué no ahora.** Ninguna spec fija todavía el esquema. Una skill que dicte cómo persistir,
escrita antes de que exista un spec de persistencia, fija decisiones que nadie ha tomado: es
la deriva que `AGENTS.md` prohíbe, solo que una capa más arriba. Se escribe cuando la spec 001
fije el esquema, no antes.

**Qué será, cuando toque.** Una skill *del proyecto*, no de la librería — deliberadamente
**no** una gemela de `fastapi`. Lo genérico de SQLAlchemy (sesiones, N+1, `select()` 2.0,
Alembic) ya lo verifica `sqlalchemy-code-review`; repetirlo en modo imperativo sería duplicar.
Cubrirá lo que ninguna skill genérica puede saber, que sale de `docs/architecture.md` §9 y
§15.6:

- **Concurrencia.** El worker, una tarea asyncio en el mismo proceso que la API, escribe un
  punto de control por capítulo mientras la API lee el estado de la ejecución. En SQLite por
  defecto eso es `database is locked`: WAL, `busy_timeout` y un único escritor son decisiones,
  no detalles.
- **Async es medio espejismo.** SQLAlchemy async sobre `aiosqlite` funciona, pero SQLite no
  tiene concurrencia de escritura real. Por eso `architecture.md` §15.1 fija SQLAlchemy 2
  síncrono; la skill lo aplica, no lo decide.
- **Afinidad de tipos.** SQLite no tiene JSON, UUID ni `datetime` con zona nativos. Las
  columnas JSON de la copia por versión (consecuencias, beats, propuesta de un cambio)
  condicionan cómo se consulta.
- **`PRAGMA foreign_keys=ON`** no está activo por defecto: hay que fijarlo por conexión o las
  claves ajenas son decorativas.
- **Los nombres los manda `definitions.md`.** El esquema no puede inventar sinónimos de
  `StoryBible`, `UsoDeHecho`, `Outline` ni del resto de términos definidos.

`feature-sliced-design` es la skill oficial de Feature-Sliced Design v2.1: enseña la jerarquía
de capas (`app`, `pages`, `widgets`, `features`, `entities`, `shared`), las reglas de importación
y dónde colocar cada pieza. Su sesgo declarado es *pages-first*: empezar con `app/`, `pages/` y
`shared/`, y abrir `features/` o `entities/` solo cuando una responsabilidad compartida y estable
lo justifique; `widgets/` está desaconsejada. Ese sesgo encaja con el frontend de
`docs/architecture.md` §14.8, que adopta FSD v2.1 *pages-first* como decisión cerrada en §18; la
skill aplica esa decisión, no la toma.

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
| `sqlite-vec` (`existential-birds/beagle`) | Ya no existe en el repo de origen. El proyecto sí usa `sqlite-vec` en su RAG híbrido de una colección (`docs/architecture.md` §6.3, spec 016), pero no hay skill publicada que vendorizar; lo que haga falta saber de él entra en `sqlalchemy-sqlite` cuando se escriba. |

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
