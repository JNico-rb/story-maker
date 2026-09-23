# 009 — LEA · Validador formal de la historia

- [x] Spec approved   <- only the user marks this

## Objetivo

Que la cronología de cada versión se verifique con Lean 4 contra T1–T6, con comprobadores demostrados correctos y completos para toda cronología, sin que ningún dato personal salga en claro.

## Alcance

Cubre:

- la biblioteca `lean/`: los tipos de la cronología, T1–T6 como predicados decidibles y un comprobador por invariante con su demostración general de corrección y de completitud;
- la construcción con `--wfail` y la auditoría de axiomas, con sus ficheros positivos y negativos, en CI;
- el generador del `FicheroDeCronologia` desde una lista de eventos, con las dos cronologías y su seudonimización;
- el resultado en JSON, su traducción de vuelta a capítulos y nombres, el fichero guardado y el score `cronologia-lean`;
- el `VerificadorFormal`, con su adaptador local y su adaptador remoto en GitHub Actions, y la seguridad del workflow.

Columnas de `chronology_files`: [001 design.md](../001-base/design.md) §12; interfaz de GitHub Actions: §11.

Depende de 001 y de 004.

**Fuera de alcance:**

- Dónde se invoca y qué se hace con su resultado: al congelar el outline, con la replanificación si falla, es de 010; en el gate, sin publicar si falla y con el testigo de vuelta al editor, es de 014.
- Pasar la ejecución a `interrupted` cuando el verificador no está disponible, que es de 007.
- La demostración del workflow remoto desde el portátil, con su tiempo de respuesta, que es de 001 (`architecture.md` §15.3).
- El caso real que solo detecta Lean, que es de 017.
- Las reglas C4, C5 y C7 del brief (005) y los avisos de cronología del linter en vivo (015): no duplican a Lean, y no son de esta spec.

## Requisitos

Todos son **Obligatorio**. `max_verifier_seconds` está sin calibrar (`architecture.md` §15.2): las pruebas fijan el suyo.

### Biblioteca

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEA-1 | La biblioteca `lean/` es un proyecto Lake que define los tipos de la cronología: eventos con identificador, momento —año, mes, día, hora y minuto—, capítulo y beat que lo narran, personajes presentes, lugar, tipo y personaje excluido, analepsis, evento que narra, edades declaradas y consecuencias de las que depende; las fechas de nacimiento de los personajes; y la fecha del novum | Obligatorio | A |
| RF-LEA-2 | T1–T6 → son predicados decidibles tal como los enuncia `domain-knowledge.md` §5.3, con las reglas de §5.2: un nacimiento es a las 00:00 de su fecha, y un cumpleaños del 29 de febrero cae el 1 de marzo en los años no bisiestos. T1 usa el orden de capítulo y beat y deja fuera las analepsis. T2 y T5 solo alcanzan a los personajes con fecha de nacimiento | Obligatorio | A |
| RF-LEA-3 | Cada invariante tiene su comprobador, con una demostración general de corrección y otra de completitud: para toda cronología, el comprobador devuelve `true` si y solo si el invariante se cumple | Obligatorio | A |
| RF-LEA-4 | Un comprobador recibe una cronología que viola su invariante → devuelve en JSON el invariante violado y su primer testigo, en el orden de la lista de eventos: los ids de sus eventos y de sus personajes | Obligatorio | T |
| RF-LEA-5 | Se construye la biblioteca → con `--wfail` y con una auditoría de los axiomas de cada teorema. Una demostración cerrada con `sorry`, o que depende de un axioma declarado en el proyecto, hace fallar la construcción. Se prueba sembrando un `sorry` | Obligatorio | T |
| RF-LEA-6 | Ficheros de prueba → los que cumplen los seis invariantes compilan; por cada uno de T1–T6, uno que lo viola falla con ese invariante y su primer testigo. Fronteras: un evento en el mismo momento que el excluyente no viola T4; uno en el momento exacto del nacimiento no viola T5; uno en la fecha exacta del novum no viola T6; y una edad declarada que se cumple el 1 de marzo por un nacimiento del 29 de febrero no viola T2 | Obligatorio | T |
| RF-LEA-7 | Cada cambio en CI → construye la biblioteca con `--wfail` y la auditoría de axiomas, y compila los ficheros positivos y los negativos de RF-LEA-6; si alguno no da lo esperado, la integración falla | Obligatorio | T |

### Generador y seudonimización

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEA-8 | El generador recibe una lista de eventos, las fechas de nacimiento de sus personajes y la fecha del novum → produce un `FicheroDeCronologia` que declara esos datos y un teorema por invariante, cerrado evaluando su comprobador. El fichero compila si y solo si se cumplen los seis. El generador no lee la tabla de cronología | Obligatorio | T |
| RF-LEA-9 | Cronologías → la planificada son los eventos de origen brief más los planificados del outline propuesto —los de sus beats y sus antecedentes—, tomados de la propuesta antes de guardarla; la registrada son, de la tabla de cronología de la versión, los de origen brief, los planificados sin beat y los registrados. Las dos llevan las fechas de nacimiento y la fecha del novum. Un beat dentro de un marco no aporta ningún evento | Obligatorio | T |
| RF-LEA-10 | Una analepsis narra un evento de trasfondo → la cronología lo cuenta una sola vez: el fichero lleva el evento narrado, no una copia. Un evento de trasfondo con su beat analéptico no da una violación de T3 por duplicado | Obligatorio | T |
| RF-LEA-11 | Un personaje sin fecha de nacimiento → queda fuera de T2 y T5, y dentro de T1, T3, T4 y T6: una edad declarada suya no viola T2, y un evento suyo anterior a cualquier fecha no viola T5 | Obligatorio | T |
| RF-LEA-12 | Se genera un fichero → va seudonimizado: los identificadores son los ids de las filas de SQLite, que una versión conserva al copiarse, y los de la propuesta para los eventos de un outline que aún no se guardó; no lleva ningún nombre, enunciado ni otro texto de la story bible; y sus fechas van desplazadas un múltiplo de 400 años distinto de cero, que se guarda con el fichero | Obligatorio | T |
| RF-LEA-13 | Para toda cronología generada, con fechas del 29 de febrero incluidas → la seudonimización es inyectiva, conserva el orden de todo par de momentos y la edad de todo personaje en todo momento; cada comprobador da el mismo resultado sobre el fichero desplazado que sin desplazar; y el testigo se traduce de vuelta a sus eventos y personajes | Obligatorio | T |

### Resultado

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEA-14 | Una verificación falla → su JSON se traduce de vuelta: el invariante violado y los eventos del testigo, con sus capítulos, sus beats, los nombres canónicos de sus personajes y lugares y sus fechas reales, en un texto que sirve de realimentación. Una prueba de contrato fija el JSON que emite la biblioteca frente al traductor | Obligatorio | T |
| RF-LEA-15 | Termina una verificación → queda su `FicheroDeCronologia`, en una tabla que solo admite inserciones: la ejecución, la versión, la cronología —planificada o registrada—, el desplazamiento, el contenido, el modo del verificador, si pasó y el resultado con su testigo | Obligatorio | T |
| RF-LEA-16 | El `CatalogoDeCriterios` → contiene `cronologia-lean` con sus seis criterios, `t1-orden`, `t2-edad`, `t3-dos-lugares`, `t4-excluyente`, `t5-nacimiento` y `t6-novum`, bloqueantes, con acción corregir en el gate y replanificación al congelar el outline. Cada verificación da en cada criterio 1 si su invariante se cumple y 0 si no, y en el agregado 1 solo si se cumplen los seis, con el testigo traducido como comentario. Los envía a Langfuse quien la invoca (010 y 014), con 004 | Obligatorio | T |

### Verificador

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEA-17 | El `VerificadorFormal` tiene dos adaptadores, `local` y `github` → sobre el mismo fichero dan el mismo resultado: los ficheros positivos y negativos de RF-LEA-6 pasan por los dos | Obligatorio | T |
| RF-LEA-18 | El adaptador → lo elige el ajuste del servidor `FORMAL_VERIFIER`, no la config: cambiar la config no lo cambia | Obligatorio | T |
| RF-LEA-19 | Adaptador `local` → compila el fichero contra la biblioteca con `lake build` en su área del directorio de datos, en Linux y en CI, y devuelve el JSON del comprobador | Obligatorio | T |
| RF-LEA-20 | Adaptador `github` → dispara el workflow con el fichero como input, comprimido en gzip y codificado en base64, pidiendo el id de la ejecución del workflow y con la versión de la API de GitHub fijada; sondea esa ejecución hasta que concluye y descarga el artefacto con el JSON. Una prueba de integración lo recorre contra un workflow de prueba | Obligatorio | T |
| RF-LEA-21 | El verificador no concluye en `max_verifier_seconds`, o no es alcanzable —un error de red, una respuesta 5xx o el token rechazado— → devuelve «no disponible», nunca un invariante violado, y no guarda ningún resultado | Obligatorio | T |
| RF-LEA-22 | El workflow de Lean → compila con `--wfail` y audita los axiomas; su job solo tiene el permiso `contents: read`; los inputs le llegan al script por variables de entorno, nunca interpolados en la orden; y el README explica el `GITHUB_TOKEN` de grano fino que lo dispara, limitado al repositorio: Actions de lectura y escritura, y Metadata de lectura | Obligatorio | I |
| RF-LEA-23 | Al cerrar 009 → la cabecera de `architecture.md` §10.5 lleva el explainer de la verificación formal de la historia con Lean 4 | Obligatorio | I |

## Restricciones

| # | Restricción | Origen | Clase |
|---|---|---|---|
| R1 | Ningún validador del harness comprueba T1–T6 fuera de Lean: la aportación del validador formal tiene que ser medible | `architecture.md` §10.5 | I |

## Docs de referencia

- `architecture.md` §4.3, §5.2 (`cronologia-lean` sobre la cronología planificada), §10.2 (`cronologia-lean`), §10.3 (sus criterios), §10.5 y §16 («Invariantes temporales», «Invariantes de Lean priorizados», «Dónde corre Lean», «Seudonimización del fichero Lean»).
- [ADR 0004](../../docs/adr/0004-lean-en-github-actions.md).
- `definitions.md` §2 (`Personaje`, `Evento`, `Cronologia`), §9, §11 (`FORMAL_VERIFIER`, `GITHUB_REPOSITORY`, `LEAN_WORKFLOW`, `GITHUB_TOKEN`, `max_verifier_seconds`) y §12.
- `domain-knowledge.md` §4.5 (lo que pasa en un marco no entra en la cronología), §5.2 y §5.3.
- `verification.md` §3.4, §3.6 (seudonimización), §3.8 (JSON del resultado), §3.12, §4.7, §5 («Validador formal de la historia», «Verificador remoto de Lean») y §6 (riesgos 10 y 14).
