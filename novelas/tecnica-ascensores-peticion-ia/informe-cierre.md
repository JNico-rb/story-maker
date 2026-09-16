---
resultado: "EXITO"
motivo: "EXITO"
fecha: "2026-09-16"
etapa: "completa"
arco: 1
capitulo: 5
intento: 2
cumple_todas: false
---

# Informe de cierre — tecnica-ascensores-peticion-ia

**Resultado:** ÉXITO
**Motivo:** EXITO
**Detalle:** Novela completa: cinco capítulos cerrados, manuscrito ensamblado y revisión global hecha sobre el texto completo. Dos capítulos se cerraron por agotamiento de reescrituras y conservan problemas de continuidad sin corregir; las métricas de calidad no se cumplen.

## Dónde se detuvo
Etapa `completa` · arco 1 de 1 · capítulo 5 de 5 · intento 2 (aceptado por agotamiento).

## Qué quedó completado
- Escaleta aprobada: sí (5 capítulos en 1 arco).
- Arcos detallados / revisados: 1 / — (con un solo arco, la revisión de arco y la global son la misma pasada; se hizo solo la global, según SKILL.md §3).
- Capítulos cerrados: 5 de 5. Por agotamiento: 2 (capítulos 3 y 5).
- Informe global: sí (base: manuscrito).

## Invocaciones
interrogador 1 · escritor 13 · resumidor 11 · revisor 12. Total: 37.
Reintentos técnicos: 0. Discrepancias de veredicto: 0. Rechazos por longitud: 2 (capítulo 3, intentos 2 y 3).

## Volumen
Suma de las filas `invocacion` del registro. `tok_*` y `coste_usd` no los devuelve la herramienta en el hito 1.

| agente | modelo | invocaciones | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd |
|---|---|---|---|---|---|---|---|
| interrogador | opus | 1 | 1.201 | 4.378 | – | – | – |
| escritor | opus | 13 | 175.907 | 21.544 | – | – | – |
| resumidor | opus | 11 | 46.217 | 51.144 | – | – | – |
| revisor | opus | 12 | 180.402 | — | – | – | – |
| **total** | | **37** | **403.727** | **77.066** | – | – | – |

El revisor no escribe ficheros: su salida es el JSON que el harness convierte en informe, de ahí la columna vacía.

## Métricas de calidad

| métrica | valor | umbral | resultado |
|---|---|---|---|
| graves_por_10 | 8,0 | ≤ 1 | NO CUMPLE |
| agotamiento_pct | 40 % | ≤ 10 % | NO CUMPLE |
| hilos_sin_cerrar | 1 | ≤ 0 | NO CUMPLE |
| primer_intento_pct | 0 % | ≥ 60 % | NO CUMPLE |
| rechazos_voz_pct | 15,4 % | ≤ 10 % | NO CUMPLE |
| desviacion_longitud | 9,3 % | informativa | – |

`cumple_todas`: **false** (0 de 5 métricas con umbral).

Detalle del cálculo:
- **graves_por_10**: 4 problemas de gravedad 1 en `informe-global.md` ÷ 5 capítulos × 10.
- **agotamiento_pct**: capítulos 3 y 5 de 5.
- **hilos_sin_cerrar**: «Reme y el vecindario», que la escaleta cierra en el capítulo 5 y que el libro de estado vigente conserva abierto («Pablo lo cuenta en el grupo del barrio», «La junta del miércoles y la vecina del segundo»).
- **primer_intento_pct**: ningún capítulo se aprobó en el intento 1 sin agotamiento (el capítulo 3 quedó en el intento 1, pero por agotamiento).
- **rechazos_voz_pct**: 2 intentos con problemas de gravedad 4 (`capitulos/01/informe-1.md`, `capitulos/03/informe-1.md`) ÷ 13 intentos.
- **desviacion_longitud**: media de |palabras − 1.500| ÷ 1.500 sobre los cinco intentos aprobados (1.613, 1.474, 1.660, 1.661, 1.737).

## Avisos
- Capítulo 3 aceptado por agotamiento (mejor intento: 1 de 3); ver `capitulos/03/informe-1.md`.
- Capítulo 3: los intentos 2 y 3 se perdieron por longitud (1.940 y 1.879 palabras sobre un máximo de 1.800), de modo que el problema de gravedad 1 del intento 1 —la cronología de «dos semanas»— quedó sin corregir en el texto cerrado.
- Capítulo 5 aceptado por agotamiento (mejor intento: 2 de 3); ver `capitulos/05/informe-2.md`.
- Capítulo 5: la regla de mejor intento (§4.2) eligió el intento 2, cuyo único problema es no cerrar el hilo «Reme y el vecindario». El intento 3 sí lo cerraba, pero tenía un problema de gravedad 1 y dos en total, y perdió el desempate.
- Tensión de canon heredada: el libro de estado fija que Julia Bandrés dio a Reme la llave del foso en 2011, mientras la biblia da a Reme 52 años y 26 de oficio (inicio hacia 2023).
- Sin fijar: el número de paradas del ascensor del nº 38 («tres alturas» con vecinos del primero al cuarto).
- El recuento de invocaciones de `estado.json` se desincronizó durante la ejecución y se recalculó desde `registro.md` al cerrar.

## Inventario
Completo: `idea.md`, `entrevista.md`, `config.json`, `estado.json`, `registro.md`, `biblia.md`, `escaleta.md`, `arcos/arco-01.md`, `libro-estado.md`, `manuscrito.md`, `informe-global.md`, `informe-cierre.md`, y para cada capítulo sus `intento-K.md`, `resumen-K.md`, `libro-estado-K.md` e `informe-K.md`. No hay informe de arco, por la regla de arco único.

## Rutas
- `novelas/tecnica-ascensores-peticion-ia/manuscrito.md` — la novela (8.271 palabras).
- `novelas/tecnica-ascensores-peticion-ia/informe-global.md` — continuidad de la novela entera.
- `novelas/tecnica-ascensores-peticion-ia/registro.md` — trazas de toda la ejecución.
- `capitulos/03/informe-1.md` y `capitulos/05/informe-2.md` — los dos cierres por agotamiento.

**Para continuar:** nada que continuar; la novela está completa.
