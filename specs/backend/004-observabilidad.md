# 004 — Observabilidad

> Carril: B · Depende de: 001-base · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Dar el **adaptador real** del puerto de observabilidad que 001-base deja abierto con su doble nulo: el cliente de Langfuse con su **máscara** de datos personales, `auth_check()` contra el fallo silencioso, los **prompts versionados** (`story-maker prompts push` y su lectura por etiqueta al arrancar) y la exportación de cada `Score` con su nombre canónico. Fija también cuándo se usa el adaptador real y cuándo el doble nulo. No abre ninguna traza, sesión ni span por su cuenta: eso lo hace quien abre la sesión de rol o la ejecución (001-base, 003-puerto-de-agente y las specs de cada rol), sobre el mismo puerto.

## Alcance

- **Selección de adaptador**: qué variables de Langfuse activan el adaptador real en vez del doble nulo de 001-base.
- **Adaptador real**: cumple el mismo contrato observable que el doble nulo de 001-base (C19–C21), pero exporta de verdad a Langfuse Cloud UE, con la máscara aplicada antes de exportar.
- **`Mascara`**: sustituye nombres y fechas del brief por `[NOMBRE_n]` y `[FECHA]` en todo texto que sale hacia Langfuse; no toca tokens, coste, latencia ni scores; la de una llamada MCP que toca varias novelas es la unión de sus máscaras.
- **`auth_check()`**: comprobación real de las credenciales de Langfuse y de que cada rol tiene su prompt con la etiqueta vigente; corre en `check-env` y al arrancar `serve`, con el mismo formato de informe de 001-C14/C15.
- **`PromptVersionado`**: `story-maker prompts push` sube una versión nueva por rol cuando cambia la huella de su fichero, con la etiqueta `LANGFUSE_PROMPT_LABEL`; al arrancar, el adaptador real lee por esa etiqueta la versión vigente de cada rol, y cada `LlamadaDeModelo` la enlaza.
- **Scores**: exporta el resultado de un validador como `Score` con su nombre canónico (`definitions.md` §12.3), asociado a la traza y, si es de capítulo, a su span, con un comentario con los motivos. TLC nunca envía score.
- **Demostraciones (D, al final)**: una ejecución real vista en Langfuse; una iteración de tuning con antes y después de un prompt cambiado.

## Fuera de alcance

- El puerto de observabilidad, sus tipos (`Traza`, `Span`, `LlamadaDeModelo`, `Score`), el doble nulo y su contrato observable (C19–C21) → 001-base. Esta spec da el segundo adaptador del mismo puerto, no un puerto nuevo.
- Abrir la traza de una ejecución, entrevista, importación, propuesta de cambio o llamada MCP, el span `capitulo-<n>` y los spans `rol:<rol>` y `tool:<tool>` → quien abre la sesión: 003-puerto-de-agente, 008-brief-y-entrevista, 011-produccion-de-capitulos, 014-cambios-del-lector, 015-servidor-mcp.
- Calcular el uso y el coste de una sesión (uso real × `operation.pricing`) → 003-puerto-de-agente (003-I5); aquí solo se exporta lo ya calculado, sin tocarlo.
- Qué resultado da cada validador y cuándo corre → cada spec de validador (005, 011, 012, 018, 019); aquí solo se define cómo se exporta ese resultado.
- El contenido de cada prompt de sistema y su ubicación en el workspace → cada spec de rol (`backend/AGENTS.md`); aquí solo su versión y su subida.
- Cola de anotación o puntuación de la revisión humana → 020-evals.
- Retención del plan gratuito de Langfuse como riesgo de proceso → `verification.md` §6 U15 (ya escrito).

## Comportamiento observable

**Convenciones.** Salvo que un caso diga lo contrario, están las cuatro variables de Langfuse (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_PROMPT_LABEL`) con marcadores de prueba y un cliente de Langfuse simulado por fixture (sin red): responde a la comprobación de credenciales, a la consulta de un prompt por etiqueta y captura lo exportado, igual que hace el doble nulo de 001-base con lo emitido por el puerto. Ninguna prueba T abre una conexión de verdad (verification.md §3.3).

### Selección de adaptador

#### 004-C01 — Con las cuatro variables de Langfuse, se usa el adaptador real (T)
- **Entrada:** ajustes válidos (001-C3, 001-C4) con las cuatro variables de Langfuse presentes.
- **Salida:** el puerto de observabilidad usa el adaptador real: `check-env` (004-C03) lo confirma y lo emitido llega al cliente simulado de Langfuse, no al doble nulo.

#### 004-C02 — Sin alguna variable de Langfuse, se usa el doble nulo (T)
- **Entrada:** ajustes válidos con una, ninguna o tres de las cuatro variables de Langfuse.
- **Salida:** el puerto usa el doble nulo de 001-base: `check-env` dice que es el doble nulo, sin Langfuse (001-C14); nada se exporta ni se comprueba de verdad. Es el mismo resultado que 001-C4 («sin ninguna variable de Langfuse, válido») para arrancar, ahora explicado: faltar una sola ya activa el doble nulo.

### `auth_check()` y `check-env`

#### 004-C03 — `check-env` informa «ok» cuando las credenciales son válidas y cada rol tiene su prompt vigente (T)
- **Entrada:** las cuatro variables de Langfuse; el cliente simulado confirma las credenciales y da, para cada rol de `definitions.md` §12.2 con fichero de prompt en el workspace (los que sube `prompts push`), una versión de prompt con la etiqueta `LANGFUSE_PROMPT_LABEL`.
- **Salida:** la línea de observabilidad de `check-env` (001-C14) dice `ok` con el adaptador real, no el doble nulo. `serve` arranca.

#### 004-C04 — `check-env` falla si las credenciales de Langfuse no son válidas (T)
- **Entrada:** las cuatro variables de Langfuse; el cliente simulado rechaza la comprobación de credenciales.
- **Salida:** la línea de observabilidad de `check-env` falla, nombra Langfuse y el motivo, sin mostrar las claves. Código 1. Nunca se calla el fallo (`architecture.md` §13.6).

#### 004-C05 — `check-env` falla si a un rol le falta el prompt con la etiqueta vigente (T)
- **Entrada:** credenciales válidas; el cliente simulado no tiene versión con `LANGFUSE_PROMPT_LABEL` para uno de los roles con fichero de prompt en el workspace.
- **Salida:** la línea de observabilidad falla y nombra el rol sin prompt. Código 1.

#### 004-C16 — `check-env` no exige prompt a un rol sin fichero en el workspace (T)
- **Entrada:** credenciales válidas; el workspace no tiene fichero de prompt para `visual_reviewer` (017, fuera de alcance) y el cliente simulado tampoco tiene versión para él; los demás roles, sí.
- **Salida:** la línea de observabilidad dice `ok`, sin nombrar `visual_reviewer`. `serve` arranca.

#### 004-C06 — `serve` no arranca en las mismas situaciones que `check-env` (T)
- **Entrada:** `serve` en cualquiera de las situaciones de fallo de 004-C04 y 004-C05.
- **Salida:** los mismos motivos que `check-env`, sale con 1 y no abre el puerto (mismo patrón que 001-C15).

### Prompts versionados

#### 004-C07 — `prompts push` sube una versión nueva si cambia la huella del fichero (T)
- **Entrada:** el prompt de un rol cuya huella no coincide con la última versión subida con la etiqueta `LANGFUSE_PROMPT_LABEL`.
- **Salida:** se sube una versión nueva, nombrada como la etiqueta del rol (`definitions.md` §12.2), con esa etiqueta.

#### 004-C08 — `prompts push` no sube si la huella no cambió (T)
- **Entrada:** el prompt de un rol cuya huella coincide con la última versión subida.
- **Salida:** no se sube nada nuevo.

#### 004-C09 — Al arrancar, cada `LlamadaDeModelo` enlaza la versión de prompt leída por la etiqueta (T)
- **Entrada:** con el adaptador real y credenciales válidas, una petición del `PromptVersionado` de un rol con `LANGFUSE_PROMPT_LABEL`.
- **Salida:** responde con la versión vigente de ese rol (no «sin versión remota», la respuesta del doble nulo en 001-C21); esa versión es la que enlaza cada `LlamadaDeModelo` de una sesión de ese rol.

### Máscara

#### 004-C10 — La máscara sustituye nombres y fechas del brief en lo exportado, sin tocar tokens, coste, latencia ni scores (T)
- **Entrada:** una novela cuyo brief nombra al destinatario («Toby») y una fecha; una entrada y una salida de una sesión de rol que citan ambos; un `Score` con un comentario que también los cita.
- **Salida:** lo que llega al cliente de Langfuse sustituye «Toby» por `[NOMBRE_1]` y la fecha por `[FECHA]`, en la entrada, en la salida y en el comentario del score. Tokens, coste, latencia y el valor del score llegan intactos.

#### 004-C11 — La máscara de una llamada MCP que toca varias novelas es la unión de sus máscaras (T)
- **Entrada:** una traza `mcp:list_novels` que devuelve datos de dos novelas, cada una con su destinatario y su fecha.
- **Salida:** lo exportado sustituye los nombres y las fechas de las dos novelas, con la máscara de cada una.

### Scores

#### 004-C12 — Cada resultado de validador se exporta como `Score` con su nombre canónico (T)
- **Entrada:** un `ResultadoDeValidador` de prueba, de un validador programático y de uno semántico, con su nombre de la tabla de `definitions.md` §12.3, su valor y su comentario con los motivos; uno de capítulo y uno que no lo es.
- **Salida:** cada uno llega como `Score` con exactamente ese nombre, asociado a la traza de su ejecución o entrevista y, el de capítulo, también a su span `capitulo-<n>`, con el comentario con los motivos.

#### 004-C13 — TLC no envía score (T)
- **Entrada:** el resultado de `harness-tla`.
- **Salida:** no se exporta ningún `Score`: solo corre en desarrollo y CI (`architecture.md` §13.3).

### Demostraciones

#### 004-C14 — Una ejecución real vista en Langfuse (D, al final)
- **Entrada:** con las cuatro variables de Langfuse de verdad y `LLM_PROVIDER=claude_login`, una ejecución de generación completa.
- **Salida:** en Langfuse Cloud UE se ven la sesión (= la novela), sus trazas, sus spans, sus scores, y los tokens, el coste y la latencia por llamada, por capítulo y por novela; el brief con nombres y fechas enmascarados. Capturas para la presentación y para `verification.md` §4.1 y §4.2.

#### 004-C15 — Una iteración de tuning muestra qué versión de prompt produjo cada resultado (D, al final)
- **Entrada:** un cambio de la huella del prompt de un rol, `prompts push`, y una ejecución antes y otra después del cambio.
- **Salida:** las dos ejecuciones enlazan versiones distintas de ese prompt; la tabla de evals (020) distingue los resultados de cada una por su versión.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 004-I1 | Todo texto que el adaptador real exporta a Langfuse —entradas, salidas y comentarios de score— pasa antes por la máscara; nunca se exporta el texto crudo del brief | T | 004-C10, 004-C11 |
| 004-I2 | Con alguna de las cuatro variables de Langfuse ausente, el puerto usa siempre el doble nulo: ninguna prueba T, ni `check-env`, ni `serve` abren una conexión real | T | 004-C02; las pruebas de la spec corren con la red saliente bloqueada, salvo `127.0.0.1` (mismo criterio que 001-I3) |
| 004-I3 | `auth_check()` falla de forma visible ante credenciales inválidas o un prompt sin su etiqueta vigente, nunca en silencio | T | 004-C04, 004-C05 (`architecture.md` §13.6) |
| 004-I4 | `prompts push` sube una versión nueva de un rol si y solo si cambia la huella de su fichero | T | 004-C07, 004-C08 |
| 004-I5 | El nombre de cada `Score` exportado es exactamente uno de la tabla canónica de `definitions.md` §12.3, sin sinónimos | A | mypy/estático sobre el catálogo de nombres (mismo criterio que 001-I5, 001-I7); `verificador` al cerrar |
| 004-I6 | El adaptador real cumple el mismo contrato observable que el doble nulo de 001-base (C19–C21: trazas, spans, niveles, excepciones) | I | `verificador`, comparando el comportamiento del adaptador real (con el cliente simulado) contra los casos de 001-base |
| 004-I7 | Ninguna llamada de esta spec a un modelo o a Langfuse real ocurre en una prueba T | T | Red saliente bloqueada salvo `127.0.0.1`; 004-I2 |

## Docs referenciados

- `architecture.md`:
  - §13.1: sesiones, trazas y spans, sus etiquetas.
  - §13.2: uso, coste y latencia; `role_sessions` como respaldo.
  - §13.3: scores de todos los validadores; TLC sin score.
  - §13.4: prompts versionados, `prompts push`, lectura por etiqueta.
  - §13.5: máscara de datos personales.
  - §13.6: fallos silenciosos, `auth_check()`, doble nulo.
  - §15.9: contratos que nacen en 001-base; el adaptador real lo aporta la spec posterior.
- `definitions.md`:
  - §8: `Sesion`, `Traza`, `Span`, `LlamadaDeModelo`, `PromptVersionado`, `Mascara`.
  - §12.1: identificadores de componentes de código (`observability_port`, `observability_hook`).
  - §12.2: roles y sus etiquetas.
  - §12.3: etiquetas de Langfuse, nombres de validadores y de scores.
  - §6: `Criterio`, `ResultadoDeValidador`.
  - §7: `AuditLog` (no aplica a esta spec: ver 001-base y 005-guardarrailes).
- `verification.md`:
  - §2: clases.
  - §3.3: ninguna prueba T llama a un modelo real ni a Langfuse.
  - §4.1: observabilidad y trazas, T con doble nulo, D en Langfuse real, retención (U15).
  - §5: filas 3.8, 5.0, 5e.3, 6.1–6.5, 7.5, O.4 (marcadas 004, con quien las comparte).
  - §6: U15 (retención del plan gratuito), U23 (coste como estimación).
- `project-constraints.md`: «Trazado con Langfuse» (opcional).
- `backend/AGENTS.md`: propiedad de `observability/` (cliente Langfuse, máscara, prompts versionados, scores, doble nulo — este último ya de 001-base).
- Specs: 001-base (puerto y doble nulo, contrato C19–C21); 003-puerto-de-agente (coste, `LlamadaDeModelo`, quién pide el `PromptVersionado`); 011-produccion-de-capitulos, 012-gate-de-publicacion, 018-linters-de-prosa, 019-edicion-manual (qué validador da cada resultado); 015-servidor-mcp (trazas `mcp:<tool>`).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué activa el adaptador real frente al doble nulo? | Las cuatro variables de Langfuse a la vez (`PUBLIC_KEY`, `SECRET_KEY`, `BASE_URL`, `PROMPT_LABEL`); falta una y es doble nulo, consistente con 001-C4 («sin ninguna, válido») | `architecture.md` §15.9 (lo deja a 004); **decisión para §18** |
| ¿Cómo se prueba `auth_check()` real sin llamar a Langfuse? | Con un cliente de Langfuse simulado por fixture, que responde igual que la API real ante credenciales válidas o inválidas; ninguna prueba T abre red | `verification.md` §3.3; **decisión para §18** |
| ¿La máscara cubre solo entradas y salidas de `LlamadaDeModelo`? | No: cualquier texto exportado a Langfuse, incluidos los comentarios de score, porque pueden citar el brief | `architecture.md` §13.5 («antes de exportar nada»); **decisión para §18** |
| ¿Quién calcula el coste que exporta 004? | Nadie aquí: lo calcula 003 (uso × `operation.pricing`); 004 solo lo transporta sin tocarlo | `specs/backend/003-puerto-de-agente.md` 003-I5 |
| ¿`prompts push` sube todos los roles o solo el que cambió? | Solo el que cambió su huella; los demás no se tocan | `architecture.md` §13.4 |
| ¿Riesgo de retención del plan gratuito? | Ya es U15 en `verification.md` §6; no se repite aquí, solo se referencia | `verification.md` §6 U15 |
