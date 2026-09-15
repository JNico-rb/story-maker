# story-maker

Harness para escribir novelas en castellano sobre el mundo tras la revolución de la IA. Tiene dos fases (`specs/functional.md` §1 y §10): **ahora**, validar el diseño en Claude Code con el modelo caro e historias de 3 capítulos; **después**, portar ese mismo diseño a un runner propio contra OpenRouter con un modelo barato para llegar a 100–200 capítulos. En esta fase **no hay código**: el harness son la skill `/novela`, tres subagentes y estas reglas. La especificación de comportamiento es `specs/functional.md`; manda sobre cualquier otro fichero.

## Cómo se usa

- Si el usuario pide "genera la novela", "haz lo de las especificaciones", "escribe una historia" o similar, **invoca la skill `novela`** con su petición como argumentos. No escribas prosa de novela desde la sesión principal: eso lo hacen los subagentes a través de la skill.
- Comandos: `/novela nueva "<idea>"` · `/novela continuar <carpeta>` · `/novela estado <carpeta>` · `/novela comparar <caso>`.
- Qué se espera que produzca una ejecución completa: `specs/inventario.md`. Comparar dos novelas de la misma idea con distinta configuración (modelo caro/barato, Claude Code/runner): `comparativa/`.
- Todo lo que se diseñe aquí tiene que poder portarse al runner (`specs/functional.md` §10): los agentes son prompts con contrato, no piezas de Claude Code. Si una solución solo funciona en Claude Code, se anota como tal.
- El interrogatorio inicial (fase 1) se hace con la skill `mattpocock-skills:grilling`; las preguntas al usuario **siguen en pie** y no se saltan salvo en modo de prueba.
- Todo lo ajustable (tamaño de la historia, modelos, reintentos, reescrituras, memoria) está en **`harness.config.json`**, explicado en `specs/functional.md` §7. Si hay que cambiar el comportamiento, se edita ahí, no en la skill ni en los subagentes.

## Reglas que aplican siempre

1. Una novela = una carpeta `novelas/<slug>/`. Es el único estado. Nada en memoria que no esté en disco tras cada paso.
2. `estado.json`, `registro.md`, `entrevista.md`, `config.json`, `informe-cierre.md`, `manuscrito.md` y los `informe-*.md` los escribe **solo el orquestador** (la sesión que ejecuta la skill). Ningún subagente los toca.
3. Cada subagente escribe únicamente en su zona (definida en su fichero de `.claude/agents/`). Al volver un subagente, el orquestador comprueba con `git status` que solo cambió su zona; lo demás se revierte con `git checkout --` y se registra.
4. **Nada aprobado se modifica**: biblia y escaleta tras la aprobación; un capítulo tras su veredicto APROBADO o su aceptación por agotamiento.
5. El orquestador hace commit en `novelas/<slug>` en los puntos consistentes (carpeta creada, escaleta aprobada, cada capítulo cerrado, novela completa, cualquier parada) **sin pedir confirmación**. Fuera de `novelas/` no se commitea nada sin que el usuario lo pida.
6. Toda ejecución termina con un informe de cierre (ÉXITO o PARADA con motivo y acción para continuar), en la sesión y en `informe-cierre.md`. Nunca morir en silencio.
7. Los cambios de diseño del harness se anotan en `CHANGELOG.md` (qué, por qué y qué se descartó), con el formato que el propio fichero explica.

## Artefactos

Tres ficheros. Cada agente toca solo lo que le corresponde.

### `biblia.md`
- Contiene: premisa, mundo post-IA, reglas inviolables (3-7, numeradas), tono/POV/estilo, personajes.
- Escribe: interrogador. Una sola vez.
- Después: INMUTABLE. Ningún agente la edita.
- Lee: escritor (antes de cada capítulo), revisor (como vara de medir).
- Plantilla: `plantillas/biblia.md`.

### `escaleta.md`
- Contiene: estructura en tres actos + una ficha por capítulo.
- Ficha: `objetivo`, `sucesos[]`, `personajes[]`, `gancho`, `palabras_objetivo`.
- Escribe: interrogador.
- Lee: escritor (SOLO la entrada de su capítulo), revisor (para contrastar).
- Plantilla: `plantillas/escaleta.md`.

### `manuscrito.md`
- Contiene: título, índice, capítulos aprobados en orden.
- Escribe: el harness, al final. Ningún agente narrativo escribe aquí.
- Entregable final.

## Reglas de revisión
- El revisor cita la fuente del fallo: "contradice biblia regla N" o "no cumple objetivo de escaleta cap. N".
- Un capítulo no entra en `manuscrito.md` sin pasar revisión.