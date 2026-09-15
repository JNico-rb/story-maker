# story-maker

Historial de cambios del harness. **Para qué sirve este fichero:** aquí se anota *qué* cambió en el harness y *por qué*, de forma que cualquiera (tú dentro de tres meses, o Claude Code en otra sesión) pueda entender una decisión sin reconstruirla del historial de git ni releer las specs enteras.

Cómo se escribe:

- Una sección `## <versión>` por versión, **de la más reciente a la más antigua**, con versionado semántico: **Major** = cambia el contrato del harness o rompe novelas existentes · **Minor** = capacidad nueva compatible · **Patch** = arreglo o ajuste de redacción.
- Dentro, `### Major Changes` / `### Minor Changes` / `### Patch Changes`.
- Cada entrada: una línea con el **resumen en negrita** y, debajo, viñetas anidadas con el detalle y el motivo. Si hay commit, se cita al principio entre corchetes.
- Las decisiones descartadas también se anotan: saber qué *no* se hizo y por qué evita volver a proponerlo.

---

## 0.2.0

### Minor Changes

- **Toda la configuración ajustable pasa a `harness.config.json`**, en la raíz del repositorio.

  - Es el único fichero que hay que editar para cambiar el comportamiento del harness: tamaño de la historia, modelos, reintentos, reescrituras, memoria y regla de veredicto. Documentado en `specs/functional.md` §7.
  - Sustituye a `.claude/skills/novela/config.md`, que se elimina. Los procedimientos y los subagentes leen ahora `config.json`.
  - Al crear una novela, la configuración efectiva se **congela** en `novelas/<slug>/config.json`. Editar el fichero global después no afecta a las novelas ya empezadas.
  - Motivo: el usuario quería poder tocar páginas, capítulos, reintentos, modelos y límites desde un sitio, sin abrir la skill ni las specs.

- **Perfiles de tamaño: `relato`, `novela_corta`, `novela`, `saga`.**

  - `perfil_activo` es una sola cadena y es lo que escala el proyecto: de 3 capítulos de prueba a 100. Por defecto, `relato`.
  - Cada perfil fija `capitulos_objetivo`, `capitulos_min`/`max` y `palabras_por_capitulo`.
  - Alternativa por páginas: si un perfil define `paginas_objetivo`, manda sobre `capitulos_objetivo` y el harness deriva los capítulos con `formato.palabras_por_pagina` (250 por defecto). Si el resultado se sale del rango, para antes de invocar a nadie.
  - Motivo: el plan es validar con pocos capítulos y escalar; así el salto es cambiar un valor, no reescribir la spec.

- **Modelo configurable por subagente, con escalado cuando algo va mal.**

  - `modelos.interrogador` / `escritor` / `revisor` fijan el modelo base (`sonnet` por defecto).
  - `modelos.escalado` sube a un modelo mejor (`opus` por defecto) en las situaciones que lo merecen: reescritura tras un rechazo (`escritor_desde_intento: 2`), juicio del último intento (`revisor_desde_intento: 3`), reintento tras fallo técnico, y revisión global final.
  - El orquestador pasa el modelo en cada invocación (SKILL.md §8) y lo registra en `registro.md`.
  - Motivo: el primer intento no necesita el modelo caro; el que arregla un capítulo rechazado, sí.

- **`memoria` como palanca de escalado.**

  - `resumenes_completos_ultimos` (por defecto `null` = todos), `capitulo_anterior_integro` y `digesto_por_acto` controlan cuánto contexto recibe el escritor.
  - Pendiente y anotado como tal: `digesto_por_acto` **no está implementado**. Hasta que lo esté, limitar la ventana de resúmenes pierde información de los capítulos antiguos, así que el perfil `saga` (100 capítulos) todavía no es viable. Es el siguiente trabajo del harness.

### Patch Changes

- **La regla de veredicto pasa a ser numérica y configurable**: `veredicto.rechaza_con_graves` (1) y `veredicto.rechaza_con_leves` (2). Antes estaba escrita en prosa en `config.md`. El orquestador la sigue recalculando él, sin fiarse del veredicto que escriba el revisor.
- **`limites.pausa_cada_capitulos` admite `null`** para desactivar la pausa programada.
- **`specs/changes.md` se elimina**: su contenido vive aquí. `specs/functional.md` §9 y `CLAUDE.md` apuntan a este fichero.

## 0.1.0

### Minor Changes

- **Harness montado sobre Claude Code, sin código.**

  - Creados `CLAUDE.md`, `.claude/skills/novela/` (SKILL.md, procedimientos/, plantillas/), `.claude/agents/{interrogador,escritor,revisor}.md`, `pruebas/respuestas-prueba.md` y `novelas/`.
  - El harness es la skill `/novela` ejecutada por Claude en la sesión; interrogador, escritor y revisor son subagentes. No hay programas, librerías ni servicios propios.
  - Motivo: el usuario quiere decirle a Claude Code "haz lo de las especificaciones" y que con eso genere la novela.

- **El interrogatorio inicial se mantiene y se hace con `mattpocock-skills:grilling`.**

  - El orquestador hace de intermediario: los subagentes no hablan con el usuario. El resultado se escribe en `entrevista.md` y el subagente `interrogador` lo convierte en biblia y escaleta.
  - El usuario confirma la escaleta antes de que se escriba una sola línea de novela.

- **Zonas de escritura verificadas con git.**

  - Cada subagente declara en qué ficheros puede escribir; al volver, el orquestador compara `git status` y revierte con `git checkout` lo que se haya salido, registrando el incidente y repitiendo la invocación.
  - Descartado: un hook `PreToolUse` que bloqueara las escrituras. Era más fuerte, pero exige un comando de shell y el usuario no quiere código de ningún tipo.

- **Commits automáticos dentro de `novelas/`** en los puntos consistentes (carpeta creada, escaleta aprobada, capítulo cerrado, novela completa, parada), sin pedir confirmación. Fuera de esa carpeta, nunca sin que el usuario lo pida. Es lo que hace posible la reanudación y la verificación de zonas.

### Major Changes

- **Se abandona la implementación en Python + OpenRouter + Pydantic AI.**

  - Toda la línea de trabajo anterior (CLI, SDK, modelos configurables por API, exportación con librerías, tests en pytest) se descarta a favor del harness en Claude Code.
  - Consecuencias: desaparecen el presupuesto en dinero (Claude Code no expone el coste; los límites pasan a ser estructurales), la exportación a PDF y DOCX (solo Markdown) y los códigos de salida (no hay proceso).
  - Motivo: decisión del usuario. Quiere el harness, no un programa, y que sea Claude Code quien escriba las historias con él.
