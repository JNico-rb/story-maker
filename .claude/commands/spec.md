---
description: Escribe o cambia una spec — redactor con autorevisión, auditoría a gap cero y bloque en TODO.md.
argument-hint: <NNN>
---

# Spec $ARGUMENTS

1. Busca la spec $ARGUMENTS en la tabla de specs de `TODO.md`: nombre, lado, carril y dependencias. Si es nueva, solo el integrador en V2 le da el número siguiente y la añade a la tabla.
2. Lanza el subagente `redactor-specs` con NNN, nombre y lado. Hecho cuando devuelve la ruta de la spec y su informe.
3. **Preguntas para el usuario:** si alguna bloquea la spec, házselas todas en un solo mensaje y espera la respuesta. **Decisiones para §18:** en V2, añádelas a `architecture.md` §18 (`AGENTS.md` proceso 1); en un carril, van al aviso para el integrador.
4. Comprueba que el bloque `## $ARGUMENTS` existe en `TODO.md` con todas las casillas sin marcar.
5. Lanza el subagente `auditor` con $ARGUMENTS, `spec` y ronda 1. HUECOS → `redactor-specs` con los huecos → `auditor` en la ronda siguiente. ESCALAR (ronda 3) → para y pasa al usuario los huecos y la decisión que falta.
6. Commit: `$ARGUMENTS: spec`.

Hecho cuando la casilla de spec del bloque está `[x]` con el acta del auditor, o el caso está escalado.

Informe (≤10 líneas): ruta, casos e invariantes, rondas del auditor, decisiones añadidas a §18, preguntas pendientes del usuario.
