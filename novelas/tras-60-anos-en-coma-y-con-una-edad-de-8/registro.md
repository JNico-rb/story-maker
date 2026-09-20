# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-20T17:35Z | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: nueva · perfil: relato · sobreescrituras: ninguna · flags: precarga=encargos/tras-60-anos-en-coma-y-con-una-edad-de-8 |
| 2026-09-20T17:36Z | commit | interrogatorio | – | – | – | – | – | – | – | – | – | aad663f · carpeta creada |
| 2026-09-20T17:38Z | entrevista_cerrada | interrogatorio | – | – | – | – | – | – | – | – | – | 0 preguntas, 0 rondas · origen: formulario+grilling · las doce respuestas del formulario venían [decide tú], que no se repreguntan · ruta: entrevista.md |
| 2026-09-20T17:41Z | invocacion | interrogatorio | – | – | – | haiku | 1440 | 3658 | – | – | – | interrogador · modo propuesta · intento técnico 1 · resultado ok · destinos: biblia.md, escaleta.md, arcos/arco-01.md · observaciones: sucesos de 9 entradas por capítulo (la plantilla sugiere 2–5); los ítems de `sucesos` se entrecomillaron al escribirlos para que el frontmatter parsee, sin cambiar el texto |
| 2026-09-20T17:44Z | invocacion | interrogatorio | – | – | – | haiku | 2638 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado ok |
| 2026-09-20T17:44Z | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 3 problemas · gravedad máx. 1 · origen: revisor-continuidad |
| 2026-09-20T17:44Z | decision_harness | interrogatorio | – | – | – | – | – | – | – | – | – | reintento · CANON devuelto al interrogador, vuelta 1/3 |
| 2026-09-20T17:48Z | invocacion | interrogatorio | – | – | – | haiku | 1440 | 3754 | – | – | – | interrogador · modo propuesta vuelta 1 · intento técnico 1 · resultado ok · reescribe escaleta.md; biblia.md con fila nueva de canon (muerte de Elena, 1989); arcos/arco-01.md vuelve idéntico |
| 2026-09-20T17:50Z | invocacion | interrogatorio | – | – | – | haiku | 2734 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado ok |
| 2026-09-20T17:50Z | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad máx. 1 · origen: revisor-continuidad · Tarek no está en Personajes de la biblia |
| 2026-09-20T17:50Z | decision_harness | interrogatorio | – | – | – | – | – | – | – | – | – | reintento · CANON devuelto al interrogador, vuelta 2/3 |
| 2026-09-20T17:54Z | invocacion | interrogatorio | – | – | – | haiku | 4373 | 3953 | – | – | – | interrogador · modo propuesta vuelta 2 · intento técnico 1 · resultado ok · añade Tarek a Personajes; escaleta.md y arcos/arco-01.md vuelven idénticos |
| 2026-09-20T17:56Z | invocacion | interrogatorio | – | – | – | haiku | 2933 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado ok |
| 2026-09-20T17:56Z | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad máx. 1 · origen: revisor-continuidad · Elena: ~75 años en Personajes contra 79 que da el canon |
| 2026-09-20T17:56Z | decision_harness | interrogatorio | – | – | – | – | – | – | – | – | – | reintento · CANON devuelto al interrogador, vuelta 3/3 (última) |
| 2026-09-20T17:58Z | invocacion | interrogatorio | – | – | – | haiku | 4572 | 3985 | – | – | – | interrogador · modo propuesta vuelta 3 · intento técnico 1 · resultado ok · fija el nacimiento de Elena (1947) como fila de canon y cuadra su entrada de Personajes; escaleta.md y arcos/arco-01.md vuelven idénticos |
| 2026-09-20T17:59Z | invocacion | interrogatorio | – | – | – | haiku | 2965 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado ok |
| 2026-09-20T17:59Z | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 2 problemas · gravedad máx. 1 · origen: revisor-continuidad · agotadas las 3 vueltas: los problemas van al usuario con la propuesta |
| 2026-09-20T17:59Z | propuesta_cierre | interrogatorio | 1 | – | – | – | – | – | – | – | – | «La memoria rota» · 3 capítulos · 1 arco (El despertar, caps. 1–3) · rutas: biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-20T17:59Z | decision_harness | interrogatorio | – | – | – | – | – | – | – | – | – | parada · ESPERA_APROBACION · estado.encargo no es null y no hay encargos/tras-60-anos-en-coma-y-con-una-edad-de-8/decision.md |
| 2026-09-20T17:59Z | fin_ejecucion | parada | – | – | – | – | – | – | – | – | – | PARADA · ESPERA_APROBACION |
