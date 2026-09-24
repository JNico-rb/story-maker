---
description: Escribe o completa una spec desde docs/ tal como están — sin autorrevisión ni auditoría; el integrador añade el bloque a TODO.md y marca la casilla.
argument-hint: <NNN> [NNN …]
---

# Spec $ARGUMENTS

Solo lo ejecuta el integrador, en el checkout principal (V2): es quien numera las specs, añade los bloques a `TODO.md` y commitea las aprobaciones. Un carril que necesite una spec se lo pide al integrador.

Sin autorrevisión, sin `auditor`, sin rondas y sin revisión del usuario (decisión del usuario, 2026-09-24). Una spec existente no se pule ni se rehace: si está completa, se aprueba tal cual; si le falta algo, se completa **solo lo que el plan necesita**.

1. Busca cada spec de $ARGUMENTS en la tabla de specs de `TODO.md`: nombre, lado, carril y dependencias. Si es nueva, dale el número siguiente y añádela a la tabla.
2. Si falta o está incompleta (le falta alguno de los cinco contenidos de `AGENTS.md` proceso 2): escríbela tú o lanza **un `redactor-specs` por spec**, en paralelo, con NNN, nombre y lado, desde `docs/` tal como están. Las decisiones de diseño que cierre van a `architecture.md` §18.
3. Añade tú el bloque `## NNN — <nombre>` de cada spec a `TODO.md`, en su posición numérica, con el formato de `AGENTS.md` proceso 3: **de uno en uno**. Ningún redactor toca `TODO.md`.
4. Marca tú la casilla: `- [x] Spec … approved — integrador YYYY-MM-DD: sin revisión, decisión del usuario`.
5. Commit por cada spec aprobada: `NNN: spec aprobada` (o uno solo con spec y plan: `NNN: spec y plan aprobados`).

Hecho cuando la casilla de spec de cada bloque está `[x]` con su acta del integrador.

Informe (≤5 líneas): rutas, casos e invariantes, decisiones añadidas a §18.
