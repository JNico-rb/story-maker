---
name: feedback-subagentes-cuota
description: "Como mucho 2 subagentes a la vez y modelo fijado por rol (auditor siempre opus); nunca recortar alcance por cuota, se para y se sigue."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-24T08:48:43.956Z
---

Como mucho **2 subagentes a la vez** por sesión. Sesiones activas: como mucho 3 (el orquestador + 2 carriles), desde el 2026-09-24; primero A (cuando 000 cierre y 001 tenga plan), después C y D según el grafo.

Modelo con `model:` en cada llamada a Agent:
- **opus**: `auditor` (puerta de calidad, nunca sonnet), el orquestador, el `implementador` de 006, 007, 012 y 014, y cualquier fallo que siga igual tras 2 intentos.
- **sonnet**: `redactor-specs`, `implementador` del resto y `verificador`.

Nunca se recortan alcance, casos ni tests para ahorrar: si falta cuota, se para y se sigue después.

Ahorro de contexto que pidió: el redactor deja el borrador del plan en `specs/.drafts/plan-NNN.md` y sus filas de §18; el auditor audita la spec y, a gap cero, el plan en la misma llamada; informes de subagente ≤5 líneas; el orquestador no relee specs completas.

**Why:** el 2026-09-24, lanzar 20 subagentes en paralelo agotó el límite de gasto mensual de la organización (HTTP 429) y cortó 18 redactores a medias. El usuario prefiere ir más lento a perder calidad.

**How to apply:** en `/orquestar`, `/spec`, `/plan` y `/carril`, pon en cola el trabajo y lánzalo de dos en dos, con el modelo de la lista. Ver [[project-aprobaciones-delegadas]] y [[feedback-respuestas-cortas]].
