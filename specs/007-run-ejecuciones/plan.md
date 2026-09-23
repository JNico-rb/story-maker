# 007 — RUN · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: integración con el doble del puerto de agente y fases dobles, «Orquestador, fases, reanudación y cola» —`Harness.tla` con TLC es de 006—; aserciones del orquestador, integración con caída simulada y propiedades de RNF-1, «Invariantes 8, 9, 10 y 11»; pruebas de los guardarraíles de intentos, turnos, tiempo, reanudaciones y presupuesto, «Presupuesto, límites y techo de entrada» —el techo de entrada es de 008 y las trazas, de 004—; unitarias del informe desde lo guardado, «Informe de ejecución»; contrato de la API y de los eventos SSE, «API, SSE y cliente generado»; y la página `progress` por TypeScript estricto, ESLint, `steiger`, build de producción e inspección con el browser MCP, «Frontend» (`docs/verification.md` §5).

Las cifras `max_retries`, `max_resumes`, `max_agent_seconds`, `roles.<rol>.max_turns` y `budget` no tienen valor (`architecture.md` §15.2): el orquestador las lee de la config del tramo en curso y, si falta una, la ejecución pasa a `blocked` con `infeasible_config` y la clave en el detalle. Cada prueba fija las suyas en su propia config.

### Steps

#### Estados y cola

- [ ] Las transiciones de una ejecución → son exactamente las de `architecture.md` §9.1: de `created` a `running` o `cancelled`; de `running` a `finished`, `blocked`, `cancelled` o `interrupted`; de `blocked` o `interrupted` a `running` o `cancelled`. Cualquier otra se rechaza, y de `finished` y `cancelled` no se sale (RF-RUN-7)
  - La prueba recorre todos los pares de estados, no solo los permitidos.
- [ ] La cola → son las ejecuciones `created` de todo el servidor, sean de la novela que sean, en orden de llegada. La `position` de una ejecución `created` es el número de las que van por delante: la `running`, si la hay, más las `created` que llegaron antes. Una `running` tiene `position` 0; una en cualquier otro estado, ninguna (RF-RUN-3)
  - Manda RF-RUN-3: la nota de posición de [001 design.md](../001-base/design.md) §4.4 no cuenta la `running`.
- [ ] `POST /api/novels/{id}/runs` sobre una novela con el brief confirmado, sin ninguna generación sin terminar y sin versión publicada → 202 con `run_id` y `position`; se crea una `Ejecucion` de tipo `generation` en estado `created`, al final de la cola (RF-RUN-1)
- [ ] `POST /api/novels/{id}/runs` con el brief en borrador, con una generación de la novela en `created`, `running`, `blocked` o `interrupted`, o con alguna versión publicada → 409 y no se crea nada. Frontera: con la generación anterior `cancelled` y ninguna versión publicada → 202, y la nueva parte de cero (RF-RUN-2)
- [ ] La API y un worker intentan lanzar a la vez → solo una ejecución pasa a `running`, y la otra sigue `created`: nunca hay dos `running` en todo el servidor (RF-RUN-4)
  - La prueba lanza los dos intentos a la vez contra la misma base en WAL, repetida muchas veces.
- [ ] Se lanza una ejecución → corre en un proceso propio del sistema operativo, su worker; pasa a `running`, guarda el PID y la hora de arranque del worker y abre su primer tramo con una copia de la config y de las tres listas prohibidas vigentes —global, del cliente y de la novela— y el commit del código (RF-RUN-5)
  - La hora de arranque la da el sistema operativo; si leerla pide una dependencia compilada, se comprueba antes en el portátil (`architecture.md` §14.4).
- [ ] Una ejecución sale de `running` → su worker lanza la primera de la cola, si la hay, y termina. Sin ninguna `running`, la lanza la API: al encolar, al pasar una caída a `interrupted` y al arrancar (RF-RUN-6)
- [ ] La API arranca, o lee una ejecución `running` en cualquier endpoint → comprueba el PID y la hora de arranque de su worker. Si no vive ningún proceso con ese PID, o el que vive arrancó a otra hora, la pasa a `interrupted` y lanza la primera de la cola; si vive, sigue `running`. Una prueba simula la caída y otra, un proceso ajeno que hereda el PID (RF-RUN-9)
  - Los endpoints que leen una ejecución son los de este plan: `GET /api/runs/{id}`, su `stream`, su `report`, `POST …/resume`, `DELETE /api/runs/{id}`, `GET /api/novels/{id}/runs` y `GET /api/novels/{id}`.

#### Fases, intentos y límites

- [ ] Una ejecución `running` → recorre en orden las fases de su tipo —generación: `planning`, `chapter_production` y `publication`; solicitud de cambio: `revalidation`, `editing` y `publication`; edición manual: `recording`, `propagation` y `publication`—, con su fase y su capítulo actual guardados. Pasa a `finished` solo cuando `publication` publica la versión (014) (RF-RUN-8)
  - Lo que hace cada fase es de 010, 011, 014 y 015: aquí las fases son dobles guionizados que entregan, aceptan, bloquean o fallan, y el orquestador solo las encadena y les aplica los límites. La candidata de las pruebas es un fixture, porque crearla es de 014.
- [ ] El orquestador abre una sesión de rol → le pasa `max_agent_seconds`, que el puerto de agente aplica (RF-BAS-21), junto a los `roles.<rol>.max_turns` de su rol (RF-RUN-25)
  - Los dos salen de la config del tramo; sin uno, la sesión no se abre y la ejecución pasa a `blocked` con `infeasible_config` y la clave en el detalle.
- [ ] Un rol de la ejecución entrega → la entrega cuenta como un intento de su evaluable en el tramo en curso, y queda guardado con su evaluable, su ordinal y su resultado; la sesión de rol que la hizo queda con ese evaluable y ese intento. Cuentan las entregas de texto de un capítulo —denegadas, bloqueadas o aceptadas—, las de la regeneración de respaldo, cada planificación y cada ciclo del gate (RF-RUN-22)
  - Los evaluables son los de `definitions.md` §12: `chapter`, `fallback_regeneration`, `outline` y `gate_cycle`. `change_interpretation` no corre en una ejecución (015).
- [ ] Cuentan cada uno como un intento fallido de su evaluable, con su resultado: una entrada de tool que falla `schema-salida` (RF-BAS-25), una sesión con desenlace «turnos agotados» (RF-BAS-20), una con «tiempo agotado» (RF-BAS-21), una denegación del hook de policy y un bloqueo del hook de validación. Un fallo de infraestructura no es un intento (RF-RUN-11) (RF-RUN-24)
- [ ] Los intentos de un evaluable llegan a `max_retries` en un tramo → no se admite otra entrega de ese evaluable: la sesión en curso termina, y decide el veredicto con los intentos agotados (011). Si escala, la ejecución pasa a `blocked` con `retries_exhausted`, y el detalle nombra el evaluable y sus defectos bloqueantes. Frontera: la entrega número `max_retries` se evalúa; la siguiente no llega a admitirse (RF-RUN-23)
  - El veredicto es un doble que escala: su tabla es de 011.
- [ ] Una fase devuelve un motivo de bloqueo —`retries_exhausted`, `budget_exceeded`, `infeasible_config`, `render_failure`, `banned_content` o `internal_error`— → la ejecución pasa a `blocked` con ese motivo y un detalle legible, sin abrir ninguna sesión más (RF-RUN-10)
  - Un caso por motivo. El detalle se guarda con la ejecución: si [001 design.md](../001-base/design.md) §4.4 no tiene su columna, la añade la migración de 007 y se anota en esa tabla al cerrar.
- [ ] Un fallo de infraestructura —una sesión con desenlace «fallo de infraestructura» del puerto de agente (RF-BAS-23), también el de Langfuse al abrirla (RF-OBS-23), o un verificador formal no disponible (009)— → la ejecución pasa a `interrupted` con el motivo, y no cuenta ningún intento (RF-RUN-11)
  - «No disponible» incluye el verificador que no concluye en `max_verifier_seconds` (RF-LEA-21).

#### Presupuesto

- [ ] Se cierra una sesión de rol de la ejecución → su coste acumulado, la suma del coste de todas sus sesiones en todos sus tramos (004), se compara con el `budget` del tramo en curso. Si lo supera, la ejecución pasa a `blocked` con `budget_exceeded` antes de abrir otra sesión. Frontera: un coste igual al `budget` sigue; uno mayor bloquea (RF-RUN-26)
  - El coste de cada sesión lo calcula 004 con `operation.pricing`; aquí solo se suma y se compara.

#### Puntos de control y aserciones

- [ ] Se acepta un capítulo → queda un `PuntoDeControl` suyo, en una tabla que solo admite inserciones: el store rechaza actualizarlo o borrarlo. Hay además puntos de control de fase: el capítulo 0, que deja la congelación del outline (010); el ciclo en curso del gate; y, en un cambio o una edición, los capítulos afectados ya registrados (RF-RUN-19)
- [ ] El orquestador comprueba en ejecución los invariantes 5, 8, 9 y 10 (`architecture.md` §10.4). Con un fallo inyectado —empezar un capítulo sin el punto de control del anterior, publicar sin haber pasado el gate, escribir en una versión publicada o reanudar hacia un capítulo ya aceptado o saltándose uno— → la ejecución pasa a `blocked` con `internal_error` y el invariante en el detalle, y no escribe nada más en la candidata (RF-RUN-12)
  - Un caso por invariante.

#### Cancelar

- [ ] `DELETE /api/runs/{id}` de una ejecución `created`, `blocked` o `interrupted` → 202, y la API la pasa a `cancelled`. Si es de edición manual, su edición queda `rejected` (RF-RUN-13)
  - Rechazar la candidata al cancelar es de 014, y lo que le pasa a una solicitud de cambio, de 015.
- [ ] `DELETE /api/runs/{id}` de una `running` → 202, y la API pone su marca de cancelación. El worker la lee antes de abrir cada sesión y mientras corre la que está en curso; al verla, corta esa sesión, que termina con desenlace «cortada» (RF-BAS-22), pasa la ejecución a `cancelled`, deja `rejected` la edición manual que aplicaba, si la hay, y lanza la primera de la cola. Tras la marca no se abre ninguna sesión ni se acepta ningún capítulo (RF-RUN-14)
  - Dos casos: la marca antes de abrir una sesión, y durante una sesión del doble que no termina sola.
- [ ] `DELETE /api/runs/{id}` de una `finished` o `cancelled` → 409, y nada cambia (RF-RUN-15)

#### Reanudar

- [ ] `POST /api/runs/{id}/resume` de una ejecución `blocked` o `interrupted`, sin ninguna `running` y con menos de `max_resumes` reanudaciones → 202; la API abre un tramo nuevo con una copia de la config y de las tres listas prohibidas vigentes en ese momento y el commit del código, y la lanza en un worker nuevo (RF-RUN-16)
- [ ] `POST /api/runs/{id}/resume` de una ejecución que no está `blocked` ni `interrupted`, con otra `running` en el servidor o con `max_resumes` reanudaciones ya hechas → 409, y nada cambia. Las reanudaciones son los tramos menos uno. Frontera: con `max_resumes` − 1 reanudaciones → 202; con `max_resumes` → 409 (RF-RUN-17)
  - `max_resumes` se lee de la config vigente; sin valor, la reanudación falla con la clave en la respuesta y la ejecución no cambia (`architecture.md` §15.2).
- [ ] Empieza un tramo → todos sus evaluables parten con cero intentos, también el que bloqueó la ejecución, y el tramo corre con la config y las listas de su copia. Subir el `budget`, corregir la config o quitar una entrada de la lista del cliente y reanudar desbloquea sin tirar la candidata (RF-RUN-18)
  - Tres casos, uno por desbloqueo: `budget_exceeded` con el `budget` subido, `infeasible_config` con la clave añadida y `banned_content` sin la entrada.
- [ ] Se reanuda una ejecución cuyo coste acumulado supera el `budget` del tramo nuevo → vuelve a `blocked` con `budget_exceeded` sin abrir ninguna sesión. Con un `budget` mayor que el coste acumulado, sigue (RF-RUN-27)
- [ ] Se reanuda una ejecución → sigue desde su último punto de control y rehace desde cero el trabajo en curso: en una generación con el capítulo *k* como último, produce el *k*+1; con el capítulo 0, no replanifica; sin él, vuelve a planificar (010); en `publication`, repite el ciclo en curso del gate; en un cambio o una edición, rehace los capítulos afectados que aún no se registraron. Una prueba de integración simula una caída en cada fase y comprueba que los capítulos aceptados son los mismos, sin ninguno repetido ni saltado (invariante 10) (RF-RUN-20)
  - La caída es la muerte real del proceso del worker, que la API detecta como en RF-RUN-9.
- [ ] Se reanuda una ejecución de cambio o de edición → antes de seguir, vuelve a revalidar como al arrancar (015). Si mientras tanto se publicó otra versión de la novela, pasa a `cancelled` con el motivo, y su solicitud o su edición, a `rejected` (RF-RUN-21)
  - La revalidación es un doble: su lógica es de 015.
- [ ] Una prueba de propiedades con el doble del puerto de agente genera secuencias de entregas, denegaciones, bloqueos, caídas, cancelaciones y reanudaciones. En todas: los intentos de un evaluable nunca pasan de `max_retries` dentro de un tramo, las reanudaciones nunca pasan de `max_resumes` (invariante 11), los capítulos aceptados son 1..*k* sin huecos ni repetidos, y toda ejecución acaba en `finished`, `blocked`, `interrupted` o `cancelled`, nunca en un bucle (RNF-1)
  - Con Hypothesis; las caídas se simulan dentro del proceso de la prueba.

#### API, progreso y estado de la novela

- [ ] `GET /api/runs/{id}` → su tipo, su novela, su estado, su fase, su capítulo actual, su coste acumulado, su `position` y, si está `blocked` o `cancelled`, su motivo y su detalle (RF-RUN-28)
  - Las rutas con id de este plan entran en el recorrido de RF-AUT-8 y RF-AUT-9 (002): el fixture del cliente A añade una ejecución.
- [ ] `GET /api/novels/{id}/runs` → las ejecuciones de la novela en orden de llegada, cada una con su id, su tipo, su estado, su fase y su `position` (RF-RUN-29)
- [ ] Se deriva el estado de una novela → `interview` con el brief en borrador; `ready` con el brief confirmado, sin versión publicada y sin generación sin terminar; `in_progress` con una generación sin terminar y ninguna versión publicada; `published` con al menos una versión publicada, aunque tenga ejecuciones de cambio en curso. No se guarda. Una prueba recorre los cuatro, y la frontera de una generación `cancelled` sin versión publicada da `ready` (RF-RUN-32)
- [ ] `GET /api/novels/{id}` → la novela con su fecha de creación, su estado derivado, el número de su versión vigente si la tiene y sus ejecuciones sin terminar —`created`, `running`, `blocked` o `interrupted`—, cada una con su id, su tipo, su estado y su `position` (RF-RUN-31)
- [ ] `GET /api/runs/{id}/stream` con el token en la cabecera de autorización → un flujo `text/event-stream` que emite una instantánea —estado, fase, capítulo, coste, `position` y motivo de bloqueo— al conectar y cada vez que alguno cambia en SQLite. Tras emitir `finished` o `cancelled`, se cierra. Una prueba de contrato fija los campos del evento, y el cliente del frontend lo lee con `fetch`, porque `EventSource` no admite cabeceras (RF-RUN-30)
- [ ] `GET /api/runs/{id}/report` de una ejecución `blocked`, `interrupted`, `finished` o `cancelled` → el `InformeDeEjecucion`: el último score agregado de cada validador en cada capítulo y en la novela; los defectos del último veredicto de cada evaluable, que son los no resueltos; las decisiones de política de la ejecución; los intentos por evaluable y por tramo; las reanudaciones; el coste; el número de defectos por causa raíz; y el motivo de bloqueo. Se calcula al pedirlo desde lo guardado —scores, veredictos, defectos, intentos, tramos, sesiones de rol y audit log— y no se guarda: dos peticiones sobre los mismos datos dan el mismo informe (RF-RUN-33)
  - Sobre un fixture de SQLite con todas esas filas, sin modelo.
- [ ] `GET /api/runs/{id}/report` de una ejecución `created` o `running` → 409 (RF-RUN-34)
  - Con los endpoints de este plan, el esquema OpenAPI y el cliente de `shared/api` se regeneran y se commitean (RF-BAS-39).

#### Restricción, página y cierre

- [ ] La API y el worker escriben cada uno solo lo suyo, según la lista de `architecture.md` §9.1: el worker, su ejecución y su candidata; la API, la cola, la marca de cancelación, el paso a `interrupted` de una caída y la cancelación de una ejecución que no está `running` (R1 · clase I)
  - Revisión de cada escritura de los dos procesos contra esa lista antes de cerrar.
- [ ] La página `progress` de una novela → si está `ready`, permite lanzar la generación; muestra cada ejecución sin terminar con su estado, su fase, su capítulo, su coste y su posición en la cola, al día por el SSE; en `blocked` e `interrupted` muestra el motivo y permite reanudar o cancelar, y en `created` y `running`, cancelar; muestra el motivo de un 409; enlaza al informe y, al publicarse, a la lectura. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 (RF-RUN-35 · clase I)
  - Las fases son dobles, así que la inspección corre sobre ejecuciones de fixture en cada estado y un SSE que las hace avanzar.
  - La misma inspección comprueba el tema corporativo en la página, como pide RF-BAS-48 de 001 a cada spec que añade una.
- [ ] Al cerrar 007 → la tabla de correspondencia del README de la raíz (RF-TLA-10) dice, para cada acción de las especificaciones que es una transición del orquestador, qué código la implementa; las de la API son de 015 y 016 (RF-RUN-36 · clase I)
- [ ] Al cerrar 007 → la cabecera de `architecture.md` §7.6 lleva el explainer de reintentos y límites: por qué ningún bucle del harness es ilimitado (RF-RUN-37 · clase I)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
