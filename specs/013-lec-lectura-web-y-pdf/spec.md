# 013 — LEC · Lectura web y PDF

- [x] Spec approved   <- only the user marks this

## Objetivo

Que el cliente lea en la web cualquier versión publicada de su novela —portada, índice, capítulos y ficha enlazada, con los capítulos cambiados marcados— y la descargue en el PDF que se generó al publicarla.

## Alcance

Cubre:

- la página «mis novelas» y la lista de novelas del cliente;
- la lectura de una versión publicada: portada, índice navegable, capítulos, ficha con su regla de enlaces, selector de versión y marca de cambiado;
- la lista de versiones y la story bible de una versión;
- la vista previa de una candidata: emisión del token, canje por la cookie, 404 y revocación;
- la ruta de impresión, la exportación del PDF, el validador `pdf-enlaces` y el PDF guardado y servido.

Versiones de Playwright, navegador y parámetros de impresión: [001 design.md](../001-base/design.md) §11; columnas de `versions` y `previews`: §12.

Depende de 001 y de 002. Lo que muestra lo producen 010, 011 y 014; las pruebas usan fixtures de versiones publicadas.

**Fuera de alcance:**

- Pedir un cambio y el modo de edición manual: la página `reader` les da paso, pero su interfaz y su flujo son de 015.
- Cuándo se emite y se revoca la vista previa, cuándo se exporta el PDF y qué le pasa a la ejecución si falla: lo decide el gate de 014. Aquí se entregan las piezas.
- Qué capítulos cuentan como cambiados: la lista la calcula y la guarda la publicación (014); aquí solo se muestra.
- El estado derivado de la novela, que define 007; aquí solo se muestra.
- Una página de novedades en el PDF: la rama elegida del encargo es la web (`architecture.md` §16, «Modelo de lectura»).
- Pantallas pequeñas: la lectura se diseña y se prueba solo para escritorio (R1).

## Requisitos

Todos son **Obligatorio**.

### Mis novelas

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEC-1 | `GET /api/novels` → las novelas del cliente del token, cada una con su id, su fecha de creación, el nombre del destinatario si el brief ya lo tiene, su estado derivado (007) y, si tiene alguna versión publicada, su título y el número de su versión vigente | Obligatorio | T |
| RF-LEC-2 | La página `novels` → lista las novelas con su título o el nombre del destinatario, su estado y su versión vigente. Cada una lleva a la página de su estado: `interview` en entrevista (005), `progress` lista o en curso (007) y `reader` publicada. Un botón crea una novela nueva (005) y abre su entrevista | Obligatorio | I |

### Lectura de una versión publicada

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEC-3 | `GET /api/novels/{id}/versions` → las versiones publicadas de la novela, en orden de número, cada una con su número, su fecha de publicación y su lista de capítulos cambiados. Nunca incluye una candidata ni una rechazada | Obligatorio | T |
| RF-LEC-4 | `GET /api/novels/{id}/versions/{v}`, con `v` el número de una versión publicada → su portada —el título de la novela, el nombre canónico del destinatario en esa versión y la dedicatoria del brief—; su índice, con el número, el título y la marca de cambiado de los 10 capítulos; sus 10 capítulos, con su título y su texto en párrafos; y su ficha (RF-LEC-6) | Obligatorio | T |
| RF-LEC-5 | `v` no es el número de una versión publicada de esa novela → 404. Una candidata no se lee por número: solo por su vista previa | Obligatorio | T |
| RF-LEC-6 | La ficha de una versión → cada personaje y cada lugar de su story bible, con su nombre canónico y un enlace a cada capítulo donde aparece: los que contienen su forma canónica literal como palabra entera, más los que registran un `UsoDeHecho` de un hecho del que es sujeto, sin repetir y en orden de capítulo. Un personaje sin ninguno de los dos no lleva enlaces. Es la regla que la revisión visual usa como estructura esperada (014) | Obligatorio | T |
| RF-LEC-7 | La marca de cambiado de la versión `v` → la llevan los capítulos de la lista de cambiados de `v`, y ningún otro | Obligatorio | T |
| RF-LEC-8 | `GET /api/novels/{id}/story-bible?version={v}` con `v` una versión publicada → sus personajes y lugares; sus hechos, cada uno con su sujeto, atributo, valor, origen y capítulo de inicio; y su cronología: cada evento con su momento, sus personajes presentes, su lugar y su origen, en orden de momento. Sin `version` → 422; `v` que no es una versión publicada → 404 | Obligatorio | T |
| RF-LEC-9 | La página `reader` → abre la versión vigente y muestra la portada, el índice, cuyas entradas llevan cada una a su capítulo, los capítulos y la ficha, cuyos enlaces llevan cada uno a su capítulo. El selector cambia a cualquier versión publicada. En la versión `v`, índice y capítulos muestran «cambiado en la versión *v*» donde RF-LEC-7 lo marca. Da paso a pedir un cambio y a editar un capítulo (015) | Obligatorio | I |

### Vista previa de una candidata

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEC-10 | Se emite la vista previa de una candidata → devuelve un token nuevo, válido solo para esa candidata, y guarda la `VistaPrevia` sin revocar y sin el token en claro | Obligatorio | T |
| RF-LEC-11 | `POST /api/candidates/{id}/preview` con el token de una vista previa sin revocar de esa candidata, sin `TokenDeAcceso` → 204 y una cookie válida solo para esa candidata | Obligatorio | T |
| RF-LEC-12 | `GET /api/candidates/{id}` con esa cookie → la portada, el índice, los capítulos y la ficha de la candidata, con la misma forma y las mismas reglas que una versión publicada (RF-LEC-4, RF-LEC-6) y sin marca de cambiado | Obligatorio | T |
| RF-LEC-13 | En los dos endpoints de la vista previa, un token o una cookie de otra candidata, inventados o de una vista previa revocada, o la falta de ellos → 404, la misma respuesta en todos los casos | Obligatorio | T |
| RF-LEC-14 | Se revoca la vista previa → desde ese momento su token y su cookie responden como en RF-LEC-13 | Obligatorio | T |
| RF-LEC-15 | La página `preview`, abierta con el id de una candidata y su token → canjea el token por la cookie y muestra la candidata con la estructura de `reader`, sin selector de versión, sin marca de cambiado y sin paso a pedir un cambio ni a editar. El frontend no la guarda como versión publicada. Con un token que no vale, muestra que no existe | Obligatorio | I |

### Ruta de impresión y PDF

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-LEC-16 | La página `print`, abierta con la cookie de la vista previa de una candidata → presenta para imprimir su portada, su índice con un enlace interno a cada capítulo, sus 10 capítulos y su ficha, con un enlace interno por cada capítulo enlazado (RF-LEC-6) | Obligatorio | I |
| RF-LEC-17 | Se exporta el PDF de una candidata → imprime su ruta `print` con la cookie de su vista previa y deja en el directorio de datos un PDF con portada, índice, capítulos y ficha, enlaces internos, un marcador por capítulo y etiquetado de accesibilidad; devuelve su ruta relativa | Obligatorio | T |
| RF-LEC-18 | `pdf-enlaces` sobre un PDF exportado → pasa si cada entrada del índice y cada enlace de la ficha resuelven a la página donde empieza su capítulo. Si una entrada del índice no resuelve, falla `pdf-enlaces/pdf-indice`; si no resuelve un enlace de la ficha, `pdf-enlaces/pdf-ficha`. Se prueba con un PDF correcto, uno con un ancla rota en el índice y otro con un ancla rota en la ficha | Obligatorio | T |
| RF-LEC-19 | `pdf-enlaces` falla → da un defecto bloqueante con causa raíz `fallo de render` y acción bloquear, y el PDF exportado no queda asociado a ninguna versión | Obligatorio | T |
| RF-LEC-20 | El catálogo de criterios → contiene `pdf-enlaces/pdf-indice` y `pdf-enlaces/pdf-ficha`, bloqueantes, con acción bloquear y causa raíz `fallo de render`. El resultado de `pdf-enlaces` se envía como score agregado y uno por criterio (004) | Obligatorio | T |
| RF-LEC-21 | `GET /api/novels/{id}/versions/{v}/pdf` de una versión publicada → 200 con `application/pdf` y el fichero guardado al publicarla. Dos descargas dan los mismos bytes, y ninguna vuelve a exportar | Obligatorio | T |
| RF-LEC-22 | Al cerrar 013 → una inspección con el browser MCP recorre `novels`, `reader`, `preview` y `print` con una novela de fixture, sigue los enlaces del índice y de la ficha, y deja su fila en `verification.md` §9.3 | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Ni el token de una vista previa ni su cookie salen en un log ni en una traza | T |

## Restricciones

| # | Restricción | Origen |
|---|---|---|
| R1 | La lectura se diseña y se prueba solo para escritorio; en una pantalla pequeña se ve como se vea | `architecture.md` §13.6; grill de 013 |

## Docs de referencia

- `architecture.md` §9.3 (capítulos cambiados), §9.4 (regla de enlaces de la ficha), §9.7, §13.6, §14.3, §14.4 («La lectura no cachea candidatas») y §16 («Modelo de lectura», «Servir la lectura», «Momento del PDF», «Generación del PDF»).
- `definitions.md` §2 (`Hecho`, `UsoDeHecho`, `Cronologia`), §3 (`Version`, `Parrafo`, `Portada`, `FichaDePersonajes`, `VistaPrevia`), §6 (`Defecto`, `Score`) y §12.
- `verification.md` §5 («Exportación del PDF», «Frontend», «API, SSE y cliente generado») y §9.3.
