# Matriz de relación: specs contra docs y encargo

Registro del bucle de gap del [proceso 2](../workflow/2-specs.md). Para cada spec anota qué secciones de [architecture.md](architecture.md) implementa y cada diferencia con los docs o con el encargo. Un requisito queda respaldado por una sección de `architecture.md` o de `verification.md`, o por un punto de [project-constraints.md](../project-constraints.md). Una spec no pasa a código mientras su apartado tenga una diferencia bloqueante abierta. El hook `guard` lo comprueba.

## 1. Cobertura

Una fila por par sección–spec. Toda sección de `architecture.md` que describe comportamiento del producto tiene al menos una spec; las que solo registran razones, como §16, no entran. La tabla se rellena al cerrar la fase de docs, y cada spec marca sus filas como revisadas al llegar a gap cero.

| Sección | Spec | Revisada |
|---|---|---|
| §1.2 | 001-base | |
| §2 | 007-run-ejecuciones | |
| §2 | 014-pub-publicacion-y-versiones | |
| §6.5 | 001-base | |
| §6.5 | 007-run-ejecuciones | |
| §6.6 | 008-mem-memoria | |
| §6.6 | 014-pub-publicacion-y-versiones | |
| §6.6 | 015-cam-cambios-y-edicion-manual | |
| §6.9 | 001-base | |
| §6.9 | 005-ent-entrevista-y-brief | |
| §6.9 | 008-mem-memoria | |
| §6.10 | 001-base | |
| §6.10 | 005-ent-entrevista-y-brief | |
| §6.10 | 008-mem-memoria | |
| §6.10 | 015-cam-cambios-y-edicion-manual | |
| §6.11 | 001-base | |
| §6.11 | 008-mem-memoria | |
| §6.11 | 010-pln-planificacion | |
| §6.11 | 011-cap-produccion-por-capitulo | |
| §6.11 | 014-pub-publicacion-y-versiones | |
| §6.11 | 015-cam-cambios-y-edicion-manual | |
| §6.12 | 001-base | |
| §7.3 | 001-base | |
| §7.3 | 004-obs-observabilidad | |
| §7.3 | 011-cap-produccion-por-capitulo | |
| §7.4 | 001-base | |
| §7.4 | 003-pol-politica-y-guardarrailes | |
| §7.4 | 007-run-ejecuciones | |
| §7.4 | 008-mem-memoria | |
| §7.5 | 001-base | |
| §7.5 | 003-pol-politica-y-guardarrailes | |
| §7.5 | 004-obs-observabilidad | |
| §7.5 | 007-run-ejecuciones | |
| §7.5 | 011-cap-produccion-por-capitulo | |
| §7.6 | 001-base | |
| §7.6 | 007-run-ejecuciones | |
| §7.6 | 009-lea-validador-formal-de-la-historia | |
| §8.1 | 011-cap-produccion-por-capitulo | |
| §8.3 | 001-base | |
| §8.3 | 011-cap-produccion-por-capitulo | |
| §9.1 | 007-run-ejecuciones | |
| §9.3 | 014-pub-publicacion-y-versiones | |
| §9.5 | 015-cam-cambios-y-edicion-manual | |
| §9.5 | 016-mcp-servidor-mcp | |
| §9.7 | 001-base | |
| §9.7 | 002-aut-autenticacion | |
| §9.7 | 013-lec-lectura-web-y-pdf | |
| §9.7 | 014-pub-publicacion-y-versiones | |
| §10.2 | 001-base | |
| §10.2 | 003-pol-politica-y-guardarrailes | |
| §10.2 | 004-obs-observabilidad | |
| §10.2 | 005-ent-entrevista-y-brief | |
| §10.2 | 009-lea-validador-formal-de-la-historia | |
| §10.2 | 010-pln-planificacion | |
| §10.2 | 011-cap-produccion-por-capitulo | |
| §10.2 | 012-lin-linters-de-prosa | |
| §10.2 | 014-pub-publicacion-y-versiones | |
| §10.2 | 015-cam-cambios-y-edicion-manual | |
| §10.3 | 001-base | |
| §10.3 | 003-pol-politica-y-guardarrailes | |
| §10.3 | 005-ent-entrevista-y-brief | |
| §10.3 | 009-lea-validador-formal-de-la-historia | |
| §10.3 | 010-pln-planificacion | |
| §10.3 | 011-cap-produccion-por-capitulo | |
| §10.3 | 012-lin-linters-de-prosa | |
| §10.3 | 014-pub-publicacion-y-versiones | |
| §10.3 | 015-cam-cambios-y-edicion-manual | |
| §10.3 | 017-evl-evaluacion-del-sistema | |
| §10.5 | 001-base | |
| §10.5 | 009-lea-validador-formal-de-la-historia | |
| §11.2 | 001-base | |
| §11.2 | 003-pol-politica-y-guardarrailes | |
| §11.2 | 014-pub-publicacion-y-versiones | |
| §11.5 | 001-base | |
| §11.5 | 004-obs-observabilidad | |
| §11.5 | 005-ent-entrevista-y-brief | |
| §11.5 | 007-run-ejecuciones | |
| §11.5 | 017-evl-evaluacion-del-sistema | |
| §11.6 | 001-base | |
| §11.6 | 017-evl-evaluacion-del-sistema | |
| §12.1 | 001-base | |
| §12.1 | 004-obs-observabilidad | |
| §12.1 | 015-cam-cambios-y-edicion-manual | |
| §12.3 | 004-obs-observabilidad | |
| §12.4 | 004-obs-observabilidad | |
| §12.6 | 004-obs-observabilidad | |
| §13.6 | 001-base | |
| §13.6 | 002-aut-autenticacion | |
| §13.6 | 003-pol-politica-y-guardarrailes | |
| §13.6 | 005-ent-entrevista-y-brief | |
| §13.6 | 007-run-ejecuciones | |
| §13.6 | 013-lec-lectura-web-y-pdf | |
| §13.6 | 015-cam-cambios-y-edicion-manual | |
| §14.1 | 001-base | |
| §14.1 | 002-aut-autenticacion | |
| §14.1 | 004-obs-observabilidad | |
| §14.1 | 006-tla-especificacion-del-harness | |
| §14.1 | 009-lea-validador-formal-de-la-historia | |
| §14.1 | 012-lin-linters-de-prosa | |
| §14.1 | 013-lec-lectura-web-y-pdf | |
| §14.1 | 016-mcp-servidor-mcp | |
| §14.1 | 018-sec-auditoria-de-seguridad | |
| §14.2 | 001-base | |
| §14.2 | 004-obs-observabilidad | |
| §14.2 | 017-evl-evaluacion-del-sistema | |
| §14.3 | 001-base | |
| §14.3 | 002-aut-autenticacion | |
| §14.3 | 003-pol-politica-y-guardarrailes | |
| §14.3 | 005-ent-entrevista-y-brief | |
| §14.3 | 007-run-ejecuciones | |
| §14.3 | 013-lec-lectura-web-y-pdf | |
| §14.3 | 015-cam-cambios-y-edicion-manual | |
| §14.3 | 016-mcp-servidor-mcp | |
| §14.4 | 001-base | |
| §14.4 | 007-run-ejecuciones | |
| §14.4 | 013-lec-lectura-web-y-pdf | |
| §14.5 | 001-base | |
| §14.5 | 003-pol-politica-y-guardarrailes | |
| §14.5 | 004-obs-observabilidad | |
| §14.5 | 014-pub-publicacion-y-versiones | |
| §15.2 | 001-base | |
| §15.2 | 007-run-ejecuciones | |
| §15.3 | 001-base | |

## 2. Diferencias

Una fila por diferencia entre el plan, junto con su spec, y `architecture.md`. Va en el apartado de su spec y se numera `NNN-k`.

| Tipo | Cuándo |
|---|---|
| omisión | `architecture.md` lo pide y el plan no lo entrega |
| deriva | el plan entrega algo que `architecture.md` no respalda |
| contradicción | los dos dicen cosas distintas: un nombre, un valor, un orden o un límite |

Cada diferencia lleva además la gravedad que le da el subagente `auditor`:

| Gravedad | Cuándo |
|---|---|
| bloqueante | contradice `architecture.md`, falta un requisito, sobra uno que `architecture.md` no respalda o usa un nombre fuera de `definitions.md` |
| menor | el resto: redacción, detalle u orden |

Una bloqueante se cierra de una de tres formas:

- **plan corregido**;
- **doc corregido**, por el [proceso 1](../workflow/1-docs.md) y con grill;
- **la cubre otra spec**, que tiene esa sección en §1.

Una menor se cierra igual o se queda en la matriz con estado **aceptada**.

**Gap cero** de una spec: todas sus filas de §1 revisadas, ninguna bloqueante abierta en su apartado y una pasada del `auditor` sobre la versión final que no encuentra ninguna bloqueante nueva. Las menores pueden quedar aceptadas.

### 001-base

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|
| 001-1 | §6.5 | contradicción | bloqueante | «una entrada por par y entero ≥ 0» | RF-BAS-11 y RF-BAS-13: una plaza `null` es una cifra sin calibrar y el servidor arranca, como pide §15.2 | Doc corregido, por el proceso 1: pendiente del grill | abierta |
| 001-2 | §15.2 | contradicción | bloqueante | «`operation.pricing` tampoco es una cifra por calibrar» | RF-BAS-11: «un modelo con valor … sin sus cuatro precios, si `operation.pricing` tiene valor»: admite `pricing` sin valor | Pendiente del grill: doc o spec | abierta |
| 001-3 | §7.4 | omisión | bloqueante | Una entrada inválida «cuenta como un intento» | RF-BAS-25 no decía dónde queda el resultado de `schema-salida` | Plan corregido: el resultado de la sesión lista cada llamada con su acierto o fallo de `schema-salida`, del que lo toman 007 (RF-RUN-24) y 004. §1: (§7.4, 007), (§10.2, 004) | cerrada |
| 001-4 | — (encargo; `verification.md` §4.7 y §9) | deriva | bloqueante | Ninguna sección respalda los entregables de proceso | R11, R13, R15–R17, RF-BAS-49, RF-BAS-50 y RF-BAS-54 | Pendiente del grill | abierta |
| 001-5 | §7.4, §7.5, §11.2, §14.3 | omisión | bloqueante | Tools integradas desactivadas, `Skill` solo con `personalizacion-natural`, hook de policy, modo de permisos, origen del revisor visual, `/api/banned-terms` | 001 da el mecanismo y remite a 003 | La cubre otra spec: 003 (§1) | cerrada |
| 001-6 | §7.3, §7.5, §10.2, §11.5, §12.1, §12.3, §12.4, §12.6, §14.1, §14.2 | omisión | bloqueante | Prompts versionados, spans de tool y hook de observabilidad, scores, coste con `pricing`, trazas, `auth_check()`, subir y promover prompts | Solo remitía a 004 la lectura de vuelta en CI | La cubre otra spec: 004 (§1). El plan nombra el hook de observabilidad de 004 | cerrada |
| 001-7 | §6.5, §7.5, §7.6, §9.1, §11.5, §14.3, §14.4, §15.2 | omisión | bloqueante | Copia de la config por tramo, intentos, `max_retries`, `max_resumes`, infraestructura → `interrupted`, `budget`, endpoints de ejecuciones, SSE, cifra sin valor en una ejecución | Solo remitía a 007 la cancelación | La cubre otra spec: 007, y 005 el presupuesto de la entrevista (§1) | cerrada |
| 001-8 | §6.6, §6.9, §6.10 | omisión | bloqueante | Corte temporal, escasez, BM25 en código, desempate, modelo congelado al crear la novela, guardián, reserva de turnos, reconciliación | Remite a 008 lo que se indexa y cómo se recupera | La cubren otras specs: 008, y 005 el modelo de incrustación (§1) | cerrada |
| 001-9 | §7.6, §10.5, §14.1 | omisión | bloqueante | Protocolo remoto completo, `max_verifier_seconds`, seguridad del workflow, Lean con Lake, TLC | «El verificador remoto completo es de 009»; TLC, de 006 | La cubren otras specs: 009 y 006 (§1) | cerrada |
| 001-10 | §6.11, §7.3, §7.5, §8.1, §8.3 | omisión | bloqueante | Escritores del índice, `CLAUDE.md` del workspace y skill, hook de validación, bucle, registro y aceptación | «Qué filas reemplaza cada registro lo decide 011» | La cubren otras specs: 010 y 011 (§1) | cerrada |
| 001-11 | §2, §6.6, §9.3, §9.7, §13.6, §14.1, §14.4, §14.5 | omisión | bloqueante | Gate, copia de la candidata, lectura, vista previa, PDF, escritorio, candidatas sin caché, versión publicada inmutable | Remite a 013 las páginas y a 014 la inmutabilidad | La cubren otras specs: 013 y 014 (§1) | cerrada |
| 001-12 | §6.11, §9.5, §13.6 | omisión | bloqueante | Flujo de cambios, cambio en el índice, página de estado de un cambio | Solo remitía a 015 la página | La cubre otra spec: 015 (§1) | cerrada |
| 001-13 | §10.2, §10.3 | omisión | bloqueante | Cada validador con sus puntos y criterios; calibración de los umbrales | «Los criterios del catálogo, de la spec de cada validador» | La cubren las specs de cada validador y 017 la calibración (§1) | cerrada |
| 001-14 | §2, §11.5, §11.6, §14.1, §14.2, §14.3 | omisión | bloqueante | bcrypt y PyJWT, spaCy, FastMCP y `/mcp`, `example`, evals, contraste de coste, `pip-audit` y `pnpm audit` | R4 sin paso ni remisión | Plan corregido: paso de R4 con la spec que adopta cada pieza. La cubren 002, 004, 005, 012, 016, 017 y 018 (§1) | cerrada |
| 001-15 | §14.2 | omisión | menor | `harness` solo sobre `store`, `platform` y `domain`; `platform` sin dependencias internas | RF-BAS-1 no nombraba `harness` | Plan corregido: el paso de RF-BAS-1 lista los contratos de `harness` y `platform` | cerrada |
| 001-16 | §11.6 | contradicción | menor | «Solo escribe fuera la orden de la CLI que reproduce el brief de ejemplo» | RF-BAS-35 sin excepción | Plan corregido: el paso lleva la excepción de 017 (RF-EVL-4) | cerrada |
| 001-17 | §14.3, §13.2 | contradicción | menor | `/mcp` fuera de `/api` | RF-BAS-37: toda ruta fuera de `/api` que no es un fichero da la página de entrada | Plan corregido: `/mcp` (016) se monta antes que el frontend compilado | cerrada |
| 001-18 | §7.3 | contradicción | menor | La skill «la cargan el writer y el editor» | RF-BAS-27: toda sesión carga sus skills | Plan corregido: cargar es tenerlas disponibles; solo el writer y el editor tienen `Skill` (003) | cerrada |
| 001-19 | §7.5 | contradicción | menor | Hook de policy, de validación y de observabilidad | «Cada hook concreto, de la spec de su rol» | Plan corregido: policy, 003; validación, 011; observabilidad, 004 | cerrada |
| 001-20 | §7.6 | contradicción | menor | Desenlaces `completed`, `turns_exhausted`, `time_exhausted`, `cut`, `infrastructure_failure` | RF-BAS-19 a 23 con el término en formato de identificador | Plan corregido: el término en texto y el identificador de `definitions.md` §12 entre paréntesis | cerrada |
| 001-21 | §1.2, §6.10 | deriva | menor | `window_ceiling` ≤ 100.000 | `design.md` §3.2: «entero entre 1 y 100.000» | El mínimo es el de un entero positivo, no una cifra inventada | aceptada |
| 001-22 | §6.5 | omisión | menor | «La config se valida entera al arrancar» | RF-BAS-11 no listaba una clave ausente | Plan corregido: una clave ausente impide arrancar, porque ningún campo tiene valor por defecto | cerrada |
| 001-23 | §14.1, §16 «Nombres» | omisión | menor | Stack y nombres | R2 a R5 y R10 sin paso; R1, R7 y R8 como notas sin clase | Plan corregido: R4 y R10 con paso propio; R1–R3, R5, R7 y R8 como notas con ID y clase | cerrada |
| 001-24 | §6.10, §14.4 | omisión | bloqueante | «la API, que es un solo proceso de uvicorn», cuenta su parte en memoria | RF-BAS-36 solo pedía uvicorn sin recarga: nada impedía `--workers` > 1 | Plan corregido: RF-BAS-36 lanza un solo proceso, sin `--workers` ni recarga, y la prueba lo comprueba | cerrada |
| 001-25 | §6.10, §15.2 | contradicción | menor | «Al arrancar se valida `api_window_share < window_ceiling`», sin condición | RF-BAS-11: «`api_window_share`, si tiene valor, …» | Sin valor es una cifra sin calibrar, que arranca por §15.2 y RF-BAS-13; la comparación corre cuando la tiene | aceptada |
| 001-26 | §6.10, §12.1, §15.2 | deriva | menor | Sin cota inferior para `api_window_share`, `api_window_wait_seconds` ni `generation_lookup_seconds` | `design.md` §3.2: entero ≥ 1 y número ≥ 0 | Es el dominio del tipo, como en 001-21 | aceptada |
| 001-27 | §14.5 | contradicción | menor | `runs ||--o| versions : candidata` | `versions.run_id` sin `UNIQUE` | Design corregido: `versions.run_id` es `UNIQUE` | cerrada |
| 001-28 | §14.5 | contradicción | menor | El diagrama da las tablas y sus relaciones | `design.md` §4 tiene 9 claves ajenas sin dibujar: `interview_messages.role_session_id`, `change_requests.base_version_id`, `manual_edits.base_version_id`, `facts.supersedes_id`, `events.excluded_character_id`, `element_assignments.personal_element_id`, `chronology_files.version_id`, `role_sessions.attempt_id`, `verdicts.attempt_id`; RF-BAS-53 no pasaría al cerrar | Doc corregido, por el proceso 1: añadirlas a §14.5. Pendiente | abierta |
| 001-29 | §14.2 | omisión | menor | `harness` con el editor, el registrador y la aceptación; `execution` con autenticación, cola, SSE e informe | `design.md` §2.1 no los nombraba | Design corregido | cerrada |

### 002-aut-autenticacion

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 003-pol-politica-y-guardarrailes

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 004-obs-observabilidad

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 005-ent-entrevista-y-brief

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 006-tla-especificacion-del-harness

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 007-run-ejecuciones

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 008-mem-memoria

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 009-lea-validador-formal-de-la-historia

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 010-pln-planificacion

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 011-cap-produccion-por-capitulo

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 012-lin-linters-de-prosa

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 013-lec-lectura-web-y-pdf

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 014-pub-publicacion-y-versiones

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 015-cam-cambios-y-edicion-manual

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 016-mcp-servidor-mcp

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 017-evl-evaluacion-del-sistema

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|

### 018-sec-auditoria-de-seguridad

| # | Sección | Tipo | Gravedad | architecture.md | Plan | Resolución | Estado |
|---|---|---|---|---|---|---|---|
