# Registro

Solo se añaden filas; nunca se editan. Lo escribe únicamente el harness. Textos completos no: rutas.

Eventos: `inicio_ejecucion` · `entrevista_cerrada` · `invocacion` (agente, modo, modelo, intento técnico, resultado ok / fallo / incumple) · `propuesta_cierre` · `decision_usuario` · `escaleta_validada` (arco) · `longitud` (ok / rechazo, palabras, objetivo) · `veredicto` (veredicto, nº problemas, gravedad máx., origen; en capítulo, el desglose por revisor) · `discrepancia_veredicto` (con qué revisor) · `decision_harness` (aprobar / ajuste_longitud / reescribir / aceptar_por_agotamiento / mejor_intento / reintento / parada) · `manuscrito` · `erratas` · `paso_descartado` · `commit` · `fin_ejecucion`.

El agente de una fila `invocacion` es uno de `interrogador`, `escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`. Los modos de `revisor-continuidad` son `canon`, `capitulo`, `arco` y `global`; el de `revisor-encargo`, solo `capitulo`. Un intento revisado produce **dos** filas `invocacion`, una por revisor.

Un rechazo por longitud que consume **ajuste** y no reescritura se distingue en la fila `decision_harness`: `ajuste_longitud <n>/<max>`. Es lo que permite reconstruir después por qué un capítulo llegó a cinco intentos.

Las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd` solo se rellenan en las filas `invocacion`: modelo con el que se invocó, palabras de los ficheros que se le mandó leer y de lo que entregó (`wc -w`), y tokens y coste reales si el proveedor los devuelve (hito 2). Son el dato de volumen de `specs/functional.md` §6.6.

| fecha-hora | evento | etapa | arco | cap | intento | modelo | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd | detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-09-17 | inicio_ejecucion | interrogatorio | – | – | – | – | – | – | – | – | – | comando: nueva · perfil: relato · sobreescrituras: ninguna · flags: precarga=encargos/una-persona-que-desde-los-10-anos-se-des |
| 2026-09-17 | entrevista_cerrada | interrogatorio | – | – | – | – | – | 283 | – | – | – | origen: formulario+grilling · 12 campos precargados, todos [decide tú] · 0 preguntas de grilling pendientes (interrogatorio.md §3) · novelas/…/entrevista.md |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 1296 | – | – | – | – | interrogador · modo propuesta · intento técnico 1 · resultado: incumple |
| 2026-09-17 | decision_harness | interrogatorio | – | – | – | – | – | – | – | – | – | reintento 1/3 · escaleta.md declaraba 3 entradas de arco con el mismo n:1, incoherente con arcos/arco-01.md (desde 1, hasta 5); faltaba la sección ## Hilos; «Reglas inviolables» no era sección propia en biblia.md |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 1296 | 4883 | – | – | – | interrogador · modo propuesta · intento técnico 2 · resultado: ok · novelas/…/biblia.md, escaleta.md, arcos/arco-01.md |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 2966 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado: ok |
| 2026-09-17 | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad máx. 1 · origen: revisor-continuidad · vuelta 1/3 |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 6179 | 4883 | – | – | – | interrogador · modo propuesta · vuelta 1 (CANON) · intento técnico 1 · resultado: ok |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 2966 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado: ok |
| 2026-09-17 | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · RECHAZADO · 1 problema · gravedad máx. 1 · origen: revisor-continuidad · vuelta 2/3 |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 6179 | 4883 | – | – | – | interrogador · modo propuesta · vuelta 2 (CANON) · intento técnico 1 · resultado: ok |
| 2026-09-17 | invocacion | interrogatorio | – | – | – | haiku | 2966 | – | – | – | – | revisor-continuidad · modo canon · intento técnico 1 · resultado: ok |
| 2026-09-17 | veredicto | interrogatorio | – | – | – | – | – | – | – | – | – | CANON · APROBADO · 0 problemas · origen: revisor-continuidad · vuelta 3/3 |
| 2026-09-17 | propuesta_cierre | interrogatorio | 1 | – | – | – | – | – | – | – | – | «La Oscuridad de Cincuenta Años» · 5 capítulos · 1 arco · ~7.500 palabras |
