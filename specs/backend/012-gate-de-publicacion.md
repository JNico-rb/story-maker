# 012 — Gate de publicación

> Carril: A · Depende de: 007-validador-lean, 011-produccion-de-capitulos · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Que ninguna candidata se publique sin pasar el `GateDePublicacion`: los validadores de novela en orden económico, la atribución de cada fallo a capítulos, la reescritura dirigida con ciclos acotados y la transacción de publicación que convierte la candidata en versión. Incluye el juez (`juez-novela`) con la rúbrica de novela y el `CatalogoDeTropos`, y el validador `elementos-obligatorios`. Es la acción `Gate` → `Validar` → `Reintentar` → `Publicar` | `Fallar` | `Caer` de `architecture.md` §9.1.

Vocabulario: una **pasada** es una ejecución completa del gate sobre la candidata; es un intento del evaluable `gate_cycle` («ciclo del gate», `definitions.md` §5). Una **etapa** es cada uno de los cuatro escalones de `architecture.md` §9.4.

## Alcance

- Entrada al gate cuando la candidata tiene sus 10 capítulos aceptados; fases `gate` ⇄ `rewriting`.
- **Etapa 1, deterministas:** `elementos-obligatorios` (validador de esta spec); `nombres-exactos` aplicado a cada capítulo; `palabras-prohibidas` sobre capítulos, portada y ficha, con origen `publication_gate`.
- **Etapa 2, en paralelo:** `cronologia-lean` sobre la candidata ∥ `juez-novela`: la sesión del juez, su tool `submit_evaluation`, su prompt y la agregación por código.
- **Etapas 3 y 4:** su lugar en el orden; qué hace el gate con el resultado del PDF.
- Atribución de fallos, veredicto de cada pasada y precedencia entre resultados.
- Reescritura dirigida, ciclos (`max_retries.gate_cycles`) e intentos de capítulo por ciclo.
- Interrupciones durante el gate y reanudación en `gate` o `rewriting`.
- Transacción de publicación: número, `published_at`, `changed_chapters`, ruta del PDF, estado de la ejecución y de la solicitud de cambio o la edición manual.
- `ResultadoDeValidador` y score de cada validador que corre en el gate.
- Constantes del dominio: rúbrica de novela y `CatalogoDeTropos` con los tropos curados.

## Fuera de alcance

- Regla de variantes de `nombres-exactos` y hook de validación de capítulo → 011-produccion-de-capitulos.
- Forma normalizada, coincidencia, `MotorDePoliticas` y audit log → 005-guardarrailes; aquí solo se le pide la decisión.
- Generación y seudonimización del `FicheroDeCronologia`, compilación, testigo traducido a eventos y personajes, modos `local` y `github`, `chronology_files` → 007-validador-lean.
- `VistaDeVersion`, generación del PDF (también su página de novedades) y lo que comprueba `pdf-enlaces` → 013-lectura-y-pdf.
- `revision-visual`: estructura esperada, fallo de datos (entidad sin capítulo en la ficha → el editor vuelve a registrar, sin writer) y fallo de render → 017-revision-visual.
- Bucle de capítulo: ventana, writer en modo `rewrite`, hooks, editor, veredicto de capítulo, transacción de aceptación y su sustitución al volver a aceptar (`architecture.md` §8.3), paso a `failed` con la candidata `discarded`, `InformeDeEjecucion`, mecánica de reanudar (puesto en la cola, `max_resumes`, caída al arrancar) → 011-produccion-de-capitulos.
- Apertura de sesiones de rol, reserva en el `TechoDeTokens`, `infeasible_config`, contrato de las tools, lista blanca → 003-puerto-de-agente (y el hook de policy, 005).
- Trazas, spans, adaptador de Langfuse y máscara → 004-observabilidad.
- Revalidación de la versión base, candidata copiada, capítulos afectados, solicitud `rejected` → 014-cambios-del-lector. Edición manual y `edit_rejected` → 019-edicion-manual.
- Revisión humana, comparación juez/humano, tropos aprendidos, prueba de validez del catálogo (`domain-knowledge.md` §6.2, paso 2), briefs de evaluación → 020-evals.
- Modelo TLA+ de estas transiciones → 006-especificacion-tla.
- Valores de umbrales, modelos y límites: config (001-base), calibrados en la iteración de tuning (`architecture.md` §17).

## Comportamiento observable

Salvo C27, cada caso es **T**: corre con el doble falso del puerto de agente (juez, writer, editor), el doble nulo de observabilidad y dobles del verificador formal, de la etapa 3 y del PDF que devuelven el resultado indicado. Umbrales, límites y listas son de fixture.

### C1 — La candidata entra al gate con sus 10 capítulos aceptados (T)
- **Entrada:** ejecución `generation` en `writing`; se acepta el capítulo 10. Variante: el capítulo 9 recién aceptado.
- **Salida:** tras el 10, la fase pasa a `gate` y se abre la pasada 1. Tras el 9, sigue en `writing` y no corre ningún validador del gate. En una ejecución de cambio o de edición, se entra tras su último capítulo afectado (014, 019), con la misma regla: el gate solo corre sobre una candidata con los 10 capítulos.

### C2 — Una pasada limpia recorre las cuatro etapas en orden y publica (T)
- **Entrada:** candidata con cada elemento obligatorio usado, nombres canónicos y ninguna prohibida; verificador `passed`; juez con todos los criterios en 4; etapa 3 que pasa; PDF generado con `pdf-enlaces` que pasa.
- **Salida:** corren una vez cada uno, por etapas y en este orden: `elementos-obligatorios`, `nombres-exactos` y `palabras-prohibidas` (entre ellos, en cualquier orden); `cronologia-lean` y `juez-novela`; `revision-visual`; PDF y `pdf-enlaces`. La pasada 1 cierra con `accept`, ningún capítulo cambia y la ejecución publica (C23).

### C3 — Un elemento obligatorio sin uso se atribuye a los capítulos que el outline le asignó (T)
- **Entrada:** el recuerdo obligatorio «se perdió en la feria», asignado por el outline a los capítulos 2 y 5, sin ningún `UsoDeHecho` de sus hechos en la candidata.
- **Salida:** `elementos-obligatorios` no pasa. Da un defecto bloqueante para el 2 y otro para el 5, con el elemento en el mensaje. La pasada no sigue a la etapa 2 (C7) y los dos capítulos van a reescritura dirigida (C19).
- **Límites:** pasa un obligatorio cuyo único uso está en un capítulo que el outline no le asignó. Pasa uno representado por varios hechos con uno solo usado. Un elemento no obligatorio sin uso no da defecto. El nombre del destinatario es siempre uno de los obligatorios (`ElementoPersonal`) y sigue la misma regla.

### C4 — Un nombre no canónico en un capítulo se atribuye a ese capítulo (T)
- **Entrada:** «Tobi» en el texto del capítulo 6, con «Toby» como forma canónica.
- **Salida:** `nombres-exactos`, con la regla de 011 aplicada a cada capítulo, no pasa. Da un defecto bloqueante del 6 con la variante y la forma canónica, y el 6 va a reescritura dirigida. Los límites de la regla son casos de 011.

### C5 — Una prohibida en un capítulo se atribuye a ese capítulo (T)
- **Entrada:** el cliente añade «tormenta» a su lista de nivel `user` después de aceptarse el capítulo 4, que contiene «tormentas».
- **Salida:** `palabras-prohibidas`, con las tres listas tal como están al correr la pasada, no pasa. Pasa lo siguiente:
  - un defecto bloqueante del 4;
  - en el audit log, una decisión `deny` de origen `publication_gate` con la coincidencia: término, nivel `user`, variante, ubicación `chapter` y capítulo 4;
  - score `palabras-prohibidas` = 0, con el término, el nivel y la variante en el comentario;
  - el 4 va a reescritura dirigida.
- **Límite:** sin coincidencias, la pasada deja una decisión `allow`. Siempre hay una decisión por pasada, con todas sus coincidencias en el detalle.

### C6 — Una prohibida en la portada o en la ficha hace fallar la ejecución (T)
- **Entrada:** (a) la dedicatoria contiene un término que el cliente añadió a su lista `user` tras confirmar el brief; (b) la descripción de un lugar inventado contiene un término `global`. En los dos casos hay además un elemento obligatorio sin uso, que es atribuible.
- **Salida:** `failed` con `banned_content`, sin reescritura y sin etapa 2. Queda una decisión `deny` con ubicación `cover` o `sheet`, la pasada cierra con `fail` y la candidata pasa a `discarded` (011).
- **Qué se escanea:**
  - en la portada, el título, el nombre del destinatario y la dedicatoria;
  - en la ficha, el nombre canónico, la descripción y los valores de los hechos de cada personaje y lugar de la candidata.

### C7 — Una etapa que falla corta la pasada (T)
- **Entrada:** una pasada en la que no pasa la etapa de la tabla.
- **Salida:**

| No pasa | No corren en esa pasada |
|---|---|
| Etapa 1 | Generación del `FicheroDeCronologia`, verificador, sesión del juez, etapa 3 y PDF |
| Etapa 2 (Lean, el juez o los dos) | Etapa 3 y PDF |
| Etapa 3 | PDF |

Dentro de una etapa corren todos sus validadores aunque falle el primero. Si en la etapa 1 fallan C3 y C4 a la vez, se reescriben el 2, el 5 y el 6 en la misma pasada.

### C8 — Lean y el juez corren a la vez (T)
- **Entrada:** etapa 1 superada; un doble del verificador y otro del juez que solo terminan cuando el otro ya ha empezado.
- **Salida:** la etapa 2 termina: ninguno espera al otro para empezar. Solo decide cuando han terminado los dos, con los defectos de ambos. El juez reserva en el techo de tokens como cualquier sesión (003); el verificador no reserva nada.

### C9 — Un invariante Lean violado se atribuye a los capítulos de los eventos del testigo (T)
- **Entrada:** el verificador devuelve `failed` por T4. El testigo tiene dos eventos: el excluyente de un recuerdo del brief («la abuela se fue a vivir lejos para siempre») y uno registrado del capítulo 6, beat 2, con la abuela presente después.
- **Salida:**
  - `cronologia-lean` = 0 y `cronologia-lean/T4` = 0; los demás invariantes, según el resultado de 007;
  - un defecto bloqueante del 6, con el testigo en nombres canónicos, capítulos y beats, sin ids de fila;
  - el 6 va a reescritura dirigida;
  - el writer recibe el defecto, y el editor también, entre las entradas de su llamada, con la indicación de que prevalece sobre `cumple-beats` si el beat planificado era el origen de la incoherencia.
- **Límite:** un testigo con eventos registrados de los capítulos 3 y 5 se atribuye a los dos.

### C10 — Un testigo Lean sin capítulo hace fallar la ejecución (T)
- **Entrada:** el testigo solo tiene eventos de origen brief. Por ejemplo, T5: un recuerdo con un allegado presente antes de su fecha de nacimiento.
- **Salida:** `failed` con `unattributable_defect` y sin reescritura. La pasada cierra con `fail`. El informe de la ejecución (011) muestra el invariante y el testigo en nombres y fechas de la historia: solo el cliente puede cambiar el brief.

### C11 — Un `FicheroDeCronologia` que no compila hace fallar la ejecución (T)
- **Entrada:** el verificador devuelve `error`: el fichero no compila por una causa que no es un invariante.
- **Salida:** `failed` con `internal_error`, el diagnóstico en el detalle y `cronologia-lean` = 0. No hay reescritura, porque ningún capítulo corrige un fallo del generador.

### C12 — Una interrupción en la etapa 2 no gasta la pasada (T)
- **Entrada:** (a) el verificador (007) informa de que es inalcanzable; (b) informa de que no respondió en `verifier_timeout_seconds`; (c) la sesión del juez termina con `infrastructure_failure` (proveedor caído o límite de uso de la suscripción).
- **Salida:** `interrupted` con `verifier_unreachable`, `verifier_timeout` o `provider_error`.
  - La pasada queda sin desenlace y no cuenta.
  - Nada se publica ni se reescribe, y la candidata se conserva.
  - Si el otro validador de la etapa sigue corriendo, se espera a que termine: su resultado se guarda y su sesión queda en `role_sessions`.
  - En (a) y (b) no hay score de `cronologia-lean`.

### C13 — Un criterio bloqueante del juez bajo su umbral se atribuye a los capítulos que cita (T)
- **Entrada:** todos los umbrales en 3. El juez entrega:
  - `continuidad` = 2, citando los capítulos 4 y 7;
  - `ritmo` = 2, citando el 4 y el 9;
  - el resto, en 4 o más.
- **Salida:**
  - `juez-novela` = 0;
  - `continuidad` da defectos bloqueantes del 4 y del 7, con su justificación como mensaje; `ritmo`, defectos no bloqueantes del 4 y del 9;
  - se reescriben el 4 y el 7, y el writer del 4 recibe los dos defectos;
  - el 9 no se reescribe: su defecto va al informe y a los scores.
- **Límite:** `continuidad` = 3, igual al umbral, pasa aunque cite capítulos.

### C14 — Ningún criterio compensa a otro (T)
- **Entrada y salida:**

| Entrega del juez | Resultado |
|---|---|
| `arco-y-final` = 2 y los otros seis en 5 | `juez-novela` = 0; se reescriben los capítulos que cita `arco-y-final` |
| Los tres bloqueantes en 3 o más; `personalizacion-natural`, `tono` y `no-cliche` en 1 | `juez-novela` = 1: el juez no hace fallar la etapa 2; tres defectos no bloqueantes van al informe; nada se reescribe |

No hay media. El agregado mira solo los criterios bloqueantes. La presencia de la personalización la exige además el código, con `elementos-obligatorios` (C3).

### C15 — Una entrega inválida del juez se corrige en su sesión, y sin entrega válida la pasada falla (T)
- **Entrada:** el juez entrega primero una evaluación inválida, de uno de estos tipos:
  - falta un criterio, o sobra uno desconocido;
  - una puntuación está fuera de 1–5, o una justificación está vacía;
  - un criterio no cita ningún capítulo, o cita uno fuera de 1–10 o repetido.
  Después entrega una válida. Variante: la sesión agota `max_turns` o `session_timeout_seconds` sin ninguna válida.
- **Salida:** cada entrega inválida vuelve al juez como error de `schema-salida` en la misma sesión, sin defecto de la novela; la válida se acepta.
- **En la variante:** la pasada cuenta como fallida sin capítulos que reescribir.
  - Si quedan ciclos, se reescriben solo los capítulos que haya atribuido Lean en esa pasada, si hay alguno, y se repite la pasada.
  - Si no quedan, `failed` con `retries_exhausted`.

### C16 — El juez recibe la novela entera y solo lo que necesita (T)
- **Entrada:** la sesión del juez de una pasada, capturada por el doble del puerto de agente.
- **Recibe, como entradas de la llamada:**
  - el título de la novela y los 10 capítulos de la candidata tal como están, con título y texto;
  - la story bible compacta: cada personaje y lugar con su forma canónica y sus hechos, y el mundo;
  - la rúbrica de novela (C25) y el `CatalogoDeTropos` entero (C26);
  - del brief, el tono, el género y los deseos de trama.
- **No recibe:** ningún texto libre ni la cita de un hecho extraído, la cronología, los resúmenes, las revisiones del editor, el razonamiento del writer ni datos de otra novela o de otra versión.
- **Sesión:** su única tool es `submit_evaluation` y su modelo, `roles.judge.model`. Su `SesionDeRol` lleva la ejecución y ningún capítulo.

### C17 — Dentro de una pasada, lo no atribuible manda sobre la interrupción, y esta sobre lo atribuible (T)
- **Entrada:** combinaciones de resultados en una misma pasada.
- **Regla**, en este orden, sobre las etapas que corrieron:
  1. Algún fallo no atribuible, sea una prohibida en portada o ficha, un testigo sin capítulo, un `error` de Lean o un fallo de render: `failed` con su motivo.
  2. Si no hay ninguno, alguna interrupción: `interrupted` con su motivo.
  3. Si no hay ninguna, defectos bloqueantes atribuibles o un juez sin entrega válida: reescritura dirigida si quedan ciclos, o `failed` con `retries_exhausted` si no quedan.
  4. Si no hay nada de lo anterior, la pasada sigue a la etapa siguiente o publica.
- **Salida:**

| Lean | Juez | Resultado |
|---|---|---|
| Testigo sin capítulo | Bloqueante en el 4 | `failed`, `unattributable_defect` |
| Inalcanzable | Bloqueante en el 4 | `interrupted`, `verifier_unreachable`; nada se reescribe |
| Testigo en el 6 | Bloqueante en el 4 | Reescritura del 4 y del 6 en el mismo ciclo, cada uno con sus defectos |
| Testigo en el 6 | Sin entrega válida | Reescritura del 6 y pasada nueva |
| `passed` | Proveedor caído | `interrupted`, `provider_error` |
| `error` | Proveedor caído | `failed`, `internal_error` |

En la etapa 1, una prohibida en la portada junto a un elemento sin uso da `failed` con `banned_content`, como en C6.

### C18 — El PDF de la candidata es la última etapa (T)
- **Entrada:** etapas 1–3 superadas y uno de estos resultados: (a) el PDF se genera y `pdf-enlaces` pasa; (b) `pdf-enlaces` falla porque un enlace interno no resuelve; (c) el PDF no llega a generarse.
- **Salida:** en (a), la ejecución publica con la ruta de ese PDF (C23). En (b) y (c), `failed` con `render_failure` y sin reescritura; en (b), además, `pdf-enlaces` = 0.

### C19 — La reescritura dirigida rehace solo los capítulos atribuidos y repite el gate (T)
- **Entrada:** la pasada 1 atribuye defectos bloqueantes a los capítulos 5 y 2, y quedan ciclos.
- **Salida:**
  - La pasada 1 cierra con `rewrite` y la fase pasa a `rewriting`.
  - Se rehacen el 2 y después el 5, por número de capítulo y uno a uno. En cada uno:
    - el writer trabaja en modo `rewrite`, con su ventana de producción (011) y los defectos de la pasada atribuidos a ese capítulo, bloqueantes y no bloqueantes;
    - pasan los mismos hooks, el editor, el veredicto y la transacción de aceptación de 011, que sustituye lo que dejó la aceptación anterior del capítulo.
  - Los otros ocho capítulos conservan su huella.
  - Después, la fase vuelve a `gate` y la pasada 2 empieza desde la etapa 1 sobre la candidata reescrita.
  - Las sesiones de rol del capítulo *n* van en su span `capitulo-<n>` de la traza de la ejecución.

### C20 — Cada capítulo reescrito tiene sus intentos en cada ciclo (T)
- **Entrada:** `max_retries.chapter` = 1, y uno de estos dos escenarios: (a) en el ciclo 1, el veredicto rechaza dos veces el capítulo 5; (b) el 5 se acepta al segundo intento en el ciclo 1 y el ciclo 2 lo vuelve a atribuir.
- **Salida:** en (a), `failed` con `retries_exhausted`, o con `banned_content` si el último rechazo fue por una prohibida (regla de 011). En (b), el 5 vuelve a tener dos intentos en el ciclo 2: cada intento de capítulo lleva su ciclo del gate y se cuenta dentro de él.

### C21 — Agotados los ciclos del gate, la ejecución falla (T)
- **Entrada:** `max_retries.gate_cycles` = 2 y un doble que atribuye un defecto bloqueante en cada pasada. Variantes: la pasada 3 pasa; `max_retries.gate_cycles` = 0.
- **Salida:** las pasadas 1 y 2 cierran con `rewrite` y tienen su reescritura. La 3 cierra con `fail`, sin reescritura, y la ejecución termina `failed` con `retries_exhausted`. Se cuentan tres pasadas y nunca hay una cuarta. Si la 3 pasa, se publica. Con 0 ciclos, la primera pasada con defectos atribuibles falla.

### C22 — Reanudar en `gate` o en `rewriting` repasa el gate sobre la candidata tal como quedó (T)
- **Entrada:** (a) una caída durante la reescritura del ciclo 1, con el capítulo 2 ya reescrito y aceptado y el 5 pendiente; (b) una interrupción `verifier_unreachable` en la pasada 2. En los dos, la ejecución se reanuda (011).
- **Salida:**
  - En (a), al relanzarse, la fase es `gate` y empieza una pasada nueva sobre la candidata: el 2 tiene su texto nuevo y el 5 el anterior, porque el 5 no se reescribe antes. Esa pasada es la del ciclo 2: el 1 ya se contó y no se devuelve.
  - En (b), se repite la pasada 2, que sigue siendo la 2.
  - No se replanifica ni se toca ningún capítulo aceptado.

### C23 — La publicación es una transacción (T)
- **Entrada:** en (a)–(c), una pasada que supera las cuatro etapas:
  - (a) la candidata de un cambio sobre la v3 de la novela A, con huellas distintas de las de la v3 en los capítulos 2 y 5 y su solicitud de cambio en `confirmed`;
  - (b) la primera generación de la novela B;
  - (c) la candidata de una edición manual en `queued`.
  - (d) Un fallo provocado dentro de la transacción.
- **Salida:** todo esto se escribe en una sola transacción:
  - la candidata pasa a `published`, con número = el de la última publicada de su novela + 1 (4 en A; 1 en B, aunque A ya tenga tres);
  - `published_at`;
  - `changed_chapters`: los capítulos cuya huella difiere de la de su versión base, [2, 5] en A y vacía sin base;
  - la ruta del PDF de la etapa 4;
  - la ejecución pasa a `published`, y la solicitud de cambio o la edición manual, a `applied`.
- **En (d):** no queda escrito nada de lo anterior. En ningún caso cambian las filas de la v3 (I4).

### C24 — Cada validador del gate deja su resultado y su score (T)
- **Entrada:** pasadas que superan el gate y pasadas que fallan, con el doble nulo de observabilidad.
- **Salida:** cada validador que corre en una pasada deja dos cosas:
  - un `ResultadoDeValidador`, con la ejecución, la candidata, el validador, si pasa, el score y un detalle con los defectos y el capítulo de cada uno;
  - una vez guardado ese resultado, su score, con el nombre de `architecture.md` §11.2, en la traza de la ejecución y dentro de su span `validador:<nombre>`.
- **Scores:**
  - 0/1 en `elementos-obligatorios`, `nombres-exactos`, `pdf-enlaces` y `palabras-prohibidas`, este con el término, el nivel y la variante en el comentario;
  - 0/1 en `cronologia-lean`, más `cronologia-lean/T1` a `/T5`;
  - 0/1 en `juez-novela`, más siete `juez-novela/<criterio>` de 1 a 5, con la justificación en el comentario;
  - los de `revision-visual` los fija 017.
- Una pasada que falla también envía los suyos. El informe (011) y la tabla de evals (020) los leen de ahí.

### C25 — La rúbrica de novela es una constante del dominio (T)
- **Entrada:** la rúbrica de novela.
- **Salida:** tiene exactamente siete criterios, cada uno con lo que juzga (`architecture.md` §11.3). Son bloqueantes (B) los tres primeros:
  - `continuidad` (B), `coherencia-personajes` (B), `arco-y-final` (B);
  - `ritmo`, `tono`, `personalizacion-natural`, `no-cliche`.
  `submit_evaluation` exige exactamente esos criterios. Es la misma rúbrica que usa la revisión humana (020).

### C26 — El `CatalogoDeTropos` trae los tropos curados del género (T)
- **Entrada:** el catálogo.
- **Salida:** los siete tropos de `domain-knowledge.md` §6, sin nombres repetidos:
  - singularidad redentora o apocalíptica;
  - rebelión de las máquinas;
  - IA que desarrolla conciencia o descubre el amor;
  - último humano con empleo;
  - renta básica distópica;
  - vigilancia total;
  - dilema del tranvía algorítmico.
  Cada tropo tiene nombre, al menos un marcador y origen `curated`. Ninguno es `learned`: esos los añade 020.

### C27 — Una sesión real del juez entrega una evaluación válida (D)
- **Entrada:** una sesión real del juez, con `LLM_PROVIDER=claude_login`, sobre una novela de fixture de 10 capítulos sin datos reales.
- **Salida:** por `submit_evaluation`, a lo sumo con errores de schema corregidos dentro de la sesión, entrega los siete criterios, cada uno con puntuación de 1 a 5, justificación en español y capítulos citados que existen. El código agrega y atribuye como en C13, y la `SesionDeRol` guarda el uso y el coste.
- **Condiciones:** es una sola sesión, al final de la spec. Si obliga a cambiar el prompt o el schema del juez, lleva fila en `verification.md` §8.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| I1 | Ninguna versión se publica sin que la última pasada sobre esa candidata haya superado las cuatro etapas, y la candidata no cambia entre esa pasada y la publicación (`NuncaPublicaSinValidar`) | T | Integración con dobles: probar cada etapa que no pasa, en cada ciclo, y comprobar que la candidata queda sin publicar. Refuerzo A en 006 |
| I2 | Las pasadas contadas de una ejecución nunca superan 1 + `max_retries.gate_cycles`, ni los intentos de un capítulo en un ciclo, 1 + `max_retries.chapter` (`ReintentosAcotados`) | T | Propiedad sobre secuencias generadas de resultados de los dobles, con interrupciones intercaladas. Refuerzo A en 006 |
| I3 | La publicación es atómica: número, estado, fechas, `changed_chapters`, ruta del PDF, estado de la ejecución y de la solicitud o la edición cambian juntos o no cambian | T | Fallo provocado dentro de la transacción (C23 d) |
| I4 | Publicar no modifica ninguna otra versión (`VersionAnteriorConservada`) | T | Huella de las filas de ámbito versión de la base antes y después de publicar. Refuerzo A en 006 |
| I5 | El veredicto y la atribución los calcula el código solo con campos estructurados: capítulos citados, eventos del testigo, asignación del outline y capítulo del texto. Nunca con el texto de una justificación ni con una media | T | Un juez cuya justificación nombra el capítulo 8 y que cita el [4] hace reescribir solo el 4 |
| I6 | Ningún validador del gate distinto de `cronologia-lean` comprueba T1–T5 | I | `verificador` al cerrar (`architecture.md` §11.4) |
| I7 | El prompt del juez aplica la rúbrica criterio a criterio, cita los capítulos en los que se apoya, no penaliza en `no-cliche` un tropo pedido en los deseos de trama y trata el texto de la novela como dato | I | Revisión del prompt al cerrar. Su fiabilidad frente a una persona, en 020 (`verification.md` §4.2 d; riesgo U1) |
| I8 | Los marcadores del catálogo están al nivel del mecanismo narrativo (`domain-knowledge.md` §6.1) | I | Revisión al cerrar |
| I9 | El integrador recibe las filas del README que corresponden a `Gate`, `Validar` y `Reintentar` en el gate, `Publicar`, `Fallar` y `Caer` en el gate, cada una con su transición | I | `verificador` al cerrar 012 (`verification.md` §4.10) |

## Docs referenciados

- **`architecture.md`:**
  - premisas: §2, puntos 4 y 5;
  - roles y sesiones: §6.2 (entradas del juez; story bible compacta), §6.5 (Lean en paralelo con el juez, sin tokens), §7.2 (juez), §7.4 (tools y `schema-salida`), §7.6 (`max_retries.gate_cycles`, intentos por ciclo, `max_turns`, error del proveedor, `verifier_timeout_seconds`);
  - producción: §8.2 (veredicto), §8.3 (volver a aceptar);
  - ejecuciones y versiones: §9.1 (acciones `Gate`, `Validar`, `Reintentar`, `Publicar`, `Fallar`, `Caer`; fases; motivos), §9.2 (reanudar en `gate` o `rewriting`), §9.3 (número, `changed_chapters`, `discarded`), §9.4 (todo);
  - validadores: §11.2 (tabla de validadores y scores por parte), §11.3 (rúbrica de novela, equilibrio, defectos tipados), §11.4 (cuándo y dónde corre Lean, `interrupted`, Lean no se duplica);
  - política y observabilidad: §12.1 (prohibidas en el gate), §12.2 (origen `publication_gate`), §13.1 y §13.3 (spans y scores);
  - config: §15.4 (`quality.thresholds`, `max_retries`).
- **`definitions.md`:** `GateDePublicacion`, `Veredicto`, `Defecto`, `Criterio`, `Rubrica`, `Score`, `ResultadoDeValidador`, `CatalogoDeTropos`, `Version`, `Ejecucion`, `Intento` y `Evaluable`, `PuntoDeControl`, `ElementoPersonal`, `UsoDeHecho`, `Coincidencia`, `DecisionDePolitica`, `Portada`, `FichaDePersonajes`, `FicheroDeCronologia`, `VerificadorFormal`, `SesionDeRol`; §12.2 (tools del juez), §12.3 (etiquetas) y §12.4 (enumerados).
- **`domain-knowledge.md`:** §2.2 y §2.3 (personalización frente a calidad), §5.3 (T1–T5), §6 y §6.1 (tropos y marcadores), §8 (descomponer en criterios).
- **`verification.md`:**
  - §2 (clases), §3.3 (integración con dobles), §4.2 d (juez frente a revisión humana), §4.10 (correspondencia en el README);
  - §5, filas C.1, C.2, C.3, 3.7, 5.0, 5a.2, 5a.4, 5b.1, 5c.3 y 6.4;
  - §6, riesgos U1 y U2.
- **`project-constraints.md` §5:** validador en el gate antes de publicar; LLM-as-judge con puntuación y justificación por criterio; Lean que, si falla, no deja publicar y vuelve al editor.
- **Specs:** 003, 004, 005, 006, 007, 009, 010, 011, 013, 014, 017, 019, 020.

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué posee 012? | El gate y la publicación en `pipeline`, `elementos-obligatorios` y el juez en `validators`, la rúbrica de novela y el catálogo en `domain`, y el prompt del juez | `backend/AGENTS.md` |
| ¿Son de 012 `nombres-exactos` y `palabras-prohibidas`? | Solo su aplicación a la novela y la atribución. La regla es de 011 y el motor, de 005 | §9.4, §11.2 |
| ¿Etapa 3? | 017 depende de 012: aquí, su lugar en el orden; el resto, en 017 | `TODO.md`; `verification.md` §5 5a.6 |
| ¿Etapa 4? | 013 no depende de 012: el PDF y `pdf-enlaces` son de 013; la reacción del gate (`render_failure`, ruta del PDF), de 012 | §9.4 |
| ¿Modo del writer en la reescritura dirigida? | `rewrite`: ventana y defectos, sin el texto anterior. La continuidad la sostiene el outline y la vuelve a juzgar la pasada siguiente | §6.2, §8.2 |
| ¿Reanudar en `rewriting` acaba la reescritura pendiente? | No: vuelve a pasar el gate | §9.2 |
| ¿`changed_chapters` y `applied` son de 012? | Sí: son de la transacción de publicación. 014 y 019 la usan | §9.4 |
| ¿Cuándo salen los scores del gate? | Cada uno, en cuanto se guarda su resultado; la publicación no espera a Langfuse | §8.3 (los scores salen tras el commit) |
| ¿Qué hace el gate con un `error` de Lean? | `failed` con `internal_error` | **Hueco** → §18 |
| ¿Precedencia entre resultados? | Lo no atribuible, antes que la interrupción; la interrupción, antes que lo atribuible | **Hueco** → §18 |
| ¿Se corta al otro validador si uno de la etapa 2 falla? | No: se espera a los dos y se combinan sus defectos | **Hueco** → §18 |
| ¿Juez sin entrega válida? | Pasada fallida sin reescritura, que cuenta en `gate_cycles` | §7.6 (`max_turns` = intento fallido) → §18 |
| ¿Qué capítulos cita el juez? | Todo criterio, al menos uno: el schema es estático y no depende de la config | §9.4 («su schema exige citarlos») → §18 |
| ¿Con qué juzga el juez `tono` y los tropos pedidos? | Con el tono, el género y los deseos de trama del brief | **Hueco del doc**: §6.2 y §7.2 no los listan; hay que actualizarlos antes de aprobar |
| ¿Qué es la ficha al escanear prohibidas? | Los datos de la story bible de sus entidades, no el HTML de 013 | → §18 |
| ¿Orden de la reescritura? ¿Una decisión de política por pasada? | Por número de capítulo. Sí: una decisión por pasada, con todas las coincidencias | → §18 |
| ¿Cómo prevalece el defecto Lean sobre `cumple-beats`? | Viaja con el defecto, como entrada del editor, sin tocar el prompt del editor (011) | §9.4 → §18 |
| ¿Quién crea el `CatalogoDeTropos`? | 010 lo necesita antes (§5.1), pero la tabla de propiedad lo da a 012 | **Conflicto** → integrador |
| ¿Prueba de validez del catálogo? | Una persona tiene que etiquetar diez mundos | → pregunta al usuario; fuera de aquí |
