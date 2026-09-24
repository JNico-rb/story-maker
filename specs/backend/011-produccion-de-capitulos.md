# 011 — Producción de capítulos

> Carril: A · Depende de: 005-guardarrailes, 010-planificacion · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Llevar una `Ejecucion` de generación desde que se lanza hasta el gate. La ejecución entra en la cola FIFO global y el worker la toma. Tras la planificación, se producen los 10 capítulos en secuencia. Por cada capítulo: el orquestador ensambla la `VentanaDeContexto`; el writer entrega pasando por sus hooks; el editor critica con la rúbrica y registra; el código decide el `Veredicto`; y una transacción acepta el capítulo con su `PuntoDeControl`. Una caída se reanuda desde el último punto de control, sin duplicar ni perder capítulos.

Del encargo cubre: writer y editor/critic separados; el `CLAUDE.md` de producto; una skill reutilizable; el hook de validación de capítulo; reintentos con límite; `UsoDeHecho` y resúmenes por capítulo; punto de control por capítulo y reanudación; longitud del capítulo; nombres exactos; prohibidas sobre cada capítulo antes de aceptarlo, con límite e informe.

## Alcance

- **Ciclo de vida de la ejecución por la API y la CLI** (Arq. §9.1, §15.7, §15.8): lanzar una generación, consultar el progreso, reanudar e informe. Transiciones de `Harness.tla` que implementa: `Configurar`, el paso a `Planificar`, `EscribirCapitulo`, `Validar` y `Reintentar` del capítulo, `Gate`, `Fallar`, `Caer` y `Reanudar`.
- **Cola y worker** (Arq. §9.1): cola FIFO global, una sola ejecución activa, `running` → `interrupted` al arrancar el servidor.
- **Ventanas del writer y del editor** (Arq. §6.1–§6.2). Los recuperados son los que devuelve el recuperador.
- **Sesión del writer** en los modos `write` y `rewrite`, con `submit_chapter`. Incluye el hook de validación de capítulo con `longitud-capitulo` y `nombres-exactos` (Arq. §7.5, §11.2) y qué cuenta como intento (Arq. §7.6, §8.1).
- **Sesión del editor** con `submit_review` y `rubrica-capitulo` (Arq. §7.2, §11.3). **Veredicto por código** (Arq. §8.2).
- **Transacción de aceptación** (Arq. §8.3): capítulo, `ResumenDeCapitulo`, `UsoDeHecho`, eventos registrados, `CanonCard` sucesoras, `ResultadoDeValidador` y `PuntoDeControl`. Incluye el reemplazo al volver a aceptar un capítulo.
- **Reanudación** (Arq. §8.4, §9.2), **`InformeDeEjecucion`**, y trazas, spans y scores de la producción (Arq. §13.1–§13.3).
- **Lo del `WorkspaceDelHarness` que usan writer y editor** (Arq. §7.3): el `CLAUDE.md` de producto, la skill `personalizacion-natural`, y los prompts del writer (modos `write` y `rewrite`) y del editor.

## Fuera de alcance

- **Fase `planning`** → 010-planificacion (Arq. §4.1, §5): la candidata con el canon del brief, el planner, `outline`, la aplicación del plan y el `PuntoDeControl` 0. Aquí solo el paso de `planning` a `writing`.
- **Gate, reescritura dirigida, ciclos del gate, publicación y `changed_chapters`** → 012-gate-de-publicacion (Arq. §9.4). También es de 012 qué hace en el gate una ejecución reanudada. Allí `nombres-exactos` corre sobre la novela con el validador de esta spec.
- **Linters de prosa** → 018-linters-de-prosa (Arq. §14.5), también su ejecución entre el hook de validación y el editor. Aquí el editor recibe la lista de defectos de los linters, vacía mientras 018 no esté.
- **Ejecuciones `change_request` y `manual_edit`** → 014-cambios-del-lector y 019-edicion-manual (Arq. §10). También el modo `revise` del writer, la revalidación de la versión base y el editor en edición manual.
- **Mecanismo del puerto de agente** → 003-puerto-de-agente (Arq. §6.5, §7.3–§7.6, §13.2): opciones de sesión, tools con schema y el error que vuelve al modelo, el mecanismo de los hooks, `TechoDeTokens` (reserva, estimador y espera), desenlaces de la `SesionDeRol`, uso y coste.
- **`MotorDePoliticas`, prohibidas, lista blanca en el hook de policy y `AuditLog`** → 005-guardarrailes (Arq. §12).
- **Recuperador y plantilla de la `CanonCard`** → 016-recuperacion-hibrida (Arq. §6.3): BM25, canal denso, RRF, corte temporal, y el texto e índice de cada tarjeta.
- **Observabilidad**: el adaptador de Langfuse, la `Mascara` y los prompts versionados (`prompts push` y lectura por etiqueta) → 004-observabilidad (Arq. §13). El puerto de observabilidad y su doble nulo → 001-base.
- **Autenticación**, 401 y propiedad (lo ajeno responde 404) → 002-autenticacion (Arq. §14.3).
- **Guardado de la story bible y copia de versión** → 009-story-bible-y-versiones.
- **Tarjetas posteriores al volver a aceptar un capítulo**: las de capítulos siguientes que citan sus eventos antiguos no se reconstruyen. Arq. §8.3 solo reemplaza las que nacieron del capítulo.

## Comportamiento observable

**Fixture común**, salvo que el caso diga otra cosa:

- una novela del cliente con el brief confirmado, de `Extension` media (objetivo de 1.250 palabras);
- `quality.thresholds` = 3 en todos los criterios, `max_retries.chapter` = 2 (como mucho 3 intentos por capítulo) y `max_resumes` = 2;
- los roles corren en el doble falso del puerto de agente y la observabilidad, en el doble nulo;
- «el recuerdo devuelve» fija la respuesta del recuperador (016) como entrada del caso.

### 011-C01 — Lanzar la generación la encola (T)
- **Sostiene:** Arq. §9.1 (`Configurar`), §15.7.
- **Dado** una novela con el brief confirmado, sin versión publicada ni generación sin terminar, y dos ejecuciones `queued` de otras novelas
- **Cuando** se llama a `POST /api/novels/{id}/runs`
- **Entonces**:
  - la respuesta es 202 con `run_id` y `position` = 3;
  - la ejecución es de tipo `generation`, está en `queued`, no tiene fase y guarda su fecha de creación;
  - aún no tiene candidata, porque la crea al arrancar (010).

### 011-C02 — Solo se lanza una generación desde una novela lista (T)
- **Sostiene:** Arq. §9.3 (relanzar la generación), §15.7 (409).
- **Dado** cada situación de la tabla
- **Cuando** se llama a `POST /api/novels/{id}/runs`
- **Entonces** responde lo de la tabla y, salvo en la fila del 202, no se crea ninguna ejecución.

| Situación | Respuesta |
|---|---|
| Brief en borrador | 409 |
| Una generación `queued`, `running` o `interrupted` | 409 |
| Una versión publicada | 409 |
| La única generación anterior terminó `failed` | 202, con una ejecución nueva |
| Novela ajena o inexistente; sin token | 404; 401 (mecanismo de 002) |

### 011-C03 — Una sola ejecución activa en una cola FIFO global (T)
- **Sostiene:** Arq. §9.1 (cola y worker), `definitions.md` §5 `Ejecucion`.
- **Dado** tres ejecuciones `queued`, ninguna `running`:
  - A, del cliente 1, creada en t1;
  - B, del cliente 2, en t2;
  - C, del cliente 1, en t3.
- **Cuando** corre el worker
- **Entonces**:
  - toma A, que pasa a `running`;
  - B y C siguen `queued`, con posiciones 1 y 2;
  - toma B solo cuando A sale de `running` (publicada, fallida o interrumpida), y C cuando sale B;
  - nunca hay dos `running`;
  - una `interrupted` no detiene la cola.

### 011-C04 — El progreso se consulta por sondeo (T)
- **Sostiene:** Arq. §9.1 (progreso por sondeo), §15.7.
- **Dado** ejecuciones en distintos estados
- **Cuando** se llama a `GET /api/runs/{id}`
- **Entonces** devuelve tipo, estado, fase, capítulo, coste acumulado, posición, motivo y detalle:
  - el coste acumulado es la suma en USD del coste de las `SesionDeRol` de la ejecución;
  - la posición solo aparece si está `queued`;
  - el motivo y el detalle solo aparecen si está `failed` o `interrupted`.

  Ejemplos:
  - una ejecución segunda en la cola: posición 2 y sin fase;
  - una `running` en el capítulo 4: fase `writing`, capítulo 4 y sin posición;
  - una `interrupted`: motivo `provider_error` y su detalle;
  - una ejecución ajena: 404.

### 011-C05 — De la planificación a la escritura (T)
- **Sostiene:** Arq. §5.4, §9.1 (`Planificar`, `Validar pasa`).
- **Dado** una generación `queued` que el worker toma
- **Cuando** arranca y, después, la planificación deja el `PuntoDeControl` 0 (010)
- **Entonces**:
  - al arrancar, la ejecución pasa a `running` en fase `planning`, sin capítulo;
  - con el punto de control 0 pasa a fase `writing` con capítulo 1, sin abrir otra sesión del planner;
  - si la planificación termina en fallo, se aplica 011-C06.

### 011-C06 — Fallar descarta la candidata y libera la cola (T)
- **Sostiene:** Arq. §9.1 (`Fallar`, estados terminales), §9.3 (candidata `discarded`).
- **Dado** una ejecución que falla por un motivo de esta spec o por uno de 010 en la planificación. Los de esta spec son `retries_exhausted`, `banned_content`, `infeasible_config`, `resumes_exhausted` e `internal_error`.
- **Cuando** se registra el fallo
- **Entonces**:
  - la ejecución queda `failed` con su motivo, su detalle y su fecha de fin;
  - su candidata, si existe, queda `discarded`;
  - el worker toma la siguiente `queued`;
  - la novela puede relanzar su generación (011-C02);
  - reanudarla responde 409 (011-C25).

### 011-C07 — Ventana del writer (T)
- **Sostiene:** Arq. §6.1–§6.2, `definitions.md` §4 `VentanaDeContexto`.
- **Dado**:
  - una candidata con los capítulos 1–3 aceptados;
  - un outline cuyo capítulo 4 tiene un beat con revelación y cuyo capítulo 6 tiene otra (tema «el origen del faro», con su contenido);
  - el recuperador devuelve K1…K8 para el capítulo 4.
- **Cuando** el orquestador ensambla la ventana del writer del capítulo 4 en modo `write`
- **Entonces** la ventana tiene estas partes y nada más:
  - **Residentes:**
    - la StyleSheet;
    - la proyección del outline: los títulos de los 10 capítulos, los beats del 4 completos (también el contenido de su revelación) y, de los capítulos 5–10, solo los temas de sus revelaciones. «el origen del faro» aparece y su contenido no;
    - los resúmenes de 1, 2 y 3, en orden;
    - el final literal del 3;
    - los elementos obligatorios asignados al 4;
    - los hechos y los personajes de los beats del 4, con sus valores vigentes en la candidata.
  - **Entradas de la llamada:** el objetivo de 1.250 palabras.
  - **Recuperados:** K1…K8, en ese orden. Se piden al recuperador con la candidata, el capítulo 4, `top_k.writer` y la **consulta prospectiva**, que son las descripciones de los beats del 4.
- **Final literal:** son las últimas 300 palabras del capítulo anterior, contadas como en 011-C11. Van desde el principio de la palabra 300 empezando por el final hasta el final, con su puntuación y sus saltos de párrafo. De un capítulo 3 de 1.000 palabras, entra desde la palabra 701.
- No hay más texto de otros capítulos: nada del 1 ni del 2, y del 3 nada más que su final.
- La ventana del capítulo 1 no tiene resúmenes ni final literal.

### 011-C08 — Ventana del editor (T)
- **Sostiene:** Arq. §6.2, §7.2 (el editor no ve el razonamiento del writer).
- **Dado** la entrega del capítulo 4 que pasó los hooks (011-C10), y el recuperador devuelve R1…R8
- **Cuando** el orquestador ensambla la ventana del editor
- **Entonces** la ventana tiene estas partes:
  - **Residentes:**
    - la StyleSheet;
    - los resúmenes 1–3;
    - el capítulo 4 del outline: sus beats con sus eventos, personajes, lugares y hechos, y los elementos obligatorios asignados;
    - el índice de entidades de la candidata: forma canónica e identificador de cada personaje y lugar;
    - la rúbrica de capítulo: los cinco criterios de Arq. §11.3, qué juzga cada uno y cuáles bloquean.

    Cada hecho, personaje y lugar lleva su identificador, para poder declarar usos y eventos.
  - **Entradas de la llamada:** el título y el texto entregados, y los defectos de los linters (lista vacía mientras 018 no esté).
  - **Recuperados:** R1…R8, pedidos con la candidata, el capítulo 4, `top_k.editor` y la **consulta retrospectiva**, que es el texto entregado.
- **No entran**:
  - ningún mensaje de la sesión del writer: ni su razonamiento, ni sus entregas rechazadas, ni los defectos que le dieron los hooks;
  - la proyección del outline de otros capítulos;
  - el final literal del capítulo 3.
- Los elementos obligatorios asignados y el índice de entidades amplían la tabla de Arq. §6.2. Van en «Decisiones de esta spec».

### 011-C09 — Cada sesión reserva en el techo, y una que no cabe nunca hace fallar (T)
- **Sostiene:** Arq. §6.5, `definitions.md` §4 `TechoDeTokens`.
- **Dado** una sesión del writer o del editor a punto de abrirse
- **Cuando** el orquestador la reserva
- **Entonces**:
  - la reserva es la entrada estimada (los textos fijos más **su ventana**, con el estimador de 003) más (`max_turns` − 1) · `max_output_tokens` de su rol;
  - si no cabe, espera en orden de llegada, sin límite propio, y se abre cuando hay sitio;
  - si no cabría ni con todo el techo libre (en la fixture, `token_ceiling` = 5.000 y una ventana mayor), no se abre ninguna sesión y la ejecución falla con `infeasible_config` (011-C06).

### 011-C10 — Una entrega que pasa los hooks llega al editor (T)
- **Sostiene:** Arq. §7.5, §8.1.
- **Dado** el writer del capítulo 4
- **Cuando** entrega por `submit_chapter` un título y un texto de 1.250 palabras, con los nombres canónicos y sin entradas prohibidas
- **Entonces**:
  - el hook de policy permite;
  - el hook de validación de capítulo pasa, con `longitud-capitulo` (pasa, 1.250 palabras) y `nombres-exactos` (pasa);
  - la sesión del writer termina con esa entrega (`completed`);
  - se abre la sesión del editor con ella (011-C08);
  - solo cuenta la primera entrega que pasa los hooks.

### 011-C11 — `longitud-capitulo` en sus límites (T)
- **Sostiene:** Arq. §11.2, `definitions.md` §3 `Capitulo`; `verification.md` §5 C.4, 5a.3.
- **Palabra**: secuencia máxima de caracteres sin espacios que contiene al menos una letra o un dígito. El título no cuenta.
  - «—Hola —dijo.» son 2 palabras.
  - Una «—» o unos «…» sueltos no cuentan.
  - «1.250» cuenta.
- **Dado** una entrega con un texto del número de palabras de la tabla
- **Cuando** corre el hook de validación
- **Entonces** da lo de la tabla. Si bloquea:
  - la salida de la tool se sustituye por la lista de defectos, que nombra el validador, las palabras contadas y el rango;
  - el writer corrige en la misma sesión;
  - la entrega cuenta como intento del capítulo;
  - no se abre el editor.

| Palabras del texto | Resultado |
|---|---|
| 999 | Bloquea |
| 1.000 | Pasa |
| 1.500 | Pasa |
| 1.501 | Bloquea |

### 011-C12 — `nombres-exactos` sobre el título y el texto (T)
- **Sostiene:** Arq. §11.2 (regla de variante), `definitions.md` §2 `Personaje`; `verification.md` §5 5a.2, §6 U10.
- **Regla:**
  - Se miran las palabras del título y del texto que empiezan por mayúscula. Una palabra es un tramo de letras, así que «¿Toby?» es «Toby».
  - Se descartan las que coinciden exactamente con una palabra de algún nombre canónico de personaje.
  - Cada una de las restantes se compara con cada palabra con mayúscula inicial de los nombres canónicos de los personajes de la candidata. Las partículas como «de» no se comparan.
  - Es defecto si, sin mayúsculas ni acentos, es igual a esa palabra canónica (variante de mayúsculas o acentos), o si está a una distancia de edición (inserciones, borrados y sustituciones de una letra) de como mucho 2 cuando la canónica tiene 7 letras o más, de 1 cuando tiene de 4 a 6, y de 0 cuando tiene 3 o menos.
- **Dado** los personajes canónicos «Toby», «Nala», «Nela», «Ana», «Bernabé» y «Marta López»
- **Cuando** la entrega contiene la palabra de la tabla
- **Entonces**:
  - resulta lo de la tabla;
  - el defecto nombra la palabra y su canónico;
  - si bloquea, se aplica lo mismo que en 011-C11.

| Palabra | Resultado | Por qué |
|---|---|---|
| «Toby» | Pasa | Canónico |
| «toby» | Pasa | En minúscula: nunca se mira |
| «TOBY» | Defecto | Variante de mayúsculas |
| «Tóby» | Defecto | Variante de acentos |
| «Tomy» | Defecto | Distancia 1; el canónico tiene 4 letras |
| «Tomi» | Pasa | Distancia 2, mayor que 1 |
| «Nela» | Pasa | Es canónico, aunque esté a distancia 1 de «Nala» |
| «Nada», a principio de frase | Defecto | Distancia 1 de «Nala»; riesgo aceptado U10 |
| «ANA» | Defecto | Variante de mayúsculas de un canónico de 3 letras |
| «Ane» | Pasa | 3 letras: solo se admite distancia 0 |
| «Vernave» | Defecto | Distancia 2 de «Bernabé», de 7 letras |
| «Bernardo» | Pasa | Distancia 3 |
| «Lopez» | Defecto | Variante de acentos de «López» |
| «Marta» | Pasa | Es palabra de un nombre canónico |
| Título «El faro de Tobi» | Defecto | El título también se comprueba |

### 011-C13 — Qué cuenta como intento en la sesión del writer (T)
- **Sostiene:** Arq. §7.4, §7.5, §7.6 (`max_retries.chapter`), §8.1, §12.1; `definitions.md` §5 `Intento`.
- **Dado** el writer del capítulo 4 en su sesión
- **Cuando** hace la llamada de la tabla
- **Entonces** pasa lo de la tabla. En las filas que cuentan:
  - el writer recibe los defectos y corrige en la misma sesión;
  - no se abre el editor para esa entrega.

| Llamada del writer | Qué pasa | ¿Cuenta como intento? |
|---|---|---|
| `submit_chapter` con una `EntradaProhibida` de nivel `novel` en el texto o el título | El hook de policy deniega antes de que corra la tool, con el término y el motivo. No corren ni el schema ni el hook de validación | Sí |
| `submit_chapter` con una prohibida y 900 palabras | Solo la denegación de la policy | Sí, uno |
| `submit_chapter` fuera de schema, por ejemplo sin texto | Error de vuelta al modelo. No corre el hook de validación | Sí |
| `submit_chapter` con 1.501 palabras | 011-C11 | Sí |
| `Skill` con `personalizacion-natural` | Permitida | No |
| `Skill` con otra skill, o una tool que no está en su lista | La policy la deniega (005) | No: la acota `max_turns` |

### 011-C14 — Una sesión del writer que termina sin entrega válida es un intento fallido (T)
- **Sostiene:** Arq. §7.6 (`max_turns` y `session_timeout_seconds` → intento fallido).
- **Dado** una sesión del writer que termina sin ninguna entrega que pase los hooks: `turns_exhausted`, `time_exhausted`, o `completed` sin entregar
- **Cuando** el orquestador la cierra
- **Entonces**:
  - el intento en curso cuenta como fallido, además de las entregas rechazadas que ya contaron;
  - si quedan intentos, se abre otra sesión del writer en modo `rewrite` con la misma ventana y los defectos de la última entrega rechazada (ninguno si no llegó a entregar);
  - no se abre el editor.

### 011-C15 — La revisión del editor tiene schema y solo cita lo que existe (T)
- **Sostiene:** Arq. §7.2 (qué produce el editor), §7.4, §8.3 (entidades inexistentes = error de schema), §11.3; `definitions.md` §2 `Evento`.
- **Dado** el editor del capítulo 4
- **Cuando** entrega por `submit_review`
- **Entonces** la revisión es válida si tiene todo esto:
  - por cada uno de los cinco criterios de la rúbrica de capítulo, una puntuación entera de 1 a 5 y su justificación;
  - defectos, cada uno con criterio, bloqueante (sí o no) y mensaje;
  - usos de hechos, por su identificador;
  - eventos narrados, cada uno con: momento (fecha y hora); lugar; presentes, cada uno con la edad que le dé el texto, si se la da; tipo (`ordinary` o `exclusion`); excluido (solo si es `exclusion`); analepsis; y beat del capítulo 4;
  - un resumen no vacío.

  Una revisión como las de la tabla es un error que vuelve al editor en la misma sesión y no cuenta como intento del capítulo. Si la sesión del editor termina sin revisión válida, el intento del capítulo se cierra sin aceptar: `rewrite`, sin defectos del texto, si quedan intentos; `fail` si no.

| Revisión | Resultado |
|---|---|
| Falta un criterio, o una puntuación es 6 | Error |
| Un evento con un personaje o un lugar que no existe en la candidata | Error |
| Un uso con un identificador que no es de un hecho de la candidata | Error |
| Un `exclusion` sin excluido, o un `ordinary` con excluido | Error |
| Un beat fuera de los del capítulo 4 | Error |

### 011-C16 — El veredicto lo decide el código (T)
- **Sostiene:** Arq. §8.2, §11.3 (equilibrio), `definitions.md` §6 `Veredicto`, `Criterio`; `verification.md` §5 C.3.
- **Regla**:
  - Un defecto es bloqueante si su criterio es bloqueante (`fidelidad-canon`, `cumple-beats`) y además:
    - ese criterio puntúa por debajo del umbral. En este caso el código crea el defecto con la justificación del editor;
    - o el editor marca el defecto como bloqueante.
  - Un defecto de un criterio no bloqueante nunca bloquea, lo marque como lo marque el editor.
- **Dado** el intento de la tabla y el umbral 3
- **Cuando** el código agrega la revisión
- **Entonces**:
  - el veredicto es el de la tabla;
  - la misma revisión con los mismos umbrales da siempre el mismo veredicto.

| Intento | Puntuaciones y defectos | Veredicto |
|---|---|---|
| 1 de 3 | Todos 4, sin defectos | `accept` |
| 1 de 3 | `fidelidad-canon` 2 y el resto 5 (media 4,4) | `rewrite` |
| 1 de 3 | `cumple-beats` 3, igual al umbral | `accept` |
| 1 de 3 | `personalizacion-natural`, `prosa` y `tono` 1; `fidelidad-canon` y `cumple-beats` 5 | `accept`, con 3 defectos no bloqueantes que van al informe y a Langfuse |
| 1 de 3 | Un defecto marcado bloqueante en `prosa`; todo ≥ 3 | `accept`; el defecto cuenta como no bloqueante |
| 1 de 3 | Un defecto marcado bloqueante en `fidelidad-canon`, que puntúa 4 | `rewrite` |
| 3 de 3 | `fidelidad-canon` 2 | `fail`: `failed` con `retries_exhausted` |

### 011-C17 — Reescribir es una sesión nueva con los defectos (T)
- **Sostiene:** Arq. §8.2 («misma ventana y los defectos»), §7.2.
- **Dado** un veredicto `rewrite` en el intento 1 del capítulo 4
- **Cuando** empieza el intento 2
- **Entonces**:
  - se abre una sesión nueva del writer en modo `rewrite`;
  - su ventana es idéntica a la del intento 1 y las entradas de la llamada añaden los defectos del intento 1, bloqueantes y no bloqueantes;
  - no recibe el texto anterior;
  - corren los mismos hooks, el mismo editor y el mismo veredicto.

### 011-C18 — Los intentos de un capítulo se agotan con motivo (T)
- **Sostiene:** Arq. §7.6 (`max_retries.chapter`, `banned_content`), §12.1; `verification.md` §5 3.7, 7.4; §4.9 RT17.
- **Dado** `max_retries.chapter` = 2
- **Cuando** los intentos del capítulo 5 son los de la tabla
- **Entonces**:
  - resulta lo de la tabla;
  - nunca hay un cuarto intento;
  - en cada fallo, el informe tiene los defectos del último intento (011-C30) y se aplica 011-C06.

| Intentos del capítulo 5 | Resultado |
|---|---|
| `rewrite`, `rewrite`, `accept` | Aceptado en el 3.º; los tres intentos quedan con sus desenlaces |
| `rewrite`, `rewrite` y un 3.º con bloqueantes | `failed`, `retries_exhausted` |
| Tres entregas denegadas por una prohibida en la misma sesión | La sesión se corta tras la 3.ª, sin editor; `failed`, `banned_content` |
| Prohibida, prohibida y 1.501 palabras | `failed`, `retries_exhausted`: la última causa no fue una prohibida |
| 1.501, 1.501 y prohibida | `failed`, `banned_content` |

### 011-C19 — Aceptar un capítulo es una transacción (T)
- **Sostiene:** Arq. §6.3 (sucesoras), §6.4, §8.3, §9.2; `definitions.md` §3 `Capitulo`, §4 `CanonCard`.
- **Dado** un veredicto `accept` del capítulo 4
- **Cuando** se acepta
- **Entonces** una sola transacción escribe todo esto:
  - el capítulo 4: el título y el texto del writer, el resumen del editor, el número de palabras y la huella del título y el texto;
  - los `UsoDeHecho` (011-C20);
  - los eventos registrados, de origen `recorded`, con el capítulo 4, su beat y sus presentes con edad;
  - una `CanonCard` sucesora con `desde_capitulo` = 5 por cada personaje presente en un evento registrado del 4 y por cada lugar donde ocurre uno. El texto y el índice de la tarjeta son los de 016; las anteriores se conservan;
  - los `ResultadoDeValidador` del intento aceptado;
  - el `PuntoDeControl` 4.

  Después, la ejecución sigue en fase `writing` con el capítulo 5, cuya ventana tiene como residente el resumen del 4.

### 011-C20 — Los usos son los declarados más la coincidencia literal de los hechos nominales (T)
- **Sostiene:** Arq. §8.3, `definitions.md` §2 `UsoDeHecho`, `Hecho` (hecho nominal), §7 (forma normalizada); `verification.md` §5 4.2.
- **Dado**:
  - los hechos nominales «Toby» (nombre del perro), «Faro de Cabo Mayor» (un lugar) y «Ana» (una allegada);
  - el hecho no nominal «le da miedo el agua fría» (un rasgo).
- **Cuando** se acepta el capítulo con lo que declara el editor y lo que contiene el texto
- **Entonces**:
  - quedan los usos de la tabla;
  - la coincidencia literal va por tokens, en la forma normalizada de 005, sobre el valor de cada hecho nominal de la candidata.

| El editor declara | El texto contiene | Usos |
|---|---|---|
| El rasgo | — | El rasgo |
| Nada | «Toby,» | El nombre del perro |
| Nada | «el faro de cabo mayor» | El lugar |
| Nada | «mañana» y «Anabel» | Ninguno de «Ana»: la coincidencia respeta los límites de palabra |
| El nombre del perro | «Toby» | Uno solo, sin duplicar |
| Nada | Ninguno de los valores | Ninguno |

### 011-C21 — Si la transacción de aceptación falla, no queda nada del capítulo (T)
- **Sostiene:** Arq. §8.3 («si la transacción falla, no queda nada»), §8.4.
- **Dado** un fallo provocado en la última escritura de la aceptación del capítulo 4
- **Cuando** se deshace la transacción
- **Entonces**:
  - la candidata no tiene nada de esa aceptación: ni el capítulo 4, ni sus usos, sus eventos registrados, sus tarjetas sucesoras, los resultados del intento aceptado o el punto de control 4;
  - no sale ningún score de ese intento;
  - la ejecución queda `interrupted` con `crash` y conserva su candidata;
  - al reanudarla, el capítulo 4 se rehace desde cero (011-C27).

### 011-C22 — Volver a aceptar un capítulo reemplaza lo que dejó su aceptación anterior (T)
- **Sostiene:** Arq. §8.3 (reemplazo), `definitions.md` §2 `UsoDeHecho`, `Evento`, §4 `CanonCard`.
- **Dado**:
  - una candidata con los capítulos 1–10 aceptados, copia de una versión publicada;
  - el capítulo 4 se vuelve a aceptar, como hace la reescritura dirigida de 012, con otro texto, otros usos y otros eventos.
- **Cuando** se acepta de nuevo
- **Entonces**:
  - se reemplazan la fila del capítulo 4, sus usos, sus eventos registrados y las tarjetas que nacieron de él: no queda ninguno de los anteriores y no hay duplicados;
  - no se añade otro punto de control 4;
  - no cambian los capítulos 1–3 y 5–10 ni sus usos;
  - la versión publicada de la que se copió no cambia en nada.

### 011-C23 — Tras el décimo capítulo, el gate (T)
- **Sostiene:** Arq. §8.1, §9.1 (`Gate`).
- **Dado** una generación que acepta el capítulo 10
- **Cuando** escribe su punto de control 10
- **Entonces**:
  - la ejecución pasa a fase `gate`;
  - no se abre ninguna sesión del writer;
  - lo que sigue es de 012.

### 011-C24 — Un error del proveedor interrumpe y no cuenta como intento (T)
- **Sostiene:** Arq. §7.6 (error de transporte o del proveedor), §9.1 (`Caer`), §15.2 (límite de uso); `verification.md` §4.9 RT19.
- **Dado** una generación con los puntos de control 0–5
- **Cuando** la sesión del writer o del editor del capítulo 6 termina con `infrastructure_failure`, también por el límite de uso de la suscripción
- **Entonces**:
  - la ejecución queda `interrupted` con `provider_error`;
  - el intento en curso queda sin desenlace y no cuenta;
  - la candidata no tiene nada del capítulo 6 y se conserva;
  - el worker toma la siguiente `queued`.

### 011-C25 — Al arrancar el servidor, lo que estaba en curso se interrumpe (T)
- **Sostiene:** Arq. §7.6 (`max_resumes`), §9.1 (arranque).
- **Dado** una ejecución `running` y otras `queued` en el momento en que se detiene el servidor
- **Cuando** el servidor arranca de nuevo
- **Entonces**:
  - la que estaba `running` queda `interrupted` con `crash` si sus reanudaciones son menos que `max_resumes`;
  - si son iguales, queda `failed` con `resumes_exhausted` (011-C06);
  - las `queued` siguen igual y el worker toma la primera.

### 011-C26 — Reanudar vuelve a encolar la ejecución en su puesto (T)
- **Sostiene:** Arq. §9.2, §15.7, §15.8; `definitions.md` §5 `Ejecucion`.
- **Dado** A (creada en t1) `interrupted`, B (en t2) `running` y C (en t3) `queued`
- **Cuando** se llama a `POST /api/runs/{A}/resume`
- **Entonces**:
  - la respuesta es 202 con `run_id` y `position` = 1;
  - A está `queued` con su fecha de creación original, delante de C, y suma una reanudación;
  - cuando B termina, el worker toma A.
- **Rechazos**:
  - reanudar una ejecución `queued`, `running`, `published` o `failed` responde 409 y no cambia nada;
  - reanudar una ajena responde 404.
- **CLI**:
  - `story-maker resume <run_id>` hace lo mismo sobre una `interrupted`, y el worker del servidor en marcha la toma cuando queda libre, sin reiniciarlo;
  - con una ejecución que no está `interrupted`, o que no existe, sale con un código distinto de 0 y un mensaje, y no cambia nada.

### 011-C27 — Reanudar sigue tras el último punto de control (T)
- **Sostiene:** Arq. §5.4 (el punto de control 0 no replanifica), §7.6 (los intentos no se reinician), §8.4, §9.2; `verification.md` §5 4.5.
- **Dado** una ejecución que cayó en el punto de la tabla y se reanuda
- **Cuando** el worker la vuelve a lanzar
- **Entonces**:
  - sigue como dice la tabla;
  - conserva su traza (011-C31);
  - los puntos de control forman siempre 0…k, sin huecos ni duplicados.

| Dónde cayó | Puntos de control | Al relanzarse |
|---|---|---|
| En `planning`, antes de aplicar el plan | Ninguno | Fase `planning` (010), sin reiniciar los intentos del plan |
| Justo después de aplicar el plan | 0 | Fase `writing`, capítulo 1, sin planner |
| En el capítulo 6, con su intento 1 cerrado en `rewrite` y el 2 abierto | 0–5 | Fase `writing`, capítulo 6 desde cero, con la ventana ensamblada de nuevo. Le quedan 2 intentos: el cerrado cuenta y el interrumpido no |
| En `gate` o `rewriting` | 0–10 | Fase `gate` (012), sin reescribir ningún capítulo y sin tocar los puntos de control |

### 011-C28 — Caer con las reanudaciones agotadas es fallar (T)
- **Sostiene:** Arq. §7.6 (`resumes_exhausted`), §11.5 (`ReintentosAcotados`, `TerminaSiempre`).
- **Dado** una ejecución con 2 reanudaciones (`max_resumes` = 2) en el capítulo 3
- **Cuando** su sesión del writer termina con `infrastructure_failure`
- **Entonces**:
  - la ejecución queda `failed` con `resumes_exhausted`, no `interrupted`;
  - se aplica 011-C06.

### 011-C29 — Un error imprevisto del worker falla con `internal_error` (T)
- **Sostiene:** Arq. §2 (premisa 5), §9.1 (motivos de `failed`).
- **Dado** una excepción no prevista fuera de la transacción de aceptación, provocada al ensamblar una ventana
- **Cuando** el worker la recibe
- **Entonces**:
  - la ejecución queda `failed` con `internal_error` y el detalle;
  - se aplica 011-C06;
  - el servidor sigue atendiendo peticiones y el worker toma la siguiente.

### 011-C30 — El informe de la ejecución se calcula al pedirlo (T)
- **Sostiene:** Arq. §8.2 (no bloqueantes al informe), §15.7, `definitions.md` §6 `InformeDeEjecucion`.
- **Dado** una generación con una reanudación que falló con `retries_exhausted` en el capítulo 3
- **Cuando** se llama a `GET /api/runs/{id}/report`
- **Entonces** el informe tiene:
  - los validadores de cada capítulo y cada intento, con pasa o falla;
  - los defectos sin resolver: los bloqueantes del último intento del capítulo 3 y los no bloqueantes de los capítulos 1–2;
  - las decisiones de política de la ejecución (005);
  - los intentos de cada capítulo con su desenlace;
  - 1 reanudación;
  - el coste, que es la suma de sus `SesionDeRol`;
  - el motivo `retries_exhausted`.

  Además:
  - se calcula de lo guardado: dos peticiones sin cambios en medio dan lo mismo;
  - el informe de una ejecución ajena responde 404.

### 011-C31 — Trazas, spans y scores de la producción (T)
- **Sostiene:** Arq. §8.3 (scores tras el commit), §11.2, §13.1, §13.3; `definitions.md` §8, §12.3; `verification.md` §4.1.
- **Dado** una generación con el doble nulo de observabilidad, en la que el capítulo 2 se acepta al segundo intento
- **Cuando** avanza, se interrumpe y se reanuda
- **Entonces**:
  - hay una sola traza `generacion`, con la sesión igual al id de la novela, que la reanudación conserva;
  - hay un span `capitulo-<n>` por capítulo, que agrupa las sesiones del writer y del editor de todos sus intentos;
  - cada vez que corren los validadores salen los scores `longitud-capitulo` (0/1, con las palabras en el comentario), `nombres-exactos` (0/1), `rubrica-capitulo` (0/1) y `rubrica-capitulo/<criterio>` (1–5, con la justificación). Van asociados a la traza y al span del capítulo;
  - queda un `ResultadoDeValidador` por cada vez que corre un validador, con su intento;
  - los scores del intento 1 del capítulo 2 salen al cerrarse ese intento; los del intento aceptado, solo después del commit de su aceptación;
  - el score `palabras-prohibidas` y los spans `rol:` y `tool:` son de 005, 003 y 004.

### 011-C32 — Una producción real con el login de Claude Code llega al gate y se reanuda (D)
- **Sostiene:** Arq. §15.2 (`claude_login`), §8.4; `verification.md` §4.1 D, §4.2 (presupuesto de cuota).
- **Dado** la máquina con sesión de Claude Code, `LLM_PROVIDER=claude_login`, Langfuse real y un brief ficticio confirmado
- **Cuando**:
  - se lanza la generación;
  - tras aceptar el capítulo 3 se detiene el servidor;
  - al arrancar, se reanuda;
  - se deja llegar al gate.
- **Entonces**:
  - hay 10 capítulos aceptados de 1.000 a 1.500 palabras, con los puntos de control 0–10 sin duplicados;
  - el capítulo 4 se rehízo desde cero;
  - writer y editor escribieron en español y entregaron por tool;
  - en Langfuse hay una traza con los spans `capitulo-1` a `capitulo-10` y los scores de 011-C31, y cada `SesionDeRol` tiene su uso y su coste.
- **Cuota:** la ejecución queda en `gate`. Al detener otra vez el servidor queda `interrupted`, y el D de 012 la reanuda en el gate, sin gastar otra generación. El resultado va a `verification.md` §8 si provoca un cambio.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 011-I1 | Hay como mucho una ejecución `running` en el servidor, y las `queued` salen en orden de fecha de creación: una reanudada conserva su puesto. Dentro de una ejecución hay como mucho una sesión de rol abierta a la vez | T | 011-C03, 011-C26, y una prueba que registra las aperturas y los cierres de sesión de una generación completa |
| 011-I2 | `ReanudacionSinDuplicarNiPerder`: para cualquier secuencia de caídas en puntos arbitrarios, dentro de `max_resumes`, seguidas de reanudaciones: los puntos de control de la ejecución son 0…k sin huecos ni duplicados, reanudar sigue en k+1 y la candidata termina con los capítulos 1–10 una vez cada uno | T | Prueba de propiedades con caídas generadas en cada fase; refuerzo A en 006 |
| 011-I3 | `ReintentosAcotados`: un capítulo tiene como mucho 1 + `max_retries.chapter` intentos que cuentan y una ejecución como mucho `max_resumes` reanudaciones. Un error del proveedor nunca es un intento, y el intento que corta una caída no cuenta | T | 011-C18, 011-C24, 011-C27, 011-C28; refuerzo A en 006 |
| 011-I4 | La aceptación es atómica: tras ella está todo lo de 011-C19, o no hay nada | T | 011-C21, con el fallo provocado en cada una de las escrituras |
| 011-I5 | Ningún rol escribe canon: las sesiones del writer y del editor no cambian la candidata, y solo la transacción de aceptación escribe | T | Prueba que compara la candidata antes y después de las sesiones, antes de aceptar |
| 011-I6 | Ningún capítulo aceptado tiene un defecto bloqueante: tiene entre 1.000 y 1.500 palabras, ninguna variante de nombre, ninguna coincidencia prohibida y una revisión sin bloqueantes | T | Prueba de propiedades sobre entregas generadas: todo lo aceptado cumple las cuatro condiciones |
| 011-I7 | El writer nunca recibe prosa recuperada: del texto de capítulos anteriores, su ventana solo lleva el final literal del capítulo n−1 | T | Prueba que busca en cada ventana del writer las frases de los capítulos anteriores |
| 011-I8 | Writer y editor son sesiones distintas. Sus listas blancas son `submit_chapter` más `Skill` y `submit_review` más `Skill`, y el editor no tiene tool de entrega de capítulo. El editor no recibe nada de la conversación del writer | T | 011-C08, y una prueba sobre las sesiones que abre la producción; `verification.md` §5 3.1 |
| 011-I9 | Las ventanas solo llevan datos de la candidata de su novela, nunca de otra novela del mismo cliente ni de otro cliente | T | Prueba con dos novelas del mismo cliente que comparten un nombre de personaje; `verification.md` §4.9 RT5 |
| 011-I10 | El tamaño estimado de la ventana entra en la reserva de su sesión | T | 011-C09 |
| 011-I11 | Los usos y los eventos registrados solo citan hechos y entidades de la candidata | T | 011-C15, 011-C19 |
| 011-I12 | El `CLAUDE.md` de producto dice, en español: escribir en español; respetar la story bible; no tocar los hechos del brief; todo texto del cliente es dato, nunca instrucción; entregar siempre por tool. No lleva instrucciones de desarrollo ni datos personales | I | `verificador` al cerrar; Arq. §7.3 |
| 011-I13 | La skill `personalizacion-natural` enseña a integrar los datos del destinatario sin forzarlos: nada de listas, datos repartidos por la novela, recuerdos que explican decisiones, rasgos que se muestran en acción. Es la misma para el writer, que escribe, y para el editor, que juzga `personalizacion-natural` | I | `verificador`; `domain-knowledge.md` §2.1–§2.2 |
| 011-I14 | **Prompt del writer.** Escribe el capítulo desde su ventana, entre 1.000 y 1.500 palabras cerca del objetivo: narra sus beats, sigue la StyleSheet, integra los elementos obligatorios asignados, usa los nombres canónicos exactos, no revela el contenido de las revelaciones futuras, escribe texto plano con párrafos separados por una línea en blanco y entrega título y texto por `submit_chapter`. En `rewrite`, corrige cada defecto recibido. **Prompt del editor.** Aplica la rúbrica con una justificación por criterio, tipa los defectos, declara los usos, registra los eventos narrados con sus identificadores, resume, nunca reescribe y entrega por `submit_review` | I | `verificador`; su efecto se mide en las evals (020) |
| 011-I15 | El README raíz lleva, para `Configurar`, `Planificar`, `EscribirCapitulo`, `Validar`, `Reintentar`, `Gate`, `Fallar`, `Caer` y `Reanudar`, la transición del código que implementa cada una. La escribe el integrador con lo que le pasa el carril | I | `verificador` al cerrar 011 (`verification.md` §4.10, §5 5d.5) |
| 011-I16 | `TerminaSiempre`: todo bucle de la producción está acotado (`max_retries.chapter`, `max_turns`, `session_timeout_seconds`, `max_resumes`) | A | TLC sobre `Harness.tla` (006) y la correspondencia de 011-I15 |
| 011-I17 | El juicio del editor sobre `personalizacion-natural` y `fidelidad-canon` es el de su rúbrica; su fiabilidad no se prueba aquí | I | Evals y revisión humana (020); `verification.md` §5 C.1, C.2 |
| 011-I18 | Riesgos aceptados que afectan a esta spec: un uso parafraseado que el editor no declara queda sin registrar (U9); `nombres-exactos` es imperfecto (U10); el estimador chars/4 puede subestimar (U22); la naturalidad solo se juzga (U2) | U | `verification.md` §6 |

## Decisiones de esta spec

Pendientes de pasar a `architecture.md` §18. Las dos primeras piden además el proceso 1 antes de aprobar.

| Decisión | Opciones | Criterio | Elección |
|---|---|---|---|
| Título del capítulo | Copiado del outline (`definitions.md` §3) · lo entrega el writer (Arq. §7.2, §8.3) | La huella incluye el título, y un cambio debe poder corregir un título con el valor antiguo | Lo entrega el writer. Su ventana lleva el del outline. Hay que corregir `definitions.md` §3 `Capitulo` |
| Ventana del editor | La de Arq. §6.2 · añadir los elementos obligatorios asignados y el índice de entidades con identificadores | Sin identificadores no puede declarar el uso de un obligatorio no nominal (y `elementos-obligatorios` fallaría) ni registrar eventos | Se añaden (011-C08). Hay que ampliar Arq. §6.2 |
| Palabra y final literal | Separar por espacios · tramos con letra o dígito | Determinista y sin contar la puntuación suelta | Tramo sin espacios con letra o dígito; el título no cuenta; el final literal son las últimas 300 palabras exactas |
| Comparación de `nombres-exactos` | Nombre entero · palabra a palabra | Nombres de varias palabras y partículas | Palabra a palabra, contra las palabras canónicas con mayúscula, sobre la forma sin mayúsculas ni acentos, en el título y el texto |
| Coincidencia literal de los hechos nominales | Subcadena · forma normalizada de 005 | Una sola normalización en todo el sistema, con límites de palabra | Forma normalizada y tokens de 005 |
| Qué cuenta como intento | Cualquier denegación · solo las entregas | `definitions.md` §5 `Intento` | Cuentan cada `submit_chapter` rechazado, la sesión del writer sin entrega válida y la del editor sin revisión válida. No cuentan las denegaciones de otras tools ni los errores de schema del editor |
| Defecto bloqueante | Lo marca el editor · lo deriva el código | Las columnas «B» de Arq. §11.3; sin compensar | Criterio B bajo el umbral, o defecto marcado bloqueante en un criterio B. En un criterio no B, nunca |
| Fin de la sesión del writer | Seguir hasta que el modelo pare · cerrar con la primera entrega que pasa los hooks | Una sola entrega por intento | La primera que pasa los hooks cierra la sesión |
| Fallo de la transacción de aceptación | `failed` (`internal_error`) · `interrupted` (`crash`) | «Se rehace» (§8.3), con bucle acotado | `interrupted` con `crash`. Otra excepción imprevista da `failed` con `internal_error` |
| `ResultadoDeValidador` | Solo el del intento aceptado · uno por ejecución del validador | Las detecciones de las evals (`verification.md` §4.2) | Uno por cada vez que corre, con su intento. Los scores del intento aceptado salen después del commit |
| Punto de control al volver a aceptar | Uno nuevo · ninguno | Un prefijo sin duplicados | Ninguno |
| `story-maker resume` | Ejecutar en la CLI · solo volver a encolar | Un proceso y un techo en memoria (Arq. §1.4) | Solo vuelve a encolar; ejecuta el worker del servidor |

## Docs referenciados

- **`architecture.md`**:
  - §2: premisas 2, 3 y 5.
  - §5.4: el punto de control 0.
  - §6.1–§6.2 (ventanas), §6.3 (sucesoras y corte temporal), §6.4, §6.5.
  - §7.2–§7.7.
  - §8.1–§8.4.
  - §9.1 (máquina de estados, cola, estados y motivos), §9.2, §9.3 (candidata `discarded` o conservada).
  - §11.2 (`longitud-capitulo`, `nombres-exactos`, `rubrica-capitulo`), §11.3 (rúbrica de capítulo y equilibrio), §11.5.
  - §12.1: prohibidas en el hook de policy y `banned_content`.
  - §13.1–§13.3.
  - §15.2 (límite de uso), §15.4 (claves de config), §15.7 (API de ejecuciones), §15.8 (`resume`).
- **`definitions.md`**:
  - §2: `Personaje` (variante de nombre), `Hecho` (hecho nominal), `UsoDeHecho`, `Evento`.
  - §3: `Capitulo`, `Outline`, `Beat`, `StyleSheet`.
  - §4: `VentanaDeContexto`, `CanonCard`, `ResumenDeCapitulo`, `TechoDeTokens`.
  - §5: `Rol`, `SesionDeRol`, `WorkspaceDelHarness`, `Tool`, `Hook`, `Skill`, `Ejecucion`, `Intento` y `Evaluable`, `PuntoDeControl`, componentes de código.
  - §6: `Validador`, `ResultadoDeValidador`, `Criterio`, `Rubrica`, `Defecto`, `Veredicto`, `Score`, `InformeDeEjecucion`.
  - §7: forma normalizada.
  - §8.
  - §11.1.
  - §12.
- **`domain-knowledge.md`**: §2.1–§2.3 (la skill y la rúbrica); §5.3 (por qué el evento registrado lleva beat y edad).
- **`verification.md`**:
  - §2 (clases).
  - §3.3 (unitarias e integración con dobles), §3.4.
  - §4.1, §4.3.
  - §4.9: RT5, RT15, RT17 y RT19.
  - §4.10: correspondencia con el README.
  - §5, filas: C.1, C.2, C.3, C.4, 3.1, 3.3, 3.4, 3.7, 4.2, 4.4, 4.5, 5a.2, 5a.3, 5d.5, 7.1 y 7.4.
  - §6: U2, U9, U10 y U22.
- **Specs vecinas**: 003-puerto-de-agente, 005-guardarrailes, 010-planificacion, 012-gate-de-publicacion, 016-recuperacion-hibrida, 018-linters-de-prosa, 014-cambios-del-lector, 019-edicion-manual, 002-autenticacion, 004-observabilidad, 009-story-bible-y-versiones, 001-base.

## Autorrevisión

| Pregunta | Resolución | Fuente |
|---|---|---|
| ¿Qué módulos posee la 011? | Cola, worker, producción y reanudación; validadores de capítulo; el `CLAUDE.md` de producto, la skill y los prompts del writer y del editor; la API de ejecuciones; `resume` | `backend/AGENTS.md` (propiedad) |
| ¿Dónde empieza y dónde acaba? | Empieza al lanzar la ejecución. Lo que va del arranque al punto de control 0 es de 010; lo que va del punto de control 10 en adelante, de 012 | Arq. §5.4, §9.1, §9.4 |
| ¿Quién ensambla los recuperados? | El orquestador pide y el recuperador (016) devuelve. Los casos fijan su respuesta | Arq. §6.1, §6.3 |
| ¿Linters antes que 018? | El editor recibe su lista, vacía hasta 018 | Arq. §11.2, `TODO.md` (018 depende de 011) |
| ¿Qué es una palabra? ¿Y «~300 palabras»? | Tramo sin espacios con letra o dígito; exactamente 300 | Hueco del doc → decisión |
| ¿Cómo se compara un nombre de varias palabras? | Palabra a palabra, sin las partículas | Hueco del doc → decisión |
| ¿Qué cuenta como intento en cada sesión? | Ver 011-C13, 011-C14, 011-C15 | `definitions.md` §5 `Intento`; hueco → decisión |
| ¿Puede el editor bloquear por `prosa`? | No: solo bloquean los criterios B | Arq. §11.3 (equilibrio) → decisión |
| ¿El título lo escribe el writer? | Sí | **Contradicción de los docs**: `definitions.md` §3 frente a Arq. §7.2 |
| ¿Cómo declara el editor usos y eventos sin identificadores? | Su ventana los lleva, más los obligatorios asignados y el índice de entidades | **Hueco de Arq. §6.2** → decisión con proceso 1 |
| ¿Qué pasa si falla la transacción? | `interrupted` con `crash`; se rehace al reanudar | Arq. §8.3 «se rehace» → decisión |
| ¿Puede la CLI ejecutar? | No: dos procesos romperían el techo en memoria | Arq. §1.4, §6.5 |
| ¿Qué D, y cuánta cuota gasta? | Una generación que 012 reanuda en el gate | `CLAUDE.md` raíz (agrupar las D), `verification.md` §4.2 |
| ¿Dependencias que faltan en `TODO.md`? | La API necesita 002 (propiedad) y la ventana necesita 016 (recuperador y tarjetas) | Aviso al integrador |
