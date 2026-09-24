# 024 — Entrevista

> Carril: E · Depende de: 023-mis-novelas, 008-brief-y-entrevista · Estado: borrador

## Objetivo

La pantalla de entrevista: el chat con el entrevistador, el panel del brief en construcción, el envío de textos libres, los hechos extraídos por aceptar o rechazar, la lista de palabras y temas prohibidos de nivel `novel`, y la confirmación del brief. Cubre la parte de pantalla de `architecture.md` §14.8; lo que responde la API sobre el brief, la entrevista, los textos libres, los hechos y las comprobaciones lo calcula y lo sirve 008-brief-y-entrevista, que esta spec no repite.

## Alcance

- Chat de la entrevista: historial de mensajes, envío de un mensaje nuevo, respuesta del entrevistador.
- Panel del brief en curso: lo que ya tiene fijado, sus `DatoFaltante` y sus `Contradiccion`, la cota de obligatorios.
- Envío de un texto libre y lista de sus `HechoExtraido` verificados, cada uno por aceptar o rechazar y por marcar obligatorio.
- Lista de palabras y temas prohibidos de nivel `novel`: verla, añadir una palabra o un tema con sus palabras clave, y borrar una entrada.
- Confirmación del brief: solo disponible sin faltantes ni contradicciones, y lo que pasa al confirmarlo o al fallar.
- Estados de carga y de error de las llamadas de esta pantalla.
- Que un brief ya confirmado deja la pantalla en modo de solo lectura.

## Fuera de alcance

- Sesión, token y qué pasa sin sesión válida → 022-acceso.
- Crear la novela y llegar aquí desde «mis novelas» → 023-mis-novelas.
- Cálculo de las comprobaciones (schema, faltantes, contradicciones, cota), la extracción de hechos, `citas-verificadas`, la verificación de cada hecho, el detector de inyección, el `MotorDePoliticas`, y las rutas `POST|GET /api/novels/{id}/interview/messages`, `POST /api/novels/{id}/free-texts`, `PATCH .../brief/extracted-facts/{fid}`, `GET .../brief`, `POST .../brief/confirm`, `GET|POST|DELETE .../banned-terms[/{tid}]` en el servidor: su forma, sus códigos y sus reglas → 008-brief-y-entrevista.
- Normalización y coincidencia de las prohibidas → 005-guardarrailes.
- Lista prohibida de nivel `user` → 023-mis-novelas.
- Pantalla de progreso (tras lanzar la generación) y pantalla de lectura → sus propias specs.
- Lanzar la generación (`POST .../runs`) → no es parte de esta pantalla.
- Marca corporativa (tokens de tema, logotipo) → `specs/000-scaffolding.md`.

## Comportamiento observable

**Convenciones.** La API simulada responde exactamente lo que definen los casos de 008-brief-y-entrevista para cada entrada; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta.

### Chat de la entrevista

#### 024-C01 — Historial vacío al entrar en una entrevista nueva (T)
- **Entrada:** la API responde con un historial de mensajes vacío y un brief en borrador vacío.
- **Salida:** el chat no muestra ningún mensaje y ofrece escribir el primero. El panel del brief muestra que todavía no hay nada fijado.

#### 024-C02 — Enviar un mensaje añade la respuesta del entrevistador (T)
- **Entrada:** la persona escribe «Se llama Marta y cumple 40» y lo envía; la API responde 200 con la respuesta del entrevistador y el brief con sus comprobaciones recalculadas.
- **Salida:** el chat muestra, en orden, el mensaje enviado y la respuesta del entrevistador. El panel del brief se actualiza con lo que ya no falta. Mientras la petición está en curso, el envío se deshabilita para no duplicar el mensaje.

#### 024-C03 — Fallo al enviar un mensaje (T)
- **Entrada:** la persona envía un mensaje; la API responde con un error (503 o 422).
- **Salida:** el chat no añade ninguna respuesta del entrevistador, muestra el motivo del fallo y deja el mensaje escrito disponible para reenviarlo. El historial y el brief quedan como estaban.

#### 024-C04 — Rechazo de un mensaje vacío antes de enviarlo (T)
- **Entrada:** la persona intenta enviar el chat sin haber escrito nada, o solo con espacios.
- **Salida:** no se hace ninguna petición a la API; el envío queda deshabilitado hasta que haya texto.

### Panel del brief

#### 024-C05 — El panel muestra lo fijado, lo que falta y las contradicciones (T)
- **Entrada:** la API responde con un brief que tiene algunos campos fijados, un `DatoFaltante` y una `Contradiccion` con sus campos implicados.
- **Salida:** el panel distingue visualmente lo ya fijado de lo que falta, y muestra la contradicción con los campos que implica. Ningún dato del brief se calcula en la pantalla: se muestra tal cual llega.

#### 024-C06 — Cota de obligatorios (T)
- **Entrada:** la API responde con el brief y su recuento de elementos obligatorios frente a `max_mandatory_elements`.
- **Salida:** el panel muestra ese recuento tal como lo entrega la API.

### Texto libre y hechos extraídos

#### 024-C07 — Enviar un texto libre y ver sus hechos verificados (T)
- **Entrada:** la persona escribe un texto libre y lo envía; la API responde 201 con la lista de `HechoExtraido` verificados de ese texto, sin aceptar y no obligatorios.
- **Salida:** cada hecho verificado aparece en una lista, con su sujeto, atributo y valor, y con una acción para aceptarlo o rechazarlo. El campo de texto libre queda vacío. Ningún hecho no verificado se muestra: la pantalla solo pinta lo que trae la respuesta.

#### 024-C08 — Aceptar y rechazar un hecho (T)
- **Entrada:** la persona pulsa aceptar sobre un hecho de la lista; la API responde 200. Después pulsa rechazar sobre otro; la API responde 200.
- **Salida:** el hecho aceptado queda marcado como parte del brief, sin recargar toda la pantalla; el rechazado deja de mostrarse como pendiente de decisión.

#### 024-C09 — Marcar un hecho obligatorio (T)
- **Entrada:** la persona marca como obligatorio un hecho ya aceptado; la API responde 200. Sobre un hecho sin aceptar, la API responde 422.
- **Salida:** en el primer caso, el hecho queda marcado obligatorio, sin recargar toda la pantalla. En el segundo, la marca no se aplica y la pantalla muestra el motivo del rechazo.

#### 024-C10 — Fallo al enviar un texto libre (T)
- **Entrada:** la persona envía un texto libre; la API responde con un error (422 o 503).
- **Salida:** no aparece ningún hecho nuevo, el texto escrito no se pierde y la pantalla muestra el motivo del fallo.

#### 024-C11 — Texto libre vacío no se envía (T)
- **Entrada:** la persona intenta enviar el texto libre sin haber escrito nada, o solo con espacios.
- **Salida:** no se hace ninguna petición a la API; el envío queda deshabilitado hasta que haya texto.

### Palabras y temas prohibidos de nivel `novel`

#### 024-C12 — Ver la lista prohibida de nivel `novel` (T)
- **Entrada:** la API responde con dos entradas: una palabra y un tema con sus palabras clave.
- **Salida:** la pantalla lista las dos, cada una con su término (y sus palabras clave, si es un tema), separada del resto de la pantalla.

#### 024-C13 — Añadir una palabra o un tema (T)
- **Entrada:** la persona da de alta la palabra «Cristina»; la API responde 201. Por separado, da de alta el tema «divorcio» con las palabras clave «separación» y «custodia»; la API responde 201.
- **Salida:** cada entrada nueva aparece en la lista, sin recargar toda la pantalla; el formulario de alta queda vacío para la siguiente.

#### 024-C14 — Alta rechazada o repetida (T)
- **Entrada:** la persona intenta dar de alta un tema sin palabras clave, una palabra con palabras clave o un término vacío (422 en cada caso); o un término ya presente con otra forma (409).
- **Salida:** ninguna entrada se añade a la lista; la pantalla muestra el motivo del rechazo junto al formulario.

#### 024-C15 — Borrar una entrada prohibida (T)
- **Entrada:** la persona borra una entrada de la lista, también una que registró el entrevistador; la API responde 204.
- **Salida:** la entrada desaparece de la lista, sin recargar toda la pantalla.

### Confirmación del brief

#### 024-C16 — Confirmar disponible solo sin problemas (T)
- **Entrada:** la API responde con un brief sin `DatoFaltante` ni `Contradiccion` y dentro de la cota; por separado, con un brief que tiene alguno de los tres problemas.
- **Salida:** en el primer caso, la acción de confirmar está disponible. En el segundo, está deshabilitada y la pantalla señala qué falta o qué contradicción lo impide, sin necesidad de pulsar para descubrirlo.

#### 024-C17 — Confirmar un brief válido lleva a la pantalla que sigue (T)
- **Entrada:** la persona pulsa confirmar; la API responde 200 con el brief confirmado.
- **Salida:** la pantalla deja de admitir cambios (chat, texto libre, hechos y lista prohibida quedan en solo lectura) y navega a la pantalla que sigue a un brief confirmado.

#### 024-C18 — Confirmación rechazada (T)
- **Entrada:** la persona pulsa confirmar; la API responde 422 con los problemas del brief.
- **Salida:** la pantalla sigue en la entrevista, editable, y muestra los problemas devueltos por la API junto a la acción de confirmar.

#### 024-C19 — Entrada en una novela con el brief ya confirmado (T)
- **Entrada:** la API responde, al abrir la pantalla, con un brief en estado confirmado.
- **Salida:** la pantalla se muestra en solo lectura desde el principio: se ve el historial, el brief, los hechos y la lista prohibida, pero no hay forma de enviar un mensaje, un texto libre, aceptar o rechazar un hecho, ni editar la lista prohibida.

### Recorrido visual (D, al final de la spec)

#### 024-C20 — Recorrido real de la entrevista (D)
- **Entrada:** con el servidor real y el login de Claude Code, el revisor sigue en un navegador una entrevista completa: mensajes, un texto libre con un hecho aceptado, una entrada prohibida de nivel `novel`, y la confirmación del brief.
- **Salida:** cada paso hace lo que describen 024-C01 a 024-C19 con el servidor real; la pantalla se ve con la marca corporativa (tokens de tema, logotipo) de `specs/000-scaffolding.md`. El resultado se anota en `docs/verification.md` §9.3.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 024-I1 | La pantalla nunca calcula por su cuenta faltantes, contradicciones, cota, verificación de un hecho ni disponibilidad de confirmar salvo lo que la propia API ya deja explícito (estado del brief): muestra tal cual lo que entrega la API | A | Revisión de que el componente no reimplementa reglas de 008; las recibe ya resueltas |
| 024-I2 | Ninguna llamada de esta pantalla a la API real fuera de 024-C20: las pruebas la sustituyen en el límite de `shared/api` | T | `frontend/AGENTS.md`: ninguna prueba T alcanza un backend real |
| 024-I3 | Un error de cualquier llamada de esta pantalla (mensaje, texto libre, aceptar o rechazar un hecho, alta o borrado prohibido, confirmar) siempre se muestra; nunca se descarta en silencio | T | 024-C03, 024-C10, 024-C14, 024-C18 |
| 024-I4 | El texto libre que la persona escribe nunca se envía por el mismo camino que un mensaje del chat, ni al revés: son dos acciones distintas con dos rutas distintas | A | Revisión de que el componente llama a `POST .../interview/messages` y a `POST .../free-texts` desde controles separados |
| 024-I5 | Con el brief confirmado, ninguna acción de escritura de esta pantalla (mensaje, texto libre, hecho, prohibida) queda disponible | T | 024-C19 |

## Docs referenciados

- `architecture.md`:
  - §3.1–§3.5 (entrevistador, extractor, validez del brief, texto libre, entrevista en la API) — para saber qué pantalla enseña qué dato, sin repetir sus reglas;
  - §14.8 (pantallas del frontend, FSD pages-first, la entrevista con chat, panel del brief, textos libres, hechos por aceptar y confirmación).
- `definitions.md`:
  - `Entrevista`, `Brief`, `DatoFaltante`, `Contradiccion`, `ElementoPersonal` (§1);
  - `TextoLibre`, `HechoExtraido` (§1, no confiable, solo lo verificado llega al cliente);
  - `ListaProhibida`, `EntradaProhibida` (§1, nivel `novel`).
- `specs/backend/008-brief-y-entrevista.md` (008-C01 a 008-C30: turnos, comprobaciones, confirmación, texto libre, hechos, listas `novel`) — referenciada, no duplicada.
- `specs/backend/005-guardarrailes.md` (forma normalizada de una entrada prohibida).
- `specs/frontend/022-acceso.md` (sesión y rutas protegidas, que esta pantalla hereda).
- `specs/frontend/023-mis-novelas.md` (cómo se llega a esta pantalla, y la lista prohibida de nivel `user`, fuera de aquí).
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).
- `docs/verification.md` §2 (clases T/A/I/D/U), §3.3 (integración con dobles; ninguna prueba T llama a un modelo o a un backend real), §9.3 (recorrido visual con Playwright MCP).
- `project-constraints.md` (entrevistador recoge datos del destinatario y las palabras o temas prohibidos; el resultado es un brief validado con schema).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban van abajo y en el informe.

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Confirmar deshabilitado o solo rechazado al pulsar? | Deshabilitado cuando hay faltantes o contradicciones, para lo más simple: evita un 422 evitable | Más fácil posible; 008-C16 sigue cubriendo el rechazo del servidor como red de seguridad (024-C18) |
| ¿Qué pasa con la pantalla si el brief ya está confirmado al entrar? | Solo lectura desde el principio, sin redirigir a otra pantalla: 008-C17 dice que las rutas de lectura siguen respondiendo 200 | §3.2 (inmutabilidad), decisión de esta spec para §18 |
| ¿Mensaje del chat y texto libre comparten un mismo campo? | No, dos controles distintos: el entrevistador nunca recibe un texto libre (§3.1), y mezclarlos en la UI arriesgaría confundir las dos rutas | §3.1; decisión de esta spec para §18 |
