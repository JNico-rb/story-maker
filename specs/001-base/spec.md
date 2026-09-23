# 001 — BAS · Base técnica

- [x] Spec approved   <- only the user marks this

## Objetivo

Levantar el backend y el frontend sobre el stack decidido, con sus restricciones técnicas hechas comprobables y los supuestos del entorno demostrados, antes de la primera feature.

## Alcance

Cubre:

- el stack y la organización en módulos, con su regla de dependencia comprobada en CI;
- el store: un solo fichero SQLite con Alembic, las conexiones y las tablas de solo inserción;
- la validación de la config y de los ajustes del servidor al arrancar, y la traducción de la clave de OpenRouter;
- el catálogo de criterios, como estructura;
- el puerto de agente con su doble: los desenlaces de una sesión, los hooks y las tools con schema;
- el aislamiento de cada sesión de rol en el workspace del harness;
- la infraestructura del índice: `sqlite-vec`, FTS5, la tabla de vectores y `fastembed` en Windows;
- la escritura solo en el directorio de datos;
- el servidor: la API bajo `/api` y el frontend en el mismo origen, el esquema OpenAPI y el cliente generado;
- la CLI con sus órdenes de operación, y las demostraciones de `architecture.md` §15.3;
- la CI de cada cambio y el workflow de mutación;
- el frontend base con el tema corporativo;
- los entregables de proceso y de Claude Code que no produce ninguna otra spec.

El esquema por columna de todas las tablas de `architecture.md` §14.5, las versiones fijadas y las interfaces externas del backend están en [design.md](design.md).

**Dependencias externas:** OpenRouter con modelos de Anthropic, Langfuse Cloud, GitHub Actions, el Edge instalado en el portátil y la descarga inicial de los modelos de incrustación y de spaCy.

**Fuera de alcance:**

- Los términos del dominio que usan estas piezas: lo que se indexa y cómo se recupera es de 008; los criterios del catálogo, de la spec de cada validador; cada tool y cada hook concretos, de la spec de su rol. 001 entrega el mecanismo, no su contenido.
- Las páginas del frontend: cada una llega con su spec —acceso (002), entrevista (005), progreso (007), mis novelas, lectura, vista previa e impresión (013) y estado de un cambio (015)—, y el diseño solo para escritorio es de 013.
- TLC, `lake build` y la lectura de vuelta de Langfuse en CI, que añaden 006, 009 y 004.
- La lista blanca de tools por rol, las tools integradas desactivadas y el modo de permisos, que son de 003.
- El estimador local de tokens y la cota de la salida de una tool (`max_tool_output`), que son del conteo del guardián de ventana, en 008.
- La inmutabilidad de una versión publicada, que es de 014.

## Requisitos

Todos son **Obligatorio**.

### Módulos y regla de dependencia

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-1 | El backend tiene los módulos `domain`, `store`, `platform`, `harness`, `lint`, las cinco fases de `phases` y `execution` (`architecture.md` §14.2) → el contrato de importación falla en CI si una fase importa otra fase o `execution`, si `domain` importa otro módulo del proyecto o una biblioteca de I/O, si `platform` importa `domain`, o si `store` o `lint` importan algo que no sea `domain`. `execution` es la raíz de composición: importa las fases y `platform` | Obligatorio | A |
| RF-BAS-2 | Un módulo distinto de `platform` importa el Agent SDK → el contrato de importación falla en CI | Obligatorio | A |
| RF-BAS-3 | Aparece en el backend un módulo o carpeta llamado `commons`, `shared` o `utils` → falla una prueba | Obligatorio | T |
| RF-BAS-4 | El frontend sigue Feature-Sliced Design v2.1 con `app`, `pages` y `shared`, sin `widgets` → `steiger` falla en CI si una capa importa una capa superior, si una página se consume sin pasar por su `index` o si `shared` se consume sin pasar por su segmento | Obligatorio | A |
| RF-BAS-5 | Lo que usa una sola página se queda en ella, y `entities` y `features` solo aparecen cuando hay reutilización real (`architecture.md` §14.2) → la revisión de cada página lo comprueba | Obligatorio | I |

### Store

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-6 | Con el directorio de datos vacío, la orden de migrar → crea en él un único fichero SQLite con las tablas, índices y disparadores de [design.md](design.md) §4; repetirla no cambia nada | Obligatorio | T |
| RF-BAS-7 | Toda conexión que abren la API o el worker → tiene `journal_mode` WAL, `busy_timeout` distinto de cero, `foreign_keys` activo —una fila que referencia una inexistente se rechaza— y `sqlite-vec` cargado | Obligatorio | T |
| RF-BAS-8 | Dos procesos escriben a la vez en el mismo fichero, como la API y el worker → los dos terminan su transacción: el segundo espera dentro de `busy_timeout` en vez de fallar | Obligatorio | T |
| RF-BAS-9 | Un `UPDATE` sobre una fila de una tabla de solo inserción (`architecture.md` §14.5) → la base lo rechaza con error y la fila no cambia | Obligatorio | T |
| RF-BAS-10 | Un `DELETE` sobre una fila de una tabla de solo inserción → la base lo rechaza, salvo en `facts` y `canon_cards` cuando la fila es de una versión candidata y la escribió el registro de un capítulo, que es el reemplazo de un registro repetido (`architecture.md` §8.3). Qué filas reemplaza cada registro lo decide 011 | Obligatorio | T |

### Config y ajustes del servidor

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-11 | Al arrancar, la config de `STORY_MAKER_CONFIG` se valida entera → el servidor no arranca, con un error que nombra la clave, ante: una clave desconocida en cualquier nivel; un tipo erróneo; en `retrieval.quotas`, una plaza negativa o no entera, una colección o un consumidor desconocidos, un par ausente o prosa con plazas para un consumidor que no sea el editor ni el linter de repetición; `window_ceiling` por encima de 100.000; un rol de `operation.roles` ausente o desconocido; un modelo con valor en `operation.roles` sin sus cuatro precios, si `operation.pricing` tiene valor; una franja desconocida en `readability_targets`; un id de `thresholds` que no esté en el catálogo de criterios, o uno de `active_criteria` que no sea un criterio de rúbrica del catálogo; `access_token_hours` o `confirmation_minutes` que no sean enteros positivos. Frontera: `window_ceiling` de 100.000 arranca y de 100.001 no | Obligatorio | T |
| RF-BAS-12 | Se leen los criterios activos de la config → son los de rúbrica que lista `active_criteria` más, siempre, los programáticos y `tema-prohibido`, que no se pueden desactivar (`architecture.md` §10.3) | Obligatorio | T |
| RF-BAS-13 | Una cifra sin calibrar (`architecture.md` §15.2) vale `null` en la config → el servidor arranca; leerla falla con un error que nombra la clave y dice que está sin calibrar, y nunca se sustituye por un valor por defecto | Obligatorio | T |
| RF-BAS-14 | El catálogo de criterios (`definitions.md` §6) declara cada criterio con su id, dimensión, niveles, método, bloqueante, acción requerida, origen, parámetros y rúbrica si la tiene → su carga falla si dos criterios tienen el mismo id o si un id no es una etiqueta ASCII en kebab-case. Cada spec añade los criterios de sus validadores; 001, el de `schema-salida`, bloqueante y sin nivel ni acción | Obligatorio | T |
| RF-BAS-15 | Al arrancar se leen del entorno los ajustes del servidor de `definitions.md` §11 → el servidor no arranca, con un error que nombra la variable, si falta una, si `FORMAL_VERIFIER` no es `local` ni `github`, si es `github` y falta `GITHUB_REPOSITORY`, `LEAN_WORKFLOW` o `GITHUB_TOKEN`, o si `JWT_SECRET` tiene menos de 32 caracteres. Frontera: 31 caracteres no arranca y 32 sí | Obligatorio | T |
| RF-BAS-16 | Se abre una sesión de rol → su entorno lleva `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN` con el valor de `OPENROUTER_API_KEY` y `ANTHROPIC_API_KEY` presente y vacía, aunque el proceso del backend tenga otra en su entorno | Obligatorio | T |

### Puerto de agente

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-17 | Las fases abren sus sesiones de rol solo a través del puerto de agente, y existe un doble que implementa el mismo puerto → un guion del doble fija las llamadas a tool, el mensaje final, el uso y los ids de mensaje de cada sesión, sin red ni modelo | Obligatorio | T |
| RF-BAS-18 | Se abre una sesión de rol → corre con el modelo, la salida máxima y los turnos máximos de su rol en `operation.roles`, y con el prompt de sistema que le pasa quien la abre | Obligatorio | T |
| RF-BAS-19 | Una sesión termina bien → el puerto devuelve el desenlace `completada`, con el uso exacto de la sesión entera —tokens de entrada, de salida, de lectura de caché y de escritura de caché—, su duración y la lista de ids de mensaje. El uso se toma solo del resultado final de la sesión, nunca del uso por turno, que por OpenRouter llega a cero | Obligatorio | T |
| RF-BAS-20 | Una sesión agota `roles.<rol>.max_turns` → el puerto devuelve el desenlace `turnos agotados`, también con su uso exacto, aunque el SDK lance su error después del resultado final | Obligatorio | T |
| RF-BAS-21 | Una sesión pasa de `max_agent_seconds` → el puerto la interrumpe, cierra su subproceso y devuelve el desenlace `tiempo agotado` (`architecture.md` §7.6) | Obligatorio | T |
| RF-BAS-22 | Quien abrió una sesión la corta mientras corre → el puerto la interrumpe, cierra su subproceso y devuelve el desenlace `cortada`. Cuándo se corta lo decide cada spec: la cancelación, 007 | Obligatorio | T |
| RF-BAS-23 | El proveedor o el transporte fallan, agotados los reintentos del propio SDK → el puerto devuelve el desenlace `fallo de infraestructura`, distinto de los anteriores | Obligatorio | T |
| RF-BAS-24 | Una sesión registra hooks antes y después de cada tool → el de antes puede denegar la llamada con un motivo, que el modelo recibe como resultado, y entonces la tool no se ejecuta; el de después puede sustituir la salida que lee el modelo. El doble pasa sus llamadas guionizadas por los mismos hooks y manejadores, en el mismo orden que el SDK | Obligatorio | T |
| RF-BAS-25 | Una tool en proceso se declara con un modelo de datos, del que sale su JSON Schema → si el modelo la llama con una entrada que no cumple el schema, el manejador la rechaza sin ningún efecto, el modelo recibe el error de validación y la sesión sigue; la llamada cuenta como fallo del validador `schema-salida`. Con una entrada válida cuenta como acierto | Obligatorio | T |
| RF-BAS-26 | Una tool entrega una salida válida → la entrega queda en las salidas de la sesión, en memoria, y la tool no escribe nada en SQLite (`architecture.md` §7.4) | Obligatorio | T |

### Workspace del harness

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-27 | Se abre una sesión de rol → corre con `cwd` en el workspace del harness y carga su `CLAUDE.md` y sus skills, y no el `CLAUDE.md` de ningún directorio padre: ni el de desarrollo de la raíz ni el personal del usuario | Obligatorio | T |
| RF-BAS-28 | Se abre una sesión de rol → solo arranca los servidores MCP que declara, nunca los del `.mcp.json` de la raíz | Obligatorio | T |
| RF-BAS-29 | Se abre una sesión de rol → la telemetría y la memoria automática del CLI están apagadas, y su directorio de configuración está dentro del directorio de datos | Obligatorio | T |

### Índice

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-30 | Con `sqlite-vec` cargado → la distancia coseno que calcula en SQL sobre vectores guardados en la tabla de vectores, en filas ya filtradas por una consulta normal, coincide con la esperada | Obligatorio | T |
| RF-BAS-31 | Las tablas FTS5 de CanonCards y de párrafos usan el tokenizador `unicode61 remove_diacritics 2` (`architecture.md` §6.9) → `MATCH` con «cancion» encuentra una fila con «Canción», y al revés | Obligatorio | T |
| RF-BAS-32 | La tabla de vectores es una tabla normal con clave (huella, modelo) → insertar un segundo vector para un par que ya existe falla | Obligatorio | T |
| RF-BAS-33 | Una transacción escribe una tabla normal, una tabla FTS5 y la de vectores, y se deshace → ninguna de las tres conserva la fila: el índice puede escribirse en la misma transacción que la story bible (`architecture.md` §6.11) | Obligatorio | T |
| RF-BAS-34 | El productor de vectores recibe un identificador de modelo y unos textos → devuelve un vector por texto, con la dimensión del modelo e igual para el mismo texto; la caché del modelo queda en el directorio de datos | Obligatorio | T |

### Directorio de datos y servidor

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-35 | Cualquier ruta en la que escribe el backend —el fichero SQLite, la configuración del CLI del SDK, las cachés de modelos, la salida de Playwright MCP y los PDF— → cae dentro de `STORY_MAKER_DATA_DIR`, y una ruta que saldría de él se rechaza; una prueba de integración con el doble no deja ningún fichero fuera | Obligatorio | T |
| RF-BAS-36 | La orden de arrancar el servidor → lanza uvicorn sin recarga automática (`architecture.md` §14.1) | Obligatorio | T |
| RF-BAS-37 | Con el servidor en marcha → la API responde bajo `/api`; una ruta fuera de `/api` que no es un fichero del frontend compilado devuelve su página de entrada, y una ruta desconocida bajo `/api` responde 404 sin devolverla. En desarrollo, el servidor de Vite reenvía `/api` al backend | Obligatorio | T |
| RF-BAS-38 | Una petición cuyo cuerpo o parámetros no cumplen su schema → 422 con los errores de validación (`architecture.md` §14.3) | Obligatorio | T |
| RF-BAS-39 | Una orden exporta el esquema OpenAPI sin arrancar el servidor, y el cliente TypeScript de `shared/api` se genera de él; los dos se commitean → CI los regenera y falla si difieren de los del repositorio | Obligatorio | A |

### CLI y demostraciones de entorno

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-40 | La CLI del backend tiene las órdenes de operación —migrar, arrancar el servidor, exportar el esquema OpenAPI, comprobar el entorno y lanzar la mutación—. La de comprobar el entorno → ejecuta cada comprobación de RF-BAS-41 a RF-BAS-43, dice cuál pasa y por qué falla cada una de las que no, y termina con código distinto de cero si falla alguna | Obligatorio | T |
| RF-BAS-41 | En el portátil de desarrollo, la orden de comprobaciones → pasa todas: el CLI que empaqueta el Agent SDK arranca bajo Smart App Control; una sesión real contra OpenRouter corre con el modelo y la salida máxima de su rol, usa una tool en proceso, un hook que deniega, uno que sustituye la salida, una skill y el workspace, carga solo el `CLAUDE.md` del workspace, deja su configuración en el directorio de datos y devuelve el uso de la sesión; spaCy con su modelo de español, `sqlite-vec` y `onnxruntime` cargan, y `fastembed` produce un vector; Playwright maneja el Edge instalado sin interfaz, incluido `page.pdf` con índice y etiquetas; Playwright MCP navega así desde una sesión del SDK; con uvicorn en marcha, una petición lanza los dos subprocesos del sistema, el CLI del SDK y un proceso como el del worker; y los ids de mensaje de OpenRouter empiezan por `gen-` y su consulta de coste por generación los resuelve | Obligatorio | D |
| RF-BAS-42 | En el portátil de desarrollo, una sesión real cortada por tiempo o por quien la abrió → no deja ningún subproceso del CLI vivo | Obligatorio | D |
| RF-BAS-43 | Un workflow mínimo de GitHub Actions con Lean se dispara con `workflow_dispatch` y `return_run_details`, se sondea hasta que concluye y deja su artefacto → se mide su tiempo de ida y vuelta frente a la estimación de 1 a 3 minutos. El verificador remoto completo es de 009 | Obligatorio | D |

Si una demostración falla, se reabre la decisión que la usa, con su motivo, y el hallazgo queda en el registro de iteraciones (`verification.md` §8).

### CI

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-44 | Cada cambio → GitHub Actions ejecuta Ruff, mypy estricto, las pruebas del backend —unitarias, de integración, de propiedades, de contrato y doradas—, la comprobación de que las migraciones cubren los modelos, el TypeScript estricto, ESLint, el build de producción del frontend, los contratos de importación, `steiger`, la deriva del cliente generado y `detect-secrets`; la integración falla si falla cualquiera | Obligatorio | T |
| RF-BAS-45 | CI corre sin clave del proveedor → toda prueba abre sus sesiones con el doble; una prueba que intentara abrir una sesión real falla | Obligatorio | T |
| RF-BAS-46 | Las pruebas de mutación no corren en cada cambio → la orden de mutación y un workflow programado las lanzan sobre los cuatro objetivos de `verification.md` §3.7 —el motor de políticas y la normalización de prohibidas (003), la validación del brief (005), los validadores del hook de capítulo (011) y el gate (014)— a medida que existen, y dan los mutantes que sobreviven en cada ruta de rechazo | Obligatorio | T |

### Frontend base

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-47 | El frontend compila con Vite, React, TypeScript estricto y Tailwind CSS, con `pnpm` 10.x → su build de producción es el que sirve FastAPI (RF-BAS-37) | Obligatorio | A |
| RF-BAS-48 | La imagen corporativa sale del logo de `images/`: nombre, logotipo, paleta y tipografía, como tokens del tema en `app` → se aplica igual en todas las páginas. Cada spec que añade una página lo inspecciona con el browser MCP y deja su fila en `verification.md` §9.3 | Obligatorio | I |

### Entregables de proceso

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BAS-49 | Toda variable de los ajustes del servidor (`definitions.md` §11) aparece en `.env.example`, y ninguna con un valor real; git ignora `.env` → una prueba compara las variables de `.env.example` con las de los ajustes, y `detect-secrets` pasa | Obligatorio | T |
| RF-BAS-50 | El README de la raíz → describe el repositorio, cómo instalar y arrancar backend y frontend en local, y dónde vive cada entregable del encargo | Obligatorio | I |
| RF-BAS-51 | ADR 0003 → dice qué se decidió construir y por qué antes de escribir código: es la spec inicial del encargo | Obligatorio | I |
| RF-BAS-52 | `architecture.md` §16 → recoge cada decisión de diseño relevante con sus opciones, su criterio y su elección: es el registro de trade-offs | Obligatorio | I |
| RF-BAS-53 | Los diagramas de la arquitectura del harness (`architecture.md` §2, §8.1 y §9.5), del esquema SQLite (§14.5) y la tabla de validadores con su punto de ejecución (§10.2) → están en los docs, y el diagrama del esquema tiene las mismas tablas y relaciones que la migración. El de la máquina de estados de TLA+ es de 006 | Obligatorio | I |
| RF-BAS-54 | Al cerrar 001 → la cabecera de `verification.md` §9 lleva el explainer del desarrollo guiado por specs —docs → spec → plan → pruebas → código—, y la de `architecture.md` §7.4, el de las tools con schema validado, como asigna la lista de explainers del README | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Tipado estricto: mypy estricto en todo el backend; modelos Pydantic en los bordes —entrada HTTP, config, ajustes, entrada de cada tool—; TypeScript estricto en el frontend | A |
| RNF-2 | Análisis estático: Ruff con las reglas de seguridad (`S`) y `detect-secrets` en cada cambio | A |
| RNF-3 | Las pruebas viven dentro de cada slice —las de extremo a extremo, en `execution`—, y sus nombres dicen el comportamiento (`workflow/4-code.md`) | I |

## Restricciones

| # | Restricción | Origen | Clase |
|---|---|---|---|
| R1 | Backend en Python 3.12 con FastAPI servida por uvicorn, Pydantic v2 y SQLAlchemy 2; dependencias con `uv`; Ruff y mypy estricto. 3.12 y no una posterior, porque Smart App Control bloquea el wheel de spaCy para 3.14 | `architecture.md` §14.1 | I |
| R2 | SQLite en WAL con migraciones Alembic desde el principio; `sqlite-vec` y FTS5 para el índice, en el mismo fichero que la story bible; `fastembed` para los vectores, local y sin servicio | §6.12, §14.1 | I |
| R3 | Harness sobre el Claude Agent SDK para Python, que ejecuta como subproceso el CLI empaquetado, con OpenRouter como proveedor y modelos de Anthropic; orquestación propia | §7.2, §14.1 | I |
| R4 | Langfuse v4 en Langfuse Cloud UE; FastMCP dentro de FastAPI; Playwright sobre el Edge instalado y pypdf; spaCy con modelo de español; bcrypt y PyJWT; Lean 4 con Lake; TLA+ con TLC sobre un JDK Temurin portable; GitHub Actions; `pip-audit`, `pnpm audit` y `detect-secrets` | §14.1 | I |
| R5 | Frontend con Vite, React, TypeScript estricto y Tailwind CSS; dependencias con `pnpm` 10.x, porque la 11 no arranca sin el Visual C++ Redistributable | §14.1; entorno | I |
| R6 | El portátil de desarrollo es Windows sin administrador, sin Visual C++ Redistributable y con Smart App Control: el runtime de Visual C++ va en espacio de usuario con `msvc-runtime`, los enlaces simbólicos de la caché de HuggingFace se desactivan y Lean no corre en local | §6.12, §15.3; ADR 0004 | D |
| R7 | SQLAlchemy es síncrono dentro del worker; las sesiones de rol son asíncronas y pueden ir en paralelo | §14.4 | I |
| R8 | Ninguna tool pide ni devuelve contexto: la ventana llega cerrada | §6.10, §7.4 | I |
| R9 | Las constantes del encargo y del dominio —10 capítulos de 1.000 a 1.500 palabras, el objetivo de cada extensión, de 3 a 6 beats por capítulo y el orden de una consecuencia como mucho 3— viven en `domain`, no en config | §1.2; `definitions.md` §11 | I |
| R10 | Código, tablas, API, MCP y JSON en inglés, con los identificadores de `definitions.md` §12; docs, prompts e interfaz en español. Excepción: los nombres que se ven en Langfuse son etiquetas en español, ASCII y kebab-case | `definitions.md` §12; §16 «Nombres» | I |
| R11 | Los commits generados por un agente se marcan como tales | `verification.md` §4.7 | I |
| R12 | `CLAUDE.md` en la raíz, cuidado y legible: es parte del examen | Encargo, «Claude Code» | I |
| R13 | `.claude/` commiteada con los ficheros de memoria y los comandos propios | Encargo, «Claude Code»; `verification.md` §9.5 | I |
| R14 | `.mcp.json` incluye un servidor MCP de inspección de browser, Playwright MCP con versión fijada y el Edge instalado, para que Claude Code abra la lectura web y la verifique; sus instantáneas van a `.playwright-mcp/`, ignorada por git | Encargo, «Claude Code»; §14.4; `verification.md` §9.2 | I |
| R15 | Cada uso real del browser MCP queda en `verification.md` §9.3: qué inspeccionó, qué detectó y qué cambio provocó | Encargo, «Claude Code» | I |
| R16 | Las skills usadas o creadas están en el repositorio y referenciadas desde `verification.md` §9.1 y `.claude/skills/README.md` | Encargo, «Claude Code» | I |
| R17 | Los subagentes y comandos propios usados quedan en `verification.md` §9.4, con su propósito y su resultado. El de la auditoría de seguridad es de 018 | Encargo, «Claude Code» | I |

## Docs de referencia

- `architecture.md` §1.2, §2, §6.5 (validación de las cuotas), §6.6, §6.9, §6.10, §6.11, §6.12, §7.3, §7.4, §7.5, §7.6, §8.1, §8.3, §9.5, §9.7 (servir la lectura), §10.2, §10.3, §10.5 (protocolo remoto), §11.2, §11.5, §11.6, §12.1, §13.6, §14.1–§14.5, §15.2, §15.3 y §16.
- `definitions.md` §5 (componentes de código, `SesionDeRol`), §6 (`CatalogoDeCriterios`), §11 y §12.
- `verification.md` §3.1, §3.2, §3.5, §3.7, §3.9, §3.10, §4.3, §4.7, §5, §8 y §9.
- [ADR 0003](../../docs/adr/0003-pivote-al-encargo.md), [ADR 0004](../../docs/adr/0004-lean-en-github-actions.md), el README de la raíz («Explainers») y `workflow/4-code.md`.
