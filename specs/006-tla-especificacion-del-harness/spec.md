# 006 — TLA · Especificación del harness

- [x] Spec approved   <- only the user marks this

## Objetivo

Especificar en TLA+ la máquina de estados del harness, la concurrencia entre regeneraciones y el código de confirmación, y comprobarlos con TLC antes de escribir el orquestador.

## Alcance

Cubre:

- las tres especificaciones de `definitions.md` §9 —`Harness.tla`, `Regenerations.tla` y `Confirmation.tla`—, en TLA+ directo y cada una con su configuración de TLC;
- sus invariantes de seguridad y la vivacidad de `Harness.tla`;
- el modelo pequeño y una configuración negativa por especificación;
- TLC en CI y en local;
- la tabla de correspondencia del README y el diagrama completo en `architecture.md` §10.6;
- el registro de sus contraejemplos.

Depende de 001, por la CI. Se cierra antes del código del orquestador (007), para que un contraejemplo cambie el diseño antes que el código (`architecture.md` §10.6).

**Fuera de alcance:**

- PlusCal: cada acción es un operador con nombre, para que la tabla del README la corresponda una a una con una transición.
- Las transiciones en código. La columna de código de la tabla la completan 007, para las del orquestador, y 015 y 016, para las de la API que confirman un cambio o encolan una edición, cada una con las acciones que implementa.
- Una especificación del servidor MCP: el opcional del encargo se cubre con la concurrencia entre regeneraciones, y la única escritura que expone MCP la modela `Confirmation.tla`.
- Correr TLC por generación: juzga el sistema, no una novela, así que corre en desarrollo y no envía score.

## Requisitos

Todos son **Obligatorio**.

### Especificaciones

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-TLA-1 | `tla/Harness.tla` → modela en TLA+ directo, con una acción por operador con nombre, la máquina de estados de `architecture.md` §9.1 para los tres tipos de ejecución con sus fases: el brief confirmado, del que parte la ejecución `created`; la planificación con sus replanificaciones; el bucle de capítulos; los puntos de control de cada capítulo aceptado, del capítulo 0, del ciclo del gate en curso y de los capítulos afectados de un cambio o una edición (§9.2); el gate y la publicación, con el número asignado al publicar; la caída o el fallo de infraestructura, que pasa a `interrupted` sin contar como intento (§7.6); la reanudación desde `interrupted` y desde `blocked`, como tramo nuevo y con intentos nuevos; la cancelación desde `created`, sin candidata que rechazar, y desde `running`, `blocked` o `interrupted`, que rechaza la candidata; la cancelación por revalidación fallida o por edición rechazada; y la regeneración por un cambio del lector. Los evaluables que cuenta son el outline, el capítulo, la regeneración de respaldo y el ciclo del gate | Obligatorio | A |
| RF-TLA-2 | TLC recorre `Harness.tla` con su configuración positiva → no encuentra contraejemplo de los invariantes 8 (ninguna versión se publica sin pasar el gate), 9 (una versión publicada no cambia y la anterior se conserva), 10 (reanudar no duplica ni pierde capítulos) y 11 (dentro de cada tramo, los intentos de cada evaluable no pasan de `max_retries`, y las reanudaciones no pasan de `max_resumes`) de `architecture.md` §10.4 | Obligatorio | A |
| RF-TLA-3 | TLC comprueba en `Harness.tla`, bajo equidad débil, que toda ejecución acaba publicando una versión o deteniéndose con error —`blocked`, `interrupted` o `cancelled`—, también a través de sus reanudaciones, y nunca queda en un bucle infinito → no encuentra contraejemplo | Obligatorio | A |
| RF-TLA-4 | `tla/Regenerations.tla` → modela ejecuciones de cambio y de edición sobre la misma novela en la cola global, en orden de llegada, con su versión base, su revalidación al arrancar y su reanudación, que solo ocurre sin otra ejecución activa y vuelve a revalidar (§9.2). TLC comprueba como invariantes que hay como mucho una ejecución `running`; que la historia de versiones es lineal —ninguna se publica sobre una versión que ya no es la vigente—; y que toda solicitud confirmada y toda edición en cola están siempre en la cola, en su ejecución —activa, `blocked` o `interrupted`—, aplicadas o rechazadas: ninguna se pierde. No encuentra contraejemplo | Obligatorio | A |
| RF-TLA-5 | `tla/Confirmation.tla` → modela el código de confirmación de una solicitud de cambio. TLC comprueba que un código encola como mucho una ejecución, nunca después de caducar y solo si lo presenta el cliente propietario de su solicitud. No encuentra contraejemplo | Obligatorio | A |
| RF-TLA-6 | Las configuraciones positivas de las tres especificaciones están en el repositorio con el modelo pequeño de `architecture.md` §10.6, como constantes del modelo y no como valores de config → 5 capítulos, `max_retries` = 2, `max_resumes` = 2, 2 solicitudes de cambio, 1 edición manual y 2 clientes | Obligatorio | A |

### Comprobación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-TLA-7 | Cada especificación tiene además una configuración negativa, que activa un fallo a propósito —publicar sin gate, perder una solicitud confirmada, aceptar un código ajeno o ya usado— → TLC da un contraejemplo del invariante que ese fallo viola; si no lo da, la comprobación falla | Obligatorio | A |
| RF-TLA-8 | En cada cambio, CI ejecuta TLC sobre las tres configuraciones positivas y las tres negativas → la integración falla si una positiva da contraejemplo o si una negativa no lo da. `harness-tla` no envía score, y ninguna ejecución del harness invoca TLC | Obligatorio | T |
| RF-TLA-9 | En el portátil de desarrollo, TLC corre sobre las mismas configuraciones con el JDK Temurin portable y la misma orden que CI → da el mismo resultado | Obligatorio | D |

### Documentación

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-TLA-10 | El README de la raíz → tiene una tabla con una fila por acción de las tres especificaciones y la transición que modela: de la ejecución (`architecture.md` §9.1), o de la solicitud de cambio o la edición manual (§9.5, §9.6) | Obligatorio | I |
| RF-TLA-11 | `architecture.md` §10.6 → lleva el diagrama de la máquina de estados completa que especifica `Harness.tla`, en lugar de remitir al de §9.1, y la fila del diagrama de TLA+ en el README de la raíz apunta a él | Obligatorio | I |
| RF-TLA-12 | TLC encuentra durante el desarrollo un contraejemplo sobre una configuración positiva → queda una fila en `verification.md` §8 con la causa y el cambio que provocó en la especificación, el diseño o el código | Obligatorio | I |
| RF-TLA-13 | Al cerrar 006 → la cabecera de `architecture.md` §10.6 lleva el explainer de la verificación formal del sistema con TLA+, como asigna la lista de explainers del README | Obligatorio | I |

## Docs de referencia

- `architecture.md` §5.2, §7.6, §8.2, §9.1–§9.6, §10.1, §10.2 (`harness-tla`), §10.4, §10.6, §12.3, §13.2 (la confirmación), §14.1 y §16 («Integración de TLA+ con el flujo real», «Especificaciones TLA+», «Concurrencia de cambios», «Reanudación»).
- `definitions.md` §5 (`Ejecucion`, `SolicitudDeCambio`, `EdicionManual`), §6 (`Evaluable`), §9 (`EspecificacionDelHarness`), §10 (`Confirmacion`) y §12.
- `verification.md` §3.4, §3.12, §4.7, §4.10, §5 y §8.
