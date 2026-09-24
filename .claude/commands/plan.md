---
description: Escribe el plan de una spec aprobada en su bloque de TODO.md y lo audita hasta que no quede ningún hueco bloqueante.
argument-hint: <NNN>
---

# Plan de la spec $ARGUMENTS

Solo lo ejecuta el integrador, en el checkout principal (V2).

1. En el bloque `## $ARGUMENTS` de `TODO.md`, la casilla de spec está `[x]`. Si no, `/spec $ARGUMENTS` primero.
2. Lee la spec y `AGENTS.md` proceso 3. Escribe en el bloque `### Steps` (o pega el borrador que dejó el redactor): un paso por caso y uno por invariante de clase T, cada uno con el nombre del caso o del invariante tal como lo da la spec, en orden de implementación (lo que otros pasos usan, antes; los casos D, al final). Deja `### Closing` con sus tres casillas sin marcar.
3. **Cobertura:** cada caso y cada invariante T de la spec aparece en exactamente un paso. Hecho cuando la comprobación no encuentra faltas ni repetidos.
4. Lanza el subagente `auditor` con $ARGUMENTS, `plan` y ronda 1. HUECOS bloqueantes → corrige y repite (≤2 rondas). ESCALAR → para y pásalo al usuario.
5. Commit: `$ARGUMENTS: plan aprobado`.

Hecho cuando la casilla de plan está `[x]` con el acta del auditor, o el caso está escalado.

Informe (≤10 líneas): pasos, orden elegido y por qué, rondas del auditor.
