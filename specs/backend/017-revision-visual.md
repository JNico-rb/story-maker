# 017 — Revisión visual

> Carril: B · Depende de: 012-gate-de-publicacion, 013-lectura-y-pdf (y, a través de ellas, 003, 005, 009 y 011) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Entregar el validador `revision-visual`, la tercera etapa del `GateDePublicacion` (`architecture.md` §9.4): el **revisor visual** abre con Playwright MCP la `VistaDeVersion` de la candidata, recorre portada, índice, capítulos y ficha, sigue cada enlace y entrega lo que ha observado; el código calcula desde SQLite la **estructura esperada**, compara y decide. El modelo navega; no juzga (§11.2). Un **fallo de datos** (una entidad de la `FichaDePersonajes` sin capítulo) vuelve al editor para que registre de nuevo; un **fallo de render** hace fallar la ejecución con `render_failure`.

Cubre la validación visual por browser MCP del encargo (§5a) y la parte visual del índice navegable, de la ficha con enlaces y de la portada con dedicatoria (`verification.md` §5, filas 2.2, 2.3, 2.4 y 5a.6).

## Alcance

- **La sesión del revisor visual** (`visual_reviewer`, etiqueta `revisor-visual`): qué recibe, sus tools, su servidor MCP, el origen al que puede navegar y su prompt versionado.
- **Lo que entrega** con `submit_visual_review`: solo observaciones, sin veredicto.
- **La estructura esperada**, calculada desde la candidata: portada, índice, capítulos y ficha.
- **La comprobación de datos**: entidades de la ficha sin capítulo, y los capítulos a los que se atribuyen.
- **La comparación** entre lo observado y lo esperado, parte por parte, y la clasificación de cada defecto como de datos o de render.
- **El resultado**: `ResultadoDeValidador`, span y scores (`revision-visual` y uno por parte).
- **La salida que la etapa entrega al gate**: pasa; fallo de datos atribuido; defecto no atribuible; fallo de render; sesión sin entrega válida; navegador no disponible. La etapa corre en el gate de los tres tipos de `Ejecucion`.

## Fuera de alcance

- Orden de las etapas del gate, ciclos del gate y `max_retries.gate_cycles`, reescritura dirigida, mecánica del re-registro por el editor sin writer, publicación → 012-gate-de-publicacion (§9.4).
- La `VistaDeVersion` (plantilla, anclas, marca, página de novedades, marcas «cambiado en vN»), el token de vista (firma, caducidad, 401), el cálculo de en qué capítulos **aparece** cada entidad de la ficha, el PDF y `pdf-enlaces` → 013-lectura-y-pdf (§14.2). Los enlaces de la página de novedades los comprueba `pdf-enlaces`, no esta etapa.
- Mecánica común de las sesiones de rol: reserva en el `TechoDeTokens` (y `infeasible_config` si no cabe), tools integradas desactivadas, exclusión de los `CLAUDE.md` de los padres y del `.mcp.json` raíz, `schema-salida`, desenlaces de la `SesionDeRol`, spans `rol:` y `tool:`, hook de observabilidad → 003-puerto-de-agente (§6.5, §7.3–§7.5). Exportación a Langfuse → 004-observabilidad.
- Las reglas del `MotorDePoliticas` (lista blanca, origen de navegación) y el `AuditLog` → 005-guardarrailes (§12.2, §12.3); aquí solo se comprueba que la sesión del revisor las recibe con su lista y su origen.
- La aceptación de un capítulo re-registrado (sustituye sus usos, eventos registrados y tarjetas) → 011-produccion-de-capitulos (§8.3), igual que la coincidencia literal normalizada de los nombres.
- Qué hace el gate de una edición manual con un defecto atribuido al capítulo editado → 019-edicion-manual (§10.3).
- Reanudar una ejecución interrumpida en el gate → 011 y 012 (§9.2).
- La estética (un CSS que no carga, un solape): riesgo aceptado `verification.md` §6 U3. La inspección de la SPA con el browser MCP en desarrollo → specs de frontend (`verification.md` §9.3).

## Comportamiento observable

Casos **T** con el doble falso del puerto de agente como revisor visual (y como editor, en la integración) y el doble nulo de observabilidad; ninguno abre un navegador ni llama a un modelo. Casos **D** con Playwright MCP en Edge y, si llevan revisor real, con `LLM_PROVIDER=claude_login`: se agrupan al final y gastan cuota.

**Comparación de textos** (017-C05): dos textos coinciden si son iguales tras colapsar los espacios (saltos de línea incluidos) y sin distinguir mayúsculas; las letras, los acentos y los signos cuentan. El **destino** de un enlace es la parte de la vista a la que lleva: el capítulo *n*, la portada, el índice, la ficha, o ninguna.

### 017-C01 — La estructura esperada sale de la candidata (T)
- **Dado** una candidata con sus 10 capítulos aceptados; el destinatario «Marta»; el allegado «Toby», que aparece en los capítulos 2 y 5; el lugar «Villaverde», con un evento registrado en el capítulo 3; y la dedicatoria del brief
- **Cuando** el validador calcula la estructura esperada
- **Entonces** la portada lleva el título de la novela del outline de la candidata, el nombre canónico del destinatario en su story bible («Marta») y la dedicatoria del brief; el índice, 10 entradas, y la *i*-ésima tiene por destino el capítulo *i*; los capítulos, los 10 con su número, su título y su texto; la ficha, cada personaje y cada lugar de la story bible de la candidata, con el conjunto de capítulos en que **aparece** según la ficha de 013 (Toby → {2, 5}; Villaverde → {3})
- **Y**, en la candidata de un cambio del lector que renombra al perro de «Toby» a «Nala», la esperada lleva «Nala» y nunca «Toby»: solo se mira la candidata, no la versión base

### 017-C02 — El revisor recibe la dirección de la vista y la forma de lo que entrega, no los valores (T)
- **Dado** la candidata de 017-C01
- **Cuando** se abre la sesión del revisor visual
- **Entonces** sus entradas son la dirección de la `VistaDeVersion` de la candidata, en el origen de `STORY_MAKER_BASE_URL` y con un token de vista de esa versión (013), y la estructura: las cuatro partes, qué entregar de cada una, 10 capítulos y cuántos personajes y lugares tiene la ficha
- **Y** ninguna entrada contiene el título de la novela, el nombre del destinatario, la dedicatoria, un título de capítulo, un nombre de entidad ni texto de un capítulo

### 017-C03 — La sesión del revisor solo navega la vista (T)
- **Dado** la sesión del revisor visual, abierta con el doble
- **Cuando** se leen las opciones con que se abre y el doble intenta llamadas a tools
- **Entonces** usa el modelo `roles.visual_reviewer.model`; sus tools permitidas son exactamente `browser_navigate`, `browser_snapshot`, `browser_click` y `submit_visual_review`, sin `Skill`; declara un único servidor MCP, Playwright MCP en Edge, con su salida dentro de `STORY_MAKER_DATA_DIR`
- **Y** el hook de policy responde según la tabla; cada denegación da el motivo al modelo, deja su fila en el audit log con origen `policy_hook` y su span `tool:` con nivel WARNING, y la sesión sigue y puede entregar

| Llamada | Decisión |
|---|---|
| `browser_navigate` a la dirección de la vista | allow |
| `browser_navigate` a otra ruta del mismo origen | allow (el token de vista decide, 013) |
| `browser_navigate` con otro puerto, otro host, `localhost` por `127.0.0.1`, `https` por `http` o `file://` | deny |
| `browser_type`, `Bash`, `Skill` o cualquier tool fuera de la lista | deny |

### 017-C04 — Una revisión que coincide pasa (T)
- **Dado** la candidata de 017-C01 y una entrega que observa exactamente lo esperado
- **Cuando** el código compara
- **Entonces** `revision-visual` pasa y pasan las cuatro partes; la etapa entrega «pasa» y el gate sigue con el PDF (012)

### 017-C05 — La comparación tolera espacios y mayúsculas, no letras (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** la entrega trae lo observado de la tabla
- **Entonces** el resultado es el de la tabla

| Observado | Esperado | Resultado |
|---|---|---|
| «MARTA» | «Marta» | coincide |
| «Para  Marta,⏎con cariño» | «Para Marta, con cariño» | coincide |
| «Martha» | «Marta» | no coincide |
| «Márta» | «Marta» | no coincide |
| «Para Marta con cariño» | «Para Marta, con cariño» | no coincide |
| Primera frase del capítulo 3, observada bajo el título del 3 | Texto del 3 | coincide (la frase está en el texto de ese capítulo) |
| Primera frase del capítulo 4, observada bajo el título del 3 | Texto del 3 | no coincide |
| Primera frase vacía | Texto del 3 | no coincide |

### 017-C06 — Una portada que no muestra lo suyo es fallo de render (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** la entrega observa en la portada, en cada caso, sin dedicatoria; la dedicatoria de otra novela; sin título; o, en la candidata que renombró al destinatario, el nombre antiguo
- **Entonces** hay un defecto de render en la parte `portada`, bloqueante y sin capítulo, que dice qué se esperaba y qué se vio; `portada` no pasa y las otras tres partes se evalúan igual

### 017-C07 — Un índice que no lleva a sus capítulos es fallo de render (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** la entrega observa en el índice, en cada caso, 9 entradas; 11 entradas; la 4.ª con destino el capítulo 5; la 7.ª sin destino; las entradas 2 y 3 en orden inverso
- **Entonces** hay un defecto de render en la parte `indice`, sin capítulo, por cada discrepancia; con 10 entradas cuyos destinos son 1…10 en orden, `indice` pasa

### 017-C08 — Un capítulo que no se ve entero es fallo de render (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** la entrega observa, en cada caso, 9 capítulos sin el 6; el 3 con un título distinto; el 8 sin primera frase; un capítulo 11
- **Entonces** hay un defecto de render en la parte `capitulos`, sin capítulo atribuido, que nombra el capítulo implicado en el mensaje

### 017-C09 — Una ficha que no enlaza lo que debe es fallo de render (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** la entrega observa en la ficha, en cada caso, sin «Villaverde»; «Toby» sin el enlace al capítulo 5; «Toby» con un enlace de destino el 3 en lugar del 2; «Toby» con un enlace de más, al 7; un enlace de «Toby» sin destino; una entidad que no está en la story bible
- **Entonces** hay un defecto de render en la parte `ficha`, sin capítulo, que nombra la entidad; con cada entidad presente y el conjunto de destinos de sus enlaces igual al esperado, `ficha` pasa

### 017-C10 — Una entidad sin capítulo cuyo nombre sale en el texto es un fallo de datos atribuido, y no se abre el revisor (T)
- **Dado** una candidata con el lugar «Zahara» sin capítulo en la ficha (ningún `UsoDeHecho` de sus hechos y ningún evento registrado en él), cuyo nombre canónico aparece en el texto de los capítulos 3 y 7 con la coincidencia literal de la aceptación (011)
- **Cuando** corre el validador
- **Entonces** no se abre la sesión del revisor visual; `revision-visual` no pasa con dos defectos de datos en la parte `ficha`, bloqueantes, atribuidos uno al capítulo 3 y otro al 7, cuyo mensaje nombra la entidad y dice que la ficha no la enlaza; la etapa entrega «fallo de datos» con los capítulos 3 y 7. Portada, índice y capítulos no se evalúan en ese ciclo, aunque la vista tuviera además un fallo de render: saldría en el ciclo siguiente

### 017-C11 — Una entidad sin capítulo que ningún capítulo nombra es un defecto no atribuible (T)
- **Dado** una candidata con el allegado «Toby» sin capítulo en la ficha y cuyo nombre no aparece en ningún capítulo, haya o no además entidades como la de 017-C10
- **Cuando** corre el validador
- **Entonces** no se abre la sesión del revisor visual; hay un defecto de datos en `ficha`, bloqueante y sin capítulo, que nombra a «Toby»; la etapa entrega «no atribuible» y la ejecución termina `failed` con `unattributable_defect`, con la entidad en el `InformeDeEjecucion`

### 017-C12 — Una entrega fuera de schema vuelve al revisor (T)
- **Dado** la sesión del revisor visual con el doble
- **Cuando** el doble entrega `submit_visual_review` sin la parte `ficha`, o con un capítulo sin número, y después una entrega válida
- **Entonces** la primera vuelve al modelo como error de schema en la misma sesión (`schema-salida`, 003) y no produce resultado; se compara solo la válida
- **Y** una parte vacía no es error de schema: significa «no lo vi» y se compara (017-C13)

### 017-C13 — Una vista vacía o con error es fallo de render en las cuatro partes (T)
- **Dado** la estructura esperada de 017-C01
- **Cuando** el revisor entrega las cuatro partes vacías, como tras abrir una vista en blanco o una página de error del servidor
- **Entonces** hay defectos de render en `portada`, `indice`, `capitulos` y `ficha`; la etapa entrega «fallo de render»

### 017-C14 — Una sesión sin entrega válida es un ciclo fallido, no un defecto de la novela (T)
- **Dado** la etapa con el doble del revisor visual
- **Cuando** su sesión termina sin una entrega válida de `submit_visual_review`: con desenlace `turns_exhausted`, con `time_exhausted`, o `completed` sin haber entregado
- **Entonces** no hay resultado de la comparación; la etapa entrega «sin entrega», el ciclo del gate cuenta como fallido sin capítulos atribuidos y, si quedan ciclos, empieza otro sin reescribir ni re-registrar nada; con los ciclos agotados, la ejecución termina `failed` con `retries_exhausted`; en ningún caso se pasa al PDF

### 017-C15 — Sin navegador, la ejecución se interrumpe y no publica (T)
- **Dado** la etapa con el doble, que simula que el servidor Playwright MCP no conecta
- **Cuando** se abre la sesión del revisor visual
- **Entonces** la sesión termina con desenlace `infrastructure_failure` y la ejecución pasa a `interrupted` con `provider_error`, con un detalle que nombra el navegador; no se compara nada, no se genera el PDF y no se publica; es infraestructura, no un intento (§7.6)

### 017-C16 — Cada revisión deja su resultado, su span y sus scores (T)
- **Dado** los casos 017-C04, 017-C06 y 017-C10, cada uno en un ciclo del gate de una ejecución
- **Cuando** termina el validador
- **Entonces** hay una fila en `validator_results` por ciclo en que corrió: validador `revision-visual`, la candidata, sin capítulo, pasa o no, score 0/1 y un detalle con el resultado de cada parte evaluada y cada defecto (parte, clase de datos o de render, capítulo si lo tiene, mensaje)
- **Y** la traza de la ejecución tiene un span `validador:revision-visual`, el score `revision-visual` (0/1) y uno por parte evaluada, `revision-visual/portada`, `/indice`, `/capitulos` y `/ficha` (0/1), con los defectos en el comentario; en 017-C10 solo se envían `revision-visual` y `revision-visual/ficha`
- **Y** cuando se abrió la sesión, su span `rol:revisor-visual` y los `tool:` de sus llamadas están en la misma traza (003, 004)

### 017-C17 — Integración: un fallo de datos vuelve al editor y el ciclo siguiente publica (T)
- **Dado** una ejecución `generation` con los dobles, cuyo primer ciclo del gate llega a la revisión visual con «Zahara» como en 017-C10, pero nombrada solo en el capítulo 3, y cuyo doble del editor, al volver a registrar el 3, registra un evento en «Zahara»
- **Cuando** corre el gate
- **Entonces** en el ciclo 1 `revision-visual` falla por datos con el capítulo 3; el editor vuelve a registrar el 3 con el defecto como entrada y sin writer (no se abre ninguna sesión del writer; el texto y la huella del 3 no cambian); en el ciclo 2 la ficha esperada lleva Zahara → {3}, `revision-visual` pasa, se genera el PDF y se publica; `validator_results` tiene dos filas de `revision-visual`, la primera no pasa y la segunda sí
- **Y** si el doble del editor no la registra nunca, cada ciclo repite el mismo fallo de datos y, agotado `max_retries.gate_cycles`, la ejecución termina `failed` con `retries_exhausted`, el defecto en el informe y ningún ciclo de más

### 017-C18 — Integración: un fallo de render hace fallar la ejecución (T)
- **Dado** una ejecución con los dobles cuyo revisor visual entrega la portada sin dedicatoria (017-C06)
- **Cuando** corre el gate
- **Entonces** la ejecución termina `failed` con `render_failure`; no se reescribe ni se re-registra ningún capítulo, no se genera el PDF y no se publica; el `InformeDeEjecucion` muestra los defectos de `revision-visual` por parte

### 017-C19 — La revisión visual corre en el gate de un cambio y de una edición manual (T)
- **Dado** una ejecución `change_request` que renombra al perro de «Toby» a «Nala» y una `manual_edit`, cada una con su candidata, con los dobles
- **Cuando** su gate llega a la tercera etapa
- **Entonces** `revision-visual` corre sobre la vista de su candidata, con la estructura esperada de esa candidata (017-C01): una ficha que aún muestra «Toby» es fallo de render; una que muestra «Nala» con sus enlaces pasa

### 017-C20 — Sonda de la vista con el browser MCP de desarrollo (D)
- **Dado** la `VistaDeVersion` de una versión de datos ficticios (10 capítulos de unas 1.250 palabras y una ficha con varios personajes y lugares), servida en `http://127.0.0.1`
- **Cuando** Claude Code la abre con el Playwright MCP de `.mcp.json` (el mismo paquete que usa el revisor), toma la instantánea, pulsa un enlace del índice, uno de la ficha y uno roto sembrado en local sin commit
- **Entonces** se anotan los tokens estimados (caracteres / 4) de la instantánea entera, si cada clic devuelve la instantánea completa y si el enlace roto se distingue de uno válido tras pulsarlo; con eso se fijan los provisionales `roles.visual_reviewer.max_turns` y `max_output_tokens` y se comprueba sobre el papel 017-I7. Si la reserva no cabe en `token_ceiling` siguiendo cada enlace, se para y se reabre §11.2 por el proceso 1 antes de escribir el prompt. Fila en `verification.md` §9.3 (y en §8 si cambia el diseño)

### 017-C21 — El revisor real aprueba una vista correcta (D)
- **Dado** la vista de 017-C20 sin defectos sembrados, el puerto de agente real y la sesión de Claude Code iniciada
- **Cuando** corre el validador sobre esa versión
- **Entonces** `revision-visual` pasa en las cuatro partes; la `SesionDeRol` del revisor se guarda con su uso, que no supera su reserva; en Langfuse se ven el span `validador:revision-visual`, la sesión `rol:revisor-visual` con sus `tool:` y los cinco scores

### 017-C22 — El revisor real caza un enlace de la ficha sembrado roto (D)
- **Dado** la vista de 017-C21 con un enlace de la ficha roto, sembrado en local sin commit: en una pasada lleva a otro capítulo y en otra a un ancla que no existe
- **Cuando** corre el validador en cada pasada
- **Entonces** `revision-visual` falla con un defecto de render en `ficha` que nombra la entidad del enlace; al retirar el defecto, vuelve a pasar. Resultado en `verification.md` §4.2 y, si el revisor no lo caza, en §8 con el cambio que provoca

### 017-C23 — En la primera generación real, la etapa corre en el gate (D)
- **Dado** la primera generación real (la del brief 1 de 020 o `story-maker example`), sin generación adicional para esta spec
- **Cuando** su gate llega a la tercera etapa
- **Entonces** `validator_results` tiene la fila de `revision-visual` de cada ciclo y Langfuse muestra su span, la sesión del revisor y sus scores en la traza de la ejecución

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 017-I1 | El resultado lo decide el código: la entrega del revisor solo trae observaciones, y la misma estructura esperada con la misma entrega da siempre el mismo resultado, con los mismos defectos en el mismo orden | T | Prueba que repite la comparación de 017-C04 a 017-C13; la entrega no tiene campo de veredicto |
| 017-I2 | El revisor nunca recibe los valores que el código compara (título, nombre del destinatario, dedicatoria, títulos y textos de capítulo, nombres de entidades): lo que entrega es observación, no eco | T | 017-C02, sobre las entradas que registra el doble |
| 017-I3 | `revision-visual` no escribe canon ni capítulos: la story bible y los capítulos de la candidata son idénticos antes y después de la etapa; solo añade su `ResultadoDeValidador` | T | Huella de las tablas de ámbito versión antes y después, en 017-C04, 017-C06 y 017-C10 |
| 017-I4 | Todo defecto de `revision-visual` es de datos o de render: los de datos son de la parte `ficha` y llevan el capítulo en que sale el nombre de la entidad, o ninguno si no sale en ninguno; los de render nunca llevan capítulo | T | 017-C06 a 017-C11 y 017-C13 comprueban la clase y el capítulo de cada defecto |
| 017-I5 | Si en un ciclo `revision-visual` no pasa (por datos, render, sin entrega o sin navegador), en ese ciclo no se genera el PDF ni se publica | T | 017-C10, 017-C11, 017-C14, 017-C15, 017-C17 y 017-C18; refuerzo A: `NuncaPublicaSinValidar` (006) |
| 017-I6 | La sesión del revisor visual solo tiene sus cuatro tools y el servidor Playwright MCP, sin `Skill`, solo navega el origen de la vista y solo escribe en el directorio de datos | T | 017-C03 |
| 017-I7 | Con la config por defecto, la reserva de la sesión del revisor visual cabe en `token_ceiling` y su uso real no la supera | D | 017-C20 (sobre el papel), 017-C21 (medido en `role_sessions`) |
| 017-I8 | El prompt del revisor visual le pide abrir la dirección recibida, recorrer las cuatro partes, seguir cada enlace, entregar siempre por `submit_visual_review` lo que ve, también si la vista está vacía o da error, y no juzgar | I | Lectura del `verificador` al cerrar; demostrado en 017-C21 y 017-C22 |
| 017-I9 | La estética de la vista no se verifica: un CSS que no carga o un solape no están en la instantánea | U | `verification.md` §6 U3 |
| 017-I10 | Un revisor que copia mal lo que ve da un falso fallo de render, que es terminal | U | Propuesto para `verification.md` §6 (comparación tolerante de 017-C05; medido en 017-C21 y 017-C22) |

## Docs referenciados

- `architecture.md` §2 (premisa 5), §6.5 (reserva del techo con una instantánea por turno), §7.2 (revisor visual: entradas, tools, modelo), §7.4 (tools y lista blanca), §7.5 (hook de policy: origen de la vista), §7.6 (desenlaces, infraestructura no es intento), §9.1 (motivos), §9.4 (etapa 3 del gate y atribución de fallos), §11.2 (fila `revision-visual` y «la revisión visual es programática aunque navegue un modelo»), §12.3 (lista blanca y origen `STORY_MAKER_BASE_URL`), §12.6 (salida de Playwright MCP en el directorio de datos), §13.1 y §13.3 (spans y scores), §14.1 y §14.2 (`VistaDeVersion`, portada, índice, ficha, token de vista), §15.1 (Playwright MCP 0.0.82 en Edge), §15.6 (`validator_results`, `role_sessions`).
- `definitions.md` §3 (`Portada`, `FichaDePersonajes` y «aparece»), §5 (`Rol`, `SesionDeRol` y sus desenlaces, `Ejecucion`, motivos, `Intento` y `Evaluable`), §6 (`Validador`, `ResultadoDeValidador`, `Defecto` atribuible, `GateDePublicacion`, `Score` por parte, `InformeDeEjecucion`), §7 (`MotorDePoliticas`, `DecisionDePolitica`), §10 (`VistaDeVersion`, token de vista), §11.1 (`roles.<rol>.*`, `token_ceiling`), §11.3 (`STORY_MAKER_BASE_URL`, `STORY_MAKER_DATA_DIR`), §12.2 (rol `visual_reviewer` y sus tools), §12.3 (etiquetas y scores `revision-visual/<parte>`).
- `verification.md` §2 (clases), §3.3 (dobles), §4.1 (doble nulo), §5 (filas 2.2, 2.3, 2.4, 5a.6; 5.0 y 6.4 para el score con su nombre), §6 U3, §9.3 (log del browser MCP; hallazgo H4 del enlace roto).
- `project-constraints.md` §5a, «validación visual via browser MCP».

## Autorrevisión

| Pregunta | Resolución | Fuente |
|---|---|---|
| ¿Qué posee la 017 y qué el gate? | El validador y su sesión; el orden de etapas, los ciclos y el re-registro, 012 | `backend/AGENTS.md` (propiedad), §9.4 |
| ¿Quién clasifica datos y render? | El código, desde la estructura esperada: entidad sin capítulo en SQLite = datos; discrepancia con lo observado = render | §11.2, §9.4, `definitions.md` `FichaDePersonajes` |
| ¿Qué recibe el revisor como «estructura esperada»? | La forma y las cantidades, sin los valores que se comparan | §7.2, §11.2 («el modelo navega, no juzga»); **decisión para §18** |
| ¿Se abre el revisor si ya hay un fallo de datos? | No: la comprobación de datos es código y va antes, como el orden económico del gate | §9.4; **decisión para §18** |
| ¿Entidad sin capítulo que ningún capítulo nombra? | Defecto sin capítulo → no atribuible → `unattributable_defect` | `definitions.md` `Defecto`, §9.4; **decisión para §18** |
| ¿Cómo se compara? | Espacios colapsados, sin distinguir mayúsculas; capítulo = título + primera frase contenida en su texto; enlaces por destino | §11.2; **decisión para §18** |
| ¿Sesión sin entrega? | Intento fallido del ciclo del gate | §7.6, `definitions.md` `Evaluable`; **decisión para §18** |
| ¿Navegador no disponible? | Infraestructura: `interrupted`, `provider_error` | §7.6, `definitions.md` motivos; **decisión para §18** |
| ¿Cabe seguir cada enlace en el techo? | Por medir: una instantánea es la novela entera (unos 22k tokens, §6.2) | **Hueco del doc**: 017-C20 lo mide antes del prompt |
| ¿Y la página de novedades y las marcas «cambiado en vN»? | Fuera: `pdf-enlaces` y el render de 013 | §11.2 (cuatro partes), `verification.md` §5 fila 2.10 |
