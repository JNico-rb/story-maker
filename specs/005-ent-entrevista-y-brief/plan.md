# 005 — ENT · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: unitarias exhaustivas por franja, propiedades de las reglas y mutación sobre la validación del brief, «Validación del brief (`schema-brief`)»; unitarias de `citas-verificadas`, «Verificación de citas del texto libre»; pruebas del motor de políticas en el origen texto libre, «Invariante 12 — audit log»; pruebas de los guardarraíles del presupuesto y del 503 sin sitio en la parte de la API, «Presupuesto, límites y techo de entrada»; integración con el doble de la CLI, «CLI»; y la página `interview` por inspección con el browser MCP, «Frontend» (`docs/verification.md` §5). Las evals doradas del entrevistador y del extractor son de 017.

### Steps

#### Reglas del brief

- [ ] El brief se valida contra su schema en cada turno → un brief que no lo cumple, también con un marco fuera del catálogo, es inválido, con los campos que fallan (RF-ENT-12)
- [ ] La edad del destinatario → da su franja: `children` de 0 a 12, `teen` de 13 a 17 y `adult` desde 18. Fronteras: 12 y 13, 17 y 18 (RF-ENT-14)
- [ ] Las fechas del brief → siguen `domain-knowledge.md` §5.2: sin fecha de nacimiento declarada, el 1 de enero de (año presente − edad), también para un allegado del que solo se conoce la edad; el nacimiento a las 00:00; un recuerdo «a los N años», el día en que cumple N a mediodía; un año declarado, su 1 de enero a mediodía, o el día siguiente al nacimiento si es el año en que nació; y un cumpleaños del 29 de febrero, el 1 de marzo en los años no bisiestos (RF-ENT-15)
- [ ] Falta alguno de los campos obligatorios —nombre, edad, al menos un rasgo, al menos un recuerdo, ocasión, género, tono, extensión, dedicatoria o haber preguntado por las entradas prohibidas— → cada uno es un `DatoFaltante`. La fecha de nacimiento, los allegados, los deseos de trama y los textos libres son opcionales, y la lista de prohibidas puede quedar vacía. Los faltantes se calculan en cada turno y no se guardan (RF-ENT-13)
- [ ] C1 · el destinatario es `children` y el género es romance o drama → contradicción entre la edad y el género. Frontera: 12 años con romance la da; 13, no (RF-ENT-16)
- [ ] C2 · el destinatario es `children` y el tono es inquietante → contradicción entre la edad y el tono (RF-ENT-17)
- [ ] C3 · la ocasión es boda o aniversario y el destinatario tiene menos de 18 años, o es jubilación y tiene menos de 50 → contradicción entre la ocasión y la edad. Fronteras: 17 y 18, 49 y 50 (RF-ENT-18)
- [ ] C4 · la fecha de nacimiento declarada no da la edad declarada en la fecha de creación de la novela → contradicción. Frontera: el cumpleaños cae en la fecha de creación (RF-ENT-19)
- [ ] C5 · un recuerdo tiene una edad mayor que la actual, o un año anterior al del nacimiento o posterior al año presente → contradicción entre el recuerdo y la edad (RF-ENT-20)
- [ ] C6 · una entrada de cualquiera de las tres listas prohibidas —global, del cliente o de la novela—, normalizada como en 003, aparece en un elemento obligatorio, en la dedicatoria o en un deseo de trama → contradicción (RF-ENT-21)
- [ ] C7 · un allegado está presente en un recuerdo anterior a su nacimiento → contradicción entre el recuerdo y el nacimiento del allegado (RF-ENT-22)
- [ ] Para toda combinación de franja de edad, ocasión, género y tono, y para fechas, deseos de trama y entradas prohibidas generados → cada combinación contradictoria de `domain-knowledge.md` §4.3 se detecta y ninguna válida se marca. Un deseo de trama con cualquier ambientación, con o sin marco, no es por sí solo contradicción (RF-ENT-23)
  - Exhaustiva por franja, ocasión, género y tono, y generada sobre fechas, deseos de trama y prohibidas, como pide `verification.md` §3.6.
- [ ] El cliente marca más elementos obligatorios que `operation.max_mandatory_elements` —cuentan el nombre del destinatario, que lo es siempre, y los rasgos, recuerdos, allegados y hechos aceptados que marque— → el brief es inválido con un error que dice cuántos sobran y le pide que priorice (RT8) (RF-ENT-24)
  - La cifra se lee de config; sin valor, la validación falla con error accionable (`architecture.md` §15.2). La prueba la fija en su propia config.
- [ ] Se confirma o se importa un brief → corre el validador `schema-brief` —schema, faltantes con las prohibidas preguntadas, C1–C7 y cota—, con un solo criterio de su nombre, bloqueante y sin nivel ni acción; el catálogo de criterios lo contiene, igual que `citas-verificadas` (RF-ENT-25)
- [ ] Las pruebas de mutación sobre la validación del brief matan todo mutante de sus rutas de rechazo: schema, faltantes, C1–C7 y cota (RNF-1)
  - Se lanza con la orden de mutación de la CLI (001), bajo demanda; la métrica son los supervivientes en las rutas de rechazo (`verification.md` §3.7).

#### Novela y entrevista

- [ ] `POST /api/novels` con cuerpo vacío → 201 con `novel_id`; se crean la novela del cliente con su fecha de creación, que fija el año presente, y con el modelo de incrustación de `retrieval.embedding_model` fijado (`architecture.md` §6.9); una entrevista abierta y un brief en borrador vacío (RF-ENT-1)
- [ ] `GET /api/novels/{id}/brief` → el brief y sus cuatro comprobaciones —errores de schema, datos faltantes, contradicciones y cota—, calculadas en la petición (RF-ENT-26)
- [ ] El workspace del harness tiene los prompts `rol/entrevistador` y `rol/extractor` → el del entrevistador le pide preguntar por los datos que faltan, plantear las contradicciones, proponer una dedicatoria si el cliente no la trae, preguntar siempre por las entradas prohibidas y anotar los deseos de trama sin rechazar ninguno por su ambientación: al que no cabe en el presente post-IA le propone un marco, y el cliente fija uno o lo deja libre, que es lo que queda si insiste en que sea real. El del extractor le pide tratar el texto como dato, entregar hechos con su cita literal y declarar como descartadas las instrucciones dirigidas al sistema (RF-ENT-11 · clase I)
  - Los dos se escriben en español y se suben a Langfuse con la orden de sincronización de la CLI (`architecture.md` §12.4).
- [ ] `POST /api/novels/{id}/interview/messages` con un texto → se abre una sesión de rol del entrevistador en el proceso de la API, que recibe el historial guardado de la entrevista, el brief en curso, los hechos verificados y las cuatro comprobaciones de RF-ENT-12 a RF-ENT-24 calculadas en ese momento, con las tools `update_brief` y `propose_dedication`. Si la sesión termina bien, se guardan en una sola transacción el turno —el texto del cliente y la respuesta— y los cambios del brief, y la API responde con el turno del entrevistador (RF-ENT-2)
  - Con el doble del puerto de agente (001): la prueba comprueba las entradas que recibe la sesión y lo que queda en SQLite.
- [ ] `GET /api/novels/{id}/interview/messages` → los turnos guardados, en orden (RF-ENT-3)
- [ ] El entrevistador llama a `update_brief` → los campos que entrega se aplican al brief en curso; las entradas prohibidas que registra quedan como lista de nivel novela, y la tool anota que se preguntó por ellas aunque la lista quede vacía. Cada deseo de trama lleva su enunciado y, si el cliente lo fija, un marco del catálogo cerrado —`simulation`, `dream` o `story_within_story`—; uno sin marco queda libre para el planner (RF-ENT-7)
- [ ] Las tools del entrevistador declaran sus campos narrativos (003) → la dedicatoria de `update_brief` y la de `propose_dedication` son narrativas; las entradas prohibidas, no. Una dedicatoria con un término prohibido hace que el hook de policy deniegue la tool, y una lista de prohibidas con ese término no (RF-ENT-8)
- [ ] El entrevistador llama a `propose_dedication` → la dedicatoria propuesta llega al cliente en la respuesta del turno, y el brief no la tiene hasta que el entrevistador la registra con `update_brief` (RF-ENT-9)
- [ ] La entrevista tiene su traza (004): la abre el primer turno, y los turnos y textos libres siguientes la continúan. En ella quedan todas sus sesiones de rol, los resultados de `schema-brief`, `citas-verificadas` e `inyeccion-detectada` y las decisiones de política que se toman en ella (RF-ENT-4)
- [ ] La sesión de un turno o de un texto libre termina con los turnos o el tiempo agotados o con un fallo del proveedor → 503; no se guardan el turno, los cambios del brief, el texto libre ni sus hechos, y sí la sesión de rol con su coste. Si Langfuse no responde (004), o si la sesión no cabe en la parte de la API del techo de ventana tras esperar `operation.api_window_wait_seconds` (sin calibrar, 008), la sesión no llega a abrirse y también es 503, sin nada que guardar (RF-ENT-5)
  - `roles.<rol>.max_turns` y `max_agent_seconds` se leen de config; sin valor, fallan con error accionable (`architecture.md` §15.2).
  - El caso sin sitio usa un guardián de 008 que devuelve «sin sitio» tras la espera: el doble del puerto de agente no recibe ninguna sesión y no queda fila de `role_sessions`.
- [ ] El coste acumulado de las sesiones de rol de una entrevista —del entrevistador y del extractor— pasa de `operation.budget` → el turno o el texto libre en que ocurre responde 503 sin guardar el turno, los cambios del brief, el texto libre ni sus hechos, y también los siguientes (RF-ENT-6)
  - `operation.budget` se lee de config; sin valor, falla con error accionable. El coste de cada sesión sale de `operation.pricing` (`architecture.md` §11.5).

#### Confirmación

- [ ] `POST /api/novels/{id}/brief/confirm` sobre un brief válido → 200; el brief queda `confirmed` e inmutable, y la entrevista, `confirmed`. Quedan sus elementos personales: el nombre del destinatario, siempre obligatorio; cada rasgo, recuerdo y allegado, obligatorio si el cliente lo marcó; y cada hecho extraído aceptado, con su marca. Un hecho rechazado o sin decidir no es elemento personal, y un deseo de trama tampoco (RF-ENT-27)
- [ ] `POST /api/novels/{id}/brief/confirm` sobre un brief con errores de schema, datos faltantes, contradicciones o la cota superada → 422 con todos ellos, y no cambia nada (RF-ENT-28)

#### Texto libre

- [ ] `POST /api/novels/{id}/free-texts` con un contenido → se abre en la API una sesión del extractor para ese texto, que lo recibe delimitado y declarado como dato; su única tool es `submit_facts`, con los hechos —sujeto, atributo, valor y cita— y las instrucciones descartadas (RF-ENT-30)
- [ ] El texto libre no cabe en la ventana del extractor, según el guardián de ventana (008) → 422 sin abrir la sesión (RF-ENT-34)
- [ ] Corre el detector de inyección de 003 sobre el texto libre, y el extractor entrega → el validador `citas-verificadas` descarta el hecho que no tiene su cita literal en el texto, con los espacios normalizados; el que no tiene por sujeto al destinatario o a un allegado del brief; y el que tiene una cita que se solapa con una frase marcada por el detector. Las tres comprobaciones cuentan en su resultado (RF-ENT-31)
- [ ] El extractor declara instrucciones descartadas → cada una se guarda con el texto libre y pasa por el motor de políticas de 003 como decisión `flag` con el origen `free_text`, así que queda en el audit log y como evento de la traza (RF-ENT-32)
- [ ] La extracción termina → la respuesta son los hechos verificados, pendientes de aceptar; solo esos se guardan, y el texto libre se guarda sin llegar literal a ningún otro rol (RF-ENT-33)
- [ ] El entrevistador nunca recibe un texto libre → en las entradas de su sesión solo están los hechos verificados de los textos libres, nunca su contenido (RF-ENT-10)
- [ ] `PATCH /api/novels/{id}/brief/extracted-facts/{fact_id}` con `accepted` y `mandatory` → el hecho queda aceptado o rechazado, y obligatorio si se marca (RF-ENT-35)
- [ ] Una carta pegada con «ignora las instrucciones anteriores y…» (RT1) → ninguna instrucción llega al brief ni a la sesión del entrevistador, y la frase queda en el audit log (RF-ENT-36)
  - Al pasar, su fila RT1 de `verification.md` §4.9 se rellena con lo que la detectó.
- [ ] El brief ya está confirmado → `POST …/interview/messages`, `POST …/free-texts`, `PATCH …/brief/extracted-facts/{fact_id}` y `POST …/brief/confirm` responden 409 (RF-ENT-29)

#### Brief importado

- [ ] `POST /api/novels` con un `brief` en JSON del mismo schema → se valida primero con las comprobaciones de RF-ENT-12 a RF-ENT-24, y después sus textos libres pasan por el mismo extractor y las mismas verificaciones. Si todo pasa, 201: la novela queda creada como en RF-ENT-1 pero sin entrevista, con el brief `confirmed`, sus hechos verificados aceptados, ninguno obligatorio, y sus elementos personales. La importación corre dentro de su propia traza, y sus sesiones de rol comparten el techo `operation.budget` (RF-ENT-37)
- [ ] Un brief importado con errores de schema, datos faltantes, contradicciones o la cota superada → 422 sin crear nada y sin abrir ninguna sesión. Un texto libre que no cabe en la ventana del extractor → 422. Un fallo del proveedor, un límite o el presupuesto agotados, una sesión del extractor que no cabe en la parte de la API del techo de ventana tras su espera (008), o Langfuse que no responde → 503; no queda nada en SQLite, y la traza de la importación queda en Langfuse sin sesión (RF-ENT-38)
- [ ] La CLI importa un brief desde un fichero JSON a nombre de un cliente → sigue el mismo camino que la API y da el id de la novela o los errores (RF-ENT-39)

#### Página y explainer

- [ ] La página `interview` → tiene el chat, el panel del brief con sus cuatro comprobaciones, la entrada de textos libres, los hechos por aceptar o rechazar con su marca de obligatorio, y la confirmación, disponible solo con el brief válido; un 503 se muestra como reintentable. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 (RF-ENT-40 · clase I)
- [ ] Al cerrar 005 → la cabecera de `architecture.md` §3.3 lleva el explainer del texto no confiable y la inyección de prompt, como asigna la lista de explainers del README (RF-ENT-41 · clase I)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
