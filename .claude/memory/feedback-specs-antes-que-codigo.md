---
name: feedback-specs-antes-que-codigo
description: "Ningún código —tampoco el scaffolding, la configuración de herramientas ni scripts de apoyo— antes de que su spec (y su plan) existan y estén aprobados; si se escapa algo, no se borra."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-24T07:07:28.695Z
---

El orden docs → specs → plan → tests → código vale también para el scaffolding: pyproject, esqueleto de paquetes, app placeholder del frontend, CI, proyectos de Lean o TLA+ y scripts de hooks. Pedir «prepara el scaffolding antes de programar el backend» no autoriza a escribirlo antes de su spec.

**Why:** el 2026-09-24 lancé un agente de scaffolding en paralelo con la reescritura de los docs y el usuario lo cortó: «las specs tenían que hacerse antes del código. No borres nada, pero en cuanto puedas hazlas y luego continúa basándote en ellas».

**How to apply:** antes de lanzar cualquier agente que escriba ficheros fuera de `docs/`, `specs/` y `TODO.md`, comprueba que la spec que lo cubre existe y está aprobada. Si ya se escribió algo sin spec, no lo borres: escribe la spec a posteriori (la 000, en el caso del scaffolding), apruébala, verifica lo existente contra ella y apunta la desviación en `verification.md` §8. Ver [[project-v2-reinicio-lean]], [[project-aprobaciones-delegadas]].
