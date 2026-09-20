---
spec_version: 1.0.0
config_version_requerida: 4
fecha: 2026-09-19
sustituye_a: "functional.md 0.8.1, inventario.md, revision-harness-2026-09-17.md, analisis-traza-2026-09-17.md"
tecnica: technical.md
diagramas: architecture.md
---

# story-maker — Especificación funcional

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. El usuario aporta una idea; cinco agentes (interrogador, escritor, resumidor, revisor de encargo y revisor de continuidad) coordinados por un **harness** la convierten en una novela completa.

El proyecto tiene **dos hitos** y este documento vale para los dos:

1. **Hito 1 — Claude Code, modelos caros.** El orquestador es la sesión de Claude Code con **Opus**; los cinco agentes son subagentes con **Haiku**. El harness es una skill orquestadora, cinco agentes y un conjunto de reglas, todo en Markdown dentro del repositorio.
2. **Hito 2 — Cáscara contra OpenRouter, modelo barato.** El **mismo** Markdown, ejecutado por un orquestador LLM barato servido por OpenRouter dentro de una **cáscara** propia (§10) que espeja lo que Claude Code da hoy: herramientas, permisos, hook y subagentes. Los agentes van en Haiku u otros modelos baratos. Esta decisión, tomada el 2026-09-18, **revierte** el "runner en código" de la 0.4.0 (consolidación §5).

Vocabulario: **hito** = fase del proyecto. **Etapa** = fase del flujo de una novela (1 interrogatorio, 2 bucle por capítulo, 3 final). No se usa "fase".

La carpeta de la novela es el único estado, en los dos hitos. Este documento es **normativo**: dice qué hace el sistema y quién lo impone. El **porqué** con sus datos vive en [technical.md](technical.md) (evidencias `E-n`). Lo **sin decidir** vive en [TODO.md](../TODO.md) (preguntas `A-n`); una regla marcada `→ A-n` está en discusión y no debe implementarse hasta que se decida.

### Cómo leer las marcas

Cada regla lleva al final dos marcas entre corchetes: **quién la impone**, por orden de fiabilidad, y **dónde funciona**.

| Marca | Quién impone la regla |
|---|---|
| `hook` | Código que corta la acción antes de ocurrir (`inmutables.sh`, `permissions.deny`) |
| `cáscara` | La plataforma que ejecuta al orquestador: hoy Claude Code (`maxTurns`, `permissions`, herramienta `Agent`); en el hito 2, la cáscara de §10 |
| `harness` | Prosa de SKILL.md o de un procedimiento, ejecutada por el orquestador. **Es un modelo leyendo instrucciones**: puede olvidarse (E3) |
| `prompt` | Contrato de un agente en `.claude/agents/`. Solo se cumple si el modelo lo cumple |
| `guion` | Código determinista fuera del bucle (`herramientas/`). Impone lo que el harness le pide y, a diferencia de la prosa, no puede olvidarse (E3); pero solo actúa si alguien lo llama |
| `ninguno` | Declarado en la spec y no impuesto por nada |
| `pendiente` | Declarado en la spec 0.8.0 y **no implementado** (→ A2). El harness hoy hace otra cosa |

| Marca | Dónde funciona hoy |
|---|---|
| `ambos` | Se porta al hito 2 sin cambios: es Markdown, `config.json`, la carpeta o un guion |
| `CC` | Solo funciona en Claude Code. La cáscara de §10 tiene que reimplementarlo |

Todo lo marcado `harness`, `prompt` o `ninguno` es la lista de lo que puede derivar sin que nadie se entere.

---

## 0. Glosario

Términos con sentido preciso. Si una palabra aparece aquí, significa esto en la spec, la skill, los agentes y la cáscara.

### 0.1 El proyecto

| Término | Qué es | Para qué sirve |
|---|---|---|
| **Harness** | El orquestador: llama a los agentes en orden, guarda el estado, impone los límites y toma todas las decisiones de flujo. Es la skill `/novela` leída por un modelo: Opus en Claude Code (hito 1), un LLM barato en la cáscara (hito 2) | Convierte cinco prompts en un sistema que produce una novela completa sin supervisión y reanudable |
| **Cáscara** | La plataforma que ejecuta al harness: le da herramientas (`Read`, `Write`, `Edit`, `Bash`, `Agent`), impone permisos y hooks, corre los subagentes y habla con el estudio. Hito 1: Claude Code. Hito 2: programa propio (§10). Antes llamada *runner* | Es lo único que cambia entre hitos. Todo lo demás es el mismo Markdown |
| **Agente** | Un prompt con contrato (entradas, salida, debe, no debe) ejecutado con un modelo. Cinco: interrogador, escritor, resumidor, revisor de encargo, revisor de continuidad | Cada uno hace una sola cosa; se les da distinto modelo y contexto y se juzgan por separado |
| **Revisor de encargo** | Contesta *¿se escribió lo que se pidió?* contra la entrada de escaleta y la voz de la biblia (criterios 2 y 4, §5.4) | Separar "lo pedido" de "lo coherente" reduce a la mitad contexto y criterios (E1) |
| **Revisor de continuidad** | Contesta *¿se contradice algo?* contra biblia, libro de estado y resúmenes (criterios 1 y 5, §5.5); revisa además el canon, cada arco y la novela completa | Las contradicciones a distancia son el fallo dominante de las novelas largas (E1, E2) |
| **Visor** | La parte de `frontend/` que solo lee (§9.2) | Cruza los seis ficheros de una novela a medias |
| **Estudio** | La parte de `frontend/` que recoge inputs y lanza el harness (§9.4). Fachada sobre `/novela`: no invoca agentes, no decide, no escribe en `novelas/` | Encargar sin terminal, sin llegar a nada a lo que no se llegue por terminal |
| **Encargo** | Lo que el usuario rellena antes de que exista la novela, en `encargos/<slug>/` | Separa lo que escribe el usuario de lo que escribe el harness |
| **Entrevista precargada** | Respuestas dadas por adelantado que entran como punto de partida del grilling (§9.4) | Un formulario no repregunta; precargar conserva las rondas |
| **Protocolo de sesión** | El subconjunto de `stream-json` con el que el estudio habla con la cáscara (§10.3) | Hace que el estudio funcione contra los dos hitos sin saber cuál es |
| **Observabilidad** | Trazas en una herramienta externa (Langfuse, §9.3). Nunca fuente de verdad ni puerta del flujo | Ver y comparar ejecuciones sin cruzar ficheros a mano |
| **Evaluador** | Un juez, determinista o LLM, que corre en Langfuse **fuera del bucle** sobre observaciones ya exportadas y mide a los revisores (§9.3.1) | Es la única fuente de defectos que no es el propio bucle (E5) |
| **Contrato** | Lo que un agente recibe, devuelve y tiene prohibido (§5) | Se porta sin cambios y el harness lo verifica en cada invocación |
| **Invocación** | Una llamada a un agente con unas entradas, que termina en salida o fallo | Unidad que se registra, reintenta y mide |
| **Hito / Etapa** | Ver arriba | El Estado guarda la etapa para reanudar |
| **Perfil** | Tamaño de la novela: `relato`, `novela_corta`, `novela`, `saga` | Cambiar `perfil_activo` escala el proyecto |
| **Escalado (de modelo)** | Subir a un modelo mejor en reescrituras, último intento, reintento tras fallo, revisiones de arco y global | Gastar el caro solo donde compensa |
| **Modo de prueba** | Entrevista desde fichero y escaleta aprobada sola | Verificar el harness sin persona delante |
| **Caso de referencia** | Idea y entrevista fijas en `pruebas/referencia/` | Comparar configuraciones sobre la misma historia |
| **Evidencia (E-n)** | Un hallazgo numerado de [technical.md](technical.md) con su dato | Que cada regla apunte a lo que la motivó sin repetirlo aquí |

### 0.2 Los artefactos de una novela

Todo vive en `novelas/<slug>/`. Por orden de aparición:

| Término | Qué es | Para qué sirve |
|---|---|---|
| **Idea** | Una o dos frases del usuario | Semilla; se guarda literal |
| **Entrevista** | Preguntas del harness y respuestas, marcando qué eligió el usuario y qué dejó en "decide tú" | Fija las decisiones antes de escribir. Única entrada del interrogador junto a la idea |
| **Biblia** | Premisa, tono y estilo, el mundo post-IA de esta historia, personajes con arco, motivación y voz, **canon** y **reglas inviolables** | Es la ley. Inmutable tras la aprobación |
| **Canon** | Sección «Cronología y datos fijos» de la biblia: año de arranque, edades con año de referencia, fechas, geometría del escenario | Una biblia que se contradice envenena todos los capítulos y es invisible a la revisión por capítulo (E1). Declarado en tabla, comprobarlo es restar |
| **Escaleta de alto nivel** | Tres actos divididos en arcos; por arco: rango, objetivo, sucesos clave, hilos que abre y cierra; total de capítulos | Lo que aprueba el usuario y queda inmutable |
| **Acto** | Planteamiento, nudo, desenlace | Estructura mínima |
| **Arco** | Tramo de como mucho `capitulos_por_arco` capítulos con objetivo propio | Unidad de planificación detallada y revisión intermedia |
| **Escaleta de arco** | Una entrada por capítulo del arco: título provisional, objetivo, sucesos, personajes, gancho, longitud objetivo | Orden de trabajo del escritor y vara del revisor de encargo |
| **Entrada / Gancho / Hilo** | Ficha de un capítulo · última nota prevista que empuja a seguir · línea argumental que se abre y debe cerrarse | Los hilos se registran con origen y cierre previsto: un hilo sin cerrar es el síntoma principal de incoherencia larga |
| **Capítulo / Intento / Reescritura** | Unidad del bucle · cada versión (máx. 3) · intento nuevo con el informe de rechazo como entrada | Se conservan todos los intentos |
| **Ajuste de longitud** | Intento pedido **solo** por salirse del margen de palabras, con presupuesto propio | Un rechazo por longitud no corrige nada; si consumiera reescritura se llevaría las correcciones pendientes (E1) |
| **Resumen** | Los **hechos** de un capítulo aprobado, acotados a `memoria.resumen_max_palabras`, con frontmatter de hilos, fechas de ficción, plazos y objetos | Memoria a corto plazo. El **estado** no va aquí (E2) |
| **Libro de estado** | Foto de la novela tras el último capítulo aprobado: personajes, hilos abiertos y cerrados, objetos, lugares, datos, reglas en vigor | Memoria a largo plazo de tamaño constante; vara del revisor de continuidad |
| **Hoja de continuidad** | Ficha corta que **compone el harness** antes de invocar a escritor y revisor de continuidad: fechas, días transcurridos, edades a la fecha, objetos y poseedores, plazos, hilos a cerrar | 7 de 9 contradicciones graves de la referencia eran aritmética que estaba en el contexto diluida (E2). Calcularlo es del harness |
| **Informe (de capítulo)** | Veredicto APROBADO/RECHAZADO con problemas concretos | Decide si se avanza y es la entrada de la reescritura |
| **Veredicto** | Cada revisor propone; el que vale es el que **recalcula el harness** sobre la unión (§7.5) | Que la decisión no dependa del humor del modelo |
| **Gravedad** | 1 contradicción · 2 incumple escaleta · 3 longitud (harness) · 4 voz/tono · 5 resumen infiel | Regla de veredicto numérica |
| **Aceptación por agotamiento** | Sin reescrituras y sin aprobado, el harness se queda con el mejor intento y sigue | Que la novela no se bloquee; su frecuencia es métrica |
| **Informe de arco / global** | Revisión de continuidad sobre el arco cerrado / la novela completa. Informativos | Detectan lo que no se ve capítulo a capítulo. Nadie reescribe a partir de ellos |
| **Manuscrito** | Título, índice y capítulos aprobados en orden | Producto final |
| **Erratas** | Arreglos de una línea que propone el informe global. El harness los escribe; nadie los aplica | Reescribir un capítulo cerrado invalidaría su resumen y todos los libros de estado posteriores |
| **Estado / Registro / Informe de cierre** | `estado.json` · `registro.md` (una fila por invocación y decisión, con volumen) · resultado de la ejecución con métricas y acción para continuar | Reanudar · trazabilidad · que el programa nunca termine en silencio |
| **Parada limpia** | Terminar sin nada a medias marcado como válido, Estado actualizado, motivo explicado | Siempre se reanuda con el mismo comando |
| **Slug** | Nombre de carpeta derivado de la idea | Identificador estable |

---

## 1. Alcance

### 1.1 Objetivo

A partir de una idea, producir una novela completa —biblia, escaleta, capítulos aprobados y manuscrito— con continuidad interna verificada, sin intervención humana desde la aprobación de la escaleta hasta el final.

### 1.2 Decisiones fijas

| Aspecto | Decisión |
|---|---|
| Género / universo / idioma | Ficción especulativa post-IA; cada novela inventa su mundo, sin canon compartido; castellano en todo |
| Interacción | Conversacional en la etapa 1, solo progreso después. Igual en los dos hitos: el estudio o la terminal hablan con la cáscara por el protocolo de sesión (§10.3) |
| Ejecución | Hito 1: Claude Code con subagentes, sin programas propios en el núcleo. Hito 2: la misma skill y los mismos agentes dentro de la cáscara de §10. **El orquestador es un modelo en los dos hitos** |
| **Quién escribe en disco** | **Solo el harness.** Los agentes devuelven su salida en el mensaje final `[prompt+cáscara · ambos]` |
| **Control determinista** | Todo lo decidible sin modelo (contar, recalcular veredicto, validar forma, actualizar estado, elegir mejor intento) lo hace el harness con herramientas mecánicas, nunca un agente. **Limitación:** en los dos hitos el harness es un modelo, así que "mecánico" significa "el modelo se acordó de ejecutar `wc -w`" (E3) `[harness · ambos]` → A3 |
| Escala | Hito 1: `relato` (5 capítulos). Hito 2: hasta 200 (`saga`), una sola novela con una trama |

### 1.3 No objetivos

- Formatos distintos de Markdown y JSON. El visor pinta Markdown; no produce ficheros.
- Código propio **en el núcleo del hito 1**: orquestador y agentes son Markdown. Excepciones declaradas: el hook `inmutables.sh` (§3.1), el visor (§9.2) y el estudio (§9.4); las dos primeras prescindibles, la tercera no genera ni decide. En el hito 2 la cáscara es código, **el orquestador no**. Guiones mecánicos en `herramientas/` llamados desde la skill: → A3.
- Coste en dinero en el hito 1 (Claude Code no lo expone). Sí volumen (§6.6). En el hito 2 OpenRouter devuelve tokens y coste.
- Interfaz de la que el harness **dependa**: `/novela nueva` desde terminal produce la misma novela sin `frontend/`.
- Ilustraciones, otros idiomas, series encadenadas (`saga` es una novela larga), modo de prueba como uso normal, volver atrás a un capítulo aprobado, reescritura automática tras arco o global, avisos externos.
- Ni portada, ni traducciones, ni una novela **corregida**: los informes se entregan tal cual.

---

## 2. Actores

| Actor | Tipo | Responsabilidad |
|---|---|---|
| **Usuario** | Persona | Idea, entrevista, aprobación de la escaleta, decidir qué hacer con los informes |
| **Harness** | La skill `/novela` leída por el orquestador (Opus en Claude Code; LLM barato en la cáscara) | Orquesta, invoca, **escribe todos los ficheros**, guarda estado, impone límites, comprueba longitud y forma, reanuda, ensambla |
| **Interrogador** | Agente | Idea + entrevista → biblia y escaleta de alto nivel; al empezar cada arco, su escaleta |
| **Escritor** | Agente | Escribe cada capítulo. Solo el capítulo |
| **Resumidor** | Agente | Del texto del capítulo y el libro de estado vigente, resumen y libro de estado propuesto |
| **Revisor de encargo** | Agente | ¿Cumple su entrada de escaleta y el tono? Nunca edita |
| **Revisor de continuidad** | Agente | ¿Contradice canon, libro de estado o resúmenes? Revisa además canon, arco y novela completa. Nunca edita |

Los agentes son **prompts con contrato**, no piezas de Claude Code. Ningún agente escribe ficheros ni habla con el usuario `[prompt+cáscara · ambos]`.

Por qué el resumen no lo escribe el escritor: resume lo que quiso escribir, no lo que quedó (E1). Por qué la revisión está partida: el revisor único recibía 19.000 palabras con cinco criterios y se le escaparon cuatro contradicciones a distancia (E1).

---

## 3. Artefactos

Todos en `novelas/<slug>/`, único estado del sistema. **Todo lo escribe el harness**; "Contenido de" dice qué agente produjo el contenido. "DdH" = definición de hecho: cuándo el artefacto está bien. Esta tabla es también el **inventario** que `/novela verificar` comprueba (§8.7) y la definición de "misma salida" para la cáscara (§10.4).

| Artefacto | Fichero | Cuántos | Contenido de | Lo leen | DdH |
|---|---|---|---|---|---|
| Idea | `idea.md` | 1 | Usuario | Todos | Literal, sin reinterpretar |
| Configuración | `config.json` | 1 | Harness | Harness, interrogador | `version: 4`; perfil resuelto con `nombre`; `proveedor`, `formato`, `modelos`, `limites`, `veredicto`, `memoria`, `calidad`, `origen`; sin `perfiles` (§7) |
| Entrevista | `entrevista.md` | 1 | Usuario vía grilling o fichero | Interrogador | `cerrada: true`, `origen: grilling \| fichero \| formulario+grilling`; cada decisión marcada [usuario], [recomendación aceptada] o [decide tú] |
| Biblia | `biblia.md` | 1 | Interrogador | Todos | `aprobada: true`; premisa, mundo, **3–7 reglas inviolables numeradas**, tono/PDV/estilo, personajes, **«Cronología y datos fijos» con contenido** |
| Escaleta (alto nivel) | `escaleta.md` | 1 | Interrogador | Todos | `aprobada: true`; `capitulos` en límites; `arcos` que cubren 1..N sin huecos ni solapes, ninguno > `capitulos_por_arco`, cada uno con `acto, objetivo, sucesos_clave, hilos_abre, hilos_cierra`; tres actos; sección Hilos |
| Escaleta de arco | `arcos/arco-AA.md` | 1 por arco | Interrogador | Todos | `validada: true`; una entrada por capítulo del rango con `n, titulo, objetivo, sucesos, personajes, gancho, palabras_objetivo` en límites; todos los `sucesos_clave` del arco asignados |
| Capítulo N, intento K | `capitulos/NN/intento-K.md` | 1–3 por capítulo | Escritor | Todos | Sin frontmatter: `# <título>` y texto. El aprobado cumple su entrada y está en tolerancia (`wc -w`) |
| Resumen N, K | `capitulos/NN/resumen-K.md` | 1 por intento que pasó la longitud | Resumidor | Todos | Frontmatter `capitulo, intento, hilos_abiertos, hilos_cerrados, personajes` (+ `fecha_ficcion_inicio, fecha_ficcion_fin, plazos, objetos` `[pendiente]`); secciones Hechos, Cambios en personajes, Elementos introducidos, Enlace |
| Libro de estado propuesto N, K | `capitulos/NN/libro-estado-K.md` | ídem | Resumidor | Harness | El libro de estado tal como quedaría si se aprueba K |
| Informe N, K | `capitulos/NN/informe-K.md` | 1 por intento | Harness, uniendo los dos revisores (o solo harness si longitud) | Todos | `veredicto` recalculado sobre la unión; `origen: revisores \| harness`; cada problema con `gravedad ∈ {1..5}, origen ∈ {encargo, continuidad, harness}, donde, que, por_que` |
| Libro de estado | `libro-estado.md` | 1 | Resumidor, adoptado por el harness | Escritor, resumidor, revisor | `hasta_capitulo` = último aprobado; copia exacta del `libro-estado-K.md` aprobado; secciones Personajes, Hilos abiertos, Hilos cerrados, Elementos, Reglas en vigor |
| Informe de arco | `arcos/informe-arco-AA.md` | 1 por arco, **solo con más de un arco** | Revisor de continuidad | Usuario | `capitulo: arco-AA`; informativo; problemas con la forma de §5.6 |
| Estado | `estado.json` | 1 | Harness | Harness | `version: 4`; último punto consistente; `etapa: completa` al terminar; `capitulos[N]` con `aprobado, por_agotamiento, intentos, reescrituras, ajustes_longitud`; `arcos[A].escaleta_validada`; `invocaciones` por agente |
| Registro | `registro.md` | 1 | Harness | Usuario, exportador | Una fila por evento (plantilla); cada `invocacion` con `modelo, pal_entrada, pal_salida` y `tok_*`, `coste_usd` si existen. Un intento revisado produce **dos** filas `invocacion`. En Claude Code cada invocación deja además una fila `resultado: pendiente` → A9 |
| Manuscrito | `manuscrito.md` | 1 | Harness | Usuario | Título, índice, capítulos aprobados en orden; nota final si alguno fue por agotamiento |
| Informe global | `informe-global.md` | 1 | Revisor de continuidad | Usuario | `capitulo: global`; `base: manuscrito \| resumenes`; informativo. Vacío de problemas es posible |
| Erratas | `erratas.md` | 1 | Harness | Usuario | Problemas del global que se arreglan en una línea, con ruta, cita literal presente en el manuscrito y cambio. `aplicadas: 0` siempre |
| Informe de cierre | `informe-cierre.md` | 1, reescrito cada ejecución | Harness | Usuario | `resultado: EXITO \| PARADA` con motivo, qué quedó hecho, volumen, métricas CUMPLE/NO CUMPLE, inventario, acción para continuar |
| Commits | git | ≥ 3 + 1 por capítulo + 2 por arco extra | Harness | — | `novela <slug>: carpeta creada · escaleta aprobada · arco AA detallado · cap NN cerrado (intento K) · arco AA revisado · novela completa · PARADA <motivo>` |

Un capítulo rechazado por longitud tiene `intento-K.md` e `informe-K.md` pero no resumen ni libro de estado. Con `relato`: mínimo 20 ficheros de capítulo, máximo 60. Varios intentos no son un fallo: son el bucle funcionando.

### 3.1 Reglas de escritura

- **Solo el harness escribe.** Los agentes se definen con `tools: Read, Glob, Grep` `[cáscara · ambos: la cáscara de §10 respeta el mismo frontmatter]`.
- **Nada aprobado se modifica**: biblia y escaleta de alto nivel tras la aprobación, escaleta de arco tras validarla, capítulo tras APROBADO o agotamiento, libro de estado salvo por el harness al cerrar capítulo. Cada uno se crea con una escritura completa; nunca se edita en sitio. Lo impone `.claude/hooks/inmutables.sh` como `PreToolUse` sobre `Edit` y `Write` dentro de `novelas/`, registrado en `.claude/settings.json` `[hook · ambos: la cáscara ejecuta el mismo hook, §10.2]`:
  - `Edit` bloquea **siempre** sobre `biblia.md`, `escaleta.md`, `arco-*.md`, `informe-arco-*.md`, `intento-*.md`, `libro-estado.md`, `libro-estado-*.md`, `manuscrito.md`.
  - `Write` **por aprobación** para `biblia.md`, `escaleta.md`, `arco-*.md`: el hook lee el frontmatter del fichero existente y bloquea con `aprobada: true` / `validada: true`. Sin la marca deja pasar: una propuesta se reescribe a propósito en cada vuelta, y aprobar es reescribir con la marca (§4.1).
  - `Write` **por existencia** para `intento-*.md`, `libro-estado-*.md`, `informe-arco-*.md`, `manuscrito.md`: el primero es el harness creándolo; el segundo, el error.
  - `libro-estado.md`: su `Write` siempre pasa (se sustituye al cerrar cada capítulo); su `Edit` no.
  - El hook **falla en abierto** si no entiende su entrada. **Limitación conocida:** no cubre Bash (`cp`, `cat >`, `sed -i`); el criterio 6 de §8.2 lo demuestra a posteriori con git.
- Estado, Registro y Libro de estado son exclusivos del harness `[harness · ambos]`.
- **Todo commit pasa por `commitear(carpeta, punto)`**, que después de `git add -A` + `git commit` comprueba dos cosas: que `HEAD` ha avanzado y que `git status --porcelain novelas/<slug>` queda **vacío**. Si falla cualquiera de las dos, PARADA `COMMIT_NO_LIMPIO` sin avanzar al paso siguiente `[harness · ambos]`. Ningún procedimiento llama a `git commit` por su cuenta. Sin esta comprobación, un commit olvidado en `cerrar_capitulo` deja el capítulo aprobado sin guardar y la reanudación lo trata como paso a medias. Única excepción: llamada desde `cerrar()`, donde el fallo se anota como aviso en vez de parar, porque una PARADA en el cierre se llamaría a sí misma.
- **Escritura atómica** (temporal + renombrado) `[cáscara · hito 2: la herramienta `Write` de la cáscara]`.
- Reglas de permisos del repositorio (`.claude/settings.json`): `Edit(/novelas/**)` y `Edit(/optimizaciones/**)` son las que autorizan `Write` sobre esas carpetas (en Claude Code las reglas `Edit(ruta)` cubren `Write`; una regla `Write(ruta)` no se consulta). `git` acotado a `novelas/`, sin `push`, `--amend`, `reset --hard` ni `rebase`. `deny` de `Read` sobre `.env`, `frontend/.env`, `.claude/settings.local.json` y `herramientas/optimizacion/conjuntos/**` `[hook · ambos: la cáscara lee el mismo fichero]`.
- **Un `deny` de `Read` no cubre lo que `Bash` lee.** En Claude Code esas reglas gobiernan la herramienta `Read`, no el contenido de un comando: con `Bash(cat *)` en el `allow`, un `cat` de cualquiera de esas rutas pasaba. Lo que lo impone es `.claude/hooks/rutas-protegidas.sh`, `PreToolUse` sobre `Bash`, que **falla en cerrado** (sin entrada legible, deniega) `[hook · ambos]`. Los `cat`/`head`/`tail` del `allow` están además acotados a `novelas/`, `encargos/`, `specs/` y `config.json`. No es un sandbox: una ruta ofuscada se le escapa; lo que corta es el camino barato, que es el único que un agente toma. Fixtures de los dos hooks: `herramientas/pruebas/hook.sh`.

### 3.2 Cuánto texto, por perfil

| Perfil | Capítulos | Palabras/cap | Arcos | Manuscrito | Páginas (250 p/pág) | Ficheros de capítulo |
|---|---|---|---|---|---|---|
| `relato` | 3 | 1.500 | 1 | ~4.500 | ~18 | 12–36 |
| `novela_corta` | 12 | 2.000 | 1 | ~24.000 | ~96 | 48–144 |
| `novela` | 30 | 2.500 | 2 | ~75.000 | ~300 | 120–360 |
| `saga` | 100 (hasta 200) | 2.500 | 7 (hasta 14) | ~250.000 (hasta ~500.000) | ~1.000 (hasta ~2.000) | 400–1.200 (hasta 800–2.400) |

A partir de `novela` la revisión global se hace sobre resúmenes e informes de arco (`limites.revision_global_max_palabras`).

---

## 4. Flujo

```mermaid
flowchart TD
    idea([Usuario: idea])
    subgraph E1["Etapa 1 — Interrogatorio"]
        preg[Harness entrevista y cierra la Entrevista]
        prop[Interrogador propone biblia + escaleta]
        can{Revisor de continuidad: ¿canon coherente?}
        conf{¿Usuario confirma?}
        preg --> prop --> can
        can -- "no" --> prop
        can -- "sí" --> conf
        conf -- "cambios" --> prop
    end
    subgraph E2["Etapa 2 — Bucle por arco y capítulo, sin intervención humana"]
        arco[Interrogador detalla arco A; harness valida]
        esc[Escritor escribe capítulo N]
        lon{Harness: ¿longitud OK?}
        ajus{¿Quedan ajustes?}
        res[Resumidor: resumen + libro de estado propuesto]
        rev[Dos revisores en paralelo; harness une]
        vered{Veredicto recalculado}
        quedan{¿Quedan reescrituras?}
        agot[Mejor intento + aviso]
        cierra[Cierra capítulo: libro de estado, estado, commit]
        finarco{¿Fin de arco?}
        revarco[Informe de arco]
        mas{¿Quedan capítulos?}
        arco --> esc --> lon
        lon -- "no" --> ajus
        ajus -- "sí" --> esc
        ajus -- "no" --> quedan
        lon -- "sí" --> res --> rev --> vered
        vered -- "RECHAZADO" --> quedan
        quedan -- "sí" --> esc
        quedan -- "no" --> agot --> cierra
        vered -- "APROBADO" --> cierra
        cierra --> finarco
        finarco -- "sí" --> revarco --> mas
        finarco -- "no" --> mas
        mas -- "mismo arco" --> esc
        mas -- "arco nuevo" --> arco
    end
    subgraph E3["Etapa 3 — Final"]
        ens[Ensamblar manuscrito] --> glob[Informe global] --> err[erratas.md]
    end
    idea --> preg
    conf -- "confirma" --> arco
    mas -- "no" --> ens
    err --> fin([Usuario])
```

### 4.1 Etapa 1 — Interrogatorio

1. El harness crea la carpeta y guarda la idea `[harness · ambos]`.
2. **Entrevista** en rondas sucesivas sin límite fijo, con la skill `grilling` `[harness · CC: la skill es un plugin de Claude Code → A17]`. Con `entrevista: <ruta>` la toma cerrada de fichero y no pregunta; con `precarga: <carpeta>` las respuestas del estudio son el punto de partida y el grilling sigue (§9.4). Resultado: `entrevista.md`.
3. **Propuesta.** Interrogador con idea, entrevista y límites → biblia, escaleta de alto nivel (y la del arco si es único) y propuesta de cierre. El harness valida contra los límites `[harness · ambos]`.
4. **Validación del canon.** Antes de enseñar nada, revisor de continuidad en modo `canon` sobre biblia y escaleta. Problemas → al interrogador, hasta `escaleta_rechazos_max`; después se presentan al usuario junto con la propuesta `[harness · ambos]`. Que compruebe también reglas inviolables contra la escaleta: → A4.
5. El usuario **confirma** o **pide cambios**; el interrogador corrige solo eso y el canon se revalida. Sin usuario en la sesión (`estado.encargo` no nulo): parada `ESPERA_APROBACION` y decisión en `encargos/<slug>/decision.md` (§9.4) `[harness · ambos]`.
6. Con la confirmación, biblia y escaleta se reescriben con `aprobada: true` `[harness+hook · ambos]`.

**Escaleta por arcos.** La de alto nivel divide en arcos de ≤ `capitulos_por_arco`; la de cada arco se genera al llegar a él con biblia, alto nivel, libro de estado e informe del arco anterior. Con total ≤ `capitulos_por_arco` hay un solo arco y el interrogador la devuelve entera en la propuesta.

**El canon, explícito.** Sección obligatoria «Cronología y datos fijos». Regla derivada: si una fecha no está en el canon, el texto no la ata a un día de la semana `[prompt · ambos]`. Evidencia: E1.

Restricciones del perfil (§7.1): capítulos entre `min` y `max`; longitud entre suelo y techo; arcos sin huecos ni solapes, cada uno ≤ `capitulos_por_arco`. Violación → al interrogador con motivo, hasta `escaleta_rechazos_max`, después presentar (propuesta) o parar (arco) `[harness · ambos]`.

### 4.2 Etapa 2 — Bucle por arco y capítulo

**Inicio de arco A.** Si `arcos/arco-AA.md` no existe: interrogador en modo arco. El harness comprueba rango exacto, longitudes y que todos los sucesos clave están asignados; si no, devuelve hasta `escaleta_rechazos_max`, después parada limpia. Validada: `validada: true` y commit. Sin confirmación del usuario `[harness · ambos]`.

Para cada capítulo N:

**Hoja de continuidad (harness, sin modelo).** Ficha de ≤ `memoria.hoja_continuidad_max_palabras` (200) con: fecha de ficción del fin de N−1 y la prevista para N, días transcurridos; edad de cada personaje presente a esa fecha desde el canon; objetos con poseedor y lugar; plazos en curso; hilos que N debe cerrar. Solo copia y resta; dato ausente → `desconocido`. Se pasa al escritor y al revisor de continuidad `[pendiente → A2]`. Evidencia: E2.

**Escritura.** El escritor recibe: hoja de continuidad `[pendiente]`, biblia, escaleta de alto nivel, escaleta del arco con la entrada N destacada, libro de estado, últimos `resumenes_completos_ultimos` resúmenes, capítulo N−1 íntegro si `capitulo_anterior_integro`, y en reescritura el informe y el texto rechazado. Devuelve el capítulo; el harness lo escribe en `intento-K.md` `[harness · ambos]`.

**Comprobación de longitud (harness, sin modelo).** `wc -w` del cuerpo. Fuera de `tolerancia_longitud`: el harness escribe él mismo `informe-K.md` con un problema de gravedad 3 y trata el intento como RECHAZADO **sin invocar a nadie más** `[harness · ambos]`. Un rechazo por longitud consume un **ajuste de longitud** (`limites.ajustes_longitud`), no reescritura; K sigue avanzando; el informe de contenido pendiente se pasa junto con el de longitud. Agotados los ajustes, vuelve a consumir reescritura `[harness · ambos]`. El prompt del escritor lleva siempre el recuento del intento anterior y suelo y techo **en palabras absolutas**, con la instrucción de que corregir no alarga `[harness · ambos]`. Evidencia: E1. Sesgo de longitud opuesto por modelo (E3): → A11.

**Resumen.** El resumidor recibe **solo** el texto, el libro de estado vigente y las plantillas. Devuelve resumen y libro de estado propuesto; el harness escribe ambos `[harness · ambos]`. El harness cuenta el resumen; si supera `memoria.resumen_max_palabras`, reinvoca **una sola vez** con el tope en palabras absolutas; si vuelve a pasarse, acepta con aviso. No rechaza el capítulo `[pendiente → A2]`. Evidencia: E2.

**Revisión.** Dos agentes en paralelo `[cáscara · ambos: dos llamadas `Agent` en el mismo mensaje]`:
- **Encargo** (§5.4): capítulo, escaleta de alto nivel, escaleta del arco (entrada N y posteriores), biblia.
- **Continuidad** (§5.5): hoja `[pendiente]`, capítulo, su resumen, biblia, libro de estado, los mismos resúmenes que el escritor.

El harness valida los dos JSON, **une** problemas y observaciones, **recalcula el veredicto** con §7.5 y escribe un único `informe-K.md` con el origen de cada problema. Veredicto propuesto ≠ recalculado → `discrepancia_veredicto`. Mismo problema en los dos → se conserva el de mayor gravedad y se anota duplicado `[harness · ambos]`. Que un revisor falle no invalida al otro: se reintenta solo ese (§6.5).

**Decisión del harness** `[harness · ambos]`:
- APROBADO → `libro-estado-K.md` sobre `libro-estado.md`, Estado, commit, N+1.
- RECHAZADO con reescrituras → escritor con el informe (máx. `reescrituras_max`, 2: tres intentos).
- RECHAZADO sin reescrituras → **mejor intento**, aviso con informe en Registro y Estado, N+1.

**Mejor intento** `[harness · ambos]`, por orden: (1) descartar los rechazados por longitud si alguno llegó a revisores; si todos lo fueron, el más cercano al objetivo y fin; (2) **cumple los cierres que la escaleta manda para N** (`hilos_cierra` de la escaleta contra `hilos_cerrados` del resumen), a igualdad el que más cierre; (3) menos problemas de gravedad 1–2; (4) menos problemas en total; (5) el más reciente. Resuelto en (4) o (5): aviso «mejor intento elegido sin criterio fuerte». No se pregunta al usuario. Evidencia: E1. Sin ejercitar aún en ninguna ejecución (E3).

**Fin de arco.** Revisor de continuidad con todos los capítulos del arco, escaletas, biblia y libro de estado → `informe-arco-AA.md`, informativo; alimenta la escaleta del arco siguiente. Con un solo arco, arco y global son la misma pasada `[harness · ambos]`.

**Progreso visible.** Una línea por evento (§6.4). El usuario puede interrumpir; se reanuda desde disco (§6.2).

### 4.3 Etapa 3 — Final

1. Ensamblar el **manuscrito** `[harness · ambos]`.
2. **Revisión global.** Si el manuscrito ≤ `revision_global_max_palabras`, una pasada sobre la novela completa; si no, sobre biblia, escaleta de alto nivel, libro de estado final, todos los resúmenes y los informes de arco, y el informe lo dice. No reescribe nada `[harness · ambos]`.
3. **Erratas.** El harness separa del informe global lo que se arregla en una línea y lo escribe en `erratas.md` con ruta, cita exacta y cambio. **No aplica ninguna** `[harness · ambos]`. Pulido de lengua fuera del bucle: → A28.
4. Métricas de calidad (§8.3) e informe de cierre (§6.5). Recuento de volumen **desde `registro.md`**, no desde los contadores de `estado.json`: → A10 (E3).

---

## 5. Contratos de los agentes

Reglas comunes: reciben exactamente las entradas de su contrato; devuelven su salida **en el mensaje final** con la forma fijada, sin texto antes ni después; no escriben ficheros; no hablan con el usuario; no deciden flujo `[prompt · ambos]`. Un mensaje final sin la forma esperada es **incumplimiento de contrato** (§6.5) y el harness repite indicando qué faltó `[harness · ambos]`.

**Bloques de documento** (interrogador, escritor, resumidor): cada documento entre `=== ARCHIVO: <ruta relativa> ===` y `=== FIN ===`. Los revisores devuelven solo JSON (§5.6). Tolerancia de formato (valla de código alrededor, ruido tras el delimitador): hoy improvisada por el orquestador (E3) → A8.

Definición en `.claude/agents/`: `tools: Read, Glob, Grep`, `maxTurns` = `limites.turnos_por_invocacion`, `model` = `modelos.<agente>`, **sin** `memory` (una memoria persistente crearía el canon compartido que §1.2 prohíbe) `[cáscara · ambos: la cáscara lee el mismo frontmatter]`. `maxTurns` y `model` son estáticos; `comprobar_entorno` comprueba que coinciden con `config.json` `[harness · ambos]`. El modelo que manda es el parámetro `model` de la llamada `Agent` (escalado, §7.3); el del frontmatter es red de seguridad.

**Modos de fallo observados** (E1, E3, E4): tabla al final de cada contrato. Es lo que hace que un prompt mejore en vez de crecer.

### 5.1 Interrogador

| | |
|---|---|
| **Entrada (propuesta)** | Idea; entrevista cerrada; límites; en segunda vuelta, el motivo |
| **Entrada (arco)** | Biblia; escaleta de alto nivel con el arco destacado; libro de estado; informe del arco anterior; límites; motivo si hay |
| **Salida** | Biblia, escaleta de alto nivel y, si hay un arco, su escaleta; propuesta de cierre. En modo arco, la escaleta del arco. Bloques con ruta destino |
| **Debe** | Respetar lo elegido en la entrevista; decidir lo "decide tú" y anotarlo; escribir «Cronología y datos fijos» y comprobar que cuadra; tamaños en límites; tres actos; objetivo propio por capítulo; en modo arco asignar todos los sucesos clave y recoger lo pendiente del informe anterior; en segunda vuelta corregir solo lo indicado |
| **No debe** | Escribir prosa de la novela; preguntar; modificar biblia o alto nivel en modo arco; marcar nada como aprobado |

| Fallo visto | Dónde |
|---|---|
| Salida sin bloques `=== ARCHIVO ===` (describe el fichero en vez de emitirlo); arcos duplicados en `escaleta.md` | 3 reintentos, haiku (E3) |
| Canon con plantas descuadradas y un final en una planta que el canon no declaraba | 2 rechazos de canon, haiku (E3) — el mecanismo funcionó |
| Llave entregada en un año incompatible con edad y oficio; ascensor con menos paradas que plantas | Biblia de referencia, opus, antes del canon explícito (E1) |

### 5.2 Escritor

| | |
|---|---|
| **Entrada** | Hoja de continuidad `[pendiente]`; biblia; escaleta de alto nivel; escaleta del arco con N destacada; libro de estado; resúmenes según `memoria`; capítulo anterior íntegro si procede; en reescritura, informe y texto rechazado |
| **Salida** | Capítulo N en un único bloque, con título |
| **Debe** | Cumplir objetivo, sucesos y gancho de N; tomar de la hoja fechas, edades, plazos y poseedores sin recalcular `[pendiente]`; respetar biblia, libro de estado y resúmenes; longitud en tolerancia; voz del capítulo anterior; en reescritura corregir cada problema sin introducir otros |
| **No debe** | Producir resumen ni notas; adelantar sucesos; resolver hilos que deben quedar abiertos; contradecir el libro de estado |

| Fallo visto | Dónde |
|---|---|
| Se pasa de largo (+10,5 %, 11 de 13 por encima) con opus; se queda corto (−22,7 %, 9 de 9 por debajo) con haiku | E1, E3 |
| Salida sin bloques o bloque sin `=== FIN ===` | 3 reintentos, haiku (E3) |
| Ampliar por longitud triplica el motivo repetido («treinta años»: 1 → 3) | Cap. 5 de B (E4, E5) |
| Aritmética de fechas, edades y plazos, y estado de objetos: 7 de 9 graves | E2 |
| Castellano roto («la agua», «La conocimiento», «hubiese trovado»), verosimilitud técnica, mundo post-IA ausente, escenas repetidas | E4, E5 — **ningún criterio los cubre** → A4 |

### 5.3 Resumidor

| | |
|---|---|
| **Entrada** | Texto del capítulo N intento K; libro de estado vigente; plantillas |
| **Salida** | Dos bloques: resumen N (frontmatter `hilos_abiertos`, `hilos_cerrados` y `[pendiente]` `fecha_ficcion_inicio`, `fecha_ficcion_fin`, `plazos`, `objetos`; cuerpo de hechos dentro de `resumen_max_palabras`) y libro de estado actualizado completo |
| **Debe** | Registrar **solo lo que está en el texto**. Reparto estricto: hechos y frontmatter en el resumen; estado en el libro de estado, actualizando lo afectado y conservando lo demás; origen de cada hilo; mover a cerrados lo que el texto cierra; fecha de ficción vacía si el texto no la dice `[pendiente el reparto → A2]` |
| **No debe** | Inferir lo que el autor quiso decir; añadir hechos; juzgar calidad; **repetir el libro de estado en el resumen**; pasarse del tope; consultar escaleta ni biblia |

| Fallo visto | Dónde |
|---|---|
| Resumen del 110 % del capítulo que resume (1.785 palabras de media), por duplicar el libro de estado | E2 |
| Copia un error de hecho del texto («50 años en el barrio», «mujer mayor») | E4 |
| Salida sin bloques; `**` sobrantes en viñetas | E3 |

### 5.4 Revisor de encargo

Contesta **¿está escrito lo que se pidió?**

| | |
|---|---|
| **Entrada** | Capítulo N; escaleta de alto nivel; escaleta del arco (N y posteriores); biblia |
| **Salida** | JSON de §5.6 |
| **Debe** | Juzgar solo contra **(2)** incumple la entrada N (suceso que falta, objetivo no logrado, gancho distinto) o adelanta sucesos o resuelve hilos que debían quedar abiertos; **(4)** ruptura de voz, PDV o tono. Recorrer la entrada suceso por suceso. Cada problema concreto y accionable |
| **No debe** | Editar; juzgar contradicciones con libro de estado o capítulos anteriores; **contar palabras**; rechazar por gusto; añadir criterios |

Solo modo capítulo.

| Fallo visto | Dónde |
|---|---|
| Aprobó un capítulo que no cumple un suceso («Marisa ignora el mensaje») y otro cuyo título («La 4ª planta») no tiene referente en el texto | B, haiku (E4) → A12 |
| No ve repetición de escena entre capítulos ni ausencia del mundo post-IA: no son sus criterios | E5 → A4 |

### 5.5 Revisor de continuidad

Contesta **¿se contradice algo?** a cuatro escalas: biblia consigo misma, capítulo, arco, novela.

| | |
|---|---|
| **Entrada (canon)** | Biblia y escaleta de alto nivel antes de aprobarse |
| **Entrada (capítulo)** | Hoja de continuidad `[pendiente]`; capítulo N; resumen N; biblia; libro de estado; resúmenes según `memoria` |
| **Entrada (arco)** | Capítulos del arco; escaletas; biblia; libro de estado |
| **Entrada (global)** | Manuscrito, o si no cabe biblia, escaleta, libro de estado final, resúmenes e informes de arco |
| **Salida** | JSON de §5.6 |
| **Debe** | Juzgar solo contra **(1)** contradice biblia, canon, libro de estado o resúmenes; **(5)** el resumen no refleja el capítulo. En `canon`, cuadrar los números de «Cronología y datos fijos» entre sí y con el resto. Contrastar cada afirmación absoluta («nadie», «siempre») con el libro de estado |
| **No debe** | Editar; juzgar escaleta ni tono; **contar palabras**; rechazar por gusto |

En `canon` los problemas son gravedad 1 contra la biblia. En arco y global el informe es informativo.

| Fallo visto | Dónde |
|---|---|
| Degrada a **observación** un salto de tres días sin justificar y unas fotos que nadie tomó («es compresión narrativa»); cierra con «Coherencia interna total» sobre un manuscrito con tres contradicciones | B, haiku (E4) → A12 |
| Con opus, la global encuentra 4–5 graves que ninguna revisión de capítulo vio | E1 |
| La frontera problema/observación no está definida en ningún sitio | E5 → A4 |

### 5.6 Forma del informe de los revisores

```json
{
  "veredicto": "RECHAZADO",
  "problemas": [
    { "gravedad": 1, "donde": "párrafo 14, escena del taller",
      "que": "Marta usa el implante que perdió en el capítulo 2",
      "por_que": "libro de estado, Personajes › Marta: 'sin implante desde el cap. 2'" }
  ],
  "observaciones": ["El diálogo del final se alarga; no obliga a reescribir"]
}
```

`problemas` puede ser vacío. `gravedad` ∈ {1, 2, 4, 5} y **cada revisor solo emite las suyas** (encargo 2 y 4; continuidad 1 y 5); otra es incumplimiento `[harness · ambos]`. El harness rechaza como incumplimiento lo que no sea JSON válido con exactamente esas tres claves `[harness · ambos]`. JSON y no YAML porque los modelos baratos rompen el YAML. Campo `cita` obligatorio verificado con `grep`, y definición comprobable de problema frente a observación: → A4.

**Regla de veredicto** sobre la **unión**: RECHAZADO si hay ≥ `veredicto.rechaza_con_gravedad_1` de gravedad 1, o ≥ `rechaza_con_gravedad_2` de gravedad 2, o ≥ `rechaza_con_leves` de gravedad 3–5 `[pendiente → A2: hoy `config.json`, `capitulo.md` y `plantillas/informe.md` aplican `rechaza_con_graves` sobre {1,2} juntas]`.

---

## 6. Contrato del harness

### 6.1 Responsabilidades `[harness · ambos]`

Crear y gestionar la carpeta · invocar con exactamente las entradas del contrato · **esperar la salida de cada agente antes de seguir** (única concurrencia: los dos revisores de un intento) · validar la forma y **escribir** · comprobar longitud del capítulo y del resumen · componer la hoja de continuidad `[pendiente]` · decidir todo el flujo · unir problemas, recalcular veredicto, elegir mejor intento · mantener el libro de estado · escribir el Estado **tras cada decisión** · registrar todo · imponer límites · ensamblar y calcular métricas · mostrar progreso.

**Primero se cuenta, después se registra**, para toda fila del registro; hoy es nota local de `comprobar_longitud` y ha fallado en el resumidor (E3) → A10.

### 6.2 Reanudación `[harness · ambos]`

Relanzar sobre una carpeta existente continúa donde se quedó: escaleta sin aprobar → interrogatorio (tras `ESPERA_APROBACION`, la propuesta no se rehace, solo se aplica la decisión); en el bucle → arco, capítulo e intento del Estado, un intento a medias se repite con el mismo número, un arco sin escaleta validada se detalla de nuevo; bucle terminado sin global → solo eso; completa → no hace nada. Siempre `/novela continuar <carpeta>`. Un paso a medias (`git status` sucio) se descarta con `descartar()` y se registra `paso_descartado`. **`descartar()` conserva antes lo que va a perder**: copia todo lo modificado o sin seguir a `novelas/<slug>/.descartado/<marca UTC>/`, con la misma ruta relativa, y solo después hace `reset` + `checkout` + `clean -fdq -e .descartado` `[harness · ambos]`. Si la copia falla, no descarta: PARADA `DESCARTE_NO_SEGURO`. `.descartado/` está en `.gitignore`, el harness nunca la lee ni la reutiliza, y borrarla no cambia ninguna novela: es material para que decida una persona (cierra A21; evidencia: E2, donde un `paso_descartado` se llevó un `intento-1.md` de 1.333 palabras).

Tras `PAUSA_PROGRAMADA` la reanudación va **en una sesión nueva**; el harness no la encadena `[harness · ambos]`.

### 6.3 Límites

| Límite | Comportamiento | Variable · defecto | Marca |
|---|---|---|---|
| Reescrituras por capítulo | Agotadas, mejor intento con aviso | `limites.reescrituras_max` · 2 | harness · ambos |
| Ajustes de longitud | Presupuesto aparte; agotado, la longitud vuelve a gastar reescritura | `limites.ajustes_longitud` · 2 | harness · ambos |
| Capítulos / palabras / capítulos por arco | Escaleta que lo viole vuelve al interrogador | perfil · `formato.capitulos_por_arco` · 15 | harness · ambos |
| Turnos por invocación | Agente que no entrega en N turnos incumple; resultado parcial = incumplimiento. Debe coincidir con `maxTurns` o `ERROR_CONFIGURACION` | `limites.turnos_por_invocacion` · 40 | cáscara · ambos (la cáscara aplica el mismo `maxTurns`) |
| Fallo técnico | Reintentos del mismo paso; después parada limpia | `limites.reintentos_tecnicos` · 3 | harness · ambos |
| Tamaño de la revisión global | Por encima, sobre resúmenes | `limites.revision_global_max_palabras` · 60.000 | harness · ambos |
| Presupuesto | Al superarlo, parada limpia. `null` desactiva | `limites.presupuesto_usd_max` · `null` | harness · **hito 2** (necesita coste real; con suscripción de Claude Code no hay coste por llamada y la variable es inerte) |
| Límite de uso de la suscripción | La cuota (de sesión o semanal) se agota a mitad del bucle. **No es un fallo técnico**: reintentar no lo arregla y gasta cuota. Parada limpia, con la hora de reinicio si el error la trae | no configurable: lo impone el proveedor | harness · **hito 1 (Claude Code)** |
| Pausa programada | Cada N capítulos, parada limpia para soltar contexto; se reanuda en sesión nueva | `limites.pausa_cada_capitulos` · 3 | harness · **ambos** (decisión 2026-09-18; compactación en la cáscara → A23) |

"Parada limpia": nada a medias marcado como válido, Estado con motivo, mensaje de cómo reanudar.

### 6.4 Progreso `[harness · ambos]`

Una línea por evento: arco y capítulo en curso y totales, intento, veredicto con motivo resumido y desglose por revisor, y cualquier aviso (longitud, agotamiento, discrepancia, incumplimiento). Publicar en el informe de cierre problemas por revisor y reparto problema/observación: → A5.

### 6.5 Fallos `[harness · ambos]`

Principio: **nunca muere en silencio ni deja el estado a medias.** Toda ejecución acaba con informe de cierre (mostrado y guardado): resultado, motivo clasificado, etapa/arco/capítulo, qué quedó hecho, avisos, métricas (§8.3), volumen (§6.6) y **la acción exacta para continuar**. `/novela estado <carpeta>` resume el Estado sin abrir ficheros.

| Motivo | Qué ha pasado | Qué hace el harness | Usuario |
|---|---|---|---|
| Fallo técnico transitorio | Agente falla, vacío o cortado | Hasta `reintentos_tecnicos`; en revisión, **solo el revisor que falló** | Nada |
| Fallo técnico persistente | Todos los reintentos fallan | Parada limpia con el error | `/novela continuar` |
| Agente incumple contrato | Forma inesperada o turnos agotados | Como fallo técnico, indicando el incumplimiento. Si se repite entre novelas, es del prompt y va al CHANGELOG | Relanzar |
| Escaleta fuera de límites | Propuesta o arco fuera de límites | Devolver hasta `escaleta_rechazos_max`; después parada | Relajar límites o idea |
| `ESPERA_APROBACION` | Propuesta lista sin usuario en la sesión | Parada con biblia y escaleta sin `aprobada: true` | Decidir (estudio o `decision.md`) y continuar |
| `PAUSA_PROGRAMADA` | N capítulos cerrados | Parada limpia | Continuar en sesión nueva |
| `LIMITE_DE_USO` (hito 1) | El proveedor rechaza la invocación por cuota de suscripción agotada | Parada limpia **sin gastar reintentos técnicos**: el paso en curso se descarta como una interrupción del usuario (§6.2) y el informe de cierre dice desde dónde se reanuda | Esperar al reinicio de la cuota y `/novela continuar <carpeta>` |
| Presupuesto agotado (hito 2) | Coste > `presupuesto_usd_max` | Parada tras cerrar el paso | Subir y relanzar |
| Error de configuración | Sin git, faltan ficheros, `maxTurns`/`model` ≠ config, `version` distinta | Parada antes de invocar a nadie | Corregir |
| `COMMIT_NO_LIMPIO` | Tras `commitear()`, `HEAD` no avanzó o `git status --porcelain` no quedó vacío | Parada inmediata, sin avanzar al paso siguiente. El trabajo sigue **entero en disco**, sin commitear | `/novela continuar`: el paso se descarta conservándolo en `.descartado/` y se repite |
| `DESCARTE_NO_SEGURO` | `descartar()` no pudo copiar a `.descartado/` lo que iba a borrar | Parada **sin descartar nada**: no destruye sin copia de seguridad | Liberar espacio o permisos y `/novela continuar` |
| `ESTADO_NO_RECONOCIDO` | `estado.json` ilegible o versión desconocida | Parada señalando el último commit consistente | Revisar |
| Interrupción del usuario | Corte | Paso en curso descartado | Relanzar |

Nunca hace falta borrar nada a mano ni editar el Estado.

### 6.6 Volumen: el dato para decidir el modelo

Cada fila `invocacion` lleva `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida`, `coste_usd`; se rellena lo disponible `[harness · ambos]`:
- **Hito 1**: `pal_*` con `wc -w` (ficheros que el prompt manda leer; lo entregado). La herramienta `Agent` **no devuelve tokens** ni coste `[CC]`. `modelo` registra el **pedido**, no el que atendió: `Agent` no lo dice; defensas: `model` del frontmatter y `comprobar_entorno` `[CC]`.
- **Hito 2**: la respuesta de OpenRouter trae tokens, coste y modelo que respondió; la cáscara los devuelve en el resultado de `Agent` (§10.2) y el harness los copia. `pal_*` se sigue rellenando para comparar.

En el informe de cierre, suma por agente y modelo, **recontada desde `registro.md`** → A10. Referencias: 403.727 / 77.066 palabras en la referencia con opus; 164.426 / 33.742 con haiku (E1, E3).

---

## 7. Variables configurables — `config.json`

Todo lo ajustable vive en [`config.json`](../config.json), único fichero que el usuario edita. Al crear una novela se **congela** en `novelas/<slug>/config.json` con el perfil resuelto. Tamaños bloqueados al aprobar la escaleta; el resto cambiable al reanudar con `<clave>=<valor>` `[harness · ambos]`.

`config.json` está en la **versión 4**; `nueva` y `continuar` la exigen; `estado` y `verificar` aceptan también la 3 `[harness · ambos]`. Subirla a 5 con el arrastre de la 0.8.0: → A1, A2.

### 7.1 Perfil activo y tamaño

| Perfil | Capítulos (obj · min–max) | Palabras/cap | Arcos |
|---|---|---|---|
| `relato` | 3 · 1–5 | 1.500 | 1 |
| `novela_corta` | 12 · 8–15 | 2.000 | 1 |
| `novela` | 30 · 20–40 | 2.500 | 2–3 |
| `saga` | 100 · 60–200 | 2.500 | 4–14 |

`relato` bajó de 5 · 3–8 a 3 · 1–5 (2026-09-19) para que una vuelta completa del harness cueste lo menos posible. Consecuencia: **la línea base E1 se midió a 5 capítulos**, así que una ejecución de 3 no es comparable con ella ni con los umbrales de §7.7. Para comparar, sobreescribe el tamaño en el comando (`perfiles.relato.capitulos_objetivo=5`), no en el fichero.

Campos: `capitulos_objetivo`, `capitulos_min/max` (límites duros), `palabras_por_capitulo` (variable por capítulo entre suelo y techo), `paginas_objetivo` (alternativa: `capitulos = redondeo(paginas × palabras_por_pagina ÷ palabras_por_capitulo)`; nunca usada → A20), `resumenes_completos_ultimos` (`null` en `relato` y `novela_corta`, 10 en `novela` y `saga`; **hoy está en `memoria`, no en el perfil** `[pendiente → A2]`), `descripcion`.

### 7.2 Formato

| Variable | Defecto | Qué hace |
|---|---|---|
| `formato.palabras_por_pagina` | 250 | Conversión páginas ↔ palabras |
| `formato.palabras_min_capitulo` / `max` | 800 / 5.000 | Suelo y techo absolutos |
| `formato.tolerancia_longitud` | 0.2 | Margen del harness (±20 %). A `0` fuerza rechazos deterministas (criterio 3 de §8.2). Asimétrica → A11 |
| `formato.capitulos_por_arco` | 15 | Tamaño máximo de arco. Con un total ≤ este número hay **un solo arco**: la escaleta se entrega entera en la propuesta y `revisar_arco` colapsa en la global (§4.2). En `relato` y `novela_corta` el valor es inerte |

### 7.3 Proveedor y modelos

`proveedor`: `"claude-code"` (hito 1) u `"openrouter"` (hito 2). Con `claude-code`, `modelos.*` son alias de `Agent` (`opus`, `sonnet`, `haiku`, `fable`); con `openrouter`, identificadores de OpenRouter, y hace falta una **tabla de alias** para que el `model` del frontmatter siga cuadrando con `config.json` → A16.

| Variable | Defecto | Qué hace |
|---|---|---|
| `modelos.interrogador/escritor/resumidor/revisor_encargo/revisor_continuidad` | `haiku` | Modelo de cada agente. Subir `escritor` cambia la prosa; `revisor_continuidad`, la coherencia; `resumidor`, la memoria |
| `modelos.temperatura.*` | escritor 0.9 · interrogador 0.7 · resto 0.0 | **Hito 2 solo**: `Agent` no la expone `[CC no; cáscara sí]` |
| `modelos.escalado.activo/modelo/escritor_desde_intento/revisor_desde_intento/tras_fallo_tecnico/revision_arco_y_global` | `false` · `opus` · 2 · 3 · `true` · `true` | Subir de modelo donde compensa. En `false` se ignora todo |
| `modelos.orquestador` | — | **Hito 2 solo, no existe aún**: modelo del orquestador LLM en la cáscara. En Claude Code el orquestador es la sesión y **no se configura aquí** → A16 |

Cada `modelos.<agente>` está escrito dos veces (aquí y en el frontmatter); `comprobar_entorno` compara y para si difieren. Para una sola ejecución, sobreescritura por comando.

Configuraciones de referencia: **mínima** = cinco en `haiku`, escalado apagado (defecto, hito 1). **Con red** = ídem con `escalado.activo: true`. **Validación** = cinco en `opus`, escalado apagado (línea base, E1). La evidencia hoy (E4): con haiku como revisor las métricas no discriminan; escritor barato con revisor caro es la combinación por probar → A19.

### 7.4 Límites

`limites.reescrituras_max` 2 · `ajustes_longitud` 2 · `reintentos_tecnicos` 3 · `escaleta_rechazos_max` 3 · `turnos_por_invocacion` 40 · `revision_global_max_palabras` 60000 · `presupuesto_usd_max` `null` (hito 2; inerte con suscripción) · `pausa_cada_capitulos` 3 (`null` desactiva) · `entrada_max_palabras_invocacion` 25000 `[pendiente]`. Comportamiento en §6.3.

### 7.5 Regla de veredicto

| Variable | Defecto | Qué hace | Marca |
|---|---|---|---|
| `veredicto.rechaza_con_graves` | 1 | Problemas de gravedad 1–2 (contradicción o incumplimiento) que bastan para RECHAZADO. Es la clave que hay en `config.json` y la que lee `procedimientos/capitulo.md` | harness · ambos |
| `veredicto.rechaza_con_leves` | 2 | Problemas de gravedad 3–5 que bastan | harness · ambos |
| separarla en `rechaza_con_gravedad_1` / `_2` | 1 · 2 | Umbral distinto para contradicción y para incumplimiento | pendiente → A2 |

Hoy `config.json` tiene `rechaza_con_graves: 1` sobre {1,2}. Motivo del cambio: una contradicción entra en el libro de estado y envenena lo que sigue; un suceso a medias se queda en su capítulo y `erratas.md` le da salida (E2). Lo que **no** arregla: el 0 de 5 de aprobados al primer intento (E2). No calibrar con informes de haiku hasta saber si haiku discrimina (E3, E4) → A19.

### 7.6 Memoria

| Variable | Defecto | Qué hace | Marca |
|---|---|---|---|
| `resumenes_completos_ultimos` | por perfil | Resúmenes íntegros para escritor y revisor de continuidad | pendiente (hoy `memoria.resumenes_completos_ultimos: null`) |
| `memoria.resumen_max_palabras` | 350 | Techo del resumen, `wc -w` | pendiente |
| `memoria.hoja_continuidad_max_palabras` | 200 | Techo de la hoja | pendiente |
| `memoria.capitulo_anterior_integro` | `true` | Capítulo anterior completo al escritor | harness · ambos |
| `memoria.libro_estado_max_palabras` | 4000 | Techo orientativo; el harness avisa | harness · ambos |
| `limites.entrada_max_palabras_invocacion` | 25000 | `comprobar_entorno` proyecta la entrada del último capítulo y **avisa**, no para | pendiente |

Evidencia: E2 (sin tope, la entrada del escritor se multiplica por 3,7 en cinco capítulos; `saga` es inviable por el resumidor, no por el modelo).

### 7.7 Calidad

| Variable | Defecto | Métrica |
|---|---|---|
| `calidad.max_graves_por_10_capitulos` | 2 | Graves en arco y global por 10 capítulos |
| `calidad.max_agotamiento_pct` | 20 | % capítulos por agotamiento |
| `calidad.max_hilos_previstos_sin_cerrar` | 0 | Hilos previstos abiertos al final |
| `calidad.min_aprobados_primer_intento_pct` | 40 | % aprobados en el intento 1 (suelo provisional) |
| `calidad.max_rechazos_voz_pct` | 20 | % intentos con gravedad 4 |

Recalibrados con la referencia (E1): a 5 capítulos, 1 y 10 exigían cero. **Con el `relato` de 3 capítulos casi no se pueden cumplir**: un solo problema grave son 3,3 por 10 capítulos (umbral 2) y un solo capítulo cerrado por agotamiento es el 33 % (umbral 20). A ese tamaño las métricas valen para leer el detalle, no para aprobar o suspender; no bajes los umbrales para que salgan verdes. **Limitación declarada:** cuatro de las seis métricas dependen de lo que el revisor declare; un revisor peor sube la nota (E4: B saca 5/5 y es peor novela). Miden el harness, no la novela → A5. Recalibrar con la segunda ejecución controlada → A22.

### 7.8 Escalar el proyecto

| Paso | Qué | Configuración | Estado |
|---|---|---|---|
| 1. Validar el diseño | `relato`, agentes en `opus` | `modelos.*: opus` | **Hecho** (E1) |
| 2. Abaratar | Mismo caso, cinco en `haiku`; comparar con 1 | defecto | **Ejecutado, no decidido**: B pasa las métricas y no la lectura; la comparación no está controlada (spec v3 frente a v4) (E4) → A19 |
| 3. Cáscara | Ejecutar el mismo harness en la cáscara de §10 con `proveedor: openrouter` | `modelos.*` con ids de OpenRouter, `modelos.orquestador` | **Pendiente**; diseño en §10 |
| 4. Crecer | `novela_corta` → `novela` en la cáscara; arcos y memoria | `perfil_activo`, `memoria.*` | Configuración |
| 5. `saga` | 100–200 capítulos | `perfil_activo: saga` | Configuración |

---

## 8. Verificación

### 8.1 Modo de prueba y caso de referencia `[harness · ambos]`

`entrevista: <ruta>` toma una entrevista cerrada; el usuario sigue confirmando. `modo-prueba: <carpeta>` toma idea y entrevista y **aprueba la escaleta sola** si cumple los límites; solo para verificar; el Registro lo anota. `pruebas/referencia/` es la entrada fija de toda comparación; cambiarla invalida las anteriores y va al CHANGELOG.

### 8.2 Criterios de aceptación

Los ejecuta el orquestador sobre el caso de referencia en modo de prueba y comprueba leyendo la carpeta.

1. **Novela completa** con ÉXITO y todos los artefactos de §3; cada capítulo aprobado en tolerancia (`wc -w`).
2. **Interrogatorio** en modo de prueba sin preguntar; escaleta en límites y fiel a la entrevista.
3. **Rechazo y reescritura** con `tolerancia_longitud: 0`: rechazo sin invocar a nadie; los dos primeros consumen ajuste, los siguientes reescritura; al agotarse, mejor intento (el más cercano) con aviso.
4. **Reanudación** tras interrumpir en el capítulo 2: capítulo 1 y libro de estado idénticos byte a byte (git); novela completa al final.
5. **Turnos agotados**: `maxTurns` bajo → 3 reintentos, parada INCUMPLE CONTRATO, continuar termina. `maxTurns` ≠ config → ERROR_CONFIGURACION antes de invocar.
6. **Inmutabilidad** comprobada con git: biblia, escaleta y capítulos aprobados idénticos; libro de estado solo cambia en cierres.
7. **Registro**: reconstruible por capítulo; invocaciones = Estado.
8. **Reanudación tras parada**: nada aprobado se regenera.
9. **Comando de estado** coherente con el Estado.
10. **Salida mal formada** de un revisor → incumplimiento y repetición; ningún informe inválido en disco.
11. **Arcos** con `capitulos_por_arco: 2`: 3 arcos, detalle al llegar, informe por arco, el arco 2 recibe el informe del 1.
12. **Dos revisores**: dos invocaciones por intento con entradas distintas; unión con origen; reintento solo del que falla.
13. **Validación del canon**: biblia sembrada con una edad que no cuadra → señalada, devuelta, la aprobada no la contiene.
14. **Mejor intento por cierres**: entre dos empatados en graves, gana el que cierra el hilo previsto; el Registro dice que decidió el paso 2.
15. **Erratas**: existen con cita literal presente; ningún capítulo aprobado cambia (git).
16. **Hoja de continuidad** verificable campo a campo contra sus fuentes; `desconocido` si falta el dato `[pendiente]`.
17. **Tope del resumen**: ninguno lo supera salvo aviso; una sola reinvocación `[pendiente]`.
18. **Proyección de entrada**: `novela` con `null` → aviso y la ejecución **continúa** `[pendiente]`.
19. **Commit comprobado**: suprimido el commit de `cerrar_capitulo`, la ejecución para con `COMMIT_NO_LIMPIO` en ese mismo capítulo —no en el siguiente— y el capítulo sigue entero en disco.
20. **Descarte reversible**: interrumpido un intento a medias, `/novela continuar` deja en `.descartado/<marca>/` una copia byte a byte de lo borrado, con su ruta relativa; `git status --porcelain` queda vacío y `.descartado/` no entra en git.

Estado real: ninguno se ejecuta de forma automatizada; 3, 4, 5, 10, 11, 13, 14 y 16–20 no se han ejercitado nunca (E3 confirma que 14 no se llegó a evaluar; 19 y 20 son nuevos de 2026-09-19). Guion de comprobación → A3.

### 8.3 Métricas de calidad — de **proceso** `[harness · ambos]`

**Autoinformadas**: se calculan solo de informes y Estado, es decir, de lo que los revisores declararon. Cuatro de las seis dependen de eso (E5c), y por eso pueden dar `6/6 CUMPLE` sobre un manuscrito con 30 defectos reales. Miden cómo fue el proceso, no cómo quedó el texto: para eso está el validador de **producto** de §9.6, que lee el manuscrito. Las dos conviven y ninguna manda sobre la otra; cada informe dice de dónde sale su número.

"Suficientemente buena" = **coherente**, **cohesionada**, **fiel a lo pedido**:

| Métrica | Cómo | Mide |
|---|---|---|
| Graves por 10 capítulos | Gravedad 1 en arco y global ÷ capítulos × 10 | Coherencia |
| Aceptados por agotamiento | % con `por_agotamiento` | Adherencia |
| Hilos previstos sin cerrar | `hilos_cierra` de la escaleta abiertos en el libro de estado final | Cohesión |
| Aprobados en el primer intento | % con `aprobado: 1` | Adherencia |
| Rechazos por voz | % intentos con gravedad 4 | Voz |
| Desviación de longitud | Media de \|palabras − objetivo\| ÷ objetivo sobre aprobados | Adherencia |
| Desviación **con signo** | Media de (palabras − objetivo) ÷ objetivo sobre todos los intentos | Sesgo del escritor. **Falta en `final.md`** → A10 |

Cada una contra su umbral (§7.7): CUMPLE / NO CUMPLE. Regla de comparación: una novela barata "aguanta" si cumple todas las que cumplió la de referencia; **vacía cuando la referencia cumple cero** (E4) → A6.

Señales sin umbral que conviene mirar: graves que aparecen en el intento 1 y desaparecen en el 2; pocas `discrepancia_veredicto`; tres hechos del capítulo 1 comprobados en el libro de estado final. Métrica informativa de lengua (errores por mil palabras): → A5.

### 8.4 Comparar dos ejecuciones

**Retirada** (2026-09-19). `/novela comparar <caso>` y la carpeta `comparativa/` ya no existen: el motivo está en el CHANGELOG 0.11.0. La evidencia que produjo se conserva en [technical.md → E4](technical.md#e4). Para comparar dos ejecuciones hoy: §8.3 (proceso) y §9.6 (producto, con línea base congelada). Donde el resto de la spec diga «la lectura (§8.4)», léase el bloque de lectura del informe de §9.6.

### 8.5 La ejecución de referencia

Movida a [technical.md → E1](technical.md#e1). Léela antes de tocar las reglas de §4.2.

### 8.6 Diagnóstico de volumen

Movido a [technical.md → E2](technical.md#e2).

### 8.7 Comprobar que una ejecución está completa `[harness · ambos]`

Lo ejecuta `/novela verificar <carpeta>`, de lo barato a lo caro:

1. `informe-cierre.md` dice `resultado: EXITO`.
2. `estado.json`: `version: 4`, `etapa: completa`, `informe_global: true`, una entrada por capítulo de `escaleta.md`, `escaleta_validada` en todos los arcos.
3. Existen `biblia.md` y `escaleta.md` con `aprobada: true`, un `arco-AA.md` con `validada: true` por arco, `libro-estado.md` con `hasta_capitulo` = total, `manuscrito.md`, `informe-global.md`, `erratas.md`; con más de un arco, un `informe-arco-AA.md` por arco. La biblia tiene «Cronología y datos fijos» con contenido.
4. Por capítulo N: `intento-K`, `resumen-K`, `libro-estado-K` e `informe-K` para la K aprobada, con `veredicto: APROBADO` o `por_agotamiento: true`.
5. `wc -w` de cada aprobado en tolerancia.
6. `git log -- novelas/<slug>` con los commits esperados y `git status --porcelain` vacío.

Después, si completa, `calcular_metricas`. Si algo falla, `informe-cierre.md` dice motivo y acción; nunca se repara a mano. Vale igual para una carpeta generada por la cáscara.

---

## 9. Dónde está implementado

**Esta sección vive ahora en [technical.md](technical.md), con la misma numeración `§9.x`.** Sigue siendo normativa; solo ha cambiado de fichero. Allí están: el mapa de qué regla vive en qué fichero (§9), cómo se escribe el orquestador (§9.1), el visor (§9.2), las seis reglas de observabilidad (§9.3), el estudio (§9.4), el bucle `/optimizar` (§9.5) y el validador `/validar` (§9.6).

---

## 10. Hito 2 — La cáscara contra OpenRouter

Decisión del 2026-09-18: el hito 2 **no es un runner en código** que reimplemente SKILL.md; es un **orquestador LLM** (barato, servido por OpenRouter) leyendo **el mismo SKILL.md**, dentro de una cáscara propia que le da lo que Claude Code le da hoy. Revierte la 0.4.0 (consolidación §5). Consecuencia aceptada: el riesgo "lo mecánico lo hace un modelo con cuidado" (E3) **no desaparece y se agrava** con un orquestador barato; la mitigación compatible es que lo mecánico sea guiones que SKILL.md llama por Bash en los dos hitos → A3.

### 10.1 Qué se porta byte a byte

| Pieza | Dónde | En la cáscara |
|---|---|---|
| `SKILL.md` y `procedimientos/` | `.claude/skills/novela/` | El system prompt del orquestador es el mismo texto. Las referencias a herramientas (`Read`, `Write`, `Edit`, `Bash`, `Agent`) resuelven contra las de la cáscara |
| Contratos de los agentes | `.claude/agents/*.md` | System prompt de cada subagente; `tools`, `maxTurns`, `model` se leen del mismo frontmatter |
| Plantillas | `plantillas/` | Idénticas |
| `config.json` y perfiles | raíz | Idéntico; `proveedor: openrouter`, `modelos.*` con ids de OpenRouter vía alias (→ A16), `modelos.orquestador` nuevo |
| Permisos y hooks | `.claude/settings.json`, `.claude/hooks/inmutables.sh` | La cáscara lee `permissions.allow/deny` y `hooks.PreToolUse` del mismo fichero y ejecuta el mismo guion con el mismo JSON por stdin. Exige `sh` |
| Carpeta de la novela, Estado, Registro, motivos de parada | plantillas, `cierre.md` | Idénticos: `/novela estado`, `verificar`, el visor y el exportador funcionan sin saber quién generó |
| Estudio salvo el lanzamiento | `frontend/` | Idéntico; `harness.mjs` cambia el binario que arranca |
| Exportador y evaluadores | `herramientas/` | Idénticos |

### 10.2 Qué implementa la cáscara

| Pieza | Cómo lo hace Claude Code | La cáscara |
|---|---|---|
| Bucle agéntico del orquestador | La sesión | Conversación con `modelos.orquestador` vía OpenRouter: system = SKILL.md + CLAUDE.md, herramientas abajo, hasta que el modelo termina el turno |
| `Read`, `Glob`, `Grep` | Nativas | Mismos nombres y semántica sobre la raíz del repositorio |
| `Write`, `Edit` | Nativas + hook | Mismos nombres; **escritura atómica** (temporal + renombrado); antes de ejecutar, pasa por `PreToolUse` (abajo) |
| `Bash` | Nativa, con `permissions` | Ejecuta en la raíz; solo comandos que casen con `permissions.allow` (prefijos) y no con `deny`; lo demás se deniega y el harness para limpio. Sin prompts de permiso |
| `Agent` | Subagentes | Lee `.claude/agents/<name>.md`; bucle propio con `Read/Glob/Grep`, `maxTurns` del frontmatter, `model` del parámetro (o del frontmatter si falta), `temperatura` de `config.json`; devuelve el mensaje final **más** `tok_entrada`, `tok_salida`, `coste_usd` y `modelo_respondido` de OpenRouter, para que el harness los copie al registro (§6.6). Siempre bloqueante: no existe segundo plano, así que la fila `pendiente` (→ A9) desaparece |
| `PreToolUse` | `settings.json` → `inmutables.sh` | Mismo matcher `Edit\|Write`, mismo comando, mismo JSON (`tool_name`, `tool_input.file_path`), mismo código de salida 2 = bloqueo. Falla en abierto igual |
| `PreToolUse` | `settings.json` → `rutas-protegidas.sh` | Mismo matcher `Bash`, mismo comando, misma entrada cruda, mismo 2 = bloqueo. Falla en **cerrado** igual |
| `permissions.deny` de `Read` | Nativo, **solo sobre `Read`** | Mismas rutas; lo que `Bash` lee lo corta `rutas-protegidas.sh`, no el `deny` |
| `maxTurns` | Frontmatter | Ídem; resultado parcial marcado como tal |
| Sesión y `--resume` | Nativo | Transcript de la conversación del orquestador en `encargos/<slug>/` o en un directorio propio; `--resume <id>` la retoma. Solo hace falta para la entrevista a medias: el resto se reanuda desde disco |
| `AskUserQuestion` | Denegada por el estudio | No existe: el orquestador pregunta en texto |
| Skill `grilling` | Plugin de Claude Code | **No está**: → A17 |
| Git | Bash | Bash |
| Contexto | `pausa_cada_capitulos` | Igual (§6.3). Compactación propia → A23 |
| Observabilidad | Hook `Stop` + exportador | Instrumentación nativa con el SDK de Langfuse (tokens y coste por invocación, atribuidos) + el mismo exportador. Fuera del bucle, fail-open |
| Lenguaje y librerías | — | **Sin decidir** → A15 |

### 10.3 Protocolo de sesión

La cáscara habla con el estudio (y con cualquier terminal) por **NDJSON en stdin/stdout**, con el subconjunto de `stream-json` que `harness.mjs` consume hoy, para que el estudio funcione contra los dos hitos cambiando solo el binario:

| Dirección | Mensaje | Campos que el estudio usa |
|---|---|---|
| salida | `{"type":"system","subtype":"init","session_id":"…"}` | `session_id`, que el estudio persiste para `--resume` |
| salida | `{"type":"assistant","message":{"content":[{"type":"text","text":"…"},{"type":"tool_use","name":"…"}]}}` | texto para el usuario; nombre de herramienta para el progreso |
| salida | `{"type":"result","subtype":"ok\|…"}` | fin de turno: si estaba entrevistando, toca al usuario; si generando, paró o acabó (lo dice `estado.json`) |
| entrada | `{"type":"user","message":{"role":"user","content":[{"type":"text","text":"…"}]}}` | el comando `/novela …` o la respuesta del usuario |
| flags | `--print --input-format stream-json --output-format stream-json --verbose --permission-prompts none --disallowed-tools AskUserQuestion [--resume <id>]` | Los mismos que hoy |

Todo lo que no esté en esta tabla el estudio lo ignora o lo pinta como `crudo`. `stderr` → `aviso`.

### 10.4 Contrato de la cáscara

La cáscara está bien si, sobre el caso de referencia:
1. Con **los mismos ficheros** de `.claude/`, `config.json` (`proveedor: openrouter`) y plantillas, produce `novelas/<slug>/` que pasa §8.7 sin adaptación.
2. `/novela estado` y `verificar` desde Claude Code, el visor y el exportador funcionan sobre esa carpeta.
3. Los criterios de §8.2 se cumplen; los de sesión (5, interrupción) se traducen a `maxTurns` propio y señal de parada.
4. `inmutables.sh` bloquea exactamente los mismos 28 casos que en Claude Code (E7), ejecutado por la cáscara.
5. El estudio arranca y dialoga con ella por §10.3 sin cambiar nada salvo el binario.
6. `registro.md` lleva `tok_*`, `coste_usd` y el modelo que respondió en cada `invocacion`, y `presupuesto_usd_max` para de verdad.
7. Con la misma configuración de agentes que el paso 2 de §7.8, las métricas de §8.3 quedan dentro de los mismos umbrales **y** la lectura (§8.4) no empeora.

Lo que **no** se decide aquí: lenguaje (A15), modelo del orquestador y alias (A16), sustituto de `grilling` (A17), compactación (A23). Lo que sí queda fijado: la cáscara no altera ningún contrato de este documento; si algo no funciona en ella, se cambia aquí primero.
