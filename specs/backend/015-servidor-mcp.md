# 015 — Servidor MCP

> Carril: B · Depende de: 002-autenticacion, 013-lectura-y-pdf, 014-cambios-del-lector · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Exponer las novelas del cliente autenticado como `ServidorMCP` en `/mcp`, dentro de la misma aplicación que `/api`, para que cualquier cliente MCP (MCP Inspector, Claude Code) las consulte, las descargue y pida un cambio del lector en dos pasos con `Confirmacion`. Cubre los dos opcionales del encargo sobre MCP: el servidor de consulta y descarga (schema validado, solo lectura, cada llamada en Langfuse, README para conectarlo, identidad del usuario en sesión) y las tools de escritura con permisos y confirmación. Son las filas O.1–O.7 de `verification.md` §5, la parte MCP de 2.10 y los casos RT7, RT11 y RT13 (en MCP) de §4.9.

## Alcance

- **Transporte HTTP de MCP en la ruta `/mcp`**, en el mismo proceso y la misma aplicación que `/api`, que arranca y se detiene con ella (§14.4, «con su lifespan»).
- **Identidad:** el `TokenDeAcceso` de la cabecera `Authorization` de cada petición, verificado en el mismo punto que la API (002-autenticacion, 002-I5).
- **Las siete tools** de `definitions.md` §12.2. De lectura: `list_novels`, `get_chapter`, `list_versions`, `query_story_bible` y `download_novel`. De escritura: `request_change` y `confirm_change`. Cada una tiene su schema de entrada y de salida, su descripción en español y su anotación de solo lectura o de escritura.
- **Errores:** cada rechazo es un error de tool con el código de estado que daría la API en el mismo caso (§15.7).
- **Registro:** una traza `mcp:<tool>` por llamada a una tool, con la máscara de la novela, y una fila del audit log con origen `mcp_write` por llamada de escritura.
- **El apartado del README** que explica cómo conectarse desde MCP Inspector y desde Claude Code con el token. El README es del integrador: el carril le entrega el texto.

## Fuera de alcance

- Registro, acceso, emisión y verificación del `TokenDeAcceso`, y la regla «lo ajeno responde 404» → 002-autenticacion. Aquí solo se comprueba que `/mcp` los aplica.
- Qué devuelve cada lectura:
  - la lista de novelas con su estado derivado y su versión vigente → 008-brief-y-entrevista (`GET /api/novels`);
  - el historial de versiones, los capítulos cambiados, los capítulos de una versión y su PDF → 013-lectura-y-pdf;
  - la story bible de una versión → 009-story-bible-y-versiones.

  Cada tool de lectura devuelve lo mismo que su endpoint (015-I6).
- El cambio del lector → 014-cambios-del-lector. Incluye la policy sobre la petición, el planner en modo cambio, la validación de la propuesta, los capítulos afectados, el código de confirmación (un solo uso, guardado como hash, caducidad a `confirmation_minutes`), la confirmación y la ejecución `change_request`. Aquí se invoca ese flujo y se traducen sus resultados.
- El `MotorDePoliticas` y el audit log → 005-guardarrailes. El adaptador de Langfuse y la máscara → 004-observabilidad.
- Cualquier otra tool (progreso de una ejecución, entrevista, edición manual, listas prohibidas), así como los recursos y prompts MCP: los docs fijan siete tools.
- Elicitation del cliente (§18, «Confirmación MCP»), OAuth, y conexión desde Claude Desktop: §14.4 pide el README para MCP Inspector y Claude Code.
- Especificación TLA+ del servidor MCP: el opcional de TLA+ se cubre con `Regenerations.tla` (006-especificacion-tla, §18).
- Auditoría con el subagente `seguridad` de RT7, RT11 y RT13 → 021-auditoria-de-seguridad, que reutiliza estos casos.

## Comportamiento observable

**Convenciones.**
- **Llamada:** una petición `tools/call` a `/mcp` con `Authorization: Bearer <token>`. A y B son dos clientes con sus tokens (002).
- **Error de tool con código N:** la llamada termina en error de tool, no de transporte, y su contenido lleva el código de estado N y el mismo motivo que la API da en el caso.
- **Error de schema:** error de tool que nombra el argumento inválido. La tool no llega a ejecutarse.
- **Huella de la base:** el contenido de todas las tablas de SQLite. **Sin cambios** quiere decir la misma huella antes y después.
- **Pruebas T:** un cliente MCP por HTTP contra la aplicación en proceso, con el doble falso del puerto de agente, el doble nulo de observabilidad, y novelas y versiones sembradas con los fixtures de 009 y 013. Los briefs son ficticios.

### Conexión e identidad

#### 015-C01 — El servidor responde en `/mcp` y publica exactamente sus siete tools (T)
- **Entrada:** con la aplicación arrancada con su ciclo de vida normal, un cliente MCP con el token de A se conecta a `/mcp` (la ruta exacta, sin sufijos), inicializa y pide la lista de tools.
- **Salida:**
  - la inicialización identifica al servidor como `story-maker`;
  - la lista tiene exactamente las siete tools de `definitions.md` §12.2, con esos nombres;
  - cada tool trae su descripción y su schema de entrada, y todas salvo `download_novel` traen además su schema de salida;
  - las cinco de lectura se anuncian como de solo lectura, y `request_change` y `confirm_change` como de escritura no destructiva;
  - no hay ninguna otra tool, ni recursos, ni prompts;
  - `/api` sigue respondiendo en la misma aplicación.

#### 015-C02 — Sin un `TokenDeAcceso` válido, `/mcp` responde 401 y no ejecuta nada (T)
- **Entrada:** inicializar, listar las tools y llamar a `list_novels`, cada vez con una de las entradas de 002-C12, 002-C13 y 002-C14 que dan 401 (RT13). Entre ellas: sin cabecera, esquema `Basic`, token en la query, token caducado, firma alterada, `alg: none` y un token de vista (`aud` = `view_token`) de una versión propia.
- **Salida:** cada petición recibe HTTP 401 con `WWW-Authenticate: Bearer` y el mismo cuerpo que da `/api` (002-C12). No corre ninguna tool, no se abre ninguna traza y no se escribe en el audit log.

#### 015-C03 — La identidad es la del token de cada petición (T)
- **Entrada:** A y B tienen una novela cada uno. Por el mismo cliente MCP, ya inicializado, se llama a `list_novels` con el token de A, después con el de B y otra vez con el de A.
- **Salida:** cada respuesta contiene solo las novelas del token de esa petición. Nada de una petición anterior fija la identidad.

### Lectura

**Mundo de partida** de los casos 015-C04 a 015-C08:
- La novela P de A tiene v1 y v2 publicadas, y además una candidata en curso. En v2 cambiaron los capítulos 3 y 7, y un hecho nominal: el perro se llama Toby en v1 y Nala en v2. Cada versión publicada tiene su PDF guardado.
- La novela S de A no tiene ninguna versión publicada.

#### 015-C04 — `list_novels` devuelve las novelas del cliente con su estado y su versión vigente (T)
- **Entrada:** A tiene cuatro novelas, una en cada estado derivado (`interview`, `ready`, `in_progress` y `published`, esta con v1 y v2). B tiene una novela publicada. A llama a `list_novels`, que no tiene argumentos.
- **Salida:**
  - A recibe cuatro entradas, cada una con su id, su título (vacío si aún no lo tiene), su estado y el número de su versión vigente: 2 en la publicada y vacío en las demás;
  - son los mismos datos que da `GET /api/novels` a A;
  - la novela de B no aparece;
  - un cliente sin novelas recibe una lista vacía, no un error;
  - la huella de la base no cambia.

#### 015-C05 — `list_versions` da el historial publicado con sus capítulos cambiados (T)
- **Entrada:** A llama a `list_versions` con P y después con S.
- **Salida:**
  - P devuelve v1, con la lista de capítulos cambiados vacía, y v2, con los capítulos 3 y 7, en orden de número y con su fecha de publicación. Son los mismos datos que `GET /api/novels/{id}/versions`;
  - la candidata no aparece;
  - S devuelve una lista vacía;
  - la huella de la base no cambia.

#### 015-C06 — `get_chapter` devuelve un capítulo de una versión publicada (T)
- **Entrada:** A llama a `get_chapter` con la novela, el número de versión y el número de capítulo.
- **Salida:**

| Llamada | Resultado |
|---|---|
| P, v1, capítulo 3 · P, v2, capítulo 3 | El título y el texto de cada versión, distintos entre sí. Son los datos de ese capítulo en `GET /api/novels/{id}/versions/{v}` |
| P, v1, capítulo 5 · P, v2, capítulo 5 | El mismo texto en las dos versiones |
| Capítulo 1 · capítulo 10 | Se devuelven |
| Capítulo 0 · capítulo 11 | Error de schema |
| P, v3 · S, v1 | Error de tool con código 404: por número solo se alcanza una versión publicada, nunca una candidata ni una descartada |

  En ninguna fila cambia la huella de la base.

#### 015-C07 — `query_story_bible` devuelve la story bible de una versión (T)
- **Entrada:** A llama a `query_story_bible` con P y el número de versión.
- **Salida:**
  - recibe los personajes, los lugares, los hechos con los capítulos que los usan, y la cronología de esa versión. Son los mismos datos que `GET /api/novels/{id}/story-bible?version={v}`;
  - el hecho del perro dice Toby en v1 y Nala en v2;
  - una versión que no está publicada da error de tool con código 404;
  - la huella de la base no cambia.

#### 015-C08 — `download_novel` devuelve el PDF guardado como recurso incrustado (T)
- **Entrada:** A llama a `download_novel` con P y el número de versión.
- **Salida:**
  - la respuesta es un único recurso incrustado de tipo `application/pdf`;
  - sus bytes son idénticos a los del PDF guardado de esa versión, que son los que sirve `GET .../versions/{v}/pdf`;
  - v1 y v2 dan PDF distintos;
  - una versión que no está publicada da error de tool con código 404;
  - la huella de la base no cambia.

#### 015-C09 — Lo ajeno responde como inexistente en las siete tools (T)
- **Entrada:** A tiene la novela P y una solicitud de cambio `proposed` sobre ella, con su código. B hace estas llamadas (RT7, RT11):
  - `get_chapter`, `list_versions`, `query_story_bible`, `download_novel` y `request_change` con el id de P;
  - `confirm_change` con la solicitud de A y el código correcto;
  - para comparar, las mismas llamadas con ids que no existen.
- **Salida:**
  - cada llamada con lo de A es error de tool con código 404, con el mismo contenido que con el id inexistente;
  - `list_novels` de B no incluye nada de A;
  - no se abre ninguna sesión de rol, la solicitud de A sigue `proposed` y no se encola ninguna ejecución;
  - cada una de las dos llamadas de escritura deja una fila `mcp_write` `deny` en el audit log de B, sin novela;
  - nada de A cambia.

#### 015-C10 — Una entrada fuera de schema es un error sin efecto (T)
- **Entrada:** cada tool con argumentos se llama de cuatro formas: sin un argumento obligatorio; con un argumento del tipo equivocado (un texto donde va un número); con un capítulo fuera de 1–10; y, en `request_change`, con una selección que no es ni un fragmento ni un hecho.
- **Salida:**
  - cada llamada es un error de schema que nombra el argumento;
  - la huella de la base no cambia;
  - no se escribe en el audit log;
  - la traza de la llamada se abre igual (015-C16).

### Escritura

#### 015-C11 — `request_change` hace la misma interpretación que la web y solo propone (T)
- **Entrada:** P de A tiene v2 como versión vigente y, desde este caso hasta 015-C15, ninguna candidata en curso. El doble del planner en modo cambio propone cambiar el hecho del nombre del perro. A llama a `request_change` con la selección de ese hecho y la petición «el perro se llama Luna». Sobre una base idéntica, se hace la misma petición por `POST /api/novels/{id}/change-requests`.
- **Salida:**
  - la respuesta trae el id de la solicitud, la propuesta, los capítulos afectados y el código;
  - la propuesta y los afectados son iguales a los que da la API;
  - la solicitud queda `proposed`, con versión base v2;
  - no se encola ninguna ejecución y ninguna versión cambia;
  - el audit log tiene una fila `mcp_write` `allow` de A con la novela, además de las filas `change_request` que escribe 014.

#### 015-C12 — Una propuesta rechazada llega con el código de la API (T)
- **Entrada:** se provoca por `request_change`, con los mismos dobles que usan las pruebas de 014, cada rechazo que 014 define para una propuesta:

| Rechazo | Código |
|---|---|
| Novela sin versión publicada | 409 |
| Petición con una entrada prohibida (la solicitud queda `rejected`) | 422 |
| Sin propuesta válida tras `max_retries.change` (la solicitud queda `rejected`) | 422 |
| Proveedor caído, o sin sitio en el techo tras `api_wait_seconds` (no se guarda nada) | 503 |

- **Salida:**
  - cada llamada es error de tool con ese código y el motivo que da la API;
  - lo que queda en SQLite es lo mismo que por la API;
  - no hay código de confirmación ni ejecución en cola;
  - cada llamada deja una fila `mcp_write` `deny` con el motivo.

#### 015-C13 — `confirm_change` con el código encola la ejecución de cambio (T)
- **Entrada:** A llama a `confirm_change` con el id de la solicitud de 015-C11 y su código.
- **Salida:**
  - la respuesta trae el id de la ejecución;
  - hay una ejecución `change_request` en cola, con versión base v2;
  - la solicitud pasa a `confirmed`;
  - ninguna versión cambia todavía;
  - hay una fila `mcp_write` `allow`.

  El flujo es el mismo en los dos canales: una propuesta hecha por la API se confirma por `confirm_change`, y una hecha por MCP se confirma por la API.

#### 015-C14 — Una confirmación inválida se rechaza sin efecto (T)
- **Entrada:** A tiene una solicitud `proposed` y su código, y llama a `confirm_change` en cada caso de la tabla (RT11):

| Llamada | Código |
|---|---|
| Con un id de solicitud que no existe (sin `request_change` previo) | 404 |
| Con un código incorrecto, incluido el de otra solicitud propia | 422 |
| Por segunda vez, con el código ya usado | 409 |
| Pasados `confirmation_minutes` desde la propuesta (solicitud `expired`) | 409 |
| Con una solicitud de B y el código de B | 404, como en 015-C09 |

- **Salida:**
  - cada llamada es error de tool con ese código;
  - no se encola ninguna ejecución;
  - la solicitud conserva su estado, salvo el paso a `expired`, que decide 014;
  - cada llamada deja una fila `mcp_write` `deny` con el motivo.

#### 015-C15 — Un cambio pedido y confirmado por MCP publica versión y PDF nuevos, y conserva la anterior (T)
- **Entrada:** partiendo de 015-C13, se usan los dobles de roles, del `VerificadorFormal` y del revisor visual con los que 014 lleva una ejecución de cambio hasta publicarla. El worker ejecuta la ejecución que encoló `confirm_change`. Después, A llama a `list_versions`, `get_chapter`, `query_story_bible` y `download_novel`.
- **Salida:**
  - `list_versions` muestra v3 con sus capítulos cambiados;
  - `get_chapter` de v3 da el texto nuevo en los capítulos cambiados y el de v2 en los demás;
  - `query_story_bible` dice Luna en v3 y Nala en v2;
  - `download_novel` de v3 da un PDF distinto del de v2, y el de v2 sigue dando los mismos bytes que antes (`verification.md` §5, fila 2.10).

### Trazas

#### 015-C16 — Cada llamada a una tool deja exactamente una traza `mcp:<tool>` (T)
- **Entrada:** con el doble nulo de observabilidad:
  - se llama a cada tool con éxito y con error (404 y de schema);
  - además, se inicializa, se listan las tools y se hace una petición sin token.
- **Salida:**
  - cada llamada deja una sola traza, llamada `mcp:<tool>` (por ejemplo, `mcp:list_novels`), con la entrada de la llamada y su salida o su error;
  - su `Sesion` es el id de la novela cuando la llamada resolvió una novela propia. Van sin sesión `list_novels`, las llamadas que acaban en 404 por una novela ajena o inexistente, y los errores de schema;
  - las que acaban en error llevan nivel WARNING y el motivo;
  - `request_change` no abre una traza de propuesta aparte: la sesión del planner en modo cambio (`rol:planner`, `tool:propose_change`) y las decisiones de la policy cuelgan de la traza `mcp:request_change`;
  - inicializar, listar las tools y la petición sin token no dejan ninguna traza.

#### 015-C17 — Las trazas pasan por la máscara y nunca llevan el código de confirmación ni el PDF (T)
- **Entrada:** A tiene dos novelas con destinatarios distintos, con nombres ficticios. El doble nulo captura lo que se exportaría. A llama a `get_chapter`, `list_novels`, `request_change`, `confirm_change` y `download_novel`.
- **Salida:**
  - en lo capturado no aparece ningún nombre ni ninguna fecha de los briefs. La traza de `get_chapter` los sustituye con la máscara de su novela, y la de `list_novels` con la unión de las máscaras de las novelas de A (`architecture.md` §13.5);
  - el código de confirmación no aparece en la salida de `mcp:request_change`, ni en la entrada de `mcp:confirm_change`, ni en ninguna fila del audit log;
  - la traza de `download_novel` registra la versión, el tipo y el tamaño del PDF, no sus bytes.

### Conexión real

#### 015-C18 — Siguiendo el README, un cliente real se conecta y pide un cambio (D)
- **Entrada:** el servidor corre en la máquina con sesión de Claude Code, con una cuenta cuya novela de ejemplo está publicada. Una persona, siguiendo solo el README, obtiene un token con el acceso y conecta a `/mcp` con ese token, primero MCP Inspector y después Claude Code.
- **Salida:**
  - los dos clientes listan las siete tools;
  - `list_novels`, `get_chapter`, `list_versions` y `query_story_bible` responden con la novela de ejemplo, y `download_novel` entrega un PDF que se abre;
  - en uno de los dos clientes, `request_change` muestra la propuesta y sus afectados, la persona la acepta, y `confirm_change` encola la ejecución. Al publicarse, `list_versions` muestra la versión nueva;
  - el README usa el marcador `TU_TOKEN_AQUI` y no deja el token en ningún fichero del repositorio;
  - el README avisa de que `request_change` tarda lo que una sesión del planner, y explica cómo ampliar el tiempo de espera del cliente.

  Esta demostración gasta cuota de la suscripción, así que se ejecuta una sola vez, al final de la spec (O.5, O.7).

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 015-I1 | Las cinco tools de lectura no modifican nada: la huella de la base es la misma antes y después de cada llamada, acabe con éxito o con error (O.3) | T | 015-C04 a 015-C10 comparan la huella |
| 015-I2 | Las tools de escritura solo proponen o encolan. Nunca cambian una versión, su story bible ni sus capítulos: la novela solo la cambia la ejecución, que pasa el gate | T | 015-C11 a 015-C14 comprueban que no cambia ninguna tabla de ámbito versión (§15.6) |
| 015-I3 | La identidad es la del `TokenDeAcceso` de cada petición, verificada en el mismo punto que la API. Lo ajeno es indistinguible de lo inexistente en las siete tools (O.6, RT7) | T | 015-C02, 015-C03 y 015-C09. El punto único lo revisa el `verificador` (002-I5) |
| 015-I4 | Por MCP solo se ven versiones publicadas | T | 015-C05 y 015-C06 |
| 015-I5 | Hay exactamente siete tools. Su schema publicado es el que se deriva de su modelo, y toda salida con éxito cumple su schema de salida (O.2) | T | 015-C01 y una prueba de contrato que valida contra su schema cada salida de 015-C04 a 015-C08, 015-C11 y 015-C13 (`verification.md` §3.5) |
| 015-I6 | Para el mismo cliente y los mismos argumentos, cada tool de lectura devuelve lo mismo que su endpoint de la API, y las de escritura recorren el mismo flujo que la API | T | 015-C04 a 015-C08 y 015-C11 a 015-C14 |
| 015-I7 | Cada llamada a una tool deja exactamente una traza `mcp:<tool>` (O.4) | T | 015-C16 |
| 015-I8 | Cada llamada a una tool de escritura que supera el schema deja exactamente una fila `mcp_write`: `allow` si tuvo efecto (una propuesta o una ejecución en cola) y `deny` si no, con el motivo | T | 015-C09 y 015-C11 a 015-C14 |
| 015-I9 | El código de confirmación solo sale en claro en la respuesta de `request_change` | T | 015-C17 |
| 015-I10 | Nada de un brief llega a Langfuse sin pasar por la máscara | T | 015-C17 |
| 015-I11 | La frontera MCP está tipada: la entrada y la salida de cada tool tienen un modelo validado, bajo mypy estricto | A | `verification.md` §3.1 |
| 015-I12 | Las descripciones de las tools están en español y dicen qué hace cada una. La de `request_change` dice que solo propone; la de `confirm_change`, que se llama solo cuando la persona ha aceptado la propuesta | I | El `verificador`, al cerrar, sobre la lista de 015-C01 |
| 015-I13 | Un cliente MCP autónomo puede confirmar por su cuenta: el código evita escrituras accidentales, no esa | U | `verification.md` §6 U13 |

## Scores y trazas

- **Trazas:** una `mcp:<tool>` por llamada a una tool (015-C16). Su `Sesion` es la novela propia que resolvió la llamada; si no resolvió ninguna, va sin sesión. Todo pasa por la máscara de la novela; en `list_novels`, por la unión de las máscaras (015-C17).
- **Spans:** los que abre 014 en la propuesta (`rol:planner`, `tool:propose_change`) cuelgan de `mcp:request_change`. La ejecución que encola `confirm_change` tiene su propia traza, `solicitud-de-cambio`, que es de 014.
- **Scores:** ninguno propio. El servidor MCP no ejecuta validadores.

## Docs referenciados

- `architecture.md`:
  - §1.4: un proceso, con el servidor MCP en la misma aplicación.
  - §6.5: 503 sin sitio en el techo.
  - §9.3: el número de versión se asigna al publicar, y la versión publicada es inmutable.
  - §10.1: el cambio del lector y la confirmación.
  - §12.2: el audit log y el origen `mcp_write`.
  - §13.1: una traza por llamada MCP.
  - §13.5: la máscara, con la unión de máscaras.
  - §14.2: el PDF guardado por versión y `download_novel`.
  - §14.3: lo ajeno responde 404, con pruebas por MCP.
  - §14.4: el servidor MCP completo.
  - §15.6: tablas de ámbito versión.
  - §15.7: códigos de estado y `/mcp`.
  - §15.9: `api` compone.
  - §16.19.
  - §18: filas «Confirmación MCP», «Autenticación», «Propuesta antes de confirmar» y «Especificaciones TLA+».
- `definitions.md`:
  - §3: `Novela` (estado derivado, versión vigente), `Version`, capítulo cambiado.
  - §5: `SolicitudDeCambio`, `Ejecucion`.
  - §7: `DecisionDePolitica`, `AuditLog`, texto no confiable.
  - §8: `Sesion`, `Traza`, `Mascara`.
  - §10: `TokenDeAcceso`, `ServidorMCP`, `Confirmacion`, `VistaDeVersion` (token de vista).
  - §12: identificadores en inglés; §12.2, tools MCP; §12.3, trazas `mcp:<tool>`; §12.4, enumerados.
- `verification.md`:
  - §2: clases.
  - §3.1: tipos en la frontera MCP.
  - §3.5: contrato de las 7 tools.
  - §4.1: traza por llamada MCP con el doble nulo.
  - §4.9: RT7, RT11 y RT13.
  - §5: O.1–O.7 y 2.10.
  - §6: U6 y U13.
- `project-constraints.md`, opcionales: «Servidor MCP para consultar y descargar novelas», «Tools de escritura sobre el servidor MCP» y «Login de usuarios» (la identidad en MCP).
- `backend/AGENTS.md`: la 015 posee `api/` (servidor MCP). `AGENTS.md` (*Parallel lanes*): el README es del integrador.
- Specs: 002-autenticacion (002-C12 a 002-C14, 002-I5), 008-brief-y-entrevista, 009-story-bible-y-versiones, 013-lectura-y-pdf, 014-cambios-del-lector, 004-observabilidad, 005-guardarrailes.

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué pide? | Siete tools en `/mcp` con el token; schema; solo lectura en las de lectura; escritura en dos pasos; traza por llamada; `mcp_write`; README | §14.4, `definitions.md` §10 y §12.2 |
| ¿Qué capa posee cada lectura? | Los endpoints de 008, 009 y 013. MCP devuelve lo mismo (015-I6) y no recalcula nada | §15.7, `backend/AGENTS.md` |
| ¿Cómo se concilian el «solo lectura» y la escritura? | Las de lectura no modifican nada; las de escritura solo proponen o encolan | `definitions.md`, `ServidorMCP` |
| ¿Dónde se autentica? | En el transporte, para todo `/mcp`, con el punto único de 002 y en cada petición | §14.4, 002-I5. **Hueco** → §18 |
| ¿Qué versiones se ven? | Solo las publicadas, por número | `definitions.md`, `Version` y `VistaDeVersion`; §9.3 |
| ¿La versión es obligatoria o por defecto es la vigente? | Obligatoria, porque el encargo pide «un capítulo concreto de una versión concreta»; la vigente la da `list_novels` | Máxima de simplicidad |
| ¿Qué recibe `confirm_change`? | El id de la solicitud y el código, como `POST /api/change-requests/{id}/confirm`. RT11 distingue un código ajeno de una solicitud ajena | **Contradice** la notación `confirm_change(code)` de §14.4 y §18 → retocar el doc |
| ¿Cómo se ven los errores? | Error de tool con el código de la API; los errores de schema, como error de schema | §15.7. **Hueco** → §18 |
| ¿Qué es «cada llamada, una traza»? | Una por `tools/call`. Ninguna por inicializar, por listar las tools ni por un 401. La propuesta de `request_change` va dentro de su traza | §13.1. **Hueco** → §18 |
| ¿Qué sesión tiene `list_novels`? | Ninguna, y usa la unión de las máscaras | §13.5 |
| ¿Qué es «cada escritura, una entrada `mcp_write`»? | Una por llamada de escritura que supera el schema: `allow` o `deny` | §12.2. **Hueco** → §18 |
| ¿Van el código o el PDF a Langfuse? | No: el código solo se guarda como hash (§10.1), y un PDF no se puede enmascarar | §10.1, §13.5 |
| ¿Más tools, elicitation, Claude Desktop o TLA+ del servidor? | No | `definitions.md` §12.2, §14.4, §18 |
| ¿En qué idioma van los identificadores y las descripciones? | Nombres y campos en inglés, descripciones en español | `definitions.md` §12 |
| ¿Quién escribe el README? | El integrador, con el texto del carril | `AGENTS.md` |
| ¿Depende la 015 de la 008? | Sí: `list_novels` es `GET /api/novels`, que es de la 008, pero la tabla de `TODO.md` no la lista | Aviso al integrador |
