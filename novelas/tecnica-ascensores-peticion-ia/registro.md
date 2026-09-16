# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen) · `discrepancia_veredicto` · `decision_harness` (aprobar / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `paso_descartado` · `commit` · `fin_ejecucion`.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-16 10:38 | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: `nueva modo-prueba: pruebas/referencia limites.pausa_cada_capitulos=null` · perfil: relato · sobreescrituras: limites.pausa_cada_capitulos=null · flags: modo-prueba=pruebas/referencia |
| 2026-09-16 10:38 | commit | interrogatorio | – | – | – | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: carpeta creada |
| 2026-09-16 10:39 | entrevista_cerrada | interrogatorio | – | – | – | – | – | – | – | – | – | origen: fichero (pruebas/referencia/entrevista.md) · modo de prueba |
| 2026-09-16 10:47 | invocacion | interrogatorio | 1 | – | – | opus | 1201 | 4378 | – | – | – | interrogador · modo propuesta · intento tecnico 1 · resultado ok · destinos: biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-16 10:47 | propuesta_cierre | interrogatorio | 1 | – | – | – | – | – | – | – | – | titulo: Contrapeso · 5 capitulos · 1 arco |
| 2026-09-16 10:47 | decision_usuario | interrogatorio | 1 | – | – | – | – | – | – | – | – | confirma (auto, modo prueba) |
| 2026-09-16 10:47 | escaleta_validada | interrogatorio | 1 | – | – | – | – | – | – | – | – | arco 1, capitulos 1-5 (llego con la propuesta) |
| 2026-09-16 10:47 | commit | capitulos | 1 | – | – | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: escaleta aprobada |
| 2026-09-16 10:49 | invocacion | capitulos | 1 | 01 | 1 | opus | 4594 | 1500 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado ok · destino: capitulos/01/intento-1.md |
| 2026-09-16 10:49 | longitud | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | ok · 1500 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 10:53 | invocacion | capitulos | 1 | 01 | 1 | opus | 2099 | 2757 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado ok · destinos: capitulos/01/resumen-1.md, capitulos/01/libro-estado-1.md |
| 2026-09-16 10:55 | invocacion | capitulos | 1 | 01 | 1 | opus | 7500 | – | – | – | – | revisor · modo capitulo · intento tecnico 1 · resultado ok · informe escrito por el harness |
| 2026-09-16 10:55 | veredicto | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | RECHAZADO · 3 problemas (1 grave, 2 leves) · gravedad max 1 · origen revisor · sin discrepancia |
| 2026-09-16 10:55 | decision_harness | capitulos | 1 | 01 | 1 | – | – | – | – | – | – | reescribir → intento 2 (K=1 <= reescrituras_max=2) |
| 2026-09-16 10:58 | invocacion | capitulos | 1 | 01 | 2 | opus | 6990 | 1613 | – | – | – | escritor · modo capitulo (reescritura) · intento tecnico 1 · resultado ok · observacion: texto de preambulo fuera de los bloques, ignorado |
| 2026-09-16 10:58 | longitud | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | ok · 1613 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 11:02 | invocacion | capitulos | 1 | 01 | 2 | opus | 2212 | 3159 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado ok · destinos: capitulos/01/resumen-2.md, capitulos/01/libro-estado-2.md |
| 2026-09-16 11:05 | invocacion | capitulos | 1 | 01 | 2 | opus | 9150 | – | – | – | – | revisor · modo capitulo · intento tecnico 1 · resultado ok · informe escrito por el harness |
| 2026-09-16 11:05 | veredicto | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | APROBADO · 1 problema (0 graves, 1 leve) · gravedad max 5 · origen revisor · sin discrepancia |
| 2026-09-16 11:05 | decision_harness | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | aprobar · libro-estado.md adoptado de capitulos/01/libro-estado-2.md |
| 2026-09-16 11:06 | commit | capitulos | 1 | 01 | 2 | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: cap 01 cerrado (intento 2) |
| 2026-09-16 12:18 | paso_descartado | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | reanudar con la carpeta sucia · perdido: capitulos/02/intento-1.md (1333 palabras, sin commitear) y filas de registro.md posteriores al ultimo commit |
| 2026-09-16 12:18 | inicio_ejecucion | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | comando: continuar novelas/tecnica-ascensores-peticion-ia · perfil relato · sin sobreescrituras · sin flags |
| 2026-09-16 12:18 | invocacion | capitulos | 1 | 02 | 1 | opus | 9150 | – | – | – | – | escritor · modo capitulo · intento tecnico 1 · en curso · destino: capitulos/02/intento-1.md |
| 2026-09-16 12:21 | invocacion | capitulos | 1 | 02 | 1 | opus | 9150 | 1433 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado ok · destino: capitulos/02/intento-1.md (cierra la fila "en curso" anterior) |
| 2026-09-16 12:21 | longitud | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | ok · 1433 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 12:26 | invocacion | capitulos | 1 | 02 | 1 | opus | 3429 | 4237 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado ok · destinos: capitulos/02/resumen-1.md, capitulos/02/libro-estado-1.md |
| 2026-09-16 12:29 | invocacion | capitulos | 1 | 02 | 1 | opus | 10716 | – | – | – | – | revisor · modo capitulo · intento tecnico 1 · resultado ok · informe escrito por el harness |
| 2026-09-16 12:29 | veredicto | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | RECHAZADO · 3 problemas (1 grave, 2 leves) · gravedad max 1 · origen revisor · sin discrepancia |
| 2026-09-16 12:29 | decision_harness | capitulos | 1 | 02 | 1 | – | – | – | – | – | – | reescribir → intento 2 (K=1 <= reescrituras_max=2) |
| 2026-09-16 12:31 | invocacion | capitulos | 1 | 02 | 2 | opus | 11644 | 1474 | – | – | – | escritor · modo capitulo (reescritura) · intento tecnico 1 · resultado ok · destino: capitulos/02/intento-2.md |
| 2026-09-16 12:31 | longitud | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | ok · 1474 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 12:35 | invocacion | capitulos | 1 | 02 | 2 | opus | 3470 | 4123 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado ok · destinos: capitulos/02/resumen-2.md, capitulos/02/libro-estado-2.md |
| 2026-09-16 12:37 | invocacion | capitulos | 1 | 02 | 2 | opus | 10726 | – | – | – | – | revisor · modo capitulo · intento tecnico 1 · resultado ok · informe escrito por el harness |
| 2026-09-16 12:37 | veredicto | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | APROBADO · 1 problema (0 graves, 1 leve) · gravedad max 5 · origen revisor · sin discrepancia |
| 2026-09-16 12:37 | decision_harness | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | aprobar · libro-estado.md adoptado de capitulos/02/libro-estado-2.md |
| 2026-09-16 12:38 | commit | capitulos | 1 | 02 | 2 | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: cap 02 cerrado (intento 2) |
| 2026-09-16 12:40 | invocacion | capitulos | 1 | 03 | 1 | opus | 11521 | 1660 | – | – | – | escritor · modo capitulo · intento tecnico 1 · resultado ok · destino: capitulos/03/intento-1.md |
| 2026-09-16 12:40 | longitud | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | ok · 1660 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 12:46 | invocacion | capitulos | 1 | 03 | 1 | opus | 4451 | 5200 | – | – | – | resumidor · modo capitulo · intento tecnico 1 · resultado ok · destinos: capitulos/03/resumen-1.md, capitulos/03/libro-estado-1.md |
| 2026-09-16 12:49 | invocacion | capitulos | 1 | 03 | 1 | opus | 13909 | – | – | – | – | revisor · modo capitulo · intento tecnico 1 · resultado ok · informe escrito por el harness |
| 2026-09-16 12:49 | veredicto | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | RECHAZADO · 3 problemas (1 grave, 2 leves) · gravedad max 1 · origen revisor · sin discrepancia |
| 2026-09-16 12:49 | decision_harness | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | reescribir → intento 2 (K=1 <= reescrituras_max=2) |
| 2026-09-16 12:53 | invocacion | capitulos | 1 | 03 | 2 | opus | 14146 | 1940 | – | – | – | escritor · modo capitulo (reescritura) · intento tecnico 1 · resultado ok · destino: capitulos/03/intento-2.md |
| 2026-09-16 12:53 | longitud | capitulos | 1 | 03 | 2 | – | – | – | – | – | – | ok · 1940 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 12:53 | longitud | capitulos | 1 | 03 | 2 | – | – | – | – | – | – | CORRIGE la fila anterior de este intento: rechazo · 1940 palabras · objetivo 1500 · margen 1200-1800 (la fila previa marcaba ok por error del harness al registrar antes de comparar) |
| 2026-09-16 12:53 | veredicto | capitulos | 1 | 03 | 2 | – | – | – | – | – | – | RECHAZADO · 1 problema (0 graves, 1 leve) · gravedad max 3 · origen harness |
| 2026-09-16 12:53 | decision_harness | capitulos | 1 | 03 | 2 | – | – | – | – | – | – | reescribir → intento 3 (K=2 <= reescrituras_max=2) |
| 2026-09-16 12:56 | invocacion | capitulos | 1 | 03 | 3 | opus | 14146 | 1879 | – | – | – | escritor · modo capitulo (reescritura) · intento tecnico 1 · resultado ok · destino: capitulos/03/intento-3.md |
| 2026-09-16 12:56 | longitud | capitulos | 1 | 03 | 3 | – | – | – | – | – | – | rechazo · 1879 palabras · objetivo 1500 · margen 1200-1800 |
| 2026-09-16 12:56 | veredicto | capitulos | 1 | 03 | 3 | – | – | – | – | – | – | RECHAZADO · 1 problema (0 graves, 1 leve) · gravedad max 3 · origen harness |
| 2026-09-16 12:56 | decision_harness | capitulos | 1 | 03 | 3 | – | – | – | – | – | – | aceptar_por_agotamiento (K=3 > reescrituras_max=2) |
| 2026-09-16 12:56 | decision_harness | capitulos | 1 | 03 | 3 | – | – | – | – | – | – | mejor_intento = 1 · motivo: los intentos 2 y 3 fueron rechazados por longitud (origen harness) y el 1 llego al revisor (regla SKILL.md 4.2, paso 1) |
| 2026-09-16 12:56 | decision_harness | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | cerrar por agotamiento con intento 1 · libro-estado.md adoptado de capitulos/03/libro-estado-1.md |
| 2026-09-16 12:57 | commit | capitulos | 1 | 03 | 1 | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: cap 03 cerrado (intento 1) |
