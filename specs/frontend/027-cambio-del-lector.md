# 027 — Cambio del lector

> Carril: E · Depende de: 026-lectura, 014-cambios-del-lector · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24); corregida el mismo día: sin 025-progreso, fuera de alcance (`architecture.md` §18, «Alcance del frontend»)

## Objetivo

Pedir un cambio desde la lectura de 026: seleccionar un fragmento o un hecho, escribir la petición, ver la propuesta y los capítulos afectados, confirmarla o descartarla, y ver en la lectura la versión nueva cuando se publique.

## Alcance

- Abrir el formulario de petición a partir de una selección (fragmento o hecho) hecha en la lectura de 026.
- Enviar la petición y mostrar lo que entrega la API: la propuesta (hecho, valor antiguo, valor nuevo, o hecho nuevo), los capítulos afectados y la caducidad.
- Confirmar la propuesta o descartarla, y lo que hace la pantalla en cada caso.
- La caducidad de la propuesta sin confirmar.
- Estados de carga y de error de pedir el cambio y de confirmarlo.
- Tras confirmar, indicar que la ejecución está en marcha; la versión nueva aparece en el selector de versiones de la lectura de 026 cuando se publica.

## Fuera de alcance

- Forma exacta de las rutas, códigos, reglas de la policy, del planner en modo cambio, del cálculo de afectados y de la caducidad del código → 014-cambios-del-lector; aquí solo se observa lo que la SPA hace con esa respuesta.
- Contenido de la lectura (índice, capítulos, ficha, selector de versión, marca «cambiado en vN») y cómo se selecciona un fragmento o un hecho en ella → «la lectura de 026».
- Sondeo detallado, reanudación e informe de una ejecución → CLI (`architecture.md` §15.8); la pantalla de progreso (025) queda fuera de alcance.
- Sesión, token y acceso sin sesión válida → 022-acceso.
- El editor manual (§10.3) → 019-edicion-manual y su spec de frontend, si la hay.
- Marca corporativa (tokens de tema, logotipo) → `specs/000-scaffolding.md`.

## Comportamiento observable

**Convenciones.** La API simulada responde exactamente lo que definen los casos de 014-cambios-del-lector para cada ruta; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta. Los casos con caducidad usan un reloj controlado.

### Pedir el cambio

#### 027-C01 — Seleccionar un fragmento o un hecho abre el formulario de petición (T)
- **Entrada:** en la lectura de 026, la persona selecciona un fragmento del texto de un capítulo, o un hecho de la ficha de personajes y lugares, y pulsa «pedir un cambio».
- **Salida:** se abre el formulario de petición, con la selección elegida visible (la cita, o el hecho con su valor actual) y un campo de texto vacío para escribir la petición.

#### 027-C02 — La petición vacía no se puede enviar (T)
- **Entrada:** el formulario de 027-C01 con el campo de texto vacío.
- **Salida:** la acción de enviar la petición está deshabilitada. Al escribir un carácter, se habilita.

#### 027-C03 — Enviar la petición muestra la propuesta, los afectados y la caducidad (T)
- **Entrada:** la persona escribe «el perro se llama Nala» y envía; la API responde 201 con la propuesta (el hecho, su valor antiguo «Toby» y el valor nuevo «Nala»), los capítulos afectados `[2, 5, 7]`, un código de confirmación y su caducidad.
- **Salida:** el formulario se sustituye por la propuesta: el hecho con su valor antiguo y el nuevo (o el hecho nuevo), la lista de capítulos afectados en el orden que entrega la API, y las dos acciones disponibles, «confirmar» y «descartar». El código no aparece en ningún sitio de la pantalla.

#### 027-C04 — Una propuesta sin afectados se muestra igual (T)
- **Entrada:** la API responde 201 con una propuesta y la lista de afectados vacía.
- **Salida:** la propuesta se muestra con una indicación de que ningún capítulo cambiará, y las dos acciones siguen disponibles.

#### 027-C05 — Petición rechazada por la policy o por la propuesta (T)
- **Entrada:** la persona envía la petición; la API responde 422 con un motivo (una prohibida, una propuesta inválida agotados los intentos, una selección o una cita que no cumple, o una petición que supera la cota).
- **Salida:** el formulario se mantiene con el texto escrito, muestra el motivo del rechazo, y no aparece ninguna propuesta.

#### 027-C06 — Petición sobre una selección que ya no vale (T)
- **Entrada:** la persona envía la petición; la API responde 409 porque la versión de la selección ya no es la vigente.
- **Salida:** se muestra que la versión ha cambiado y hay que volver a seleccionar sobre la lectura vigente; no aparece ninguna propuesta.

#### 027-C07 — Fallo del servidor al pedir el cambio (T)
- **Entrada:** la persona envía la petición; la API responde con un error de servidor.
- **Salida:** el formulario se mantiene con el texto escrito, muestra que no se pudo enviar la petición, y ofrece reintentar sin perder lo escrito.

#### 027-C08 — Enviar deshabilita la acción mientras está en curso (T)
- **Entrada:** la persona pulsa enviar; la respuesta tarda.
- **Salida:** mientras la petición está en curso, la acción de enviar queda deshabilitada, para no pedir el mismo cambio dos veces.

### Confirmar o descartar

#### 027-C09 — Confirmar encola la ejecución y lo indica en la lectura (T)
- **Entrada:** sobre la propuesta de 027-C03, la persona pulsa «confirmar» antes de la caducidad; la API responde 202 con el id de la ejecución.
- **Salida:** la propuesta se cierra y la lectura muestra que el cambio está en marcha (con el id de la ejecución), sin mostrar el código; la persona sigue en la lectura de la versión actual. Cuando la versión nueva se publica, aparece en el selector de versiones de la lectura de 026.

#### 027-C10 — Descartar no confirma nada (T)
- **Entrada:** sobre la propuesta de 027-C03, la persona pulsa «descartar».
- **Salida:** la propuesta desaparece de la pantalla, sin ninguna llamada a confirmar. La persona vuelve a la lectura y puede seleccionar y pedir otro cambio.

#### 027-C11 — Confirmar o descartar deshabilita las dos acciones mientras está en curso (T)
- **Entrada:** sobre la propuesta de 027-C03, la persona pulsa «confirmar»; la respuesta tarda.
- **Salida:** mientras la confirmación está en curso, tanto «confirmar» como «descartar» quedan deshabilitadas, para no encolar dos ejecuciones ni descartar durante el envío.

#### 027-C12 — La propuesta caduca sin confirmar (T)
- **Entrada:** sobre la propuesta de 027-C03, el reloj avanza hasta la caducidad que trae la respuesta, sin que la persona confirme ni descarte.
- **Salida:** la pantalla muestra que la propuesta ha caducado y que hay que volver a pedirla; la acción de confirmar deja de estar disponible.

#### 027-C13 — Confirmar una propuesta que el servidor ya considera caducada (T)
- **Entrada:** sobre la propuesta de 027-C03, la persona pulsa «confirmar»; la API responde 409 porque ya ha caducado.
- **Salida:** la pantalla muestra que la propuesta ha caducado, igual que 027-C12, sin encolar nada.

#### 027-C14 — Fallo del servidor al confirmar (T)
- **Entrada:** sobre la propuesta de 027-C03, la persona pulsa «confirmar»; la API responde con un error de servidor.
- **Salida:** la propuesta se mantiene visible con sus afectados y su caducidad, muestra que no se pudo confirmar, y ofrece reintentar mientras no haya caducado.

### Recorrido visual (D, al final de la spec)

#### 027-C15 — Recorrido real: pedir, confirmar y ver la versión nueva (D)
- **Entrada:** con el servidor real y la novela publicada del brief de ejemplo, el revisor sigue la lectura con Playwright MCP: selecciona el hecho del nombre del perro, pide «el perro se llama Nala», ve la propuesta y los afectados, confirma y, cuando se publica, abre la versión nueva en el selector.
- **Salida:** la pantalla se ve con la marca corporativa de `specs/000-scaffolding.md` en cada paso, y la versión nueva se lee con sus capítulos cambiados marcados. El resultado se anota en `docs/verification.md` §9.3, junto con 014-C20.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 027-I1 | El código de confirmación nunca se muestra en la pantalla: la SPA lo recibe con la propuesta y lo envía ella misma al confirmar, sin que la persona lo escriba | T | 027-C03, 027-C09 |
| 027-I2 | Confirmar nunca se dispara sin que la persona pulse «confirmar»; ningún temporizador ni sondeo la confirma por su cuenta | T | 027-C12: avanzar el reloj hasta la caducidad no encola nada |
| 027-I3 | Un error de cualquier llamada de esta pantalla (pedir, confirmar) siempre se muestra; nunca se descarta en silencio ni deja la pantalla como si hubiera ido bien | T | 027-C05 a 027-C07, 027-C13, 027-C14 |
| 027-I4 | La pantalla nunca calcula los capítulos afectados, el valor antiguo o el nuevo, ni la caducidad por su cuenta: muestra tal cual lo que entrega la API | A | Revisión de que el componente no deriva estos valores, los recibe ya resueltos |
| 027-I5 | La petición nunca se envía sin una selección previa de fragmento o hecho | T | 027-C01, 027-C02 |

## Docs referenciados

- `architecture.md`:
  - §10.1: el flujo completo (selección, petición, policy, planner, propuesta, confirmación, ejecución de cambio);
  - §10.2: la concurrencia entre cambios (una solicitud rechazada por `stale_base` se repite sobre la versión nueva);
  - §14.1: la lectura web, «seleccionar un fragmento o un hecho → pedir un cambio (propuesta, afectados, confirmación)»;
  - §14.8: páginas de la SPA (lectura);
  - §18: «Alcance del frontend» (configuración y progreso por la CLI).
- `definitions.md`:
  - §5: `SolicitudDeCambio` (selección, petición, propuesta, capítulos afectados, estado);
  - §10: `Confirmacion` (segundo paso obligatorio, código de un solo uso, caducidad).
- `specs/backend/014-cambios-del-lector.md` (014-C01 a 014-C11: pedir y confirmar, sus respuestas y códigos; 014-C20 demostración) — referenciada, no duplicada.
- `specs/frontend/022-acceso.md` (sesión, rutas protegidas).
- «la lectura de 026» (selección de fragmento o hecho, contenido de la pantalla de lectura): spec aún en redacción, referenciada solo por su nombre.
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).
- `docs/verification.md` §2 (clases T/A/I/D/U), §3.3 (integración con dobles; ninguna prueba T llama a un modelo o a un backend real), §9.3 (recorrido visual con Playwright MCP).
- `project-constraints.md` §2, «Lectura interactiva» (seleccionar un fragmento o un hecho y pedir un cambio desde la propia página).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban:

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Escribe la persona el código de confirmación? | No: la SPA lo guarda de la respuesta de la propuesta y lo envía ella misma al confirmar. Más simple y ningún doc exige tecleo manual | **Decisión** |
| ¿Cómo se descarta una propuesta? | Solo en el cliente: 014 no tiene ruta para cancelar una solicitud, así que descartar no llama a la API; la solicitud caduca sola en el servidor | `specs/backend/014-cambios-del-lector.md`, alcance («no hay ruta... para cancelar»); **decisión** |
| ¿Qué pasa si los afectados vienen vacíos? | Se muestra igual, con aviso de que ningún capítulo cambia, como ya decide 014-C02 en el backend | `specs/backend/014-cambios-del-lector.md` 014-C02; **decisión** |
