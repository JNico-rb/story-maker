# 003 — Puerto de agente

> Carril: A · Depende de: 001-base · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Que todo lo que llama a un modelo pase por una sola vía, el **puerto de agente** (`definitions.md` §5, componentes de código), y que esa vía aplique lo que es común a los siete roles: abrir cada `SesionDeRol` aislada en el `WorkspaceDelHarness`, con la lista blanca de su rol y sin tools integradas; publicar cada tool con su schema y recoger sus entregas sin persistirlas; pasar toda llamada a tool por el hook de policy y cada `submit_chapter` por el hook de validación de capítulo; reservar en el `TechoDeTokens` antes de abrir; terminar la sesión por `max_turns` y `session_timeout_seconds`; y guardar y trazar el uso y el coste de cada sesión.

El puerto tiene dos adaptadores con el mismo comportamiento observable: el Claude Agent SDK con el proveedor de `LLM_PROVIDER`, y un **doble falso determinista** con el que corren todas las pruebas T del backend (`architecture.md` §15.9, regla 5). Es el contrato que usan, con sus roles, 008 (entrevistador, extractor), 010 (planner), 011 (writer, editor), 012 (juez), 014 (planner en modo `change`) y 017 (revisor visual). Cierra además el primer punto de `architecture.md` §17.2: que el SDK con `LLM_PROVIDER=claude_login` usa el login de la máquina con tools en proceso, hooks, skill y workspace, y devuelve el uso por sesión.

## Alcance

- **El puerto y sus dos adaptadores**: el del SDK, en los dos modos de `LLM_PROVIDER` (`claude_login` por defecto, `anthropic_compatible`), y el doble falso, que sigue un guion por sesión.
- **Perfil de cada rol**: su lista blanca por rol y modo (`definitions.md` §12.2), su modelo, `max_turns` y `max_output_tokens` (`operation.roles.<rol>`, de la config de 001-base).
- **Configuración de la sesión**: workspace, `CLAUDE.md` de producto, exclusiones, servidores MCP, permisos, entorno del proveedor (`architecture.md` §7.3, §7.4, §12.3, §12.6, §15.2; `verification.md` §4.7).
- **Tools con schema**: publicación del JSON Schema derivado del modelo de cada tool, validación de la entrada, error al modelo, entrega en memoria y score `schema-salida` (`architecture.md` §7.4, §11.2).
- **Los tres hooks como mecanismo** (`architecture.md` §7.5): el de policy consulta al `MotorDePoliticas` y aplica su decisión; el de validación de capítulo ejecuta las comprobaciones que le da quien abre la sesión del writer y, si bloquean, sustituye lo que lee el modelo; el de observabilidad cierra los spans de las tools sin manejador propio.
- **`TechoDeTokens`**: reserva, estimador chars/4, espera en orden de llegada, espera acotada de la API, reserva imposible y liberación (`architecture.md` §6.5).
- **Límites y desenlace** de la sesión (`architecture.md` §7.6; `definitions.md` §5, `SesionDeRol`).
- **Uso, coste y registro**: la `SesionDeRol` en SQLite, el span `rol:<etiqueta>`, su `LlamadaDeModelo` y los spans `tool:<tool>`, por el puerto de observabilidad de 001-base (`architecture.md` §13.1, §13.2).
- **Sonda real** con `claude_login` (D), agrupada al final: remide los hechos H6–H9 de `verification.md` §8 con el login y cierra el punto de §17.2.

## Fuera de alcance

- Las reglas del `MotorDePoliticas` (lista blanca, `palabras-prohibidas`, skill admitida, origen de navegación del revisor visual) y el audit log → 005-guardarrailes. Aquí el motor es siempre un doble.
- Las comprobaciones del hook de validación de capítulo (`longitud-capitulo`, `nombres-exactos`) y su registro con la entrega → 011-produccion-de-capitulos.
- El schema, el manejador y los campos narrativos de cada tool propia: `update_brief` y `submit_facts` → 008-brief-y-entrevista; `submit_plan` → 010-planificacion; `submit_chapter` y `submit_review` → 011; `submit_evaluation` → 012-gate-de-publicacion; `propose_change` → 014-cambios-del-lector; `submit_visual_review` → 017-revision-visual. Cada una usa el mecanismo de esta spec.
- Contar intentos, aplicar `max_retries.*` y el veredicto → 010, 011, 012, 014. Decidir qué hace cada desenlace o rechazo con la ejecución o con la respuesta HTTP (`interrupted` con `provider_error`, `failed` con `infeasible_config`, 422, 503) → quien abre la sesión: 008, 011, 012, 014, 017.
- Ensamblar la `VentanaDeContexto` y las entradas de la llamada → 011 y 016-recuperacion-hibrida para writer y editor; cada spec de rol para las suyas.
- El contenido del `WorkspaceDelHarness` (el `CLAUDE.md` de producto, la skill `personalizacion-natural` y los prompts) → 011 y las specs de cada rol (`backend/AGENTS.md`). Esta spec solo lo usa como directorio de trabajo.
- De dónde sale el prompt de cada rol y su versión (`PromptVersionado`), la máscara, el adaptador de Langfuse y `auth_check()` → 004-observabilidad. La traza de cada ejecución, entrevista, importación o propuesta, y el span `capitulo-<n>` → quien abre la sesión (004, 008, 011, 014).
- Validar la config (`token_ceiling` ≤ 100.000, un bloque por rol, un precio por modelo usado) y los ajustes, el esquema de `role_sessions` y el puerto de observabilidad con su doble nulo → 001-base.
- Copiar `schema-salida` a `validator_results` dentro de una ejecución → quien abre la sesión, con lo que el puerto le devuelve.
- Demostrar `anthropic_compatible` con un modelo real: es el camino de producción, fuera de alcance (`architecture.md` §15.2). Aquí solo se prueba en T el entorno que construye.

## Contrato del puerto

Lo que ve quien abre una sesión, en términos de comportamiento:

- **Petición de sesión:** rol y modo; cliente y novela; ejecución y capítulo, si los hay; el prompt del rol con su versión; el mensaje de la llamada (la `VentanaDeContexto` y las entradas, ya ensambladas); las tools propias del rol, cada una con su schema y sus campos de texto narrativo marcados; en el writer, las comprobaciones del hook de validación de capítulo; y el contexto de traza en que se abre. Una sesión **sin ejecución** es una sesión de la API (entrevista, extracción, propuesta de un cambio); una con ejecución es de la ejecución.
- **Tools propias** de un rol: las de su lista blanca que no son `Skill` ni del browser MCP.
- **Al abrir**, o la sesión corre y se cierra, o se rechaza antes de abrirse, sin `SesionDeRol`: *tools que no cuadran* con la lista blanca, *no cabe nunca* (la reserva supera el techo) o *sin sitio a tiempo* (solo en la API, tras `api_wait_seconds`).
- **Mientras corre**, quien la abrió ve cada llamada a tool en cuanto se resuelve y puede cortar la sesión.
- **Al cerrarse**, devuelve el desenlace (`completed`, `turns_exhausted`, `time_exhausted`, `cut`, `infrastructure_failure`); las llamadas a tools en orden, cada una con su tool, su entrada y cómo quedó: aceptada (con los defectos no bloqueantes, si los hubo), rechazada por schema (con los errores), denegada (con el motivo de la política) o bloqueada (con los defectos del hook de validación); la respuesta final del modelo en texto; el modelo, el uso, el coste, la latencia y la reserva. Una **entrega** es una llamada a una tool propia; la última aceptada es la que el rol entrega.
- El puerto no juzga ni persiste ninguna entrega: qué hacer con ellas lo decide quien abrió la sesión.

## Comportamiento observable

En los casos T, lo observable de la configuración es la que el puerto construye para el SDK (`verification.md` §4.7); que el SDK la respeta lo demuestran 003-C30 a 003-C32. Las tools de las pruebas son tools de prueba con el nombre de una tool de la lista blanca; el `MotorDePoliticas` es un doble; la observabilidad, el doble nulo de 001-base; las claves, marcadores de prueba (`TU_CLAVE_AQUI`).

### Perfil y configuración de la sesión

#### 003-C01 — Cada rol abre con su lista blanca y nada más (T)
- **Entrada:** una petición de sesión por cada rol y modo de `definitions.md` §12.2, con sus tools propias.
- **Salida:** la sesión expone exactamente estas tools. Entrevistador: `update_brief`. Extractor: `submit_facts`. Planner en modo `plan`: `submit_plan`; en modo `change`: solo `propose_change`. Writer, en `write`, `rewrite` y `revise`: `submit_chapter` y `Skill`. Editor: `submit_review` y `Skill`. Juez: `submit_evaluation`. Revisor visual: `submit_visual_review`, `browser_navigate`, `browser_snapshot` y `browser_click`. Ninguna tool integrada del CLI (ficheros, órdenes, web, subagentes) en ningún rol. Modelo = `operation.roles.<rol>.model`; turnos = `operation.roles.<rol>.max_turns`.

#### 003-C02 — Unas tools que no cuadran con la lista blanca impiden abrir (T)
- **Entrada:** una sesión del editor que declara también `submit_chapter`; una del planner en modo `change` que declara también `submit_plan`; una del writer sin `submit_chapter`.
- **Salida:** las tres se rechazan antes de abrirse, con un error que nombra el rol, el modo y la tool sobrante o la que falta. No reservan en el techo, no lanzan nada y no dejan `SesionDeRol`.

#### 003-C03 — La sesión corre aislada en el workspace (T)
- **Entrada:** la configuración de cualquier rol, con un workspace de prueba que tiene su `CLAUDE.md` y cuelga de dos directorios padre que tienen el suyo, más un `CLAUDE.md` personal del usuario.
- **Salida:**
  - directorio de trabajo = el workspace; se cargan los ajustes del proyecto y ninguno del usuario de la máquina;
  - quedan excluidos todos los `CLAUDE.md` que no son el del workspace (los dos de los padres y el personal); el del workspace no se excluye;
  - ninguna configuración MCP de la raíz entra: solo los servidores que declara la sesión, el de sus tools propias y, en el revisor visual, el browser MCP;
  - los permisos deniegan lo no preaprobado sin pedir confirmación;
  - la sesión empieza sin conversación previa: nunca reanuda ni continúa otra;
  - telemetría no esencial y memoria automática del CLI desactivadas (`CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`).

#### 003-C04 — Solo el revisor visual declara el browser MCP (T)
- **Entrada:** la configuración del revisor visual y la de los otros seis roles.
- **Salida:** el revisor visual declara un único servidor MCP externo, el browser MCP del stack en su versión fijada (`architecture.md` §15.1), sobre el Edge instalado y con su salida dentro de `STORY_MAKER_DATA_DIR`; de sus tools solo están permitidas las tres de navegación. Ningún otro rol declara servidores MCP externos.

#### 003-C05 — Con `claude_login`, la sesión usa el login de la máquina y ninguna clave (T)
- **Entrada:** `LLM_PROVIDER=claude_login` y tres situaciones: (a) sin `CLAUDE_CODE_OAUTH_TOKEN`; (b) con él en los ajustes; (c) el entorno del servidor trae `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` y `ANTHROPIC_BASE_URL` con marcadores de prueba, y los ajustes traen `OPENROUTER_API_KEY`.
- **Salida:** en las tres, el entorno de la sesión no redefine `CLAUDE_CONFIG_DIR` y lleva las dos variables de desactivación de 003-C03. (a) Ninguna credencial. (b) Solo `CLAUDE_CODE_OAUTH_TOKEN`. (c) Ninguna de las tres `ANTHROPIC_*` llega con valor a la sesión y la clave de OpenRouter no se traduce.

#### 003-C06 — Con `anthropic_compatible`, la sesión lleva solo las variables de su endpoint (T)
- **Entrada y salida:** según los ajustes (marcadores de prueba):

| Ajustes | Entorno de la sesión |
|---|---|
| `ANTHROPIC_BASE_URL` y `ANTHROPIC_AUTH_TOKEN` | Esos dos; `ANTHROPIC_API_KEY` vacía |
| Solo `OPENROUTER_API_KEY` | `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN` = esa clave, `ANTHROPIC_API_KEY` vacía |
| `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN` y `OPENROUTER_API_KEY` | Los dos primeros; la clave de OpenRouter no se usa |
| Ni `ANTHROPIC_AUTH_TOKEN` ni `OPENROUTER_API_KEY`, o `ANTHROPIC_AUTH_TOKEN` sin `ANTHROPIC_BASE_URL` | Construir el adaptador del SDK falla con un error accionable que nombra las variables que faltan; no se abre ninguna sesión |

- En todas las filas con sesión: las dos variables de desactivación, `CLAUDE_CONFIG_DIR` sin redefinir y ningún `CLAUDE_CODE_OAUTH_TOKEN`.

### Tools con schema

#### 003-C07 — El schema que recibe la sesión es el derivado del modelo de la tool (T)
- **Entrada:** una tool de prueba con campos obligatorios y opcionales, un enumerado y una lista con longitud acotada.
- **Salida:** el JSON Schema que la sesión publica al modelo es igual al que se deriva de su modelo de datos: mismos campos, obligatorios, valores del enumerado y cotas.

#### 003-C08 — Una entrada inválida vuelve al modelo como error y se corrige en la misma sesión (T)
- **Entrada:** con el doble, un guion que llama a la tool sin un campo obligatorio y con otro fuera de su enumerado, y después la llama con una entrada válida.
- **Salida:** en la primera llamada, el modelo lee un error que nombra los dos campos; las llamadas quedan como [rechazada por schema, con los dos errores; aceptada]; `schema-salida` vale 0 en el span de la primera y 1 en el de la segunda; todo ocurre en una sola sesión, con una sola `SesionDeRol`.

#### 003-C09 — Las entregas quedan en memoria, en orden, y nada se persiste (T)
- **Entrada:** un guion del entrevistador que llama tres veces a `update_brief` con entradas válidas y termina con un texto.
- **Salida:** las tres entregas aceptadas, en su orden y con su entrada validada, y el texto final como respuesta; tras cada entrega, el modelo lee un acuse de recibo. La base de datos no cambia salvo por la `SesionDeRol` y lo que registre la política.

#### 003-C10 — Una sesión que termina sin entregar no es un error del puerto (T)
- **Entrada:** un guion que solo responde con texto.
- **Salida:** desenlace `completed`, ninguna llamada a tool y la respuesta en texto; quien abrió la sesión decide qué significa.

### Hook de policy

#### 003-C11 — Toda llamada a tool pasa antes por la política, y su decisión se aplica (T)
- **Entrada:** un guion del writer con cinco llamadas: `Skill` con `personalizacion-natural` (el doble de la política permite); `Skill` con otra skill (deniega con el motivo «skill no admitida»); `submit_chapter` válida (marca, `flag`); `submit_chapter` válida (deniega con el motivo «término prohibido»); y `Bash`, que no está en la lista (deniega).
- **Salida:**
  - la política recibe cinco peticiones, cada una antes de que corra su tool, con origen `policy_hook`, cliente, novela, ejecución, rol, tool y los campos de la llamada;
  - lo permitido y lo marcado corren: la skill carga y la primera `submit_chapter` queda aceptada;
  - lo denegado no corre (su manejador no se ejecuta) y el modelo lee el motivo tal como lo dio la política; las tres quedan denegadas con su motivo.

#### 003-C12 — La política recibe como narrativos solo los campos que la tool marca (T)
- **Entrada:** una tool de prueba con un texto narrativo en la raíz (como la dedicatoria), textos narrativos anidados en una lista (como los beats de cada capítulo del outline) y un campo que es una lista de prohibidas, sin marcar; además, una llamada a `Skill` y una a `browser_navigate`.
- **Salida:** la petición a la política lleva cada texto narrativo con su ruta dentro de la entrada, y solo esos van marcados como narrativos; la lista de prohibidas llega sin marca. En `Skill` llega el nombre de la skill y en `browser_navigate` la URL de destino, ninguno como narrativo.

#### 003-C13 — Si la política falla, la tool no corre (T)
- **Entrada:** el doble de la política lanza un error al decidir sobre una `submit_chapter`.
- **Salida:** el manejador no se ejecuta; la sesión se corta (desenlace `cut`) y el error llega a quien la abrió; la reserva se libera y la `SesionDeRol` se guarda.

### Hook de validación de capítulo

#### 003-C14 — Con defectos bloqueantes, el modelo lee los defectos en lugar del acuse (T)
- **Entrada:** una sesión del writer cuyas comprobaciones de prueba dan un defecto bloqueante en la primera entrega y ninguno en la segunda; un guion con dos `submit_chapter` válidas por schema.
- **Salida:** tras la primera, el modelo lee la lista de defectos en lugar del acuse de recibo, y la llamada queda bloqueada con esos defectos; la segunda queda aceptada. Las dos, en la misma sesión.

#### 003-C15 — Las comprobaciones corren solo sobre entregas permitidas y válidas, y lo no bloqueante no bloquea (T)
- **Entrada:** tres `submit_chapter`: una que la política deniega, una rechazada por schema y una válida cuyas comprobaciones dan solo defectos no bloqueantes.
- **Salida:** las comprobaciones corren una sola vez, sobre la tercera; la tercera queda aceptada con sus defectos no bloqueantes y el modelo lee el acuse de recibo.

### Techo de tokens

Con un `token_ceiling` de prueba, menor que 100.000 (`architecture.md` §1.3).

#### 003-C16 — La reserva es la entrada estimada más el crecimiento de los turnos (T)
- **Entrada:** una sesión del entrevistador con `max_turns` 4 y `max_output_tokens` 2.000, cuyos textos enviados por el código (prompt, `CLAUDE.md` del workspace, schemas de sus tools y mensaje) suman 12.001 caracteres; la misma con `max_turns` 1; y una del writer.
- **Salida:** entrada estimada = ⌈12.001 / 4⌉ = 3.001 tokens; reserva = 3.001 + 3 × 2.000 = 9.001. Con `max_turns` 1, la reserva es la entrada estimada, 3.001. En el writer, los caracteres de la skill cuentan en la entrada. La reserva queda registrada con la `SesionDeRol`.

#### 003-C17 — Se abre hasta llenar el techo exacto; si no cabe, se espera en orden de llegada (T)
- **Entrada:** techo 10.000. La sesión A reserva 6.000 y sigue abierta. Llegan, en este orden, B (de una ejecución, 5.000) y C (de la API, 1.000). Aparte, con el techo libre, una sesión que reserva 10.000 justos.
- **Salida:** A abre; B espera; C espera detrás de B aunque cabría. Al cerrar A abren B y luego C (5.000 + 1.000 ≤ 10.000). La de 10.000 justos abre.

#### 003-C18 — La API espera como mucho `api_wait_seconds`; la ejecución, sin límite propio (T)
- **Entrada:** el techo lleno por una sesión que no cierra; llega una sesión de la API y, detrás, una de una ejecución.
- **Salida:** la de la API se rechaza como *sin sitio a tiempo* al vencer `api_wait_seconds`, no antes: sin sesión, sin reserva y sin `SesionDeRol`, y deja de bloquear a la que tenía detrás. La de la ejecución sigue esperando pasado ese tiempo y abre en cuanto se libera sitio.

#### 003-C19 — Una reserva mayor que el techo no espera (T)
- **Entrada:** techo 10.000, libre; una sesión de la API y otra de una ejecución que reservan 10.001 cada una.
- **Salida:** las dos se rechazan en el acto como *no cabe nunca*: sin espera, sin sesión y sin `SesionDeRol`.

#### 003-C20 — La reserva se libera siempre al cerrar (T)
- **Entrada:** una sesión por cada desenlace (`completed`, `turns_exhausted`, `time_exhausted`, `cut`, `infrastructure_failure`) y la de 003-C13, cada una con otra esperando detrás.
- **Salida:** tras cada cierre, el techo recupera exactamente lo reservado y la que esperaba abre.

### Límites y desenlace

#### 003-C21 — Agotar los turnos conserva el uso (T)
- **Entrada:** un guion que pide más turnos que `max_turns` y trae el uso de la sesión en su resultado final.
- **Salida:** desenlace `turns_exhausted`; el uso y el coste de la sesión son los del resultado final, no cero; las llamadas hechas antes se devuelven.

#### 003-C22 — Pasar de `session_timeout_seconds` interrumpe y desconecta (T)
- **Entrada:** un guion que no termina, con un `session_timeout_seconds` de prueba; y otra sesión de una ejecución que espera en el techo más que ese tiempo y, ya abierta, termina enseguida.
- **Salida:** la primera se interrumpe y se desconecta al vencer el tiempo: desenlace `time_exhausted`, con el uso del resultado final si llegó y vacío si no. La segunda termina `completed`: la espera en el techo no cuenta en el tiempo de la sesión ni en su latencia.

#### 003-C23 — Un fallo del proveedor es `infrastructure_failure`, no `completed` (T)
- **Entrada:** un guion en que el transporte falla a mitad de sesión; otro en que el proveedor cierra la sesión con un resultado de error, como el del límite de uso de la suscripción.
- **Salida:** desenlace `infrastructure_failure` en los dos; el puerto no reintenta por su cuenta (los reintentos son los del propio SDK); si llegó resultado final se guarda su uso; si no, el uso queda vacío, no a cero.

#### 003-C24 — Quien abre la sesión puede cortarla (T)
- **Entrada:** quien abre la sesión del writer observa cada llamada y corta tras la segunda entrega bloqueada.
- **Salida:** la sesión se interrumpe y se desconecta; desenlace `cut`; no corre ninguna tool más; se devuelven las llamadas hasta el corte.

### Uso, coste y registro

#### 003-C25 — El coste es el uso real por el precio de lista del modelo (T)
- **Entrada:** una sesión del writer con `claude-sonnet-5` y `operation.pricing` de 2,00 / 10,00 / 0,20 / 2,50 USD por millón (entrada, salida, lectura y escritura de caché); uso final de 10.000 / 3.000 / 50.000 / 8.000 tokens; el SDK declara un coste propio distinto.
- **Salida:** coste = (10.000 × 2,00 + 3.000 × 10,00 + 50.000 × 0,20 + 8.000 × 2,50) / 1.000.000 = 0,08 USD. El coste que declara el SDK no es el de la sesión: solo va, como contraste, en su `LlamadaDeModelo`.

#### 003-C26 — Toda sesión abierta deja su `SesionDeRol`, y solo ellas (T)
- **Entrada:** una sesión por desenlace; una sesión del entrevistador cuya entrega descarta después quien la abrió (un turno que no se guarda, `architecture.md` §3.5); y los rechazos de 003-C02, 003-C18 y 003-C19.
- **Salida:** una `SesionDeRol` por sesión abierta, guardada al cerrarse aunque quien la abrió no guarde nada: rol, novela, ejecución (vacía en la API), capítulo (si lo hay), modelo, versión de prompt, tokens de entrada, de salida, de lectura y de escritura de caché, coste, latencia, desenlace, reserva y traza. Ninguna por los rechazos.

#### 003-C27 — Cada sesión y cada llamada a tool dejan su span (T)
- **Entrada:** una sesión del writer del capítulo 4, abierta dentro del span que le pasa quien la abre, con cinco llamadas: `Skill` permitida, `submit_chapter` denegada, rechazada por schema, bloqueada y aceptada.
- **Salida:**
  - un span `rol:writer` con el capítulo 4, hijo del span recibido, y dentro una `LlamadaDeModelo` con modelo, latencia, versión de prompt, uso y coste (y el coste del SDK como contraste);
  - `tool:Skill`, abierto por el hook de policy y cerrado por el de observabilidad;
  - cuatro `tool:submit_chapter`: la denegada con nivel WARNING y el motivo; la rechazada por schema con WARNING y `schema-salida` = 0; la bloqueada con WARNING y los defectos; la aceptada con `schema-salida` = 1;
  - los spans de rol llevan la etiqueta de `definitions.md` §12.2 (`rol:entrevistador`, `rol:juez`, `rol:revisor-visual`…); al cerrarse la sesión no queda ningún span abierto.

### Doble falso

#### 003-C28 — El doble recorre el camino del SDK y es determinista (T)
- **Entrada:** el mismo guion de sesión ejecutado dos veces; sin red, sin CLI y sin `.env`.
- **Salida:** las dos pasadas dan las mismas llamadas, desenlace, uso, coste, spans y `SesionDeRol` (salvo ids y tiempos). En las dos, la sesión pasa por la reserva, el hook de policy, el schema, el hook de validación de capítulo, el registro y los spans igual que con el adaptador del SDK. El guion puede responder texto, llamar a una tool con una entrada, pedir más turnos, no terminar o fallar como el proveedor, con un uso dado.

#### 003-C29 — Una sesión sin guion hace fallar la prueba (T)
- **Entrada:** se abre una sesión de un rol y modo para el que la prueba no dio guion.
- **Salida:** error que nombra el rol y el modo, antes de reservar ni abrir nada.

### Sonda real con el login de Claude Code (D)

Una sola tanda, al final de la spec: en la máquina con `claude` con sesión iniciada, `LLM_PROVIDER=claude_login` y `claude-haiku-4-5`. Workspace de sonda temporal dentro del directorio de datos por defecto, que está bajo la raíz del repositorio (así los `CLAUDE.md` de desarrollo son sus padres) y lo ignora git (000-C01); lleva un `CLAUDE.md` con una frase marcador, una skill `personalizacion-natural` de sonda y otra skill de sonda. Rol editor con una `submit_review` de sonda; política doble que deniega toda skill que no sea `personalizacion-natural`; observabilidad con el doble nulo. Se borra al terminar. Los resultados van a `verification.md` §8 (H6–H9 remedidos con el login) y §4.7, y el primer punto de `architecture.md` §17.2 se cierra o se reabre con su motivo.

#### 003-C30 — El login funciona con tools en proceso, hooks y skill (D)
- **Entrada:** además, `ANTHROPIC_API_KEY` con un marcador inválido en el entorno del servidor. Se pide a la sesión cargar la skill de sonda, cargar la otra skill, entregar con un campo inválido y entregar después.
- **Salida:** la sesión corre con el login, sin error de autenticación pese a la clave heredada; `personalizacion-natural` carga y la otra se deniega con su motivo; el error de schema llega al modelo, que corrige en la misma sesión; desenlace `completed` con una entrega aceptada; el uso del resultado final es mayor que cero y el coste sale de `operation.pricing`. Se anotan el uso por turno (si llega o es cero) y el coste declarado por el SDK frente al propio.

#### 003-C31 — La sesión real no hereda nada del entorno de desarrollo (D)
- **Entrada:** la sesión de 003-C30 y una sesión del writer con una `submit_chapter` de sonda cuyas comprobaciones bloquean la primera entrega; se le pide también usar `Bash` y leer un fichero.
- **Salida:** al empezar, la sesión declara como tools solo las de su lista blanca (ninguna integrada, ningún servidor del `.mcp.json` de la raíz) y el login como origen de la credencial; `Bash` y la lectura no ejecutan nada ni esperan confirmación; el modelo lee los defectos del hook de validación y vuelve a entregar; preguntado por sus instrucciones, cita la frase marcador y nada de los `CLAUDE.md` de los padres ni del personal; los ajustes y hooks de desarrollo de la raíz no actúan; la memoria automática del CLI no guarda nada nuevo; `CLAUDE_CONFIG_DIR` no cambia. Se anota si el CLI deja la transcripción de la sesión en su directorio de configuración.

#### 003-C32 — Los límites reales terminan la sesión sin dejar subprocesos (D)
- **Entrada:** una sesión con `max_turns` 1 y una tarea que necesita más turnos; otra con un `session_timeout_seconds` de pocos segundos y una tarea larga.
- **Salida:** la primera termina `turns_exhausted` con el uso conservado; la segunda, `time_exhausted`, anotando si llegó uso; tras cerrar cada una no queda vivo ningún subproceso del CLI de esa sesión.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 003-I1 | La suma de las reservas abiertas nunca supera `token_ceiling`, con cualquier secuencia de reservas, esperas, vencimientos y liberaciones | T | Propiedad sobre el contador con secuencias generadas (`verification.md` §4.3) |
| 003-I2 | Toda reserva se libera exactamente una vez, sea cual sea el desenlace | T | 003-C20 y la propiedad de 003-I1 |
| 003-I3 | Ninguna tool corre sin una decisión `allow` o `flag` de la política, tomada antes de que corra | T | 003-C11, 003-C13 |
| 003-I4 | Las tools entregan, no persisten: una sesión solo escribe su `SesionDeRol` (y lo que registre la política) | T | Huella de la base de datos antes y después de las sesiones de 003-C09 y 003-C11 |
| 003-I5 | El coste de una `SesionDeRol` es su uso × `operation.pricing` de su modelo, nunca el que declara el SDK | T | 003-C25 |
| 003-I6 | Ninguna prueba T llega a un modelo: en la suite, el adaptador del SDK no puede abrir sesiones y falla sin lanzar el CLI | T | Una prueba que intenta abrirlo en la suite y comprueba que falla sin subproceso |
| 003-I7 | Solo el puerto de agente usa el Agent SDK: ningún otro módulo del backend lo importa | T | Prueba que recorre el código del backend, como la regla de dependencias de 000-C05 |
| 003-I8 | Sesiones concurrentes no comparten estado: llamadas, entregas, comprobaciones y peticiones a la política de una no aparecen en otra | T | Dos sesiones intercaladas con el doble |
| 003-I9 | El doble falso es determinista: el mismo guion da el mismo resultado | T | 003-C28 |
| 003-I10 | Ninguna sesión deja vivo su subproceso del CLI tras cerrarse | D | 003-C32 |
| 003-I11 | Las sesiones reales respetan la configuración de 003-C01 a 003-C05 | D | 003-C30, 003-C31 |

## Scores y trazas

- `schema-salida`: 0/1 en el span `tool:<tool>` de cada llamada a una tool propia (003-C08, 003-C27). Su copia a `validator_results` es de quien abre la sesión.
- Spans `rol:<etiqueta>` (con capítulo, si lo hay), una `LlamadaDeModelo` por sesión y `tool:<tool>` por llamada, también las denegadas (003-C27). La traza, la sesión de Langfuse y `capitulo-<n>` los abre quien abre la sesión.
- Ningún otro score sale de esta spec.

## Docs referenciados

- `architecture.md` §1.3 (techos menores en pruebas), §1.4 (un proceso), §3.5 (una sesión por turno HTTP; la `SesionDeRol` se guarda siempre que se abrió), §6.5 (techo de tokens), §7.2 (roles), §7.3 (workspace, `CLAUDE.md`, exclusiones), §7.4 (tools con schema, sin tools integradas), §7.5 (hooks), §7.6 (límites; errores del proveedor), §7.7 (writer y editor separados), §11.2 (`schema-salida`), §12.2–§12.3 (motor de políticas, lista blanca aplicada dos veces), §12.6 (directorio de datos, `CLAUDE_CONFIG_DIR`, variables del CLI), §13.1–§13.2 (spans, uso y coste), §15.1 (stack), §15.2 (proveedor y hechos medidos del SDK), §15.4 (config), §15.5 (ajustes), §15.9 (módulo `agents`, regla 5, contrato con doble en la 003), §17.2 (primer punto), §18 (decisiones cerradas por esta spec: propiedad de los schemas de tool, campos que escanea la policy, coste del SDK como contraste, uso vacío sin resultado final, `ANTHROPIC_API_KEY` vacía en `anthropic_compatible`, `ANTHROPIC_*` heredadas limpiadas en `claude_login`, fallo del motor de políticas).
- `definitions.md` §4 (`TechoDeTokens`, `VentanaDeContexto`), §5 (`Rol`, `SesionDeRol`, `WorkspaceDelHarness`, `Tool`, `Hook`, `Skill`, `Intento`, componentes de código), §6 (`Validador`, `Defecto`, `Score`), §7 (`MotorDePoliticas`, `DecisionDePolitica`), §8 (`Span`, `LlamadaDeModelo`, `PromptVersionado`), §11.1 y §11.3 (config, ajustes y modos de `LLM_PROVIDER`), §12.1–§12.4 (identificadores, roles y tools, etiquetas, enumerados).
- `verification.md` §2 (clases), §3.3 (dobles; ninguna prueba T llama a un modelo), §3.5 (contrato de las tools), §4.1 (sonda del uso por turno), §4.3 (techo y límites), §4.7 (aislamiento de las sesiones de rol, T y D), §4.9 (RT12, RT15, RT19), §5 (filas 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 5a.1, 6.2, 7.8), §6 (U22, U23, U26, U27), §8 (H6–H9).
- `backend/AGENTS.md` (propiedad de `agents/`, dobles obligatorios, demostraciones D agrupadas).
- Specs: 001-base (config, ajustes, esquema de `role_sessions`, puerto de observabilidad con doble nulo); 005-guardarrailes (reglas del motor y audit log); 004-observabilidad (prompts versionados, máscara, adaptador de Langfuse); 008, 010, 011, 012, 014 y 017 (tools de cada rol y qué hacen con cada desenlace).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué posee la 003? | El puerto con sus dos adaptadores, el perfil y la configuración de cada rol, el mecanismo de tools y hooks, el techo, los límites de sesión, el registro de la `SesionDeRol` y sus spans | `architecture.md` §15.9; `backend/AGENTS.md` |
| ¿Son de la 003 los schemas de las tools de cada rol? | No: su contenido es del dominio de cada rol y su spec lo declara con este mecanismo. La 003 exige que cuadren con la lista blanca | Tabla de propiedad de `backend/AGENTS.md`; `architecture.md` §18 (spec 003) |
| ¿Quién decide lista blanca, prohibidas, skill y origen de navegación? | El `MotorDePoliticas` (005); el hook pregunta y aplica | `architecture.md` §7.5, §12.2 |
| ¿Qué campos escanea la política? | Los que cada tool marca como narrativos, con su ruta; nunca listas de prohibidas ni léxico a evitar | `architecture.md` §7.5; `architecture.md` §18 (spec 003) |
| ¿Dónde vive la tabla de la lista blanca, que usan el puerto y el motor? | Es la de `definitions.md` §12.2; su ubicación en código la fija el integrador, porque `policy` no importa `agents` | `architecture.md` §15.9, regla 4; **pregunta al integrador** |
| ¿Hook de validación genérico? | No: solo en `submit_chapter` del writer, con las comprobaciones que da 011 | `architecture.md` §7.5 |
| ¿Cuenta intentos el puerto? | No: informa de cada llamada en cuanto se resuelve y deja cortar | `architecture.md` §7.6, `definitions.md` §5 (`Intento`) |
| ¿Quién guarda la `SesionDeRol`? | El puerto, al cerrar, siempre que se abrió | `architecture.md` §3.5 |
| ¿Se guarda la reserva? | Sí, con la `SesionDeRol`: la columna `reserved_tokens` de `role_sessions`, que 001-C6 ya declara («la calcula 003, esta spec solo declara la columna») | `architecture.md` §6.5.5; `specs/backend/001-base.md` C6. Sigue sin figurar como atributo de `SesionDeRol` en `definitions.md` §5; no bloquea esta spec, aviso para el integrador |
| ¿Dónde va el coste que declara el SDK? | Solo en la `LlamadaDeModelo`, como contraste | `architecture.md` §13.2; `architecture.md` §18 (spec 003) |
| ¿Uso de una sesión sin resultado final? | Vacío, no cero: cero ocultaría un consumo real | Premisa 5 (`architecture.md` §2); `architecture.md` §18 (spec 003) |
| ¿Se impone `max_output_tokens` al modelo? | No: es un parámetro de la reserva; truncar una entrega la convertiría en error de schema | `architecture.md` §6.5.1; `verification.md` §6 U22 |
| ¿Y las `ANTHROPIC_*` heredadas con `claude_login`? | No llegan con valor a la sesión: el puerto limpia el entorno del subproceso de cualquier `ANTHROPIC_*` heredada del proceso del servidor; una clave suelta cobraría créditos de API. No contradice «el backend no toca `ANTHROPIC_*`» de §15.2: ese texto dice que no las usa para autenticar en este modo, no que las reenvíe sin control | `verification.md` §4.7; `architecture.md` §18 (spec 003), que cierra la tensión con §15.2 |
| ¿`ANTHROPIC_API_KEY` en `anthropic_compatible` sin OpenRouter? | Vacía siempre: solo las variables del endpoint | `verification.md` §4.7; `architecture.md` §18 (spec 003) |
| ¿`anthropic_compatible` sin sus variables? | El adaptador no se construye; error accionable | Premisa 5 |
| ¿Espera en orden de llegada estricto? | Sí: una pequeña no adelanta a una grande que llegó antes | `architecture.md` §6.5.3 |
| ¿Cuenta la espera en el tiempo de la sesión? | No: el tiempo y la latencia empiezan al abrir | `architecture.md` §6.5.3 |
| ¿Y si la política falla? | La tool no corre; la sesión se corta con `infrastructure_failure` y el error sube | Cierre a fallo de §7.5; `architecture.md` §18 (spec 003) |
| ¿Cómo se prueba sin modelo? | Con el doble por guion y sobre la configuración que construye el puerto | `verification.md` §3.3, §4.7 |
| ¿Qué workspace usa la sonda? | Uno temporal bajo la raíz del repo; el real lo rellena 011 | `backend/AGENTS.md`; contradice la línea de 000 que asigna el contenido del workspace a 003 |
| ¿Deja el CLI transcripciones con datos del brief? | Unsure; la sonda lo anota; si sí, riesgo para `verification.md` §6 o una opción que lo evite | `architecture.md` §12.6 |
| ¿Cómo señala el CLI el límite de uso de la suscripción? | Unsure; se trata como resultado de error del proveedor; la sonda no puede forzarlo | `architecture.md` §15.2; RT19 |
| ¿Las tools del browser MCP entran en la estimación? | No: el código no conoce su texto | `verification.md` §6 U22 |
| ¿«Solo el puerto importa el SDK» es T o I? | T: una prueba barata que guarda a todos los carriles | `architecture.md` §15.9, regla 5 |
| ¿Pico de tokens concurrentes de las evals? | Fuera de la 003: lo mide 020 con las reservas de `SesionDeRol`; a esa spec le faltará el momento de apertura, que ninguna columna de `role_sessions` guarda hoy — aviso para 020, no bloquea esta spec | `verification.md` §4.2 (b) |
