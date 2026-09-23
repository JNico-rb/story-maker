---
name: project-examen-harness
description: "story-maker es el examen final de Harness Engineering; project-constraints.md es el encargo, lo opcional se trata como obligatorio y el tema post-IA se mantiene"
metadata:
  type: project
---

story-maker es el examen final de un curso de Harness Engineering. El encargo está en `project-constraints.md`: novelas personalizadas de regalo, de 10 capítulos de 1.000–1.500 palabras. Llegó el 2026-09-23 y sustituyó al diseño anterior, una novela de ciencia ficción autónoma a partir de un único prompt.

- El usuario quiere hacer **todo lo opcional del encargo**, tratado como obligatorio.
- **El tema post-IA se mantiene**: la novela personalizada transcurre en un mundo posterior a la revolución de la IA.
- El examen evalúa también `/docs` (proceso, trade-offs, logs), `/presentacion` y el uso de Claude Code en el repo: `CLAUDE.md` legible, `.claude/` commiteado y un browser MCP.

**Why:** determina qué es alcance y qué se corrige. Un proyecto sin evals medibles ni documentación de proceso en `/docs` no aprueba.

**How to apply:** contrasta cada decisión con `project-constraints.md` y aplica [[feedback-maxima-simplicidad]]. Las decisiones concretas viven en `docs/architecture.md` §16; no las dupliques aquí.
