# story-maker

Historial de cambios del harness. **Para qué sirve este fichero:** aquí se anota *qué* cambió en el harness y *por qué*, de forma que cualquiera (tú dentro de tres meses, o Claude Code en otra sesión) pueda entender una decisión sin reconstruirla del historial de git ni releer las specs enteras.

Cómo se escribe:

- Una sección `## <versión>` por versión, **de la más reciente a la más antigua**, con versionado semántico: **Major** = cambia el contrato del harness o rompe novelas existentes · **Minor** = capacidad nueva compatible · **Patch** = arreglo o ajuste de redacción.
- Dentro, `### Major Changes` / `### Minor Changes` / `### Patch Changes`.
- Cada entrada: una línea con el **resumen en negrita** y, debajo, viñetas anidadas con el detalle y el motivo. Si hay commit, se cita al principio entre corchetes.
- Las decisiones descartadas también se anotan: saber qué *no* se hizo y por qué evita volver a proponerlo.

---

## 0.2.0

##### 0.4.0

### Major Changes

- **El proyecto tiene dos fases y la spec lo dice: Claude Code ahora, runner contra OpenRouter después.**

  - `specs/functional.md` §1 deja de afirmar "no hay código" como decisión fija y pasa a describir dos fases: (1) validar el diseño en Claude Code con el modelo caro e historias de 3 capítulos; (2) portar ese mismo diseño a un runner propio contra OpenRouter con un modelo barato para llegar a 100–200 capítulos. Nueva §10 con qué se porta sin cambios (contratos de los agentes, plantillas, prompts, configuración, carpeta y estado), qué se reimplementa (orquestador, invocación, zona de escritura, entrevista, confirmación) y el contrato que debe cumplir el runner (pasar el inventario y los criterios de aceptación sin adaptación).
  - `CLAUDE.md` añade la regla: todo lo que se diseñe tiene que poder portarse; si algo solo funciona en Claude Code, se anota.
  - Motivo: el objetivo del usuario siempre fue montar la solución agéntica con el modelo caro y pasarla después a uno barato en OpenRouter. La 0.1.0 había abandonado la línea OpenRouter por completo y la spec, que manda sobre todo, prohibía el código; con eso el destino era inalcanzable y cualquier sesión futura lo habría defendido. La decisión de 0.1.0 se reinterpreta: se abandonó **empezar** por el código, no llegar a él.
  - Descartado: seguir en Claude Code con modelos baratos como fase final. Funciona para abaratar (paso 2 del plan), pero no da el bucle desatendido de 200 capítulos (una pausa cada 5 capítulos son 40 relanzamientos a mano).

### Minor Changes

- **Volumen por invocación: el dato para decidir el modelo.**

  - Cada fila `invocacion` de `registro.md` lleva `modelo`, `pal_entrada` (palabras de los ficheros que se le mandó leer) y `pal_salida` (lo que entregó). El informe de cierre suma por subagente y por modelo. `specs/functional.md` §6.6.
  - Motivo: Claude Code no expone el coste, pero la decisión de pasar a un modelo barato es económica. Volumen × tarifa = coste, para cualquier modelo y para el runner (que registrará tokens reales en las mismas columnas).

- **Inventario de salidas: `specs/inventario.md`.**

  - Lista, fichero a fichero, lo que debe producir una ejecución completa: qué es, cuántos hay, quién lo escribe y su definición de hecho. Incluye la cuenta por perfil, lo que **no** genera, un procedimiento de 6 pasos para comprobar que una ejecución está completa, y señales de calidad distintas de la completitud.
  - Es además la definición de "misma salida" para el runner de la fase 2 (§10.3).

- **Carpeta `comparativa/` y comando `/novela comparar <caso>`: dos ejecuciones del harness con la misma idea.**

  - Un caso = `caso.md` (idea, qué se compara, lados A y B como rutas a `novelas/<slug>/`, qué difiere en `config.json`) + `comparacion.md` (lo rellena el comando). Las novelas se referencian, no se copian: su historial de git es parte de lo que se mide. `plantilla/` se copia para crear un caso.
  - El comando llena un bloque medible (capítulos, palabras contadas, intentos, agotamientos, reintentos, problemas globales, artefactos, volumen por modelo) y otro de lectura donde cada casilla exige una cita. Nada se estima; lo no disponible es `desconocido`. Termina con el veredicto y una lista de cambios accionables para el harness.
  - Motivo: es lo que decide el paso 2 (modelo caro frente a barato) y valida el paso 3 (Claude Code frente al runner) del plan de §7.7.
  - Descartado: la versión anterior de esta carpeta comparaba el harness con un **prompt suelto** a OpenRouter. Medía si el harness aporta algo frente a no tener harness, que no es la decisión pendiente; y además nunca llegó a crearse en disco aunque la 0.3.0 la daba por hecha. Se sustituye por esta.

- **Plan de escalado en cinco pasos (`specs/functional.md` §7.7)**: validar (relato, opus) → abaratar (mismo harness, haiku/sonnet con escalado) → portar al runner → crecer (12, 30) → saga (100–200). Cada paso cambia solo configuración salvo los dos marcados como trabajo de harness: el runner y `memoria.digesto_por_acto`.

- **`saga` llega a 200 capítulos** (`capitulos_max: 200`). El objetivo declarado es 100–200; el techo anterior de 120 lo hacía inalcanzable por configuración.

### Patch Changes

- **Arreglado el bug de `verificar-zona.md` que borraba el capítulo antes de revisarlo.** El paso (a) exigía `git status` vacío antes de *cada* invocación y, si no lo estaba, hacía `git checkout` + `git clean` de la carpeta. Al invocar al revisor, `intento-K.md` y `resumen-K.md` recién escritos están sin commitear: el procedimiento los habría eliminado. Ahora el orquestador **fija el índice** (`git add -A`) antes de invocar y, al volver, lo que difiere del índice es exactamente lo que tocó el subagente; los ficheros fuera de zona se restauran desde el índice. La limpieza total pasa a `descartar()`, que solo se usa al reanudar o al parar, y deshace también el índice (`git reset -q HEAD --`) antes de `checkout` y `clean`.
- **La spec dice quién escribe los informes.** `functional.md` §3 y §5.3 afirmaban que el revisor escribía `informe-N.md` e `informe-global.md`; `CLAUDE.md`, el inventario, `revisor.md` y `capitulo.md` decían que los escribe el orquestador a partir del YAML del revisor. Gana lo segundo (el veredicto en disco es el recalculado por el harness) y la spec queda corregida.
- **Configuración por defecto = fase de validación**: los tres agentes en `opus`, `escalado.activo: false`. Antes era `sonnet` con escalado a `opus`, un híbrido que no respondía ni a "cuál es el techo del diseño" ni a "aguanta el modelo barato". Las configuraciones de abaratamiento y mínima quedan documentadas en §7.3 y se aplican por comando sin editar el fichero.
- **`README.md` explica el proyecto**: las dos fases, cómo se lanza, dónde está cada cosa. Antes eran tres líneas.
- **El cierre en ÉXITO comprueba la ejecución contra el inventario** y avisa en el informe de cierre de cualquier artefacto que falte.
- **`functional.md` §9 referencia el inventario y la comparativa**; antes eran un comando y un documento que la spec que manda no conocía.

 Minor Changes

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
