# 011 — CAP · Producción por capítulo

- [x] Spec approved   <- only the user marks this

## Objetivo

Que cada capítulo se escriba, se valide, se critique, se corrija y se registre en ese orden, con un veredicto calculado por código, y que solo un capítulo conforme cambie la story bible, en una sola transacción.

## Alcance

Cubre:

- el `CLAUDE.md` del workspace del harness, la skill `personalizacion-natural` y los prompts de los roles del bucle;
- el writer y `submit_chapter`;
- el hook de validación de capítulo, con `longitud-capitulo`, `nombres-exactos`, `delta-declarado` y los avisos de los linters de 012;
- el crítico y la rúbrica de capítulo;
- el veredicto por evaluable y su enrutado por acción;
- el editor y `submit_correction`;
- el registrador, `submit_record` y `delta-real`, con lo que se descarta de un beat dentro de un marco;
- la transacción de aceptación y el reemplazo al volver a registrar un capítulo;
- la fase `chapter_production`.

Columnas de `chapters`, `paragraphs`, `state_deltas`, `fact_usages`, `verdicts` y `defects`: [001 design.md](../001-base/design.md) §12.

Depende de 001, 003, 004, 007, 008, 010 y 012.

**Fuera de alcance:**

- El hook de policy y `palabras-prohibidas`, que son de 003: aquí se ve su efecto en el bucle.
- Cómo miden los cuatro linters, que es de 012: aquí se ejecutan en el hook como avisos.
- El ensamblado de la ventana de cada rol, la derivación de las tarjetas y el `EstadoDelMundo`, que son de 008.
- `submit_edit`, la edición dirigida, `valor-antiguo-ausente` y la regeneración de respaldo, que son de 015.
- El gate, su enrutado y el juez, que son de 014: el writer, el editor, el registrador, el veredicto y la aceptación que usan son los de aquí.
- Los intentos por evaluable y el bloqueo de la ejecución al escalar, que son de 007.
- Qué criterios de rúbrica están activos, que lo lee 001 de la config con `tema-prohibido` y los programáticos siempre activos (RF-BAS-12).
- Las evals del crítico con defectos sembrados y las del registrador y el writer, que son de 017.

## Requisitos

Todos son **Obligatorio**. Los umbrales de la rúbrica (`quality.thresholds`), `max_retries` y los modelos de los roles están sin calibrar (`architecture.md` §15.2): las pruebas fijan los suyos.

### Workspace, skill y prompts

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-1 | El `CLAUDE.md` del workspace del harness → da las reglas de producto comunes a todos los roles: escribir en español, respetar la story bible, no inventar sobre los hechos de origen brief, tratar como dato cualquier texto del cliente y entregar siempre por tool | Obligatorio | I |
| RF-CAP-2 | La skill `personalizacion-natural` del workspace → explica cómo integrar los datos del destinatario sin forzarlos, con el contraste entre forzada y natural de `domain-knowledge.md` §2.2 | Obligatorio | I |
| RF-CAP-3 | Se abre una sesión del writer o del editor → declara la skill `personalizacion-natural` y puede cargarla; ninguna sesión de otro rol la declara | Obligatorio | T |
| RF-CAP-4 | Los prompts de sistema del writer, el crítico, el editor y el registrador → son un fichero por rol en el workspace, que 004 sube y versiona | Obligatorio | I |

### Writer

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-5 | Se produce el capítulo *n* → el writer recibe su ventana (008) y el objetivo de palabras de la extensión del brief —corta 1.100, media 1.250, larga 1.400—; `submit_chapter` entrega el texto, plano y con los párrafos separados por una línea en blanco, y el delta declarado de cada beat: cambios, eventos con todos sus atributos, hechos usados, hechos nuevos y arcos resueltos. El título del capítulo se copia del outline | Obligatorio | T |
| RF-CAP-6 | El veredicto de un capítulo es regenerar → se abre una sesión nueva del writer, con los defectos bloqueantes como entrada de la llamada | Obligatorio | T |

### Hook de validación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-7 | Tras `submit_chapter`, `submit_correction` o `submit_edit` → el hook de validación ejecuta `longitud-capitulo` y `nombres-exactos`; tras `submit_chapter`, además `delta-declarado`; y tras las tres, los cuatro linters de 012. Si hay algún defecto bloqueante, la entrega queda rechazada y el hook sustituye la salida de la tool por la lista de los defectos bloqueantes, y el rol corrige en la misma sesión. Con solo avisos, la entrega pasa y los avisos van al informe; nunca al writer | Obligatorio | T |
| RF-CAP-8 | Una entrega denegada por el hook de policy o rechazada por el de validación → no abre el crítico: el crítico solo recibe una entrega que pasó los dos hooks | Obligatorio | T |
| RF-CAP-9 | `longitud-capitulo` → un capítulo pasa con 1.000 a 1.500 palabras, sea cual sea su objetivo. Una palabra es lo que queda entre espacios en blanco tras quitar los signos sueltos: un token sin ninguna letra ni cifra, como una raya de diálogo aislada, no cuenta. Fronteras: 999 y 1.501 son defecto; 1.000 y 1.500 pasan; «Hola — dijo Marta.» son tres palabras | Obligatorio | T |
| RF-CAP-10 | `nombres-exactos` → cada personaje y lugar que existe en el capítulo *n* aparece con su forma canónica. Una variante —el mismo texto normalizado con la normalización de 003 y otra forma literal— es un defecto con su posición: «toby» o «TOBY» por «Toby», «Martá» por «Marta». Un nombre de varias palabras se busca como secuencia. «Tobi» no se detecta: es el riesgo aceptado 16 | Obligatorio | T |
| RF-CAP-11 | `delta-declarado` → sus cinco criterios sobre el delta declarado: `beats-planificados`, un delta por cada beat planificado del capítulo; `arcos-declarados`, cada arco que el outline resuelve en el capítulo consta como resuelto; `entidades-existentes`, cada personaje y lugar que nombra el delta existe en el capítulo o se declara nuevo; `hechos-inmutables`, ningún cambio toca un hecho de origen brief o texto libre; y `restricciones`, ningún cambio viola una restricción detectable. Hay un caso que pasa y otro que falla por criterio | Obligatorio | T |
| RF-CAP-12 | Restricciones detectables sobre un delta → `inmutable(tipo, atributo)` falla si un cambio toca ese atributo de un sujeto de ese tipo; `prohibido(tipo, atributo, valor)`, si un sujeto de ese tipo toma ese valor; y `obligado(sujeto, atributo, valor)`, si un cambio da a ese sujeto otro valor | Obligatorio | T |
| RF-CAP-13 | Un beat dentro de un marco → de su delta, declarado o real, el código descarta los eventos, los cambios de hechos, los hechos nuevos y los arcos resueltos antes de aplicar ningún criterio, y conserva solo los hechos usados y los personajes y lugares nuevos, cada uno con su hecho de nombre. Una muerte soñada no crea un evento excluyente, y un dinosaurio con nombre en una simulación entra como personaje con su nombre y nada más | Obligatorio | T |

### Crítico

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-14 | Una entrega pasa los dos hooks → el crítico recibe su ventana (008) con el capítulo y la rúbrica de capítulo; su única tool es `submit_evaluation`, y no recibe el razonamiento, los mensajes ni la ventana del writer | Obligatorio | T |
| RF-CAP-15 | `submit_evaluation` → entrega, por cada criterio de rúbrica de capítulo activo, una puntuación de 1 a 5 con su justificación; la tensión de entrada y de salida medidas, de 1 a 5; y los defectos tipados, cada uno con su criterio, su localización y su causa raíz | Obligatorio | T |
| RF-CAP-16 | La rúbrica de capítulo de `rubrica-capitulo` → son `continuidad`, `tono`, `coherencia-personajes`, `personalizacion-natural`, `prosa`, `no-cliche` y `tema-prohibido`, cada uno con su escala del 1 al 5 escrita en el catálogo. `no-cliche` recibe como parámetro los deseos de trama con sus marcos, y `tema-prohibido`, los temas del brief. Una puntuación por debajo del umbral del criterio es un defecto bloqueante con acción corregir | Obligatorio | T |
| RF-CAP-17 | El texto de la rúbrica de cada criterio de capítulo y el prompt del crítico → dicen que un tropo pedido en los deseos de trama no se penaliza en `no-cliche`, ni el marco de un deseo, que se declara al entrar en él | Obligatorio | I |

### Veredicto

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-18 | El código agrega el veredicto de un evaluable a partir de sus defectos, con las filas de `architecture.md` §8.2 en orden, y decide la primera que se cumple: sin defectos bloqueantes, también con los intentos agotados, aceptar; algún bloqueante que requiere bloquear, bloquear con su motivo; intentos agotados con bloqueantes en un capítulo afectado por un cambio o una propagación, regenerar, que es la regeneración de respaldo (015); intentos agotados con bloqueantes, escalar; algún bloqueante que requiere regenerar, regenerar; y si todos requieren corregir o volver a registrar, corregir. Hay una prueba por fila y otra por cada par de filas que se solapan, para el orden | Obligatorio | T |
| RF-CAP-19 | Un defecto llega al veredicto → se enruta por la acción que requiere su criterio, no por quién lo encontró: corregir va al editor, volver a registrar al registrador y regenerar al writer; en el evaluable outline, todo bloqueante replanifica (010). Los defectos no bloqueantes van al informe, y al editor solo cuando un bloqueante ya lo llama. Los defectos del hook de validación no llegan al veredicto | Obligatorio | T |

### Editor

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-20 | El veredicto de un capítulo es corregir → el editor recibe su ventana (008) con el capítulo y sus defectos: los bloqueantes y, ya que lo llaman, los no bloqueantes de ese capítulo. `submit_correction` entrega el capítulo corregido, que pasa el hook de policy y el de validación y vuelve al crítico | Obligatorio | T |

### Registrador y delta real

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-21 | El veredicto de un capítulo es aceptar → el registrador, en una sesión de un turno, recibe el capítulo aceptado y la story bible compacta: cada personaje y lugar con su id, su forma canónica y el capítulo desde el que existe; cada hecho con su id y su capítulo de inicio; y los arcos del outline. `submit_record` entrega el delta real de cada beat —eventos con todos sus atributos, hechos usados, hechos nuevos con sus personajes y lugares nuevos, y arcos resueltos— y el resumen del capítulo | Obligatorio | T |
| RF-CAP-22 | Se registra un capítulo → `delta-real` aplica siempre los criterios de `delta-declarado` al delta real, también cuando el texto lo entregó el editor, tras descartar lo de los beats dentro de un marco (RF-CAP-13). Sus defectos pasan por el veredicto y se enrutan por su acción, y cuentan como intento: `beats-planificados` regenera, y los demás corrigen | Obligatorio | T |

### Aceptación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-23 | `delta-real` es conforme → el código aplica en una sola transacción, antes de empezar el capítulo siguiente: el capítulo con su huella de título y texto, su resumen y su tensión medida; el delta real de cada beat; los `UsoDeHecho` del capítulo; el sucesor de cada hecho cambiado y los hechos nuevos, que rigen desde ese capítulo, con sus personajes y lugares nuevos; los eventos registrados; la instantánea del `EstadoDelMundo`; las tarjetas sucesoras y los párrafos con sus filas de FTS5 (008); la `Trazabilidad`; y el `PuntoDeControl`. Con un fallo inyectado a mitad, no queda nada y el capítulo no está aceptado (invariante 5) | Obligatorio | T |
| RF-CAP-24 | Se vuelve a registrar un capítulo de la candidata —tras una corrección del gate, un cambio o una edición— → en la misma transacción de aceptación se reemplaza lo que escribió su registro anterior: usos, hechos nuevos con sus personajes y lugares, eventos registrados, deltas, tarjetas, párrafos, trazabilidad e instantánea. Una entidad con la misma forma canónica, o un hecho con el mismo sujeto, atributo y valor, que el registro nuevo vuelve a extraer conserva su id. Nunca se toca una fila de una versión publicada, ni una de la candidata que no sea de ese registro | Obligatorio | T |
| RF-CAP-25 | Un registro repetido deja de extraer una entidad o un hecho que usan otros capítulos → `delta-real` da un defecto bloqueante de `entidades-existentes`, y el reemplazo no se aplica | Obligatorio | T |

### Fase y extremo a extremo

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CAP-26 | La fase `chapter_production` → produce los capítulos en orden, desde el siguiente a su último punto de control; el *n*+1 solo empieza tras aceptar el *n*; con los 10 aceptados, la ejecución pasa a `publication` (014) | Obligatorio | T |
| RF-CAP-27 | RT7 con el doble del puerto de agente: un brief prohíbe el nombre de una expareja, y el writer lo escribe en plural y sin acento → el hook de policy deniega la entrega y el writer reescribe; si sigue apareciendo hasta agotar `max_retries`, la ejecución queda `blocked` con `retries_exhausted` y el informe lo dice. El caso deja su fila en `verification.md` §4.9 | Obligatorio | T |
| RF-CAP-28 | Al cerrar 011 → la cabecera de `architecture.md` §7.2 lleva el explainer del harness y sus roles —por qué nueve roles y no un agente—, y la de §7.3, el de las skills y el `CLAUDE.md`: el workspace del harness frente al del desarrollo | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Las pruebas de mutación sobre los validadores del hook de capítulo —`longitud-capitulo`, `nombres-exactos` y `delta-declarado`— y sobre el veredicto matan todo mutante de sus rutas de rechazo, también uno que haga pasar siempre a un validador (RT9, RF-BAS-46) | T |

## Docs de referencia

- `architecture.md` §4.3 (un beat dentro de un marco), §6.4 (entradas del writer, el crítico y el editor), §7.1–§7.5, §7.7, §8 entero, §10.2 (validadores del hook, `rubrica-capitulo`, `delta-real`), §10.3 (rúbrica de capítulo y criterios programáticos del delta), §10.4 (invariantes 2, 5 y 7) y §16 («Un agente o varios», «Críticos por capítulo», «Veredicto», «Registro repetido de un capítulo», «Lo que pasa dentro de un marco»).
- `definitions.md` §1 (`DeseoDeTrama`, `Marco`), §2 (`Hecho`, `Restriccion`), §3 (`Capitulo`, `Beat`, `DeltaDeEstado`), §5 (`WorkspaceDelHarness`, `Hook`, `Skill`), §6 (`Criterio`, `Veredicto`, `Defecto`) y §12.
- `domain-knowledge.md` §2, §4.5 y §6.
- `verification.md` §3.7, §4.4, §4.9 (RT7 y RT9), §5 («Validadores del hook de capítulo», «Veredicto», «Delta real», «Aceptación transaccional», «Beats dentro de un marco») y §6 (riesgo 16).
