---
description: Escribe un plan rápido de una spec aprobada en su bloque de TODO.md — un paso por caso — y lo marca el integrador, sin revisión.
argument-hint: <NNN>
---

# Plan de la spec $ARGUMENTS

Solo lo ejecuta el integrador, en el checkout principal (V2). Sin autorrevisión, sin `auditor` y sin revisión del usuario (decisión del usuario, 2026-09-24).

1. En el bloque `## $ARGUMENTS` de `TODO.md`, la casilla de spec está `[x]`. Si no, `/spec $ARGUMENTS` primero.
2. En `### Steps` (o pegando el borrador de `specs/.drafts/plan-$ARGUMENTS.md`, si existe): un paso por caso y uno por invariante de clase T, con el nombre que les da la spec, en orden de implementación (lo que otros usan, antes). Los casos D, al final y con `(D, al final)`: no se ejecutan hasta que el backend esté completo. `### Closing` con sus tres casillas sin marcar.
3. **Cobertura:** cada caso y cada invariante T de la spec aparece en exactamente un paso.
4. Marca tú la casilla: `- [x] Plan below approved — integrador YYYY-MM-DD: sin revisión, decisión del usuario`.
5. Commit: `$ARGUMENTS: plan aprobado`.

Frontend (022–028): mismo plan rápido, un paso por caso; el carril E no empieza un paso hasta que las specs de backend de las que depende estén cerradas en V2. Revisión solo como excepción (error claro que impide que funcione o requisito de `project-constraints.md` sin cubrir), una sola corrección.

Hecho cuando la casilla de plan está `[x]` con su acta del integrador.

Informe (≤3 líneas): pasos y orden.
