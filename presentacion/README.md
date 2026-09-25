# Presentación

**Idioma:** castellano, con los términos técnicos en inglés (harness, trace, score, gate, story bible, LLM-as-judge…), como recomienda el encargo.

Propuesta formal de **Qaracter** a su cliente, con imagen corporativa propia: logotipo ([images/qaracter-logo.png](../images/qaracter-logo.png)), paleta y tipografía definidas en [tema.css](tema.css) y aplicadas en el deck y en cada anexo.

## Deck

| Fichero | Qué es |
|---|---|
| [Story Maker · Propuesta.pdf](<Story Maker · Propuesta.pdf>) | El deck final de la presentación (10 minutos), en PDF |
| [deck.pptx](deck.pptx) · [deck.pdf](deck.pdf) · [deck.md](deck.md) | La versión anterior del deck, en PowerPoint, en PDF y en su fuente Markdown editable |
| [presupuesto.md](presupuesto.md) · [costes.py](costes.py) | La slide de presupuesto y coste razonada, y el script que calcula coste unitario, margen, escenarios de volumen y sensibilidad a partir del coste de tokens medido en Langfuse |

Contenido obligatorio del encargo: portada, problema y cliente, configuración y lectura, arquitectura del harness, validación, evaluación y observabilidad (tabla de evals con números, fallo detectado por Lean, propiedades de TLC, tuning, traza de Langfuse), guardrails, **presupuesto y coste** (coste unitario desde Langfuse, precio y margen, horas × tarifa, tres volúmenes, sensibilidad a tokens +50 % y a más de tres revisiones), demo del cambio del lector y contraportada.

## Anexos

Un fichero por anexo en [anexos/](anexos/), en PDF y con su fuente Markdown:

| Anexo | PDF |
|---|---|
| A · Arquitectura detallada del harness | [anexo-a-arquitectura.pdf](anexos/anexo-a-arquitectura.pdf) |
| B · Especificación TLA+ comentada y verificación Lean | [anexo-b-tla-lean.pdf](anexos/anexo-b-tla-lean.pdf) |
| C · Tabla completa de resultados de las evals | [anexo-c-evals-tabla.pdf](anexos/anexo-c-evals-tabla.pdf) |
| D · Esquema de la base de datos SQLite | [anexo-d-esquema-sqlite.pdf](anexos/anexo-d-esquema-sqlite.pdf) |
| E · Análisis de sensibilidad extendido | [anexo-e-sensibilidad.pdf](anexos/anexo-e-sensibilidad.pdf) |
| F · Red-team log | [anexo-f-red-team.pdf](anexos/anexo-f-red-team.pdf) |
| G · Modelos de LLM considerados | [anexo-g-modelos-llm.pdf](anexos/anexo-g-modelos-llm.pdf) |
| H · Observabilidad en Langfuse | [anexo-h-langfuse.pdf](anexos/anexo-h-langfuse.pdf) |
| I · Claude Code en el desarrollo | [anexo-i-claude-code.pdf](anexos/anexo-i-claude-code.pdf) |

[anexos.md](anexos.md) es la fuente original de la que salen A, B, D, E, G e I. Los datos de C, F y H salen de `docs/verification.md` §4.2 y §4.9 y de SQLite (`story-maker evals table`).

## Vídeo de demo

`demo.mp4` en esta carpeta; si supera el límite de GitHub (100 MB), va enlazado desde el [README](../README.md) raíz.
