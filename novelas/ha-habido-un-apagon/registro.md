# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-20 | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: `nueva "Ha habido un apagón." precarga: encargos/ha-habido-un-apagon` · perfil: relato · sobreescrituras: ninguna · flags: precarga=encargos/ha-habido-un-apagon |
| 2026-09-20 | commit | interrogatorio | – | – | – | – | – | – | – | – | – | punto: carpeta creada · sha: 7895281 |
| 2026-09-20 | entrevista_cerrada | interrogatorio | – | – | – | – | – | – | – | – | – | 24 decisiones (12 precargadas + 12 del grilling), 2 rondas + cierre · origen: formulario+grilling · precarga: encargos/ha-habido-un-apagon/entrevista-previa.md · ruta: novelas/ha-habido-un-apagon/entrevista.md |
| 2026-09-20 | invocacion | interrogatorio | 1 | – | – | haiku | 1890 | 4294 | – | – | – | agente: interrogador · modo: propuesta · intento técnico 1 · resultado: ok · destinos: biblia.md, escaleta.md, arcos/arco-01.md · observación: «Reglas inviolables» entregada como negrita dentro de «Cronología y datos fijos» en vez de sección propia; contenido presente y numerado 1–6 |
| 2026-09-20 | invocacion | interrogatorio | 1 | – | – | haiku | 2405 | – | – | – | – | agente: revisor-continuidad · modo: canon · intento técnico 1 · resultado: ok |
| 2026-09-20 | veredicto | interrogatorio | 1 | – | – | – | – | – | – | – | – | origen: CANON · RECHAZADO · 2 problemas · gravedad máx. 1 · (a) balance de gasóleo imposible: 5000 l / 30 días = 167 l/día frente a 200 l/día solo del ambulatorio; (b) 1000 l finales no dan «dos meses asegurados» a 200 l/día |
| 2026-09-20 | decision_harness | interrogatorio | 1 | – | – | – | – | – | – | – | – | devuelto al interrogador por CANON (vuelta 1/3) · sin molestar al usuario |
