# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen) · `discrepancia_veredicto` · `decision_harness` (aprobar / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `paso_descartado` · `commit` · `fin_ejecucion`.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-16 10:38 | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: `nueva modo-prueba: pruebas/referencia limites.pausa_cada_capitulos=null` · perfil: relato · sobreescrituras: limites.pausa_cada_capitulos=null · flags: modo-prueba=pruebas/referencia |
| 2026-09-16 10:38 | commit | interrogatorio | – | – | – | – | – | – | – | – | – | novela tecnica-ascensores-peticion-ia: carpeta creada |
