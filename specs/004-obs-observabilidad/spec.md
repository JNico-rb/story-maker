# 004 — OBS · Observabilidad

- [ ] Spec approved   <- only the user marks this

## Objetivo

Que la trayectoria entera del harness —sesiones, trazas, spans, tokens, coste, latencia y scores— se vea en Langfuse con los datos personales enmascarados, y que el coste y los scores queden además en SQLite.

## Alcance

Cubre:

- la comprobación de las credenciales y de los prompts al arrancar;
- la sesión por novela y las seis clases de traza, con el commit y la huella de la config;
- los nombres de span, también el de una llamada a tool denegada;
- una llamada de modelo por turno de cada sesión de rol, resuelta en OpenRouter tras cerrarla, con `llamada-sin-detalle` para lo que no se resuelve a tiempo;
- el coste por el uso exacto y `operation.pricing`, y cada sesión de rol guardada en SQLite;
- los scores de los validadores, en Langfuse y en SQLite, con sus excepciones;
- las decisiones de política como eventos de la traza;
- la máscara de cada novela y la unión de máscaras;
- los prompts versionados: un fichero por rol, las órdenes de la CLI de subir y de promover, y la lectura por etiqueta;
- el fallo de Langfuse al abrir una sesión;
- la lectura de vuelta en CI.

Depende de 001. Las decisiones de política que emite como eventos son las del motor de 003.

Promover un prompt es un paso de procedimiento: se hace tras pasar las evals con la versión nueva (`verification.md` §4.8, 017). La orden de promover no comprueba las evals.

**Fuera de alcance:**

- Quién abre cada traza y qué hace con un fallo de infraestructura: la entrevista y la importación son de 005; la ejecución, de 007, que pasa a `interrupted`; la interpretación de un cambio y el guardado de una edición manual, de 015; y la llamada MCP, de 016.
- El bloqueo por presupuesto: 004 calcula el coste; `budget_exceeded` es de 007 y el 503 de la entrevista y de la importación, de 005.
- El contraste con lo que factura OpenRouter y la cola de anotación de la revisión humana, que son de 017.
- El conteo estimado de la entrada y su deriva, que son de 008.
- El evaluable y el intento de cada sesión de una ejecución, que los fija 007; la ventana de cada sesión, que la guarda 008.

## Requisitos

Todos son **Obligatorio**.

### Arranque, sesiones y trazas

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-1 | Al arrancar, las credenciales de Langfuse no pasan `auth_check()`, Langfuse no responde, o el prompt `rol/<etiqueta>` de algún rol no tiene la etiqueta de los prompts → el servidor no arranca, con un error accionable que dice cuál falla | Obligatorio | T |
| RF-OBS-2 | Toda traza de una novela → lleva como sesión el identificador de la novela: su entrevista o su importación, sus ejecuciones, las interpretaciones de sus cambios, los guardados de sus ediciones manuales y las llamadas MCP que la tocan solo a ella quedan en la misma sesión. Una llamada MCP que toca varias novelas o ninguna, y una importación que falla antes de crear la novela, van sin sesión | Obligatorio | T |
| RF-OBS-3 | Se abre la traza de una entrevista, de la importación de un brief, de la interpretación de un cambio, de una ejecución, del guardado de una edición manual o de una llamada MCP → la traza lleva el nombre de su clase: `entrevista`, `importacion`, `interpretacion`, `ejecucion`, `guardado` o `mcp`. Abrirla para algo que ya tiene traza —el turno siguiente de una entrevista, una ejecución reanudada— continúa la misma, sin crear otra | Obligatorio | T |
| RF-OBS-4 | Se abre una traza, o empieza un tramo nuevo de la traza de una ejecución → se le añaden el commit del código y la huella de la config con que corre; la traza de una ejecución reanudada lleva los de cada tramo | Obligatorio | T |

### Spans y llamadas de modelo

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-5 | Dentro de una traza → cada capítulo es un span `capitulo-<n>`; cada sesión de rol, un span `rol:<etiqueta>` con la etiqueta de su rol —`entrevistador`, `extractor`, `planner`, `writer`, `critico`, `editor`, `registrador`, `juez` o `revisor-visual`—; cada llamada a tool, un span `tool:<identificador>`, con el identificador de la tool sin el prefijo que le añade el SDK; y cada validador, un span `validador:<nombre>`. Los nombres de traza, de span, de prompt y de score son ASCII de 200 caracteres como mucho | Obligatorio | T |
| RF-OBS-6 | Una tool en proceso → abre y cierra su span en su manejador. Una tool de Playwright MCP o `Skill`, que no tienen manejador propio → su span se abre en el hook de policy y lo cierra un `PostToolUse` de observabilidad. Una llamada que deniega el hook de policy → también tiene su span `tool:<identificador>`: el hook lo abre y lo cierra en el acto, con nivel WARNING y el motivo en su mensaje. Así toda llamada a tool, permitida o no, aparece como span | Obligatorio | T |
| RF-OBS-7 | Se cierra una sesión de rol → su span `rol:` lleva como metadato su uso exacto, y de él cuelga una llamada de modelo (`LlamadaDeModelo`) por turno, con su id `gen-…`: una observación de generación con el modelo, la latencia, la versión del prompt de la sesión, `usage_details` —entrada, salida, lectura y escritura de caché— y `cost_details` con el coste de RF-OBS-10. Sus cifras son las que da OpenRouter al consultar ese id | Obligatorio | T |
| RF-OBS-8 | Se cierra una sesión de rol → una tarea en segundo plano de su mismo proceso consulta en OpenRouter cada id `gen-…` de sus turnos, reintentando mientras responde 404, durante `operation.generation_lookup_seconds` (sin calibrar) como mucho, y envía cada llamada resuelta. Nada espera por ella: ni la sesión siguiente, ni el presupuesto, ni la respuesta de la API. El worker acaba sus consultas pendientes antes de salir | Obligatorio | T |
| RF-OBS-9 | Unas llamadas no se resuelven dentro de `generation_lookup_seconds` → se envían juntas como una sola, `llamada-sin-detalle`, con la diferencia entre el uso exacto de la sesión y la suma de las resueltas; si se resuelven todas, no hay ninguna. Para toda sesión y todo subconjunto de llamadas resueltas, la suma del uso de sus llamadas, `llamada-sin-detalle` incluida, es su uso exacto: Langfuse no cuenta nada dos veces | Obligatorio | T |
| RF-OBS-10 | Una sesión de rol termina con su uso exacto → su coste es cada tipo de token por su precio en `operation.pricing` para su modelo, en USD por millón; nunca el coste que estima el SDK. El de cada llamada de modelo se calcula igual sobre su uso, así que las de una sesión suman su coste. Con un uso y unos precios fijados, el coste es el calculado a mano. Si el modelo del rol no tiene sus cuatro precios, la sesión no se abre, con un error que nombra el modelo | Obligatorio | T |
| RF-OBS-11 | Se cierra una sesión de rol, dentro o fuera de una ejecución → queda en SQLite con su novela; lo que la abrió —una ejecución, una entrevista, una importación o una interpretación—; su capítulo, si es de uno; su rol, su modelo, la versión de su prompt, su desenlace, su uso exacto, su coste, su duración, sus ids `gen-…`, su traza y su span `rol:`. Desde SQLite, sin llamar a Langfuse, se calculan el coste de un capítulo y de una ejecución, el acumulado de una novela y el de producirla: su entrevista o su importación más su generación (`architecture.md` §10.8, §12.2) | Obligatorio | T |
| RF-OBS-12 | Las sesiones de rol de un capítulo → quedan anidadas bajo su span `capitulo-<n>`, así que Langfuse da sus tokens, su coste y su latencia por llamada, por capítulo y, sumando las trazas de la sesión, por novela | Obligatorio | T |

### Scores y eventos

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-13 | Un validador da su resultado dentro de una traza → Langfuse recibe un score agregado con el nombre del validador, 1 si pasa y 0 si no, y uno por criterio, `<validador>/<criterio>`, en 0/1 o de 1 a 5 según el criterio. Un validador de un solo criterio envía un solo score, con su nombre. Cada score lleva un comentario con los motivos y se asocia a su traza y, si es de capítulo, a su span `capitulo-<n>` | Obligatorio | T |
| RF-OBS-14 | Se envía un score → se copia en SQLite con su novela, su ejecución si la hay, su nombre, su valor, su tipo, su comentario, su traza, su observación y su capítulo | Obligatorio | T |
| RF-OBS-15 | `harness-tla` o un validador que corre en el linter en vivo → no envía score ni deja fila en SQLite. Al guardar una edición manual los validadores sí lo envían, a la traza `guardado` (015) | Obligatorio | T |
| RF-OBS-16 | El motor de políticas toma una decisión dentro de una traza → la traza recibe un evento con la decisión, el origen, el código de motivo y el detalle: cada coincidencia con su nivel y la variante encontrada. También la del guardado de una edición manual, que va a su traza `guardado` | Obligatorio | T |

### Máscara

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-17 | Antes de exportar nada de una novela → su máscara sustituye por etiquetas (`[DESTINATARIO]`, `[ALLEGADO_1]`, `[FECHA]`, `[RECUERDO_2]`, …), en todas las entradas y salidas, los datos personales de su brief —nombres, fechas de nacimiento, rasgos, textos de los recuerdos, dedicatoria, entradas prohibidas de nivel novela y hechos extraídos desde que se verifican, aceptados o no— y los valores de los hechos de origen brief o texto libre de todas sus versiones; además, los correos y los teléfonos por patrón. Tokens, coste, latencia y scores llegan intactos | Obligatorio | T |
| RF-OBS-18 | Para todo brief ficticio generado → ningún dato personal del brief aparece en lo que se exporta a Langfuse | Obligatorio | T |
| RF-OBS-19 | Una traza que toca varias novelas → aplica la unión de sus máscaras | Obligatorio | T |

### Prompts versionados

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-20 | El prompt de sistema de cada rol es un fichero del workspace del harness → la orden de subir de la CLI crea en Langfuse una versión nueva de `rol/<etiqueta>`, sin la etiqueta de los prompts, para cada rol cuyo fichero tiene una huella distinta de la de su última versión; un fichero sin cambios no crea nada | Obligatorio | T |
| RF-OBS-21 | La orden de promover de la CLI, con un rol y una versión → mueve a esa versión la etiqueta de los prompts (`LANGFUSE_PROMPT_LABEL`), y la versión que la tenía la pierde | Obligatorio | T |
| RF-OBS-22 | Se abre una sesión de rol → su prompt de sistema se lee de Langfuse por la etiqueta de los prompts del servidor, y sus llamadas de modelo y la fila de SQLite quedan enlazadas a esa versión. Con la etiqueta `latest`, que Langfuse pone a la última versión, las evals corren una versión recién subida antes de promoverla | Obligatorio | T |
| RF-OBS-23 | Langfuse no responde al abrir una sesión de rol, o el prompt del rol ya no tiene la etiqueta → la sesión no se abre y el fallo es de infraestructura, el mismo desenlace que el de un proveedor que falla (001). La lectura no sirve una versión en caché | Obligatorio | T |

### Lectura de vuelta y explainer

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OBS-24 | En cada cambio, una prueba de CI envía a Langfuse una traza con un span `rol:`, una llamada de modelo hija suya con `usage_details` y `cost_details`, un score y un valor de un brief ficticio que la máscara debe sustituir, y la lee de vuelta por la API v2 de observaciones, reintentando durante un tiempo acotado porque la ingesta tarda de 15 a 30 s → la integración falla si no la encuentra a tiempo, si un nombre o una cifra no coinciden, o si el valor sin enmascarar aparece. La prueba no pasa de 30 peticiones por minuto | Obligatorio | T |
| RF-OBS-25 | Al cerrar 004 → la cabecera de `architecture.md` §12 lleva el explainer de la observabilidad con Langfuse y los prompts versionados, como asigna la lista de explainers del README | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Ninguna prueba de CI salvo la de RF-OBS-24 envía nada a Langfuse: las demás usan un doble del cliente que guarda lo que se exportaría. Las evals y la demostración de extremo a extremo de 017 sí envían | T |

## Docs de referencia

- `architecture.md` §3.4 (importación sin novela), §7.3, §7.4, §7.5 (spans de tool, también la denegada), §9.2 (tramos), §9.6 (traza del guardado), §10.2 y §10.3 (validadores y criterios), §10.8 (coste de una novela), §11.1, §11.3, §11.4, §11.5, §12, §13.2 (unión de máscaras), §14.2 (la CLI) y §14.5 (`role_sessions`, `scores`).
- `definitions.md` §5 (`SesionDeRol`), §6 (`Score`), §8 (con `LlamadaDeModelo`), §11 (`LANGFUSE_*`, `operation.pricing`, `operation.generation_lookup_seconds`) y §12 (excepción de las etiquetas de Langfuse).
- `verification.md` §4.1, §4.8, §5 («Observabilidad», «Llamadas de modelo por turno») y §6 (riesgos 6, 15 y 19).
- README de la raíz («Explainers») y `workflow/4-code.md`, paso 5.
