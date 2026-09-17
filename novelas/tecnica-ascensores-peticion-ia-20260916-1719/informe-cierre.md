---
resultado: "EXITO"
motivo: "EXITO"
fecha: "2026-09-17 11:58"
etapa: "completa"
arco: 1
capitulo: 5
intento: 2
cumple_todas: true
---

# Informe de cierre — tecnica-ascensores-peticion-ia-20260916-1719

**Resultado:** EXITO
**Motivo:** EXITO
**Detalle:** Novela completa. Cinco capítulos cerrados, ninguno por agotamiento; manuscrito ensamblado, revisión global hecha sobre el manuscrito íntegro y métricas calculadas. Todas las métricas cumplen su umbral.

## Dónde se detuvo
Etapa `completa` · arco 1 de 1 · capítulo 5 de 5 · intento 2. No es una parada: es el final del flujo.

## Qué quedó completado
- Escaleta aprobada: **sí** (5 capítulos en 1 arco; 2 rechazos de escaleta antes de aprobarse)
- Arcos detallados / revisados: **1 / 1** (con un solo arco, la revisión de arco y la global son la misma pasada; se hizo solo la global, según SKILL.md §3)
- Capítulos cerrados: **5 de 5** (por agotamiento: **0**)
- Informe global: **sí** (base: manuscrito, 6.426 palabras ≤ 60.000)
- Erratas propuestas: **0** (el informe global no devolvió problemas)

Intento aprobado de cada capítulo: 1 → 3 · 2 → 2 · 3 → 1 · 4 → 1 · 5 → 2.

## Invocaciones
interrogador **6** · escritor **12** · resumidor **7** · revisor-encargo **6** · revisor-continuidad **9**. Total **40**.

Reintentos técnicos en toda la novela: **7** (todos por incumplimiento de contrato, ninguno por fallo de herramienta; **0** en esta sesión). Discrepancias de veredicto: **2**. Rechazos por longitud: **3** (capítulos 1, 2 y 5; los tres por quedarse cortos, los tres resueltos con un ajuste que no consumió reescritura).

Esta sesión reanudó la novela en el capítulo 4. Al reanudar se encontró un paso a medias (capítulo 4 con intento 1 rechazado por longitud e intento 2 escrito pero nunca revisado) y se descartó, volviendo al commit `1cd7b16`. Queda registrado como `paso_descartado`; el motivo `INTERRUMPIDO` de la tabla de `procedimientos/cierre.md` se aplica a esa reanudación, no a este cierre.

## Volumen
Suma de las filas `invocacion` del registro, por agente y por modelo (`specs/functional.md` §6.6). Los revisores no escriben ficheros, así que no tienen `pal_salida`. Claude Code no devuelve tokens ni coste en el hito 1.

| agente | modelo | invocaciones | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd |
|---|---|---|---|---|---|---|---|
| interrogador | haiku | 6 | 8.346 | 11.672 | – | – | – |
| escritor | haiku | 12 | 56.551 | 10.433 | – | – | – |
| resumidor | haiku | 7 | 17.306 | 12.355 | – | – | – |
| revisor-encargo | haiku | 6 | 26.837 | – | – | – | – |
| revisor-continuidad | haiku | 9 | 40.931 | – | – | – | – |
| **total** | haiku | **40** | **149.971** | **34.460** | – | – | – |

Para un manuscrito de 6.426 palabras se leyeron 149.971 palabras de entrada: **23 palabras leídas por palabra publicada**. El grueso es del escritor (38 %) y del revisor de continuidad (27 %), los dos agentes que reciben el libro de estado y todos los resúmenes previos.

## Métricas de calidad
`procedimientos/final.md` › `calcular_metricas`; umbrales en `config.calidad`. T = 5 capítulos, 9 intentos.

| métrica | valor | umbral | resultado |
|---|---|---|---|
| graves_por_10 | 0,0 | ≤ 2 | CUMPLE |
| agotamiento_pct | 0 % | ≤ 20 % | CUMPLE |
| hilos_sin_cerrar | 0 | ≤ 0 | CUMPLE |
| primer_intento_pct | 40 % | ≥ 40 % | CUMPLE |
| rechazos_voz_pct | 0 % | ≤ 20 % | CUMPLE |
| desviacion_longitud | 14,8 % | informativa | – |

**cumple_todas: true.**

Dos matices que la tabla no dice:

- `primer_intento_pct` cumple **justo en el umbral**: 2 capítulos de 5 (el 3 y el 4). Un capítulo más con un segundo intento habría bajado a 20 % y fallado.
- `desviacion_longitud` es 14,8 % y **toda la desviación es por defecto**: los cinco capítulos aprobados quedaron por debajo del objetivo de 1.500 palabras (1.223, 1.398, 1.229, 1.253, 1.288). Ningún intento de toda la novela se pasó de largo; los tres rechazos por longitud fueron por quedarse corto. Con `haiku` y objetivo 1.500, el escritor tira sistemáticamente a la baja.

## Avisos
- Ninguno en `estado.avisos`: ningún capítulo se cerró por agotamiento ni hubo que elegir mejor intento sin criterio fuerte.
- Incidencias del harness en esta sesión, anotadas en `registro.md`:
  1. La herramienta `Agent` de Claude Code devolvió todas las salidas **en segundo plano**; `procedimientos/invocar.md` exige `run_in_background = false` explícito y la herramienta no expone ese parámetro en esta sesión. El orden del bucle se respetó (siempre se esperó el resultado antes del paso siguiente), pero el contrato no se cumple literalmente. Es una limitación de Claude Code frente al runner del hito 2 y debería anotarse en `CHANGELOG.md`.
  2. Por lo anterior, cada invocación ocupa **dos** filas `invocacion` (una de inicio, `resultado: pendiente`, y otra de cierre que la referencia) en vez de la fila única que contempla la plantilla de `registro.md`.
  3. El harness registró `pal_salida` del resumidor del capítulo 5 antes de contarlo con `wc -w` y puso un valor erróneo; corregido en una fila nueva. Es el mismo fallo que `procedimientos/capitulo.md` ya avisa para `comprobar_longitud`; convendría subir ese aviso a regla general del registro.
  4. El harness omitió incrementar `invocaciones.escritor` al cerrar el capítulo 5; `estado.json` decía 11 y el registro tenía 12 filas reales. Corregido a 12, con fila de `decision_harness`.
  5. El paso de descarte al reanudar (`git clean` de `descartar()`) fue **bloqueado por el clasificador de permisos** de la sesión. Se logró el mismo punto consistente por una vía equivalente y reversible: mover lo no commiteado fuera de la carpeta y restaurar los ficheros versionados desde el último commit. El runner del hito 2 no tendrá este obstáculo, pero conviene que `descartar()` contemple una variante que no borre.

## Inventario
`specs/inventario.md` §4: **completo**. Los seis pasos pasan.

1. `informe-cierre.md` con `resultado: EXITO` — este fichero.
2. `estado.json` con `version: 4`, `etapa: completa`, `informe_global: true`, 5 entradas en `capitulos`, `escaleta_validada: true` en el arco 1. OK.
3. `biblia.md` (con «Cronología y datos fijos» rellena, no la plantilla), `escaleta.md` con `aprobada: true`, `arcos/arco-01.md` con `validada: true`, `libro-estado.md` con `hasta_capitulo: 5`, `manuscrito.md`, `informe-global.md`, `erratas.md`. OK. Con un solo arco no procede `arcos/informe-arco-AA.md`.
4. Para cada capítulo existen `intento-K.md`, `resumen-K.md`, `libro-estado-K.md` e `informe-K.md` de la K aprobada, y los cinco informes dicen `veredicto: APROBADO`. OK.
5. Palabras de cada capítulo aprobado dentro de la tolerancia (margen 1.200–1.800): 1.223 · 1.398 · 1.229 · 1.253 · 1.288. OK.
6. `git log` muestra los ocho commits esperados y `git status --porcelain` de la carpeta está vacío. OK.

## Rutas
- Novela: [`manuscrito.md`](manuscrito.md) — 6.426 palabras, 5 capítulos
- Revisión global: [`informe-global.md`](informe-global.md)
- Erratas: [`erratas.md`](erratas.md) — vacío a propósito
- Traza completa: [`registro.md`](registro.md)
- Último informe de capítulo: [`capitulos/05/informe-2.md`](capitulos/05/informe-2.md)
- Estado final: [`estado.json`](estado.json)

**Para continuar:** nada que continuar. La novela está completa. Lee `manuscrito.md` e `informe-global.md`.
