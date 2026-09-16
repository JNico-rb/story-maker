---
capitulo: 0                   # N, "arco-AA" o "global"
intento: 0                    # K, o null en arco y global
origen: revisor               # revisor | harness (rechazo por longitud, sin revisor)
base: null                    # solo global: manuscrito | resumenes
veredicto: APROBADO           # APROBADO | RECHAZADO — el recalculado por el harness (informativo en arco y global)
veredicto_revisor: null       # solo si difiere del recalculado
problemas:
  - gravedad: 1               # 1 contradice biblia/libro de estado/resúmenes · 2 no cumple escaleta o adelanta · 3 longitud (solo harness) · 4 voz/PDV/tono · 5 resumen no refleja
    donde: ""                 # párrafo, escena o cita breve
    que: ""                   # qué está mal, concreto
    por_que: ""               # contra qué regla, entrada o hecho del libro de estado choca
observaciones: []             # menores; no obligan a reescribir
---

# Informe del capítulo N (intento K)

**Veredicto: …** (n problemas de gravedad 1–2, m de gravedad 3–5; regla: `veredicto.rechaza_con_graves` / `rechaza_con_leves`).

## Problemas
1. **[gravedad X]** Dónde — qué — por qué.

## Observaciones
-
