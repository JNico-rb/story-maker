# 013 — Lectura y PDF

> Carril: D · Depende de: 009-story-bible-y-versiones · Estado: borrador

## Objetivo

Renderizar una versión (candidata o publicada) como `VistaDeVersion` y como PDF, servir ambos, exponer por la API lo que la lectura web necesita, y ofrecer por CLI la novela de ejemplo y la exportación de un PDF. La `VistaDeVersion` es el único render: la usan el PDF y el revisor visual (017). Cubre del encargo la entrega web y PDF (`verification.md` §5, C.4, 2.1–2.4, 2.9, 2.10, R.1).

## Alcance

- **`VistaDeVersion`** (HTML de servidor, Jinja2) de una versión, candidata o publicada: portada con título, destinatario y dedicatoria; página de **novedades** si la versión tiene capítulos cambiados, con un enlace interno a cada uno; índice navegable de los 10 capítulos, con la marca «cambiado en vN» en los que corresponda; los capítulos; ficha de personajes y lugares con enlaces internos a los capítulos donde aparece cada uno.
- **Token de vista**: lo firma el servidor con `JWT_SECRET`, vale solo para la versión a la que se emite, caduca con `operation.session_timeout_seconds` y lleva `aud=view_token`. `GET /view/versions/{version_id}?token=...` lo exige y sirve la `VistaDeVersion`.
- **PDF**: generado desde la `VistaDeVersion` con Playwright sobre el Edge instalado; guardado por versión en el directorio de datos; servido tal cual por `GET /api/novels/{id}/versions/{v}/pdf`.
- **`pdf-enlaces`**: comprueba con `pypdf` que el PDF tiene los 10 capítulos y que los enlaces internos del índice, de la página de novedades y de la ficha resuelven a un ancla existente.
- **API de lectura**: `GET /api/novels/{id}/versions` (historial publicado con sus capítulos cambiados) y `GET /api/novels/{id}/versions/{v}` (detalle de una versión publicada: portada, índice, capítulos y ficha, para la SPA).
- **CLI**: `example <brief.json>` (brief → novela → PDF, con `--email` de un cliente ya registrado como propietario, deja el PDF en la ruta que recibe) y `export-pdf <novela> <v>` (regenera y guarda el PDF de una versión ya publicada). `ejemplos/novela-ejemplo.pdf` es el resultado commiteado de `example` sobre el brief del README.

## Fuera de alcance

- Story bible, estados y ciclo de vida de la versión, capítulos cambiados al publicar, versión vigente → 009-story-bible-y-versiones. Esta spec solo lee lo que 009 escribe.
- Orden de las etapas del gate, cuándo se llama a `pdf-enlaces` dentro del gate y la atribución de sus fallos a capítulos → 012-gate-de-publicacion; 012-C18 ya cubre que el PDF es la última etapa.
- Identidad, `TokenDeAcceso` y la regla de propiedad (lo ajeno como inexistente) → 002-autenticacion; esta spec solo añade la comprobación propia del token de vista, distinto del `TokenDeAcceso`.
- El revisor visual y su navegación de la `VistaDeVersion` con Playwright MCP → 017-revision-visual; esta spec entrega la vista que él consume.
- Pedir un cambio desde la lectura, capítulos afectados y regeneración → 014-cambios-del-lector. `query_story_bible` y `download_novel` por MCP → 015-servidor-mcp.
- La SPA de lectura (portada, índice, ficha, selector de versión, «cambiado en vN» en pantalla) → 026-lectura (frontend); esta spec entrega el JSON que consume.
- Cinco briefs de evaluación y `evals run|table` → 020-evals. `ejemplos/novela-ejemplo.pdf` es su brief `ejemplo`, generado aquí.

## Comportamiento observable

**Convenciones.** N es una novela con V1 publicada (sin capítulos cambiados) y V2 publicada (copia de V1, con los capítulos 3 y 7 cambiados y ficha con Toby/Nala como en 009). K es una candidata de N sin publicar. A es el cliente dueño de N.

### `VistaDeVersion`

#### 013-C01 — Portada, índice y ficha de una versión sin capítulos cambiados (T)
- **Entrada:** `GET /view/versions/{V1}?token=<token de vista válido para V1>`.
- **Salida:** 200, HTML con la portada (título, destinatario y dedicatoria del brief de N), sin página de novedades, un índice con un ancla a cada uno de los 10 capítulos, los 10 capítulos, y una ficha con un enlace por cada capítulo donde aparece cada personaje o lugar (por `UsoDeHecho` o por evento registrado).

#### 013-C02 — Página de novedades y marca de cambio (T)
- **Entrada:** `GET /view/versions/{V2}?token=<token de vista válido para V2>`.
- **Salida:** 200, HTML con una página de novedades que enlaza internamente a los capítulos 3 y 7, y el índice marca esos dos capítulos como «cambiado en v2» y ninguno más.

#### 013-C03 — Una entidad sin capítulo aparece en la ficha sin enlaces (T)
- **Entrada:** una versión con un personaje que no tiene `UsoDeHecho` ni evento registrado en ningún capítulo.
- **Salida:** la ficha incluye a ese personaje, con la lista de enlaces vacía.

#### 013-C04 — La `VistaDeVersion` sirve también una candidata (T)
- **Entrada:** `GET /view/versions/{K}?token=<token de vista válido para K>`.
- **Salida:** 200, con el mismo contenido que 013-C01 para el estado actual de K.

#### 013-C05 — Dos versiones de la misma novela no se mezclan (T)
- **Entrada:** las vistas de V1 y de V2 de N.
- **Salida:** el contenido de cada una es el de su propia versión: la ficha de V1 nombra a «Toby» y la de V2 a «Nala», y cada una enlaza solo a sus propios capítulos.

### Token de vista

#### 013-C06 — El token de vista se emite firmado y con sus reclamaciones (T)
- **Entrada:** se emite el token de vista de V1.
- **Salida:** JWT HS256 firmado con `JWT_SECRET`, con `aud=view_token`, un identificador de V1 y `exp` = ahora + `operation.session_timeout_seconds`.

#### 013-C07 — Un token de vista inválido responde 401 (T)
Cada fila usa un token de vista válido de V1 salvo que diga otra cosa:

| Token | Resultado |
|---|---|
| Presentado en `GET /view/versions/{V2}` (otra versión) | 401 |
| Con `aud=access_token` (un `TokenDeAcceso`, no de vista) | 401 |
| Emitido y usado tras `operation.session_timeout_seconds` | 401 |
| Con la firma alterada | 401 |
| Sin `token` en la query | 401 |

En cada fila, la respuesta no revela si la versión existe.

### PDF

#### 013-C08 — El PDF se genera desde la `VistaDeVersion` con sus 10 capítulos (T)
- **Entrada:** generación del PDF de V1.
- **Salida:** un fichero PDF con 10 capítulos y sus marcadores (`outline`) y etiquetado (`tagged`); su contenido de texto corresponde al de los capítulos de V1.

#### 013-C09 — `pdf-enlaces` valida los enlaces internos (T)
- **Entrada:** el PDF de V2 (con página de novedades).
- **Salida:** `pdf-enlaces` da 1/1: el enlace del índice a cada capítulo, el de la página de novedades a los capítulos 3 y 7, y el de la ficha a cada capítulo donde aparece una entidad resuelven a su ancla.

#### 013-C10 — `pdf-enlaces` falla ante un enlace que no resuelve (T)
- **Entrada:** un PDF con un enlace interno a un ancla que no existe (fabricado para la prueba).
- **Salida:** `pdf-enlaces` da 0/1, con el enlace que no resuelve en el detalle.

#### 013-C11 — El PDF se guarda por versión y se sirve tal cual (T)
- **Entrada:** el PDF de V1 generado y guardado; después, `GET /api/novels/{N}/versions/1/pdf` con el token de A.
- **Salida:** 200, `Content-Type: application/pdf`, los mismos bytes que se guardaron.

#### 013-C12 — Sin PDF guardado, la ruta responde 404 (T)
- **Entrada:** `GET /api/novels/{N}/versions/1/pdf` para una versión publicada cuyo PDF aún no se ha guardado (fabricado para la prueba).
- **Salida:** 404.

### API de lectura

#### 013-C13 — Listado de versiones publicadas (T)
- **Entrada:** `GET /api/novels/{N}/versions` con el token de A.
- **Salida:** 200, con V1 y V2 en orden ascendente de número, cada una con su número, su fecha de publicación y sus capítulos cambiados ([] para V1, [3, 7] para V2). Ninguna candidata aparece.

#### 013-C14 — Detalle de una versión publicada (T)
- **Entrada:** `GET /api/novels/{N}/versions/2` con el token de A.
- **Salida:** 200, con la portada, el índice (con la marca de cambio de 013-C02), los 10 capítulos con su texto y la ficha con sus enlaces, todo de V2.

#### 013-C15 — Lo que no existe, lo ajeno y lo mal formado (T)
Con B, un cliente que no posee N:

| Petición | Resultado |
|---|---|
| `GET /api/novels/{N}/versions/3` (no existe) por A | 404 |
| `GET /api/novels/{N}/versions/1` por B | 404, idéntico al de una novela inexistente |
| `GET /api/novels/{N}/versions` por B | 404 |
| `GET /api/novels/{N}/versions/0` o `.../uno` | 422 |
| `GET /api/novels/{N}/versions/1` (candidata K, sin publicar, con ese número) | no aplica: los números solo existen en lo publicado; se usa 404 |

### CLI

#### 013-C16 — `example` produce la novela y su PDF (T)
- **Entrada:** `story-maker example ejemplos/briefs/ejemplo.json --email <cliente registrado>`, con el doble determinista del puerto de agente.
- **Salida:** una novela nueva, propiedad del cliente de `--email`, con una versión publicada y su PDF guardado en la ruta que recibe la orden.

#### 013-C17 — `export-pdf` regenera el PDF de una versión publicada (T)
- **Entrada:** `story-maker export-pdf <novela> 1`, con la versión 1 ya publicada y su PDF existente.
- **Salida:** el PDF se regenera desde la `VistaDeVersion` de V1 y sustituye al guardado, con el mismo contenido que 013-C08; no se repite el gate ni cambia ningún dato de la versión.

#### 013-C18 — `export-pdf` sobre lo que no existe o no está publicado (T)
- **Entrada:** `export-pdf` con una novela inexistente, o con una versión sin publicar.
- **Salida:** error con el motivo, y ningún fichero se escribe ni se sobrescribe.

#### 013-C19 — La novela de ejemplo real (D, al final)
- **Entrada:** `story-maker example` sobre el brief del README, con el modelo real.
- **Salida:** `ejemplos/novela-ejemplo.pdf`, con 10 capítulos, pasa `pdf-enlaces`. Es el fichero que se commitea.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 013-I1 | Todo enlace interno del PDF y de la `VistaDeVersion` (índice, novedades, ficha) resuelve a un ancla que existe en el mismo documento | T | 013-C01, 013-C02, 013-C09, 013-C10 |
| 013-I2 | El token de vista solo vale para la versión a la que se emitió, nunca como `TokenDeAcceso`, y caduca con `operation.session_timeout_seconds` | T | 013-C06, 013-C07 |
| 013-I3 | La `VistaDeVersion` y el detalle de la API de una versión no muestran nada de otra versión ni de otra novela | T | 013-C05, 013-C14, 013-C15 |
| 013-I4 | El backend solo escribe el PDF de una versión en `STORY_MAKER_DATA_DIR`; la única excepción es `example`, que lo escribe en la ruta que recibe | T | 013-C11, 013-C16. Refuerzo de `verification.md` §12.6 |
| 013-I5 | Con los mismos datos de versión, la `VistaDeVersion` y el PDF que produce son iguales | T | Genera dos veces la vista de V1 y compara el HTML; genera dos veces su PDF y compara el resultado de `pdf-enlaces` y el número de capítulos |

## Scores y trazas

No aplica en esta spec: el render y el servicio de PDF no ejecutan sesiones de rol ni validadores con score propio salvo `pdf-enlaces`, cuyo resultado y score los deja el gate al invocarlo (012-gate-de-publicacion, `architecture.md` §13.1).

## Docs referenciados

- `architecture.md`:
  - §14.1 (contenido de la lectura web), §14.2 (`VistaDeVersion`, token de vista, PDF, dos consumidores);
  - §11 punto 3–4 (`revision-visual` y PDF como etapas del gate, consumidores de esta spec);
  - §12.6 (solo se escribe en `STORY_MAKER_DATA_DIR`, salvo `example`);
  - §15.7 (rutas `/api/novels/{id}/versions[...]`, `/view/versions/{id}`, 401/404/422);
  - §15.4/§15.5 (`JWT_SECRET`, `operation.session_timeout_seconds`);
  - §15.8 (`example`, `export-pdf`);
  - §15.9 (propiedad de `render/`);
  - §18: «Vista de versión» (un solo render con token de vista), «Generación del PDF» (Playwright sobre Edge, comprobado con `pypdf`).
- `definitions.md`:
  - §3 (Version, capítulo cambiado), §2 (Ficha de personajes y lugares, cómo aparece una entidad), §10 (`VistaDeVersion`, token de vista, distinto de `TokenDeAcceso`), §12.1 (`view_token`).
- `verification.md`:
  - §2 (clases), §5 (C.4, 2.1–2.4, 2.9, 2.10, R.1), §8 H3 (Chromium descarta enlaces a anclas inexistentes → `pdf-enlaces`), §9.2–§9.3 (Playwright MCP y `http://127.0.0.1`, aplicable al revisor visual que consume esta vista).
- `specs/backend/002-autenticacion.md` (identidad y propiedad de `/api`, sin duplicar sus casos).
- `specs/backend/009-story-bible-y-versiones.md` (story bible, estados y capítulos cambiados que esta spec lee, sin duplicar sus casos).
- `backend/AGENTS.md`: propiedad de la 013 — `render/`, `api/` (versions, PDF, `/view`), `cli.py` (`example`, `export-pdf`), `ejemplos/novela-ejemplo.pdf`.

## Decisiones para §18 (sin doc previo)

- **Orden del listado de versiones**: ascendente por número (v1, v2, …), lo más simple, coherente con la historia lineal de 009.
- **Forma del detalle JSON de `GET /api/novels/{id}/versions/{v}`**: los mismos bloques que la `VistaDeVersion` (portada, índice, capítulos, ficha), como estructura de datos en vez de HTML, porque es lo único que la SPA necesita y evita un segundo modelo.
- **`export-pdf`**: regenera desde la `VistaDeVersion` guardada (sin repetir el gate ni `pdf-enlaces` como parte del gate), porque exportar de nuevo un PDF ya publicado no debe revalidar una versión que ya pasó.
- **Candidata con el mismo número que una publicada** (013-C15, última fila): las candidatas no tienen número (009-I1); la ruta de versión publicada por número nunca la alcanza, así que se trata como inexistente. Ninguna decisión nueva, solo la consecuencia de 009.

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Quién dispara el gate y la atribución de `pdf-enlaces`? | 012; esta spec solo entrega la función que produce el PDF y la que lo valida | `architecture.md` §11, `backend/AGENTS.md` |
| ¿La `VistaDeVersion` distingue candidata de publicada? | No en su contenido: renderiza el estado actual de la versión que se le pide: la exigencia de token de vista ya limita quién puede pedirla | §14.2 |
| ¿Dónde vive el JSON de la SPA si no es la `VistaDeVersion`? | En el detalle de la API (013-C14), pensado para 026-lectura, nunca HTML | Decisión para §18 (arriba) |
