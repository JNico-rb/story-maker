# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-19T00:00:00 | inicio_ejecucion | interrogatorio | | | | | | | | | | comando: nueva; perfil: relato; sobreescrituras: {}; flags: ninguno |
| 2026-09-19T00:05:00 | entrevista_cerrada | interrogatorio | | | | | | | | | | 6 preguntas, 3 rondas (grilling) |
| 2026-09-19T00:10:00 | invocacion | interrogatorio | | | | haiku | | | | | | interrogador, propuesta, intento 1, ok: biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-19T00:12:00 | invocacion | interrogatorio | | | | haiku | | | | | | revisor-continuidad, canon, ok |
| 2026-09-19T00:12:00 | veredicto | interrogatorio | | | | | | | | | | CANON: RECHAZADO, 1 problema, gravedad máx. 1 (tanque de agua: 3 días en tabla vs. 1,5 días en verificación) |
| 2026-09-19T00:16:00 | invocacion | interrogatorio | | | | haiku | | | | | | interrogador, propuesta vuelta 1, ok (con error técnico recuperado): biblia.md corregida |
| 2026-09-19T00:18:00 | invocacion | interrogatorio | | | | haiku | | | | | | revisor-continuidad, canon (revalidación), ok |
| 2026-09-19T00:18:00 | veredicto | interrogatorio | | | | | | | | | | CANON: RECHAZADO, 1 problema, gravedad máx. 1 (hora 6 del colapso de agua sin justificar frente a las 24h de autonomía del generador) |
| 2026-09-19T00:22:00 | invocacion | interrogatorio | | | | haiku | | | | | | interrogador, propuesta vuelta 2, ok: biblia.md corregida (dos sistemas de respaldo separados) |
| 2026-09-19T00:26:00 | invocacion | interrogatorio | | | | haiku | | | | | | revisor-continuidad, canon (revalidación final), ok |
| 2026-09-19T00:26:00 | veredicto | interrogatorio | | | | | | | | | | CANON: APROBADO, 0 problemas |
| 2026-09-19T00:27:00 | propuesta_cierre | interrogatorio | | | | | | | | | | título provisional pendiente de confirmación; 3 capítulos, 1 arco |
| 2026-09-19T00:30:00 | decision_usuario | interrogatorio | | | | | | | | | | confirma |
| 2026-09-19T00:31:00 | escaleta_validada | interrogatorio | 1 | | | | | | | | | biblia.md y escaleta.md aprobadas; arcos/arco-01.md validado; título: "El apagón y el redescubrimiento" |
