# 006 — Especificación TLA+ del harness

> Carril: D · Depende de: 000 · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Especificar en TLA+ la máquina de estados de la `Ejecucion` (`architecture.md` §9.1) **antes de escribir el orquestador**, y comprobar con TLC sobre un modelo pequeño que cumple las cuatro invariantes de seguridad y la propiedad de vivacidad de §11.5. Como opcional del encargo, se especifica también la concurrencia entre dos cambios (`VersionesLineales`). Es el validador `harness-tla` (formal del sistema): corre en desarrollo y en la CI, bloquea la integración y no envía score (§11.2). Si aparece un contraejemplo, cambia el diseño antes que el código (§11.5, §18).

## Alcance

- **`Harness.tla`** (obligatoria): la `Ejecucion` de §9.1 con sus doce acciones (`Configurar`, `Planificar`, `EscribirCapitulo`, `Validar`, `Reintentar`, `Caer`, `Reanudar`, `Gate`, `Publicar`, `Fallar`, `PedirCambio`, `Regenerar`), los límites de §7.6, el punto de control y la reanudación de §9.2, las versiones de §9.3, el gate y la reescritura dirigida de §9.4, y el cambio del lector y la edición manual de §10.1 y §10.3, visto desde la ejecución.
- **`Regenerations.tla`** (opcional del encargo): dos cambios confirmados sobre la misma novela, con la cola FIFO global, una ejecución en curso como mucho, la versión base y la revalidación de §10.2.
- **Configs:** una que pasa por especificación, con el modelo pequeño de §11.5 y §4.10, y una de control por propiedad, con un defecto sembrado (`verification.md` §4.10, «Control del comprobador»). Además, el informe de cobertura por acción.
- **Veredictos**, en el portátil y en la CI. Aquí se describe el comportamiento del job formal; el workflow lo cambia el integrador, que es el dueño de la CI (spec 000).
- **Contenido de la tabla de correspondencia** del README raíz (acción ↔ transición ↔ spec que implementa el código) y **registro de los contraejemplos** en `verification.md` §8. Los escribe el integrador, único escritor del README y de `docs/` (`AGENTS.md`, *Parallel lanes*).

## Fuera de alcance

- Código del orquestador, la cola, el worker y la reanudación → 011-produccion-de-capitulos. Planificación y `outline` → 010-planificacion. Gate, reescritura dirigida y publicación → 012-gate-de-publicacion. Ejecución de cambio → 014-cambios-del-lector. Ejecución de edición → 019-edicion-manual. La correspondencia entre el código y el modelo la revisa el `verificador` al cerrar esas specs (`verification.md` §4.10).
- Todo lo que pasa antes de `PedirCambio`: la policy sobre la petición, las propuestas del planner (el evaluable del cambio, `max_retries.change`), el código de confirmación y su caducidad → 014-cambios-del-lector y 015-servidor-mcp. El 409 al guardar una edición → 019-edicion-manual. No son estados de la `Ejecucion`.
- El interior de una sesión de rol (turnos, tiempos, techo de tokens) → 003-puerto-de-agente. En el modelo, su efecto es un `Validar` que falla o un `Caer`.
- Los fallos terminales ajenos al bucle (`internal_error`, `infeasible_config`) y volver a lanzar una generación fallida. Solo añaden salidas a `failed`, que ni publican ni tocan versiones publicadas ni dejan la ejecución sin terminar: no pueden violar ninguna propiedad.
- Una tercera especificación (servidor MCP, confirmación): fuera por el ADR 0006.
- TLC en versión fijada, JDK Temurin, que el job formal exista y que git ignore lo que genera TLC → 000-scaffolding (000-C01, 000-C18, 000-I1).
- El anexo de la presentación con la especificación comentada y los diagramas: tarea de la presentación. El diagrama de la máquina de estados ya está en `architecture.md` §9.1.

## Comportamiento observable

Excepción de la 006: el producto de esta spec son dos especificaciones y sus configs. Su comportamiento observable es **lo que hace el modelo** (las transiciones de C4 y C5) y **lo que decide TLC** sobre cada config. Por eso se nombran `Harness.tla` y `Regenerations.tla` (términos de `definitions.md` §9) y TLC (el validador `harness-tla`).

**Términos del modelo.**

- **Secuencia de una ejecución.** En `generation`: el plan (punto de control 0) y los capítulos 1..5. En `change_request`: los capítulos afectados, en orden. En `manual_edit`: primero el capítulo editado y después los demás afectados, en orden (§9.1: «una edición manual es un `PedirCambio` cuyo primer capítulo afectado llega ya escrito»).
- **Evaluables del modelo:**
  - el plan;
  - cada capítulo de la secuencia en `writing`;
  - cada capítulo atribuido en cada ciclo de `rewriting`;
  - el ciclo del gate.

  Son los de `definitions.md` §5 (*Intento y Evaluable*) menos el del cambio, que es de la API (fuera de alcance).
- **Entrega pendiente:** la de un `EscribirCapitulo` que aún no ha pasado por `Validar`.
- **No determinismo.** En el modelo es no determinista todo lo que decide un modelo o el entorno:
  - si `Validar` pasa o falla;
  - a qué capítulos atribuye el gate su fallo;
  - qué capítulos afecta un cambio y cuál se edita a mano;
  - el tipo del cambio y cuándo se pide;
  - cuándo cae la ejecución.

  Lo que decide el código es una guarda determinista: los límites, la revalidación de la base y el orden de la cola.

### C1 — `Harness.tla` pasa en el modelo pequeño (A)
- **Dado** `Harness.tla` con su config que pasa: 5 capítulos; `max_retries` 2 para el plan, el capítulo y el ciclo del gate; `max_resumes` 2; 1 cambio, de tipo `change_request` o `manual_edit`.
- **Cuando** TLC la comprueba.
- **Entonces:**
  - explora el espacio de estados completo y termina sin error;
  - no hay ningún estado ni paso que viole `NuncaPublicaSinValidar`, `ReanudacionSinDuplicarNiPerder`, `VersionAnteriorConservada` ni `ReintentosAcotados` (I1–I4);
  - `TerminaSiempre` se cumple con la equidad de I5;
  - informa del número de estados distintos;
  - en el runner de la CI tarda 10 minutos o menos.

### C2 — `Regenerations.tla` pasa con dos cambios (A)
- **Dado** `Regenerations.tla` con su config que pasa:
  - una versión publicada vigente;
  - 2 cambios, que se confirman en cualquier orden y momento, así que pueden tener la misma base o bases consecutivas;
  - cola FIFO global y una ejecución en curso como mucho;
  - 1 reanudación por ejecución, la mínima que pone a prueba la revalidación al relanzar y el puesto original en la cola.
- **Cuando** TLC la comprueba.
- **Entonces** termina sin error, `VersionesLineales` se cumple en todo estado (I6) y tarda 10 minutos o menos en el runner de la CI. No se comprueba vivacidad (`verification.md` §4.10).

### C3 — Ninguna acción queda sin disparar (A)
- **Dado** el informe de cobertura por acción de las pasadas de C1 y C2.
- **Cuando** se revisa.
- **Entonces** cada una de las doce acciones de `Harness.tla` y cada una de las seis de `Regenerations.tla` (C5) se toma al menos una vez.
- **Rechazo:** si una acción nunca se habilita, la comprobación falla y la nombra. Una guarda imposible hace que las propiedades se cumplan en vacío.

### C4 — Las transiciones de `Harness.tla` son las de §9.1 (I)
- **Dado** el modelo de `Harness.tla`.
- **Cuando** se lee cada acción.
- **Entonces** se habilita y actúa según la tabla. Otra transición cualquiera es un defecto del modelo.

| Acción | Se habilita cuando | Efecto en el modelo |
|---|---|---|
| `Configurar` | Al inicio, una sola vez | Una `generation` en `queued`, con su candidata vacía |
| `Planificar` | Hay una `generation` en `queued` y ninguna ejecución en curso | Pasa a `running`. Sin puntos de control → `planning`. Relanzada tras `Reanudar` → la fase siguiente al último punto de control: `writing` del capítulo k+1; o `gate` si no quedan capítulos o si cayó en `gate` o `rewriting` (§9.2) |
| `Regenerar` | Hay una `change_request` o una `manual_edit` en `queued` y ninguna ejecución en curso | Revalida la base; aquí siempre es la vigente, porque la base obsoleta es de C5. La primera vez, la candidata es una copia de la base → `writing` del primer afectado. Relanzada, sigue como `Planificar` y no vuelve a copiar |
| `EscribirCapitulo` | En `writing` o `rewriting`, sin entrega pendiente ni defectos por reintentar, y el capítulo actual no es el editado a mano | Deja una entrega pendiente del capítulo actual |
| `Validar` | En `planning`, con la entrega del planner implícita; en `writing` o `rewriting`, con una entrega pendiente o con el capítulo editado a mano por juzgar; en `gate`, una vez por pasada | Cuenta un intento del evaluable; en `gate`, solo si falla (un ciclo fallido, §9.4). **Si pasa:** se aplica el plan (punto de control 0 → `writing` del capítulo 1); se acepta el capítulo en la candidata (en `writing`, con su punto de control) y se sigue con el siguiente de la secuencia o de los atribuidos; o queda superado el gate. **Si falla:** la entrega se descarta y quedan defectos por reintentar. En `gate`, si quedan ciclos y el fallo es atribuible a un conjunto no vacío de capítulos → `rewriting`, con esos capítulos en orden |
| `Reintentar` | Tras un `Validar` que falla, si el evaluable lleva menos de 1 + `max_retries` intentos y no es el capítulo editado a mano; o, en `rewriting`, cuando todos los atribuidos se han vuelto a aceptar | En `planning`, el planner entrega de nuevo. En `writing` y `rewriting`, el mismo capítulo vuelve al writer con los defectos. Con todos los atribuidos aceptados → `gate`, para un ciclo nuevo |
| `Gate` | En `writing`, sin capítulos por escribir en la secuencia | → `gate` |
| `Publicar` | En `gate`, con el gate superado | La candidata se publica como versión siguiente; la ejecución pasa a `published`; en un cambio, la solicitud o la edición pasan a `applied` |
| `Fallar` | (a) Tras un `Validar` que falla sin intentos que reintentar (`retries_exhausted`, `banned_content`). (b) En `gate`: fallo sin capítulo atribuible (`render_failure`, `unattributable_defect`, `banned_content`) o ciclos agotados (`retries_exhausted`). (c) El capítulo editado a mano falla en su `Validar` o el gate le atribuye el fallo (`edit_rejected`). (d) Una caída con `max_resumes` agotado (`resumes_exhausted`) | → `failed`; la candidata se descarta; en un cambio, la solicitud o la edición pasan a `rejected` |
| `Caer` | En `running`, en cualquier fase, con menos de `max_resumes` reanudaciones | → `interrupted`. La entrega pendiente se pierde y no cuenta como intento; se conservan la candidata, los puntos de control y los intentos (§7.6) |
| `Reanudar` | En `interrupted` | Reanudaciones + 1 → `queued`, en su puesto original |
| `PedirCambio` | Hay versión publicada, ninguna ejecución sin terminar y el cambio del modelo aún no se ha pedido | Una `change_request` (afectados: un conjunto no vacío de capítulos, en orden) o una `manual_edit` (primero el capítulo editado, que llega escrito, y después un conjunto de otros, quizá vacío, en orden), en `queued` y con la vigente como base |

Notas:
- Los motivos de fallo que comparten rama no se distinguen en el modelo.
- Cuando el gate atribuye a un capítulo un fallo de datos (§9.4), el editor vuelve a registrarlo sin writer. En el modelo es un `EscribirCapitulo` que conserva el texto, seguido de `Validar`.

### C5 — Las transiciones de `Regenerations.tla` son las de §10.2 (I)
- **Dado** el modelo de `Regenerations.tla`: estado inicial con una versión publicada vigente y ningún cambio confirmado. Solo usa nombres de acción de `Harness.tla`.
- **Cuando** se lee cada acción.
- **Entonces** se habilita y actúa según la tabla. El interior de cada ejecución (fases, intentos) es de C4 y aquí se resume en `Publicar` o `Fallar`.

| Acción | Se habilita cuando | Efecto en el modelo |
|---|---|---|
| `PedirCambio` | Queda un cambio sin confirmar | Queda confirmado, con la versión vigente de ese momento como base; su ejecución entra al final de la cola |
| `Regenerar` | No hay ninguna ejecución en curso, la suya es la primera de la cola por fecha de creación y su base sigue siendo la vigente | → en curso |
| `Fallar` | (a) Es la primera de la cola, no hay ninguna en curso y su base ya no es la vigente: `stale_base` al arrancar o al relanzarse. (b) Está en curso: cualquier fallo del bucle. (c) Cae en curso con las reanudaciones agotadas (`resumes_exhausted`) | Ejecución `failed`; el cambio pasa a `rejected` con su motivo |
| `Publicar` | Está en curso | Versión nueva = vigente + 1, con la base del cambio; pasa a ser la vigente; el cambio pasa a `applied` |
| `Caer` | Está en curso y le queda la reanudación | → `interrupted`: deja de estar activa y la cola sigue |
| `Reanudar` | Está en `interrupted` | → `queued`, en su puesto original: conserva su fecha de creación, así que sale antes que las posteriores (§9.2) |

### C6 — Cada config de control da el contraejemplo de su propiedad (A)
- **Dado** el mismo modelo de C1 o de C2 con **un único** defecto sembrado, activado solo desde su config de control, que comprueba solo la propiedad de su fila.
- **Cuando** TLC la comprueba.
- **Entonces** informa de que se viola **esa propiedad, por su nombre**, y da una traza con lo que indica la tabla.
- **Rechazos**, que cuentan como fallo del control:
  - TLC termina sin error (control sin contraejemplo);
  - informa de otra propiedad;
  - se detiene por otra causa (error de sintaxis o semántico, falta de memoria).

| Control | Defecto sembrado | Propiedad que debe violarse | La traza muestra |
|---|---|---|---|
| 1 | `Publicar` se habilita en `gate` sin el gate superado | `NuncaPublicaSinValidar` | Una versión publicada sin gate superado |
| 2 | Al relanzarse tras `Reanudar`, la ejecución sigue en el capítulo k+2 | `ReanudacionSinDuplicarNiPerder` | Una caída en `writing`, `Reanudar` y puntos de control con un hueco |
| 3 | `Regenerar` reescribe los afectados sobre la versión base publicada, sin copiarla | `VersionAnteriorConservada` | `PedirCambio`, `Regenerar` y un capítulo de la versión 1 que cambia |
| 4 | La guarda de `Reintentar` admite un intento más | `ReintentosAcotados` | Un evaluable con 1 + `max_retries` intentos fallidos (el límite se alcanza) y uno más |
| 5 | Una caída con `max_resumes` agotado deja la ejecución en `interrupted` en vez de `Fallar` | `TerminaSiempre` | `max_resumes` reanudaciones (el límite se alcanza), otra caída y un `interrupted` del que no sale ninguna acción |
| 6 (`Regenerations.tla`) | `Regenerar` no revalida la base | `VersionesLineales` | Dos cambios con base 1 que publican las versiones 2 y 3, la 3 con base 1 |

Las filas 4 y 5 muestran además que los límites se alcanzan en el modelo, no solo que no se superan.

### C7 — La CI decide con las configs de la 006 (D)
- **Dado** el job formal de la CI (`verification.md` §4.6) con las dos configs que pasan y las seis de control, y un push a `V2` que decide el integrador.
- **Cuando** corre la CI.
- **Entonces** el job termina en verde: C1 y C2 pasan, C3 no nombra ninguna acción y cada control da su contraejemplo (C6).
- **Y**, en una PR desde una rama desechable que decide el usuario, el job termina en rojo en cada uno de estos casos, nombrando la config y el motivo:
  - un defecto activado en la config que pasa;
  - el defecto de una config de control desactivado;
  - un error de sintaxis en el modelo.

  La PR se cierra sin fusionar y se borra la rama: `V2` no cambia.

### C8 — En el portátil, el mismo veredicto (D)
- **Dado** el portátil de desarrollo con un JDK Temurin portátil y TLC en la versión que fija la 000, sin instalar nada.
- **Cuando** se ejecuta TLC sobre cada config.
- **Entonces:**
  - los veredictos son los de C1, C2 y C6;
  - nada de lo que genera TLC queda sin ignorar en git (000-C01).
- **Si** Smart App Control bloquea el JDK, se registra en `verification.md` §8 (disparador `entorno`) y TLC queda solo en la CI, como Lean (ADR 0004).

### C9 — El README dice qué transición implementa cada acción (I)
- **Dado** el README raíz, que escribe el integrador con el contenido de esta spec.
- **Cuando** se lee su tabla de correspondencia.
- **Entonces** hay una fila por cada una de las doce acciones de `Harness.tla`, con:
  - su transición de §9.1 tal como la modela C4, por ejemplo `Reanudar`: `interrupted` → `queued`;
  - quién la dispara;
  - la spec que implementa el código.

  Además:
  - las acciones de `Regenerations.tla` remiten a esas mismas filas y a la revalidación de §10.2;
  - no hay filas de más ni de menos respecto a los modelos;
  - la columna de código se rellena al cerrar cada spec implementadora y el `verificador` la revisa (`verification.md` §4.10).

| Acción | Spec que implementa el código |
|---|---|
| `Configurar` | 011 (API de ejecuciones) |
| `Planificar` | 011 (el worker la toma de la cola), 010 (planner) |
| `Regenerar` | 014 (cambio), 019 (edición) |
| `EscribirCapitulo` | 011; en `rewriting`, 012 |
| `Validar` | 010 (`outline`), 011 (hooks, editor, veredicto), 012 (gate) |
| `Reintentar` | 010, 011, 012 |
| `Gate`, `Publicar` | 012 |
| `Fallar` | 010, 011, 012, 014, 019, según el motivo |
| `Caer` | 011 (caída y arranque), 012 (verificador inalcanzable o agotado) |
| `Reanudar` | 011 (API y CLI) |
| `PedirCambio` | 014 (confirmar; por MCP, 015), 019 (guardar la edición) |

### C10 — Un contraejemplo real queda registrado con su cambio (I)
- **Dado** que TLC da un contraejemplo sobre una config que pasa durante el desarrollo.
- **Cuando** el carril lo analiza.
- **Entonces:**
  - si es un error de escritura del modelo, se corrige el modelo;
  - si revela un fallo del diseño, primero se cambia `architecture.md` (proceso 1, a través del integrador) y después el modelo. El integrador añade una fila en `verification.md` §8 con disparador `TLC`, la traza resumida, el cambio y dónde quedó;
  - los contraejemplos de las configs de control son los esperados y no se registran;
  - si no aparece ninguno, el cierre de la 006 lo dice, sin inventarlo.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| I1 | **`NuncaPublicaSinValidar`**: en todo estado, cada versión publicada tuvo el gate superado sobre esa misma candidata después de su última aceptación de capítulo, y cada uno de sus capítulos lo aceptó `Validar`: en esa ejecución o, si no era de los afectados, en la versión de la que se copió | A | TLC en C1; que no se cumple en vacío, control 1 de C6 |
| I2 | **`ReanudacionSinDuplicarNiPerder`**: en todo estado, los puntos de control de una ejecución son exactamente el prefijo de su secuencia hasta k, sin huecos ni repetidos, y en `writing` el capítulo actual es el siguiente de la secuencia tras el último punto de control, también después de `Reanudar`. Las aceptaciones de la reescritura dirigida no crean puntos de control: reanudar desde `gate` o `rewriting` vuelve al gate (§9.2) | A | TLC en C1; control 2 |
| I3 | **`VersionAnteriorConservada`**: ningún paso cambia ni quita una versión ya publicada: ni la reescritura de su sucesora, ni publicar otra, ni que falle un cambio | A | TLC en C1; control 3 |
| I4 | **`ReintentosAcotados`**: en todo estado, los intentos de cada evaluable no pasan de 1 + su `max_retries`, y las reanudaciones de cada ejecución no pasan de `max_resumes` | A | TLC en C1; control 4 |
| I5 | **`TerminaSiempre`**: toda ejecución creada acaba en `published` o `failed`. Se supone equidad débil de las acciones del sistema (`Planificar`, `Regenerar`, `EscribirCapitulo`, `Validar`, `Reintentar`, `Gate`, `Publicar` y `Fallar` salvo su rama de caída) y de `Reanudar` (§11.5). No se supone para `Configurar`, `PedirCambio` ni las caídas, que son del entorno. Un estado no terminal del que no sale ninguna acción es un contraejemplo | A | TLC en C1; control 5 |
| I6 | **`VersionesLineales`**: cada versión publicada n+1 tiene como base la n. En todo estado, cada cambio confirmado está pendiente (en cola, en curso o interrumpido), aplicado o rechazado, nunca en otro estado ni desaparecido. Está aplicado solo si su ejecución publicó y rechazado solo si falló | A | TLC en C2; control 6 |
| I7 | Fidelidad y nombres: TLA+ directo, sin PlusCal (§11.5); módulos `Harness` y `Regenerations`; en `Harness.tla`, exactamente las doce acciones de §11.5, y en `Regenerations.tla`, solo nombres de esas; propiedades con los nombres y enunciados de §11.5; cada transición, la de C4 o C5 | I | `auditor` sobre esta spec; `verificador` sobre el modelo al cerrar la 006; C3 contra las acciones muertas |
| I8 | Las configs de control comprueban el mismo modelo que la que pasa, con un único defecto activado; en las que pasan no hay ningún defecto activo. Los defectos y las propiedades de control son internos de la verificación: no son propiedades del harness ni términos del dominio | I | `verificador` al cerrar la 006 |
| I9 | Todo lo que decide un modelo o el entorno es no determinista en el modelo, y todo lo que decide el código es una guarda (Términos del modelo). El modelo permite al menos lo que puede hacer el código | I | `auditor` y `verificador`; y por las filas de C9 al cerrar 011, 012 y 014 |
| I10 | TLC solo corre en desarrollo y en la CI: el backend no lo invoca en ninguna generación, no envía score ni llama a un modelo, y su job no usa secretos (§11.2; `definitions.md` §6, *Validador*) | I | Revisión del workflow (000-I9) y del backend |
| I11 | Modelo pequeño: un defecto que solo aparezca con más de 5 capítulos, más reintentos o reanudaciones, o más cambios que los del modelo escapa a TLC. Mitigación: los límites son constantes de la config; las pruebas T de 011, 012 y 014 usan 10 capítulos | U | `verification.md` §6 U30 |

## Docs referenciados

- `architecture.md`:
  - §7.6 (límites; los intentos no se reinician; `resumes_exhausted`);
  - §8.3 y §8.4 (aceptación y punto de control; reanudar);
  - §9.1 (máquina de estados, tabla de acciones, motivos, cola y una ejecución activa);
  - §9.2 (reanudación en su puesto; gate y `rewriting` al relanzar);
  - §9.3 (candidata copiada, número al publicar, anterior conservada, `discarded`);
  - §9.4 (gate, atribución, ciclos);
  - §10.1 a §10.3 (cambio, concurrencia, edición manual y `edit_rejected`);
  - §11.1 y §11.2 (familia formal del sistema, `harness-tla`);
  - §11.5 (acciones, modelo pequeño, propiedades, equidad, `Regenerations.tla`, integración con el flujo real);
  - §16.18;
  - §18 (filas «Integración de TLA+ con el flujo real» y «Especificaciones TLA+»).
- `definitions.md`:
  - §5 (*Ejecucion*, *Intento y Evaluable*, *PuntoDeControl*, *SolicitudDeCambio*, *EdicionManual*, orquestador);
  - §6 (*Validador*, *GateDePublicacion*);
  - §9 (*EspecificacionDelHarness*);
  - §12.3 (`harness-tla` y la excepción de nombres de TLA+).
- `verification.md`:
  - §1 y §2 (frontera y clases);
  - §3.6 y §4.10 (TLC, control del comprobador, correspondencia, contraejemplos);
  - §4.6 (job formal);
  - §5, filas 5d.1 (C1, C4), 5d.2 (I1–I4), 5d.3 (I5), 5d.4 (C1, C2, C7), 5d.5 (C9), 5d.6 (C10) y O.13 (C2, I6), y los refuerzos A de 2.11 (I3), 3.7 (I4) y 4.5 (I2);
  - §6 (U30, de I11);
  - §8.
- `project-constraints.md` §5d (flujo con reintentos, reanudación y regeneración; tres o más invariantes de seguridad y una de vivacidad; TLC sobre un modelo pequeño con la config en el repo; README; contraejemplos) y el opcional «Especificación TLA+ … de la concurrencia entre regeneraciones simultáneas».
- ADR 0004 (Lean solo en la CI, alternativa de C8) y ADR 0006 (dos especificaciones; la tercera, fuera).
- 000-scaffolding: 000-C01, 000-C18, 000-I1 y 000-I9.

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué es observable en una spec de TLA+? | Las transiciones del modelo (I) y los veredictos de TLC (A) | `verification.md` §2, §4.10 |
| ¿Qué clase tiene el control del comprobador? | A: forma parte del método de §4.10. La CI y el portátil, D, porque necesitan un push o el JDK | `verification.md` §4.10, §4.6 |
| ¿Qué acción relanza una ejecución reanudada? | La de entrada de su tipo (`Planificar` o `Regenerar`), que sigue desde el último punto de control. `Reanudar` termina en `queued` | **Hueco del doc**: la flecha `queued → running` de §9.1 no tiene nombre → §18 |
| ¿Una caída con las reanudaciones agotadas es `Caer`? | No: es `Fallar` (`resumes_exhausted`). `Caer` siempre lleva a `interrupted` | §7.6, §9.1 → §18 |
| ¿Crea puntos de control la reescritura dirigida? | No: si los crease, habría repetidos. Reanudar desde `gate` o `rewriting` vuelve al gate | **Hueco del doc**: §8.3 y §9.2 → §18 |
| ¿Qué pasa si el capítulo editado falla en su propio `Validar`? | `Fallar` (`edit_rejected`), sin reintento: ningún rol reescribe lo que escribió una persona | **Hueco del doc**: §10.3 solo trata el gate → §18 |
| ¿El evaluable del cambio está en el modelo? | No: sus intentos ocurren en la API, antes de `PedirCambio` | §10.1, paso 3 |
| ¿Cuántos controles? | Uno por propiedad (seis), para que ninguna propiedad se cumpla en vacío | §4.10 → §18 |
| ¿Reanudaciones en `Regenerations.tla`? | Una por ejecución: la mínima para revalidar al relanzar y conservar el puesto | §9.2, §10.2 → §18 |
| ¿Quién escribe el README, `verification.md` §8 y el workflow? | El integrador; la 006 aporta el contenido | `AGENTS.md`, *Parallel lanes*; `backend/AGENTS.md` |
| ¿Cuánto puede tardar TLC en la CI? | 10 minutos o menos por config | Decisión → §18 |
