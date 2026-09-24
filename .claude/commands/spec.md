---
description: Escribe o cambia una spec — un redactor por spec, autorevisión, bloque en TODO.md por el integrador y casillas que marca el integrador, sin auditoría.
argument-hint: <NNN> [NNN …]
---

# Spec $ARGUMENTS

Solo lo ejecuta el integrador, en el checkout principal (V2): es quien numera las specs, añade los bloques a `TODO.md` y commitea las aprobaciones. Un carril que necesite una spec se lo pide al integrador.

1. Busca cada spec de $ARGUMENTS en la tabla de specs de `TODO.md`: nombre, lado, carril y dependencias. Si es nueva, dale el número siguiente y añádela a la tabla.
2. Lanza **un subagente `redactor-specs` por spec**, todos en paralelo, con NNN, nombre y lado. Hecho cuando cada uno devuelve la ruta de su spec y su informe.
3. **Preguntas para el usuario:** si alguna bloquea una spec, házselas todas en un solo mensaje y espera la respuesta. **Decisiones para §18:** añádelas a `architecture.md` §18 (`AGENTS.md` proceso 1).
4. Añade tú el bloque `## NNN — <nombre>` de cada spec a `TODO.md`, en su posición numérica, con el formato de `AGENTS.md` proceso 3 y todas las casillas sin marcar: **de uno en uno**. Ningún redactor toca `TODO.md`.
5. Revisa tú que la spec tiene sus cinco contenidos y marca la casilla: `- [x] Spec … approved — integrador YYYY-MM-DD: sin auditoría, decisión del usuario`. No se lanza el `auditor`.
6. Commit por cada spec aprobada: `NNN: spec aprobada`.

Hecho cuando la casilla de spec de cada bloque está `[x]` con su acta del integrador.

Informe (≤10 líneas): rutas, casos e invariantes, decisiones añadidas a §18, preguntas pendientes del usuario.
