# 016 — MCP · Servidor MCP

- [x] Spec approved   <- only the user marks this

## Objetivo

Que cualquier cliente MCP consulte y descargue las novelas del cliente autenticado, y pida y confirme un cambio sobre ellas, sin ver nunca las de otro.

## Alcance

Cubre el servidor MCP montado en la aplicación, su identidad con el `TokenDeAcceso`, las cinco tools de lectura, las dos de escritura con confirmación, sus schemas, la traza de cada llamada, el audit log de las escrituras, el aislamiento entre clientes por MCP y el README de conexión. FastMCP, su montaje y su verificador del token: [001 design.md](../001-base/design.md) §11.

Depende de 002, 004, 013, 014 y 015.

**Fuera de alcance:**

- La interpretación de un cambio y su confirmación: son de 015, y MCP las expone sin cambiarlas.
- La máscara de cada novela y la unión de máscaras de una llamada que toca varias: 004.
- `Confirmation.tla`, la especificación TLA+ de la única escritura que expone MCP: 006.
- Claude Desktop y Claude Code como clientes: no se demuestran, y el README explica solo MCP Inspector (`architecture.md` §13.2).
- Confirmar con la elicitation del cliente: se eligió el código en dos pasos, que funciona con cualquier cliente MCP (`architecture.md` §16).

## Requisitos

Todos son **Obligatorio**.

### Servidor e identidad

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MCP-1 | `/mcp` → un servidor MCP con transporte HTTP, montado en la aplicación FastAPI, que arranca y se detiene con ella. Un cliente MCP lista exactamente siete tools: `list_novels`, `get_chapter`, `list_versions`, `query_story_bible`, `download_novel`, `request_change` y `confirm_change` | Obligatorio | T |
| RF-MCP-2 | Una petición a `/mcp` sin token, con el token caducado, con la firma inválida o con un `aud` o un `iss` que no son los del servidor → 401. Con un `TokenDeAcceso` válido, firmado en HS256, cada tool actúa como el cliente de su `sub` | Obligatorio | T |
| RF-MCP-3 | Cada tool → tiene un schema validado. Una entrada que no lo cumple da un error de validación, sin efecto. Una prueba de contrato fija el schema de cada una | Obligatorio | T |

### Tools de lectura

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MCP-4 | `list_novels` → las novelas del cliente con lo mismo que `GET /api/novels` (013): su estado derivado y su versión vigente | Obligatorio | T |
| RF-MCP-5 | `get_chapter` con una novela, el número de una versión publicada y un capítulo de 1 a 10 → su título, su texto y su marca de cambiado en esa versión | Obligatorio | T |
| RF-MCP-6 | `list_versions` con una novela → sus versiones publicadas, cada una con su número, su fecha de publicación y su lista de capítulos cambiados | Obligatorio | T |
| RF-MCP-7 | `query_story_bible` con una novela y el número de una versión publicada → lo mismo que su story bible por la API (013): personajes, lugares, hechos y cronología | Obligatorio | T |
| RF-MCP-8 | `download_novel` con una novela y el número de una versión publicada → el PDF guardado al publicarla, como recurso incrustado, byte a byte igual al fichero; no vuelve a exportar | Obligatorio | T |
| RF-MCP-9 | Una novela, una versión o un capítulo que no existen o que son de otro cliente → el mismo error de inexistente en todos los casos, sin revelar que existen | Obligatorio | T |
| RF-MCP-10 | Tras cualquier llamada a una tool de lectura → ninguna tabla de SQLite ha cambiado | Obligatorio | T |

### Tools de escritura

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MCP-11 | `request_change` con una novela, una selección y una petición → hace la interpretación de 015, con su propia traza, y devuelve el id de la solicitud, la propuesta —los hechos que cambian y los capítulos afectados— y un código de confirmación de un solo uso que caduca a los 15 minutos. Rechaza en los mismos casos que la API: sin versión publicada; con la policy que deniega o los intentos agotados, con la solicitud guardada `rejected` y su id y motivo; y con el proveedor o Langfuse caídos, sin guardar nada | Obligatorio | T |
| RF-MCP-12 | `confirm_change` con el id de una solicitud propia `proposed` sin caducar y su código → encola la ejecución de cambio como la confirmación de 015 y devuelve su `run_id` y su posición. Es la única tool que encola | Obligatorio | T |
| RF-MCP-13 | Caso RT3: `confirm_change` sobre la solicitud de otro cliente → error de inexistente; con un código que no es el de esa solicitud → código inválido; con uno caducado o ya usado → la solicitud ya no está `proposed`. En los tres, sin efecto | Obligatorio | T |
| RF-MCP-14 | Cada llamada a `request_change` o `confirm_change` → deja una entrada en el audit log con origen `mcp_write`, la tool, la decisión `allow` si devolvió una propuesta o encoló, o `deny` si se rechazó, y su motivo | Obligatorio | T |

### Observabilidad y aislamiento

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MCP-15 | Cada llamada a una tool → es una traza `mcp` en Langfuse (004), en la sesión de la novela si toca una sola y sin sesión si toca varias o ninguna, y con la máscara de la novela que toca o la unión de las máscaras si toca varias (004). Con el doble de Langfuse, `list_novels` sobre dos novelas no exporta sin máscara ningún dato personal de ninguna de las dos | Obligatorio | T |
| RF-MCP-16 | Caso RT5: el cliente B, con su token → `list_novels` solo devuelve las suyas, y las demás tools, con los ids de una novela, una versión, un capítulo o una solicitud del cliente A, responden como inexistentes. Una prueba recorre las siete tools con un fixture de A que tiene un recurso de cada tipo | Obligatorio | T |

### README y explainer

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MCP-17 | El README de la raíz → explica cómo conectar MCP Inspector a `/mcp` con transporte HTTP, cómo obtener el token con `POST /api/auth/login` y cómo pasarlo en la cabecera de autorización. No explica ningún otro cliente | Obligatorio | I |
| RF-MCP-18 | Siguiendo solo el README → MCP Inspector se conecta al servidor local, lista las siete tools, llama a las cinco de lectura y pide y confirma un cambio | Obligatorio | D |
| RF-MCP-19 | Al cerrar 016 → la cabecera de `architecture.md` §13.2 lleva el explainer de MCP: el servidor de la plataforma y el browser MCP | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Ni el token ni el código de confirmación salen en un log ni en una traza | T |

## Restricciones

| # | Restricción | Origen |
|---|---|---|
| R1 | FastMCP con la versión fijada en [001 design.md](../001-base/design.md) §1; su aplicación HTTP se monta con su lifespan, que es obligatorio | `architecture.md` §13.2 y §14.1 |

## Docs de referencia

- `architecture.md` §9.5, §11.4, §12.1, §12.5, §13.1, §13.2, §14.3 y §16 («Confirmación de escritura MCP», «Caducidades», «Autenticación»).
- `definitions.md` §7 (`DecisionDePolitica`), §8 (`Traza`, `Mascara`), §10 (`TokenDeAcceso`, `ServidorMCP`, `Confirmacion`) y §12.
- `verification.md` §3.8 (tools del servidor MCP), §4.9 (RT3 y RT5) y §5 («Autenticación y aislamiento entre clientes», «Servidor MCP: schemas, solo lectura y confirmación»).
