---
capitulo: 1
intento: 1
origen: harness
base: null
veredicto: RECHAZADO
veredicto_encargo: null
veredicto_continuidad: null
problemas:
  - gravedad: 3
    origen: harness
    donde: "capítulo completo"
    que: "1012 palabras; objetivo 1500, margen 1200-1800"
    por_que: "formato.tolerancia_longitud = 0.2; entrada 1 de arcos/arco-01.md"
observaciones:
  - "Rechazo generado por el harness; el capítulo no ha pasado por el resumidor ni por los revisores"
---

# Informe del capítulo 1 (intento 1)

**Veredicto: RECHAZADO** (0 problemas de gravedad 1–2, 1 de gravedad 3–5; regla: `veredicto.rechaza_con_graves` = 1 / `rechaza_con_leves` = 2). Rechazo mecánico del harness por longitud: el capítulo no llegó al resumidor ni a los revisores.

## Problemas
1. **[gravedad 3 · harness]** Capítulo completo — 1012 palabras frente a un objetivo de 1500 con margen 1200–1800: faltan 188 palabras para entrar en el margen — `formato.tolerancia_longitud` = 0,2 sobre el `palabras_objetivo` de la entrada 1 de `arcos/arco-01.md`.

## Observaciones
- Rechazo generado por el harness; el capítulo no ha pasado por el resumidor ni por los revisores.
