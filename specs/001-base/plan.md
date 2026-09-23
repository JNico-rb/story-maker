# 001 — BAS · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md); columnas, versiones e interfaces externas: [design.md](design.md). Verificación (`docs/verification.md` §5): unitarias de la config, «Validación de la config al arrancar»; contratos de importación, «Aislamiento entre slices y capas»; tipos y validación en los bordes, «Fronteras de datos entre capas»; pruebas de contrato y regeneración del cliente en CI, «API, SSE y cliente generado» —el SSE es de 007—; TypeScript estricto, ESLint, `steiger`, build de producción e inspección con el browser MCP, «Frontend»; e integración con el doble, «CLI» —la demostración de extremo a extremo que la usa es de 017—. Las pruebas del workspace son parte de las de sandbox (`verification.md` §4.3), y las demostraciones de entorno, las de `architecture.md` §15.3.

### Steps

#### Módulos y regla de dependencia

- [ ] El backend tiene los módulos `domain`, `store`, `platform`, `harness`, `lint`, las cinco fases de `phases` y `execution` → el contrato de importación falla en CI si una fase importa otra fase o `execution`, si `domain` importa otro módulo del proyecto o una biblioteca de I/O, si `platform` importa `domain`, o si `store` o `lint` importan algo que no sea `domain`. `execution` es la raíz de composición: importa las fases y `platform` (RF-BAS-1 · clase A)
  - Sobre el stack de R1: Python 3.12 fijado, dependencias con `uv`, FastAPI servida por uvicorn, Pydantic v2 y SQLAlchemy 2 (R1 · clase I).
  - Los contratos son los de `design.md` §2.1, que siguen el diagrama de `architecture.md` §14.2: además de los anteriores, `harness` no importa `phases`, `execution` ni `lint`, y `platform` no importa ningún otro módulo del proyecto.
- [ ] Código, tablas, API, MCP y JSON en inglés, con los identificadores de `definitions.md` §12; docs, prompts e interfaz en español; los nombres que se ven en Langfuse, etiquetas en español, ASCII y kebab-case (R10 · clase I)
- [ ] El resto del stack de `architecture.md` §14.1, con las versiones de `design.md` §1 (R4 · clase I)
  - 001 lo fija; cada pieza la adopta la spec que la usa: Langfuse, 004; FastMCP, 016; Playwright y pypdf, 013 y 014; spaCy, 012; bcrypt y PyJWT, 002; Lean con Lake, 009; TLA+ con TLC, 006; `pip-audit` y `pnpm audit`, 018. GitHub Actions y `detect-secrets` entran en 001, con la CI.
- [ ] Un módulo distinto de `platform` importa el Agent SDK → el contrato de importación falla en CI (RF-BAS-2 · clase A)
- [ ] Aparece en el backend un módulo o carpeta llamado `commons`, `shared` o `utils` → falla una prueba (RF-BAS-3)
- [ ] Las constantes del encargo y del dominio —10 capítulos de 1.000 a 1.500 palabras, el objetivo de cada extensión, de 3 a 6 beats por capítulo y el orden de una consecuencia como mucho 3— viven en `domain`, no en config (R9 · clase I)

#### Ajustes del servidor y config

- [ ] Al arrancar se leen del entorno los ajustes del servidor de `definitions.md` §11 → el servidor no arranca, con un error que nombra la variable, si falta una, si `FORMAL_VERIFIER` no es `local` ni `github`, si es `github` y falta `GITHUB_REPOSITORY`, `LEAN_WORKFLOW` o `GITHUB_TOKEN`, o si `JWT_SECRET` tiene menos de 32 caracteres. Frontera: 31 caracteres no arranca y 32 sí (RF-BAS-15)
- [ ] Toda variable de los ajustes del servidor aparece en `.env.example`, y ninguna con un valor real; git ignora `.env` → una prueba compara las variables de `.env.example` con las de los ajustes, y `detect-secrets` pasa (RF-BAS-49)
- [ ] El catálogo de criterios declara cada criterio con su id, dimensión, niveles, método, bloqueante, acción requerida, origen, parámetros y rúbrica si la tiene → su carga falla si dos criterios tienen el mismo id o si un id no es una etiqueta ASCII en kebab-case. 001 declara el de `schema-salida`, bloqueante y sin nivel ni acción (RF-BAS-14)
  - Cada spec añade los criterios de sus validadores.
- [ ] Al arrancar, la config de `STORY_MAKER_CONFIG` se valida entera → el servidor no arranca, con un error que nombra la clave, ante: una clave desconocida en cualquier nivel; un tipo erróneo; en `retrieval.quotas`, una plaza negativa o no entera, una colección o un consumidor desconocidos, un par ausente o prosa con plazas para un consumidor que no sea el editor ni el linter de repetición; `window_ceiling` por encima de 100.000; `api_window_share`, si tiene valor, que no sea menor que `window_ceiling`; un rol de `operation.roles` ausente o desconocido; un modelo con valor en `operation.roles` sin sus cuatro precios, si `operation.pricing` tiene valor; una franja desconocida en `readability_targets`; un id de `thresholds` que no esté en el catálogo de criterios, o uno de `active_criteria` que no sea un criterio de rúbrica del catálogo; `access_token_hours` o `confirmation_minutes` que no sean enteros positivos. Fronteras: `window_ceiling` de 100.000 arranca y de 100.001 no; `api_window_share` igual a `window_ceiling` no arranca, y uno menos sí (RF-BAS-11)
  - Una clave ausente también impide arrancar con un error que la nombra: ningún campo tiene valor por defecto (`design.md` §3.2).
  - Una plaza `null` es una cifra sin calibrar: la trata RF-BAS-13.
- [ ] Se leen los criterios activos de la config → son los de rúbrica que lista `active_criteria` más, siempre, los programáticos y `tema-prohibido`, que no se pueden desactivar (RF-BAS-12)
- [ ] Una cifra sin calibrar (`architecture.md` §15.2) vale `null` en la config → el servidor arranca; leerla falla con un error que nombra la clave y dice que está sin calibrar, y nunca se sustituye por un valor por defecto (RF-BAS-13)
  - Las pruebas fijan sus propias cifras; ninguna va a `config.json`.

#### Store

- [ ] Toda conexión que abren la API o el worker → tiene `journal_mode` WAL, `busy_timeout` distinto de cero, `foreign_keys` activo —una fila que referencia una inexistente se rechaza— y `sqlite-vec` cargado (RF-BAS-7)
  - Un solo fichero SQLite en WAL, con migraciones Alembic desde el principio, y `sqlite-vec` y FTS5 en el mismo fichero que la story bible (R2 · clase I).
  - SQLAlchemy es síncrono y recibe la conexión de `platform` (R7 · clase I).
- [ ] Con el directorio de datos vacío, la orden de migrar → crea en él un único fichero SQLite con las tablas, índices y disparadores de `design.md` §4; repetirla no cambia nada (RF-BAS-6)
- [ ] Dos procesos escriben a la vez en el mismo fichero, como la API y el worker → los dos terminan su transacción: el segundo espera dentro de `busy_timeout` en vez de fallar (RF-BAS-8)
- [ ] Un `UPDATE` sobre una fila de una tabla de solo inserción → la base lo rechaza con error y la fila no cambia (RF-BAS-9)
- [ ] Un `DELETE` sobre una fila de una tabla de solo inserción → la base lo rechaza, salvo en `facts` y `canon_cards` cuando la fila es de una versión candidata y la escribió el registro de un capítulo, que es el reemplazo de un registro repetido (`architecture.md` §8.3) (RF-BAS-10)
  - Qué filas reemplaza cada registro lo decide 011.

#### Índice

- [ ] Con `sqlite-vec` cargado → la distancia coseno que calcula en SQL sobre vectores guardados en la tabla de vectores, en filas ya filtradas por una consulta normal, coincide con la esperada (RF-BAS-30)
- [ ] Las tablas FTS5 de CanonCards y de párrafos usan el tokenizador `unicode61 remove_diacritics 2` → `MATCH` con «cancion» encuentra una fila con «Canción», y al revés (RF-BAS-31)
- [ ] La tabla de vectores es una tabla normal con clave (huella, modelo) → insertar un segundo vector para un par que ya existe falla (RF-BAS-32)
- [ ] Una transacción escribe una tabla normal, una tabla FTS5 y la de vectores, y se deshace → ninguna de las tres conserva la fila: el índice puede escribirse en la misma transacción que la story bible (RF-BAS-33)
- [ ] El productor de vectores recibe un identificador de modelo y unos textos → devuelve un vector por texto, con la dimensión del modelo e igual para el mismo texto; la caché del modelo queda en el directorio de datos (RF-BAS-34)
  - Qué se indexa y cómo se recupera es de 008.

#### Puerto de agente

- [ ] Las fases abren sus sesiones de rol solo a través del puerto de agente, y existe un doble que implementa el mismo puerto → un guion del doble fija las llamadas a tool, el mensaje final, el uso y los ids de mensaje de cada sesión, sin red ni modelo (RF-BAS-17)
  - El adaptador real es el Claude Agent SDK para Python, que ejecuta como subproceso el CLI empaquetado, con OpenRouter como proveedor y modelos de Anthropic (R3 · clase I).
  - Las sesiones son asíncronas y pueden ir en paralelo (R7 · clase I).
- [ ] CI corre sin clave del proveedor → toda prueba abre sus sesiones con el doble; una prueba que intentara abrir una sesión real falla (RF-BAS-45)
  - Los requisitos del adaptador del SDK se prueban traduciendo secuencias de mensajes del SDK construidas en la prueba, sin CLI ni red. La sesión real es la de RF-BAS-41.
- [ ] Se abre una sesión de rol → corre con el modelo, la salida máxima y los turnos máximos de su rol en `operation.roles`, y con el prompt de sistema que le pasa quien la abre (RF-BAS-18)
- [ ] Se abre una sesión de rol → su entorno lleva `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN` con el valor de `OPENROUTER_API_KEY` y `ANTHROPIC_API_KEY` presente y vacía, aunque el proceso del backend tenga otra en su entorno (RF-BAS-16)
- [ ] Una sesión termina bien → el puerto devuelve el desenlace «completada» (`completed`), con el uso exacto de la sesión entera —tokens de entrada, de salida, de lectura de caché y de escritura de caché—, su duración y la lista de ids de mensaje. El uso se toma solo del resultado final de la sesión, nunca del uso por turno, que por OpenRouter llega a cero (RF-BAS-19)
- [ ] Una sesión agota `roles.<rol>.max_turns` → el puerto devuelve el desenlace «turnos agotados» (`turns_exhausted`), también con su uso exacto, aunque el SDK lance su error después del resultado final (RF-BAS-20)
- [ ] Una sesión pasa de `max_agent_seconds` → el puerto la interrumpe, cierra su subproceso y devuelve el desenlace «tiempo agotado» (`time_exhausted`) (RF-BAS-21)
  - El tiempo lo pasa quien abre la sesión, leído de config: sin valor, falla como en RF-BAS-13.
- [ ] Quien abrió una sesión la corta mientras corre → el puerto la interrumpe, cierra su subproceso y devuelve el desenlace «cortada» (`cut`) (RF-BAS-22)
  - Cuándo se corta lo decide cada spec: la cancelación, 007.
- [ ] El proveedor o el transporte fallan, agotados los reintentos del propio SDK → el puerto devuelve el desenlace «fallo de infraestructura» (`infrastructure_failure`), distinto de los anteriores (RF-BAS-23)
- [ ] Una sesión registra hooks antes y después de cada tool → el de antes puede denegar la llamada con un motivo, que el modelo recibe como resultado, y entonces la tool no se ejecuta; el de después puede sustituir la salida que lee el modelo. El doble pasa sus llamadas guionizadas por los mismos hooks y manejadores, en el mismo orden que el SDK (RF-BAS-24)
  - 001 da el mecanismo. Los hooks concretos son de sus specs: el de policy, de 003; el de validación de capítulo, de 011; el de observabilidad, de 004. La lista blanca, las tools integradas desactivadas y el modo de permisos, de 003.
- [ ] Una tool en proceso se declara con un modelo de datos, del que sale su JSON Schema → si el modelo la llama con una entrada que no cumple el schema, el manejador la rechaza sin ningún efecto, el modelo recibe el error de validación y la sesión sigue; la llamada cuenta como fallo del validador `schema-salida`. Con una entrada válida cuenta como acierto (RF-BAS-25)
  - El resultado de la sesión lista cada llamada a tool con su acierto o fallo de `schema-salida`. De ahí lo toman 007, que cuenta el fallo como intento (RF-RUN-24), y 004, que envía su score.
- [ ] Una tool entrega una salida válida → la entrega queda en las salidas de la sesión, en memoria, y la tool no escribe nada en SQLite (RF-BAS-26)
  - Ninguna tool pide ni devuelve contexto: la ventana llega cerrada (R8 · clase I). La cota de su salida, `max_tool_output`, es de 008.

#### Workspace del harness

- [ ] Se abre una sesión de rol → corre con `cwd` en el workspace del harness y carga su `CLAUDE.md` y sus skills, y no el `CLAUDE.md` de ningún directorio padre: ni el de desarrollo de la raíz ni el personal del usuario (RF-BAS-27)
  - Cargar las skills es tenerlas disponibles: solo el writer y el editor tienen la tool `Skill` para usar la del producto (`architecture.md` §7.3, §7.4), y eso es de 003.
  - El contenido del `CLAUDE.md` del workspace y de su skill es de 011; 001 deja el workspace con los ficheros que la prueba necesita.
- [ ] Se abre una sesión de rol → solo arranca los servidores MCP que declara, nunca los del `.mcp.json` de la raíz (RF-BAS-28)
- [ ] Se abre una sesión de rol → la telemetría y la memoria automática del CLI están apagadas, y su directorio de configuración está dentro del directorio de datos (RF-BAS-29)

#### Directorio de datos

- [ ] Cualquier ruta en la que escribe el backend —el fichero SQLite, la configuración del CLI del SDK, las cachés de modelos, la salida de Playwright MCP y los PDF— → cae dentro de `STORY_MAKER_DATA_DIR`, y una ruta que saldría de él se rechaza; una prueba de integración con el doble no deja ningún fichero fuera. La única excepción es el PDF que deja la orden `example` en la ruta que recibe (`architecture.md` §11.6), que es de 017 (RF-EVL-4) (RF-BAS-35)

#### Servidor

- [ ] La orden de arrancar el servidor → lanza uvicorn en un solo proceso, sin `--workers` ni recarga automática: la parte de la API del techo de ventana se cuenta en la memoria de ese proceso (RF-BAS-36)
  - La prueba comprueba los argumentos con que se lanza uvicorn. Un segundo proceso de la API contaría su propia parte, y la suma en vuelo podría pasar de `window_ceiling` (008).
- [ ] Una petición cuyo cuerpo o parámetros no cumplen su schema → 422 con los errores de validación (RF-BAS-38)
  - En 001 no hay ruta de producto con cuerpo: la prueba monta una propia en la aplicación de prueba, y cada spec que añade una ruta la cubre con sus casos.
- [ ] El frontend compila con Vite, React, TypeScript estricto y Tailwind CSS, con `pnpm` 10.x → su build de producción es el que sirve FastAPI (RF-BAS-47 · clase A)
  - `pnpm` 10.x y no la 11, que no arranca sin el Visual C++ Redistributable (R5 · clase I).
- [ ] El frontend sigue Feature-Sliced Design v2.1 con `app`, `pages` y `shared`, sin `widgets` → `steiger` falla en CI si una capa importa una capa superior, si una página se consume sin pasar por su `index` o si `shared` se consume sin pasar por su segmento (RF-BAS-4 · clase A)
- [ ] Con el servidor en marcha → la API responde bajo `/api`; una ruta fuera de `/api` que no es un fichero del frontend compilado devuelve su página de entrada, y una ruta desconocida bajo `/api` responde 404 sin devolverla. En desarrollo, el servidor de Vite reenvía `/api` al backend (RF-BAS-37)
  - `/mcp` es el servidor MCP (016): se monta antes que el frontend compilado, así que no cae en la página de entrada.
- [ ] Una orden exporta el esquema OpenAPI sin arrancar el servidor, y el cliente TypeScript de `shared/api` se genera de él; los dos se commitean → CI los regenera y falla si difieren de los del repositorio (RF-BAS-39 · clase A)
- [ ] La imagen corporativa sale del logo de `images/`: nombre, logotipo, paleta y tipografía, como tokens del tema en `app` → se aplica igual en todas las páginas (RF-BAS-48 · clase I)
  - Cada spec que añade una página lo inspecciona con el browser MCP y deja su fila en `verification.md` §9.3.
- [ ] Lo que usa una sola página se queda en ella, y `entities` y `features` solo aparecen cuando hay reutilización real → la revisión de cada página lo comprueba (RF-BAS-5 · clase I)
  - Las páginas llegan con sus specs (002, 005, 007, 013 y 015); en 001, la revisión confirma que `pages` está vacía y no hay `entities`, `features` ni `widgets`.

#### CLI y demostraciones de entorno

- [ ] La CLI del backend tiene las órdenes de operación —migrar, arrancar el servidor, exportar el esquema OpenAPI, comprobar el entorno y lanzar la mutación—. La de comprobar el entorno → ejecuta cada comprobación de RF-BAS-41 a RF-BAS-43, dice cuál pasa y por qué falla cada una de las que no, y termina con código distinto de cero si falla alguna (RF-BAS-40)
  - La prueba sustituye las comprobaciones por dobles que pasan y fallan; las reales son las demostraciones siguientes.
- [ ] En el portátil de desarrollo, la orden de comprobaciones → pasa todas: el CLI que empaqueta el Agent SDK arranca bajo Smart App Control; una sesión real contra OpenRouter corre con el modelo y la salida máxima de su rol, usa una tool en proceso, un hook que deniega, uno que sustituye la salida, una skill y el workspace, carga solo el `CLAUDE.md` del workspace, deja su configuración en el directorio de datos y devuelve el uso de la sesión; spaCy con su modelo de español, `sqlite-vec` y `onnxruntime` cargan, y `fastembed` produce un vector; Playwright maneja el Edge instalado sin interfaz, incluido `page.pdf` con índice y etiquetas; Playwright MCP navega así desde una sesión del SDK; con uvicorn en marcha, una petición lanza los dos subprocesos del sistema, el CLI del SDK y un proceso como el del worker; y los ids de mensaje de OpenRouter empiezan por `gen-` y su consulta de coste por generación los resuelve (RF-BAS-41 · clase D)
  - Con el runtime de Visual C++ de `msvc-runtime` en espacio de usuario y los enlaces simbólicos de la caché de HuggingFace desactivados (R6 · clase D).
  - Fija los hechos marcados **unsure** en `design.md` §5.1 y §5.7 —la variable de la salida máxima, el campo que sustituye la salida de una tool MCP y la variable de los enlaces simbólicos— y los corrige allí.
- [ ] En el portátil de desarrollo, una sesión real cortada por tiempo o por quien la abrió → no deja ningún subproceso del CLI vivo (RF-BAS-42 · clase D)
- [ ] Un workflow mínimo de GitHub Actions con Lean se dispara con `workflow_dispatch` y `return_run_details`, se sondea hasta que concluye y deja su artefacto → se mide su tiempo de ida y vuelta frente a la estimación de 1 a 3 minutos (RF-BAS-43 · clase D)
  - Fija la versión de la API de GitHub, marcada **unsure** en `design.md` §5.4. El verificador remoto completo es de 009.
  - Si una de estas tres demostraciones falla, se reabre la decisión que la usa, con su motivo, y el hallazgo queda en el registro de iteraciones (`verification.md` §8).

#### CI

- [ ] Cada cambio → GitHub Actions ejecuta Ruff, mypy estricto, las pruebas del backend —unitarias, de integración, de propiedades, de contrato y doradas—, la comprobación de que las migraciones cubren los modelos, el TypeScript estricto, ESLint, el build de producción del frontend, los contratos de importación, `steiger`, la deriva del cliente generado y `detect-secrets`; la integración falla si falla cualquiera (RF-BAS-44)
  - TLC, `lake build` y la lectura de vuelta de Langfuse los añaden 006, 009 y 004.
- [ ] Tipado estricto: mypy estricto en todo el backend; modelos Pydantic en los bordes —entrada HTTP, config, ajustes, entrada de cada tool—; TypeScript estricto en el frontend (RNF-1 · clase A)
- [ ] Análisis estático: Ruff con las reglas de seguridad (`S`) y `detect-secrets` en cada cambio (RNF-2 · clase A)
- [ ] Las pruebas viven dentro de cada slice —las de extremo a extremo, en `execution`—, y sus nombres dicen el comportamiento (RNF-3 · clase I)
- [ ] Las pruebas de mutación no corren en cada cambio → la orden de mutación y un workflow programado las lanzan sobre los cuatro objetivos de `verification.md` §3.7 —el motor de políticas y la normalización de prohibidas (003), la validación del brief (005), los validadores del hook de capítulo (011) y el gate (014)— a medida que existen, y dan los mutantes que sobreviven en cada ruta de rechazo (RF-BAS-46)
  - En 001 no existe ninguno de los cuatro: la spec que crea uno lo añade a los objetivos.

#### Entregables de proceso y de Claude Code

- [ ] El README de la raíz → describe el repositorio, cómo instalar y arrancar backend y frontend en local, y dónde vive cada entregable del encargo (RF-BAS-50 · clase I)
- [ ] ADR 0003 → dice qué se decidió construir y por qué antes de escribir código: es la spec inicial del encargo (RF-BAS-51 · clase I)
- [ ] `architecture.md` §16 → recoge cada decisión de diseño relevante con sus opciones, su criterio y su elección: es el registro de trade-offs (RF-BAS-52 · clase I)
- [ ] Los diagramas de la arquitectura del harness (`architecture.md` §2, §8.1 y §9.5), del esquema SQLite (§14.5) y la tabla de validadores con su punto de ejecución (§10.2) → están en los docs, y el diagrama del esquema tiene las mismas tablas y relaciones que la migración (RF-BAS-53 · clase I)
  - El de la máquina de estados de TLA+ es de 006.
- [ ] Al cerrar 001 → la cabecera de `verification.md` §9 lleva el explainer del desarrollo guiado por specs —docs → spec → plan → pruebas → código—, y la de `architecture.md` §7.4, el de las tools con schema validado, como asigna la lista de explainers del README (RF-BAS-54 · clase I)
- [ ] Los commits generados por un agente se marcan como tales (R11 · clase I)
- [ ] `CLAUDE.md` en la raíz, cuidado y legible (R12 · clase I)
- [ ] `.claude/` commiteada con los ficheros de memoria y los comandos propios (R13 · clase I)
  - El comando de la auditoría de seguridad es de 018.
- [ ] `.mcp.json` incluye Playwright MCP con versión fijada y el Edge instalado; sus instantáneas van a `.playwright-mcp/`, ignorada por git (R14 · clase I)
- [ ] Cada uso real del browser MCP queda en `verification.md` §9.3: qué inspeccionó, qué detectó y qué cambio provocó (R15 · clase I)
- [ ] Las skills usadas o creadas están en el repositorio y referenciadas desde `verification.md` §9.1 y `.claude/skills/README.md` (R16 · clase I)
- [ ] Los subagentes y comandos propios usados quedan en `verification.md` §9.4, con su propósito y su resultado (R17 · clase I)
  - El de la auditoría de seguridad es de 018.

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
