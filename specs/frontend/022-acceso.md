# 022 — Acceso

> Carril: E · Depende de: 000-scaffolding, 002-autenticacion · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Que la persona se registre, entre y salga de la sesión desde la SPA, que toda pantalla protegida exija esa sesión y que los errores del servidor (registro duplicado, datos inválidos, credenciales incorrectas) se vean en el formulario. Cubre la parte de frontend de O.14 y O.15, y la fila 2.1 de `verification.md` §5 en lo que depende de entrar.

## Alcance

- Formulario de registro (email, contraseña) y formulario de acceso (email, contraseña), con sus mensajes de error.
- Guardado del token que devuelve el acceso, su envío en cada petición a una ruta protegida y su borrado al cerrar sesión o al recibir una respuesta no autorizada.
- Redirección a la pantalla de acceso cuando no hay sesión guardada o cuando el servidor la rechaza.
- Que las pantallas de acceso y registro llevan la marca común de la SPA.

## Fuera de alcance

- Las reglas de forma del email y la contraseña, el formato exacto de cada código (201/401/409/422) y la regla de identidad y propiedad → 002-autenticacion: aquí solo se observa que la SPA muestra lo que la API responde.
- La cabecera y los tokens de marca (logotipo, paleta, tipografía) → 000-scaffolding: aquí solo se observa que las pantallas de acceso la reutilizan.
- El contenido de las pantallas que siguen a entrar (mis novelas, entrevista, progreso, lectura) → sus propias specs de frontend.
- Renovación de sesión, recuperación de contraseña, verificación de email, límite de intentos, cierre de sesión en el servidor → fuera de alcance del producto (`architecture.md` §14.3).
- El token de vista de `VistaDeVersion` → 013-lectura-y-pdf; no es el `TokenDeAcceso` de esta spec.
- Auditoría de suplantación de token (RT13) y de fuerza bruta → 021-auditoria-de-seguridad.

## Comportamiento observable

**Convenciones.** La API simulada responde exactamente lo que definen los casos de 002-autenticacion para cada entrada; aquí se describe solo lo que la persona ve y lo que la SPA hace con esa respuesta. «Sesión guardada» es el estado, en el navegador de la persona, de tener un token recibido de un acceso válido y no haberlo borrado todavía.

### Registro

#### 022-C01 — Registro válido lleva a la pantalla de acceso (T)
- **Entrada:** la persona rellena el formulario de registro con un email y una contraseña válidos y lo envía; la API simulada responde con éxito.
- **Salida:** la SPA muestra la pantalla de acceso con un aviso de que la cuenta se creó, y el campo de email viene ya relleno con el que se acaba de registrar. Ninguna sesión queda guardada.

#### 022-C02 — Registro con un email ya usado (T)
- **Entrada:** el formulario de registro se envía con un email para el que la API simulada responde que ya existe una cuenta.
- **Salida:** la SPA se queda en el formulario de registro y muestra un mensaje de que ese email ya tiene cuenta, junto al campo de email. La contraseña escrita desaparece del formulario. Ninguna sesión queda guardada.

#### 022-C03 — Errores de datos inválidos, campo a campo (T)
- **Entrada:** el formulario de registro, y por separado el de acceso, se envían con datos para los que la API simulada responde que alguno no tiene forma válida (email mal formado, contraseña fuera de sus límites, un campo vacío).
- **Salida:** en cada formulario, junto al campo que la API señaló, aparece su mensaje; los demás campos conservan lo escrito salvo la contraseña, que se borra; el formulario sigue activo y se puede corregir y reenviar.

### Acceso

#### 022-C04 — Acceso válido guarda la sesión y entra (T)
- **Entrada:** la persona rellena el formulario de acceso con un email y una contraseña para los que la API simulada responde con un token, y lo envía.
- **Salida:** queda una sesión guardada con ese token; la SPA deja la pantalla de acceso y muestra la pantalla principal de la aplicación (la que sigue a entrar).

#### 022-C05 — Credenciales incorrectas (T)
- **Entrada:** el formulario de acceso se envía con un email y una contraseña para los que la API simulada responde que no son válidos.
- **Salida:** la SPA se queda en el formulario de acceso con un mismo mensaje genérico de credenciales incorrectas, sin decir si el email existe; la contraseña escrita desaparece; ninguna sesión queda guardada.

### Rutas protegidas

#### 022-C06 — Cada petición a una pantalla protegida envía la sesión guardada (T)
- **Entrada:** con una sesión guardada, la persona abre una pantalla protegida que pide datos a la API.
- **Salida:** cada petición que la pantalla hace lleva el token de la sesión guardada; ninguna lo lleva en la dirección de la petición.

#### 022-C07 — Sin sesión guardada, una pantalla protegida redirige a acceso (T)
- **Entrada:** sin ninguna sesión guardada, la persona abre directamente una pantalla protegida.
- **Salida:** la SPA muestra la pantalla de acceso sin haber pedido datos a la API para esa pantalla.

#### 022-C08 — Una sesión rechazada por el servidor redirige a acceso (T)
- **Entrada:** con una sesión guardada, una petición a una pantalla protegida recibe de la API simulada una respuesta de sesión no válida (caducada, alterada o de otro uso).
- **Salida:** la sesión guardada se borra y la SPA muestra la pantalla de acceso. Una petición posterior a otra pantalla protegida ya no lleva ese token.

### Cierre de sesión

#### 022-C09 — Cerrar sesión borra la sesión guardada sin avisar al servidor (T)
- **Entrada:** con una sesión guardada, la persona pide cerrar sesión desde la pantalla principal.
- **Salida:** la sesión guardada desaparece y la SPA muestra la pantalla de acceso; la SPA no hace ninguna petición a la API para este cierre.

### Marca y recorrido completo

#### 022-C10 — El recorrido completo se observa en el navegador (D)
- **Entrada:** con el servidor real, se sigue en un navegador el recorrido registro → acceso → pantalla principal → cierre de sesión, y se visita una pantalla protegida sin haber entrado.
- **Salida:** las pantallas de registro y acceso muestran la misma marca (logotipo, paleta, tipografía) que el resto de la SPA; cada paso del recorrido hace lo que describen 022-C01 a 022-C09 con el servidor real, no con la API simulada.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 022-I1 | El token de la sesión solo viaja en la cabecera de autorización de cada petición: nunca en la dirección de la petición ni en una cookie | T | 022-C06 |
| 022-I2 | Ninguna contraseña escrita en un formulario queda guardada ni se vuelve a mostrar tras enviarse, la petición salga bien o mal | T | 022-C01 a 022-C05 |
| 022-I3 | Una sesión guardada sobrevive a volver a cargar la pantalla, hasta que se cierra sesión o el servidor la rechaza | T | Recarga simulada tras 022-C04, después de la cual 022-C06 sigue cumpliéndose |
| 022-I4 | Una pantalla protegida nunca pide datos a la API antes de comprobar que hay una sesión guardada | T | 022-C07 |
| 022-I5 | Las pantallas de acceso y registro usan los mismos tokens de marca que el resto de la SPA, nunca un color o una tipografía propios | I | 022-C10; inspección del browser MCP (`verification.md` §9.3), registrada junto a P.1 |

## Docs referenciados

- `architecture.md`:
  - §14.1: pantallas de la lectura, para saber qué queda fuera de esta spec.
  - §14.3: registro y acceso con email y contraseña, `TokenDeAcceso`, sin renovación ni recuperación.
  - §14.8: páginas de la SPA (acceso entre ellas), marca corporativa, mismo origen que `/api`.
- `definitions.md`:
  - `Cliente`: quien se registra y entra.
  - `TokenDeAcceso`: qué identifica a la sesión y dónde caduca.
- `verification.md`:
  - §2: clases T/A/I/D/U.
  - §5: O.14, O.15 (parte de frontend), 2.1, P.1.
  - §9.3: inspecciones con el browser MCP.
- `specs/backend/002-autenticacion.md`: forma exacta de cada respuesta (201/401/409/422), reglas de email y contraseña, qué es un token rechazado.
- `specs/000-scaffolding.md`: tokens de marca y cabecera común que estas pantallas reutilizan.
- `frontend/AGENTS.md`: organización por pantallas, pruebas con la API simulada en el límite del cliente.
