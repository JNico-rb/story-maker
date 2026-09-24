---
name: feedback-subagentes-cuota
description: "Paralelizar todo lo que sea seguro (hoy 4 implementadores: A, B, C, D) con modelo fijado por spec; integración automática con push; nunca recortar alcance por cuota."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-24T10:47:50.548Z
---

**Más agentes en paralelo si no hay peligro y ahorra tiempo** (decisión del usuario 2026-09-24, sustituye al límite de 3): un implementador por carril, sin dos specs a la vez en el mismo worktree, y solo specs con sus dependencias cerradas. Hoy cuatro carriles de backend: A, B, C y D. Los carriles los lleva el integrador como subagentes `implementador` en `../sm-<x>`, salvo que el usuario diga que abre terminales.

Modelo del `implementador` (decisión del usuario 2026-09-24):
- **opus** donde hay riesgo de fallo: 003 (Agent SDK en Windows), 006 (TLA+), 007 (Lean), 009 (versiones), 011 (producción de capítulos), 012 (gate), 014 (cambios del lector), 016 (sqlite-vec y fastembed en Windows), y cualquier fallo que siga igual tras 2 intentos.
- **sonnet**: el resto, y `redactor-specs` y `verificador` (frontmatter de `.claude/agents/`).

**Integración automática, sin preguntar:** verificador PASS → `merge --no-ff` en V2 → suite completa → `git push origin V2`; después, rebase de los demás carriles sobre V2 antes de su siguiente spec. Rojo → deshacer el merge y devolver el fallo al carril.

Nunca se recortan alcance, casos ni tests para ahorrar: si falta cuota, se para y se sigue después.

**Why:** el 2026-09-24, 20 subagentes en paralelo agotaron el límite de gasto de la organización (HTTP 429). El usuario prefiere ir más lento a perder calidad, pero quiere el backend cuanto antes.

**How to apply:** en `/orquestar` y `/integrar`. Ver [[project-aprobaciones-delegadas]] y [[feedback-respuestas-cortas]].
