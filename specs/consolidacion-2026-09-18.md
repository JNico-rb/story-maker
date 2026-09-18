# Consolidación de la spec — 2026-09-18

Fichero **de transición**: acompaña a la spec 1.0.0 y se borra cuando las preguntas de §3 estén decididas y sus respuestas hayan pasado al CHANGELOG y a [functional.md](functional.md). Contiene lo que la spec no debe cargar: el mapa desde los documentos viejos, lo que está sin decidir, lo que se propone tirar y los descartes del CHANGELOG antiguo que siguen vigentes.

Nada de aquí es normativo. Cada cifra sale de contar o de leer; lo que no se tiene es `desconocido`.

---

## 1. Qué se ha hecho

| Fichero | Estado | Líneas antes → después |
|---|---|---|
| `specs/functional.md` | Reescrito. Normativo, numeración §0–§10 estable, frontmatter `spec_version: 1.0.0`, marcas de enforcement y portabilidad por regla, marcas `→ A-n`, §10 rediseñado como cáscara | 1.021 (copia de trabajo) → 804 |
| `specs/hallazgos.md` | Nuevo. Evidencia E1–E7 | — → 194 |
| `specs/inventario.md` | Stub de punteros (absorbido en §3, §3.2, §1.3, §8.7, §8.3) | 113 → 11 |
| `specs/consolidacion-2026-09-18.md` | Este fichero | — → 285 |
| `specs/revision-harness-2026-09-17.md` | **Sin tocar.** Absorbido; propuesto para borrar (§4) | 333 |
| `specs/analisis-traza-2026-09-17.md` | **Sin tocar.** Absorbido en E3, E6; propuesto para borrar o mover (§4) | 258 |
| `herramientas/trazas/analisis-traza-2026-09-16.md` | Ya borrado en la copia de trabajo; leído de HEAD y absorbido en E1, E6 | 170 en HEAD |

No se ha tocado ningún fichero del harness, ni `CHANGELOG.md`, `TODO.md`, `CLAUDE.md` ni `README.md`.

**Decisiones tomadas en la sesión** (entran como regla en la 1.0.0 y necesitan entrada en el CHANGELOG nuevo, §7):

1. Hito 1 = orquestador Opus en Claude Code, agentes Haiku. Hito 2 = **orquestador LLM barato vía OpenRouter dentro de una cáscara** que espeja Claude Code. Revierte el runner en código de la 0.4.0.
2. La cáscara da `Read/Write/Edit/Bash/Agent` al orquestador; los agentes conservan `Read/Glob/Grep` con bucle de turnos. SKILL.md, procedimientos, plantillas y agentes se portan byte a byte.
3. La cáscara lee permisos y hooks de `.claude/settings.json` y ejecuta `inmutables.sh`.
4. Protocolo de sesión = subconjunto de `stream-json` que hoy consume `harness.mjs`. Entrevista interactiva en los dos hitos.
5. `pausa_cada_capitulos` se queda en los dos hitos.
6. Dos ficheros normativo/evidencia; `inventario.md` absorbido con stub.
7. `spec_version: 1.0.0`; el CHANGELOG nuevo arranca ahí. `config.version` sigue en 4 (A1).
8. Rechazadas las propuestas de la revisión §3.1 de quitar `/novela comparar` y `Edit(/novelas/**)` (§4).

---

## 2. Mapa de trazabilidad

### 2.1 `functional.md` 0.8.1 (copia de trabajo, 1.021 líneas) → 1.0.0

| Vieja | Nueva | Qué cambió |
|---|---|---|
| Cabecera (hitos, vocabulario) | Cabecera + «Cómo leer las marcas» | Hito 1 y 2 redefinidos según la decisión 1; leyenda de marcas nueva |
| §0.1 proyecto | §0.1 | + Cáscara, Protocolo de sesión, Evaluador, Evidencia. «Runner» pasa a ser nombre antiguo de Cáscara. Motivaciones recortadas a una línea o a `E-n` |
| §0.2 artefactos | §0.2 | Filas fusionadas (Entrada/Gancho/Hilo; Capítulo/Intento/Reescritura; Estado/Registro/Cierre) |
| §1.1–1.3 | §1.1–1.3 | Ejecución: hito 2 = cáscara + LLM. Control determinista con su limitación declarada. «Lo que no genera» de inventario §3 absorbido en 1.3 |
| §2 | §2 | Harness redefinido; motivaciones a E1 |
| §3 tabla | §3 tabla | Fusionada con inventario §1: columnas Cuántos y DdH; fila Commits |
| §3.1 | §3.1 | Misma regla, con marcas; añadida la regla de permisos (`Edit(ruta)` cubre `Write`) |
| — | §3.2 | Inventario §2 (texto por perfil) |
| §4 diagrama | §4 diagrama | Recortado en etiquetas |
| §4.1 | §4.1 | Motivaciones a E1; `grilling` marcado CC → A17; ESPERA_APROBACION integrada |
| §4.2 | §4.2 | Motivaciones a E1/E2; hoja, tope del resumen y veredicto 1/2 marcados `pendiente`; punteros A8–A12 |
| §4.3 | §4.3 | Igual; pulido → A28; recuento → A10 |
| §5 común, 5.1–5.5 | §5 | + tabla «Fallo visto» por agente (revisión §6.3.2); tolerancia → A8 |
| §5.6 | §5.6 | Regla de veredicto marcada `pendiente`; `cita` y frontera → A4 |
| §6.1–6.5 | §6.1–6.5 | Comprimidas; tabla de motivos amplía ESPERA_APROBACION, PAUSA, ESTADO_NO_RECONOCIDO |
| §6.6 | §6.6 | Hito 2: la cáscara devuelve tokens/coste en `Agent` |
| §7 y 7.1–7.7 | §7.1–7.7 | Claves `pendiente` marcadas; `modelos.orquestador` nueva (hito 2); limitación de §7.7 declarada |
| §7.8 | §7.8 | Paso 2 «Ejecutado, no decidido» (E4); paso 3 = cáscara |
| §8.1–8.2 | §8.1–8.2 | Criterios comprimidos + estado real (ninguno automatizado) |
| §8.3 | §8.3 | + regla vacía → A6; señales de inventario §5 |
| §8.4 | §8.4 | Puntero a comparativa/README; precondiciones → A7 |
| §8.5 | §8.5 (stub) | → hallazgos E1 |
| §8.6 | §8.6 (stub) | → hallazgos E2 |
| — | §8.7 | Inventario §4 (completitud) |
| §9 tabla, 9.1 | §9, 9.1 | Tabla comprimida; 9.1 ya no promete traducción a código |
| §9.2 | §9.2 | Comprimido |
| §9.3 | §9.3 | + estado del exportador (análisis 09-17 §4) y **9.3.1 Evaluadores** (nuevo) |
| §9.4 | §9.4 | Comprimido; flags reales de `harness.mjs`; protocolo → §10.3 |
| §10.1–10.3 | §10.1–10.4 | **Rediseñado**: qué se porta byte a byte, qué implementa la cáscara, protocolo de sesión, contrato |

### 2.2 Otros documentos → dónde están ahora

| Fuente | Sección | Destino |
|---|---|---|
| `inventario.md` | §1 · §2 · §3 · §4 · §5 | functional §3 · §3.2 · §1.3 · §8.7 · §8.3 |
| `revision-harness-2026-09-17.md` | Resumen ejecutivo, §1 (matriz), §2 | hallazgos **E5**; A4, A5 |
| | §3.1 sobra | §4 de este fichero (dos rechazadas; `paginas_objetivo` → A20; congelar estudio → A18) |
| | §3.2 falta, §3.3 duplicado, §3.4 erratas | A3, A4, A24, A27, A28 |
| | §4.1 lo que aguanta | hallazgos E7 |
| | §4.2 guiones, §4.3 esquemas, §4.4 longitud | A3, A11 |
| | §5 evaluadores | functional §9.3.1; A13, A14, A24 |
| | §6 forma de la spec | Aplicado: normativo/evidencia, marcas por regla, `spec_version`. **No** aplicado: enlazar `spec_version` con `config.version` (A1) |
| | §7 orden de trabajo, §8 lo que no propone | §3 de este fichero, como contexto de cada A |
| `analisis-traza-2026-09-17.md` | §0, §1, §2, §3 | hallazgos **E3**; A8–A11, A19 |
| | §4 herramienta, §5, §6 | hallazgos **E6**; A13 |
| `analisis-traza-2026-09-16.md` (HEAD) | §1, §2, §3, §5, §6 | hallazgos **E1**, **E2**; A21 |
| | §4 herramienta | hallazgos E6 |
| `comparativa/caso-01-opus-vs-haiku/` | `caso.md`, `comparacion.md` | hallazgos **E4**; A5–A7, A10–A12, A19. Los ficheros se quedan donde están: son datos, no spec |
| `CHANGELOG.md` (HEAD, 453 líneas) | Descartes | §5 de este fichero |
| `TODO.md` (copia de trabajo) | Cuatro bloques | A2, A18, A22, A13 |
| `README.md` (copia de trabajo) | Dos hitos | Cabecera de functional |
| `p2.md` | Hitos, evaluadores, portabilidad | Cabecera, §9.3.1, marcas CC |

### 2.3 Lo que se ha dejado fuera a propósito

- **Las motivaciones en línea** de cada regla (párrafos «Motivo, medido…»): sustituidas por `E-n`. Nada se pierde; cambia de sitio.
- **El detalle de la API de Langfuse** (endpoints, parámetros, límites): estaba en la spec §9.3 y en el análisis; la 0.7.3 decidió que eso vive en `herramientas/trazas/README.md`, no en la spec. En functional §9.3 queda una línea; el detalle en E6 y en el README.
- **Las tablas de los criterios de aceptación con su texto completo**: comprimidas a una línea por criterio. El texto largo está en `git show HEAD:specs/functional.md` §8.2.
- **Las propuestas de la revisión que ya son decisiones descartadas** (§4 abajo).
- **El diseño del bucle de auto-optimización de prompts y del uso de los evaluadores**: por petición explícita. La spec deja el hueco en §9.3.1 («circuito previsto, no diseñado») y en A4/A5.
- **Las secciones 9.2 y 9.4 en detalle de código**: viven en `frontend/CLAUDE.md`.

---

## 3. Preguntas abiertas

Cada una con las opciones vistas y una recomendación. Ninguna está decidida. Al decidir, la respuesta va al CHANGELOG y la regla pierde su marca `→ A-n`.

### A. La spec promete lo que la implementación no cumple

**A1 · `config.version`.** La spec exige 4; el arrastre de la 0.8.0 (A2) pedía subirla a 5; «empezar de nuevo» podría sugerir reiniciarla. Opciones: (a) 4 hasta implementar A2, entonces 5; (b) reiniciar a 1 con la spec 1.0.0; (c) atarla a `spec_version`. **Recomendación: (a).** `version` es la versión del **esquema** de configuración y la comprueba el harness; atarla al documento obligaría a tocar el esquema por una frase. (c) es lo que proponía la revisión §6.3.3 y no lo aplico por eso.

**A2 · El arrastre de la 0.8.0** (hoja de continuidad y campos nuevos del resumen, `resumen_max_palabras` con reinvocación única, `rechaza_con_gravedad_1/_2`, `resumenes_completos_ultimos` por perfil, `entrada_max_palabras_invocacion`, `hoja_continuidad_max_palabras`). Todo marcado `pendiente` en la spec; `config.json`, `capitulo.md`, `plantillas/informe.md`, `resumidor.md`, `escritor.md`, `plantillas/resumen.md` y `estado.json` hacen lo anterior y son coherentes entre sí. Opciones: (a) implementar de una vez (TODO actual); (b) que la spec retroceda a lo implementado y la 0.8.0 pase a «propuesta»; (c) implementar solo lo barato (veredicto 1/2, `resumen_max_palabras`) y dejar la hoja para después. **Recomendación: (a), precedido de A3 (`comprobar.sh`)**, que es lo que habría detectado esta deriva el mismo día. Dato: E7.

**A3 · Guiones mecánicos en `herramientas/`** que SKILL.md llame por Bash: `contar` (longitud, JSON ok/rechazo), `verificar-citas` (grep de cada `cita`), `metricas.py` (recuento desde `registro.md` con signo), `comprobar.sh` (claves de config citadas ↔ existentes, frontmatter ↔ config, versiones). Con la decisión de espejo y orquestador barato, el riesgo «lo mecánico lo hace un modelo con cuidado» (E3: tres fallos de contabilidad en cinco capítulos) **se agrava**, y esta es la única mitigación compatible: los guiones se portan tal cual porque leen la carpeta. Roza §1.3 («sin código en el núcleo del hito 1») igual que ya lo roza `inmutables.sh`. Opciones: (a) los cuatro, `comprobar.sh` y `metricas.py` primero; (b) solo `comprobar.sh` (deriva) y `metricas.py` (contabilidad); (c) ninguno, aceptar el riesgo por escrito. **Recomendación: (a).** El TODO viejo ya descartó bien framework de tests, cobertura, CD y pre-commit; esto son cuatro guiones y quince líneas de CI.

**A4 · La matriz de criterios** (E5): 21 de 30 defectos sin dueño. Piezas: (i) `cita` obligatoria en cada problema, verificada con `grep -F` por el harness, con métrica «fracción de citas verificables»; (ii) frontera comprobable problema/observación (problema = cita literal + contrario nombrado); (iii) reglas inviolables como lista de comprobación por capítulo en continuidad, y compatibilidad reglas↔escaleta en `validar_canon`; (iv) agente `corrector` (gravedad 6 lengua, 7 verosimilitud; entrada solo el capítulo + tono y reglas de la biblia); (v) gravedad 8 repetición y presencia del mundo en encargo; (vi) tabla de veredicto nueva (6 rechaza con 3; 7 y 8 con 2). Opciones: (a) todo; (b) i–iii ahora (sin agente nuevo, baratas), iv–vi cuando los evaluadores 3 y 4 (§9.3.1) estén calibrados y su prompt ascienda; (c) esperar todo a los evaluadores. **Recomendación: (b).** i–iii cambian solo prosa del harness y dos contratos; iv es un contrato nuevo que conviene calibrar fuera antes (E5 corolario e). Es la pieza que tu siguiente encargo (auto-optimización + evaluadores) va a mover: no cerrar aquí.

**A5 · Las métricas de calidad miden al revisor** (E4: B 5/5 y peor novela). Opciones: (a) mantenerlas declarando la limitación (hecho en §7.7) y añadir métrica informativa de lengua (errores por mil palabras) cuando exista evaluador; (b) sustituir la columna CUMPLE por el `recall_revisor` externo cuando exista; (c) publicar además en el informe de cierre problemas por revisor y reparto problema/observación (análisis 09-17 §3.1.3). **Recomendación: (a) + (c) ahora**, (b) es el destino y depende de A13/A24.

### B. Contradicciones y duplicaciones

**A6 · «B aguanta si cumple todas las que cumple A» es vacía** cuando A cumple cero (E4). Opciones: (a) si A cumple cero, `b_aguanta` = «no informativo» y decide la lectura; (b) comparar contra umbrales fijos, no contra A. **Recomendación: (a)**, es una línea en `comparar.md` §4 y en §8.3.

**A7 · Precondiciones de `comparar`**: misma `config.version` y mismo bloque `calidad`, y commit del harness anotado en `registro.md › inicio_ejecucion`. Caso-01 tuvo que compararse v3 contra v4 y las cuatro comprobaciones actuales lo dejaron pasar. **Recomendación: adoptar.** Toca `comparativa/README.md`, `comparar.md` §1, plantilla de registro.

**A8 · Tolerancia de formato explícita en `invocar.md`**: aceptar JSON en valla de código y ruido a la derecha del delimitador, registrando `observacion`; reintentar el bloque sin `=== FIN ===` pidiendo solo el cierre; **no** tolerar la salida sin bloques. Hoy es improvisado (E3: tres variantes absorbidas a criterio del turno). **Recomendación: adoptar.** Con modelos baratos es buena parte de los reintentos (7 de 41).

**A9 · Filas `pendiente` en el registro.** `Agent` en Claude Code no expone `run_in_background` y devuelve en segundo plano; cada invocación deja dos filas (13 sobre 50 en B). La plantilla dice «una invocación = una fila» y no es cierto. Opciones: (a) contemplar la fila `pendiente` en la plantilla con referencia a la que la cierra, y que exportador y `calcular_metricas` la fusionen; (b) cambiar la forma de invocar. **Recomendación: (a)** y anotarlo como limitación CC: en la cáscara `Agent` es bloqueante y la fila desaparece (§10.2).

**A10 · Recuento obligatorio desde `registro.md`** al cerrar capítulo y al cerrar ejecución, tratando filas `pendiente` y de corrección, en vez de leer contadores de `estado.json`; y «primero cuentas, después registras» como regla general del registro. E3: una invocación de menos, corrección no propagada, coste publicado un 9 % bajo. **Recomendación: adoptar**, idealmente como `metricas.py` (A3). Incluye publicar `desviacion_longitud` con signo, que la spec 0.8.0 ya exige y `final.md` no hace.

**A11 · Longitud frente al modelo barato.** opus +10,5 % (11/13 arriba); haiku −22,7 % (9/9 abajo). La corrección `objetivo × (1 − sesgo)` está retirada (habría empeorado B). Opciones: (a) tolerancia asimétrica (p. ej. −25 % / +10 %) tras comprobar la hipótesis de que ampliar fabrica relleno (comparar motivos repetidos entre intento corto y ampliado en caps. 1, 2 y 5 de B: cuesta cero invocaciones); (b) aviso asimétrico en el prompt según el modelo; (c) nada hasta una segunda ejecución por modelo. **Recomendación: probar la hipótesis primero (gratis), después (a).** No bajar el objetivo a 1.200: el suelo dejaría de serlo.

**A12 · Dos criterios de contrato a partir de E4**: continuidad no puede degradar a observación un salto temporal no justificado ni un objeto usado sin sembrar; encargo comprueba que el título de la entrada tiene referente en el texto. **Recomendación: adoptar**; son dos líneas en dos prompts con cita de dónde falló. Compatible con A4 (ii).

**A20 · `perfiles.*.paginas_objetivo`**: `null` en los cuatro perfiles, una rama en `resolver_perfil`, un motivo de parada y un párrafo de spec, nunca usado. **Recomendación: quitarlo con A2**, no suelto.

**A21 · `.descartado/<timestamp>/`** en vez de borrar al reanudar con la carpeta sucia (E1: se perdió un intento de 1.333 palabras). **Recomendación: adoptar**, no cambia ninguna garantía.

**A22 · Recalibrar con la segunda ejecución controlada** (A relanzada con spec v4): `pausa_cada_capitulos` (3, a ojo), `min_aprobados_primer_intento_pct` (40, suelo provisional), y si procede A11. **Recomendación: no tocar ninguno antes de esa ejecución.**

**A27 · La inmutabilidad está escrita en cuatro sitios** (spec §3.1, CLAUDE.md, SKILL.md §9, cabecera del hook). **Recomendación:** hogar normativo en §3.1 y punteros en CLAUDE.md y SKILL.md; el hook conserva su comentario. Toca el harness.

**A28 · Pulido de lengua fuera del bucle**: `manuscrito-pulido.md` nuevo, aplicando solo erratas de lengua por sustitución literal verificada con `grep`, sin modelo; lo demás sigue en `erratas.md`. No rompe la inmutabilidad ni el libro de estado. **Recomendación: después del corrector (A4 iv)**, que es quien produce esas erratas.

### C. Modelo barato: lo que la evidencia dice y falta decidir

**A19 · ¿Qué se prueba a continuación?** El paso 2 de §7.8 está ejecutado y no decidido (E4). Opciones: (a) relanzar A con spec v4 y los cinco en opus (comparación limpia); (b) reprocesar el manuscrito de B con los revisores en opus y el resto igual (cero escritura, cero reescrituras: dice si haiku discrimina); (c) escritor barato + revisores caros como configuración candidata. **Recomendación: (b) primero** (es la más barata y contesta la pregunta que bloquea A5, A22 y la calibración del veredicto), después (a). No volver a opus en todo: 21 de 30 defectos tampoco los habría visto (E5).

### D. La cáscara del hito 2

**A15 · Lenguaje y librerías.** Python (ya habla con Langfuse y OpenRouter en el repo; SDK de Langfuse para la instrumentación nativa) o Node/TypeScript (un runtime con el frontend; `harness.mjs` ya parsea el protocolo). **Recomendación: Python**, por reutilizar `exportar.py`/`crear.py` y el SDK; el estudio la lanza como proceso igual que hoy.

**A16 · Modelo del orquestador y alias.** Hace falta `modelos.orquestador` (hito 2) y una tabla de alias `haiku/sonnet/opus → id de OpenRouter` para que `model: haiku` del frontmatter siga cuadrando con `config.json` en `comprobar_entorno`. Opciones de forma: `proveedores.openrouter.alias`, o ids directos en `modelos.*` y el frontmatter comparado vía alias. **Recomendación: tabla de alias en `config.json`** y que `comprobar_entorno` compare tras resolverla. Qué modelo orquesta: `desconocido`; el título del hito dice «barato», E3 dice que barato como orquestador cuesta contabilidad.

**A17 · `grilling` es un plugin de Claude Code.** `interrogatorio.md` paso 3 invoca `mattpocock-skills:grilling`; la cáscara no la tiene. Opciones: (a) copiar el encargo de entrevista como texto propio en `procedimientos/` y que Claude Code lo use también (una sola versión); (b) que la cáscara cargue la skill desde `~/.claude`. **Recomendación: (a)**: es portable y quita una dependencia externa del hito 1.

**A23 · Contexto del orquestador en la cáscara.** Decidido: `pausa_cada_capitulos` se queda. Abierto: si la cáscara compacta o reinicia conversación por capítulo para llegar a 200 sin 66 relanzamientos. **Recomendación: no diseñar hasta medir** cuánto contexto gasta una novela (hoy `desconocido`); la traza de sesión del hito 1 puede darlo.

**A18 · Congelar el estudio** hasta la prueba de punta a punta (TODO) y gastar el ciclo en A4/A19, como pedía la revisión §3.1. **Recomendación: congelar**, salvo el cambio de binario para la cáscara cuando exista.

### E. Observabilidad y evaluadores (fuera del harness)

**A13 · Arreglar el exportador** antes de activar una sola regla: `resultado:?\s*(ok|fallo|incumple|pendiente)`; fusionar filas `pendiente` con su cierre; descartar filas de corrección; `input`/`output` con rutas y, para lo evaluable, **contenido** del capítulo/informe; `start_time`/`end_time` desde `fecha_hora`; `trace_id` derivado del slug; `encoding="utf-8"`. Decisión explícita que exige: **subir el texto de los capítulos a Langfuse** es publicarlo en un servicio externo. **Recomendación: hacerlo todo**, es borrable y no toca el harness; y dejar la decisión de subir texto por escrito en el CHANGELOG.

**A14 · El juez es `openrouter/free`**, que incumple «el juez nunca es el modelo que escribió» y no garantiza cuál toca. **Recomendación:** conexión a `opus` o `sonnet` en Langfuse y cambiar `MODELO_JUEZ` en `crear.py` antes de calibrar.

**A24 · El dataset de 30 defectos no está en el repo.** Solo la clasificación por clases (E5). Sin él no hay `recall_revisor` ni calibración de `lengua_erratas`. **Recomendación:** `pruebas/defectos/ascensores-20260916.md` con clase, cita literal, capítulo y por qué, y subirlo como dataset. Es el activo más valioso de la ejecución B y vive solo en la memoria de quien lo hizo.

---

## 4. Lo que se propone tirar

| Qué | Motivo | Estado |
|---|---|---|
| `specs/revision-harness-2026-09-17.md` | Absorbida: hallazgos E5, E7 y las A de §3. Ella misma decía «después se borra» | Propuesto borrar. No tocado |
| `specs/analisis-traza-2026-09-17.md` | Absorbido en E3, E6. Es el informe de una ejecución, no spec; su sitio natural era `herramientas/trazas/` como el del 09-16 | Propuesto borrar (o mover a `herramientas/trazas/` si quieres conservar el detalle por observación) |
| `herramientas/trazas/analisis-traza-2026-09-16.md` | Ya borrado en la copia de trabajo; su contenido está en E1, E2, E6. El análisis del 09-17 lo citaba como «referencia de contraste»: ese puntero muere con él | Confirmar el borrado |
| `specs/inventario.md` (contenido) | Duplicaba §3 de la spec y §8.2; su §4 es lo que ejecuta `verificar` y ahora es §8.7 | Hecho: stub. Borrar cuando se actualicen SKILL.md §8, `cierre.md` y `plantillas/informe-cierre.md` |
| Texto de §10 «runner en código», §9.1 «el runner conserva los nombres», §10.2 «salida estructurada con esquema donde el modelo lo admita», «el runner solo admite entrevista desde fichero» | Contradicen la decisión 1 y 4 | Hecho en la spec; quedan restos en SKILL.md e `invocar.md` (§6) |
| §7.8 «Paso 2: Siguiente, por ejecutar» | Estaba ejecutado desde el 09-17 (E3, E4) | Hecho |
| Propuesta de la revisión §3.1: **quitar `/novela comparar` y `comparativa/`** por «uso cero» | **Rechazada.** Se usó al día siguiente para caso-01 (commit `cdbbdd6`), que es la fuente con más conclusiones accionables del proyecto (8 cambios propuestos, E4). Su valor no es el comando: es obligar a citar y a no estimar | Decidido 2026-09-18 |
| Propuesta de la revisión §3.1: **quitar `Edit(/novelas/**)` de `settings.json`** | **Rechazada.** El CHANGELOG 0.8.1 verificó con control que en Claude Code solo las reglas `Edit(ruta)` cubren rutas y que cubren también `Write`; quitarla haría que cada escritura del harness pidiera permiso y rompería el lanzamiento del estudio (`--permission-prompts none`). Lo que la revisión temía (`Edit` en sitio sobre aprobados) lo bloquea el hook | Decidido 2026-09-18 |
| Enlazar `spec_version` con `config.version` (revisión §6.3.3) | Mezcla versión de documento y de esquema; hoy ya no coinciden (0.8.1 frente a 4) | → A1, recomendación de no hacerlo |
| `p2.md`, `prompt.md` (untracked en la raíz) | Son los prompts de esta sesión y de la anterior, no documentación del proyecto | Sugerido no commitear |

---

## 5. Descartes heredados del CHANGELOG antiguo que siguen vigentes

El `CHANGELOG.md` de la copia de trabajo está vacío a propósito; el de HEAD (453 líneas, 12 versiones) tiene estos descartes. Los que siguen protegiendo una decisión de la spec 1.0.0 deben reentrar en la primera entrada del CHANGELOG nuevo, o se volverán a proponer. Marcados **vigente**, **superado** o **parcial**.

| Versión | Descarte | Por qué | Estado |
|---|---|---|---|
| 0.8.1 | Que el interrogador devuelva ya `aprobada: true` | Quien aprueba es el usuario, después de ver la propuesta | vigente |
| 0.8.1 | Borrar el fichero antes de reescribirlo | Ventana sin artefacto; una interrupción pierde la propuesta | vigente |
| 0.8.1 | Extender el hook a Bash | Parser nuevo dentro del bucle; limitación conocida, criterio 6 la demuestra | vigente (§3.1) |
| 0.8.0 | Recortar la ventana de resúmenes en vez de acotar el resumen | Tira capítulos enteros para un problema de redundancia | vigente |
| 0.8.0 | Comprimir resúmenes antiguos con otra invocación (digesto) | Pieza de memoria más; con 350 palabras, 200 capítulos caben | vigente |
| 0.8.0 | Decirle al escritor «comprueba las fechas» en el prompt | No bastó con opus; aritmética sobre 17.000 palabras es lo que no se le pide a un modelo | vigente |
| 0.8.0 | Agente «continuista» que prepare la hoja | Una invocación más para algo sin juicio | vigente |
| 0.8.0 | Subir `rechaza_con_graves` a 2 | Compra 38.190 palabras metiendo una contradicción en la memoria | vigente |
| 0.8.0 | Corregir el objetivo por el sesgo (`objetivo × (1 − sesgo)`) «por ahora» | Calibrar con una ejecución es ajustar a un punto | **reforzado**: E3 muestra sesgo opuesto por modelo (A11) |
| 0.7.3 | Escribir el detalle de la API de Langfuse en la spec | §9.3 fija el contrato, no una API de terceros | vigente |
| 0.7.2 | Hook en una sola línea dentro de `settings.json` | Ilegible y no probable por partes | vigente |
| 0.7.2 | No tocar el hook y detectar a posteriori | Prevenir salía barato y el criterio 6 no se pierde | vigente |
| 0.7.1 | Naranja como color de acento general; `publicDir` a `images/` | Contraste AA; publicar la carpeta entera | vigente (frontend) |
| 0.7.0 | Un solo revisor invocado con dos modos | Un prompt con dos trabajos confunde a los modelos pequeños | vigente |
| 0.7.0 | Seguir con un revisor y reforzar el prompt | No reduce las 19.000 palabras de entrada | vigente |
| 0.7.0 | Mejor intento ordenado estrictamente por gravedad | No arregla el caso: vuelve a elegir el intento 2 | vigente |
| 0.7.0 | Puntuación por pesos en el veredicto | Exige un campo en el JSON, que se porta literal | vigente; A4 (i) añade `cita`, no pesos |
| 0.7.0 | Que el harness pare y pregunte ante un empate | Rompe «la etapa 2 sin intervención humana» | vigente |
| 0.7.0 | Relajar `formato.tolerancia_longitud` | Maquilla una métrica declarada | vigente; A11 propone asimetría, no relajación |
| 0.7.0 | Reescrituras acotadas desde el informe global | La cadena de memoria es secuencial | vigente; A28 respeta el límite |
| 0.7.0 | Llamar a Langfuse desde `invocar()` | Red dentro de un bucle con cero fallos | vigente |
| 0.7.0 | Leer transcripts de subagente para atribuir tokens | Formato interno no garantizado; en el hito 2 la API lo da | vigente (E6 lo confirma) |
| 0.7.0 | Credenciales en `.claude/settings.json` ignorado | Ese fichero lleva los permisos del harness y se versiona | vigente |
| 0.6.0 | Que el visor calcule las métricas | Dos cifras para la misma novela | vigente |
| 0.6.0 | Que el visor lance o continúe generaciones | «Una web no puede invocar la sesión» | **superado** por el estudio (0.8.x, §9.4): sí lanza, con reglas |
| 0.6.0 | Volcado estático a JSON; frontend en repo aparte | Sin progreso en vivo; dos historiales | vigente |
| 0.5.1 | Modelo solo en el frontmatter | Mataría el escalado por invocación | vigente |
| 0.5.1 | Verificar a posteriori qué modelo respondió por transcripts | Rutas y formato no garantizados | vigente en CC; en la cáscara la API lo dice (§10.2) |
| 0.5.0 | `permissions.deny` con patrones de ruta para zonas de escritura | Se aplica a toda la sesión; bloquearía al interrogador | vigente |
| 0.5.0 | `permissions.deny` para inmutabilidad | Las reglas `Edit(...)` cubren `Write` y bloquearían la creación | vigente (y es la base para rechazar quitar `Edit(/novelas/**)`) |
| 0.4.0 | Seguir en Claude Code con modelos baratos como fase final | No da el bucle desatendido (40 relanzamientos) | **parcial**: la decisión de hoy saca el orquestador LLM de Claude Code (cáscara) pero mantiene la pausa (A23) |
| 0.4.0 | Comparar el harness con un prompt suelto a OpenRouter | No es la decisión pendiente | vigente |
| 0.1.0 | Hook `PreToolUse` («el usuario no quiere código») | — | **superado** en 0.5.0 |
| 0.1.0 | Abandonar Python + OpenRouter + Pydantic AI | El usuario quería el harness, no un programa | **parcial**: la cáscara será código (A15, quizá Python); el harness sigue siendo Markdown |

Decisiones del CHANGELOG antiguo que la 1.0.0 **revierte** y deben constar como tales: 0.4.0 «runner en código» (§10); 0.4.0/0.5.0 «§9.1: el runner lo escribirá Claude Code a partir de SKILL.md» (ahora no se traduce).

---

## 6. Punteros del harness y de la documentación que quedan desactualizados

No se han tocado (regla de esta pasada). Ordenados por lo que dicen ahora de falso:

| Fichero | Dice | Debería |
|---|---|---|
| `SKILL.md` cabecera | «El runner del hito 2 implementa estas mismas funciones con estos mismos nombres» | «El mismo texto lo ejecuta el orquestador de la cáscara (§10)» |
| `procedimientos/invocar.md` línea 40 | «en el hito 2 el runner espera la respuesta de la API y no hay nada que declarar» | En la cáscara `Agent` es bloqueante (§10.2) |
| `SKILL.md` §8, `procedimientos/cierre.md`, `plantillas/informe-cierre.md` | `specs/inventario.md §4` | `specs/functional.md §8.7` (el stub resuelve mientras tanto) |
| `CLAUDE.md` | «spec §8.5» para la primera ejecución | `specs/hallazgos.md E1` (el stub de §8.5 resuelve) |
| `CLAUDE.md`, `README.md` | Hitos con la redacción vieja / nueva sin la cáscara | Cabecera de functional 1.0.0 |
| `config.json` `_documentacion` | «Las claves marcadas 'hito 2' solo las usa el runner» | «la cáscara» |
| Agentes (`description`) | «Contrato en specs/functional.md §5.x» | Sigue siendo correcto: numeración estable |
| `frontend/server/harness.mjs` cabecera | «Esta capa es la única parte del estudio que NO se porta al hito 2» | Sigue siendo correcto; el protocolo que habla ya está en §10.3 |

---

## 7. Esqueleto de la primera entrada del CHANGELOG nuevo

Para que no salga de memoria. Sigue la estructura de la cabecera que dejaste.

```
## 1.0.0

### Major Changes

- **El hito 2 deja de ser un runner en código: es el mismo harness ejecutado por un
  orquestador LLM vía OpenRouter dentro de una cáscara que espeja Claude Code.** (spec §10, §0.1)
  - Revierte 0.4.0. Motivo: <el tuyo>.
  - SKILL.md, procedimientos, plantillas, agentes, settings.json e inmutables.sh se portan byte a byte.
  - Coste aceptado: el riesgo «lo mecánico lo hace un modelo» (E3) se mantiene; mitigación → A3.
  - Descartado: runner en código (0.4.0); herramientas de dominio en la cáscara (SKILL.md dejaría de ser
    portable tal cual); incrustar contenidos en los agentes (rompe el espejo y maxTurns).

- **La spec se parte en normativo (functional.md) y evidencia (hallazgos.md), con marcas de quién impone
  cada regla y de portabilidad, y spec_version en frontmatter.** (spec cabecera)
  - Descartado: un solo fichero (elegido dos); enlazar spec_version con config.version (A1); renumerar
    (56 punteros §N.N en 19 ficheros del harness).

### Minor Changes

- **Protocolo de sesión fijado** (spec §10.3): el subconjunto de stream-json que consume harness.mjs.
- **pausa_cada_capitulos vale en los dos hitos** (spec §6.3).

### Patch Changes

- **Rechazadas dos propuestas de la revisión del 09-17**: quitar /novela comparar (se usó al día siguiente
  para caso-01) y quitar Edit(/novelas/**) (rompería toda escritura del harness, 0.8.1).
- **Descartes heredados que siguen vigentes**: consolidación §5 (a copiar aquí los que protejan algo).
```
