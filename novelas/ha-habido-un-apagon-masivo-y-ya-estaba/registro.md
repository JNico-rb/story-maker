# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-19T00:00:00 | inicio_ejecucion | interrogatorio | | | | | | | | | | comando: nueva; perfil: relato; sobreescrituras: {}; flags: ninguno |
