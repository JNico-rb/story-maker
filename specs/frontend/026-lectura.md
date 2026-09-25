# 026 — Lectura

> Carril: E · Depende de: 022-acceso, 013-lectura-y-pdf · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

La pantalla de lectura de una novela: muestra una versión publicada (portada con dedicatoria, página de novedades si tiene capítulos cambiados, índice navegable, capítulos, ficha de personajes y lugares con enlaces internos), deja elegir entre las versiones publicadas y descargar el PDF de la que se está viendo. Cubre la parte de frontend de `architecture.md` §14.1 y §14.8, y la lectura web del encargo (`project-constraints.md` §2).

## Alcance

- Al entrar sin indicar versión, se muestra la versión vigente (la publicada de número más alto).
- Portada: título, nombre del destinatario y dedicatoria.
- Página de novedades, solo si la versión tiene capítulos cambiados, con un enlace a cada uno.
- Índice navegable de los 10 capítulos, con la marca «cambiado en vN» en los que corresponda.
- Los 10 capítulos, accesibles desde el índice y desde la página de novedades.
- Ficha de personajes y lugares, con un enlace a cada capítulo donde aparece cada uno (lista vacía si no aparece en ninguno).
- Selector de las versiones publicadas de la novela; cambiar de versión recarga portada, novedades, índice y ficha con los de la versión elegida.
- Descargar el PDF de la versión que se está viendo.
- Estados de carga y de error de la lista de versiones, del detalle de una versión y de la descarga del PDF.
- Marca corporativa de la pantalla.

## Fuera de alcance

- Sesión, token y qué pasa sin sesión válida → 022-acceso.
- Forma, códigos y reglas de `GET /api/novels/{id}/versions`, `GET /api/novels/{id}/versions/{v}` y `GET /api/novels/{id}/versions/{v}/pdf`, cálculo de capítulos cambiados y de la ficha, `VistaDeVersion` y token de vista → 013-lectura-y-pdf; esta spec solo consume el detalle JSON que 013 entrega para la SPA.
- Estados, ciclo de vida de la versión y versión vigente de la novela → 009-story-bible-y-versiones; esta spec solo lee lo que ya llega calculado.
- Seleccionar un fragmento o un hecho y pedir un cambio, propuesta, afectados y confirmación → 027-cambio-del-lector.
- Editor manual con lint en vivo → 028-edicion-manual.
- Llegar a la lectura desde «mis novelas» y en qué versión → 023-mis-novelas (023-C09 ya fija que se entra en la versión vigente).
- Marca y tokens de tema (logotipo, paleta, tipografía) → `specs/000-scaffolding.md`; aquí solo se observa que la pantalla los reutiliza.

## Comportamiento observable

**Convenciones.** N es una novela publicada, con V1 (sin capítulos cambiados) y V2 (copia de V1 con los capítulos 3 y 7 cambiados, ficha con Toby en V1 y Nala en V2), como en 013-lectura-y-pdf. La API simulada responde exactamente lo que fijan los casos de 013 para cada entrada; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta.

### Entrar en la lectura

#### 026-C01 — Sin versión indicada, se muestra la vigente (T)
- **Entrada:** se abre la lectura de N sin indicar versión; la API simulada responde la lista de versiones con V1 y V2 (la de número más alto, V2, al final).
- **Salida:** la pantalla pide el detalle de V2 y lo muestra; el selector de versiones marca V2 como la que se está viendo.

#### 026-C02 — Portada con dedicatoria (T)
- **Entrada:** detalle de V1.
- **Salida:** la portada muestra el título, el nombre del destinatario y la dedicatoria de N.

#### 026-C03 — Índice navegable a los capítulos (T)
- **Entrada:** detalle de V1, sin capítulos cambiados.
- **Salida:** un índice con los 10 capítulos; al elegir uno, la pantalla muestra su texto; ningún capítulo lleva la marca «cambiado en vN».

#### 026-C04 — Página de novedades y marca de cambio (T)
- **Entrada:** detalle de V2, con los capítulos 3 y 7 cambiados.
- **Salida:** la pantalla muestra una página de novedades con un enlace a cada uno de los capítulos 3 y 7; el índice marca esos dos capítulos como «cambiado en v2» y ninguno más; seguir cada enlace de la página de novedades lleva al capítulo correspondiente.

#### 026-C05 — Sin capítulos cambiados, no hay página de novedades (T)
- **Entrada:** detalle de V1.
- **Salida:** la pantalla no muestra ninguna página de novedades.

#### 026-C06 — Ficha con enlaces a los capítulos donde aparece cada entidad (T)
- **Entrada:** detalle de V1, con su ficha (Toby, con los capítulos donde aparece).
- **Salida:** la ficha lista a Toby con un enlace por cada capítulo donde aparece; seguir un enlace lleva a ese capítulo.

#### 026-C07 — Una entidad sin capítulos aparece en la ficha sin enlaces (T)
- **Entrada:** detalle de una versión con una entidad de ficha sin ningún capítulo asociado.
- **Salida:** la ficha incluye a esa entidad, sin ningún enlace.

### Selector de versiones

#### 026-C08 — El selector lista las versiones publicadas, en el orden que entrega la API (T)
- **Entrada:** la lista de versiones de N, con V1 y V2 en ese orden.
- **Salida:** el selector ofrece V1 y V2 en ese mismo orden; no las reordena.

#### 026-C09 — Cambiar de versión recarga todo el contenido con el de la versión elegida (T)
- **Entrada:** viendo V2, la persona elige V1 en el selector.
- **Salida:** la pantalla pide el detalle de V1 y lo muestra: la ficha pasa a nombrar a Toby en vez de a Nala, el índice ya no marca ningún capítulo como cambiado y desaparece la página de novedades; nada de V2 queda visible.

### Descargar el PDF

#### 026-C10 — Descargar el PDF de la versión que se está viendo (T)
- **Entrada:** viendo V1, la persona pide descargar el PDF; la API simulada responde con el fichero.
- **Salida:** la pantalla ofrece el PDF de V1 para su descarga.

#### 026-C11 — El PDF aún no está disponible (T)
- **Entrada:** viendo una versión cuyo PDF la API simulada responde como no encontrado.
- **Salida:** la pantalla indica que el PDF no está disponible todavía, sin afectar al resto de la lectura (portada, índice, capítulos, ficha siguen mostrándose).

### Carga y error

#### 026-C12 — Fallo al cargar la lista de versiones (T)
- **Entrada:** la API simulada responde con un error a la lista de versiones.
- **Salida:** la pantalla muestra que no se pudo cargar y ofrece reintentar; no se muestra ningún selector ni contenido de versión.

#### 026-C13 — Fallo al cargar el detalle de una versión (T)
- **Entrada:** la API simulada responde con un error al detalle de la versión elegida.
- **Salida:** la pantalla muestra que no se pudo cargar esa versión y ofrece reintentar; el selector sigue disponible para elegir otra versión.

#### 026-C15 — Mientras carga, la pantalla lo indica (T)
- **Entrada:** la API simulada aún no ha respondido a la lista de versiones, o al detalle de la versión elegida.
- **Salida:** la pantalla muestra un aviso de carga accesible (`role="status"`) en el lugar de lo que falta; no muestra contenido vacío como si la novela no tuviera nada ni un error. Al llegar la respuesta, el aviso desaparece.

#### 026-C16 — La lectura se presenta como un libro, en escritorio y en móvil (D)
- **Entrada:** la lectura de una versión real (y el panel de cambio de 027-cambio-del-lector sobre ella), vista con Playwright MCP a ancho de escritorio y de móvil (≈390 px), sin llamar a ningún modelo.
- **Salida:** portada centrada con la dedicatoria destacada; índice y ficha con buen aspecto y la marca «cambiado en vN» visible; capítulos en columna de lectura con tipografía de libro; sin desbordes horizontales en móvil; estados de carga y error claros. Sin comportamiento nuevo: 026-C01 a C15 y 027-C01 a C14 siguen en verde.

### Marca y recorrido completo

#### 026-C14 — El recorrido completo se observa en el navegador (D, al final)
- **Entrada:** con el servidor real, se abre la lectura de una novela publicada con más de una versión y se recorren portada, novedades, índice, capítulos, ficha, cambio de versión y descarga del PDF con Playwright MCP.
- **Salida:** la pantalla lleva la misma marca (logotipo, paleta, tipografía) que el resto de la SPA; cada paso hace lo que describen 026-C01 a 026-C13 con el servidor real. El resultado se anota en `docs/verification.md` §9.3.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 026-I1 | Lo mostrado (portada, novedades, índice, capítulos, ficha) es siempre de una sola versión, la que marca el selector; nunca mezcla datos de dos versiones | T | 026-C09 |
| 026-I2 | La pantalla nunca calcula por su cuenta qué capítulos cambiaron ni construye la ficha: muestra tal cual lo que entrega el detalle de la API | A | Revisión de que el componente no combina capítulos o entidades; los recibe ya resueltos, como en 013-lectura-y-pdf |
| 026-I3 | Todo enlace interno de la página de novedades, del índice y de la ficha lleva al capítulo correcto dentro de la propia pantalla | T | 026-C04, 026-C06 |
| 026-I4 | Un error de cualquier llamada de esta pantalla (lista de versiones, detalle, PDF) siempre se muestra; nunca se descarta en silencio ni deja contenido de una carga anterior como si fuera el actual | T | 026-C11, 026-C12, 026-C13 |
| 026-I5 | Ninguna llamada de esta pantalla a la API real: las pruebas la sustituyen en el límite de `shared/api` | T | `frontend/AGENTS.md`: ninguna prueba alcanza un backend real |

## Docs referenciados

- `architecture.md` §14.1 (contenido de la lectura web), §14.2 (`VistaDeVersion`, dos consumidores, referencia de lo que entrega la API), §14.8 (páginas de la SPA, FSD pages-first, marca corporativa).
- `definitions.md`: §3 (Version, capítulo cambiado, versión vigente = publicada de número más alto), §2 (Ficha de personajes y lugares, cómo aparece una entidad), §10 (`VistaDeVersion`, `LecturaWeb`).
- `verification.md` §2 (clases T/A/I/D/U), §3.3 (ninguna prueba T llama a un backend real), §9.3 (recorrido visual con Playwright MCP).
- `specs/backend/013-lectura-y-pdf.md` (forma del detalle de una versión, `GET /versions` y `/versions/{v}/pdf`, 013-C01 a 013-C15) — referenciada, no duplicada.
- `specs/backend/009-story-bible-y-versiones.md` (estados, versión vigente) — referenciada, no duplicada.
- `specs/frontend/022-acceso.md` (sesión, rutas protegidas).
- `specs/frontend/023-mis-novelas.md` (023-C09: se entra en la lectura desde una novela `published`, en su versión vigente).
- `project-constraints.md` §2 (lectura interactiva web: índice, ficha, portada con dedicatoria, novedades).
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban van abajo y en el informe.

- **Versión mostrada al entrar sin indicar ninguna**: la vigente (publicada de número más alto), ya fijado en `definitions.md` §3; no es una decisión nueva.
- **Qué pasa si el PDF de la versión vista no está guardado (026-C11)**: se muestra un aviso local sin bloquear el resto de la pantalla, lo más simple, coherente con que 013-C12 ya responde 404 sin afectar al resto del detalle.
