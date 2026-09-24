---
name: project-v2-reinicio-lean
description: "El 2026-09-24 V2 se reinició desde cero con un diseño lean (ADR 0006); solo se trabaja en la rama V2; esta sesión prepara docs, scaffolding y specs de backend y otro chat implementa por carriles."
metadata:
  node_type: memory
  type: project
  modified: 2026-09-24T06:53:37.268Z
---

El 2026-09-24 el usuario vació `backend/` y `frontend/` en V2, copió los docs de V2-test como cantera y pidió: (1) docs completos, (2) todo el scaffolding, (3) specs de backend aprobadas, y después lanzar la implementación en otro chat con la mínima intervención suya. Dijo: «solamente vamos a trabajar en esta rama [V2]».

Se decidió reescribir los docs en versión lean (el diseño completo de V2-test se estimó en 45–60 días-persona): 7 roles (el editor critica y registra), RAG de una colección, un solo proceso con techo de 100k en memoria, `create_all` sin Alembic, linters heurísticos, reanudación solo desde `interrupted`. 21 specs de backend en `specs/backend/`, cuatro carriles A–D en worktrees hermanos `..\sm-<x>` (ruta corta por `LongPathsEnabled=0`), integración con `/orquestar` en el checkout principal.

**Why:** «lo más fácil posible» para completar todo el encargo, incluidos los opcionales, en poco tiempo.

**How to apply:** no reutilizar código ni ramas antiguas (V2-test, v2-test-*); solo como referencia técnica de configs probadas. Las decisiones viven en `docs/architecture.md` §18 y ADR 0006. Ver [[project-aprobaciones-delegadas]], [[project-examen-harness]].
