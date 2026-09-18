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
