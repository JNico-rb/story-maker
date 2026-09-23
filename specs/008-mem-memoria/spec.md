# 008 — MEM · Memoria

- [ ] Spec approved   <- only the user marks this

## Objetivo

Que cada sesión de rol reciba una ventana cerrada por el código, determinista y dentro de su cuota, con la memoria de su versión y sin ver nada de capítulos posteriores ni de otras novelas.

## Alcance

Cubre:

- las dos colecciones del índice: las `CanonCard`, proyección de la story bible, y los párrafos de prosa;
- la escritura del índice dentro de la transacción de quien cambia la story bible, los vectores por huella y el modelo de incrustación congelado;
- la recuperación: corte temporal, BM25 en código, fusión por rango recíproco dentro de cada colección, desempate estable, arrastre por el grafo, cuotas y escasez;
- las consultas del writer, el crítico y el editor;
- los residentes y las entradas de la llamada de cada consumidor, con la proyección del outline, el `ResumenRodante` y el `EstadoDelMundo`;
- el guardián de ventana: la cuota de cada sesión dentro de su parte del techo —la de la ejecución o la de la API—, la reserva de la parte de la API con su espera, la reserva de turnos, los gastos fijos, el orden de recorte y la config infactible;
- el conteo local y la reconciliación al cerrar cada sesión;
- la `VentanaDeContexto` guardada y la `Trazabilidad` de cada capítulo.

Columnas de `canon_cards`, `embeddings`, las tablas de FTS5, `world_states`, `traceability` y `context_windows`: [001 design.md](../001-base/design.md) §12.

Depende de 001, que entrega la infraestructura del índice: `sqlite-vec` cargado, las tablas de FTS5 con su tokenizador, la tabla de vectores por (huella, modelo) y el productor de vectores funcionando en Windows. Esta spec entrega todo lo que tiene términos del dominio.

**Fuera de alcance:**

- La infraestructura del índice y la validación de las cuotas, del techo y de su parte para la API al arrancar, que son de 001.
- El 503 de una sesión de la API que no encuentra sitio en su parte: lo responde quien la abre, 005 y 015.
- Las transacciones que escriben el índice con lo que esta spec deriva: el canon del brief y la congelación (010), la aceptación de un capítulo y el reemplazo de un registro repetido (011), la copia de la candidata (014) y la aplicación de un cambio (015).
- Bloquear la ejecución cuando el guardián declara la config infactible, que es de 007.
- El linter de repetición como consumidor de la prosa, que es de 012.
- La elección de las cuotas, que no la cubre ninguna prueba del recuperador: la mide la eval del crítico (017).

## Requisitos

Todos son **Obligatorio**. Las cuotas (`retrieval.quotas`), el modelo de incrustación, `roles.<rol>.max_turns`, `roles.<rol>.max_output`, `max_tool_output`, `count_drift_threshold`, `api_window_share` y `api_window_wait_seconds` están sin calibrar (`architecture.md` §15.2): las pruebas fijan los suyos.

### Colecciones e índice

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-1 | Se proyecta la story bible de una versión → hay una `CanonCard` por entidad: el novum, con los hechos cuyo sujeto es el mundo; cada consecuencia; cada restricción; cada personaje, con sus hechos vigentes; y cada lugar, con los suyos. Cada tarjeta guarda su contenido, su huella y su `desde_capitulo` | Obligatorio | T |
| RF-MEM-2 | Cambia una entidad —un hecho suyo nuevo o sucesor, o un personaje o lugar nuevo— → se añade su tarjeta sucesora, y la anterior no cambia. `hasta_capitulo` no se guarda: es el `desde_capitulo` de la sucesora de la misma entidad en esa versión. Las tarjetas del canon del brief y de la planificación rigen desde el capítulo 0; la nacida al aceptar el capítulo *n*, desde el *n*+1 | Obligatorio | T |
| RF-MEM-3 | Se acepta un capítulo → cada párrafo suyo, el texto entre dos líneas en blanco, es una unidad de la colección de prosa, con la cabecera de su capítulo. Solo tiene fila de FTS5, sin vector | Obligatorio | T |
| RF-MEM-4 | Quien escribe la story bible invoca la escritura del índice → las tarjetas, y en una aceptación los párrafos, se escriben en la misma transacción. Si esa transacción falla, no queda ninguna tarjeta, fila de FTS5 ni vector nuevo. Solo la invocan los cinco momentos de `architecture.md` §6.11 | Obligatorio | T |
| RF-MEM-5 | Se escribe una tarjeta → su vector es el de (huella, modelo de la novela), y se calcula solo si ese par no existe: un contenido ya incrustado nunca se reincrusta. Copiar el índice de una versión no llama al productor de vectores: con un productor de prueba que cuenta sus llamadas, la copia hace cero | Obligatorio | T |
| RF-MEM-6 | Una novela tiene fijado su modelo de incrustación desde que se creó (RF-ENT-1) → todo vector de su índice, en todas sus versiones, es de ese modelo; cambiar después `retrieval.embedding_model` en la config no afecta a esa novela | Obligatorio | T |
| RF-MEM-7 | Para toda versión generada, reconstruir su índice desde su story bible y sus capítulos → da las mismas tarjetas, los mismos párrafos y las mismas filas de FTS5 que el guardado, también tras un cambio o una edición que reescribe un capítulo anterior y tras el reemplazo de un registro repetido (invariante 6) | Obligatorio | T |

### Recuperación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-8 | Se recuperan tarjetas para el capítulo *n* → solo son candidatas las de `desde_capitulo` ≤ *n* < `hasta_capitulo`, filtradas antes de puntuar. Frontera: la tarjeta nacida al aceptar el capítulo 3 no se ve en el 3 y sí en el 4, y su predecesora, al revés | Obligatorio | T |
| RF-MEM-9 | Se recupera prosa mientras se produce el capítulo *n* → solo son candidatos los párrafos de capítulos anteriores a *n*: en el capítulo 1 no hay ninguno. Al aplicar un cambio o una edición sobre una versión, la recuperación del editor abarca la prosa de todos sus capítulos | Obligatorio | T |
| RF-MEM-10 | Se recupera para una versión → solo salen unidades de esa versión de esa novela, y añadir a las mismas tablas unidades de otra novela no cambia el ranking: ninguna ventana contiene datos de otra novela (RT6, `verification.md` §4.9) | Obligatorio | T |
| RF-MEM-11 | Canal léxico → FTS5 solo da los candidatos por coincidencia, con `unicode61 remove_diacritics 2`, así que «cafe» encuentra «café»; BM25 se calcula en código sobre esos candidatos, con las estadísticas de la colección de esa versión tras el filtro. Una consulta con comillas, asteriscos u operadores de FTS5 se busca como palabras y no falla | Obligatorio | T |
| RF-MEM-12 | Se recupera de las CanonCards → cada tarjeta se puntúa por BM25 y por la distancia coseno de su vector al de la consulta, y las dos listas se funden por rango recíproco, con una constante fija del código. El desempate es por (tipo de entidad, id de entidad, `desde_capitulo`) | Obligatorio | T |
| RF-MEM-13 | Se recupera prosa → solo por BM25, sin incrustaciones, con desempate por (capítulo, ordinal) | Obligatorio | T |
| RF-MEM-14 | Una ventana recupera de las dos colecciones → cada colección da su propia lista, con su propio ranking: ninguna fusión mezcla una tarjeta y un párrafo | Obligatorio | T |
| RF-MEM-15 | Se recupera para un par (colección, consumidor) → entran como mucho las plazas de `retrieval.quotas` para ese par; con 0 no entra nada de esa colección, y las plazas que sobran no pasan a otro par. Con una config válida, la ventana del writer nunca lleva prosa | Obligatorio | T |
| RF-MEM-16 | Una colección tiene menos unidades que plazas → se entregan las que hay, sin bloquear, y en una ejecución queda un defecto no bloqueante con causa raíz `missing_context` en el informe. Frontera: en el capítulo 1 la prosa está vacía, y el editor sigue sin párrafos | Obligatorio | T |
| RF-MEM-17 | Se recupera una tarjeta de consecuencia o de restricción → entran además sus ancestros hasta el novum, vigentes en el capítulo *n*, cada uno como enunciado de una línea y sin consumir cuota; la cadena tiene como mucho tres consecuencias más el novum. Una tarjeta de personaje o de lugar no arrastra nada | Obligatorio | T |
| RF-MEM-18 | Consultas → la del writer es prospectiva, construida desde el outline del capítulo que va a escribir; la del crítico, retrospectiva, desde el texto que entregó el writer; la del editor, desde los defectos y el texto del capítulo. Una prueba dorada con una tarjeta que solo nombra el texto la da al crítico y no al writer, y otra con una que solo nombra el outline, al revés | Obligatorio | T |

### Residentes y entradas de la llamada

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-19 | Se ensambla la ventana de un consumidor → lleva exactamente los residentes, las entradas de la llamada y las colecciones de su fila de `architecture.md` §6.4: el writer, la StyleSheet, los elementos obligatorios asignados al capítulo, la proyección del outline, el `EstadoDelMundo` y el `ResumenRodante`, con los defectos bloqueantes si regenera, y recupera CanonCards; el crítico, los mismos residentes con todos los elementos obligatorios y el `CatalogoDeTropos`, con el capítulo y la rúbrica de capítulo, y recupera CanonCards; el editor, la StyleSheet y el `EstadoDelMundo`, con el capítulo y los defectos —en un cambio, el capítulo afectado entero con los párrafos numerados y la propuesta—, y recupera CanonCards y prosa; el linter de repetición, el capítulo, y recupera prosa. Los demás roles reciben sus entradas fijas (§7.2) y no recuperan nada | Obligatorio | T |
| RF-MEM-20 | Se proyecta el outline para el capítulo *n* → lleva los títulos de los 10 capítulos, los beats de *n* y los temas de las revelaciones de los capítulos posteriores, sin su contenido: el contenido de una revelación posterior nunca aparece | Obligatorio | T |
| RF-MEM-21 | Se construye el `ResumenRodante` del capítulo *n* → son los resúmenes de los capítulos 1..*n*−2 más el capítulo *n*−1 literal. Fronteras: en el 1 está vacío; en el 2 es el capítulo 1 literal, sin resúmenes; en el 3, el resumen del 1 y el capítulo 2 literal | Obligatorio | T |
| RF-MEM-22 | Se construye el `EstadoDelMundo` al empezar el capítulo *n* → lleva el momento actual de la historia; por personaje, su último lugar, si está excluido y los hechos que cambió algún delta real; y el estado de cada arco, abierto o resuelto. Sale de aplicar en orden los deltas reales de 1..*n*−1, y no lleva el detalle estable de cada entidad, que llega por las tarjetas | Obligatorio | T |
| RF-MEM-23 | Para toda secuencia generada de deltas reales, también con reescrituras de capítulos anteriores por un cambio o una edición → el `EstadoDelMundo` tras el capítulo *n* es la aplicación ordenada de los deltas reales de 1..*n* (invariante 4) | Obligatorio | T |

### Guardián de ventana

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-24 | Se va a abrir una sesión de rol → antes, el orquestador invoca al guardián de ventana, que cierra la ventana: lo que no cabe se niega ahí. Ningún rol tiene una tool para pedir contexto, y ningún modelo elige qué se suelta | Obligatorio | T |
| RF-MEM-25 | Cuota de una sesión de una ejecución → cuenta solo la entrada, y es la parte de la ejecución del techo, `operation.window_ceiling` − `operation.api_window_share`, dividida entre las sesiones de su ejecución en vuelo a la vez en esa etapa; la suma de sus cuotas nunca pasa de esa parte. Una sesión sola de la producción recibe la parte entera; el juez y el revisor visual en el gate, la mitad cada uno, porque Lean no consume tokens; *k* editores de un cambio, un *k*-ésimo cada uno | Obligatorio | T |
| RF-MEM-26 | Una sesión que corre en la API, fuera de una ejecución —un turno de la entrevista, el extractor o la interpretación de un cambio— → antes de abrirse reserva como cuota su mínimo —gastos fijos, entradas y reserva de turnos— en la parte de la API, `operation.api_window_share`, y la libera al cerrarse, también si termina mal. Si no cabe en lo que queda libre, espera como mucho `operation.api_window_wait_seconds` a que se libere sitio; si sigue sin caber, devuelve «sin sitio» sin abrirla, y quien la abre responde 503 (005, 015). Para toda secuencia generada de reservas y liberaciones concurrentes, la suma de las cuotas reservadas nunca pasa de `api_window_share`. La cuenta la lleva en memoria el proceso de la API, sin coordinarse con el worker | Obligatorio | T |
| RF-MEM-27 | Unas sesiones paralelas de una ejecución no caben con su mínimo —gastos fijos, intocables y reserva de turnos— en su parte del techo → van en serie, una detrás de otra, cada una con la parte de la ejecución entera | Obligatorio | T |
| RF-MEM-28 | Se ensambla la ventana de una sesión → en la cuota menos los gastos fijos de su rol y menos su reserva de turnos, que es (`max_turns` − 1) × (`max_output` + `max_tool_output`) de su rol. Los gastos fijos —prompt de sistema, `CLAUDE.md` del workspace y descripciones de skills y tools— se estiman en cada sesión con el estimador local sobre los textos que envía el código; lo que añada el CLI por su cuenta sale como deriva al reconciliar (RF-MEM-34). Frontera: con `max_turns` = 1, la reserva es 0 | Obligatorio | T |
| RF-MEM-29 | La ventana no cabe → se recorta en el orden declarado y la sesión sigue: primero la prosa; después las CanonCards, de la de peor rango de su colección hacia arriba; y por último el `ResumenRodante`, de su resumen más antiguo al capítulo anterior literal. Son intocables los demás residentes, el arrastre y las entradas de la llamada. Cada unidad recortada va a los negados de la ventana y, en una ejecución, deja `missing_context` en el informe | Obligatorio | T |
| RF-MEM-30 | Lo intocable, los gastos fijos y la reserva de turnos ya superan la cuota, con el `ResumenRodante` recortado entero → el guardián no abre la sesión y declara `infeasible_config` con las cifras: en una ejecución, la ejecución se bloquea con ese motivo (007); fuera de una ejecución, cuando la sesión no cabría ni con la parte de la API entera libre, no espera, y responde quien la abre, según su spec (005 y 015) | Obligatorio | T |
| RF-MEM-31 | Para toda ventana, config y conjunto de sesiones en vuelo generados → los gastos fijos estimados más la ventana más la reserva de turnos no pasan de la cuota de la sesión, y la suma de las cuotas en vuelo de la ejecución y de la API no pasa de `window_ceiling`: la cuota se cumple por construcción, sin cortar ninguna sesión en vivo | Obligatorio | T |
| RF-MEM-32 | Una tool devuelve algo al modelo —un acuse, un error de schema, la lista de defectos del hook o una denegación— → según el estimador local, nunca pasa de `max_tool_output`: lo que sobra se trunca con una nota que lo dice | Obligatorio | T |

### Conteo y reconciliación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-33 | Se cuenta la entrada → con un estimador local, sin llamar a ningún proveedor: antes de abrir la sesión, para ensamblar la ventana, y turno a turno sobre los mensajes que ve pasar el orquestador. La sesión guarda la suma estimada de todos sus turnos | Obligatorio | T |
| RF-MEM-34 | Se cierra una sesión → su suma estimada se compara con su entrada exacta, los tokens de entrada más los de lectura y escritura de caché de su uso. Si \|estimada − exacta\| / exacta supera `count_drift_threshold`, se anota la causa raíz `count_drift`: en una ejecución, como defecto no bloqueante en el informe; fuera, la sesión guarda los dos conteos. No bloquea ni reintenta. Frontera: una divergencia igual al umbral no se anota | Obligatorio | T |

### Ventana guardada y trazabilidad

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-35 | Se abre una sesión de rol → queda guardada su `VentanaDeContexto`: consumidor, capítulo, residentes, entradas de la llamada, recuperados por colección, negados con su causa —cuota o recorte—, cuota de entrada y tokens de entrada ocupados | Obligatorio | T |
| RF-MEM-36 | Se acepta un capítulo → su `Trazabilidad` registra los hechos que usa, las CanonCards de la ventana de la sesión que entregó el texto aceptado y los elementos obligatorios que le asigna el outline (invariante 7). Una prueba dorada con una ventana conocida da la trazabilidad esperada | Obligatorio | T |
| RF-MEM-37 | Al cerrar 008 → la cabecera de `architecture.md` §6.1 lleva el explainer de contexto y memoria: RAG híbrido sin re-ranking, residentes y el techo de 100.000 tokens | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | El recuperador y el guardián de ventana son deterministas: con el mismo índice, la misma consulta, la misma config y la misma cuota dan la misma ventana, unidad a unidad y en el mismo orden, sin llamar a ningún modelo. Las pruebas doradas, sobre un índice de fixture con sus vectores guardados y la cuota como entrada («capítulo 4, crítico, 50k»), cubren cada caso de `verification.md` §3.11 | T |

## Docs de referencia

- `architecture.md` §6 entero, §7.1 (guardián y recuperador son código), §7.2 (entradas fijas de los roles que no recuperan), §7.4 (ninguna tool pide contexto; `max_tool_output`), §8.3 (tarjetas y párrafos en la aceptación) y §9.3 (copia del índice).
- `definitions.md` §3 (`Parrafo`, `Outline`), §4 entero, §5 (guardián de ventana, recuperador), §6 (causas raíz `contexto ausente` y `deriva del conteo`), §11 (`retrieval`, `window_ceiling`, `api_window_share`, `api_window_wait_seconds`, `count_drift_threshold`) y §12.
- `verification.md` §3.6 (invariantes 4 y 6), §3.11, §4.4, §4.9 (RT6), §5 («Recuperador y guardián de ventana», «Presupuesto, límites y techo de entrada», invariantes 4, 6 y 7) y §6 (riesgo 5).
