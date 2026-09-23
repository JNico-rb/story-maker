# 012 — LIN · Linters de prosa

- [ ] Spec approved   <- only the user marks this

## Objetivo

Que cuatro linters deterministas, escritos desde cero con la morfología del español de spaCy, avisen de la prosa repetitiva, poco legible para su lector, con giros de texto generado o incoherente en su estilo, sin bloquear nunca un capítulo.

## Alcance

Cubre:

- `linter-repeticion`, `linter-legibilidad`, `linter-estilo-ia` y `linter-consistencia`, con sus criterios de `architecture.md` §10.3;
- el aviso que da cada criterio: su métrica, su umbral y su defecto no bloqueante;
- la exclusión del diálogo en el narrador y el tiempo verbal;
- las listas propias de `domain` que usan;
- los scores de cada linter.

Los linters corren en tres puntos (`architecture.md` §10.2): el hook de validación de capítulo, que los invoca en 011; y el guardado de una edición manual y el linter en vivo, que los invocan en 015. Los tres usan las mismas funciones.

Depende de 001, 004 y 008.

**Fuera de alcance:**

- Invocarlos en el hook de validación, que es de 011, y en la edición manual y el linter en vivo, que es de 015.
- Llevar un aviso al editor cuando un defecto bloqueante ya lo llama, que es del veredicto de 011.
- La calibración de sus umbrales y de los objetivos de legibilidad: se quedan sin valor (`architecture.md` §15.2).
- El matiz del tono en la legibilidad, que juzga la rúbrica (`architecture.md` §10.3), no un linter.
- La recuperación de prosa, que es de 008: `linter-repeticion` la usa como consumidor.

## Requisitos

Todos son **Obligatorio**. Los umbrales de cada criterio (`quality.thresholds`) y los objetivos de legibilidad por franja de edad (`quality.readability_targets`) están sin calibrar (`architecture.md` §15.2): las pruebas fijan los suyos, y ningún requisito les da valor.

### Comunes

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-1 | El `CatalogoDeCriterios` → contiene los cuatro linters con sus criterios deterministas: `linter-repeticion` con `repeticion-parrafo` y `ngramas-entre-capitulos`; `linter-legibilidad` con `longitud-frase` y `fernandez-huerta`; `linter-estilo-ia` con `adverbios-mente`, `cliches` y `giros-generados`; y `linter-consistencia` con `narrador`, `tiempo-verbal` y `tratamiento`. Todos son no bloqueantes, con acción corregir, y siempre activos: `active_criteria` no los desactiva | Obligatorio | T |
| RF-LIN-2 | Un linter mide un capítulo → cada criterio compara su métrica con su umbral de `quality.thresholds`; si la métrica queda del lado del defecto, da un defecto no bloqueante con acción corregir, causa raíz `style_drift`, su localización —capítulo, párrafo y desplazamiento— y el valor medido junto al umbral. Un umbral sin valor falla al leerse, con el error de RF-BAS-13, y el linter nunca se inventa uno | Obligatorio | T |
| RF-LIN-3 | Un linter mide el mismo texto con la misma config y la misma colección de prosa → da los mismos avisos, sin llamar a ningún modelo | Obligatorio | T |
| RF-LIN-4 | Un linter corre dentro de una traza → envía su score agregado, 1 si ningún criterio da aviso y 0 si alguno lo da, y uno por criterio, `<linter>/<criterio>`, 1 sin aviso y 0 con él, con el valor medido y el umbral en el comentario (004). En el linter en vivo, que no tiene traza, no envía ninguno (RF-OBS-15) | Obligatorio | T |
| RF-LIN-5 | Palabras y frases → un linter cuenta palabras con la regla de `longitud-capitulo` (`architecture.md` §10.2) y separa frases y lemas con el modelo de español de spaCy | Obligatorio | T |

### `linter-repeticion`

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-6 | `repeticion-parrafo` → cuenta, dentro de cada párrafo, las apariciones de cada lema con contenido —sin las palabras vacías— y de cada muletilla de la lista propia de `domain`; un lema o una muletilla que supera el umbral en un párrafo es un aviso con su párrafo y su palabra. Las apariciones en párrafos distintos no se suman | Obligatorio | T |
| RF-LIN-7 | `ngramas-entre-capitulos` → busca los n-gramas distintivos del capítulo en los párrafos de los capítulos anteriores, recuperados con BM25 de la colección de prosa como consumidor `repetition_linter`, con su cuota y su corte temporal (008). Un número de coincidencias por encima del umbral es un aviso con los dos pasajes. En el capítulo 1, sin prosa anterior, no hay aviso | Obligatorio | T |

### `linter-legibilidad`

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-8 | `longitud-frase` → la media de palabras por frase del capítulo se compara con el objetivo `sentence_length` de la franja de edad del destinatario; si lo supera en más del umbral, es un aviso con las frases más largas | Obligatorio | T |
| RF-LIN-9 | `fernandez-huerta` → el índice de Fernández-Huerta del capítulo, con las sílabas por palabra y las palabras por frase, se compara con el objetivo `fernandez_huerta` de su franja; si queda por debajo en más del umbral —el texto es más difícil de lo que toca—, es un aviso. Sobre textos de referencia de índice conocido, el calculado coincide dentro de una tolerancia fijada en la prueba | Obligatorio | T |

### `linter-estilo-ia`

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-10 | `adverbios-mente` → la densidad de adverbios terminados en -mente, cada cien palabras, reconocidos como adverbios por la morfología; por encima del umbral es un aviso. «La mente», «demente» o «clemente» no cuentan | Obligatorio | T |
| RF-LIN-11 | `cliches` y `giros-generados` → las apariciones de las expresiones de la lista de clichés y de la de giros típicos de texto generado, las dos propias y en `domain`, comparadas con la normalización de 003; por encima del umbral de cada criterio es un aviso con cada aparición | Obligatorio | T |
| RF-LIN-12 | Las listas de `domain` de muletillas, clichés y giros de texto generado → son propias, curadas a mano y sin licencia de terceros | Obligatorio | I |

### `linter-consistencia`

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-13 | Se separa el diálogo → es diálogo lo que va entre rayas y lo que va entre comillas —«», "" o “”—. Los incisos del narrador dentro de una línea de diálogo son narración: en «—Tengo hambre —dijo Marta.», «Tengo hambre» es diálogo y «dijo Marta» es narración | Obligatorio | T |
| RF-LIN-14 | `narrador` → sobre la narración, sin el diálogo, la proporción de formas de la persona que no fija la StyleSheet —primera o tercera—; por encima del umbral es un aviso. Un diálogo entero en primera persona en una novela en tercera no da aviso | Obligatorio | T |
| RF-LIN-15 | `tiempo-verbal` → sobre la narración, sin el diálogo, la proporción de formas del tiempo verbal que no fija la StyleSheet —pasado o presente—; por encima del umbral es un aviso. Un diálogo en presente en una novela narrada en pasado no da aviso | Obligatorio | T |
| RF-LIN-16 | `tratamiento` → dentro del diálogo, para cada réplica cuyo hablante y destinatario se identifican, el tratamiento, tú o usted, frente al que fija la StyleSheet para ese par; un número de réplicas con el otro tratamiento por encima del umbral es un aviso con el par y las réplicas. Una réplica sin hablante o sin destinatario identificados no cuenta | Obligatorio | T |

### Textos de referencia

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LIN-17 | Cada criterio tiene un texto de referencia limpio y otro con su defecto → con los umbrales de prueba, el limpio no da ningún aviso de ningún criterio y el otro da el de su criterio | Obligatorio | T |

## Docs de referencia

- `architecture.md` §8.2 (avisos al informe y al editor), §10.1, §10.2 (fila de los linters), §10.3 (criterios programáticos de los linters), §13.3, §15.2 y §16 («Linters de prosa», «Objetivos de legibilidad»).
- `definitions.md` §3 (`StyleSheet`), §6 (`Linter`, `Criterio`, `Defecto`), §11 (`quality.thresholds`, `quality.readability_targets`) y §12.
- `domain-knowledge.md` §2.3 y §7.
- `verification.md` §5 («Linters de prosa»).
