# 002 — AUT · Autenticación y propiedad

- [x] Spec approved   <- only the user marks this

## Objetivo

Que cada cliente entre con su cuenta y solo pueda ver y tocar lo suyo por la API.

## Alcance

Cubre el registro, el acceso, el `TokenDeAcceso`, los 401 y los 404, la propiedad de cada recurso, las pruebas de aislamiento entre clientes por la API y la página de acceso. Columnas y parámetros del JWT: [001 design.md](../001-base/design.md) §4.2 y §5.9.

Depende de 001. Las rutas con id que recorre la prueba de aislamiento las añaden las specs siguientes, cada una con su recurso en el fixture de la prueba.

**Fuera de alcance:**

- La gestión de cuentas —renovar el token, recuperar la contraseña, el perfil, las reglas de complejidad de la contraseña y el límite de intentos de acceso—, que el encargo deja fuera («cuentas de usuario»).
- El aislamiento por MCP, que es de 016 con la misma identidad.
- La vista previa de una candidata, que no usa el `TokenDeAcceso` sino su propio token, emitido por el worker y canjeado por una cookie (013).

## Requisitos

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-AUT-1 | `POST /api/auth/register` con un email de formato válido que no tiene cuenta y una contraseña de 8 caracteres o más → 201; se crea el `Cliente` con su fecha de alta y la contraseña guardada con bcrypt, nunca en claro. Sin límite superior: con una contraseña de 100 caracteres también es 201, y se entra con ella | Obligatorio | T |
| RF-AUT-2 | `POST /api/auth/register` con un email sin formato válido, o con una contraseña de menos de 8 caracteres → 422 y no se crea nada. Frontera: 7 caracteres, 422; 8, 201 | Obligatorio | T |
| RF-AUT-3 | `POST /api/auth/register` con un email que ya tiene cuenta, también si solo difiere en mayúsculas → 409 y no se crea nada | Obligatorio | T |
| RF-AUT-4 | `POST /api/auth/login` con el email y la contraseña de una cuenta → 200 con `access_token`: un JWT firmado con HS256 y `JWT_SECRET`, con `sub` el id del cliente, `aud`, `iss` y `exp` a `operation.access_token_hours` desde la emisión. Con el `config.json` del repositorio, `exp` es la emisión más 24 horas | Obligatorio | T |
| RF-AUT-5 | `POST /api/auth/login` con un email que no tiene cuenta, sea cual sea su formato, o con una contraseña que no es la suya → 401, con la misma respuesta en los dos casos | Obligatorio | T |
| RF-AUT-6 | Una petición a cualquier endpoint de `/api` salvo el registro, el acceso y la vista previa, sin token, con el token caducado, con la firma inválida, o con un `aud` o un `iss` que no son los del servidor → 401 | Obligatorio | T |
| RF-AUT-7 | Una petición con un token válido → la API actúa como el cliente de su `sub`, y todo lo que crea queda a su nombre: novelas, briefs, entradas de su lista prohibida y entradas del audit log | Obligatorio | T |
| RF-AUT-8 | Para toda ruta de `/api` que nombra un recurso por su id, salvo las de la vista previa, el cliente B pide con su token un recurso del cliente A → 404, con la misma respuesta que para un id inexistente, y sin efecto: el recurso de A no cambia. Una prueba recorre todas las rutas del esquema OpenAPI con un fixture de A que tiene un recurso de cada tipo, así que cubre también las rutas que añadan las specs siguientes; entre ellas, la novela, la story bible y el PDF de RT4 (`verification.md` §4.9) | Obligatorio | T |
| RF-AUT-9 | Una ruta de `/api` que devuelve una lista → solo contiene recursos del cliente del token. La prueba de RF-AUT-8 lo comprueba en todas las listas con dos clientes | Obligatorio | T |
| RF-AUT-10 | La página `login` → permite registrarse y entrar con email y contraseña, y muestra el motivo de un 409 o un 422 del registro o de un 401 del acceso. Tras entrar, el cliente del frontend envía el token en la cabecera de autorización (`architecture.md` §14.4), y un 401 de cualquier otra petición vuelve a `login`, porque el token no se renueva. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 | Obligatorio | I |

## Docs de referencia

- `architecture.md` §9.7 (la vista previa), §13.1, §13.6, §14.3 (tabla de códigos), §14.4 y §16 («Autenticación», «Caducidades»).
- `definitions.md` §1 (`Cliente`), §10 (`TokenDeAcceso`), §11 (`access_token_hours`, `JWT_SECRET`) y §12.
- `verification.md` §4.9 (RT4), §5 («Autenticación y aislamiento entre clientes») y §9.3.
