# 023 — Mis novelas

> Carril: E · Depende de: 022-acceso, 005-guardarrailes, 008-brief-y-entrevista · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24); alcance mínimo en N1 (usuario, 2026-09-25, carril R)

## Objetivo

La pantalla «mis novelas»: lo primero que ve el cliente tras acceder. Muestra sus novelas con su estado derivado y su versión vigente, deja crear una novela nueva y gestionar su lista de palabras prohibidas de nivel `user`. Cubre la parte de pantalla de `architecture.md` §14.8; los datos que muestra los calcula y los sirve 008-brief-y-entrevista, que esta spec no repite.

## Alcance

**N1, mínima (usuario, 2026-09-25):** solo la lista de novelas (023-C01 a C06), ir a la lectura de las que tienen versión vigente (023-C09) y llegar aquí tras el acceso (023-C17). Crear novela (C07, C08) y las prohibidas de nivel `user` (C10 a C15) quedan «(recortado)»: la entrevista y las prohibidas van por la CLI (`architecture.md` §18, «Alcance del frontend»).

- Lista de las novelas del cliente: título, nombre del destinatario, estado derivado, versión vigente y fecha de creación, en el orden que entrega la API.
- Acción «crear novela»: crea una novela vacía y lleva a su entrevista.
- Ir de una novela de la lista a su pantalla, según su estado.
- Lista de palabras prohibidas de nivel `user`: verla, añadir una palabra o un tema con sus palabras clave, y borrar una entrada.
- Estados de carga y de error de las llamadas de esta pantalla.

## Fuera de alcance

- Sesión, token y qué pasa sin sesión válida → 022-acceso.
- Cálculo del estado derivado, de la versión vigente, y las rutas `GET /api/novels`, `POST /api/novels`, `GET|POST|DELETE /api/banned-terms[/{id}]` en el servidor: su forma, sus códigos y sus reglas de validación (tipo, palabras clave, duplicado) → 008-brief-y-entrevista.
- Normalización y coincidencia de las prohibidas → 005-guardarrailes.
- Contenido de la pantalla de entrevista, de progreso y de lectura, y qué hacen al llegar a ellas → 024-entrevista y las specs de esas pantallas.
- Lista prohibida de nivel `novel` (se edita desde la entrevista) → 024-entrevista.
- Importar un brief en JSON: no hay pantalla para ello (`architecture.md` §14.8 no la lista); solo la crea la CLI.
- Marca corporativa (tokens de tema, logotipo) → `specs/000-scaffolding.md`.

## Comportamiento observable

### Lista de novelas

#### 023-C01 — Lista vacía (T)
- **Entrada:** la API de novelas responde con una lista vacía.
- **Salida:** la pantalla muestra que el cliente no tiene ninguna novela todavía (en N1, sin botón de crear: la novela nace por la CLI). No hay tabla ni filas.

#### 023-C02 — Cada estado derivado tiene una etiqueta propia (T)
- **Entrada:** la API responde con una novela por cada estado de `definitions.md` §3: `interview`, `ready`, `in_progress`, `published`.
- **Salida:** cada novela muestra una etiqueta distinta, una por estado, siempre la misma para el mismo estado. Ningún estado se muestra sin etiqueta ni con una etiqueta genérica de «desconocido».

#### 023-C03 — Versión vigente, con número o vacía (T)
- **Entrada:** una novela `published` con versión vigente 2; una novela `ready` sin versión vigente.
- **Salida:** la primera muestra el número 2; la segunda no muestra ningún número de versión.

#### 023-C04 — Novela sin título todavía (T)
- **Entrada:** una novela cuyo título llega vacío de la API (`architecture.md` §14.8, antes de que exista el plan).
- **Salida:** la fila muestra un texto que marca que la novela aún no tiene título, en vez de dejar el hueco en blanco.

#### 023-C05 — La lista respeta el orden que entrega la API (T)
- **Entrada:** la API responde con tres novelas en un orden dado (de la más reciente a la más antigua, como fija 008-C02).
- **Salida:** la pantalla las pinta en ese mismo orden, sin reordenarlas por su cuenta.

#### 023-C06 — Fallo al cargar la lista (T)
- **Entrada:** la API de novelas responde con un error.
- **Salida:** la pantalla muestra que no se pudo cargar la lista, no muestra una lista vacía como si el cliente no tuviera novelas, y ofrece reintentar.

### Crear novela

#### 023-C07 — Crear una novela lleva a su entrevista (T, recortado)
- **Entrada:** el cliente pulsa «crear novela»; la API responde 201 con el id de la novela nueva.
- **Salida:** la pantalla navega a la entrevista de esa novela (024-entrevista). Mientras la petición está en curso, el botón se deshabilita para no duplicar la creación.

#### 023-C08 — Fallo al crear una novela (T, recortado)
- **Entrada:** el cliente pulsa «crear novela»; la API responde con un error.
- **Salida:** la pantalla se queda en «mis novelas», muestra el motivo del fallo, no navega a ninguna entrevista y el botón vuelve a estar disponible.

### Ir a una novela

#### 023-C09 — Solo las novelas con versión vigente llevan a su lectura (T)
- **Entrada:** la lista con una novela con versión vigente (p. ej. `published`, o `in_progress` tras un cambio del lector) y otra sin versión vigente (`interview`, `ready` o `in_progress` de su primera generación).
- **Salida:**
  - con versión vigente → la fila enlaza a su lectura (026-lectura), que abre la versión vigente (026-C01);
  - sin versión vigente → la fila muestra su estado sin enlace (la entrevista y el progreso no tienen pantalla en N1).

#### 023-C17 — El acceso lleva a «mis novelas» (T)
- **Entrada:** un acceso válido (022-C04).
- **Salida:** la pantalla que se abre es «mis novelas», con la lista de novelas del cliente.

### Palabras prohibidas de nivel `user`

#### 023-C10 — Ver la lista prohibida de nivel `user` (T, recortado)
- **Entrada:** la API responde con dos entradas: una palabra y un tema con sus palabras clave.
- **Salida:** la pantalla lista las dos, cada una con su término (y sus palabras clave, si es un tema), separada de la lista de novelas.

#### 023-C11 — Añadir una palabra (T, recortado)
- **Entrada:** el cliente escribe «Cristina» y confirma; la API responde 201 con la entrada creada.
- **Salida:** la entrada nueva aparece en la lista, sin recargar toda la pantalla. El campo queda vacío para la siguiente.

#### 023-C12 — Añadir un tema con sus palabras clave (T, recortado)
- **Entrada:** el cliente da de alta un tema «divorcio» con las palabras clave «separación» y «custodia»; la API responde 201.
- **Salida:** el tema aparece en la lista con sus dos palabras clave.

#### 023-C13 — Alta rechazada (T, recortado)
- **Entrada:** el cliente intenta dar de alta un tema sin palabras clave, una palabra con palabras clave, o un término vacío; la API responde 422 en cada caso.
- **Salida:** ninguna entrada se añade a la lista; la pantalla muestra el motivo del rechazo junto al formulario.

#### 023-C14 — Alta de un término repetido (T, recortado)
- **Entrada:** el cliente da de alta «pedro» cuando ya existe «Pedro»; la API responde 409.
- **Salida:** ninguna entrada se añade; la pantalla indica que el término ya está en la lista.

#### 023-C15 — Borrar una entrada (T, recortado)
- **Entrada:** el cliente borra una entrada de la lista; la API responde 204.
- **Salida:** la entrada desaparece de la lista, sin recargar toda la pantalla.

### Recorrido visual (D, al final de la spec)

#### 023-C16 — Recorrido real de «mis novelas» (D)
- **Entrada:** con el servidor real y un cliente con novelas en varios estados y alguna prohibida de nivel `user`, el revisor navega la pantalla con Playwright MCP.
- **Salida:** la lista, sus etiquetas de estado, el botón de crear y la lista prohibida se ven con la marca corporativa (tokens de tema, logotipo) de `specs/000-scaffolding.md`. El resultado se anota en `docs/verification.md` §9.3.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 023-I1 | Los cuatro estados derivados de `definitions.md` §3 tienen cada uno su etiqueta, y ningún otro valor cae en un caso por defecto silencioso | T (recortado) | 023-C02, con los cuatro estados en un solo barrido |
| 023-I2 | La pantalla nunca calcula el estado ni la versión vigente por su cuenta: muestra tal cual lo que entrega la API | A | Revisión de que el componente no combina campos de ejecuciones o versiones; los recibe ya resueltos |
| 023-I3 | Ninguna llamada de esta pantalla a la API real: las pruebas la sustituyen en el límite de `shared/api` | T (recortado) | `frontend/AGENTS.md`: ninguna prueba alcanza un backend real |
| 023-I4 | Un error de cualquier llamada de esta pantalla (lista, alta o borrado prohibido, crear novela) siempre se muestra; nunca se descarta en silencio ni dibuja una lista vacía en su lugar | T (recortado) | 023-C06, 023-C08, 023-C13, 023-C14 |

## Docs referenciados

- `architecture.md` §14.8 (pantallas del frontend, FSD pages-first), §14.3 (propiedad, todo recurso es del cliente), §12.1 (tres niveles de prohibidas, tipo palabra/tema).
- `definitions.md` §3 (Novela, estado derivado, versión vigente), §1 (`ListaProhibida`, `EntradaProhibida`).
- `specs/backend/008-brief-y-entrevista.md` (008-C01, 008-C02: crear y listar novelas con su estado; 008-C25, 008-C26: listas prohibidas `novel` y `user`) — referenciada, no duplicada.
- `specs/backend/005-guardarrailes.md` (forma normalizada de una entrada prohibida).
- `frontend/AGENTS.md` (FSD pages-first, límite de las pruebas al `shared/api`, recorrido visual como D).
- `docs/verification.md` §2 (clases T/A/I/D/U), §3.3 (integración con dobles; ninguna prueba T llama a un modelo o a un backend real), §9.3 (recorrido visual con Playwright MCP).

## Autorrevisión

Sin ronda de autorrevisión ni auditoría, por decisión del usuario (2026-09-24, `AGENTS.md`). Las decisiones que los docs no fijaban van abajo y en el informe.
