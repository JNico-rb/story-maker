# 002 — Autenticación

> Carril: C · Depende de: 001-base · Estado: borrador

## Objetivo

Que cada `Cliente` se registre y entre con email y contraseña, que la API lo identifique solo por su `TokenDeAcceso` y que todo lo de otro cliente le responda como inexistente. Esta spec fija la regla de identidad y de propiedad que cumplen todas las rutas de `/api`, con la prueba que las recorre una a una. El servidor MCP (015) usa la misma verificación del token. Cubre las filas O.14, O.15 y O.17 de `verification.md` §5, y la parte de API de O.6, O.16, RT6 y RT13.

## Alcance

- **Registro** (`POST /api/auth/register {email, password}` → 201) y **acceso** (`POST /api/auth/login {email, password}` → `{access_token}`), con las reglas de forma del email y de la contraseña.
- La contraseña se guarda solo como hash bcrypt, en el `Cliente` que crea la spec 001-base.
- **Emisión del `TokenDeAcceso`**: JWT HS256 firmado con `JWT_SECRET`, con `exp`, `aud` e `iss`, que caduca a las `operation.access_token_hours` (§14.3).
- **Verificación del token** en toda ruta de `/api` salvo el registro y el acceso: 401 si falta, si está mal formado o si no es válido.
- **Regla de propiedad**: un recurso de otro cliente se trata igual que uno inexistente (404) y no cambia nada. Se aplica a la novela y a todo lo que cuelga de ella, a la ejecución, a la solicitud de cambio y a la entrada prohibida de nivel `user`. Los recursos anidados se buscan dentro de su padre, un listado solo devuelve lo del cliente, y el propietario de lo que se crea sale del token.
- **La prueba por ruta** de O.17: recorre todas las rutas de `/api` que tenga la aplicación. Cada ruta que integra otra spec entra en ella sin que esa spec escriba otra.

## Fuera de alcance

- Esquema de `users` y columnas de propietario de cada tabla; validación de `JWT_SECRET` (32 caracteres o más) y de `access_token_hours` al arrancar → 001-base (§15.4–§15.6).
- Las rutas de cada recurso y lo que responden al propietario → 008-brief-y-entrevista (novelas, entrevista, textos libres, brief, listas prohibidas de nivel `user` y `novel`), 009-story-bible-y-versiones, 011-produccion-de-capitulos (ejecuciones), 013-lectura-y-pdf (versiones y PDF), 014-cambios-del-lector, 018-linters-de-prosa, 019-edicion-manual. Esta spec fija la regla que cumplen; no las implementa.
- Identidad en el servidor MCP: token en cada tool, `list_novels` y `download_novel` solo con lo del cliente (O.6, RT7) → 015-servidor-mcp, con la verificación de esta spec.
- Token de vista y `/view/versions/{version_id}` → 013-lectura-y-pdf. Aquí solo se exige que un token con la audiencia del de vista no valga como `TokenDeAcceso` (002-C13).
- Gestión de cuentas (§14.3; el encargo deja fuera las cuentas de usuario): renovación del token, cierre de sesión en el servidor o revocación, recuperación o cambio de la contraseña, verificación del email, borrado de la cuenta y roles. El «editor humano» es el propio cliente (`definitions.md`, `Cliente`).
- Límite de intentos de acceso → riesgo aceptado (002-I6).
- Pantallas de registro, acceso y rutas protegidas → 022-acceso. Auditoría con agente de RT6, RT7 y RT13 → 021-auditoria-de-seguridad.
- Qué cliente es propietario de las novelas que crea la CLI (`example`, `evals run`) → 013-lectura-y-pdf y 020-evals.

## Comportamiento observable

**Convenciones.** A y B son dos clientes registrados, con `cliente-a@example.com` y `cliente-b@example.com` y contraseñas de prueba. El «token de X» es el `TokenDeAcceso` que devuelve el acceso de X y viaja en la cabecera `Authorization: Bearer <token>`. El reloj es controlable. Salvo que el caso diga otra cosa, `access_token_hours` vale 24 y `JWT_SECRET` es un secreto de prueba con marcador. Una **ruta protegida** es cualquier ruta de `/api` salvo el registro y el acceso.

### Registro

#### 002-C01 — Registro válido (T)
- **Entrada:** `POST /api/auth/register {email: "cliente-a@example.com", password: <8 caracteres o más>}`.
- **Salida:** 201 con `{id, email}` y ningún otro campo. Existe un `Cliente` con ese email y con su fecha de alta. Lo que se guarda de la contraseña es un hash bcrypt que la verifica y que no la contiene.

#### 002-C02 — El email se guarda normalizado (T)
- **Entrada:** registro con `"  Cliente-A@Example.COM "`.
- **Salida:** 201 con `email: "cliente-a@example.com"`: sin los espacios de los extremos y en minúsculas. Así se guarda.

#### 002-C03 — Un email ya registrado no crea otra cuenta (T)
- **Entrada:** con A registrado, un registro con `"CLIENTE-A@example.com"` y otra contraseña.
- **Salida:** 409. No se crea ningún cliente. A sigue entrando con su contraseña original, y la nueva da 401.

#### 002-C04 — Email sin forma de email (T)
Después de normalizar (002-C02):

| Email | Resultado |
|---|---|
| Sin arroba (`cliente-a.example.com`) | 422 |
| Con dos arrobas | 422 |
| Parte local vacía (`@example.com`) | 422 |
| Dominio sin punto (`cliente-a@example`) | 422 |
| Dominio que empieza o acaba en punto | 422 |
| Con un espacio interior | 422 |
| 255 caracteres, bien formado | 422 |
| 254 caracteres, bien formado | 201 |

En los 422 no se crea nada.

#### 002-C05 — Contraseña en sus límites (T)
Los caracteres se cuentan como caracteres Unicode y los bytes, en UTF-8:

| Contraseña | Resultado |
|---|---|
| 7 caracteres ASCII | 422 |
| 8 caracteres ASCII | 201 |
| 72 caracteres ASCII (72 bytes) | 201 |
| 73 caracteres ASCII (73 bytes) | 422 |
| 24 veces «€» (24 caracteres, 72 bytes) | 201 |
| 25 veces «€» (75 bytes) | 422 |

Ningún 422 reproduce la contraseña enviada: ni el valor ni un fragmento aparecen en la respuesta.

#### 002-C06 — Registro con cuerpo incompleto (T)
- **Entrada:** sin `email`, sin `password`, o con alguno que no es texto.
- **Salida:** 422. No se crea nada.

### Acceso

#### 002-C07 — Acceso válido (T)
- **Entrada:** en el instante t0, `POST /api/auth/login` con el email y la contraseña de A.
- **Salida:** 200 con `{access_token}`. El token es un JWT HS256 firmado con `JWT_SECRET` que lleva exactamente estas reclamaciones:

| Reclamación | Valor |
|---|---|
| `sub` | el id de A |
| `iat` | t0 |
| `exp` | t0 + `access_token_hours` horas |
| `aud` | `access_token` |
| `iss` | `story-maker` |

Ni el email ni ningún otro dato del cliente van en el token.

#### 002-C08 — Al entrar, el email no distingue mayúsculas (T)
- **Entrada:** acceso con `"CLIENTE-A@EXAMPLE.COM "` y la contraseña de A.
- **Salida:** 200 con un token cuyo `sub` es el id de A.

#### 002-C09 — Credenciales incorrectas (T)
Todas las filas responden 401 con **el mismo cuerpo** y sin token:

| Entrada | Resultado |
|---|---|
| Email de A con una contraseña equivocada | 401 |
| Email no registrado | 401 |
| Contraseña vacía | 401 |
| Contraseña de 73 bytes o más | 401, nunca 500 |
| Email sin forma de email | 401, no 422: el acceso no revela las reglas del registro |

#### 002-C10 — Acceso con cuerpo incompleto (T)
- **Entrada:** sin `email`, sin `password`, o con alguno que no es texto.
- **Salida:** 422.

### Token en las rutas protegidas

#### 002-C11 — Un token válido identifica al cliente (T)
- **Entrada:** una petición a una ruta protegida con el token de A. El esquema `Bearer` se acepta con cualquier mezcla de mayúsculas.
- **Salida:** la ruta atiende la petición como A. Con el token de B, como B.

#### 002-C12 — Sin token, o con el token mal presentado, responde 401 (T)
Cada 401 lleva la cabecera `WWW-Authenticate: Bearer` y un mismo cuerpo, igual para cualquier causa de este caso y del 002-C13:

| Entrada | Resultado |
|---|---|
| Sin cabecera `Authorization` | 401 |
| Esquema `Basic` con credenciales | 401 |
| `Bearer` sin token | 401 |
| Token válido en la query (`?token=`) o en una cookie, sin cabecera | 401 |
| Un texto que no es un JWT | 401 |

#### 002-C13 — Un token manipulado o de otro uso responde 401 (T)

| Token | Resultado |
|---|---|
| El de A con un carácter de la firma cambiado | 401 |
| El de A con `sub` cambiado al id de B y la firma original | 401 |
| Firmado con un secreto distinto de `JWT_SECRET` | 401 |
| `alg: none` y sin firma | 401 |
| Firmado con `JWT_SECRET` pero con otro algoritmo (HS512) | 401 |
| Sin `exp` | 401 |
| Con `aud` = `view_token`, la del token de vista, aunque lo demás sea válido | 401 |
| Con otro `iss` | 401 |
| Sin `sub`, o con un `sub` que no es el id de ningún cliente | 401 |

#### 002-C14 — La caducidad en su límite (T)
Token de A emitido en t0:

| `access_token_hours` | Instante de la petición | Resultado |
|---|---|---|
| 24 | t0 + 24 h − 1 s | atendida |
| 24 | t0 + 24 h | 401 |
| 24 | t0 + 24 h + 1 s | 401 |
| 1 | t0 + 1 h − 1 s | atendida |
| 1 | t0 + 1 h | 401 |

La caducidad sale de la config, no de una constante.

#### 002-C15 — El token se comprueba antes que la propiedad (T)
- **Entrada:** sin token, o con uno caducado, una petición a una ruta que lleva el id de un recurso de A o un id inexistente.
- **Salida:** 401, nunca 404. Sin token no se sabe si el recurso existe.

### Propiedad

**Mundo de partida** de 002-C16 a 002-C21:
- A tiene una novela con su brief, una ejecución, una versión publicada con sus capítulos, una solicitud de cambio, un hecho extraído, una entrada prohibida de nivel `novel` y una de nivel `user`.
- B tiene lo mismo, con otros valores.
- Hay además una entrada prohibida de nivel `global`.

#### 002-C16 — Lo ajeno responde como inexistente (T)

| Recurso de A | Rutas (§15.7) | B con el id de A | B con un id inexistente | A con su id |
|---|---|---|---|---|
| Novela | `/api/novels/{id}` y todas las que cuelgan de ella | 404 | 404, mismo cuerpo | no 404 |
| Ejecución | `/api/runs/{id}` y las que cuelgan de ella | 404 | 404, mismo cuerpo | no 404 |
| Solicitud de cambio | `/api/change-requests/{id}` y las que cuelgan de ella | 404 | 404, mismo cuerpo | no 404 |
| Entrada prohibida de nivel `user` | `/api/banned-terms/{id}` | 404 | 404, mismo cuerpo | no 404 |

El código y el cuerpo que recibe B con el id de A son idénticos a los de un id inexistente. La ejecución y la solicitud de cambio son del propietario de su novela.

#### 002-C17 — Un recurso anidado solo existe dentro de su padre (T)
- **Entrada:** B, sobre su propia novela, pide el id de un hecho extraído (`{fid}`) o de una entrada de nivel `novel` (`{tid}`) que pertenecen a la novela de A. B pide también la versión `{v}` = 1 y el capítulo `{n}` = 1 de su novela.
- **Salida:** con los ids de A, 404, idéntico al de un id inexistente. La versión y el capítulo se buscan en la novela de la ruta, así que B obtiene su v1 y su capítulo 1, nunca los de A.

#### 002-C18 — Una entrada global no es de ningún cliente (T)
- **Entrada:** A y B piden o borran por `/api/banned-terms/{id}` la entrada de nivel `global`.
- **Salida:** 404 para los dos, idéntico al de un id inexistente. La entrada sigue existiendo.

#### 002-C19 — Un listado solo contiene lo del cliente (T)
- **Entrada:** B pide los listados de la API (`GET /api/novels`, `GET /api/banned-terms`) con A y B en el mundo de partida, y después con A dueño de dos novelas más.
- **Salida:** B solo recibe lo suyo, y su respuesta es la misma en las dos situaciones. A recibe lo suyo, sin nada de B.

#### 002-C20 — Lo ajeno no cambia nada (T)
- **Entrada:** B manda, con ids de A, peticiones que escriben: borrar la entrada de nivel `user` de A, confirmar el brief de A, reanudar la ejecución de A o confirmar su solicitud de cambio.
- **Salida:** 404, igual que con un id inexistente. La base queda idéntica antes y después, y el estado del recurso no revela nada: un brief ya confirmado de A también da 404, no 409.

#### 002-C21 — El propietario de lo creado es el cliente del token (T)
- **Entrada:** con el token de B, una petición que crea un recurso lleva en el cuerpo, además, un campo con el id de A (por ejemplo `user_id`).
- **Salida:** el recurso creado es de B: B lo ve en sus listados y A no, y A recibe 404 con su id. El campo se ignora.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 002-I1 | La contraseña nunca queda en claro: no está en SQLite, en ninguna respuesta (tampoco en los 422) ni en el token | T | 002-C01 y 002-C05. Además, tras un registro, una prueba busca la contraseña en los bytes del fichero SQLite y en cada respuesta del flujo registro → acceso, y no la encuentra |
| 002-I2 | Toda ruta de `/api` salvo el registro y el acceso exige un `TokenDeAcceso` válido | T | Prueba que recorre todas las rutas y métodos de `/api` que tiene la aplicación, las que haya en cada momento. Sin token, cada una responde 401 con `WWW-Authenticate: Bearer`. La lista de rutas públicas tiene exactamente las dos |
| 002-I3 | Para B, un recurso de A es indistinguible de uno inexistente y no cambia nada: el mismo código y el mismo cuerpo, 404 si la petición es por lo demás válida, y la base intacta. Excepción declarada: la posición en la cola cuenta las ejecuciones de todos los clientes (§9.1, `verification.md` §6 U16). Revela un número, no un recurso | T | La prueba parametrizada por ruta de O.17 (RT6). Recorre toda ruta de `/api` con un identificador de recurso en el camino (los tipos de §15.7: novela, ejecución, solicitud de cambio, entrada de nivel `user`, hecho extraído, entrada de nivel `novel`, número de versión y de capítulo). Llama a cada ruta como B con el id de A y con uno inexistente, y compara código, cuerpo y huella de la base. Si una ruta lleva un identificador de otro tipo, la prueba falla: esa ruta está fuera de §15.7. Al cerrar 002 todavía no hay rutas de recurso, así que la prueba se ejerce con una ruta de prueba por tipo, montada solo en las pruebas. El `verificador` de cada spec que añade rutas (008, 009, 011, 013, 014, 018, 019) comprueba que la prueba las recorre |
| 002-I4 | El cliente de una petición sale solo del token: ningún campo de cuerpo, parámetro ni cabecera de la API, salvo `Authorization`, identifica a un cliente | T | Prueba sobre el esquema OpenAPI de la aplicación: ninguna entrada declara un campo de cliente o de propietario. Más 002-C21 |
| 002-I5 | La identidad y la propiedad se deciden en un solo punto, compartido por las rutas de la API y por el servidor MCP (015). Ninguna ruta ni tool verifica el token ni la propiedad por su cuenta | I | `verificador`, al cerrar esta spec, la 015 y cada spec que añade rutas |
| 002-I6 | Sin límite de intentos de acceso: la fuerza bruta de contraseñas no se frena. Además, el registro revela con 409 que un email ya tiene cuenta | U | Riesgo propuesto para `verification.md` §6. Motivo: la gestión de cuentas está fuera de alcance (§14.3) y no hay despliegue en producción. Mitigación parcial: el mínimo de 8 caracteres, bcrypt y la misma respuesta para un email desconocido y una contraseña equivocada (002-C09) |

## Scores y trazas

No aplica. El registro y el acceso no ejecutan validadores ni abren trazas (`architecture.md` §13.1). Tampoco escriben en el `AuditLog`, cuyos orígenes no incluyen el acceso (§12.2).

## Docs referenciados

- `architecture.md`:
  - §14.3: bcrypt, JWT HS256 con `JWT_SECRET`, `exp`, `aud` e `iss`, 24 h, sin gestión de cuentas, lo ajeno responde 404.
  - §14.4: el mismo token en la cabecera de autorización, también en MCP.
  - §14.2: el token de vista, firmado con el mismo secreto.
  - §15.7: rutas, 401 salvo registro y acceso, 404, 409 y 422.
  - §15.4 y §15.5: `access_token_hours` y `JWT_SECRET`.
  - §15.6: `users` y la propiedad de cada tabla.
  - §15.9: `api` compone.
  - §9.1: posición en la cola.
  - §12.2 y §13.1: el acceso no deja audit log ni trazas.
- `definitions.md`:
  - §1: `Cliente` y su invariante de propiedad.
  - §10: `TokenDeAcceso`, `VistaDeVersion` (token de vista), `ServidorMCP`.
  - §11.1: `operation.access_token_hours`.
  - §11.3: `JWT_SECRET`.
  - §12.1: identificadores `user`, `access_token`, `view_token`.
- `verification.md`:
  - §2: clases.
  - §3.3: autenticación y propiedad con dobles.
  - §3.5: contrato de la API con 401 y 404.
  - §4.9: RT6 y RT13, y RT7 para 015.
  - §5: O.6, O.14, O.15, O.16 y O.17.
  - §6: U16.
- `project-constraints.md`: «Login de usuarios con SQLite» (opcional) y «Fuera de alcance» (cuentas de usuario).
- `backend/AGENTS.md`: la propiedad de la 002 es `api/` (autenticación, dependencia de cliente actual y propiedad) y `store/` (repositorio de clientes).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué entrega la 002 y qué las demás? | La 002 entrega el registro, el acceso, el token y la regla de identidad y propiedad con su prueba por ruta. Las rutas de cada recurso son de sus specs | `TODO.md` (Specs), `backend/AGENTS.md` |
| ¿Cómo se prueba la propiedad «por endpoint» si las rutas aún no existen? | La prueba recorre las rutas reales de la aplicación, así que cubre cada ruta al integrarse. Al cerrar la 002, se ejerce con una ruta de prueba por tipo de identificador | `verification.md` §5 O.17. Decisión para §18 |
| ¿Qué código para un email duplicado? | 409, porque el estado no admite la operación | §15.7. **Hueco del doc**: su tabla de 409 no lo lista |
| ¿Reglas de email y contraseña? | Email: forma sintáctica, 254 caracteres como mucho, sin espacios en los extremos y en minúsculas. Contraseña: de 8 caracteres a 72 bytes, el límite de bcrypt | **Hueco del doc** → decisión para §18 |
| ¿Valores de `aud` e `iss`? | `aud` = `access_token`; el token de vista usará `view_token`, que es su identificador de §12.1. `iss` = `story-maker`. Así un token de vista, firmado con el mismo secreto, no vale como `TokenDeAcceso` | §14.2, §14.3, `definitions.md` §12.1. Decisión para §18 |
| ¿Por dónde viaja el token? | Solo en la cabecera `Authorization`, nunca en la query ni en una cookie. La query es solo del token de vista | §14.4, §14.2 |
| ¿Distingue algo un 401? | No: un mismo cuerpo para cualquier causa del token. En el acceso, el mismo para un email desconocido y para una contraseña equivocada | §14.3 («sin revelar que existe») |
| ¿Deja el acceso audit log o trazas? | No | §12.2 (orígenes), §13.1 (trazas) |
| ¿Límite de intentos? | Fuera, como riesgo U | §14.3 (gestión de cuentas fuera). Propuesta para `verification.md` §6 |
| ¿La salud de 001-base puede ir bajo `/api` sin token? | No: contradiría §15.7 y 002-I2. Va fuera de `/api` o 001-base declara el conflicto | §15.7. Aviso al integrador |
| ¿La posición en la cola filtra datos de otros? | Solo un número; queda como excepción declarada en 002-I3 | §9.1, `verification.md` §6 U16 |
| ¿Quién es el propietario de lo que crea la CLI? | Fuera de la 002 | **Hueco del doc** → 013-lectura-y-pdf, 020-evals |
