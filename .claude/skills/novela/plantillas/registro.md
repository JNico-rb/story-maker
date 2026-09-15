# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el orquestador. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (subagente, modelo, intento técnico, resultado ok/fallo/incumple) · `propuesta_cierre` · `decision_usuario` · `veredicto` (veredicto, nº problemas, gravedad máx.) · `discrepancia_veredicto` · `decision_harness` (aprobar / reescribir / aceptar_por_agotamiento / reintento / escaleta_fuera_limites / parada) · `escritura_fuera_de_zona` · `paso_descartado` · `commit` · `fin_ejecucion`.

| fecha-hora | evento | fase | cap | intento | detalle |
|---|---|---|---|---|---|
