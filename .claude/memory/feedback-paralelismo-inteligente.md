---
name: feedback-paralelismo-inteligente
description: "Paralelizar todo lo posible pero sin construir la casa por el tejado — anchura dentro de una capa, nunca saltar capas; un escritor por fichero/checkout."
metadata:
  node_type: memory
  type: feedback
  modified: 2026-09-24T08:23:38.613Z
---

El usuario quiere paralelizar al máximo, pero con "paralelismo inteligente": en paralelo solo lo independiente de la misma capa (varias specs a la vez, varios carriles con dependencias cerradas); una capa no empieza hasta que la anterior está aprobada (p. ej. specs de frontend esperan a las specs de backend de las que dependen).

**Why:** 2026-09-24 hubo colisiones de varias sesiones escribiendo en el mismo checkout V2 y agentes adelantándose a las gates; pidió explícitamente "no construir la casa por el tejado".

**How to apply:** proponer siempre qué va en paralelo y qué espera a qué, con paradas de revisión; un único escritor en V2 (el integrador), otras sesiones solo lectura o en worktrees `../sm-<x>`. Relacionado: [[feedback-specs-antes-que-codigo]], [[project-aprobaciones-delegadas]].
