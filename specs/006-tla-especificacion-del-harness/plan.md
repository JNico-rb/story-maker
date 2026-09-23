# 006 — TLA · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: TLC sobre las tres especificaciones con el modelo pequeño, cada una con una configuración positiva y una negativa, en CI (`docs/verification.md` §3.12, §4.10); es la parte de TLA+ de las filas «Invariantes 8, 9, 10 y 11», «Orquestador, fases, reanudación y cola», «Regeneraciones concurrentes» y «Confirmación de un cambio», cuyas integraciones son de 007 y 015 (`docs/verification.md` §5).

### Steps
- [ ] `tla/Harness.tla`, en TLA+ directo y con una acción por operador con nombre, modela la máquina de estados de `architecture.md` §9.1 para los tres tipos de ejecución con sus fases, y TLC la recorre con su configuración positiva sin error ni deadlock (RF-TLA-1 · clase A)
  - Estados, tipos, fases y evaluables con los valores de `definitions.md` §12: `created`, `running`, `finished`, `blocked`, `cancelled`, `interrupted`; `generation` con `planning` → `chapter_production` → `publication`, `change_request` con `revalidation` → `editing` → `publication`, y `manual_edit` con `recording` → `propagation` → `publication`; y los evaluables `outline`, `chapter`, `fallback_regeneration` y `gate_cycle`. La interpretación de un cambio no es una ejecución y no entra.
  - La generación parte `created` del brief confirmado. Cada planificación es un intento de `outline`, y el outline congelado es el punto de control del capítulo 0 (§5.2, §9.2).
  - El veredicto sigue el orden de §8.2: sin bloqueantes se acepta, aun con los intentos agotados; agotados con bloqueantes, un capítulo afectado por un cambio o una propagación pasa a la regeneración de respaldo, y cualquier otro evaluable, o la regeneración de respaldo agotada, bloquea con `retries_exhausted`. Cada capítulo aceptado deja su punto de control.
  - Con la candidata completa corre el gate: cada ciclo es un intento de `gate_cycle`, y superado, la versión se publica con el número siguiente al de la última publicada (§9.3, §9.4). Un bloqueo por cualquier otro motivo de bloqueo es una sola acción de `running` a `blocked`.
  - Una caída o un fallo de infraestructura —también el verificador formal inalcanzable o fuera de tiempo— pasa a `interrupted` sin contar intento; los turnos o el tiempo agotados de una sesión son un intento fallido más (§7.6).
  - Reanudar, desde `blocked` o `interrupted`, abre un tramo nuevo con los intentos a cero, también los del evaluable que bloqueó, y sigue desde el último punto de control: el capítulo siguiente al último aceptado, sin replanificar tras el capítulo 0; en el gate, el ciclo en curso; en un cambio o una edición, los capítulos afectados aún no registrados, tras revalidar otra vez (§9.2). Agotadas las `max_resumes`, solo queda cancelar.
  - Cancelar desde `created` no rechaza nada; desde `running`, `blocked` o `interrupted`, rechaza la candidata. Una ejecución de cambio o de edición crea su candidata tras revalidar al arrancar, así que su revalidación fallida la cancela sin candidata (§9.3, §9.6). Una edición rechazada por un fallo del capítulo editado a mano pasa de `running` a `cancelled` (§9.6).
  - La regeneración por un cambio del lector es una ejecución de cambio sobre la versión publicada, que edita sus capítulos afectados, con la regeneración de respaldo, y publica una versión nueva.
  - Toda acción es una transición del orquestador o de la API (§10.6): la caída la pasa a `interrupted` la API, y cancelar y reanudar los pide el cliente a la API (§9.1).
- [ ] TLC recorre `Harness.tla` con su configuración positiva → ningún contraejemplo de los invariantes 8, 9, 10 y 11 de `architecture.md` §10.4: ninguna versión se publica sin pasar el gate; una versión publicada no cambia y la anterior se conserva; reanudar no duplica ni pierde capítulos; y dentro de cada tramo, los intentos de cada evaluable no pasan de `max_retries`, y las reanudaciones no pasan de `max_resumes` (RF-TLA-2 · clase A)
  - Cada invariante tiene nombre propio, por el que la configuración negativa reconoce su contraejemplo (RF-TLA-7).
  - El 9 relaciona dos estados seguidos: TLC lo comprueba como propiedad de acción.
  - El 10: los capítulos aceptados de una candidata son siempre 1..*k*, sin repetidos ni huecos, y en un cambio o una edición cada capítulo afectado se registra una vez, con reanudaciones o sin ellas.
- [ ] TLC comprueba en `Harness.tla`, bajo equidad débil, que toda ejecución acaba publicando una versión o deteniéndose con error —`blocked`, `interrupted` o `cancelled`—, también a través de sus reanudaciones, y nunca queda en un bucle infinito → sin contraejemplo (RF-TLA-3 · clase A)
  - Se enuncia como que toda ejecución acaba parada para siempre en uno de esos cuatro estados, o en `finished`. Se sostiene porque todo bucle está acotado, las reanudaciones incluidas (§7.6).
- [ ] `tla/Regenerations.tla` modela ejecuciones de cambio y de edición sobre la misma novela en la cola global, en orden de llegada, con su versión base, su revalidación al arrancar y su reanudación, que solo ocurre sin otra ejecución activa y vuelve a revalidar (§9.2). TLC comprueba como invariantes que hay como mucho una ejecución `running`; que la historia de versiones es lineal —ninguna se publica sobre una versión que ya no es la vigente—; y que toda solicitud confirmada y toda edición en cola están siempre en la cola, en su ejecución —activa, `blocked` o `interrupted`—, aplicadas o rechazadas → sin contraejemplo (RF-TLA-4 · clase A)
  - Una solicitud confirmada encola su ejecución de cambio con la versión base que vio el lector. Una edición guardada con la versión base vigente queda `queued` y encola la suya; con una que ya no lo es, no encola nada (§9.5, §9.6).
  - La cola lanza la primera ejecución `created`, en orden de llegada, solo si no hay ninguna `running` (§9.1).
  - Al arrancar, una ejecución de edición revalida que su versión base sigue siendo la vigente. Una de cambio revalida que su cita y los valores antiguos siguen en la vigente: el modelo lo deja abierto si se publicó otra versión después de su base, y lo da por bueno si no. Si pasa, la candidata copia la vigente; si no, la ejecución pasa a `cancelled` sin candidata, y su solicitud o su edición, a `rejected` (§9.5 paso 6, §9.6).
  - Una ejecución `running` puede pasar a `blocked` o `interrupted`. Al reanudar, si se publicó otra versión después de la que copió su candidata, pasa a `cancelled`, y su solicitud o su edición, a `rejected` (§9.2).
  - Publicar deja la solicitud o la edición `applied`; cancelar, `rejected` (§9.5 paso 12).
- [ ] `tla/Confirmation.tla` modela el código de confirmación de una solicitud de cambio. TLC comprueba que un código encola como mucho una ejecución, nunca después de caducar y solo si lo presenta el cliente propietario de su solicitud → sin contraejemplo (RF-TLA-5 · clase A)
  - Presentar el código de una solicitud `proposed` sin caducar, por su propietario, la pasa a `confirmed` y encola su ejecución. Cualquier otra presentación —de otro cliente, caducada o ya usada— no cambia nada (§9.5, §13.2).
  - Caducar es una acción que pasa una solicitud `proposed` a `expired`. El modelo no tiene reloj, así que no fija los 15 minutos de `operation.confirmation_minutes`.
- [ ] Las configuraciones positivas de las tres especificaciones están en el repositorio con el modelo pequeño de `architecture.md` §10.6, como constantes del modelo: 5 capítulos, `max_retries` = 2, `max_resumes` = 2, 2 solicitudes de cambio, 1 edición manual y 2 clientes (RF-TLA-6 · clase A)
  - Cada configuración fija las constantes que usa su especificación. No se leen de `config.json`: en el producto, `max_retries` y `max_resumes` siguen siendo cifras sin calibrar que el código lee de la config (§15.2).
- [ ] Cada especificación tiene además una configuración negativa, que activa un fallo a propósito: en `Harness.tla`, publicar sin pasar el gate; en `Regenerations.tla`, perder una solicitud confirmada; en `Confirmation.tla`, aceptar un código ajeno, el que presenta un cliente que no es el propietario de su solicitud → TLC da un contraejemplo del invariante que ese fallo viola; si no lo da, la comprobación falla (RF-TLA-7 · clase A)
  - Cada negativa activa un solo fallo, y la comprobación reconoce el contraejemplo por el nombre de su invariante en la salida de TLC. Un contraejemplo de otro invariante, un error de TLC o ninguno hacen fallar la comprobación.
  - El fallo no forma parte de las acciones de la especificación: lo activa solo su configuración negativa, así que no tiene fila en la tabla del README (RF-TLA-10).
- [ ] En cada cambio, CI ejecuta TLC sobre las tres configuraciones positivas y las tres negativas → la integración falla si una positiva da contraejemplo o si una negativa no lo da. `harness-tla` no envía score, y ninguna ejecución del harness invoca TLC (RF-TLA-8)
  - Una sola orden recorre las seis configuraciones y termina con código distinto de cero si falla una. Una positiva falla también si TLC no termina bien por otro motivo, como un error de sintaxis o un deadlock.
  - Se comprueba que la orden termina con código distinto de cero con una positiva que da contraejemplo y con una negativa que no lo da.
  - El job se llama `harness-tla`, como el validador (§10.2), y no tiene credenciales de Langfuse ni ningún paso que envíe un score. Una comprobación de CI falla si el backend nombra TLC o `tla2tools.jar`.
  - La versión de `tla2tools.jar` queda fijada en `specs/001-base/design.md` §1, junto al JDK Temurin 21 (`architecture.md` §14.1).
- [ ] En el portátil de desarrollo, la misma orden que CI, con el JDK Temurin portable, corre las seis configuraciones → da el mismo resultado que CI (RF-TLA-9 · clase D)
  - Sin admin: el JDK portable y `tla2tools.jar` van en el perfil del usuario, y la orden corre igual en Git Bash que en el runner de CI.
- [ ] El README de la raíz → tiene una tabla con una fila por acción de las tres especificaciones y la transición que modela: de la ejecución (`architecture.md` §9.1), o de la solicitud de cambio o la edición manual (§9.5, §9.6) (RF-TLA-10 · clase I)
  - Cada fila dice además si la transición es del orquestador o de la API (§10.6). La columna del código la completa la spec que implementa cada transición: 007, 015 o 016.
  - La revisión compara las acciones de cada especificación con las filas: ninguna acción sin fila y ninguna fila sin acción.
  - El README deja de dar `tla/` como carpeta planificada.
- [ ] `architecture.md` §10.6 → lleva el diagrama de la máquina de estados completa que especifica `Harness.tla`, en lugar de remitir al de §9.1, y la fila del diagrama de TLA+ en el README de la raíz apunta a él (RF-TLA-11 · clase I)
  - En Mermaid, con identificadores ASCII sin espacios (`CLAUDE.md`); cada transición lleva el nombre de la acción de `Harness.tla` que la modela.
  - Es un cambio de un doc de referencia: pasa por el [proceso 1](../../workflow/1-docs.md).
- [ ] TLC encuentra durante el desarrollo un contraejemplo sobre una configuración positiva → queda una fila en `verification.md` §8 con la causa y el cambio que provocó en la especificación, el diseño o el código (RF-TLA-12 · clase I)
  - Los contraejemplos de las negativas son los esperados y no dejan fila.
  - Si un contraejemplo muestra un defecto del diseño de `architecture.md`, se para y se cambia el doc con el usuario por el proceso 1 antes de seguir (§10.6).
  - Sin ninguno, el cierre lo dice en «Process records».
- [ ] Al cerrar 006 → la cabecera de `architecture.md` §10.6 lleva el explainer de la verificación formal del sistema con TLA+, como asigna la lista de explainers del README de la raíz (RF-TLA-13 · clase I)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
