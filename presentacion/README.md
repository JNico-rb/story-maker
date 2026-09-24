# Presentación

**Idioma:** castellano, con los términos técnicos en inglés (harness, trace, score, gate, story bible, LLM-as-judge…), como recomienda el encargo.

Contenido previsto (pendiente):

| Fichero | Qué es |
|---|---|
| `deck.pdf` | el deck, en PDF (anexos incluidos) |
| `deck.pptx` | el mismo deck, editable |
| `demo.mp4` | vídeo de demo; si supera el límite de GitHub (100 MB), va enlazado desde el `README.md` raíz |

## Deck

- Qué se construyó y por qué, y cómo funciona el harness.
- **Slide obligatoria de presupuesto y coste**, como propuesta económica al cliente: coste unitario por novela (tokens medidos en Langfuse, infraestructura, margen operativo), precio de venta y margen, coste del desarrollo en horas por fase con tarifa y total, escenarios de tres volúmenes mensuales y sensibilidad (tokens +50 %, más de tres revisiones por novela).
- **Evidencias obligatorias:** tabla de resultados de las evals con números; coste real por novela desde Langfuse y margen resultante; demo de un cambio del lector propagado a los capítulos afectados.

## Anexos

No son ficheros aparte: son las últimas slides de `deck.md` (y por tanto de `deck.pdf`/`deck.pptx`), una por tema — arquitectura detallada del harness, especificación TLA+ comentada, tabla completa de resultados de las evals, esquema de la base de datos SQLite, análisis de sensibilidad extendido, red-team log, modelos de LLM considerados y capturas de Langfuse —, cada una con nombre descriptivo (Anexo A–H).
