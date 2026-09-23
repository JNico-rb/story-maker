# 010 — PLN · Planificación

- [x] Spec approved   <- only the user marks this

## Objetivo

Que cada generación parta de un plan validado antes de escribir nada: el canon del brief escrito por el código, un mundo post-IA que se sostiene causalmente, un outline de 10 capítulos con una cronología verificada y una StyleSheet, congelados juntos como punto de control del capítulo 0.

## Alcance

Cubre:

- el primer paso de la planificación: el canon del brief, que escribe el código en la primera candidata;
- la sesión del planner, con sus entradas y sus cuatro tools, y los deseos de trama con sus marcos;
- `grafo-causal` al entregar el mundo, y `outline` y `cronologia-lean` antes de congelar;
- la replanificación, cada una como intento del evaluable outline;
- la StyleSheet;
- la congelación con el canon inicial, su índice y el punto de control del capítulo 0;
- el `CatalogoDeTropos`, con su prueba de validez.

Columnas de la story bible, del outline y de la StyleSheet: [001 design.md](../001-base/design.md) §12.

Depende de 001, 003, 004, 005, 007, 008 y 009.

**Fuera de alcance:**

- El planner en modo cambio, con `propose_change`, que es de 015.
- La derivación de las tarjetas del índice, que es de 008: aquí se invoca en las dos transacciones de la planificación.
- La generación del fichero Lean, su verificador y la traducción del testigo, que son de 009.
- El hook de policy sobre los campos narrativos de las entregas del planner, que es de 003.
- La reanudación y los intentos, que son de 007: aquí se dice qué deja la planificación para reanudar.
- El uso del catálogo de tropos por el crítico y el juez, con el criterio `no-cliche`, que es de 011 y de 014.
- La incorporación de los tropos aprendidos que se repitan en las evals, que sale de las evals de 017.
- El brief de evaluación «Fuera de ambientación», que comprueba los marcos de extremo a extremo (017).

## Requisitos

Todos son **Obligatorio**. `max_retries` y el modelo del planner están sin calibrar (`architecture.md` §15.2): las pruebas fijan los suyos.

### Canon del brief

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PLN-1 | Empieza la planificación, en la primera candidata de una generación → antes de abrir ninguna sesión del planner, el código escribe en la story bible, según la tabla de `architecture.md` §4.1: un `Personaje` de origen brief por el destinatario y por cada allegado, con su hecho de nombre; un `Hecho(destinatario, rasgo)` por rasgo; por cada recuerdo, un `Hecho(destinatario, recuerdo)` y su `Evento` de origen brief; un `Lugar` de origen brief por el lugar de cada recuerdo; un `Hecho(allegado, relación)` por allegado; y un `Hecho(sujeto, atributo, valor)` de origen texto libre por cada hecho extraído aceptado. Hay una prueba por fila | Obligatorio | T |
| RF-PLN-2 | Se escribe el canon del brief → cada personaje de origen brief lleva la fecha de nacimiento que dan las reglas de RF-ENT-15, o ninguna si no tiene edad ni fecha; y el evento de cada recuerdo, el momento que dan esas reglas, con el destinatario y los allegados presentes, su lugar y, si el recuerdo declara una edad, esa edad como declarada del destinatario. Fronteras: un destinatario de 40 años sin fecha, en una novela creada el 2026-09-23, nace el 1986-01-01; nacido un 29 de febrero, su recuerdo «a los 9 años» queda el 1 de marzo a las 12:00 | Obligatorio | T |
| RF-PLN-3 | Se escribe un hecho de origen brief → su atributo pertenece al vocabulario cerrado de `domain`; con cualquier otro, se rechaza | Obligatorio | T |
| RF-PLN-4 | Se escribe un hecho de origen brief o texto libre → queda enlazado al `ElementoPersonal` que representa, con su marca de obligatorio; el nombre del destinatario es siempre obligatorio | Obligatorio | T |
| RF-PLN-5 | Se escribe el canon del brief → en una sola transacción con sus tarjetas (008): con un fallo inyectado, no queda nada | Obligatorio | T |
| RF-PLN-6 | Se inserta el sucesor de un hecho de origen brief o texto libre por cualquier ruta que no sea una solicitud de cambio ni una edición manual (015) → el store lo rechaza y nada cambia (invariante 2) | Obligatorio | T |

### Planner

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PLN-7 | Se abre una sesión del planner → recibe el brief confirmado sin textos libres, con sus deseos de trama y el marco de cada uno, fijado o libre; la story bible inicial; y el `CatalogoDeTropos` como lista de evitación. Un texto libre de fixture con una marca única no aparece en su ventana ni en sus mensajes | Obligatorio | T |
| RF-PLN-8 | Una planificación → es una sesión del planner con `submit_world`, `submit_cast`, `submit_outline` y `submit_style_sheet`, cada una con su schema, y cuenta como un intento del evaluable outline. Una sesión que termina sin haber entregado las cuatro es un intento fallido | Obligatorio | T |
| RF-PLN-9 | `submit_world` → entrega el novum, con su enunciado, su ámbito y su fecha; las consecuencias, cada una con su enunciado, su ámbito y aquello de lo que deriva, el novum u otra consecuencia; las restricciones, con su predicado detectable cuando lo hay —`inmutable`, `prohibido` u `obligado`—; y los antecedentes, eventos planificados sin beat con todos los atributos de `Evento` | Obligatorio | T |
| RF-PLN-10 | Se entrega `submit_world` → `grafo-causal` lo comprueba en el acto con sus tres criterios del catálogo, bloqueantes y con acción regenerar: `alcanzable`, toda consecuencia alcanzable desde el novum y sin ciclos; `orden-maximo`, ninguna a más de 3 pasos del novum; y `novum-anterior`, el novum anterior al año presente. Si falla, la sesión se corta, cuenta como intento fallido y se abre una sesión nueva del planner con los defectos. Fronteras: una consecuencia a 3 pasos pasa y a 4 falla; un novum del 31 de diciembre del año anterior pasa y uno del 1 de enero del año presente falla | Obligatorio | T |
| RF-PLN-11 | Para todo grafo generado con orden ≤ 3 y el novum anterior al año presente → `grafo-causal` lo acepta si y solo si toda consecuencia es alcanzable desde el novum; la propiedad se prueba en las dos direcciones (invariante 1) | Obligatorio | T |
| RF-PLN-12 | `submit_cast` → entrega los personajes inventados —nombre, especie, rasgos y fecha de nacimiento opcional— y los lugares inventados —nombre, tipo y descripción—, con sus hechos, todos de origen inventado; existen desde el capítulo 0 | Obligatorio | T |
| RF-PLN-13 | `submit_outline` → entrega el título de la novela; 10 capítulos, cada uno con su título, su función en el arco, su tensión planificada de entrada y de salida de 1 a 5 y sus beats; cada beat con su evento, con todos los atributos de `Evento`, o, si ocurre dentro de un marco, su marco y ningún evento; los hechos que usa; y, si revela algo, el tema y el contenido de la revelación; los arcos, con su capítulo de planteamiento, el de resolución y sus protagonistas; y la asignación de cada elemento obligatorio a uno o más capítulos. Un beat con evento y marco a la vez, o sin ninguno de los dos, no cumple su schema | Obligatorio | T |
| RF-PLN-14 | Deseos de trama → el planner planifica dentro de su marco cada deseo que lo tiene fijado; uno con el marco libre va tal cual si cabe en el presente post-IA, y si no, lo enmarca con uno del catálogo: simulación, sueño o relato dentro del relato. Ningún deseo se descarta por su ambientación. Lo pide el prompt del planner, y ningún validador lo comprueba (`architecture.md` §4.2) | Obligatorio | I |
| RF-PLN-15 | Se entrega el outline → pasa `outline` con sus cinco criterios del catálogo, bloqueantes y con acción regenerar: `diez-capitulos`, `beats-por-capitulo`, `obligatorios-asignados`, `arcos-con-resolucion` y `extremos-sin-marco`, que exige el primer beat del capítulo 1 y el último del 10 fuera de todo marco. Fronteras: 9 y 11 capítulos fallan; 2 y 7 beats en un capítulo fallan, y 3 y 6 pasan; un elemento obligatorio sin capítulo falla; un marco en el primer beat del capítulo 1 o en el último del 10 falla, y en cualquier otro beat pasa | Obligatorio | T |
| RF-PLN-16 | `outline` pasa → `cronologia-lean` verifica la cronología planificada de la propuesta (009) antes de guardar nada; si falla, se replanifica con el invariante violado y el testigo traducido como realimentación. Si `outline` falla, Lean no llega a correr | Obligatorio | T |
| RF-PLN-17 | El evaluable outline tiene algún defecto bloqueante, sea cual sea su acción → se abre una sesión nueva del planner con los defectos como realimentación. Con `max_retries` agotado, la ejecución se bloquea con `retries_exhausted` (007) | Obligatorio | T |
| RF-PLN-18 | `submit_style_sheet` → el planner fija el narrador, el tiempo verbal —pasado o presente—, el tratamiento, tú o usted, entre cada par de personajes, el tono y el género del brief, y el léxico a evitar. El código deriva el registro de la franja de edad del destinatario y añade al léxico a evitar las entradas de tipo tema de las tres listas del tramo | Obligatorio | T |

### Congelación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PLN-19 | Pasan los tres validadores → el código aplica en una sola transacción el mundo con sus antecedentes, los personajes, lugares y hechos inventados, el outline congelado, la StyleSheet, sus tarjetas (008) y el punto de control del capítulo 0. Con un fallo inyectado no queda nada de eso, y la planificación no termina | Obligatorio | T |
| RF-PLN-20 | Se reanuda una ejecución que no llegó al punto de control del capítulo 0 → la planificación empieza con una sesión nueva y reutiliza el canon del brief ya escrito, sin duplicarlo. Con ese punto de control, la producción empieza en el capítulo 1 sin replanificar | Obligatorio | T |

### Catálogo de tropos

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PLN-21 | El `CatalogoDeTropos` → vive en `domain`, versionado con el código; cada `Tropo` tiene nombre, descripción, marcadores y origen, `curated` o `learned`, y el planner recibe los de los dos orígenes por igual | Obligatorio | T |
| RF-PLN-22 | Los tropos curados → salen de pedir al modelo los clichés del subgénero post-IA con sus marcadores y podarlos a mano, reescribiendo cada marcador al nivel del mecanismo narrativo (`domain-knowledge.md` §6.1); cubren al menos los siete tropos de `domain-knowledge.md` §6 | Obligatorio | I |
| RF-PLN-23 | Prueba de validez del catálogo → el planner genera mundos para briefs variados, y una persona elige y etiqueta cinco buenos y cinco malos, que quedan como fixture. Aplicados los marcadores a los diez, cada mundo malo presenta al menos uno y ningún bueno presenta ninguno; si no los separan, se reescriben los marcadores antes de integrar el catálogo | Obligatorio | I |

## Docs de referencia

- `architecture.md` §4.1–§4.3, §5, §6.11 (dos primeras filas), §7.2 (planner), §7.7 (regla 4), §8.2 (evaluable outline), §9.2 (punto de control del capítulo 0), §10.2 (`grafo-causal`, `outline`, `cronologia-lean`), §10.3 (sus criterios), §10.4 (invariantes 1 y 2) y §16 («Deseos de trama», «Deseos fuera de la ambientación», «Catálogo de marcos», «Quién elige el marco», «Lo que pasa dentro de un marco», «Novum», «Catálogo de tropos»).
- `definitions.md` §1 (`Brief`, `DeseoDeTrama`, `Marco`, `ElementoPersonal`), §2, §3 (`Outline`, `Beat`, `Arco`, `StyleSheet`, `PuntoDeControl`), §6 (`Tropo`, `CatalogoDeTropos`) y §12.
- `domain-knowledge.md` §3, §4.1, §4.5, §5.2 y §6.
- `verification.md` §3.6 (invariante 1), §4.5 (catálogo de tropos) y §5 («Grafo causal», «Outline», «Invariante 2», «Planner»).
