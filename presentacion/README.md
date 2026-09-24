# Presentación

**Idioma:** castellano, con los términos técnicos en inglés (harness, trace, score, gate, story bible, LLM-as-judge…), como recomienda el encargo.

Contenido previsto (pendiente):

| Fichero | Qué es |
|---|---|
| `story-maker.pdf` | el deck, en PDF |
| `story-maker.pptx` | el mismo deck, editable |
| `demo.mp4` | vídeo de demo; si supera el límite de GitHub (100 MB), va enlazado desde el `README.md` raíz |

## Deck

- Qué se construyó y por qué, y cómo funciona el harness.
- **Slide obligatoria de presupuesto y coste**, como propuesta económica al cliente: coste unitario por novela (tokens medidos en Langfuse, infraestructura, margen operativo), precio de venta y margen, coste del desarrollo en horas por fase con tarifa y total, escenarios de tres volúmenes mensuales y sensibilidad (tokens +50 %, más de tres revisiones por novela).
- **Evidencias obligatorias:** tabla de resultados de las evals con números; coste real por novela desde Langfuse y margen resultante; demo de un cambio del lector propagado a los capítulos afectados.

## Anexos (al final del deck, cada uno con nombre descriptivo)

- Anexo A — Arquitectura detallada del harness
- Anexo B — Especificación TLA+ comentada
- Anexo C — Tabla completa de resultados de las evals
- Anexo D — Esquema de la base de datos SQLite
- Anexo E — Análisis de sensibilidad extendido
- Anexo F — Red-team log
- Anexo G — Modelos de LLM considerados
- Anexo H — Capturas de Langfuse
