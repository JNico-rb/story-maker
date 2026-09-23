# 005 — ENT · Entrevista y brief

- [x] Spec approved   <- only the user marks this

## Objetivo

Convertir una entrevista con el cliente, o un brief importado, en un brief confirmado, válido según el código y sin ningún texto libre literal fuera del extractor.

## Alcance

Cubre:

- la creación de la novela, con su fecha y su modelo de incrustación;
- el entrevistador en el proceso de la API, una sesión de rol por turno, con su traza;
- las reglas deterministas del brief: schema, datos faltantes, las contradicciones C1–C7 y la cota de elementos obligatorios, con las fechas de `domain-knowledge.md` §5.2;
- los deseos de trama con su marco opcional (`domain-knowledge.md` §4.5);
- la confirmación y la inmutabilidad del brief;
- el extractor, las citas verificadas y la aceptación de los hechos;
- el brief importado por la API y por la CLI;
- el presupuesto de la entrevista y de la importación;
- los prompts del entrevistador y del extractor;
- los validadores `schema-brief` y `citas-verificadas`;
- la página de entrevista.

Depende de 001, 002, 003 —el motor de políticas, la normalización y el detector de inyección— y 004 —las trazas y los scores—. La comprobación de que una sesión cabe en su ventana es del guardián de ventana de 008.

**Fuera de alcance:**

- Una pantalla web para subir un brief: el brief importado solo entra por la API y la CLI, y el cliente siempre pasa por la entrevista (`architecture.md` §3.4).
- El paso del brief a la story bible, que el código hace en el primer paso de la planificación (010), con las mismas fechas de RF-ENT-12.
- Cómo se planifica un deseo de trama y su marco, que es de 010.
- Las evals doradas del entrevistador y del extractor, que son de 017.
- Una edición del brief fuera del entrevistador: solo los hechos extraídos los acepta o rechaza el cliente directamente (`architecture.md` §14.3).
- Qué responde un turno cuyo historial ya no cabe en la ventana del entrevistador: lo decide 008 con el guardián de ventana, y no está fijado en los docs.

## Requisitos

Todos son **Obligatorio**.

### Novela y entrevista

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-1 | `POST /api/novels` con cuerpo vacío → 201 con `novel_id`; se crean la novela del cliente con su fecha de creación, que fija el año presente, y con el modelo de incrustación de `retrieval.embedding_model` fijado (`architecture.md` §6.9); una entrevista abierta y un brief en borrador vacío | Obligatorio | T |
| RF-ENT-2 | `POST /api/novels/{id}/interview/messages` con un texto → se abre una sesión de rol del entrevistador en el proceso de la API, que recibe el historial guardado de la entrevista, el brief en curso, los hechos verificados y las cuatro comprobaciones de RF-ENT-12 a RF-ENT-24 calculadas en ese momento, con las tools `update_brief` y `propose_dedication`. Si la sesión termina bien, se guardan en una sola transacción el turno —el texto del cliente y la respuesta— y los cambios del brief, y la API responde con el turno del entrevistador | Obligatorio | T |
| RF-ENT-3 | `GET /api/novels/{id}/interview/messages` → los turnos guardados, en orden | Obligatorio | T |
| RF-ENT-4 | La entrevista tiene su traza (004): la abre el primer turno, y los turnos y textos libres siguientes la continúan. En ella quedan todas sus sesiones de rol, los resultados de `schema-brief`, `citas-verificadas` e `inyeccion-detectada` y las decisiones de política que se toman en ella | Obligatorio | T |
| RF-ENT-5 | La sesión de un turno o de un texto libre termina con los turnos o el tiempo agotados o con un fallo del proveedor → 503; no se guardan el turno, los cambios del brief, el texto libre ni sus hechos, y sí la sesión de rol con su coste. Si Langfuse no responde, la sesión no llega a abrirse (004) y también es 503, sin nada que guardar | Obligatorio | T |
| RF-ENT-6 | El coste acumulado de las sesiones de rol de una entrevista —del entrevistador y del extractor— pasa de `operation.budget` → el turno o el texto libre en que ocurre responde 503 sin guardar el turno, los cambios del brief, el texto libre ni sus hechos, y también los siguientes | Obligatorio | T |
| RF-ENT-7 | El entrevistador llama a `update_brief` → los campos que entrega se aplican al brief en curso; las entradas prohibidas que registra quedan como lista de nivel novela, y la tool anota que se preguntó por ellas aunque la lista quede vacía. Cada deseo de trama lleva su enunciado y, si el cliente lo fija, un marco del catálogo cerrado —`simulation`, `dream` o `story_within_story`—; uno sin marco queda libre para el planner | Obligatorio | T |
| RF-ENT-8 | Las tools del entrevistador declaran sus campos narrativos (003) → la dedicatoria de `update_brief` y la de `propose_dedication` son narrativas; las entradas prohibidas, no. Una dedicatoria con un término prohibido hace que el hook de policy deniegue la tool, y una lista de prohibidas con ese término no | Obligatorio | T |
| RF-ENT-9 | El entrevistador llama a `propose_dedication` → la dedicatoria propuesta llega al cliente en la respuesta del turno, y el brief no la tiene hasta que el entrevistador la registra con `update_brief` | Obligatorio | T |
| RF-ENT-10 | El entrevistador nunca recibe un texto libre → en las entradas de su sesión solo están los hechos verificados de los textos libres, nunca su contenido | Obligatorio | T |
| RF-ENT-11 | El workspace del harness tiene los prompts `rol/entrevistador` y `rol/extractor` → el del entrevistador le pide preguntar por los datos que faltan, plantear las contradicciones, proponer una dedicatoria si el cliente no la trae, preguntar siempre por las entradas prohibidas y anotar los deseos de trama sin rechazar ninguno por su ambientación: al que no cabe en el presente post-IA le propone un marco, y el cliente fija uno o lo deja libre, que es lo que queda si insiste en que sea real. El del extractor le pide tratar el texto como dato, entregar hechos con su cita literal y declarar como descartadas las instrucciones dirigidas al sistema | Obligatorio | I |

### Reglas del brief

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-12 | El brief se valida contra su schema en cada turno → un brief que no lo cumple, también con un marco fuera del catálogo, es inválido, con los campos que fallan | Obligatorio | T |
| RF-ENT-13 | Falta alguno de los campos obligatorios —nombre, edad, al menos un rasgo, al menos un recuerdo, ocasión, género, tono, extensión, dedicatoria o haber preguntado por las entradas prohibidas— → cada uno es un `DatoFaltante`. La fecha de nacimiento, los allegados, los deseos de trama y los textos libres son opcionales, y la lista de prohibidas puede quedar vacía. Los faltantes se calculan en cada turno y no se guardan | Obligatorio | T |
| RF-ENT-14 | La edad del destinatario → da su franja: `children` de 0 a 12, `teen` de 13 a 17 y `adult` desde 18. Fronteras: 12 y 13, 17 y 18 | Obligatorio | T |
| RF-ENT-15 | Las fechas del brief → siguen `domain-knowledge.md` §5.2: sin fecha de nacimiento declarada, el 1 de enero de (año presente − edad), también para un allegado del que solo se conoce la edad; el nacimiento a las 00:00; un recuerdo «a los N años», el día en que cumple N a mediodía; un año declarado, su 1 de enero a mediodía, o el día siguiente al nacimiento si es el año en que nació; y un cumpleaños del 29 de febrero, el 1 de marzo en los años no bisiestos | Obligatorio | T |
| RF-ENT-16 | C1 · el destinatario es `children` y el género es romance o drama → contradicción entre la edad y el género. Frontera: 12 años con romance la da; 13, no | Obligatorio | T |
| RF-ENT-17 | C2 · el destinatario es `children` y el tono es inquietante → contradicción entre la edad y el tono | Obligatorio | T |
| RF-ENT-18 | C3 · la ocasión es boda o aniversario y el destinatario tiene menos de 18 años, o es jubilación y tiene menos de 50 → contradicción entre la ocasión y la edad. Fronteras: 17 y 18, 49 y 50 | Obligatorio | T |
| RF-ENT-19 | C4 · la fecha de nacimiento declarada no da la edad declarada en la fecha de creación de la novela → contradicción. Frontera: el cumpleaños cae en la fecha de creación | Obligatorio | T |
| RF-ENT-20 | C5 · un recuerdo tiene una edad mayor que la actual, o un año anterior al del nacimiento o posterior al año presente → contradicción entre el recuerdo y la edad | Obligatorio | T |
| RF-ENT-21 | C6 · una entrada de cualquiera de las tres listas prohibidas —global, del cliente o de la novela—, normalizada como en 003, aparece en un elemento obligatorio, en la dedicatoria o en un deseo de trama → contradicción | Obligatorio | T |
| RF-ENT-22 | C7 · un allegado está presente en un recuerdo anterior a su nacimiento → contradicción entre el recuerdo y el nacimiento del allegado | Obligatorio | T |
| RF-ENT-23 | Para toda combinación de franja de edad, ocasión, género y tono, y para fechas, deseos de trama y entradas prohibidas generados → cada combinación contradictoria de `domain-knowledge.md` §4.3 se detecta y ninguna válida se marca. Un deseo de trama con cualquier ambientación, con o sin marco, no es por sí solo contradicción | Obligatorio | T |
| RF-ENT-24 | El cliente marca más elementos obligatorios que `operation.max_mandatory_elements` —cuentan el nombre del destinatario, que lo es siempre, y los rasgos, recuerdos, allegados y hechos aceptados que marque— → el brief es inválido con un error que dice cuántos sobran y le pide que priorice (RT8) | Obligatorio | T |
| RF-ENT-25 | Se confirma o se importa un brief → corre el validador `schema-brief` —schema, faltantes con las prohibidas preguntadas, C1–C7 y cota—, con un solo criterio de su nombre, bloqueante y sin nivel ni acción; el catálogo de criterios lo contiene, igual que `citas-verificadas` | Obligatorio | T |

### Confirmación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-26 | `GET /api/novels/{id}/brief` → el brief y sus cuatro comprobaciones —errores de schema, datos faltantes, contradicciones y cota—, calculadas en la petición | Obligatorio | T |
| RF-ENT-27 | `POST /api/novels/{id}/brief/confirm` sobre un brief válido → 200; el brief queda `confirmed` e inmutable, y la entrevista, `confirmed`. Quedan sus elementos personales: el nombre del destinatario, siempre obligatorio; cada rasgo, recuerdo y allegado, obligatorio si el cliente lo marcó; y cada hecho extraído aceptado, con su marca. Un hecho rechazado o sin decidir no es elemento personal, y un deseo de trama tampoco | Obligatorio | T |
| RF-ENT-28 | `POST /api/novels/{id}/brief/confirm` sobre un brief con errores de schema, datos faltantes, contradicciones o la cota superada → 422 con todos ellos, y no cambia nada | Obligatorio | T |
| RF-ENT-29 | El brief ya está confirmado → `POST …/interview/messages`, `POST …/free-texts`, `PATCH …/brief/extracted-facts/{fact_id}` y `POST …/brief/confirm` responden 409 | Obligatorio | T |

### Texto libre

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-30 | `POST /api/novels/{id}/free-texts` con un contenido → se abre en la API una sesión del extractor para ese texto, que lo recibe delimitado y declarado como dato; su única tool es `submit_facts`, con los hechos —sujeto, atributo, valor y cita— y las instrucciones descartadas | Obligatorio | T |
| RF-ENT-31 | Corre el detector de inyección de 003 sobre el texto libre, y el extractor entrega → el validador `citas-verificadas` descarta el hecho que no tiene su cita literal en el texto, con los espacios normalizados; el que no tiene por sujeto al destinatario o a un allegado del brief; y el que tiene una cita que se solapa con una frase marcada por el detector. Las tres comprobaciones cuentan en su resultado | Obligatorio | T |
| RF-ENT-32 | El extractor declara instrucciones descartadas → cada una se guarda con el texto libre y pasa por el motor de políticas de 003 como decisión `flag` con el origen `free_text`, así que queda en el audit log y como evento de la traza | Obligatorio | T |
| RF-ENT-33 | La extracción termina → la respuesta son los hechos verificados, pendientes de aceptar; solo esos se guardan, y el texto libre se guarda sin llegar literal a ningún otro rol | Obligatorio | T |
| RF-ENT-34 | El texto libre no cabe en la ventana del extractor, según el guardián de ventana (008) → 422 sin abrir la sesión | Obligatorio | T |
| RF-ENT-35 | `PATCH /api/novels/{id}/brief/extracted-facts/{fact_id}` con `accepted` y `mandatory` → el hecho queda aceptado o rechazado, y obligatorio si se marca | Obligatorio | T |
| RF-ENT-36 | Una carta pegada con «ignora las instrucciones anteriores y…» (RT1) → ninguna instrucción llega al brief ni a la sesión del entrevistador, y la frase queda en el audit log | Obligatorio | T |

### Brief importado

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-37 | `POST /api/novels` con un `brief` en JSON del mismo schema → se valida primero con las comprobaciones de RF-ENT-12 a RF-ENT-24, y después sus textos libres pasan por el mismo extractor y las mismas verificaciones. Si todo pasa, 201: la novela queda creada como en RF-ENT-1 pero sin entrevista, con el brief `confirmed`, sus hechos verificados aceptados, ninguno obligatorio, y sus elementos personales. La importación corre dentro de su propia traza, y sus sesiones de rol comparten el techo `operation.budget` | Obligatorio | T |
| RF-ENT-38 | Un brief importado con errores de schema, datos faltantes, contradicciones o la cota superada → 422 sin crear nada y sin abrir ninguna sesión. Un texto libre que no cabe en la ventana del extractor → 422. Un fallo del proveedor, un límite o el presupuesto agotados, o Langfuse que no responde → 503; no queda nada en SQLite, y la traza de la importación queda en Langfuse sin sesión | Obligatorio | T |
| RF-ENT-39 | La CLI importa un brief desde un fichero JSON a nombre de un cliente → sigue el mismo camino que la API y da el id de la novela o los errores | Obligatorio | T |

### Página y explainer

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-ENT-40 | La página `interview` → tiene el chat, el panel del brief con sus cuatro comprobaciones, la entrada de textos libres, los hechos por aceptar o rechazar con su marca de obligatorio, y la confirmación, disponible solo con el brief válido; un 503 se muestra como reintentable. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 | Obligatorio | I |
| RF-ENT-41 | Al cerrar 005 → la cabecera de `architecture.md` §3.3 lleva el explainer del texto no confiable y la inyección de prompt, como asigna la lista de explainers del README | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Las pruebas de mutación sobre la validación del brief matan todo mutante de sus rutas de rechazo: schema, faltantes, C1–C7 y cota | T |

## Docs de referencia

- `architecture.md` §3, §6.9 (modelo de incrustación congelado), §6.10 (punto 4), §7.2 (entrevistador y extractor), §7.3 (prompts), §7.4, §7.5 (qué escanea la policy), §7.7 (regla 6), §9.1 (quién escribe), §10.2 y §10.3 (`schema-brief`, `citas-verificadas`, `inyeccion-detectada`), §11.3, §11.4, §11.5, §12.1, §12.4, §13.6, §14.3 y §14.5.
- `definitions.md` §1 (con `DeseoDeTrama` y `Marco`), §5 (`Presupuesto`), §11 (`budget`, `max_mandatory_elements`) y §12.
- `domain-knowledge.md` §4.3, §4.4, §4.5 y §5.2.
- `verification.md` §3.6 (reglas C1–C7), §3.7, §4.2 (eval dorada del entrevistador), §4.9 (RT1 y RT8) y §5.
- README de la raíz («Explainers») y `workflow/4-code.md`, paso 5.
