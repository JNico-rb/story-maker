# 007 — RUN · Ejecuciones

- [x] Spec approved   <- only the user marks this

## Objetivo

Que cada ejecución corra sola en su worker, con límites que siempre la hacen terminar, y que el cliente pueda seguirla, cancelarla y reanudarla sin perder ni repetir capítulos.

## Alcance

Cubre:

- el lanzamiento de una generación y la cola global, con una sola ejecución `running` en todo el servidor;
- el worker, quién lanza cada ejecución y la detección de caídas;
- los estados, sus transiciones y el encadenado de las fases de cada tipo;
- los bloqueos con su motivo, las interrupciones por infraestructura y las aserciones del orquestador;
- cancelar y reanudar, con un tramo nuevo por reanudación, y los puntos de control de capítulo y de fase;
- los intentos por evaluable, los límites de `architecture.md` §7.6 y qué errores cuentan como intento;
- el presupuesto en dinero de una ejecución;
- los endpoints de ejecuciones, el SSE de progreso, `GET /api/novels/{id}` y el estado derivado de la novela;
- el informe de ejecución;
- la página `progress`.

Columnas de `runs`, `run_segments`, `attempts` y `checkpoints`: [001 design.md](../001-base/design.md) §12.

Depende de 001, 002, 003, 004 y 006. La especificación TLA+ de 006 se escribe antes que el orquestador (`architecture.md` §10.6).

**Fuera de alcance:**

- Lo que hace cada fase: la planificación es de 010; la producción de capítulos, de 011; el gate y la publicación, de 014; la revalidación, la edición y la propagación de un cambio o una edición, de 015. Esta spec las encadena y les aplica los límites.
- La creación y la copia de la candidata, y su rechazo al cancelar, que son de 014.
- Encolar una ejecución de cambio o de edición, y lo que le pasa a una solicitud de cambio al cancelarse su ejecución, que son de 015.
- El veredicto y su tabla, que son de 011: aquí se aplica su «escalar».
- De dónde salen los demás motivos de bloqueo: `infeasible_config` (008), `render_failure` (013 y 014) y `banned_content` (014). Aquí se aplican a la ejecución.
- Cómo corta el puerto de agente una sesión y cierra su subproceso, que es de 001.
- La traza de la ejecución, con el commit y la huella de cada tramo, y el coste de cada sesión de rol, que son de 004.
- La lista de «mis novelas», `GET /api/novels`, que es de 013, y la creación de la novela, que es de 005.

## Requisitos

Todos son **Obligatorio**. Las cifras `max_retries`, `max_resumes`, `max_agent_seconds`, `roles.<rol>.max_turns` y `budget` están sin calibrar (`architecture.md` §15.2): las pruebas fijan las suyas.

### Lanzamiento y cola

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-1 | `POST /api/novels/{id}/runs` sobre una novela con el brief confirmado, sin ninguna generación sin terminar y sin versión publicada → 202 con `run_id` y `position`; se crea una `Ejecucion` de tipo `generation` en estado `created`, al final de la cola | Obligatorio | T |
| RF-RUN-2 | `POST /api/novels/{id}/runs` con el brief en borrador, con una generación de la novela en `created`, `running`, `blocked` o `interrupted`, o con alguna versión publicada → 409 y no se crea nada. Frontera: con la generación anterior `cancelled` y ninguna versión publicada → 202, y la nueva parte de cero | Obligatorio | T |
| RF-RUN-3 | La cola → son las ejecuciones `created` de todo el servidor, sean de la novela que sean, en orden de llegada. La `position` de una ejecución `created` es el número de las que van por delante: la `running`, si la hay, más las `created` que llegaron antes. Una `running` tiene `position` 0; una en cualquier otro estado, ninguna | Obligatorio | T |
| RF-RUN-4 | La API y un worker intentan lanzar a la vez → solo una ejecución pasa a `running`, y la otra sigue `created`: nunca hay dos `running` en todo el servidor | Obligatorio | T |
| RF-RUN-5 | Se lanza una ejecución → corre en un proceso propio del sistema operativo, su worker; pasa a `running`, guarda el PID y la hora de arranque del worker y abre su primer tramo con una copia de la config y de las tres listas prohibidas vigentes y el commit del código | Obligatorio | T |
| RF-RUN-6 | Una ejecución sale de `running` → su worker lanza la primera de la cola, si la hay, y termina. Sin ninguna `running`, la lanza la API: al encolar, al pasar una caída a `interrupted` y al arrancar | Obligatorio | T |

### Estados y fases

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-7 | Las transiciones de una ejecución → son exactamente las de `architecture.md` §9.1: de `created` a `running` o `cancelled`; de `running` a `finished`, `blocked`, `cancelled` o `interrupted`; de `blocked` o `interrupted` a `running` o `cancelled`. Cualquier otra se rechaza, y de `finished` y `cancelled` no se sale | Obligatorio | T |
| RF-RUN-8 | Una ejecución `running` → recorre en orden las fases de su tipo —generación: `planning`, `chapter_production` y `publication`; solicitud de cambio: `revalidation`, `editing` y `publication`; edición manual: `recording`, `propagation` y `publication`—, con su fase y su capítulo actual guardados. Pasa a `finished` solo cuando `publication` publica la versión (014) | Obligatorio | T |
| RF-RUN-9 | La API arranca, o lee una ejecución `running` en cualquier endpoint → comprueba el PID y la hora de arranque de su worker. Si no vive ningún proceso con ese PID, o el que vive arrancó a otra hora, la pasa a `interrupted` y lanza la primera de la cola; si vive, sigue `running`. Una prueba simula la caída y otra, un proceso ajeno que hereda el PID | Obligatorio | T |

### Bloqueos, interrupciones y aserciones

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-10 | Una fase devuelve un motivo de bloqueo —`retries_exhausted`, `budget_exceeded`, `infeasible_config`, `render_failure`, `banned_content` o `internal_error`— → la ejecución pasa a `blocked` con ese motivo y un detalle legible, sin abrir ninguna sesión más | Obligatorio | T |
| RF-RUN-11 | Un fallo de infraestructura —una sesión con desenlace «fallo de infraestructura» del puerto de agente (RF-BAS-23), también el de Langfuse al abrirla (RF-OBS-21), o un verificador formal no disponible (009)— → la ejecución pasa a `interrupted` con el motivo, y no cuenta ningún intento | Obligatorio | T |
| RF-RUN-12 | El orquestador comprueba en ejecución los invariantes 5, 8, 9 y 10 (`architecture.md` §10.4). Con un fallo inyectado —empezar un capítulo sin el punto de control del anterior, publicar sin haber pasado el gate, escribir en una versión publicada o reanudar hacia un capítulo ya aceptado o saltándose uno— → la ejecución pasa a `blocked` con `internal_error` y el invariante en el detalle, y no escribe nada más en la candidata | Obligatorio | T |

### Cancelar

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-13 | `DELETE /api/runs/{id}` de una ejecución `created`, `blocked` o `interrupted` → 202, y la API la pasa a `cancelled`. Si es de edición manual, su edición queda `rejected` | Obligatorio | T |
| RF-RUN-14 | `DELETE /api/runs/{id}` de una `running` → 202, y la API pone su marca de cancelación. El worker la lee antes de abrir cada sesión y mientras corre la que está en curso; al verla, corta esa sesión, que termina con desenlace «cortada» (RF-BAS-22), pasa la ejecución a `cancelled`, deja `rejected` la edición manual que aplicaba, si la hay, y lanza la primera de la cola. Tras la marca no se abre ninguna sesión ni se acepta ningún capítulo | Obligatorio | T |
| RF-RUN-15 | `DELETE /api/runs/{id}` de una `finished` o `cancelled` → 409, y nada cambia | Obligatorio | T |

### Reanudar y puntos de control

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-16 | `POST /api/runs/{id}/resume` de una ejecución `blocked` o `interrupted`, sin ninguna `running` y con menos de `max_resumes` reanudaciones → 202; la API abre un tramo nuevo con una copia de la config y de las tres listas prohibidas vigentes en ese momento y el commit del código, y la lanza en un worker nuevo | Obligatorio | T |
| RF-RUN-17 | `POST /api/runs/{id}/resume` de una ejecución que no está `blocked` ni `interrupted`, con otra `running` en el servidor o con `max_resumes` reanudaciones ya hechas → 409, y nada cambia. Las reanudaciones son los tramos menos uno. Frontera: con `max_resumes` − 1 reanudaciones → 202; con `max_resumes` → 409 | Obligatorio | T |
| RF-RUN-18 | Empieza un tramo → todos sus evaluables parten con cero intentos, también el que bloqueó la ejecución, y el tramo corre con la config y las listas de su copia. Subir el `budget`, corregir la config o quitar una entrada de la lista del cliente y reanudar desbloquea sin tirar la candidata | Obligatorio | T |
| RF-RUN-19 | Se acepta un capítulo → queda un `PuntoDeControl` suyo, en una tabla que solo admite inserciones: el store rechaza actualizarlo o borrarlo. Hay además puntos de control de fase: el capítulo 0, que deja la congelación del outline (010); el ciclo en curso del gate; y, en un cambio o una edición, los capítulos afectados ya registrados | Obligatorio | T |
| RF-RUN-20 | Se reanuda una ejecución → sigue desde su último punto de control y rehace desde cero el trabajo en curso: en una generación con el capítulo *k* como último, produce el *k*+1; con el capítulo 0, no replanifica; sin él, vuelve a planificar (010); en `publication`, repite el ciclo en curso del gate; en un cambio o una edición, rehace los capítulos afectados que aún no se registraron. Una prueba de integración simula una caída en cada fase y comprueba que los capítulos aceptados son los mismos, sin ninguno repetido ni saltado (invariante 10) | Obligatorio | T |
| RF-RUN-21 | Se reanuda una ejecución de cambio o de edición → antes de seguir, vuelve a revalidar como al arrancar (015). Si mientras tanto se publicó otra versión de la novela, pasa a `cancelled` con el motivo, y su solicitud o su edición, a `rejected` | Obligatorio | T |

### Intentos y límites

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-22 | Un rol de la ejecución entrega → la entrega cuenta como un intento de su evaluable en el tramo en curso, y queda guardado con su evaluable, su ordinal y su resultado; la sesión de rol que la hizo queda con ese evaluable y ese intento. Cuentan las entregas de texto de un capítulo —denegadas, bloqueadas o aceptadas—, las de la regeneración de respaldo, cada planificación y cada ciclo del gate | Obligatorio | T |
| RF-RUN-23 | Los intentos de un evaluable llegan a `max_retries` en un tramo → no se admite otra entrega de ese evaluable: la sesión en curso termina, y decide el veredicto con los intentos agotados (011). Si escala, la ejecución pasa a `blocked` con `retries_exhausted`, y el detalle nombra el evaluable y sus defectos bloqueantes. Frontera: la entrega número `max_retries` se evalúa; la siguiente no llega a admitirse | Obligatorio | T |
| RF-RUN-24 | Cuentan cada uno como un intento fallido de su evaluable, con su resultado: una entrada de tool que falla `schema-salida` (RF-BAS-25), una sesión con desenlace «turnos agotados» (RF-BAS-20), una con «tiempo agotado» (RF-BAS-21), una denegación del hook de policy y un bloqueo del hook de validación. Un fallo de infraestructura no es un intento (RF-RUN-11) | Obligatorio | T |
| RF-RUN-25 | El orquestador abre una sesión de rol → le pasa `max_agent_seconds`, que el puerto de agente aplica (RF-BAS-21), junto a los `roles.<rol>.max_turns` de su rol | Obligatorio | T |

### Presupuesto

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-26 | Se cierra una sesión de rol de la ejecución → su coste acumulado, la suma del coste de todas sus sesiones en todos sus tramos (004), se compara con el `budget` del tramo en curso. Si lo supera, la ejecución pasa a `blocked` con `budget_exceeded` antes de abrir otra sesión. Frontera: un coste igual al `budget` sigue; uno mayor bloquea | Obligatorio | T |
| RF-RUN-27 | Se reanuda una ejecución cuyo coste acumulado supera el `budget` del tramo nuevo → vuelve a `blocked` con `budget_exceeded` sin abrir ninguna sesión. Con un `budget` mayor que el coste acumulado, sigue | Obligatorio | T |

### API, progreso y estado de la novela

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-28 | `GET /api/runs/{id}` → su tipo, su novela, su estado, su fase, su capítulo actual, su coste acumulado, su `position` y, si está `blocked` o `cancelled`, su motivo y su detalle | Obligatorio | T |
| RF-RUN-29 | `GET /api/novels/{id}/runs` → las ejecuciones de la novela en orden de llegada, cada una con su id, su tipo, su estado, su fase y su `position` | Obligatorio | T |
| RF-RUN-30 | `GET /api/runs/{id}/stream` con el token en la cabecera de autorización → un flujo `text/event-stream` que emite una instantánea —estado, fase, capítulo, coste, `position` y motivo de bloqueo— al conectar y cada vez que alguno cambia en SQLite. Tras emitir `finished` o `cancelled`, se cierra. Una prueba de contrato fija los campos del evento, y el cliente del frontend lo lee con `fetch`, porque `EventSource` no admite cabeceras | Obligatorio | T |
| RF-RUN-31 | `GET /api/novels/{id}` → la novela con su fecha de creación, su estado derivado, el número de su versión vigente si la tiene y sus ejecuciones sin terminar —`created`, `running`, `blocked` o `interrupted`—, cada una con su id, su tipo, su estado y su `position` | Obligatorio | T |
| RF-RUN-32 | Se deriva el estado de una novela → `interview` con el brief en borrador; `ready` con el brief confirmado, sin versión publicada y sin generación sin terminar; `in_progress` con una generación sin terminar y ninguna versión publicada; `published` con al menos una versión publicada, aunque tenga ejecuciones de cambio en curso. No se guarda. Una prueba recorre los cuatro, y la frontera de una generación `cancelled` sin versión publicada da `ready` | Obligatorio | T |
| RF-RUN-33 | `GET /api/runs/{id}/report` de una ejecución `blocked`, `interrupted`, `finished` o `cancelled` → el `InformeDeEjecucion`: el último score agregado de cada validador en cada capítulo y en la novela; los defectos del último veredicto de cada evaluable, que son los no resueltos; las decisiones de política de la ejecución; los intentos por evaluable y por tramo; las reanudaciones; el coste; el número de defectos por causa raíz; y el motivo de bloqueo. Se calcula al pedirlo desde lo guardado —scores, veredictos, defectos, intentos, tramos, sesiones de rol y audit log— y no se guarda: dos peticiones sobre los mismos datos dan el mismo informe | Obligatorio | T |
| RF-RUN-34 | `GET /api/runs/{id}/report` de una ejecución `created` o `running` → 409 | Obligatorio | T |
| RF-RUN-35 | La página `progress` de una novela → si está `ready`, permite lanzar la generación; muestra cada ejecución sin terminar con su estado, su fase, su capítulo, su coste y su posición en la cola, al día por el SSE; en `blocked` e `interrupted` muestra el motivo y permite reanudar o cancelar, y en `created` y `running`, cancelar; muestra el motivo de un 409; enlaza al informe y, al publicarse, a la lectura. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 | Obligatorio | I |
| RF-RUN-36 | Al cerrar 007 → la tabla de correspondencia del README de la raíz (RF-TLA-10) dice, para cada acción de las especificaciones que es una transición del orquestador, qué código la implementa; las de la API son de 015 y 016 | Obligatorio | I |
| RF-RUN-37 | Al cerrar 007 → la cabecera de `architecture.md` §7.6 lleva el explainer de reintentos y límites: por qué ningún bucle del harness es ilimitado | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Una prueba de propiedades con el doble del puerto de agente genera secuencias de entregas, denegaciones, bloqueos, caídas, cancelaciones y reanudaciones. En todas: los intentos de un evaluable nunca pasan de `max_retries` dentro de un tramo, las reanudaciones nunca pasan de `max_resumes` (invariante 11), los capítulos aceptados son 1..*k* sin huecos ni repetidos, y toda ejecución acaba en `finished`, `blocked`, `interrupted` o `cancelled`, nunca en un bucle | T |

## Restricciones

| # | Restricción | Origen | Clase |
|---|---|---|---|
| R1 | La API y el worker escriben cada uno solo lo suyo, según la lista de `architecture.md` §9.1: el worker, su ejecución y su candidata; la API, la cola, la marca de cancelación, el paso a `interrupted` de una caída y la cancelación de una ejecución que no está `running` | `architecture.md` §9.1 | I |

## Docs de referencia

- `architecture.md` §2 (premisa 5), §7.6, §9.1, §9.2, §10.4 (invariantes 5, 8, 9, 10 y 11, y las aserciones), §11.5, §13.6 (página de progreso), §14.3 y §14.4.
- `definitions.md` §3 (`Novela`, su estado derivado, y `PuntoDeControl`), §5 (`SesionDeRol` y su desenlace, orquestador, worker, cola, `Ejecucion`, `Presupuesto`), §6 (`Evaluable`, `Defecto`, `Veredicto`, `InformeDeEjecucion`), §11 (`operation`) y §12.
- `verification.md` §3.5, §3.8 (eventos SSE), §4.3 (todo bucle tiene techo), §4.4, §4.10 y §5 («Orquestador, fases, reanudación y cola», «Informe de ejecución», «Presupuesto, límites y techo de entrada»).
