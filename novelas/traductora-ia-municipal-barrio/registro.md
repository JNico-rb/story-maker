# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el orquestador. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (subagente, modelo, intento técnico, resultado ok/fallo/incumple) · `propuesta_cierre` · `decision_usuario` · `veredicto` (veredicto, nº problemas, gravedad máx.) · `discrepancia_veredicto` · `decision_harness` (aprobar / reescribir / aceptar_por_agotamiento / reintento / escaleta_fuera_limites / parada) · `escritura_fuera_de_zona` · `paso_descartado` · `commit` · `fin_ejecucion`.

Las columnas `modelo`, `pal_entrada` y `pal_salida` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y palabras de lo que entregó (recuento aproximado). Son el dato de volumen con el que se estima el coste en otro modelo o en el runner.

| fecha-hora | evento | fase | cap | intento | modelo | pal_entrada | pal_salida | detalle |
|---|---|---|---|---|---|---|---|---|
| 2026-09-15 17:49 | inicio_ejecucion | interrogatorio | – | – | | | | comando: nueva; perfil relato; sobreescrituras palabras_por_capitulo=350, palabras_min=200, palabras_max=600 |
| 2026-09-15 17:49 | commit | interrogatorio | – | – | | | | carpeta creada |
| 2026-09-15 17:52 | entrevista_cerrada | interrogatorio | – | – | | | | 12 preguntas en 3 rondas (grilling); todas las recomendaciones aceptadas; ruta: entrevista.md |
| 2026-09-15 17:52 | invocacion | interrogatorio | – | – | opus | 777 | | interrogador, intento técnico 1, inicio |
| 2026-09-15 17:55 | invocacion | interrogatorio | – | – | opus | 777 | 2844 | interrogador, intento técnico 1, resultado ok; zona correcta (biblia.md, escaleta.md) |
| 2026-09-15 17:55 | propuesta_cierre | interrogatorio | – | – | | | | 3 caps × 350 palabras; título "Lo que dice el expediente"; validación escaleta ok |
| 2026-09-15 17:56 | decision_usuario | interrogatorio | – | – | | | | confirma biblia y escaleta sin cambios |
| 2026-09-15 17:56 | commit | interrogatorio | – | – | | | | escaleta aprobada |
| 2026-09-15 17:56 | invocacion | capitulos | 1 | 1 | opus | 2844 | | escritor, intento técnico 1, inicio |
| 2026-09-15 17:58 | invocacion | capitulos | 1 | 1 | opus | 2844 | 1045 | escritor, intento técnico 1, resultado ok; zona correcta; intento-1.md 362 palabras |
| 2026-09-15 17:58 | invocacion | capitulos | 1 | 1 | opus | 3889 | | revisor, intento técnico 1, inicio |
| 2026-09-15 18:00 | invocacion | capitulos | 1 | 1 | opus | 3889 | 210 | revisor, intento técnico 1, resultado ok; sin ficheros escritos |
| 2026-09-15 18:00 | veredicto | capitulos | 1 | 1 | | | | APROBADO; 1 problema; gravedad máx 5; recalculado coincide con revisor; informe: capitulos/01/informe-1.md |
| 2026-09-15 18:00 | decision_harness | capitulos | 1 | 1 | | | | aprobar |
| 2026-09-15 18:00 | commit | capitulos | 1 | 1 | | | | cap 01 cerrado (intento 1) |
| 2026-09-15 18:00 | invocacion | capitulos | 2 | 1 | opus | 3889 | | escritor, intento técnico 1, inicio |
| 2026-09-15 18:01 | invocacion | capitulos | 2 | 1 | opus | 3889 | 1133 | escritor, intento técnico 1, resultado ok; zona correcta; intento-1.md 356 palabras |
| 2026-09-15 18:01 | invocacion | capitulos | 2 | 1 | opus | 4633 | | revisor, intento técnico 1, inicio |
| 2026-09-15 18:03 | invocacion | capitulos | 2 | 1 | opus | 4633 | 330 | revisor, intento técnico 1, resultado ok; sin ficheros escritos |
| 2026-09-15 18:03 | veredicto | capitulos | 2 | 1 | | | | RECHAZADO; 1 problema; gravedad máx 1; recalculado coincide; informe: capitulos/02/informe-1.md |
| 2026-09-15 18:03 | decision_harness | capitulos | 2 | 1 | | | | reescribir → intento 2 |
| 2026-09-15 18:03 | invocacion | capitulos | 2 | 2 | opus | 4587 | | escritor, intento técnico 1, inicio (reescritura) |
| 2026-09-15 18:05 | invocacion | capitulos | 2 | 2 | opus | 4587 | 1218 | escritor, intento técnico 1, resultado ok; zona correcta; intento-2.md 359 palabras |
| 2026-09-15 18:05 | invocacion | capitulos | 2 | 2 | opus | 5047 | | revisor, intento técnico 1, inicio |
| 2026-09-15 18:07 | invocacion | capitulos | 2 | 2 | opus | 5047 | 380 | revisor, intento técnico 1, resultado ok; sin ficheros escritos |
| 2026-09-15 18:07 | veredicto | capitulos | 2 | 2 | | | | APROBADO; 0 problemas; recalculado coincide; informe: capitulos/02/informe-2.md |
| 2026-09-15 18:07 | decision_harness | capitulos | 2 | 2 | | | | aprobar |
| 2026-09-15 18:07 | commit | capitulos | 2 | 2 | | | | cap 02 cerrado (intento 2) |
| 2026-09-15 18:07 | invocacion | capitulos | 3 | 1 | opus | 4718 | | escritor, intento técnico 1, inicio |
| 2026-09-15 18:09 | invocacion | capitulos | 3 | 1 | opus | 4718 | 1221 | escritor, intento técnico 1, resultado ok; zona correcta; intento-1.md 402 palabras |
| 2026-09-15 18:09 | invocacion | capitulos | 3 | 1 | opus | 5550 | | revisor, intento técnico 1, inicio |
| 2026-09-15 18:11 | invocacion | capitulos | 3 | 1 | opus | 5550 | 400 | revisor, intento técnico 1, resultado ok; sin ficheros escritos |
| 2026-09-15 18:11 | veredicto | capitulos | 3 | 1 | | | | APROBADO; 0 problemas; recalculado coincide; informe: capitulos/03/informe-1.md |
| 2026-09-15 18:11 | decision_harness | capitulos | 3 | 1 | | | | aprobar |
