# Anexo C · Tabla completa de resultados de evals

**Fuente:** `story-maker evals table`, generado en la máquina con sesión de Claude Code (única que ejecuta generación real), snapshot del **2026-09-25**, commit `bd1a994`. Ninguna prueba ni la CI llaman a un modelo (`docs/verification.md` §4.2); esta tabla sale de las cinco ejecuciones reales de evals sobre `ejemplos/briefs/`.

**Aviso de honestidad.** Snapshot **antes de cualquier publicación**: de los cinco briefs, ninguno llegó a `published`. Lean bloqueó las 3 candidatas que sí alcanzaron el gate (3/3). Esta tabla documenta el estado del tuning en curso (iteración de prompt del writer v1 → v3), no un resultado final ni una demostración de éxito.

## Leyenda de las celdas

Tomada de `docs/verification.md` §4.2 y de `backend/src/story_maker/observability/scores.py` (los 18 nombres de score canónicos; TLC/`harness-tla` no envía score).

- **Bloqueantes por capítulo** (`outline`, `longitud-capitulo`, `nombres-exactos`, `palabras-prohibidas`, `elementos-obligatorios`, `cronologia-lean`): `pasa · d` o `falla · d`, con *d* = intentos rechazados por ese validador antes del resultado final. En una versión publicada todo bloqueante pasa por construcción — la información está en lo que cazó antes de eso.
- **Semánticos** (`rubrica-capitulo`, `juez-novela`): media de sus criterios, con el criterio mínimo entre paréntesis. Escala 1–5.
- **`citas-verificadas`**: número de hechos extraídos del texto libre y descartados por no tener cita literal que los respalde.
- **Detector de inyección** / **hook de policy**: cuentas de `audit_log` (flags de inyección marcados; denegaciones del `PreToolUse` de policy), no scores 1–5.
- **`n/a`**: el validador no llegó a ejecutarse porque la ejecución terminó antes (brief `queued` o `failed` en un punto anterior).
- Filas sin dato en este snapshot (el validador no forma parte de esta extracción parcial, o depende de una versión publicada que aún no existe): *sin dato*.

Briefs: **1** ejemplo · **2** infantil · **3** boda/aniversario · **4** adversarial · **5** incoherencia temporal (`docs/verification.md` §4.2, tabla "qué debería ejercitar cada brief").

## (a) Resultados brief × validador

| Validador | 1 ejemplo | 2 infantil | 3 boda | 4 adversarial | 5 temporal |
|---|---|---|---|---|---|
| `schema-brief` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `citas-verificadas` (hechos descartados) | 0 | 0 | 0 | 0 | 0 |
| `schema-salida` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `outline` | pasa · 0 | pasa · 1 | pasa · 0 | pasa · 0 | pasa · 0 |
| `longitud-capitulo` | pasa · 2 | pasa · 6 | pasa · 2 | pasa · 0 | pasa · 3 |
| `nombres-exactos` | pasa · 6 | pasa · 14 | pasa · 4 | pasa · 0 | pasa · 0 |
| `palabras-prohibidas` | pasa · 0 | pasa · 0 | pasa · 0 | n/a | n/a |
| `elementos-obligatorios` | pasa · 0 | pasa · 0 | pasa · 0 | n/a | n/a |
| `rubrica-capitulo` | 5,0 (5) | 3,8 (2) | 4,0 (2) | 4,8 (4) | 4,0 (1) |
| `juez-novela` | 3,7 (1) | 4,4 (2) | 4,0 (2) | n/a | n/a |
| `cronologia-lean` | falla · 1 | falla · 1 | falla · 1 | n/a | n/a |
| `revision-visual` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `pdf-enlaces` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `linter-repeticion` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `linter-legibilidad` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `linter-estilo-ia` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| `linter-consistencia` | *sin dato* | *sin dato* | *sin dato* | *sin dato* | *sin dato* |
| Detector de inyección (flags en `audit_log`) | 0 | 0 | 0 | 3 | 0 |
| Hook de policy (denegaciones en `audit_log`) | 6 | 1 | 13 | 0 | 1 |
| `revision-humana` | *sin dato* (I, pendiente de sesión con el usuario) | — | — | — | — |

Ninguno de los cinco alcanzó `published`; por eso `schema-salida`, `revision-visual`, `pdf-enlaces` y los cuatro linters de prosa —validadores del artefacto final o que corren sobre la versión ya montada— no tienen dato en este snapshot, y no se ha inventado un valor para ellos.

## (b) Resumen por brief

| Métrica | 1 ejemplo | 2 infantil | 3 boda | 4 adversarial | 5 temporal |
|---|---|---|---|---|---|
| Estado final | `running` | `failed` (`retries_exhausted`) | `failed` (`retries_exhausted`) | `queued` | `failed` (`retries_exhausted`) |
| Capítulos aceptados al primer intento | 7 | 2 | 5 | 1 | 4 |
| Ciclos de gate | 1 | 1 | 1 | 0 | 0 |
| Tokens de entrada | 847 | 1.224 | 1.158 | 58 | 792 |
| Tokens de salida | 372.438 | 502.587 | 424.333 | 61.215 | 346.471 |
| Coste USD (Langfuse, precio de lista) | 3,5781 | 4,8250 | 3,9418 | 0,6997 | 3,2501 |
| Latencia total | 4.049.497 ms (≈ 67 min) | 5.312.293 ms (≈ 89 min) | 4.651.561 ms (≈ 78 min) | 573.530 ms (≈ 10 min) | 3.658.830 ms (≈ 61 min) |
| Pico de tokens concurrentes reservados (techo 100.000) | 28.246 | 24.394 | 26.562 | 11.734 | 21.733 |
| Prompts con etiqueta explícita | 2 | 1 | 1 | 1 | 2 |
| Traza Langfuse | `run:16` | `run:12` | `run:13` | `run:14` | `run:15` |

*(«Prompts con etiqueta explícita»: cuenta de prompts servidos por Langfuse con `label` versionado en esa ejecución, según el dato de la tabla; este anexo no infiere a qué versión de `writer` corresponde cada cuenta — ver Anexo H para el mecanismo de etiquetado.)*

El brief 4 (adversarial) quedó `queued`: la carta con instrucciones dirigidas al sistema activó el detector de inyección (3 flags) antes de consumir una sesión completa de generación — coherente con el diseño (`docs/verification.md` §4.2, tabla "qué debería ejercitar cada brief": "nada llega al brief ni a la novela").

## Iteración de tuning (`docs/verification.md` §4.2(c))

Disparador común: en 020-C10 (ejecuciones 1–5), `longitud-capitulo` falla en los 5 briefs y ninguna novela llega al gate.

### Iteración 1 — writer v1 → v2

| Campo | Valor |
|---|---|
| Fecha · commit | 2026-09-25 · `cf6b5e4`, `ff129b7` |
| Disparador | `longitud-capitulo` en `falla` en los briefs 1–5 (2, 5, 5, 3 y 3 rechazos); 5 `failed (retries_exhausted)`. Entregas de 666 a 1.194 palabras con objetivo 1.100–1.250 |
| Hipótesis | El writer (Haiku 4.5) subestima la extensión; repartir `target_words` por beat y contar en párrafos |
| Cambio | prompt `writer` v1 → v2 en Langfuse |
| Control | los 5 briefs (antes = ejecuciones 1–5) → después = ejecuciones 6–10, misma config |

| Métrica | Antes (v1) | Después (v2) | Δ |
|---|---|---|---|
| Capítulos aceptados al primer intento | 1 | 0 | −1 |
| Entregas en rango de `longitud-capitulo` | 8 de 26 (media 945) | 11 de 28 (media 979) | +3 (+34 palabras) |
| Novelas publicadas | 0 | 0 | 0 |
| Coste USD por novela (media) | 0,73 | 0,86 | +0,13 |

Efecto insuficiente: la extensión apenas se mueve.

### Iteración 2 — writer v2 → v3

| Campo | Valor |
|---|---|
| Fecha · commit | 2026-09-25 · `0455b81` |
| Disparador | Iteración 1: entregas de 674 a 1.226 palabras, 5 `failed` |
| Hipótesis | Haiku 4.5 entrega ~25 % menos de lo que cree; `target_words` + 200 y al menos 14 párrafos compensa el sesgo. El writer sigue en Haiku por decisión del usuario (cuota, `architecture.md` §18) |
| Cambio | prompt `writer` v2 → v3 en Langfuse |
| Control | los 5 briefs → después = ejecuciones 11–16. Desde la 12, la lista de prohibidas de nivel user del brief boda solo está activa durante su ejecución — la 11 (brief 1) cayó por una prohibida de otro cliente que se filtró («pantalla»), fallo corregido en 020-C18 |

| Métrica | Brief | Antes (v2) | Después (v3) | Δ |
|---|---|---|---|---|
| Entregas en rango de `longitud-capitulo` | 1 | 0 de 2 (media 858) | 5 de 6 (media 1.375) | +5 (+517 palabras) |
| Novelas publicadas | 1–5 | 0 | en curso (esta tabla) | — |
| Coste USD por novela | 1 | 0,52 | 1,28 (hasta el capítulo 4) | — |

La tabla (a)/(b) de este anexo corresponde a las trazas `run:12`–`run:16`, tomadas en el mismo snapshot (2026-09-25, commit `bd1a994`) que la iteración 2 de tuning describe como «en curso»; no se afirma aquí en qué versión de `writer` corrió cada una más allá de lo que ya documenta la sección de iteración anterior.

---

Story Maker · Anexo C — tabla completa de resultados de evals
