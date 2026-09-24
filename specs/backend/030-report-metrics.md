# 030 — Informe de métricas

> Carril: J · Depende de: 001-base, 004-observabilidad (las tablas `role_sessions` y `validator_results`) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Dar en un fichero corto del repo las cifras reales de las ejecuciones —coste por novela para la slide de presupuesto, scores para la tabla de evals, el antes y el después del tuning, y el rol o la fase que más gasta— sin leer trazas en crudo. `story-maker report metrics` agrega lo que SQLite ya guarda (`architecture.md` §13.2, §11.7, §15.8 y §18) y escribe `docs/metrics.md`.

## Alcance

- `story-maker report metrics [--out <ruta>]`: lee `role_sessions` y `validator_results` (con `runs` y `novels` para agrupar) y escribe un Markdown, por defecto `docs/metrics.md`.
- Secciones, en este orden: resumen por novela; por capítulo; por rol; scores por validador y novela; versiones de prompt.
- Solo agregados: sumas, recuentos y medias. Ningún texto de capítulo, prompt, brief ni detalle JSON de un validador.

## Fuera de alcance

- Consultar Langfuse o cualquier red (§18: la fuente es SQLite).
- La tabla brief × validador de las evals → 020 (`evals table`); aquí no se repite su formato.
- Guardar el uso, el coste o los scores → 004, 011, 012.

## Comportamiento observable

#### 030-C01 — Coste, tokens y latencia por novela (T)

Dos novelas con sesiones de rol en sus ejecuciones → una fila por novela con la suma de tokens (entrada, salida, lectura y escritura de caché), coste en USD y latencia, y el número de ejecuciones. Las sesiones de entrevista, fuera de una ejecución, cuentan en su novela.

#### 030-C02 — Por capítulo (T)

Sesiones con capítulo → una fila por novela y capítulo con sus sumas. Las sesiones sin capítulo (plan, juez, entrevista) no entran en esta sección.

#### 030-C03 — Por rol (T)

Una fila por rol con recuento de sesiones, sumas de tokens, coste y latencia, y su porcentaje del coste total; ordenadas de mayor a menor coste. La primera fila es el rol que más gasta.

#### 030-C04 — Scores por validador y novela (T)

`validator_results` de dos novelas → una fila por novela y validador con recuento de resultados, cuántos pasan, y score medio, mínimo y máximo. Un validador sin score (solo pasa/falla) muestra los recuentos y deja el score como hueco.

#### 030-C05 — Versiones de prompt (T)

Una fila por ejecución y rol con la versión o las versiones de prompt de sus sesiones. Una ejecución con dos versiones del mismo rol muestra las dos: así se ve el antes y el después de un tuning.

#### 030-C06 — Un dato que falta es un hueco, nunca una estimación (T)

Una sesión sin coste, sin latencia o sin versión de prompt → esa celda dice `hueco` y la suma de su fila también, en vez de contar la sesión como cero. Las demás filas no cambian.

#### 030-C07 — Sin ejecuciones, el informe lo dice (T)

Base de datos sin sesiones ni resultados → el fichero se escribe con una sola línea que dice que no hay ejecuciones; la orden termina con éxito.

#### 030-C08 — Ruta de salida (T)

`--out <ruta>` escribe ahí; sin `--out`, en `docs/metrics.md`. Un fichero existente se sustituye entero.

## Invariantes

- **030-I1 (T)** · El informe es determinista: la misma base de datos da el mismo fichero byte a byte (orden fijo de filas y columnas, sin fecha de generación).
- **030-I2 (T)** · Ninguna prueba ni la orden llaman a un modelo, a Langfuse ni a la red.
- **030-I3 (T)** · El fichero no contiene texto de capítulos, prompts, briefs ni el detalle JSON de los validadores.

## Docs referenciados

- `docs/architecture.md` §11.7, §13.2, §15.6 (`role_sessions`, `validator_results`), §15.8 y §18 (fuente de `report metrics`).
- `docs/verification.md` §4.2 (evals).
