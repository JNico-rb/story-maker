# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el orquestador. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (subagente, modelo, intento técnico, resultado ok/fallo/incumple) · `propuesta_cierre` · `decision_usuario` · `veredicto` (veredicto, nº problemas, gravedad máx.) · `discrepancia_veredicto` · `decision_harness` (aprobar / reescribir / aceptar_por_agotamiento / reintento / escaleta_fuera_limites / parada) · `escritura_fuera_de_zona` · `paso_descartado` · `commit` · `fin_ejecucion`.

Las columnas `modelo`, `pal_entrada` y `pal_salida` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y palabras de lo que entregó (recuento aproximado). Son el dato de volumen con el que se estima el coste en otro modelo o en el runner.

| fecha-hora | evento | fase | cap | intento | modelo | pal_entrada | pal_salida | detalle |
|---|---|---|---|---|---|---|---|---|
| 2026-09-15 17:49 | inicio_ejecucion | interrogatorio | – | – | | | | comando: nueva; perfil relato; sobreescrituras palabras_por_capitulo=350, palabras_min=200, palabras_max=600 |
