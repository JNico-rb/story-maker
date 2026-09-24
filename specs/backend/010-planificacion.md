# 010 — Planificación

> Carril: A · Depende de: 003-puerto-de-agente, 004-observabilidad, 009-story-bible-y-versiones · Estado: borrador

## Objetivo

Llevar una ejecución `generation` desde que arranca hasta su punto de control del capítulo 0. Primero nace la candidata con el canon del brief, que escribe el código. Después el planner, en una sesión de rol con entradas fijas, entrega el plan por `submit_plan` y el validador `outline` lo juzga. Un plan rechazado se replanifica en una sesión nueva con los defectos, hasta `max_retries.plan`. El plan aceptado se aplica en una sola transacción, que es el `PuntoDeControl` 0, y la ejecución pasa a la fase `writing`. Es la fase `planning` de `architecture.md` §9.1, la caja «canon del brief + plan» del flujo de §2.

## Alcance

- La candidata de la generación y el canon del brief (§4.1, §9.3), fechado según `domain-knowledge.md` §5.2.
- La `VentanaDeContexto` del planner en modo `plan` (§5.1, §6.2, §7.2) y el `CatalogoDeTropos` curado que recibe como lista de evitación (`domain-knowledge.md` §6). Ver Autorrevisión: el catálogo lo asigna hoy a 012 la tabla de propiedad del backend.
- El contenido de la entrega `submit_plan` (§5.1): lo que su schema acepta y rechaza, y qué campos son narrativos para la policy (§7.5).
- El validador `outline` (§5.2, §11.2): sus defectos, su `ResultadoDeValidador` y su score.
- Intentos y `Veredicto` del evaluable `plan` (§7.6), replanificación y fallo.
- La aplicación del plan en una transacción (§5.4): mundo, reparto, lugares, hechos, eventos planificados, outline, StyleSheet (§5.3), título, CanonCards iniciales con su `desde_capitulo` (§6.3) y punto de control 0.
- Qué hace la fase cuando se relanza tras una interrupción, ante un fallo del proveedor y ante una reserva inviable en el `TechoDeTokens`.
- El prompt del planner en modo `plan`.
- Las cifras provisionales (`max_retries.plan`, límites del rol, `token_ceiling`) salen de la config; las pruebas las fijan con su propia config y esta spec no fija ninguna (§17.1).

## Fuera de alcance

- Lanzar la ejecución (`Configurar`, sus 409), la cola, el worker que la toma, reanudar por API o CLI, el `InformeDeEjecucion` y el paso de `running` a `interrupted` al arrancar el servidor → 011-produccion-de-capitulos. Esta spec describe qué hace la fase cuando la lanzan o la relanzan.
- La fase `writing` y las ventanas del writer y del editor (proyección del outline, residentes) → 011-produccion-de-capitulos.
- El texto de cada CanonCard, su huella, su índice léxico y denso y el recuperador → 016-recuperacion-hibrida. Aquí solo se decide qué tarjetas iniciales nacen, con qué `desde_capitulo` y en qué transacción.
- Los repositorios de la story bible, la copia de versiones y la API de la story bible → 009-story-bible-y-versiones.
- El mecanismo de las sesiones de rol → 003-puerto-de-agente: lista blanca en la sesión, `schema-salida` con el error devuelto al modelo, hooks, reserva y espera en el techo, `max_turns`, `session_timeout_seconds`, desenlace, uso y coste de la `SesionDeRol` y spans `rol:` y `tool:`. El motor de políticas, `palabras-prohibidas`, la normalización y el `AuditLog` → 005-guardarrailes. El adaptador de Langfuse, la máscara y `prompts push` → 004-observabilidad. El puerto de observabilidad y su doble nulo → 001-base.
- El schema del brief, incluido cómo se declara un recuerdo excluyente; los faltantes y C1–C6 → 008-brief-y-entrevista.
- El planner en modo `change` (`propose_change`) y su parte del prompt → 014-cambios-del-lector.
- El uso del catálogo en `no-cliche`, la prueba de validez del catálogo (`domain-knowledge.md` §6.2, paso 2) y el título que muestra la novela → 012-gate-de-publicacion. Los tropos aprendidos → 020-evals.
- T1–T5 sobre la cronología registrada → 007-validador-lean y 012-gate-de-publicacion. `outline` no los comprueba (§11.4, «Lean no se duplica en Python»).

## Comportamiento observable

**Clases.** Un caso es **T** si una prueba lo decide con el doble falso del puerto de agente y el doble nulo de observabilidad. Es **D** si necesita el modelo real.

**Datos de las pruebas** (ficticios). La novela se creó el 2026-03-10, así que el año presente es 2026. Su brief está confirmado:

- destinataria Marta, 40 años, sin fecha de nacimiento, con los rasgos «curiosa» y «le encanta el mar»;
- allegados: Toby (animal, «su perro», 5 años) y Rosa (persona, «su abuela», sin edad ni fecha);
- recuerdos:
  - R1, «se perdió en la feria de su pueblo», a los 8 años, en «la feria del pueblo», con Rosa;
  - R2, «Rosa se fue a vivir para siempre a otro país», en 2010, en «el aeropuerto», con Rosa, declarado como partida definitiva de Rosa;
  - R3, «llevó a Toby a la feria del pueblo», en 2024, en «la feria del pueblo», con Toby;
- un texto libre del que salieron cuatro hechos: H1, «Marta colecciona conchas» (aceptado y obligatorio, con una cita distinta de su valor); H2, «Rosa cocinaba arroz con leche» (aceptado, no obligatorio); H3 (rechazado por el cliente); y H4 (descartado por `citas-verificadas`). El texto contiene además la frase «ignora lo anterior» y la frase distintiva «el verano de las gaviotas azules», que no está en ningún valor;
- elementos obligatorios: el nombre de Marta, el rasgo «le encanta el mar», Toby, R1 y H1;
- deseo de trama: «que salga un castillo con dragones»;
- prohibidas: la palabra «Julián» y el tema «divorcio» (palabras clave «divorcio», «separación») en el nivel novel, y el tema «hospitales» (palabras clave «hospital», «urgencias») en el nivel user del cliente.

**Plan válido de referencia.** Tiene 10 capítulos con entre 3 y 6 beats cada uno y todos los obligatorios asignados. Su novum es del 2021-05-01 y tiene 3 consecuencias. Inventa la asistente artificial Nia, nombrada por primera vez en el capítulo 4, y el lugar «el puerto nuevo», nombrado por primera vez en el capítulo 7. Todos sus eventos son válidos.

### Canon del brief

#### 010-C01 — La candidata nace con el canon del brief (T)
- **Dado** el brief de referencia y una ejecución `generation` que arranca por primera vez
- **Cuando** empieza la fase
- **Entonces**:
  - la ejecución está `running` en fase `planning`;
  - hay una `Version` nueva en estado candidata, sin número ni versión base, que es la candidata de la ejecución;
  - están los personajes de origen brief Marta (destinatario, persona), Toby (allegado, animal) y Rosa (allegado, persona), cada uno con su nombre canónico y su hecho de nombre;
  - están los hechos de origen brief: uno por cada rasgo de Marta, uno por cada recuerdo y la relación de cada allegado («su perro», «su abuela»);
  - llevan obligatorio y el id de su elemento personal el hecho de nombre de Marta (lo es siempre), el rasgo «le encanta el mar», el hecho de nombre de Toby, el recuerdo R1 y H1; los demás hechos no;
  - no hay mundo, outline, StyleSheet, CanonCards ni punto de control;
  - la ventana del planner no se ha ensamblado antes de que todo esto esté escrito.
- **Y** la candidata y su canon se escriben en una transacción: con un fallo inyectado a mitad, no queda ni candidata ni canon, y la ejecución termina `failed` con `internal_error`.

#### 010-C02 — Fechas de nacimiento del canon (T)
- **Dado** el brief de referencia y, aparte, un brief igual cuya destinataria declara nacer el 2000-02-29
- **Cuando** se escribe el canon
- **Entonces** las fechas de nacimiento son estas:
  - Marta, 1986-01-01 a las 00:00 (sin fecha declarada: el 1 de enero de 2026 − 40);
  - Toby, 2021-01-01 a las 00:00 (solo tiene edad);
  - Rosa no tiene fecha de nacimiento;
  - la destinataria del segundo brief, 2000-02-29 a las 00:00, que es la declarada.

#### 010-C03 — Fechado de los recuerdos (T)
- **Dado** los recuerdos de la tabla
- **Cuando** se escribe el canon
- **Entonces** cada uno da un evento de origen brief con el momento y la edad declarada de la destinataria que dice la tabla (`domain-knowledge.md` §5.2)

| Nacimiento de la destinataria | Recuerdo | Momento | Edad declarada |
|---|---|---|---|
| 1986-01-01 | R1, a los 8 años | 1994-01-01 12:00 | 8 |
| 1986-01-01 | R2, en 2010 | 2010-01-01 12:00 | ninguna |
| 1986-01-01 | uno en 1986, su año de nacimiento | 1986-01-02 12:00 | ninguna |
| 2000-02-29 | uno a los 9 años (2009 no es bisiesto) | 2009-03-01 12:00 | 9 |
| 2000-02-29 | uno a los 8 años (2008 sí lo es) | 2008-02-29 12:00 | 8 |

#### 010-C04 — Eventos y lugares de los recuerdos (T)
- **Dado** el brief de referencia
- **Cuando** se escribe el canon
- **Entonces**:
  - R1, R2 y R3 son tres eventos de origen brief, sin capítulo ni beat y sin analepsis;
  - sus presentes son la destinataria más los allegados que declara cada recuerdo: Marta y Rosa en R1 y R2, Marta y Toby en R3;
  - R2 es excluyente, con Rosa como excluida; R1 y R3 son ordinarios y no tienen excluido;
  - hay dos lugares de origen brief, «la feria del pueblo» y «el aeropuerto», y R1 y R3 comparten el mismo lugar, porque un nombre de lugar idéntico es un solo `Lugar`.

#### 010-C05 — Hechos extraídos en el canon (T)
- **Dado** el brief de referencia
- **Cuando** se escribe el canon
- **Entonces**:
  - H1 y H2 son hechos de origen free_text con su sujeto, Marta y Rosa;
  - H1 lleva obligatorio y el id de su elemento personal, y H2 no;
  - ni H3 ni H4 están en la story bible.

### Ventana y entrega

#### 010-C06 — Ventana del planner (T)
- **Dado** la candidata de 010-C01
- **Cuando** se abre la sesión del planner en modo `plan` y el doble falso captura su ventana
- **Entonces** la ventana contiene:
  - el brief confirmado: destinataria, allegados, recuerdos, ocasión, género, tono, extensión, dedicatoria, entradas prohibidas de nivel novel, el deseo de trama y los elementos personales con su obligatoriedad. De los hechos extraídos aceptados entran solo sujeto, atributo y valor;
  - la story bible inicial de la candidata con sus identificadores (personajes, lugares, hechos con su obligatoriedad y su elemento personal, eventos de origen brief) y el año presente, 2026;
  - el `CatalogoDeTropos` como lista de evitación, cada tropo con sus marcadores.
- **Y** la única tool de la sesión es `submit_plan`.
- **Y no** aparecen en ella el contenido del texto libre, «ignora lo anterior», «el verano de las gaviotas azules», la cita de H1, los valores de H3 y H4, ninguna CanonCard recuperada ni prosa de capítulo.

#### 010-C07 — Catálogo de tropos curado (T)
- **Dado** el `CatalogoDeTropos`
- **Cuando** una prueba lo recorre
- **Entonces** contiene al menos los siete tropos de `domain-knowledge.md` §6: singularidad redentora o apocalíptica, rebelión de las máquinas, IA que desarrolla conciencia o descubre el amor, último humano con empleo, renta básica distópica, vigilancia total y dilema del tranvía algorítmico
- **Y** cada tropo tiene nombre, al menos un marcador y origen curado; ninguno es aprendido. Que los marcadores estén escritos al nivel del mecanismo narrativo (§6.1) es 010-I8.

#### 010-C08 — Schema de `submit_plan` (T)
- **Dado** una sesión del planner con quedan intentos
- **Cuando** entrega `submit_plan` con un mundo de 1 consecuencia, con uno de 5, o con un novum de ámbito fuera de tecnológico, social o cognitivo
- **Entonces** la entrega no pasa el schema: el error vuelve al modelo en la misma sesión (mecanismo de 003), el intento se cierra con `rewrite` y el planner puede corregir sin sesión nueva
- **Y** con 2 y con 4 consecuencias la entrega pasa el schema. El número de capítulos y el de beats no los rechaza el schema, sino `outline` (010-C11).

#### 010-C09 — Policy sobre la entrega del plan (T)
- **Dado** una sesión del planner
- **Cuando** entrega un plan con «Julián» en la descripción de un beat, o con «Julián» en el título de la novela, o con «separación» en una consecuencia del mundo
- **Entonces** el hook de policy deniega la entrega con el término y su nivel (005), la decisión queda en el `AuditLog` con origen `policy_hook`, el intento se cierra con `rewrite` y el planner corrige en la misma sesión
- **Y** un plan cuyo léxico a evitar contiene «Julián», «divorcio» y «separación» se permite: la policy no escanea el léxico a evitar (§7.5)
- **Y** una llamada del planner a una tool que no es `submit_plan` se deniega por la lista blanca, no es una entrega y no consume intento; la sesión la acota `max_turns`.

Son campos narrativos del plan todos sus textos salvo el léxico a evitar: el mundo, el reparto, los lugares, los valores de sus hechos, los títulos y la función en el arco de cada capítulo del outline, los beats con sus eventos y revelaciones, y el título de la novela.

### Validador `outline`

#### 010-C10 — Un plan válido pasa (T)
- **Dado** el plan válido de referencia, que no incluye el deseo de trama
- **Cuando** `outline` lo juzga
- **Entonces** pasa sin defectos y el `Veredicto` del intento es `accept`: ningún validador exige que se cumpla un deseo de trama (`definitions.md` §1, `DeseoDeTrama`).

#### 010-C11 — Capítulos y beats (T)
- **Dado** el plan de referencia modificado como dice la tabla
- **Cuando** `outline` lo juzga
- **Entonces** da el resultado de la tabla

| Plan | Resultado |
|---|---|
| 9 capítulos | Defecto de número de capítulos |
| 11 capítulos | Defecto de número de capítulos |
| 10 capítulos | Sin defecto de número |
| El capítulo 5 con 2 beats | Defecto atribuido al capítulo 5 |
| El capítulo 5 con 7 beats | Defecto atribuido al capítulo 5 |
| El capítulo 5 con 3 beats y el 6 con 6 | Sin defecto de beats |

#### 010-C12 — Elementos obligatorios asignados (T)
- **Dado** el plan de referencia modificado como dice la tabla
- **Cuando** `outline` lo juzga
- **Entonces** da el resultado de la tabla

| Plan | Resultado |
|---|---|
| R1 sin capítulo asignado | Defecto que nombra el elemento R1 |
| El nombre de Marta sin capítulo asignado | Defecto que nombra ese elemento: es obligatorio siempre |
| H1 asignado solo al capítulo 11 | Defecto: capítulo fuera de 1–10; H1 queda sin asignar |
| Una asignación a un elemento que no existe en el brief | Defecto de referencia |
| Cada obligatorio asignado a uno o más capítulos del 1 al 10 | Sin defecto de asignación |

#### 010-C13 — Momentos de los eventos y año presente (T)
- **Dado** la novela creada el 2026-03-10 y la fase ejecutándose el 2027-01-02, así que el año presente sigue siendo 2026 (`definitions.md` §3, `Novela`)
- **Cuando** `outline` juzga eventos planificados con estos momentos
- **Entonces** da el resultado de la tabla

| Evento planificado | Resultado |
|---|---|
| No analepsis, 2026-01-01 00:00 | Válido |
| No analepsis, 2026-12-31 23:59 | Válido |
| No analepsis, 2025-12-31 23:59 | Defecto: fuera del año presente |
| Analepsis, 2025-12-31 23:59 | Válido |
| Analepsis, 2026-02-01 | Válido |
| Analepsis o no, 2027-01-01 00:00 | Defecto: posterior al año presente |

#### 010-C14 — Referencias y tipo de evento (T)
- **Dado** el plan de referencia modificado como dice la tabla
- **Cuando** `outline` lo juzga
- **Entonces** da el resultado de la tabla. Una referencia es válida si apunta a una entidad de la story bible inicial o a una que el mismo plan inventa.

| Plan | Resultado |
|---|---|
| Un evento con un presente que no existe | Defecto atribuido al capítulo del evento |
| Un evento con un lugar que no existe | Defecto atribuido al capítulo del evento |
| Un evento excluyente con un excluido que no existe | Defecto |
| Un evento excluyente sin excluido | Defecto |
| Un evento ordinario con excluido | Defecto |
| Un beat que usa un personaje o un hecho que no existe | Defecto atribuido a su capítulo |
| Un hecho inventado cuyo sujeto no existe | Defecto |
| Una excepción de tratamiento con un personaje que no existe | Defecto |
| Eventos con Marta, Rosa, Nia, «la feria del pueblo» y «el puerto nuevo» | Válido |

#### 010-C15 — Fecha del novum (T)
- **Dado** el plan de referencia con el novum del 2025-12-31, y después del 2026-01-01
- **Cuando** `outline` lo juzga
- **Entonces** el del 2025-12-31 es válido y el del 2026-01-01 es un defecto: el novum no es anterior al año presente.

#### 010-C16 — `outline` no juzga la cronología (T)
- **Dado** el plan de referencia con dos cambios: Rosa está presente en un evento planificado del capítulo 5, posterior a su partida definitiva (R2); y un evento del capítulo 3, sin analepsis, es anterior a uno del capítulo 2
- **Cuando** `outline` lo juzga
- **Entonces** pasa sin defectos: T1–T5 los comprueba Lean sobre la cronología registrada, nunca sobre la planificada (§4.5, §11.4).

### Intentos del plan

#### 010-C17 — Replanificación con los defectos (T)
- **Dado** `max_retries.plan` = 2 y un doble del planner cuya primera sesión entrega un plan de 9 capítulos y la segunda el plan de referencia
- **Cuando** corre la fase
- **Entonces**:
  - el intento 1 se cierra con `rewrite` y se abre una sesión nueva del planner;
  - su ventana es la de 010-C06 más los defectos del intento 1, sin el plan rechazado;
  - el intento 2 se cierra con `accept` y se aplica el plan (010-C20);
  - hay dos sesiones del planner y dos intentos del evaluable `plan`, numerados 1 y 2.

#### 010-C18 — Una sesión sin entrega cuenta como intento (T)
- **Dado** una sesión del planner que termina sin ninguna entrega válida de `submit_plan`, porque agota `max_turns`, porque agota `session_timeout_seconds` o porque acaba sin llamarla
- **Cuando** se cierra
- **Entonces** es un intento fallido con un defecto de `schema-salida` que dice «sin entrega» y el motivo, y su veredicto sigue la regla de siempre
- **Y** si queda intento, la sesión siguiente recibe ese defecto.

#### 010-C19 — Intentos agotados (T)
- **Dado** `max_retries.plan` = 2 y tres sesiones seguidas del planner que entregan planes rechazados por `outline`
- **Cuando** se juzga el tercero
- **Entonces**:
  - su veredicto es `fail` y no se abre una cuarta sesión;
  - la ejecución termina `failed` con `retries_exhausted` y la candidata pasa a descartada;
  - la candidata solo tiene el canon del brief y no hay punto de control.
- **Y** con `max_retries.plan` = 1, si una sola sesión entrega primero un plan fuera de schema y después uno con «Julián», la segunda denegación cierra el último intento con `fail`. La sesión termina con desenlace `cut` y la ejecución termina `failed` con `retries_exhausted`. No es `banned_content`: ese motivo es de los capítulos (§7.6).

### Aplicación del plan

#### 010-C20 — El plan aceptado se aplica en una transacción (T)
- **Dado** el plan de referencia aceptado
- **Cuando** se aplica
- **Entonces** tras una sola transacción la candidata tiene:
  - el mundo con su novum (descripción, ámbito, fecha) y sus 3 consecuencias;
  - Nia como personaje inventado (especie artificial, origen inventado) y «el puerto nuevo» como lugar inventado;
  - los hechos del plan como hechos nuevos de origen inventado, no obligatorios, también los que tienen por sujeto a un personaje del brief;
  - los eventos planificados con su capítulo y beat, momento, lugar, presentes, tipo, excluido y analepsis;
  - los 10 capítulos del outline con su título, su función en el arco, sus beats (revelaciones con tema y contenido incluidas) y la asignación de los obligatorios;
  - la StyleSheet (010-C21), el título de la novela y las CanonCards iniciales (010-C22).
- **Y** en esa misma transacción se escriben el `PuntoDeControl` 0 de la ejecución, el desenlace `accept` del intento y el paso a la fase `writing`
- **Y** los personajes, lugares, hechos y eventos de origen brief y free_text son idénticos a los de antes: el plan añade y nunca modifica.

#### 010-C21 — StyleSheet (T)
- **Dado** el plan de referencia, cuya StyleSheet propone narrador, tiempo verbal, tratamiento por defecto con una excepción entre Marta y Rosa, y un léxico a evitar que no contiene ningún tema prohibido
- **Cuando** se aplica
- **Entonces**:
  - la StyleSheet guarda lo propuesto;
  - su registro es el de la `FranjaDeEdad` de la destinataria: adulto para Marta, e infantil con una destinataria de 9 años;
  - su léxico a evitar añade cada tema prohibido que aplica a la novela, en sus tres niveles, con su término y sus palabras clave: «divorcio» (novel) y «hospitales» (user);
  - la palabra «Julián» no se añade, porque una palabra no es un tema: la caza la policy.

#### 010-C22 — CanonCards iniciales (T)
- **Dado** el plan de referencia más un personaje inventado que ningún beat nombra
- **Cuando** se aplica
- **Entonces** nace una CanonCard por cada personaje, cada lugar y el mundo, con este `desde_capitulo`:
  - Marta, Toby, Rosa, «la feria del pueblo», «el aeropuerto» y el mundo, 1, porque son del brief o son el mundo;
  - Nia, 4;
  - «el puerto nuevo», 7;
  - el personaje que ningún beat nombra, 1.

Un beat nombra una entidad si la tiene entre sus personajes, si es presente, excluida o lugar de uno de sus eventos, o si es sujeto de uno de los hechos que usa. El texto, la huella y el índice de cada tarjeta → 016-recuperacion-hibrida.

#### 010-C23 — La transacción de aplicación falla (T)
- **Dado** un fallo inyectado en la transacción de aplicación, con parte del plan ya escrita
- **Cuando** se produce
- **Entonces**:
  - la candidata no tiene nada del plan (ni mundo, ni entidades o hechos inventados, ni eventos planificados, ni outline, ni StyleSheet, ni CanonCards);
  - no hay punto de control 0;
  - el intento aceptado queda sin desenlace y no cuenta;
  - si el fallo es una excepción del código, la ejecución termina `failed` con `internal_error` y la candidata pasa a descartada. Si el proceso cae en ese punto, al relanzarla se replanifica sin haber gastado ese intento (010-C24).

### Relanzamiento e infraestructura

#### 010-C24 — Relanzar antes del punto de control 0 (T)
- **Dado** `max_retries.plan` = 2 y una ejecución interrumpida en fase `planning`, con el intento 1 cerrado en `rewrite` y el intento 2 abierto al caer
- **Cuando** se relanza (reanudación: 011)
- **Entonces**:
  - la candidata es la misma;
  - el canon del brief no se reescribe: mismos personajes, hechos, eventos y lugares, sin duplicados;
  - se abre una sesión del planner con los defectos del intento 1, que cuenta como intento 2 (el cortado no contó) y todavía permite un intento 3.

#### 010-C25 — Relanzar tras el punto de control 0 (T)
- **Dado** una ejecución interrumpida con su punto de control 0 ya escrito
- **Cuando** se relanza
- **Entonces**:
  - no se abre el planner ni se cuenta ningún intento del plan;
  - no se duplican ni cambian el mundo, las entidades, los hechos, los eventos, el outline, la StyleSheet ni las CanonCards;
  - no se escribe otro punto de control 0;
  - la ejecución sigue en `writing`, en el capítulo 1 (011).

#### 010-C26 — Fallo del proveedor (T)
- **Dado** una sesión del planner que termina con desenlace `infrastructure_failure`, por ejemplo por el límite de uso de la suscripción
- **Cuando** se cierra
- **Entonces**:
  - la ejecución pasa a `interrupted` con `provider_error`;
  - el intento abierto queda sin desenlace y no cuenta;
  - la candidata sigue siendo candidata;
  - no se abre otra sesión.

#### 010-C27 — Reserva inviable en el techo (T)
- **Dado** un `token_ceiling` de prueba menor que la reserva de la sesión del planner, que calcula 003
- **Cuando** llega el momento de abrirla
- **Entonces**:
  - no se abre ninguna sesión ni se cuenta ningún intento;
  - la ejecución termina `failed` con `infeasible_config`;
  - la candidata, que ya tiene el canon del brief, pasa a descartada.

#### 010-C28 — Una generación nueva tras un fallo tiene su propia candidata (T)
- **Dado** una novela cuya generación anterior terminó `failed` con su candidata A descartada
- **Cuando** arranca otra ejecución de generación (su lanzamiento es de 011)
- **Entonces** nace una candidata B con su propio canon del brief, que es la de la nueva ejecución, y A sigue descartada e intacta.

### Observabilidad

#### 010-C29 — Resultado y score de `outline` (T)
- **Dado** la fase de 010-C17 con el doble nulo de observabilidad
- **Cuando** `outline` juzga cada plan
- **Entonces**, por cada juicio:
  - hay un `ResultadoDeValidador` con la ejecución, la candidata, el validador `outline`, sin capítulo, si pasa, el score 0/1 y los defectos;
  - el doble nulo recibe un span `validador:outline` y un score `outline` (0 en el intento 1 y 1 en el 2), con los defectos en el comentario, asociados a la traza de la ejecución, cuya sesión es la novela.
- **Y** cada sesión del planner deja su `SesionDeRol` y sus spans `rol:planner` y `tool:submit_plan` por el mecanismo de 003.

### Demostración

#### 010-C30 — Planificación con el modelo real (D)
- **Dado** el brief de referencia importado y una máquina con sesión de Claude Code (`LLM_PROVIDER=claude_login`), una sola vez al final de la spec
- **Cuando** corre la fase `planning`
- **Entonces**:
  - el plan pasa `outline` en 1 + `max_retries.plan` intentos como mucho y se aplica;
  - el novum dice qué capacidad apareció, cuándo y qué dejó de ser cierto, en un tono compatible con la ocasión (`domain-knowledge.md` §3.3, §3.4);
  - el castillo con dragones aparece adaptado al presente post-IA, sin marcos (§4.5);
  - no aparece ningún tropo del catálogo;
  - la `SesionDeRol` registra el uso y el coste, y la traza se ve en Langfuse.
- El resultado se anota con el commit y la etiqueta de prompts (`verification.md` §6 U27).

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 010-I1 | Ninguna ventana del planner contiene el contenido de un `TextoLibre` ni la cita de un `HechoExtraido`: de un hecho aceptado solo llegan sujeto, atributo y valor | T | Sobre cada ventana que captura el doble falso en 010-C06, 010-C17 y 010-C24 |
| 010-I2 | Planificar no modifica ni borra nada de origen brief o free_text: el canon escrito al arrancar sigue idéntico tras cada intento, tras la aplicación y tras relanzar | T | Comparación del canon antes y después en 010-C17, 010-C20 y 010-C24 |
| 010-I3 | Una entrega rechazada (schema, policy, `outline` o sin entrega) no deja nada en la candidata: hasta la aplicación, la candidata solo tiene el canon del brief | T | Estado de la candidata tras 010-C08, 010-C09, 010-C11–C15, 010-C18 y 010-C19 |
| 010-I4 | Los intentos del evaluable `plan` nunca superan 1 + `max_retries.plan`, contando los de antes de una reanudación; el cortado por una caída o un fallo del proveedor no cuenta | T | 010-C19, 010-C24 y 010-C26; refuerzo A: `ReintentosAcotados` (006-especificacion-tla) |
| 010-I5 | El punto de control 0 existe si y solo si el plan está aplicado, se escribe una sola vez, y relanzar con él nunca abre el planner | T | 010-C20, 010-C23 y 010-C25; refuerzo A: `ReanudacionSinDuplicarNiPerder` (006) |
| 010-I6 | `outline` es determinista y exhaustivo: el mismo plan con la misma story bible da los mismos defectos, y los da todos en un solo juicio | T | Dos juicios del mismo plan comparados; un plan con defectos de capítulos, de momento y de referencia devuelve los tres |
| 010-I7 | El plan y los defectos de `outline` están tipados de extremo a extremo, y el schema de `submit_plan` es el derivado de su modelo | A | Tipado estricto y análisis estático (`verification.md` §3.1, §3.2); la prueba de contrato común de las tools de 003 cubre `submit_plan` (§3.5) |
| 010-I8 | El prompt del planner en modo `plan` le pide cuatro cosas: un novum concreto (capacidad, fecha anterior al año presente, 2 a 4 consecuencias compatibles con la ocasión y el tono); adaptar al presente post-IA, sin marcos, el deseo que no cabe y dejar tal cual el que cabe; evitar los tropos del catálogo salvo los pedidos; y no contradecir los hechos del brief. Los marcadores del catálogo están al nivel del mecanismo narrativo | I | El `verificador` lee el prompt y el catálogo al cerrar (`domain-knowledge.md` §3.3, §4.5, §6.1) |
| 010-I9 | Cada transición de la fase corresponde a una acción de `Harness.tla`: empezar la fase es `Planificar`; juzgar un plan es `Validar`; una sesión nueva, `Reintentar`; `retries_exhausted`, `infeasible_config` o `internal_error` son `Fallar`; un fallo del proveedor es `Caer` | I | Tabla acción ↔ código del README, revisada por el `verificador` (`verification.md` §4.10; 006, 011) |
| 010-I10 | Con el modelo real, el plan cumple `outline` dentro del límite y su contenido respeta 010-I8 | D | 010-C30 |
| 010-I11 | Que el novum sea plausible y que la adaptación de un deseo sea buena no lo verifica nada | U | Riesgo aceptado `verification.md` §6 U24 (y U1) |

## Scores y trazas

| Nombre | Dónde | Valor |
|---|---|---|
| `outline` | Span `validador:outline` en la traza de la ejecución (`generacion`, sesión = novela), uno por juicio | 0/1, con los defectos en el comentario |
| `schema-salida`, `palabras-prohibidas` | Span `tool:submit_plan` (WARNING si se deniega), por el mecanismo de 003 y 005 | 0/1 |
| `rol:planner` y su `LlamadaDeModelo` | Uno por sesión del planner, por el mecanismo de 003 y 004 | Uso, coste, latencia y versión de prompt |

## Docs referenciados

- `architecture.md`:
  - §2 (flujo: «Planificación = canon del brief + plan»), §4.1–§4.5 (canon del brief, mundo, inmutabilidad, tiempo, cronología), §5.1–§5.4 (planificación, `outline`, StyleSheet, aplicación);
  - §6.2 (el planner no recupera), §6.3–§6.4 (CanonCards iniciales en la transacción), §6.5 (reserva e `infeasible_config`);
  - §7.2 (rol planner), §7.4 (tools con schema), §7.5 (hook de policy y campos narrativos), §7.6 (intentos, límites, infraestructura), §7.7 (ningún rol escribe canon);
  - §9.1 (máquina de estados, `Planificar`, `Validar`, motivos), §9.2 (punto de control 0 y reanudación), §9.3 (candidata de generación, descarte);
  - §11.2 (fila `outline`), §11.4 (Lean no se duplica), §12.1 (prohibidas sobre cada entrega), §13.1–§13.3 (traza, spans, scores), §15.4 (`max_retries.plan`), §15.9 (regla de contratos entre carriles), §17.1 (cifras provisionales).
- `definitions.md`:
  - §1: `Destinatario`, `Allegado`, `Recuerdo`, `HechoExtraido`, `ElementoPersonal`, `DeseoDeTrama`, `ListaProhibida`;
  - §2: `StoryBible`, `Mundo`, `Novum`, `Consecuencia`, `Personaje`, `Lugar`, `Hecho`, `Evento`, `Cronologia`;
  - §3: `Novela` (año presente), `Version`, `Outline`, `Beat`, `StyleSheet`;
  - §4: `VentanaDeContexto`, `CanonCard`, `TechoDeTokens`;
  - §5: `Rol`, `SesionDeRol`, `Tool`, `Ejecucion`, `Intento y Evaluable`, `PuntoDeControl`;
  - §6: `ResultadoDeValidador`, `Defecto`, `Veredicto`, `Score`, `CatalogoDeTropos`;
  - §11.1–§11.2 y §12 (identificadores y enumerados).
- `domain-knowledge.md` §3.3–§3.4 (novum), §4.1–§4.2 (zonas), §4.5 (deseos), §5.2 (fechado), §5.3 (T1–T5, fuera de `outline`), §6 (tropos y marcadores).
- `verification.md`:
  - §2 (clases), §3.1–§3.3 y §3.5 (tipos, dobles, contrato), §4.3 (todo bucle tiene techo), §4.10 (correspondencia con TLA+);
  - §5, filas C.4, 3.1, 3.7, 4.1, 5.0 y 6.4;
  - §6, U1, U24 y U27.
- `backend/AGENTS.md` (módulos de la 010) y `specs/backend/007-validador-lean.md` (la 007 atribuye a esta spec el canon del brief con su fechado y los eventos planificados).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué entrega la 010? | La fase `planning` entera: candidata con el canon del brief, sesiones del planner, `outline`, intentos y aplicación del plan hasta el punto de control 0 | `architecture.md` §2 (caja «canon del brief + plan»), §5, §9.1 |
| ¿El canon del brief es de la 009 o de la 010? | De la 010, que lo escribe al arrancar la generación; la 009 da los repositorios | §2, §4.1; `verification.md` §5 fila 4.1 (009, 010); spec 007 |
| ¿Qué recibe el planner? | El brief sin textos libres y sin citas, la story bible inicial con el año presente y el catálogo; al replanificar, los defectos, sin el plan rechazado; nada recuperado | §5.1, §5.2, §6.2, §3.3 («ningún otro rol lo recibe literal») |
| ¿Qué cuenta como intento del plan? | Una entrega rechazada por schema, policy u `outline`, o una sesión sin entrega. Las llamadas a otras tools no son entregas | §7.4, §7.6; `definitions.md` `Intento` |
| ¿Se juzga la primera entrega válida de la sesión o la última? | La última que pasó schema y policy. Hay que alinearlo con 003 | §7.4 (la entrega queda en la memoria de la sesión) |
| ¿Plan agotado por prohibidas = `banned_content`? | No: el plan agotado siempre da `retries_exhausted` | §7.6 (tabla); `definitions.md` (motivo de fallo, «de un capítulo») |
| ¿`outline` comprueba T1–T5 sobre lo planificado? | No | §4.5, §11.4; `domain-knowledge.md` §5.3 |
| ¿Qué es «entidades que existen»? | Toda referencia del plan apunta a la story bible inicial o a lo que inventa el mismo plan; además, un evento es excluyente si y solo si tiene excluido | §5.2, extendido a todas las referencias del plan |
| ¿Quién pone el registro y los temas en la StyleSheet? | El código: el registro sale de la `FranjaDeEdad` y los temas prohibidos se añaden al léxico a evitar. Las palabras no, porque nombrarlas ante el writer lo induce a usarlas | §5.3; `definitions.md` `StyleSheet`, `ListaProhibida` («un tema entra además en las instrucciones del writer») |
| ¿Cuándo «aparece» una entidad en un beat, y qué pasa si no aparece en ninguno? | Cuando el beat la nombra (010-C22). Si ningún beat la nombra, `desde_capitulo` es 1 | §6.3 |
| ¿Qué pasa si falla la transacción del plan? | No deja rastro. El `accept` del intento va dentro de la transacción, así que una caída no lo gasta; una excepción da `internal_error` | §5.4, §8.3 por analogía, §7.6 («el intento que cortó una caída no cuenta») |
| ¿Cómo sigue la planificación tras reanudar? | Con la misma candidata, sin reescribir el canon, y con los defectos del último intento cerrado | §9.2, §9.3, §5.4 |
| ¿Varios recuerdos en el mismo sitio? | Un nombre de lugar idéntico es un solo `Lugar` | §4.1 |
| ¿El recuerdo excluyente está en el brief? | §4.1 lo pide, pero `definitions.md` `Recuerdo` no tiene tipo ni excluido. Lo fija el schema del brief (008) | **Hueco del doc**: añadir tipo y excluido a `Recuerdo` |
| ¿Quién crea el `CatalogoDeTropos`? | La 010, que es la primera que lo necesita. `backend/AGENTS.md` lo da a 012, pero 012 → 011 → 010 hace un ciclo | §15.9 («lo crea la spec más temprana que lo necesita») → **integrador** |
| ¿Y las CanonCards iniciales? | Su contenido e índice son de 016, que la tabla de dependencias no pone antes de la 010 | §5.4, §6.4; `backend/AGENTS.md` (`retrieval/` → 016) → **integrador**: añadir 016 a las dependencias de la 010 |
| ¿Dónde queda el título? | En la candidata; que la novela muestre el de su versión vigente lo decide la publicación | §5.4; §15.6 (`novels` tiene título) → hueco para 012 |
| ¿De quién es la traza de la ejecución? | La abre y la conserva quien lanza la ejecución (011, 004); la 010 solo emite en ella | §13.1 |
| ¿Se verifican los deseos de trama? | No. Su adaptación la pide el prompt (I) y se observa en la demo (D) | `definitions.md` `DeseoDeTrama`; `domain-knowledge.md` §4.5 |
