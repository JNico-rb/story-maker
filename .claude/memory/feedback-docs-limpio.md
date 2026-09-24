---
name: feedback-docs-limpio
description: "docs/ solo con los cuatro docs de referencia más adr/; ficheros nuevos solo si son estrictamente necesarios, o temporales y borrados después"
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-23T11:35:59.679Z
---

`docs/` contiene solo `architecture.md`, `definitions.md`, `verification.md`, `domain-knowledge.md`, `adr/` y `relational-matrix.md` (el gap plan–arquitectura del proceso 3, que el usuario pidió el 2026-09-23 y se queda como registro). Un fichero nuevo en `docs/` solo si es estrictamente necesario (p. ej. `security-report.md`, que el encargo nombra), o se crea como temporal y se borra al terminar.

**Why:** el usuario lo pidió el 2026-09-23 al ver `docs/` lleno de registros de proceso sueltos (spec inicial, logs, README, matriz).

**How to apply:** los registros de proceso que pide el encargo (iteraciones, red-team, uso de Claude Code y browser MCP, evals) van como secciones de los docs existentes; el mapa de entregables va al README de la raíz; la spec inicial, como ADR. Relacionado: [[feedback-maxima-simplicidad]], [[project-examen-harness]].
