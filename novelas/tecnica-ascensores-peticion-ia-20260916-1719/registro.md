# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-16 17:19 | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: nueva · perfil: relato · sobreescrituras: limites.pausa_cada_capitulos=null · flags: modo-prueba pruebas/referencia |
| 2026-09-16 17:19 | entrevista_cerrada | interrogatorio | – | – | – | – | – | – | – | – | – | origen: pruebas/referencia/entrevista.md |
| 2026-09-16 17:21 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | – | – | – | – | interrogador · modo propuesta · intento tecnico 1 · resultado: incumple · motivo: escaleta.md declara tres arcos con el mismo n:1 (1-2, 3-4, 5-5) y contradice arcos/arco-01.md (desde 1, hasta 5); con 5 capitulos y capitulos_por_arco 15 debe haber un unico arco |
| 2026-09-16 17:21 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | reintento 1/3: arcos duplicados en escaleta.md |
| 2026-09-16 17:30 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | 3600 | – | – | – | interrogador · modo propuesta · intento tecnico 2 · resultado: ok · biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-16 17:31 | invocacion | interrogatorio | 1 | – | – | haiku | 3234 | – | – | – | – | revisor-continuidad · modo canon · intento tecnico 1 · resultado: ok |
| 2026-09-16 17:31 | veredicto | interrogatorio | 1 | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad max 1 · origen: revisor-continuidad |
| 2026-09-16 17:31 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | reescribir propuesta (vuelta 1/3) · CANON: la escaleta situa el final en el cuarto piso y el canon solo declara planta baja, 1a, 2a y 3a |
| 2026-09-16 17:31 | paso_descartado | interrogatorio | 1 | – | – | – | – | – | – | – | – | descartados los borradores sin commitear: biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-16 17:36 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | – | – | – | – | interrogador · modo propuesta (vuelta 1) · intento tecnico 1 · resultado: incumple · motivo: escaleta.md vuelve a declarar tres arcos con el mismo n:1 (1-2, 3-4, 5-5) y contradice arcos/arco-01.md (desde 1, hasta 5); el canon si quedo corregido |
| 2026-09-16 17:36 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | reintento 1/3: arcos duplicados en escaleta.md (regresion respecto a la vuelta 0) |
| 2026-09-16 17:38 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | – | – | – | – | interrogador · modo propuesta (vuelta 1) · intento tecnico 2 · resultado: incumple · motivo: el mensaje final describe la propuesta pero no contiene ningun bloque === ARCHIVO: … === / === FIN === |
| 2026-09-16 17:38 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | reintento 2/3: salida sin bloques |
| 2026-09-16 17:45 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | 4361 | – | – | – | interrogador · modo propuesta (vuelta 1) · intento tecnico 3 · resultado: ok · biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-16 17:46 | invocacion | interrogatorio | 1 | – | – | haiku | 2650 | – | – | – | – | revisor-continuidad · modo canon · intento tecnico 1 · resultado: ok · observacion: el JSON vino envuelto en valla de codigo, se acepto quitandola |
| 2026-09-16 17:46 | veredicto | interrogatorio | 1 | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad max 1 · origen: revisor-continuidad |
| 2026-09-16 17:46 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | reescribir propuesta (vuelta 2/3) · CANON: la fila del edificio declara 5 plantas + planta baja (6 niveles) y su consecuencia enumera PB + 1a + 2a + 3a + 4a (5 niveles) |
| 2026-09-16 17:46 | paso_descartado | interrogatorio | 1 | – | – | – | – | – | – | – | – | descartados los borradores sin commitear: biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-16 17:53 | invocacion | interrogatorio | 1 | – | – | haiku | 1391 | 3711 | – | – | – | interrogador · modo propuesta (vuelta 2) · intento tecnico 1 · resultado: ok · observacion: acto del arco vale "planteamiento, nudo y desenlace" en vez de uno de los tres; se acepta porque el arco unico cubre los tres y estos aparecen en Estructura |
| 2026-09-16 17:53 | paso_descartado | interrogatorio | 1 | – | – | – | – | – | – | – | – | primera escritura de la vuelta 2 descartada: el harness habia corregido texto del agente (titulo del cap 5, dia de la semana, erratas); reescrita fiel a la salida |
| 2026-09-16 17:56 | invocacion | interrogatorio | 1 | – | – | haiku | 2458 | – | – | – | – | revisor-continuidad · modo canon · intento tecnico 1 · resultado: ok |
| 2026-09-16 17:56 | veredicto | interrogatorio | 1 | – | – | – | – | – | – | – | – | CANON · APROBADO · 0 problemas · origen: revisor-continuidad |
| 2026-09-16 17:56 | propuesta_cierre | interrogatorio | 1 | – | – | – | – | – | – | – | – | Corrosion · 5 capitulos · 1 arco |
| 2026-09-16 17:56 | decision_usuario | interrogatorio | 1 | – | – | – | – | – | – | – | – | confirma (auto, modo prueba) |
| 2026-09-16 17:58 | escaleta_validada | interrogatorio | 1 | – | – | – | – | – | – | – | – | biblia.md y escaleta.md aprobadas; arcos/arco-01.md validada |
| 2026-09-16 18:01 | invocacion | capitulos | 1 | 01 | 1 | haiku | 3927 | – | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: incumple · motivo: el bloque abre con === ARCHIVO: capitulos/01/intento-1.md === pero no se cierra con === FIN === |
| 2026-09-16 18:01 | decision_harness | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | reintento 1/3: falta el delimitador de cierre |
| 2026-09-16 18:03 | invocacion | capitulos | 1 | 01 | 1 | haiku | 3927 | – | – | – | – | escritor · modo capitulo · intento tecnico 2 · resultado: incumple · motivo: el mensaje final describe el capitulo y afirma haberlo entregado, pero no contiene ningun bloque === ARCHIVO: … === |
| 2026-09-16 18:03 | decision_harness | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | reintento 2/3: salida sin bloques (mismo patron que el interrogador en el interrogatorio) |
| 2026-09-16 18:05 | invocacion | capitulos | 1 | 01 | 1 | haiku | 3927 | 1012 | – | – | – | escritor · modo capitulo · intento tecnico 3 · resultado: ok · capitulos/01/intento-1.md |
| 2026-09-16 18:05 | longitud | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | rechazo · 1012 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:05 | veredicto | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | RECHAZADO · 1 problema · gravedad max 3 · origen: harness |
| 2026-09-16 18:05 | decision_harness | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | ajuste_longitud 1/2 -> intento 2 · no consume reescritura |
| 2026-09-16 18:07 | invocacion | capitulos | 1 | 01 | 2 | haiku | 4939 | 1229 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/01/intento-2.md |
| 2026-09-16 18:07 | longitud | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | ok · 1229 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:09 | invocacion | capitulos | 1 | 01 | 2 | haiku | 1828 | – | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: incumple · motivo: el mensaje final describe los dos documentos ("listos para escribir en disco") pero no contiene ningun bloque === ARCHIVO: … === |
| 2026-09-16 18:09 | decision_harness | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | reintento 1/3: salida sin bloques (tercer agente distinto con el mismo patron) |
| 2026-09-16 18:11 | invocacion | capitulos | 1 | 01 | 2 | haiku | 1828 | 924 | – | – | – | resumidor · modo capitulo · intento tecnico 2 · resultado: ok · capitulos/01/resumen-2.md, capitulos/01/libro-estado-2.md |
| 2026-09-16 18:13 | invocacion | capitulos | 1 | 01 | 2 | haiku | 4940 | – | – | – | – | revisor-encargo · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas · observacion: JSON en valla de codigo |
| 2026-09-16 18:13 | invocacion | capitulos | 1 | 01 | 2 | haiku | 3487 | – | – | – | – | revisor-continuidad · modo capitulo · intento tecnico 1 · resultado: ok · RECHAZADO, 1 problema · observacion: JSON en valla de codigo |
| 2026-09-16 18:13 | veredicto | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | RECHAZADO · 1 problema · gravedad max 1 · origen: revisores · desglose: continuidad 1, encargo 0 |
| 2026-09-16 18:13 | discrepancia_veredicto | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | revisor: encargo · suyo: APROBADO · harness: RECHAZADO |
| 2026-09-16 18:13 | decision_harness | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | reescribir 1/2 -> intento 3 · rechazo de contenido |
| 2026-09-16 18:15 | invocacion | capitulos | 1 | 01 | 3 | haiku | 5412 | 1223 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/01/intento-3.md |
| 2026-09-16 18:15 | longitud | capitulos | 1 | 01 | 3 | – | – | – | – | – | – | ok · 1223 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:17 | invocacion | capitulos | 1 | 01 | 3 | haiku | 1822 | 1001 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/01/resumen-3.md, capitulos/01/libro-estado-3.md |
| 2026-09-16 18:20 | invocacion | capitulos | 1 | 01 | 3 | haiku | 4934 | – | – | – | – | revisor-encargo · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:20 | invocacion | capitulos | 1 | 01 | 3 | haiku | 3563 | – | – | – | – | revisor-continuidad · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:20 | veredicto | capitulos | 1 | 01 | 3 | – | – | – | – | – | – | APROBADO · 0 problemas · origen: revisores · desglose: continuidad 0, encargo 0 |
| 2026-09-16 18:20 | decision_harness | capitulos | 1 | 01 | 3 | – | – | – | – | – | – | aprobar |
| 2026-09-16 18:22 | invocacion | capitulos | 1 | 02 | 1 | haiku | 5935 | 980 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/02/intento-1.md |
| 2026-09-16 18:22 | longitud | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | rechazo · 980 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:22 | veredicto | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | RECHAZADO · 1 problema · gravedad max 3 · origen: harness |
| 2026-09-16 18:22 | decision_harness | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | ajuste_longitud 1/2 -> intento 2 · no consume reescritura |
| 2026-09-16 18:23 | invocacion | capitulos | 1 | 02 | 2 | haiku | – | – | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: incumple · motivo: el mensaje final describe la ampliacion ("ampliado de 980 a 1487 palabras") pero no contiene ningun bloque === ARCHIVO: … === |
| 2026-09-16 18:23 | decision_harness | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | reintento 1/3: salida sin bloques (5a vez en la ejecucion) |
| 2026-09-16 18:26 | invocacion | capitulos | 1 | 02 | 2 | haiku | 3900 | 1398 | – | – | – | escritor · modo capitulo · intento tecnico 2 · resultado: ok · capitulos/02/intento-2.md |
| 2026-09-16 18:26 | longitud | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | ok · 1398 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:30 | invocacion | capitulos | 1 | 02 | 2 | haiku | 2100 | 1689 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: ok · observacion: el delimitador de cierre del segundo bloque llego como === FIN ===" con una comilla sobrante |
| 2026-09-16 18:32 | invocacion | capitulos | 1 | 02 | 2 | haiku | 3600 | – | – | – | – | revisor-encargo · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:32 | invocacion | capitulos | 1 | 02 | 2 | haiku | 4300 | – | – | – | – | revisor-continuidad · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:32 | veredicto | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | APROBADO · 0 problemas · origen: revisores · desglose: continuidad 0, encargo 0 |
| 2026-09-16 18:32 | decision_harness | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | aprobar |
| 2026-09-16 18:34 | invocacion | capitulos | 1 | 03 | 1 | haiku | 5400 | 1229 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/03/intento-1.md |
| 2026-09-16 18:34 | longitud | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | ok · 1229 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 18:37 | invocacion | capitulos | 1 | 03 | 1 | haiku | 2700 | 2048 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/03/resumen-1.md, capitulos/03/libro-estado-1.md |
| 2026-09-16 18:39 | invocacion | capitulos | 1 | 03 | 1 | haiku | 3400 | – | – | – | – | revisor-encargo · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:39 | invocacion | capitulos | 1 | 03 | 1 | haiku | 5500 | – | – | – | – | revisor-continuidad · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-16 18:39 | veredicto | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | APROBADO · 0 problemas · origen: revisores · desglose: continuidad 0, encargo 0 |
| 2026-09-16 18:39 | decision_harness | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | aprobar |
| 2026-09-17 11:20 | paso_descartado | capitulos | 1 | 04 | – | – | – | – | – | – | – | reanudar: carpeta con un paso a medias · descartadas capitulos/04/intento-1.md, capitulos/04/informe-1.md, capitulos/04/intento-2.md y los cambios sin commitear de estado.json y registro.md · vuelta al commit 1cd7b16 (cap 03 cerrado) · copia de seguridad fuera del harness en el scratchpad de la sesion |
| 2026-09-17 11:21 | inicio_ejecucion | capitulos | 1 | 04 | 1 | – | – | – | – | – | – | comando: continuar · perfil: relato · sobreescrituras: ninguna · flags: ninguno |
| 2026-09-17 11:21 | invocacion | capitulos | 1 | 04 | 1 | haiku | 8257 | – | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: pendiente |
| 2026-09-17 11:24 | invocacion | capitulos | 1 | 04 | 1 | haiku | 8257 | 1253 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/04/intento-1.md · cierra la fila 'pendiente' de las 11:21 (la herramienta Agent de Claude Code devolvio la salida en segundo plano; no expone run_in_background) |
| 2026-09-17 11:24 | longitud | capitulos | 1 | 04 | 1 | – | – | – | – | – | – | ok · 1253 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-17 11:24 | invocacion | capitulos | 1 | 04 | 1 | haiku | 3012 | – | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: pendiente |
| 2026-09-17 11:27 | invocacion | capitulos | 1 | 04 | 1 | haiku | 3012 | 3201 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado: ok · capitulos/04/resumen-1.md, capitulos/04/libro-estado-1.md · libro de estado 2345 palabras (max 4000, sin aviso) · cierra la fila 'pendiente' de las 11:24 |
| 2026-09-17 11:31 | invocacion | capitulos | 1 | 04 | 1 | haiku | 4964 | – | – | – | – | revisor-encargo · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-17 11:31 | invocacion | capitulos | 1 | 04 | 1 | haiku | 7042 | – | – | – | – | revisor-continuidad · modo capitulo · intento tecnico 1 · resultado: ok · APROBADO, 0 problemas |
| 2026-09-17 11:31 | veredicto | capitulos | 1 | 04 | 1 | – | – | – | – | – | – | APROBADO · 0 problemas · origen: revisores · desglose: continuidad 0, encargo 0 |
| 2026-09-17 11:31 | decision_harness | capitulos | 1 | 04 | 1 | – | – | – | – | – | – | aprobar |
