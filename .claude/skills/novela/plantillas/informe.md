---
capitulo: 0                   # N, "arco-AA" o "global"
intento: 0                    # K, o null en arco y global
origen: revisores             # revisores | harness (rechazo por longitud, sin revisores)
base: null                    # solo global: manuscrito | resumenes
veredicto: APROBADO           # APROBADO | RECHAZADO — el recalculado por el harness (informativo en arco y global)
veredicto_encargo: null       # el que propuso el revisor de encargo, si difiere del recalculado
veredicto_continuidad: null   # idem, el de continuidad
problemas:
  - gravedad: 1               # 1 contradice biblia/libro de estado/resúmenes · 2 no cumple escaleta o adelanta · 3 longitud (solo harness) · 4 voz/PDV/tono · 5 resumen no refleja
    origen: continuidad       # encargo (gravedades 2 y 4) · continuidad (1 y 5) · harness (3)
    donde: ""                 # párrafo, escena o cita breve
    que: ""                   # qué está mal, concreto
    por_que: ""               # contra qué regla, entrada o hecho del libro de estado choca
observaciones: []             # menores; no obligan a reescribir
---

# Informe del capítulo N (intento K)

**Veredicto: …** (n problemas de gravedad 1–2, m de gravedad 3–5; regla: `veredicto.rechaza_con_graves` / `rechaza_con_leves`). Recalculado por el harness sobre la **unión** de los dos informes: continuidad <n>, encargo <m>.

## Problemas
1. **[gravedad X · continuidad|encargo]** Dónde — qué — por qué.

## Observaciones
-
