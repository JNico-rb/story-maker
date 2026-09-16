---
capitulo: 3
intento: 2
origen: harness
base: null
veredicto: RECHAZADO
veredicto_revisor: null
problemas:
  - gravedad: 3
    donde: "capítulo completo"
    que: "1940 palabras; objetivo 1500, margen ±300 (1200–1800)"
    por_que: "formato.tolerancia_longitud = 0.2; entrada 3 de arcos/arco-01.md, palabras_objetivo: 1500"
observaciones:
  - "Rechazo generado por el harness; el capítulo no ha pasado por el resumidor ni el revisor"
---

# Informe del capítulo 3 (intento 2)

**Veredicto: RECHAZADO** (0 problemas de gravedad 1–2, 1 de gravedad 3–5). Rechazo mecánico por longitud: el harness cuenta las palabras con `wc -w` antes de invocar al resumidor y al revisor.

## Problemas

1. **[gravedad 3]** Capítulo completo — 1940 palabras frente a un objetivo de 1500 con margen de ±300 (1200–1800): se pasa en 140 palabras del límite superior.

## Observaciones

- El capítulo no ha pasado por el resumidor ni por el revisor, de modo que no hay juicio sobre su contenido. Las correcciones pedidas en el informe del intento 1 (cronología de seis días y tensión con Pablo) sí están incorporadas en el texto, pero al añadirlas creció por encima del margen.
