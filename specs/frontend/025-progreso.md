# 025 — Progreso

> Carril: E · Depende de: 024-entrevista, 011-produccion-de-capitulos · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

La pantalla de progreso de una ejecución: mientras una novela tiene una ejecución sin terminar (`in_progress`), muestra su avance por sondeo, deja reanudar una ejecución interrumpida y, cuando termina, lleva a la lectura si publica o muestra su informe si falla.

## Alcance

- Sondeo periódico del estado de la ejecución de la novela: tipo, estado, fase, capítulo actual, coste acumulado y posición en la cola, tal como los entrega la API.
- Parar el sondeo al llegar a un estado terminal (`published`, `failed`) y lo que hace la pantalla en cada uno: navegar a la lectura, o mostrar el informe de la ejecución.
- Ofrecer reanudar una ejecución interrumpida, y lo que muestra la pantalla mientras y después.
- Estados de carga y de error del sondeo, de pedir el informe y de reanudar.

## Fuera de alcance

- Sesión, token, redirección a acceso sin sesión válida → 022-acceso.
- Forma exacta de las respuestas, códigos, reglas de la máquina de estados de la `Ejecucion`, cola FIFO, motivos de fallo e interrupción, y cálculo del `InformeDeEjecucion` → 011-produccion-de-capitulos (progreso, reanudar, informe) y 012-gate-de-publicacion (fases `gate` y `rewriting`); aquí solo se observa lo que la SPA hace con esa respuesta.
- Cómo se llega a esta pantalla desde «mis novelas» (023-mis-novelas: una novela `in_progress` navega aquí) y el contenido de la entrevista (024-entrevista).
- Contenido de la pantalla de lectura a la que se navega al publicar → 026-lectura.
- Marca corporativa (tokens de tema, logotipo) → `specs/000-scaffolding.md`.

## Comportamiento observable

**Convenciones.** La API simulada responde exactamente lo que definen los casos de 011-produccion-de-capitulos y 012-gate-de-publicacion para cada estado de la `Ejecucion`; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta. El sondeo se prueba con un reloj controlado: cada caso avanza el tiempo a mano y observa qué pide la SPA y qué muestra en cada paso.

### Sondeo

#### 025-C00 — La pantalla sigue la ejecución más reciente de la novela (T)
- **Entrada:** se abre el progreso de una novela; la API del detalle de la novela (008-C02) responde con el id de su ejecución más reciente; por separado, sin ninguna ejecución.
- **Salida:** la pantalla sondea esa ejecución (025-C01). Sin ninguna, muestra que la novela no tiene ninguna ejecución y enlaza a su entrevista, sin sondear. Añadido 2026-09-25: el progreso se abre por la novela, desde «mis novelas», la entrevista o la edición manual.

#### 025-C01 — El sondeo refleja fase y capítulo mientras la ejecución avanza (T)
- **Entrada:** la ejecución de la novela está `running`. Sucesivas respuestas del sondeo: fase `planning` sin capítulo; fase `writing` con capítulo 1; fase `writing` con capítulo 4; fase `gate` sin capítulo.
- **Salida:** en cada sondeo, la pantalla actualiza la fase y el capítulo mostrados a los de la última respuesta, y muestra el coste acumulado que llega en ella. Cada sondeo pide `GET /api/runs/{id}` a un intervalo fijo, siempre el mismo.

#### 025-C02 — En cola, se muestra la posición sin fase ni capítulo (T)
- **Entrada:** la ejecución está `queued` con posición 2.
- **Salida:** la pantalla muestra que la novela espera en la cola y su posición, sin ninguna fase ni capítulo. El sondeo sigue al mismo intervalo.

#### 025-C03 — Un fallo al sondear se muestra sin detener el sondeo (T)
- **Entrada:** una respuesta del sondeo es un error del servidor; la siguiente, tras el intervalo, responde con normalidad.
- **Salida:** tras el fallo, la pantalla muestra que no se pudo actualizar el progreso, conservando el último estado que sí llegó a mostrar; en el siguiente sondeo, si responde bien, el aviso desaparece y el progreso se actualiza.

### Fin de la ejecución

#### 025-C04 — Publicada, el sondeo se detiene y navega a la lectura (T)
- **Entrada:** un sondeo responde que la ejecución está `published`.
- **Salida:** la pantalla deja de sondear (ningún sondeo posterior, aunque pase el intervalo) y navega a la lectura de la novela, en su versión vigente (026-lectura).

#### 025-C05 — Fallida, el sondeo se detiene y muestra el informe (T)
- **Entrada:** un sondeo responde que la ejecución está `failed`, con su motivo.
- **Salida:** la pantalla deja de sondear y pide el informe (`GET /api/runs/{id}/report`); al recibirlo, muestra el motivo del fallo, los defectos sin resolver, los intentos con su desenlace, las reanudaciones y el coste, tal como los entrega la API.

#### 025-C06 — Fallo al pedir el informe (T)
- **Entrada:** la ejecución está `failed`; la petición del informe responde con un error.
- **Salida:** la pantalla muestra que no se pudo cargar el informe, sin inventar ningún dato, y ofrece reintentar la petición.

### Reanudar

#### 025-C07 — Interrumpida, se ofrece reanudar con su motivo (T)
- **Entrada:** un sondeo responde que la ejecución está `interrupted`, con motivo `provider_error` y su detalle.
- **Salida:** la pantalla muestra que la ejecución está interrumpida, su motivo y su detalle, y ofrece un botón para reanudarla. El sondeo sigue al mismo intervalo mientras la persona no reanuda, por si otro cliente ya la reanudó.

#### 025-C08 — Reanudar vuelve a mostrar el progreso en curso (T)
- **Entrada:** con la ejecución `interrupted`, la persona pulsa «reanudar»; la API responde 202. El siguiente sondeo devuelve la ejecución `queued` con posición 1.
- **Salida:** mientras la petición de reanudar está en curso, el botón se deshabilita para no reanudar dos veces; al responder 202, la pantalla vuelve a mostrar el progreso por sondeo, ahora con la posición en la cola.

#### 025-C09 — Reanudar rechazada (T)
- **Entrada:** la persona pulsa «reanudar» sobre una ejecución que el siguiente sondeo ya mostró `queued` (otro cliente la reanudó primero); la API responde con un error.
- **Salida:** la pantalla muestra el motivo del rechazo junto al botón, que vuelve a estar disponible, y sigue sondeando con lo que ya tenía.

### Acceso a la pantalla

#### 025-C10 — Ejecución ajena o inexistente (T)
- **Entrada:** la novela o su ejecución no son del cliente, o no existen; la API responde 404 al primer sondeo.
- **Salida:** la pantalla muestra que no encuentra esa ejecución, sin haber mostrado ningún progreso antes, y no vuelve a sondear.

### Recorrido visual (D, al final de la spec)

#### 025-C11 — Recorrido real de una ejecución hasta publicar o fallar (D)
- **Entrada:** con el servidor real y una ejecución en curso, el revisor sigue la pantalla de progreso con Playwright MCP hasta que termina; en otra pasada, reanuda una ejecución interrumpida de verdad.
- **Salida:** la pantalla se ve con la marca corporativa de `specs/000-scaffolding.md`, actualiza fase y capítulo mientras avanza, y hace lo que describen 025-C04 a 025-C09 con el servidor real. El resultado se anota en `docs/verification.md` §9.3.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 025-I1 | El sondeo pide `GET /api/runs/{id}` al mismo intervalo fijo mientras la ejecución no está en un estado terminal, y nunca deja de pedirlo por su cuenta antes de `published` o `failed`, salvo el error de acceso de 025-C10 | T | 025-C01, 025-C02, 025-C03, 025-C07, con el reloj controlado |
| 025-I2 | Tras `published` o `failed`, la pantalla no vuelve a pedir `GET /api/runs/{id}` | T | 025-C04, 025-C05, avanzando el reloj después de detectar el estado terminal |
| 025-I3 | La pantalla nunca reanuda una ejecución sin que la persona pulse el botón | T | 025-C07, 025-C08: ningún sondeo dispara `POST /api/runs/{id}/resume` por sí mismo |
| 025-I4 | Un error de cualquier llamada de esta pantalla (sondeo, informe, reanudar) siempre se muestra; nunca se descarta en silencio ni deja la pantalla como si todo hubiera ido bien | T | 025-C03, 025-C06, 025-C09 |
| 025-I5 | La pantalla nunca calcula el estado, la fase, el motivo o el contenido del informe por su cuenta: muestra tal cual lo que entrega la API | A | Revisión de que el componente no deriva estos valores de otros campos, los recibe ya resueltos |

## Docs referenciados

- `architecture.md`:
  - §9.1: máquina de estados de la `Ejecucion`, progreso por sondeo (`GET /api/runs/{id}`, sin SSE), motivos de fallo e interrupción.
  - §9.2: reanudación, `POST /api/runs/{id}/resume`.
  - §14.8: páginas de la SPA (progreso entre ellas).
  - §15.7: API de ejecuciones (`GET /api/runs/{id}`, `POST /api/runs/{id}/resume`, `GET /api/runs/{id}/report`), 404 de lo ajeno o inexistente.
- `definitions.md`:
  - `Ejecucion`: estado, fase, atributos, motivo de fallo y de interrupción.
  - `InformeDeEjecucion`: qué contiene, que se calcula al pedirlo.
  - `Novela`: estado derivado `in_progress`.
- `specs/backend/011-produccion-de-capitulos.md` (011-C04 progreso por sondeo; 011-C26, 011-C27 reanudar; 011-C30 informe) — referenciada, no duplicada.
- `specs/backend/012-gate-de-publicacion.md` (fases `gate` y `rewriting`, reanudar en el gate) — referenciada, no duplicada.
- `specs/frontend/022-acceso.md` (sesión, rutas protegidas, redirección sin sesión).
- `specs/frontend/023-mis-novelas.md` (llegada a esta pantalla desde una novela `in_progress`).
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).
- `docs/verification.md` §2 (clases T/A/I/D/U), §3.3 (integración con dobles; ninguna prueba T llama a un modelo o a un backend real), §9.3 (recorrido visual con Playwright MCP).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban van abajo y en el informe.
