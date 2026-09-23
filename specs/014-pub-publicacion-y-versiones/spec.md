# 014 — PUB · Publicación y versiones

- [x] Spec approved   <- only the user marks this

## Objetivo

Que ninguna candidata se publique sin pasar entera el gate de publicación, que cada fallo vuelva a quien puede arreglarlo, y que cada publicación deje una versión numerada e inmutable sin tocar las anteriores.

## Alcance

Cubre:

- la candidata: su creación, la copia completa de la vigente y su rechazo solo al cancelar;
- la publicación: el número, los capítulos cambiados por huella y la inmutabilidad de lo publicado;
- el gate de publicación en tres etapas, con su orden, su tabla de enrutado y cada ciclo como intento;
- los validadores `elementos-obligatorios` y `arcos-cerrados`, y la pasada de `nombres-exactos` y `palabras-prohibidas` sobre la novela entera;
- el juez, con la rúbrica de novela (`rubrica-novela`);
- el revisor visual con Playwright MCP y el veredicto de `revision-visual` por código.

Columnas de `versions` y de las tablas de ámbito versión: [001 design.md](../001-base/design.md) §12; Playwright MCP del revisor visual: §11.

Depende de 001, 003, 004, 007, 008, 009, 011 y 013.

**Fuera de alcance:**

- Cómo comprueban `nombres-exactos` y el motor de `palabras-prohibidas`, que son de 011 y de 003: aquí se invocan sobre la novela entera.
- `cronologia-lean`: el generador del fichero, las dos cronologías, el verificador y la traducción del testigo son de 009. Aquí se invoca sobre la cronología registrada.
- El editor, el registrador, el hook de validación, el veredicto (`architecture.md` §8.2) y la transacción de aceptación que usan las correcciones del gate: son de 011.
- La vista previa, la exportación del PDF y `pdf-enlaces`: 013.
- El reparto del techo de ventana entre el juez y el revisor visual, y la copia del índice sin reincrustar: 008.
- Cancelar, reanudar y el punto de control del gate: 007.
- Qué les pasa a la solicitud de cambio o a la edición manual al publicarse su candidata o al fallar el gate: 015.
- Las evals del juez con defectos sembrados y del revisor visual, y la revisión humana: 017.
- Lo estético de la lectura: la revisión visual no lo ve (`verification.md` §6, riesgo 12).

## Requisitos

Todos son **Obligatorio**.

### Candidata y versiones

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PUB-1 | Una ejecución de generación arranca → crea su candidata: una `Version` en estado candidata, sin número, que se identifica por su id y no tiene filas de ámbito versión hasta que escribe la planificación | Obligatorio | T |
| RF-PUB-2 | Una ejecución de cambio o de edición supera su revalidación (015) → crea su candidata copiando de la vigente, en una sola transacción, todas las tablas de ámbito versión de `architecture.md` §14.5 —la story bible con sus usos de hechos, los capítulos con sus deltas y su trazabilidad, el outline, la `StyleSheet`, el índice y las instantáneas del `EstadoDelMundo`—, cada fila con su mismo id. Tras la copia, cada una de esas tablas tiene en la candidata exactamente las filas de la vigente salvo la versión. Un fallo a mitad de la copia no deja nada de ella | Obligatorio | T |
| RF-PUB-3 | La ejecución se cancela (007) → su candidata pasa a rechazada y la vigente no cambia. Una ejecución `blocked` o `interrupted` conserva su candidata sin cambiarla de estado | Obligatorio | T |
| RF-PUB-4 | Cualquier intento de modificar o borrar una fila de ámbito versión de una versión publicada → el store lo rechaza (invariante 9), también desde el reemplazo de un registro repetido, que solo alcanza a la candidata (011) | Obligatorio | T |
| RF-PUB-5 | Se publica una versión nueva → cada versión publicada antes conserva sus filas y su PDF byte a byte | Obligatorio | T |

### Gate de publicación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PUB-6 | La candidata tiene sus 10 capítulos aceptados → empieza el gate, en la fase `publication`. Con menos, el gate no empieza | Obligatorio | T |
| RF-PUB-7 | Etapa 1 → corren en este orden `elementos-obligatorios`, `nombres-exactos` sobre los 10 capítulos, `palabras-prohibidas` sobre la novela entera (RF-PUB-21) y `arcos-cerrados`. El primero que falla enruta su fallo, y los siguientes no corren en ese ciclo | Obligatorio | T |
| RF-PUB-8 | Etapa 2, solo si pasa la 1 → corren en paralelo `cronologia-lean` sobre la cronología registrada (009), `rubrica-novela` con el juez y `revision-visual` sobre la vista previa de la candidata. Los fallos de los tres se enrutan juntos en el mismo ciclo | Obligatorio | T |
| RF-PUB-9 | Etapa 3, solo si pasan la 1 y la 2 → se exporta el PDF de la candidata y pasa `pdf-enlaces` (013). Si falla, la ejecución queda `blocked` con motivo `render_failure` y la candidata no se publica | Obligatorio | T |
| RF-PUB-10 | Cada ciclo del gate → usa una vista previa sin revocar de la candidata, y la emite si no la hay (013). Al terminar el gate —al publicar o al detenerse la ejecución en él—, la vista previa se revoca | Obligatorio | T |
| RF-PUB-11 | Un fallo del gate que vuelve al editor → le llega con sus capítulos: un elemento obligatorio ausente, sobre los capítulos que el outline le asignó; un nombre no canónico o un término prohibido en un capítulo, sobre los capítulos implicados; un arco abierto, sobre su capítulo de resolución planificado; un invariante de Lean violado, con los eventos del testigo traducidos a capítulos y nombres (009); y un criterio de la rúbrica de novela bajo su umbral, sobre los capítulos que cita el juez | Obligatorio | T |
| RF-PUB-12 | Falla `revision-visual/enlaces-ficha` → el registrador vuelve a extraer los usos del capítulo al que falta el enlace | Obligatorio | T |
| RF-PUB-13 | Falla `beats-planificados` en el gate, que requiere regenerar → el writer regenera ese capítulo dentro del ciclo | Obligatorio | T |
| RF-PUB-14 | Un término prohibido en la portada o la ficha → la ejecución queda `blocked` con motivo `banned_content`. Una portada, un índice, un capítulo o una ficha que no renderizan en la vista previa —también un capítulo vacío o sin título que en la base tiene texto y título— → `blocked` con motivo `render_failure`. En los dos casos no hay nada que un rol pueda corregir | Obligatorio | T |
| RF-PUB-15 | Toda corrección del gate → pasa el hook de validación, vuelve a pasar por el registrador y por la transacción de aceptación, que reemplaza el registro anterior del capítulo (011), y después el gate se repite desde la etapa 1. Las correcciones de un ciclo van juntas: el editor corrige y el registrador vuelve a registrar | Obligatorio | T |
| RF-PUB-16 | Cada ciclo del gate, con sus correcciones → es un intento del evaluable `gate_cycle`, y las entregas de sus correcciones no cuentan como intentos del capítulo. Agotado `max_retries` (sin calibrar, `architecture.md` §15.2) con defectos bloqueantes → la ejecución queda `blocked` con `retries_exhausted` | Obligatorio | T |
| RF-PUB-17 | El gate supera sus tres etapas → publica en una sola transacción: la candidata pasa a publicada con el número siguiente al de la última versión publicada de la novela —1 si no hay ninguna—, su fecha de publicación, la ruta del PDF y su lista de capítulos cambiados; la ejecución termina `finished` (007). Es la única operación que da número a una versión | Obligatorio | T |
| RF-PUB-18 | Los capítulos cambiados de una versión → son los que tienen una huella de título y texto distinta de la del mismo capítulo en la última versión publicada. La primera versión publicada guarda la lista vacía: no hay versión anterior con la que comparar | Obligatorio | T |

### Validadores de la novela entera

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PUB-19 | `elementos-obligatorios` → pasa si cada elemento obligatorio del brief tiene un `UsoDeHecho`, de alguno de los hechos que lo representan, en al menos un capítulo de la candidata (invariante 3). Si no, da un defecto por elemento ausente, con los capítulos que el outline le asignó | Obligatorio | T |
| RF-PUB-20 | `arcos-cerrados` → pasa si cada arco del outline consta como resuelto en el delta real de algún capítulo. Si no, da un defecto por arco abierto, con su capítulo de resolución planificado | Obligatorio | T |
| RF-PUB-21 | `palabras-prohibidas` en el gate → el motor de 003, con origen `publication_gate` y las listas del tramo, escanea los 10 capítulos, el título, el nombre del destinatario y la dedicatoria de la portada, y los nombres de la ficha. Una coincidencia en un capítulo da `palabras-prohibidas/en-capitulo`; una en la portada o la ficha, `palabras-prohibidas/en-portada-o-ficha` | Obligatorio | T |
| RF-PUB-22 | El catálogo de criterios → contiene `elementos-obligatorios` y `arcos-cerrados`, un criterio cada uno con su nombre, bloqueantes y con acción corregir | Obligatorio | T |

### Juez

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PUB-23 | La etapa 2 abre la sesión del juez → recibe la novela entera; la story bible compacta con el mundo —novum, consecuencias y restricciones—; la tensión planificada y la medida de cada capítulo, para `ritmo`; la rúbrica de novela con sus criterios activos; el `CatalogoDeTropos`; los deseos de trama, con sus marcos, como parámetro de `no-cliche`, y los temas prohibidos como parámetro de `tema-prohibido`. Su única tool es `submit_evaluation` | Obligatorio | T |
| RF-PUB-24 | La entrega del juez → trae, por cada criterio de novela activo, una puntuación de 1 a 5, su justificación y los capítulos que cita en un campo estructurado. Una sesión que termina sin entrega válida es un intento fallido del ciclo del gate | Obligatorio | T |
| RF-PUB-25 | Una puntuación del juez por debajo del umbral de su criterio (`quality.thresholds`, sin calibrar) → da un defecto bloqueante con acción corregir, localizado en los capítulos que cita. Los criterios de novela son `continuidad`, `tono`, `coherencia-personajes`, `personalizacion-natural`, `prosa`, `no-cliche`, `tema-prohibido`, `arco`, `ritmo` y `final`; se juzgan los activos en `quality.active_criteria`, y `tema-prohibido` siempre | Obligatorio | T |
| RF-PUB-26 | El prompt del juez (`rol/juez`) → contiene la rúbrica de novela: qué juzga cada criterio, su escala de 1 a 5, y que no se penaliza un tropo pedido en los deseos de trama ni el marco de un deseo | Obligatorio | I |
| RF-PUB-27 | Al cerrar 014 → la cabecera de `architecture.md` §10.3 lleva el explainer del LLM-as-judge y sus rúbricas | Obligatorio | I |

### Revisor visual

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PUB-28 | La etapa 2 abre la sesión del revisor visual → recibe la URL de la vista previa de la candidata y la estructura esperada; sus tools son las de navegación de Playwright MCP —navegar, instantánea y clic— y `submit_visual_review` (lista blanca de 003) | Obligatorio | T |
| RF-PUB-29 | La entrega del revisor visual → trae lo observado en la portada, el índice, la ficha y cada uno de los diez capítulos, y, por cada entrada del índice y cada enlace de la ficha, la página a la que llegó al seguirlo, no lo que el enlace dice. Una entrega a la que le falta un capítulo o un enlace de la estructura esperada no cumple su schema | Obligatorio | T |
| RF-PUB-30 | La estructura esperada, calculada desde la base → 10 entradas de índice, cada una a su capítulo; cada capítulo con su título y su texto; cada personaje y cada lugar de la story bible en la ficha, con los enlaces de la regla de 013 (RF-LEC-6); y la portada, con el nombre del destinatario y la dedicatoria | Obligatorio | T |
| RF-PUB-31 | El veredicto de `revision-visual` → lo da el código comparando lo observado con lo esperado, sin modelo: un fallo de la portada, el índice, los capítulos o la ficha da su criterio (`portada`, `indice`, `capitulos`, `ficha`), y un enlace de la ficha que falta o que llega a otro capítulo, `enlaces-ficha`. Se prueba con el doble del agente contra vistas previas con defectos de estructura y de enlaces sembrados | Obligatorio | T |
| RF-PUB-32 | El catálogo de criterios → contiene `revision-visual/portada`, `/indice`, `/capitulos` y `/ficha`, bloqueantes, con acción bloquear y causa raíz `fallo de render`, y `revision-visual/enlaces-ficha`, bloqueante, con acción volver a registrar | Obligatorio | T |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Las pruebas de mutación sobre el gate matan todo mutante de sus rutas de rechazo, también uno que publique con un validador fallido o que se salte una etapa | T |

## Docs de referencia

- `architecture.md` §6.10 (punto 3), §7.2 (juez, revisor visual y story bible compacta), §8.2, §8.3, §9.3, §9.4, §10.2, §10.3, §10.4 (invariantes 3, 8 y 9), §11.2 (origen del revisor visual), §14.5 y §16 («Versionado de la story bible», «Número de versión», «Enrutado de los fallos visuales», «Momento del PDF», «Alcance de la revisión visual»).
- `definitions.md` §3 (`Version`), §6 (`Evaluable`, `Criterio`, `Rubrica`, `Veredicto`, `GateDePublicacion`), §12.
- `domain-knowledge.md` §2.3 y §4.5.
- `verification.md` §3.7, §5 («Gate de publicación», «Enrutado del gate», «`elementos-obligatorios`», «`arcos-cerrados`», «Revisión visual») y §6 (riesgos 9 y 12).
