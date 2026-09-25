# Anexo G · Modelos y proveedores de LLM considerados

## G.1 Modelo por rol

Criterio: calidad donde se planifica o se juzga la novela entera; modelo ligero en el resto, por coste y por cuota. Asignación provisional hasta la iteración de tuning.

| Modelo | Precio de lista (entrada / salida, $/M) | Roles | Motivo |
|---|---|---|---|
| Claude Sonnet 5 | 2 / 10 | Planner, juez | Planifican o juzgan la novela entera; el juez hace de filtro de calidad |
| Claude Haiku 4.5 | 1 / 5 | Writer, editor, entrevistador, extractor, revisor visual | Tareas acotadas por capítulo o por turno; el writer, el rol que más tokens gasta, pasó a Haiku por cuota |
| Claude Opus 5.5 | 4 / 20 | Ninguno | +2,96 €/novela si sustituye a Sonnet; el margen baja al 54 % (Anexo E) |

## G.2 Proveedor con 0 € en desarrollo

Criterio: 0 € en créditos de API, calidad suficiente y tool calling fiable con el Claude Agent SDK.

| Opción | Decisión | Motivo |
|---|---|---|
| Login de Claude Code de la máquina | **Elegido** | 0 €, tool calling fiable, mismas funciones que la API (hooks, skills, tools) |
| OpenRouter con modelos gratuitos | Descartado | ~50 peticiones al día: no alcanza para 10 capítulos con reintentos |
| Ollama local | Descartado | Calidad y tool calling no garantizados con el Agent SDK en el portátil |
| Gemini gratis con proxy LiteLLM | Descartado | Añade un proxy y el tool calling con el Agent SDK no está garantizado |

El proveedor es configurable (`LLM_PROVIDER=anthropic_compatible` apunta a la API de Anthropic u otro endpoint compatible): es el camino a producción sin tocar los roles. El coste de la propuesta se calcula siempre a precio de lista de la API.

---
