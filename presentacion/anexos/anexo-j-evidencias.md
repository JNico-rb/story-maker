# Anexo J · Evidencias obligatorias

**Fuente:** SQLite (`story-maker evals table`, `runs`, `role_sessions`, `validator_results`) y Langfuse Cloud UE (consulta por MCP, solo lectura). Snapshot del **2026-09-25**, código en el commit `af68db6` (V2 con los arreglos del carril Z). Cubre las tres evidencias que el encargo exige en la presentación: tabla de evals con números, coste real por novela y margen, y demo de un cambio del lector.

## J.1 Tabla de resultados de las evals

Salida literal de `story-maker evals table` (última ejecución de cada brief de `ejemplos/briefs/`). Leyenda en el Anexo C: `pasa · d` / `falla · d` = resultado final y rechazos previos de ese validador; semánticos = media (mínimo) en escala 1–5; `n/a` = no llegó a ejecutarse.

| Validador | 1 ejemplo | 2 infantil | 3 boda | 4 adversarial | 5 temporal |
|---|---|---|---|---|---|
| `citas-verificadas` (hechos descartados) | 0 | 0 | 0 | 0 | 0 |
| `outline` | pasa · 0 | pasa · 1 | pasa · 0 | pasa · 0 | pasa · 0 |
| `longitud-capitulo` | pasa · 2 | pasa · 6 | pasa · 2 | pasa · 3 | pasa · 3 |
| `nombres-exactos` | pasa · 7 | pasa · 14 | pasa · 4 | pasa · 0 | pasa · 0 |
| `palabras-prohibidas` | pasa · 0 | pasa · 0 | pasa · 0 | pasa · 0 | n/a |
| `elementos-obligatorios` | pasa · 0 | pasa · 0 | pasa · 0 | pasa · 0 | n/a |
| `rubrica-capitulo` | 5,0 (5) | 3,8 (2) | 4,0 (2) | 4,6 (4) | 4,0 (1) |
| `juez-novela` | 4,3 (2) | 4,4 (2) | 4,0 (2) | 4,3 (3) | n/a |
| `cronologia-lean` | pasa · 1 | falla · 1 | falla · 1 | falla · 1 | n/a |
| Detector de inyección (flags en `audit_log`) | 0 | 0 | 0 | 3 | 0 |
| Hook de policy (denegaciones en `audit_log`) | 6 | 1 | 13 | 0 | 1 |

`schema-brief`, `schema-salida`, `revision-visual`, `pdf-enlaces` y los cuatro linters de prosa quedan en `n/a` en los cinco: corren sobre la versión publicada o sobre el PDF, y ninguna ejecución llegó ahí.

| Métrica | 1 ejemplo | 2 infantil | 3 boda | 4 adversarial | 5 temporal |
|---|---|---|---|---|---|
| Estado final | `failed` (`retries_exhausted`) | `failed` (`retries_exhausted`) | `failed` (`retries_exhausted`) | `failed` (`retries_exhausted`) | `failed` (`retries_exhausted`) |
| Capítulos aceptados al primer intento | 9 | 2 | 5 | 6 | 4 |
| Ciclos de gate | 3 | 1 | 1 | 1 | 0 |
| Tokens (entrada / salida) | 1.027 / 462.248 | 1.224 / 502.587 | 1.158 / 424.333 | 868 / 328.047 | 792 / 346.471 |
| Coste USD | 4,6361 | 4,8250 | 3,9418 | 3,3126 | 3,2501 |
| Latencia total | ≈ 83 min | ≈ 89 min | ≈ 78 min | ≈ 58 min | ≈ 61 min |
| Pico de tokens concurrentes reservados (techo 100.000) | 28.246 | 24.394 | 26.562 | 26.253 | 21.733 |
| Traza Langfuse | `run:16` | `run:12` | `run:13` | `run:14` | `run:15` |

Lectura: los bloqueantes deterministas terminan pasando en los cinco (con reintentos); lo que impide publicar es `cronologia-lean` en el gate (3 de 4 briefs que llegan a él) y el agotamiento de reintentos en la reescritura dirigida. El brief 1 es el único con Lean en verde (tras 1 rechazo) y cae después, en su tercer ciclo de gate.

### Ejecución de control con brief sintético (ejecución 18)

Brief nuevo, ficticio y sin contradicciones (C1–C5 vacías): aniversario, aventura de tono emocionante, tres obligatorios, con el mismo código `af68db6`.

| Métrica | Valor |
|---|---|
| Estado final | `failed` (`retries_exhausted`): capítulo 3, 4 intentos agotados; último rechazo `longitud-capitulo` (1.537 palabras, rango 1.000–1.500) |
| Capítulos escritos | 10 de 10 antes del gate |
| Ciclos de gate | 1, tumbado por `cronologia-lean` |
| Fallo de Lean (literal) | «T1 · Orden temporal declarado: el evento registrado (capítulo 3, beat 1; 16 de septiembre de 2026 a las 18:00) se narra después que el evento registrado (capítulo 2, beat 2; 16 de septiembre de 2026 a las 20:00), pero ocurre antes.» |
| Otros rechazos en la reescritura | `nombres-exactos` (variante de un nombre del reparto, caps. 2 y 3); `rubrica-capitulo` · fidelidad-canon (aritmética de años entre recuerdos, cap. 3) |
| Sesiones de rol | 37 (planner 1, writer 18, editor 17, judge 1) |
| Coste USD | 4,2960 (Haiku 4.5: 3,4670 · Sonnet 5: 0,8290) |
| Duración | 13:55:54 → 15:42:46 (≈ 1 h 47 min) |
| Traza Langfuse | `run:18` |

Es el ejemplo de **fallo detectado por Lean** que pide la slide de validación: el texto era coherente capítulo a capítulo (la rúbrica local lo aceptó) y solo la comprobación formal de la cronología global vio la inversión entre los capítulos 2 y 3.

## J.2 Coste real por novela y margen

### Coste de tokens medido

| Fuente | Ejecución 18 (USD) |
|---|---|
| `role_sessions.cost_usd` (precio de lista propio, el que usa `costes.py`) | 4,2960 |
| Langfuse, suma de `totalCost` de las generaciones de la ventana de la ejecución | 4,3130 |
| `role_sessions.sdk_cost_usd` (suma que devuelve el Agent SDK) | 5,1995 |

Langfuse y la cifra propia coinciden al 0,4 %; el SDK da un 21 % más (misma divergencia que ya anota el Anexo H.2, `docs/verification.md` §4.2 «Protocolo de coste»). Media de las seis ejecuciones completas más recientes (12–18): **4,04 USD**.

### Coste unitario y margen (200 novelas/mes, 3 revisiones incluidas)

Mismo modelo de `costes.py` (IVA 21 %, pasarela 1,5 % + 0,25 €, contingencia 15 % sobre tokens, 0,90 EUR/USD), con el coste de tokens de la novela sustituido por el medido (3,87 € frente a los 2,48 € estimados).

| Concepto | € por novela |
|---|---|
| Tokens de la novela (medido) | 3,87 |
| Tokens de las 3 revisiones incluidas (estimado) | 1,54 |
| Contingencia 15 % sobre tokens | 0,81 |
| Pasarela de pago | 0,69 |
| Infraestructura (÷ 200) | 0,46 |
| Soporte y operación (÷ 200) | 2,25 |
| **Coste unitario total** | **9,61** |
| Precio de venta neto (29,00 € con IVA) | 23,97 |
| **Margen** | **14,35 € (60 %)** |

### Escenarios de volumen

| Novelas/mes | Ingresos netos | Coste variable | Coste fijo | Margen | % |
|---|---|---|---|---|---|
| 50 | 1.198 € | 345 € | 262 € | 591 € | 49 % |
| 200 | 4.793 € | 1.381 € | 542 € | 2.871 € | 60 % |
| 500 | 11.983 € | 3.452 € | 1.041 € | 7.490 € | 63 % |

### Sensibilidad (200/mes)

| Caso | Coste variable €/novela | Margen/mes | % |
|---|---|---|---|
| Base (tokens medidos) | 6,90 | 2.871 € | 60 % |
| Tokens +50 % | 10,01 | 2.249 € | 47 % |
| 6 revisiones (3 extra gratis) | 8,68 | 2.516 € | 52 % |
| 6 revisiones (3 extra a 2,99 €) | 8,68 | 3.999 € | 64 % |

Con el coste medido el margen baja del que daba la estimación, pero el negocio sigue en positivo en los tres volúmenes y en los dos casos de sensibilidad que pide el encargo (tokens +50 %, más de tres revisiones).

---

Story Maker · Anexo J — evidencias obligatorias
