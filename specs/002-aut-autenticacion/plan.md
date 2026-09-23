# 002 — AUT · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: pruebas de API de que un cliente no accede a lo de otro, «Autenticación y aislamiento entre clientes», y la página `login` por TypeScript estricto, ESLint, `steiger`, build de producción e inspección con el browser MCP, «Frontend» (`docs/verification.md` §5).

### Steps
- [ ] `POST /api/auth/register` con un email de formato válido que no tiene cuenta y una contraseña de 8 caracteres o más → 201; se crea el `Cliente` con su fecha de alta y la contraseña guardada con bcrypt, nunca en claro. Sin límite superior: con una contraseña de 100 caracteres también es 201, y se entra con ella (RF-AUT-1)
  - El caso de 100 caracteres resuelve el **unsure** de [001 design.md](../001-base/design.md) §5.9, y comprueba además que otra contraseña con los mismos 72 primeros bytes no entra (RF-AUT-5): lance bcrypt o trunque en silencio, la contraseña pasa antes por SHA-256 en base64, como dice ese apartado.
- [ ] `POST /api/auth/register` con un email sin formato válido, o con una contraseña de menos de 8 caracteres → 422 y no se crea nada. Frontera: 7 caracteres, 422; 8, 201 (RF-AUT-2)
- [ ] `POST /api/auth/register` con un email que ya tiene cuenta, también si solo difiere en mayúsculas → 409 y no se crea nada (RF-AUT-3)
- [ ] `POST /api/auth/login` con el email y la contraseña de una cuenta → 200 con `access_token`: un JWT firmado con HS256 y `JWT_SECRET`, con `sub` el id del cliente, `aud`, `iss` y `exp` a `operation.access_token_hours` desde la emisión. Con el `config.json` del repositorio, `exp` es la emisión más 24 horas (RF-AUT-4)
  - `access_token_hours` se lee de la config; `aud` e `iss` son los de 001 design.md §5.9.
- [ ] `POST /api/auth/login` con un email que no tiene cuenta, sea cual sea su formato, o con una contraseña que no es la suya → 401, con la misma respuesta en los dos casos (RF-AUT-5)
  - Un email sin formato válido en el acceso es un 401, no el 422 de schema de RF-BAS-38.
- [ ] Una petición a cualquier endpoint de `/api` salvo el registro, el acceso y la vista previa, sin token, con el token caducado, con la firma inválida, o con un `aud` o un `iss` que no son los del servidor → 401 (RF-AUT-6)
  - La prueba recorre las rutas del esquema OpenAPI, así que cubre las que añadan las specs siguientes. Una ruta desconocida bajo `/api` no es un endpoint: sigue en el 404 de RF-BAS-37.
  - Un token sin `exp`, `aud` o `iss` no es un `TokenDeAcceso` (`definitions.md` §10): da 401 como uno con esos campos inválidos.
- [ ] Una petición con un token válido → la API actúa como el cliente de su `sub`, y todo lo que crea queda a su nombre: novelas, briefs, entradas de su lista prohibida y entradas del audit log (RF-AUT-7)
  - En 002 aún no hay rutas que creen esos recursos: el caso comprueba el cliente con el que actúa una petición. El fixture de RF-AUT-8 crea con el token de A, por su ruta, cada recurso que tenga ruta de creación, así que la prueba de aislamiento cubre también que lo creado quede a nombre de A.
  - Las entradas del audit log no tienen ruta de creación: el cliente de cada una lo guarda el motor de políticas, en 003 (RF-POL-13).
- [ ] Para toda ruta de `/api` que nombra un recurso por su id, salvo las de la vista previa, el cliente B pide con su token un recurso del cliente A → 404, con la misma respuesta que para un id inexistente, y sin efecto: el recurso de A no cambia. Una prueba recorre todas las rutas del esquema OpenAPI con un fixture de A que tiene un recurso de cada tipo, así que cubre también las rutas que añadan las specs siguientes; entre ellas, la novela, la story bible y el PDF de RT4 (`verification.md` §4.9) (RF-AUT-8)
  - La prueba falla ante una ruta con id cuyo tipo no tiene recurso en el fixture: la spec que añade la ruta añade su recurso.
  - En 002 aún no hay rutas con id: el recorrido se prueba sobre una aplicación de prueba con una ruta que no comprueba el propietario, que el recorrido tiene que cazar.
- [ ] Una ruta de `/api` que devuelve una lista → solo contiene recursos del cliente del token. La prueba de RF-AUT-8 lo comprueba en todas las listas con dos clientes (RF-AUT-9)
  - Igual que en RF-AUT-8, en 002 el recorrido se prueba sobre una lista de prueba que devuelve también lo de otro cliente.
- [ ] La página `login` → permite registrarse y entrar con email y contraseña, y muestra el motivo de un 409 o un 422 del registro o de un 401 del acceso. Tras entrar, el cliente del frontend envía el token en la cabecera de autorización (`architecture.md` §14.4), y un 401 de cualquier otra petición vuelve a `login`, porque el token no se renueva. Una inspección con el browser MCP lo comprueba y deja su fila en `verification.md` §9.3 (RF-AUT-10 · clase I)
  - El 401 del acceso muestra su motivo en la página; no es la vuelta a `login` de las demás peticiones.
  - En 002 ninguna página pide una ruta protegida: la inspección lanza una petición con el cliente del frontend desde la página y simula su 401 en el navegador.
  - La misma inspección comprueba el tema corporativo en la página, como pide RF-BAS-48 de 001 a cada spec que añade una.

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
