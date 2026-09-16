# story-maker

Historial de cambios del harness. **Para qué sirve este fichero:** aquí se anota *qué* cambió en el harness y *por qué*, de forma que cualquiera (tú dentro de tres meses, o Claude Code en otra sesión) pueda entender una decisión sin reconstruirla del historial de git ni releer las specs enteras.

Cómo se escribe:

- Una sección `## <versión>` por versión, **de la más reciente a la más antigua**, con versionado semántico: **Major** = cambia el contrato del harness o rompe novelas existentes · **Minor** = capacidad nueva compatible · **Patch** = arreglo o ajuste de redacción.
- Dentro, `### Major Changes` / `### Minor Changes` / `### Patch Changes`.
- Cada entrada: una línea con el **resumen en negrita** y, debajo, viñetas anidadas con el detalle y el motivo. Si hay commit, se cita al principio entre corchetes.
- Las decisiones descartadas también se anotan: saber qué *no* se hizo y por qué evita volver a proponerlo.

---

## 0.5.0

### Major Changes

- **Solo el harness escribe en disco; los agentes devuelven su salida en el mensaje final.**

  - `specs/functional.md` §1.2, §3.1, §5 y §6.1. Los subagentes del hito 1 se definen con `tools: Read, Glob, Grep`, sin herramientas de escritura. El harness valida la forma de cada salida y la escribe en su ruta.
  - Motivo: es lo que §10.2 ya preveía para el runner. Hacerlo igual en los dos hitos deja los contratos de los agentes idénticos y elimina `verificar-zona.md`, la pieza con el bug más grave de la 0.4.0 (borraba el capítulo antes de revisarlo). La zona de escritura queda garantizada por construcción y desaparece el motivo de parada `ESCRITURA_FUERA_DE_ZONA`.
  - Descartado: `permissions.deny` con patrones de ruta. Se aplica a toda la sesión, no por subagente, y bloquearía también al interrogador cuando escribe la biblia.

- **Cuarto agente: `resumidor`. El escritor ya no escribe el resumen.**

  - El resumidor recibe **solo** el texto del capítulo y el libro de estado vigente, y devuelve el resumen y el libro de estado actualizado. No ve la escaleta ni la biblia, para que registre lo que hay en la página y no lo que debía haber.
  - Motivo: en la ejecución 0.4.0 el resumen del capítulo 1 afirmaba un hecho que el texto no mostraba. A 200 capítulos los resúmenes son la memoria del sistema; el escritor es parte interesada.

- **Libro de estado (`libro-estado.md`) como memoria de tamaño constante.** §3, §7.6.

  - Personajes (dónde, qué saben, estado), hilos abiertos con capítulo de origen y cierre previsto, hilos cerrados, objetos/lugares/datos, reglas en vigor. El resumidor propone la versión nueva en cada intento (`libro-estado-K.md`); el harness la adopta solo al aprobar. Escritor y revisor lo reciben siempre.
  - Sustituye a `memoria.digesto_por_acto`, que nunca se implementó y no resolvía el problema: una ventana de resúmenes pierde estado, no solo texto. `memoria.libro_estado_max_palabras` (4000) acota su tamaño.

- **Escaleta en dos niveles: alto nivel (arcos) + escaleta de cada arco generada al llegar a él.** §4.1, §4.2.

  - `formato.capitulos_por_arco` (15). Con total ≤ 15 hay un solo arco y el comportamiento es el de antes. La escaleta de alto nivel es lo que aprueba el usuario y lo inmutable; la de cada arco la valida el harness sin intervención humana, con el libro de estado y el informe del arco anterior como entrada.
  - Motivo: ningún modelo produce 200 entradas de capítulo coherentes de una vez, y el arco 9 debe conocer lo que realmente pasó en los arcos 1–8. `saga` es una sola novela con una sola trama, no una serie.

- **La longitud la comprueba el harness, no el revisor.** §4.2, §5.4.

  - `wc -w` antes de invocar a nadie más. Si se sale de la tolerancia, el harness genera el informe (gravedad 3) y consume el intento sin llamar al resumidor ni al revisor. El criterio 3 desaparece del contrato del revisor; la numeración se conserva.
  - Motivo: los modelos no saben contar palabras, y el revisor de la 0.4.0 tenía la instrucción "cuenta tú las palabras". El criterio de aceptación 3 (tolerancia 0) pasa a ser determinista.

- **Vocabulario: `hito` para las fases del proyecto, `etapa` para las del flujo.** La palabra "fase" desaparece de la spec: significaba dos cosas distintas en el mismo documento.

### Minor Changes

- **Revisión por arco y revisión global acotada.** Al cerrar cada arco, el revisor emite `arcos/informe-arco-AA.md`, que alimenta la escaleta del arco siguiente. La pasada global sobre el manuscrito completo solo se hace si no supera `limites.revision_global_max_palabras` (60000); por encima, se hace sobre biblia, escaleta, libro de estado, resúmenes e informes de arco. Motivo: 200 × 2500 palabras no caben en ningún contexto.
- **El revisor devuelve JSON, no YAML**, con exactamente tres claves; el harness lo valida y cualquier otra cosa es incumplimiento de contrato. En el hito 2 se valida con esquema y se pide salida estructurada donde el modelo lo admita. Motivo: los modelos baratos rompen el YAML con más facilidad.
- **Aceptación por agotamiento elige el mejor intento, no el último**: menos problemas de gravedad 1–2, luego menos problemas en total, luego el más reciente. Un rechazo por longitud nunca gana frente a uno que pasó al revisor.
- **Métricas de calidad (§8.3) y umbrales `calidad.*` (§7.7)**: graves por 10 capítulos, % por agotamiento, hilos previstos sin cerrar, % aprobados en el primer intento, % rechazos por voz, desviación de longitud. El informe de cierre dice CUMPLE / NO CUMPLE por métrica. Es la traducción medible de "coherente, cohesionada y fiel a lo pedido", que es la definición del usuario de "suficientemente buena" para decidir si el modelo barato aguanta.
- **Caso de referencia fijo en `pruebas/referencia/`** (idea + entrevista + respuestas). Todas las comparaciones de §7.8 usan esa entrada. Motivo: sin entrada fija, comparar dos configuraciones es comparar dos historias distintas. `pruebas/respuestas-prueba.md` pasa a `pruebas/referencia/respuestas.md`.
- **`config.json` versión 3**: `proveedor` (`claude-code` | `openrouter`), `modelos.resumidor`, `modelos.temperatura.*` (hito 2), `modelos.escalado.revision_arco_y_global`, `formato.capitulos_por_arco`, `limites.revision_global_max_palabras`, `limites.presupuesto_usd_max` (hito 2), `memoria.libro_estado_max_palabras`, bloque `calidad`. Se elimina `memoria.digesto_por_acto`. `relato` pasa a 5 capítulos (3–8): la 0.4.0 se validó con capítulos de 350 palabras, así que el perfil a 1500 palabras aún no está validado.
- **§9.1: el orquestador se escribe como pseudocódigo con nombres de función estables** (`crear_novela`, `detallar_arco`, `escribir_capitulo`, `comprobar_longitud`, `resumir`, `revisar`, `decidir`, `cerrar_capitulo`, `revisar_arco`, `invocar`, `elegir_modelo`…). Motivo: el runner del hito 2 lo escribirá Claude Code a partir de SKILL.md; así el porte es traducción, no interpretación.
- **Volumen (§6.6)**: el registro lleva `pal_*`, `tok_*` y `coste_usd`; se rellena lo disponible en cada hito. En el hito 2 OpenRouter devuelve coste real y `presupuesto_usd_max` es un límite efectivo.

### Patch Changes

- **Glosario en `specs/functional.md` §0**: qué es y para qué sirve cada término del proyecto (harness, agente, hito, etapa, biblia, escaleta de alto nivel y de arco, arco, acto, hilo, gancho, intento, resumen, libro de estado, informe, veredicto, gravedad, aceptación por agotamiento, parada limpia…). Motivo: el usuario pidió un sitio único donde se defina el vocabulario antes de reconstruir la implementación.

- **Reconstruida la implementación completa sobre la spec 0.5.0.** `SKILL.md` como pseudocódigo con las funciones de §9.1; procedimientos `interrogatorio`, `arco`, `capitulo`, `final`, `invocar`, `cierre`, `comparar`; plantillas (nuevas: `arco.md`, `libro-estado.md`; `estado.json` y `registro.md` pasan a versión 3 con arcos, resumidor y columnas `tok_*`/`coste_usd`); `specs/inventario.md`; `comparativa/`. Nuevo subcomando `/novela verificar <carpeta>`: inventario §4 + métricas, solo lectura. `intento-K.md` ya no lleva frontmatter: es título y texto, y `wc -w` se aplica directo.

- **El modo de prueba toma `idea.md` y `entrevista.md` de una carpeta** (`modo-prueba: pruebas/referencia`) en vez de emparejar palabras clave con una tabla de respuestas. Nuevo flag `entrevista: <ruta>` para la ejecución de referencia con confirmación manual. Motivo: es exactamente el mecanismo con el que el runner recibe la entrevista, así que el hito 1 lo prueba gratis; y el caso de referencia queda escrito una vez, no reconstruido en cada ejecución. `pruebas/referencia/respuestas.md` se elimina; su contenido pasa a `entrevista.md`.

- **Reconstruidos `CLAUDE.md`, `README.md`, `.claude/settings.json` y los cuatro agentes.** `CLAUDE.md` queda en seis reglas y un puntero a la spec. `settings.json` lleva la lista de permisos (lectura, escritura en `novelas/` y `comparativa/`, `git` acotado a `novelas/`, `wc`, `mkdir`, `cp`) para que el bucle corra sin confirmaciones, y deniega `git push`, `--amend`, `reset --hard` y `rebase`. Los agentes llevan `tools: Read, Glob, Grep`, `maxTurns: 40` y no llevan `memory`. La forma de los bloques de salida (`=== ARCHIVO: ruta ===` … `=== FIN ===`) queda fijada en la spec §5.

- **Hook `PreToolUse` que bloquea `Edit` sobre artefactos inmutables** (`biblia.md`, `escaleta.md`, `arco-*.md`, `intento-*.md`, `libro-estado.md`, `manuscrito.md`). Una línea de shell en `.claude/settings.json`, sin `jq`. Es la única excepción a "sin código en el hito 1" y se anota como tal en la spec §1.3 y §3.1. Motivo: el harness nunca necesita `Edit` sobre esos ficheros (los crea con `Write`), así que cualquier `Edit` es un error del orquestador y se puede cortar en seco sin conocer el estado. No protege contra una sobreescritura completa; eso lo detecta el criterio 6 con git. En el hito 2 la inmutabilidad es código.

- Descartado: `permissions.deny` con patrones de ruta para lo mismo. Las reglas `Edit(...)` de permisos se aplican también a `Write`, así que bloquearían la creación legítima del fichero.

- **`harness.config.json` pasa a llamarse `config.json`** en la raíz. La copia congelada por novela sigue siendo `novelas/<slug>/config.json`.
- **`limites.turnos_por_invocacion` es realmente aplicable**: `maxTurns` en el frontmatter del subagente (Claude Code ≥ 2.1.246). Como es estático, el harness comprueba al arrancar que coincide con `config.json` y para con `ERROR_CONFIGURACION` si no. Un resultado marcado como parcial se trata como incumplimiento de contrato. Verificado contra la documentación: la herramienta `Agent` no devuelve tokens en el resultado.
- **Criterios de aceptación nuevos** (§8.2): 10, salida mal formada del revisor; 11, arcos con `capitulos_por_arco: 2`. El 6 pasa de "permisos" a "inmutabilidad".
- **Reconstrucción**: la implementación 0.4.0 (skill, agentes, plantillas, procedimientos, inventario, comparativa) se retira del árbol de trabajo y se reconstruye sobre esta spec. Sigue en el historial de git como referencia. Se quita la referencia al `.drawio` archivado.

---

## 0.4.0

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
