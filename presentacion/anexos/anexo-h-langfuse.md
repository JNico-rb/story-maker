# Anexo H · Capturas de Langfuse

**Observabilidad, no solo logging:** cada ejecución de generación abre una traza en Langfuse Cloud UE (plan Hobby); dentro de ella, un span por rol, por tool y por capítulo, y una generación por llamada al modelo con su coste y su versión de prompt.

## H.1 Verificación en vivo (MCP, solo lectura)

Durante la redacción de este anexo se consultó Langfuse por MCP, en modo lectura (`getHealth`, `listObservations`), sin escribir nada:

- `getHealth` → `{"status": "OK", "version": "4.45.2"}`, proyecto `cmu40h15j05s9ad0c5uz7e8tr`.
- Se listaron observaciones reales del proyecto (2026-09-25) y se confirmó en vivo la jerarquía de spans que documenta `docs/verification.md`: una traza raíz `generacion` → `capitulo-N` → `rol:planner` / `rol:writer` / `rol:editor` → `tool:submit_plan` / `tool:submit_chapter` / `tool:submit_review` / `tool:Skill` → `llamada:claude-<modelo>` (la generación). También aparece `validador:outline` como span propio bajo la traza.
- No se ha correlacionado con certeza esta traza concreta con una fila de `run:*` del Anexo C (la consulta no expone ese mapeo de forma directa); se documenta como evidencia en vivo de la estructura, no como el trace-level total de `run:16`.

## H.2 Un ejemplo real de generación

Observación `llamada:claude-sonnet-5` bajo `rol:planner`, capturada por MCP:

| Campo | Valor |
|---|---|
| Modelo | `claude-sonnet-5` |
| Tokens: entrada / salida / cache-read / cache-write | 4 / 48.471 / 15.468 / 54.051 (total 117.994) |
| `costDetails.total` (modelo de coste de Langfuse) | 0,6229391 USD |
| `metadata.sdk_cost_usd` (suma propia del SDK) | 0,7040156 USD |
| `metadata.prompt_version` | 1 |
| `metadata.latency_ms` | 498.202 |

**Hallazgo real, no hipotético:** las dos cifras de coste difieren (~13 %). `docs/verification.md` §4.2 «Protocolo de coste» prevé exactamente este contraste — «la suma propia por sesión se contrasta con el `total_cost_usd` que devuelve el SDK; la diferencia se anota aquí» — y esta observación es esa anotación: el coste de lista usado en el Anexo C y en `presentacion/costes.py` es el propio (`sdk_cost_usd`), no el recalculado por Langfuse con su propio tarificador de modelos.

## H.3 18 scores por traza (`backend/src/story_maker/observability/scores.py`)

Cada validador escribe su resultado como score de Langfuse sobre la traza (o el span del capítulo), con nombre canónico y tipado (`ScoreName`, comprobado por mypy — 004-I5):

`schema-brief` · `schema-salida` · `citas-verificadas` · `outline` · `longitud-capitulo` · `nombres-exactos` · `palabras-prohibidas` · `elementos-obligatorios` · `revision-visual` · `pdf-enlaces` · `linter-repeticion` · `linter-legibilidad` · `linter-estilo-ia` · `linter-consistencia` · `rubrica-capitulo` · `juez-novela` · `revision-humana` · `cronologia-lean`

Excepción: TLC (`harness-tla`) nunca envía score — corre en desarrollo y en CI, no sobre una traza de generación (`is_scoreable()`, 004-C13).

## H.4 Spans de policy y de validador

Además de `rol:*`, `tool:*` y `capitulo-N` (confirmados en vivo, H.1), el adaptador registra:

- `validador:<nombre>` — un span por validador ejecutado, con su resultado.
- `politica:<regla>` — una entrada por decisión del hook `PreToolUse` (allow/deny/flag), la misma fuente que `audit_log` (Anexo C, filas «detector de inyección» y «hook de policy»).

## H.5 Prompts versionados con label

Los prompts de cada rol viven en Langfuse (`prompts push` / `updatePromptLabels`), no en el repositorio: cada generación registra `prompt_version` (H.2) y la etiqueta vigente en el momento de la llamada. La iteración de tuning del Anexo C (writer v1 → v2 → v3) es exactamente este mecanismo: cambiar el prompt en Langfuse, mover la etiqueta y relanzar los mismos briefs como control.

## H.6 Coste por novela

Mismo origen que el Anexo C (b) — `role_sessions` en SQLite, contrastado con Langfuse por sesión (H.2):

| Brief | Coste USD | Traza |
|---|---|---|
| 1 ejemplo | 3,5781 | `run:16` |
| 2 infantil | 4,8250 | `run:12` |
| 3 boda | 3,9418 | `run:13` |
| 4 adversarial | 0,6997 | `run:14` |
| 5 temporal | 3,2501 | `run:15` |

## H.7 Sesiones agrupadas por `session_id` real

En desarrollo, en el momento de escribir este anexo (2026-09-25), `backend/src/story_maker/observability/langfuse_adapter.py` y su test (`backend/tests/observability/test_adapter.py`) tienen cambios sin commitear que agrupan las trazas por el `session_id` real de la ejecución, en vez de un identificador sintético — es trabajo en curso, no cerrado; el estado que se documenta aquí es el del checkout en este momento, no el de un commit.

## H.8 Captura de pantalla

`Captura de pantalla: añadir` — este anexo usa datos reales obtenidos por MCP (lectura) en vez de una captura de la UI de Langfuse; añadir el pantallazo de la traza cuando se disponga de una sesión interactiva con el navegador contra `cloud.langfuse.com`.

---

Story Maker · Anexo H — capturas de Langfuse
