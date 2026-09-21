# CHANGELOG.md

Historial de cambios del harness.

**Quién lee esto: Claude Code, en una sesión futura, antes de tocar el harness.** Sirve para dos cosas concretas, y solo para esas dos:

1. **No volver a proponer algo ya descartado.**
2. **No romper una decisión sin saber que lo es.**

Todo lo que no sirva a una de esas dos cosas, sobra. Escribe para que se entienda de una lectura y sin abrir otro fichero, no para que quede bien.

**Cómo se escribe una entrada:**

- Una sección `## <versión>`, **de la más reciente a la más antigua**. **Major** = cambia el contrato del harness o rompe novelas existentes · **Minor** = capacidad nueva compatible · **Patch** = arreglo o ajuste. Dentro, `### Major Changes` / `### Minor Changes` / `### Patch Changes`.
- Cada entrada: **resumen en negrita en una línea** —qué cambió, no qué se hizo—, entre paréntesis dónde vive ahora (spec §, fichero), y debajo **de una a cuatro viñetas**. Una idea por viñeta. Si necesitas más de cuatro, la decisión son dos decisiones: pártela.
- **Un motivo por decisión, con el dato que lo sostiene.** Un dato, no la serie entera: «el resumen pesaba más que el capítulo que resumía» basta; las proyecciones a 5, 12, 30 y 200 capítulos van en la spec.
- **Lo que está en otro fichero se enlaza, no se copia.** La spec es la fuente de verdad de *cómo funciona*; aquí solo va *por qué es así*. Si una entrada explica el mecanismo, está duplicando la spec.
- **Descartes: solo los que alguien volvería a proponer**, en una viñeta, con la razón por la que no valen. Si dos descartes comparten motivo, van juntos. Descartar por escrito una opción que nadie iba a defender es ruido.
- Cuando una versión posterior invalida una regla, se anota en una línea en la versión vieja en vez de dejar dos secciones contradiciéndose.

**Lo que no entra aquí:**

- **Trabajo pendiente.** Va en [TODO.md](TODO.md).
- **Erratas, desincronizaciones entre dos ficheros y ajustes que no protegen ninguna decisión.** Lo cuenta mejor `git log`.
- **Constancia de que se siguió una regla del proyecto**: glosario actualizado, criterios de aceptación añadidos, inventarios de ficheros tocados.
- **Detalle de verificación**: cuántos casos se probaron y cuáles. Lo demuestra el propio fichero de pruebas.
- **Cómo funciona algo.** Eso es la spec.

---

## 0.12.1

### Patch Changes

- **El orquestador lee con `Read`/`Grep`/`Glob` y reserva `Bash` para los literales del `allow`.** (spec technical §9.4; `SKILL.md` §1.3 y §9)

  - Primera ejecución real desde el estudio: dos comandos del propio orquestador —un bucle `for` sobre los cinco `.claude/agents/*.md` y un `cat … | sed -n`— se denegaron solos, porque `--permission-prompts none` no tiene a quién preguntar.
  - No es un agujero del `allow`: un bucle o una expansión `$var` piden aprobación **aunque cada parte esté permitida**, así que ningún prefijo los cubre. Ensanchar la lista no lo arregla y afloja la línea que `frontend/CLAUDE.md` regla 4 sostiene.
  - Descartado lanzar el estudio con `--permission-prompts accept` o equivalente: sería `bypassPermissions` por la puerta de atrás, y el hook de inmutabilidad no cubre `Bash`.
  - No rompía la ejecución —el harness siguió por `Read` y creó la novela— pero dejaba en la web un aviso técnico que el usuario no puede accionar.

---

## 0.12.0

### Minor Changes

- **Todo commit pasa por `commitear()`, que comprueba que el commit se creó y que la carpeta quedó limpia; si no, PARADA `COMMIT_NO_LIMPIO`.** (spec §3.1, §6.5, §8.2 criterio 19; `procedimientos/invocar.md`, `capitulo.md`, `arco.md`, `interrogatorio.md`, `cierre.md`, SKILL.md §9)

  - El commit era el único punto de retorno de una novela y estaba en el nivel más débil de la spec: prosa que el orquestador tiene que acordarse de ejecutar (`harness`, «puede olvidarse»). Nada comprobaba que hubiera ocurrido.
  - El fallo encadenaba mal: capítulo cerrado sin commitear → la reanudación ve `git status` sucio → `descartar()` borra un capítulo aprobado. La red de seguridad era la trituradora.
  - Para en vez de reintentar porque el paso siguiente daría por guardado algo que no lo está. Única excepción: llamado desde `cerrar()` no para, se anota como aviso; una PARADA en el cierre se llamaría a sí misma.

- **`descartar()` copia a `novelas/<slug>/.descartado/<marca UTC>/` antes de borrar; si no puede copiar, no borra (`DESCARTE_NO_SEGURO`).** (spec §6.2, §6.5, §8.2 criterio 20; `procedimientos/invocar.md`, `.gitignore`) — cierra **A21**

  - Ya había pasado: un `paso_descartado` al reanudar se llevó un `intento-1.md` de 1.333 palabras (E2). `git clean -fdq` no deja de dónde tirar.
  - Quien protege la copia es el `.gitignore` (`git clean -fdq` no borra ignorados); el `-e .descartado` del `clean` es un segundo cinturón por si alguien quita esa línea o añade `-x`.
  - `.descartado/` va al `.gitignore`. Si se versionara, el paso 6 de §8.7 y la aserción de `commitear()` verían la carpeta sucia para siempre: las dos piezas solo encajan así.
  - El harness nunca lee de ahí ni lo reutiliza: no es caché ni punto de retorno, es material para que decida una persona. Borrarlo no cambia ninguna novela.

- **Descartado: reintentar el commit, y hacer que `descartar()` haga `stash` en vez de copiar.** Reintentar no arregla la causa (un commit que no cierra suele ser un índice bloqueado o un hook fallando) y deja avanzar sobre un punto de retorno inexistente. `git stash` mete lo descartado en el historial de git, donde el usuario no lo va a buscar y donde ensucia `git log` de la novela; una carpeta que se ve con `ls` es lo que hace que alguien la rescate.
---

## 0.11.1

### Patch Changes

- **El agotamiento de cuota de la suscripción es un motivo de parada propio, `LIMITE_DE_USO`, y no un fallo técnico.** (spec §6.3 y §6.5; `procedimientos/invocar.md`, `cierre.md`)

  - El harness corre sobre una suscripción de Claude Code, sin API key: lo que se acaba a mitad del bucle no es dinero, es cuota. Tratarlo como fallo técnico gastaría los tres `reintentos_tecnicos` en llamadas que el proveedor va a rechazar igual, y cerraría con un motivo que dice mentira («persistente») sobre algo que se arregla solo con esperar.
  - Por eso no consume reintentos: descarta el paso a medias como una interrupción y cierra con la hora de reinicio si el error la trae. La reanudación es la de §6.2, sin nada especial.
  - `limites.presupuesto_usd_max` queda declarado inerte mientras el proveedor sea la suscripción: sin coste por llamada no hay nada que sumar. Se mantiene porque es el contrato del runner del hito 2.

- **`relato` pasa de 5 · 3–8 capítulos a 3 · 1–5, y se declara que deja de ser comparable con la línea base.** (spec §3.2, §7.1, §7.7)

  - El motivo es el uso real del perfil: probar el harness entero lo más barato posible, no leer una historia.
  - La consecuencia hay que escribirla porque si no se olvida: E1 se midió a 5 capítulos y los umbrales de `calidad.*` están calibrados sobre eso. A 3 capítulos un solo grave son 3,3 por 10 (umbral 2) y un capítulo por agotamiento es el 33 % (umbral 20), o sea que un fallo suspende. Para comparar contra la base se sobreescribe el tamaño en el comando, no en el fichero.
  - Descartado: **bajar los umbrales de `calidad.*` para que el perfil pequeño salga verde.** Los umbrales miden el harness contra una referencia; moverlos para acomodar el tamaño de la prueba destruye lo único que hacían.

## 0.11.0

### Major Changes

- **Se retira `/novela comparar` y con él la carpeta `comparativa/`.** (spec §8.4 ahora dice solo que está retirada; `procedimientos/comparar.md` y el permiso `Edit(/comparativa/**)` fuera)

  - El motivo: su único caso real, `caso-01-opus-vs-haiku`, **no aislaba lo que decía medir**. Entre A y B cambiaron el modelo, la revisión partida, los ajustes de longitud y los umbrales a la vez (E4), así que el veredicto no era atribuible a nada concreto. Un comparador cuya precondición de justicia no se cumple ni una vez no es un instrumento.
  - Lo que hacía lo hacen ya dos cosas que sí tienen número reproducible: §8.3 mide el proceso y §9.6 mide el producto contra línea base congelada. El bloque de lectura con cita obligatoria, que era lo valioso, vive en el informe de §9.6.
  - La evidencia no se pierde: E4 se queda en [technical.md](specs/technical.md#e4) y es el origen de A6, A7 y A19. Retirar la herramienta no retira lo que enseñó.
  - Descartado: **conservar el comando y la plantilla sin casos**. Un procedimiento que nadie puede ejecutar correctamente —hacen falta dos novelas de la misma `config.version` y `config.calidad`, que el repositorio nunca ha tenido— se degrada en spec muerta que alguien vuelve a citar como si funcionara.

## 0.10.0

Versión del 18/09/2026: el harness gana una forma de medirse **por fuera**. Entra un validador que puntúa el texto producido con reglas deterministas y verdad de campo etiquetada a mano, y las métricas de §8.3 quedan reclasificadas por lo que son. Ejecutado: hay línea base congelada y una primera comparación.

### Minor Changes

- **Las métricas de calidad se parten en dos: proceso y producto, y las viejas quedan declaradas como autoinformadas.** (spec §8.3, §9.6; `herramientas/validacion/`, `.claude/skills/validar/`)

  - El dato que lo obliga: `erratas.md` de la novela B dice `total: 0` sobre el manuscrito donde E5 contó **13 agramaticalidades a mano**, y §8.3 le da `6/6 CUMPLE`. No fallaron por poco: no vieron ninguna, porque cuatro de esas seis métricas cuentan lo que los revisores declararon.
  - §8.3 no se retira: ve cosas que el texto no muestra (agotamientos, reintentos). Pasa a llamarse **proceso** y §9.6 aporta **producto**. Cuando discrepen, cada informe dice de dónde sale su número.
  - El validador **no es un bucle** y §9.6 lo declara así en vez de rellenar STOP y MEMORY por inercia: mide una vez y devuelve un número. Bloques de adorno que nadie respeta son peores que un hueco explicado.
  - Descartado: **un agente validador LLM**, que era la petición literal. Un modelo puntuando da números distintos sobre el mismo texto, y eso es incompatible con la línea base congelada que el propio diseño necesita. El juez LLM entra cuando exista un modelo independiente (hoy solo `openrouter/free`, que no garantiza cuál contesta → A14).

- **La verdad de campo de lengua entra en el repositorio, y con ella el alcance real del detector.** (spec §9.6.6; `herramientas/validacion/etiquetado/`, `calibracion.md`)

  - Cierra **A24**: la lista itemizada de los defectos de E5 no estaba en ningún sitio. Ahora están los 13 de la novela B con su cita literal verificada, y los 0 de la novela A.
  - El detector v1 mide **precisión 1,000 y recall 0,462**. El recall no es un fallo: 7 de los 13 defectos exigen un léxico o análisis morfosintáctico, y están marcados uno a uno con `detectable_v1: false`. Sobre lo que la v1 puede expresar, el recall es 1,000.
  - Descartado: **spaCy y language-tool-python**. Subirían el recall de verdad, pero atan la línea base a una versión externa: al actualizarse cambian los números y las comparaciones viejas dejan de valer. Hoy el proyecto tiene una sola dependencia Python (`langfuse`) y esto la habría multiplicado por un servidor Java o un modelo de cientos de MB.

- **El detector no puede escribirse contra los casos que va a puntuar.** (spec §9.6.5; `comprobar_patrones.py`)

  - Un patrón escrito contra la frase concreta encuentra justo lo que se escribió para encontrar. Es el mismo lazo de E5(c) con otra cara, y se corta en código, no en prosa: ningún patrón puede llevar dentro **tres palabras seguidas** de una cita del etiquetado, y cada clase viaja con ejemplos positivos y negativos inventados que debe casar y respetar.
  - La puerta se ganó el sueldo en la primera ejecución: rechazó cuatro comprobaciones, y una de ellas era un defecto de la propia regla —medida en caracteres, rechazaba la palabra «conocimiento», que es léxico común y no una instancia—. La regla pasó a medirse en palabras.
  - Umbral de tres palabras y no dos: `la agua` es la forma canónica de su clase de error, no la copia de un caso.

### Patch Changes

- **Primera medición, con su reserva.** (spec §9.6.7)

  - A (opus) **0,934**, B (haiku) **0,569**, delta **−0,365**. Con `n=1` por configuración no se puede separar el efecto del modelo del azar de esa generación, así que el informe lo escribe siempre y no se declara ninguna mejora establecida.
  - Lo que ninguna métrica anterior daba: **la novela de opus pierde en repetición** (8,10 frente a 2,82 6-gramas compartidos por mil palabras). Sus capítulos 3 y 4 comparten muchas secuencias literales, y §8.3 le da CUMPLE sin verlo.

---
## 0.9.0

Versión de **diseño**, del 18/09/2026: se diseña el bucle de optimización de prompts que §9.3.1 dejaba anunciado y sin diseñar. Nada ejecutado todavía: faltan prerrequisitos y la spec los declara como condición de arranque. No toca el harness de la novela.

### Minor Changes

- **El sistema deja de poder corregirse a sí mismo los exámenes: quien propone un prompt ya no puede puntuarlo.** (spec §9.5; `.claude/skills/optimizar/`, `.claude/agents/optimizador.md`, `herramientas/optimizacion/`)

  - El dato que lo obliga: `6/6 CUMPLE` sobre un manuscrito con 30 defectos verificados a mano (E5c). Las métricas de §8.3 cuentan lo que los revisores declaran, y nadie mide a los revisores.
  - Tres papeles separados por construcción: el **optimizado** solo se ejecuta, el **juez** es un evaluador de código contra un conjunto etiquetado, el **optimizador** propone y nunca puntúa. Que el optimizador no vea el conjunto no queda en prosa: un `deny` de `Read` sobre la carpeta del conjunto lo corta, y con él `cat` y las redirecciones de Bash.
  - El bucle es **manual, offline y fuera del harness**, como el visor y la observabilidad: decide qué prompt usará un agente la próxima vez, no si un capítulo se aprueba. Las seis reglas de §9.3 quedan intactas; no hubo que cambiar ninguna.
  - Descartado: **servir el prompt de producción desde Langfuse Prompt Management**, que era la petición inicial. Convierte a Langfuse en fuente de verdad (regla 1) y en puerta del flujo (regla 2), deja el harness sin arrancar cuando no hay red (regla 3) y rompe §10.1, que porta los contratos byte a byte desde `.claude/agents/`. Langfuse archiva candidatos e historial; git manda. Además hoy es inejecutable: la herramienta `Agent` lee el contrato del disco y no admite un prompt inyectado.

- **La puntuación de un agente se filtra por su contrato, no por el conjunto entero.** (spec §9.5.1; `herramientas/optimizacion/puntuar.py`)

  - Cada revisor solo emite sus gravedades (§5.6), así que medir a `revisor-encargo` contra los 30 defectos de E5 le imputa 29 que no puede ver: los puntuables para él son **1 de 30** (A7, título huérfano). Un objetivo de 0,80 sobre ese denominador es inalcanzable por aritmética, no por calidad del prompt.
  - El conjunto guarda los treinta con su clase y su gravedad dueña; el evaluador cuenta solo los del contrato del agente optimizado. Así el mismo conjunto sirve para los cinco agentes.
  - Consecuencia inmediata y buscada: con el conjunto de E5, `/optimizar revisor-encargo` **no arranca** y dice que faltan 29 ítems puntuables. Gastar 300 invocaciones para confirmar aritmética no es una ejecución, es una factura.
  - Descartado: **dejar que el optimizador añada criterios nuevos** (clases B–E de E5, que no tienen dueño en ningún contrato). Sube el techo de verdad, pero convierte el bucle en editor de contratos y ya no corre desatendido. Un criterio nuevo es un cambio de §5.4, y eso se decide en la spec, no en una vuelta del bucle.

- **El presupuesto del bucle se cuenta en invocaciones y no en dinero.** (spec §9.5.1)

  - En el hito 1 la herramienta `Agent` no devuelve tokens de subagente (§9.3), así que un tope en dólares no es comprobable: sería una cifra que nadie puede contrastar. En el hito 2 la cáscara devuelve `coste_usd` (§10.2) y el tope pasa a ser de coste.
  - Por lo mismo, las restricciones del objetivo miden **palabras** (`wc -w`) y no tokens: el harness no tiene tokenizador, y una aproximación declarada vale más que una cifra inventada.

### Patch Changes

- **La tabla de marcas gana `guion`.** (spec §«Cómo leer las marcas»)

  - Faltaba el caso de una regla impuesta por código determinista fuera del bucle: no es `hook` (no corta la acción antes de ocurrir), no es `cáscara` y no es `harness` (no puede olvidarse como la prosa, E3), pero solo actúa si alguien lo llama. §9.5 lo usa en las comprobaciones que impiden que el optimizador memorice el examen.

**Lo que esta versión no decide.** El conjunto etiquetado no existe todavía (A24 seguía abierta) y lo escribe el usuario; hasta entonces el bucle está montado y sin ejecutar, que es como se pidió. La contaminación del split de control —se consulta en todas las vueltas, hasta 10 decisiones sobre los mismos 10 casos— queda como **limitación conocida y declarada en cada informe de cierre**, no como error: se prefirió ver la curva completa a proteger el control, y el informe dice cuántas consultas se gastaron para que la cifra final se lea con esa reserva.

---
