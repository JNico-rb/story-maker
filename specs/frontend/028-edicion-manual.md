# 028 — Edición manual

> Carril: E · Depende de: 026-lectura, 025-progreso, 018-linters-de-prosa (backend), 019-edicion-manual (backend) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

El editor manual de la lectura: la persona abre desde un capítulo de la versión vigente un editor de su texto, ve en vivo los avisos del lint mientras escribe, guarda su edición —lo que lanza la ejecución `manual_edit`— y, cuando la ejecución termina, ve la versión nueva publicada o el motivo del rechazo. Cubre la parte de frontend de `architecture.md` §14.1 y §14.6, y `verification.md` §5 O.9 (parte de frontend).

## Alcance

- Abrir el editor de un capítulo desde la lectura de la versión vigente (026-lectura), con el texto del capítulo precargado.
- Que el editor solo se ofrezca sobre la versión vigente.
- Lint en vivo: mientras la persona escribe, la pantalla pide diagnósticos a la API y los muestra con su mensaje, su posición (cuando la hay) y si bloquearán el guardado.
- Guardar la edición: envía el texto y la versión base; según la respuesta, la pantalla:
  - si se acepta, lleva al seguimiento de la ejecución que lanza (025-progreso);
  - si se rechaza por diagnósticos bloqueantes, los muestra sin descartar el texto editado;
  - si la base ya no es la vigente, lo avisa y ofrece recargar el capítulo vigente.
- Estados de carga y de error de: cargar el capítulo, el lint en vivo y el guardado.

## Fuera de alcance

- Qué detecta cada diagnóstico del lint, sus reglas, su ruta y su forma exacta → 019-edicion-manual; aquí solo se consume su respuesta.
- Qué bloquea el guardado, los códigos de la ruta de guardado y sus rechazos exactos → 019-edicion-manual.
- Todo lo que ocurre en la ejecución `manual_edit` (fases, validadores, Lean, propagación de hechos) → 019-edicion-manual.
- Qué detecta cada linter de prosa → 018-linters-de-prosa; aquí solo se muestran sus avisos como diagnósticos de tipo «linter».
- El seguimiento de la ejecución tras el guardado (sondeo, reanudar, informe de fallo, navegación a la lectura al publicar) → 025-progreso; esta spec solo observa que el guardado aceptado lleva a esa pantalla.
- El resto de la lectura (portada, índice, novedades, ficha, selector de versión, PDF) → 026-lectura.
- Sesión, token y acceso sin sesión válida → 022-acceso.
- Pedir un cambio sobre un fragmento o un hecho → 027-cambio-del-lector.
- Marca corporativa → `specs/000-scaffolding.md`.

## Comportamiento observable

**Convenciones.** N es una novela publicada, con V2 vigente. El capítulo 3 de V2 tiene un texto conocido. La API simulada responde exactamente lo que fijan los casos de 019-edicion-manual para cada entrada de lint y de guardado; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta. El lint en vivo se prueba con un reloj controlado: cada caso avanza el tiempo a mano.

### Abrir el editor

#### 028-C01 — Abrir el editor precarga el texto vigente del capítulo (T)
- **Entrada:** desde el capítulo 3 de la lectura de la versión vigente de N, la persona abre el editor.
- **Salida:** el editor muestra, ya cargado y editable, el texto vigente del capítulo 3.

#### 028-C02 — El editor solo se ofrece en la versión vigente (T)
- **Entrada:** la lectura muestra una versión que no es la vigente.
- **Salida:** ningún capítulo de esa versión ofrece abrir el editor.

#### 028-C03 — Fallo al cargar el capítulo (T)
- **Entrada:** al abrir el editor, la API simulada responde con un error al pedir el texto del capítulo.
- **Salida:** la pantalla muestra que no se pudo cargar el capítulo y ofrece reintentar; no se muestra ningún editor de texto.

### Lint en vivo

#### 028-C04 — Los diagnósticos llegan tras una pausa de escritura, no en cada pulsación (T)
- **Entrada:** la persona escribe varios caracteres seguidos, sin dejar pasar la pausa fija entre ellos, y después se detiene.
- **Salida:** ninguna petición de lint se envía mientras escribe seguido; una sola petición se envía con el texto completo, tras la pausa fija posterior a la última pulsación.

#### 028-C05 — Los diagnósticos con posición se resaltan en el texto (T)
- **Entrada:** la respuesta del lint trae un diagnóstico de tipo «forma no canónica», con posición y marcado como que bloqueará el guardado.
- **Salida:** el editor resalta ese fragmento del texto y muestra su mensaje; el resaltado indica que bloqueará el guardado.

#### 028-C06 — Los diagnósticos sin posición se muestran aparte (T)
- **Entrada:** la respuesta del lint trae un diagnóstico de tipo «hecho», sin posición.
- **Salida:** ese diagnóstico se muestra en una lista aparte del texto, con su mensaje, sin ningún resaltado sobre el texto.

#### 028-C07 — Diagnósticos no bloqueantes se distinguen de los que bloquean (T)
- **Entrada:** la respuesta del lint trae un diagnóstico de tipo «linter» (no bloqueante) y uno de tipo «prohibida» (bloqueante).
- **Salida:** los dos se muestran con su mensaje; solo el de «prohibida» se marca como que bloqueará el guardado.

#### 028-C08 — Cada respuesta de lint sustituye a la anterior, aunque lleguen desordenadas (T)
- **Entrada:** la persona escribe, se envía una petición de lint con el texto A y, antes de que responda, escribe más y se envía otra con el texto B; la respuesta de B llega antes que la de A.
- **Salida:** los diagnósticos mostrados son siempre los de la última petición enviada (B); la respuesta tardía de A no los sustituye.

#### 028-C09 — Un fallo del lint no impide seguir editando (T)
- **Entrada:** una petición de lint responde con un error.
- **Salida:** la pantalla muestra que no se pudo comprobar el texto, conserva los diagnósticos que ya tenía y deja seguir escribiendo y guardar con normalidad.

#### 028-C10 — Ningún diagnóstico bloquea la escritura (T)
- **Entrada:** el lint devuelve varios diagnósticos marcados como que bloquearán el guardado.
- **Salida:** la persona sigue escribiendo en el editor sin ninguna restricción; solo el guardado en sí queda sujeto a esos diagnósticos.

### Guardar

#### 028-C11 — Guardar aceptado lleva al seguimiento de la ejecución (T)
- **Entrada:** la persona guarda un texto válido; la API simulada responde 202 con el id de la ejecución.
- **Salida:** la pantalla navega a la pantalla de progreso de esa ejecución (025-progreso), que a partir de ahí sigue su propio comportamiento (sondeo, y al publicar, la lectura de la versión nueva; al fallar, su informe).

#### 028-C12 — Guardar rechazado por diagnósticos bloqueantes (T)
- **Entrada:** la persona guarda un texto con una forma no canónica; la API simulada responde 422 con los diagnósticos bloqueantes.
- **Salida:** la pantalla muestra esos diagnósticos junto al editor; el texto editado sigue en el editor, sin descartarse, y la persona puede corregirlo y volver a guardar.

#### 028-C13 — Guardar con la base obsoleta (T)
- **Entrada:** mientras la persona edita, otra versión se publica; al guardar, la API simulada responde 409.
- **Salida:** la pantalla avisa de que hay una versión más nueva y ofrece recargar el capítulo con el texto de la versión vigente actual, descartando la edición en curso si la persona lo confirma.

#### 028-C14 — Fallo de red al guardar (T)
- **Entrada:** al guardar un texto válido, la API simulada responde con un error del servidor.
- **Salida:** la pantalla muestra que no se pudo guardar, conserva el texto editado y deja reintentar.

### Recorrido visual

#### 028-C15 — El recorrido completo se observa en el navegador (D, al final)
- **Entrada:** con el servidor real, se abre el editor de un capítulo de una novela publicada, se escribe un texto que dispara un diagnóstico y luego se corrige, y se guarda con Playwright MCP hasta ver la versión nueva publicada.
- **Salida:** la pantalla lleva la misma marca que el resto de la SPA; cada paso hace lo que describen 028-C01 a 028-C14 con el servidor real. El resultado se anota en `docs/verification.md` §9.3.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 028-I1 | El texto que se envía al guardar es exactamente el que hay en el editor en ese momento, sin que la pantalla lo transforme | T | 028-C11, 028-C12: se compara el texto mostrado con el cuerpo de la petición de guardado |
| 028-I2 | Los diagnósticos mostrados corresponden siempre a la última petición de lint enviada, nunca a una respuesta anterior que llega tarde | T | 028-C08 |
| 028-I3 | Ningún diagnóstico del lint impide escribir en el editor; solo el guardado queda sujeto a lo que la API rechace | T | 028-C10 |
| 028-I4 | La pantalla nunca decide por su cuenta si un diagnóstico bloqueará el guardado: usa el campo que entrega la API | A | Revisión de que el componente no deriva ese dato del tipo de diagnóstico, lo recibe ya resuelto (`specs/backend/019-edicion-manual.md`) |
| 028-I5 | Un error de cualquier llamada de esta pantalla (cargar el capítulo, lint, guardar) siempre se muestra; nunca se descarta en silencio ni deja contenido de una carga anterior como si fuera el actual | T | 028-C03, 028-C09, 028-C14 |
| 028-I6 | Ninguna llamada de esta pantalla a la API real: las pruebas la sustituyen en el límite de `shared/api` | T | `frontend/AGENTS.md`: ninguna prueba alcanza un backend real |

## Docs referenciados

- `architecture.md` §14.1 (el editor manual con lint en vivo, parte de la lectura web), §14.6 (editor manual con linter propio, integrado en el editor web), §14.8 (páginas de la SPA, FSD pages-first, marca corporativa).
- `definitions.md`: §5 (`EdicionManual`, `Ejecucion` tipo `manual_edit`), §6 (`Linter`, `Defecto`), §3 (`Version`, versión vigente), §10 (`Lectura web`).
- `verification.md` §2 (clases T/A/I/D/U), §3.3 (ninguna prueba T llama a un backend real), §5 O.9 (parte de frontend), §9.3 (recorrido visual con Playwright MCP).
- `specs/backend/019-edicion-manual.md` (ruta y forma del lint en vivo, ruta y códigos del guardado, diagnósticos, ejecución `manual_edit`) — referenciada, no duplicada.
- `specs/backend/018-linters-de-prosa.md` (qué detecta cada linter, servido igual en el lint en vivo) — referenciada, no duplicada.
- `specs/frontend/026-lectura.md` (pantalla de la que se abre el editor, versión vigente, navegación a un capítulo).
- `specs/frontend/025-progreso.md` (pantalla a la que lleva un guardado aceptado, y su comportamiento al publicar o fallar) — referenciada, no duplicada.
- `specs/frontend/022-acceso.md` (sesión, rutas protegidas).
- `project-constraints.md`, opcional «Linter propio para edición manual de la novela»: integrado en el editor web; una edición que cambia un hecho actualiza la story bible y pasa de nuevo por los validadores antes de publicar.
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban van abajo y en el informe.

- **Pausa fija entre la última pulsación y la petición de lint**: los docs no la fijan un valor; se deja como constante simple de la pantalla, probada con reloj controlado.
- **Qué pasa tras un guardado aceptado**: los docs (019-alcance) remiten el editor web a 028, y 025-progreso ya cubre el seguimiento de cualquier ejecución de la novela; lo más simple es navegar a esa pantalla en vez de duplicar su sondeo aquí.
- **Base obsoleta al guardar (409)**: se ofrece recargar el capítulo vigente, coherente con que 026-C09 ya recarga contenido al cambiar de versión.
