# story-maker — Especificación funcional

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. El usuario aporta una idea; cuatro agentes (interrogador, escritor, resumidor, revisor) coordinados por un **harness** la convierten en una novela completa.

El proyecto tiene **dos hitos** y este documento vale para los dos:

1. **Hito 1 — Validar el diseño en Claude Code, con el modelo caro.** El harness es una skill orquestadora, cuatro subagentes y un conjunto de reglas, todo en Markdown dentro del repositorio; no hay programas propios. Claude ejecuta el flujo en la sesión cuando el usuario lanza `/novela`. Se prueba con historias pequeñas (perfil `relato`, 5 capítulos) para ver qué da el diseño cuando el modelo no es el cuello de botella.
2. **Hito 2 — Llevar ese mismo diseño a un runner propio contra OpenRouter, con un modelo barato,** para generar novelas de 100–200 capítulos sin sesión interactiva. El runner es código (§10); los contratos, artefactos, límites y configuración son **los mismos** que aquí. Lo que se valida en el hito 1 es lo que se porta en el 2.

Vocabulario: **hito** = fase del proyecto (1: Claude Code, 2: runner). **Etapa** = fase del flujo de una novela (1: interrogatorio, 2: bucle por capítulo, 3: final). No se usa la palabra "fase" en este documento para evitar la confusión.

La carpeta de la novela es el único estado, en los dos hitos. Este documento describe **qué** hace el sistema y cómo se comportan sus partes. Dónde está implementada cada pieza: §9. Qué puedes ajustar sin tocar nada del harness: §7 y [`config.json`](../config.json). Qué hay que reimplementar para el hito 2 y qué no: §10.

Historial de cambios y motivos: [CHANGELOG.md](../CHANGELOG.md).

---

## 0. Glosario

Términos que este documento usa con un sentido preciso. Si una palabra aparece aquí, en el resto de la spec, en la skill, en los agentes y en el runner significa exactamente esto.

### 0.1 El proyecto

| Término | Qué es | Para qué sirve |
|---|---|---|
| **Harness** | El orquestador: la pieza que llama a los agentes en orden, guarda el estado, impone los límites y toma todas las decisiones de flujo. En el hito 1 es Claude ejecutando la skill `/novela`; en el hito 2 es un programa | Es lo que convierte cuatro prompts sueltos en un sistema que produce una novela completa sin supervisión y que se puede reanudar |
| **Agente** | Un prompt con un contrato (entradas, salida, debe, no debe) que se ejecuta con un modelo. Hay cuatro: interrogador, escritor, resumidor y revisor | Cada uno hace una sola cosa. Separarlos permite darles distinto modelo, distinto contexto y juzgarlos por separado |
| **Contrato** | Lo que un agente recibe, lo que devuelve y con qué forma, y lo que tiene prohibido hacer (§5) | Es lo que se porta sin cambios al runner y lo que el harness verifica en cada invocación |
| **Invocación** | Una llamada a un agente con unas entradas concretas, que termina con una salida o con un fallo | Es la unidad que se registra, se reintenta y cuyo volumen se mide |
| **Hito** | Fase del proyecto. Hito 1: validar el diseño en Claude Code con el modelo caro. Hito 2: runner propio contra OpenRouter con un modelo barato | Separa "¿funciona el diseño?" de "¿aguanta el modelo barato?" |
| **Etapa** | Fase del flujo de una novela. Etapa 1: interrogatorio. Etapa 2: bucle por arco y capítulo. Etapa 3: final | Es lo que guarda el Estado para saber dónde reanudar |
| **Runner** | El programa del hito 2 que implementa el harness en código contra OpenRouter | Permite el bucle desatendido de 100–200 capítulos que una sesión de Claude Code no puede sostener |
| **Perfil** | Un conjunto de valores de tamaño de la novela: capítulos, palabras por capítulo. Hay cuatro: `relato`, `novela_corta`, `novela`, `saga` | Cambiar `perfil_activo` es lo que escala el proyecto sin tocar nada más |
| **Escalado (de modelo)** | Subir a un modelo mejor en situaciones concretas: reescritura tras rechazo, último intento, reintento tras fallo, revisiones de arco y global | Gastar el modelo caro solo donde compensa |
| **Modo de prueba** | Ejecución en la que las respuestas de la entrevista salen de un fichero y la escaleta se aprueba sola | Verificar el harness sin una persona delante |
| **Caso de referencia** | Una idea y una entrevista fijas en `pruebas/referencia/` | Comparar configuraciones distintas sobre la misma historia; sin él, cada comparación sería entre historias distintas |

### 0.2 Los artefactos de una novela

Todo lo que se genera vive en `novelas/<slug>/`. Por orden de aparición:

| Término | Qué es | Para qué sirve |
|---|---|---|
| **Idea** | Una o dos frases del usuario con el punto de partida | Es la semilla; se guarda literal para saber qué se pidió |
| **Entrevista** | Las preguntas del harness al usuario y sus respuestas, con lo que eligió él y lo que dejó en "decide tú" | Fija las decisiones que cambian la novela antes de escribir nada. Es la única entrada del interrogador junto a la idea |
| **Biblia** | El documento de referencia de la novela: premisa, tono y estilo, cómo es el mundo post-IA de esta historia y qué reglas rigen, personajes con arco, motivación y voz, y las reglas internas que la historia no puede romper | Es la ley. Todos los agentes la reciben y el revisor juzga contra ella. Inmutable tras la aprobación del usuario. El nombre viene del "show bible" de las series de televisión |
| **Escaleta** | El plan de la novela, capítulo a capítulo, antes de escribirla. Aquí tiene dos niveles: la de **alto nivel** y la de cada **arco** | Da a cada capítulo un objetivo propio y evita que el escritor invente la trama sobre la marcha. El nombre es el término del guion audiovisual para el esquema de escenas |
| **Escaleta de alto nivel** | Tres actos, divididos en arcos. Para cada arco: rango de capítulos, objetivo, sucesos clave que deben ocurrir y hilos que abre y cierra. Total de capítulos | Es lo que aprueba el usuario y lo que queda inmutable. Cabe en una lectura aunque la novela tenga 200 capítulos |
| **Acto** | Cada una de las tres partes clásicas: planteamiento, nudo y desenlace | Estructura mínima que garantiza que la historia arranca, se complica y se resuelve |
| **Arco** | Un tramo de la novela de como mucho `capitulos_por_arco` capítulos (15 por defecto), con objetivo propio dentro de un acto. Una novela de 5 capítulos tiene un solo arco; una de 100, siete o más | Es la unidad de planificación detallada y de revisión intermedia. Permite que el detalle del arco 9 conozca lo que realmente pasó en los arcos 1 a 8 |
| **Escaleta de arco** | Una entrada por capítulo del arco: título provisional, objetivo, sucesos clave, personajes, gancho de cierre y longitud objetivo | Es lo que recibe el escritor para saber qué debe pasar en el capítulo N y qué no debe adelantar. Se genera al llegar al arco |
| **Entrada (de escaleta)** | La ficha de un capítulo concreto dentro de la escaleta de arco | Es la "orden de trabajo" del escritor y la vara de medir del revisor (criterio 2) |
| **Gancho** | La última nota de un capítulo, prevista en la escaleta, que empuja a leer el siguiente | Mantiene la tensión entre capítulos y da al revisor algo concreto que comprobar |
| **Hilo** | Una línea argumental, pregunta o promesa que la novela abre y debe cerrar más adelante: un misterio, un conflicto, una relación | El principal síntoma de incoherencia en novelas largas es un hilo abierto que nadie cierra. Por eso se registran con capítulo de origen y cierre previsto |
| **Capítulo** | Unidad de texto de la novela, de la longitud que fija su entrada de escaleta | Es la unidad del bucle: se escribe, se resume, se revisa y se aprueba de uno en uno |
| **Intento** | Cada versión de un capítulo. El intento 1 es el original; los siguientes, reescrituras tras un rechazo. Máximo 3 por defecto | Se conservan todos; el aprobado se marca en el Estado. Permite comparar qué cambió entre versiones |
| **Reescritura** | Un intento nuevo del mismo capítulo, hecho con el informe de rechazo del anterior como entrada | Es el mecanismo de corrección. Cuando se agotan, se acepta el mejor intento |
| **Resumen** | Lo que pasa en un capítulo aprobado, en forma estructurada: hechos, cambios de estado de personajes, hilos abiertos y cerrados, cosas introducidas | Es la memoria a corto plazo: el escritor recibe los últimos N en vez de los capítulos completos. Lo escribe el resumidor a partir solo del texto |
| **Libro de estado** | La foto de la novela tras el último capítulo aprobado: dónde está cada personaje, qué sabe, en qué estado queda; hilos abiertos y cerrados; objetos, lugares y datos introducidos; reglas del mundo en vigor | Es la memoria a largo plazo. Tiene tamaño constante aunque la novela tenga 200 capítulos, y es contra lo que el revisor comprueba las contradicciones (criterio 1) |
| **Informe (de capítulo)** | El veredicto sobre un intento, APROBADO o RECHAZADO, con la lista de problemas concretos: dónde, qué, por qué | Es lo que decide si se avanza o se reescribe, y lo que el escritor recibe para corregir |
| **Veredicto** | APROBADO o RECHAZADO. Lo propone el revisor, pero el que vale es el que **recalcula el harness** a partir de los problemas y la regla de §7.5 | Que la decisión no dependa del humor del modelo sino de una regla fija |
| **Gravedad** | Número del 1 al 5 que clasifica cada problema: 1 contradicción con biblia o estado, 2 incumple la escaleta, 3 longitud (lo pone el harness), 4 voz o tono, 5 resumen infiel | Permite que la regla de veredicto sea numérica: un grave rechaza; hacen falta dos leves |
| **Aceptación por agotamiento** | Cuando se agotan las reescrituras y ningún intento fue aprobado, el harness se queda con el mejor y sigue adelante, dejándolo anotado | Que la novela no se bloquee por un desacuerdo entre agentes. Su frecuencia es una métrica de calidad |
| **Informe de arco** | Revisión de continuidad sobre todos los capítulos de un arco al cerrarse. Informativo | Detecta lo que no se ve capítulo a capítulo y alimenta la escaleta del arco siguiente |
| **Manuscrito** | La novela ensamblada: título, índice y los capítulos aprobados en orden | Es el producto final para el lector |
| **Informe global** | Revisión de continuidad sobre la novela completa al final. Informativo | Detecta hilos sin cerrar y contradicciones lejanas. Nadie reescribe a partir de él; es para el usuario |
| **Estado** | `estado.json`: etapa, arco, capítulo e intento en curso, capítulos aprobados, invocaciones, motivo de parada | Es lo que permite reanudar exactamente donde se quedó. Solo lo escribe el harness |
| **Registro** | `registro.md`: una fila por invocación y por decisión del harness, con modelo y volumen | Trazabilidad: reconstruir qué pasó, y datos para estimar el coste con otro modelo |
| **Informe de cierre** | Resultado de una ejecución: ÉXITO o PARADA, motivo, qué quedó hecho, métricas de calidad y qué hacer para continuar | Que el programa nunca termine en silencio |
| **Parada limpia** | Terminar sin dejar nada a medias marcado como válido, con el Estado actualizado y el motivo explicado | Garantiza que siempre se puede reanudar con el mismo comando |
| **Slug** | Nombre de carpeta de la novela derivado de la idea: minúsculas, sin acentos, con guiones | Identificador estable de la novela en disco y en los commits |

---

## 1. Alcance

### 1.1 Objetivo

A partir de una idea inicial del usuario, producir una novela completa —biblia, escaleta, capítulos aprobados y manuscrito ensamblado— con continuidad interna verificada, sin intervención humana desde la aprobación de la escaleta hasta el final.

### 1.2 Decisiones fijas

| Aspecto | Decisión |
|---|---|
| Género | Fijo: ficción especulativa sobre el mundo posterior a la revolución de la IA |
| Universo | Cada novela inventa su propio mundo post-IA. No existe canon compartido entre novelas |
| Idioma | Castellano, en todo: interrogatorio, artefactos internos y novela |
| Interacción | Hito 1: sesión de Claude Code, comando `/novela`; conversacional durante el interrogatorio, solo progreso después. Hito 2: el runner toma la entrevista de un fichero y corre desatendido (§10) |
| Ejecución | Hito 1: Claude Code con subagentes, sin programas ni librerías propias. Hito 2: runner propio contra OpenRouter que implementa este mismo contrato |
| **Quién escribe en disco** | **Solo el harness.** Los agentes devuelven su salida en el mensaje final y el harness la escribe en la ruta que corresponde. Es igual en los dos hitos; así los contratos de los agentes (§5) se portan sin cambios |
| **Control determinista** | Todo lo que puede decidirse sin un modelo (contar palabras, recalcular el veredicto, validar la forma de una salida, actualizar el estado, elegir el mejor intento) lo hace el harness, nunca un agente. En el hito 1 el harness es Claude, pero usa herramientas mecánicas (`wc`, comparación de campos) para esas tareas |
| Escala | Hito 1: perfil `relato` (5 capítulos). Hito 2: hasta 200 capítulos (perfil `saga`), una sola novela con una sola trama, lo que exige la memoria de §7.6 y la escaleta por arcos de §4.1 |

### 1.3 No objetivos

Quedan explícitamente fuera:

- Formatos de salida distintos de Markdown (sin PDF, DOCX, EPUB ni HTML): **el sistema no escribe ningún artefacto que no sea Markdown o JSON**. El usuario convierte el manuscrito con la herramienta que prefiera. Que el visor (§9.2) pinte ese Markdown en un navegador no es un formato de salida: no produce ficheros.
- Código propio **en el hito 1**: programas, scripts, librerías. En el hito 2 el runner es código, pero ninguna parte del hito 1 lo requiere. Dos excepciones, y ninguna de las dos es una pieza del harness: el hook de una línea de `.claude/settings.json` que bloquea `Edit` sobre artefactos inmutables (§3.1), y el visor de `frontend/` (§9.2), que solo lee. El hito 1 funciona igual sin ninguno de los dos.
- Medición del coste en **dinero en el hito 1**: Claude Code no lo expone. Sí se mide el **volumen** (§6.6). En el hito 2 el runner sí registra el coste real que devuelve OpenRouter y `presupuesto_usd_max` pasa a ser un límite.
- Interfaz web o gráfica **como parte del harness**. Ninguna pieza del sistema depende de una interfaz para funcionar, ni en el hito 1 ni en el 2. Sí se admite un **visor** externo de solo lectura sobre `novelas/` ([frontend/](../frontend/), §9.2): no genera, no decide, no escribe, y borrarlo entero no cambia lo que el harness produce.
- Ilustraciones.
- Otros idiomas.
- Canon o universo compartido entre novelas. Series de novelas encadenadas: `saga` es una novela larga, no varias.
- Uso del modo de prueba (§8.1) como forma normal de generar novelas: existe solo para verificación.
- Volver atrás a un capítulo anterior ya aprobado y regenerar desde ahí.
- Reescritura automática tras las revisiones de arco o global.
- Avisos externos (email, webhook) al terminar o fallar.

---

## 2. Actores

| Actor | Tipo | Responsabilidad |
|---|---|---|
| **Usuario** | Persona | Aporta la idea, responde al interrogatorio, aprueba la escaleta, observa el progreso, decide qué hacer con los informes finales |
| **Harness** | Hito 1: Claude Code ejecutando la skill orquestadora `/novela`. Hito 2: el runner (§10) | Orquesta el flujo, invoca a los agentes, **escribe todos los ficheros**, guarda el estado, impone límites, comprueba longitudes y formatos, reanuda, ensambla |
| **Agente interrogador** | Hito 1: subagente de Claude Code. Hito 2: una llamada al modelo con el mismo prompt | Convierte la idea y la entrevista cerrada en biblia y escaleta de alto nivel; al empezar cada arco, detalla la escaleta de ese arco |
| **Agente escritor** | Ídem | Escribe cada capítulo. Solo el capítulo |
| **Agente resumidor** | Ídem | A partir **únicamente del texto del capítulo** y del libro de estado vigente, produce el resumen del capítulo y la propuesta de libro de estado actualizado |
| **Agente revisor** | Ídem | Juzga cada capítulo, cada arco al cerrarse y, si cabe, la novela completa. Nunca edita |

Los cuatro agentes son **prompts con un contrato** (§5), no piezas de Claude Code: por eso son lo primero que se porta al runner sin cambios. Ningún agente escribe ficheros ni habla con el usuario.

Por qué el resumen no lo escribe el escritor: el escritor resume lo que quiso escribir, no lo que quedó en la página. En la ejecución de validación 0.4.0 el resumen del capítulo 1 afirmaba un hecho que el texto no mostraba. A 200 capítulos los resúmenes y el libro de estado son la única memoria del sistema; un error ahí se propaga a todo lo que viene después.

---

## 3. Artefactos

Todos los artefactos de una novela viven en **una carpeta propia de esa novela**, `novelas/<slug>/`. Son el único estado del sistema: no hay nada en memoria que no esté también en disco tras cada paso completado.

| Artefacto | Fichero | Contenido | Lo produce | Lo leen |
|---|---|---|---|---|
| **Idea** | `idea.md` | Texto libre inicial del usuario | Harness (al arrancar) | Todos |
| **Configuración** | `config.json` | Copia congelada de la configuración raíz con el perfil ya resuelto y los valores efectivos de esta novela (§7) | Harness (al crear la novela) | Harness, interrogador |
| **Entrevista** | `entrevista.md` | Todas las decisiones de la etapa 1 en forma pregunta → respuesta, marcando cuáles eligió el usuario y cuáles quedaron en "decide tú". Cerrada antes de lanzar al interrogador | Harness (tras la entrevista) | Interrogador |
| **Biblia** | `biblia.md` | Premisa; tono y estilo; el mundo post-IA de esta novela (qué pasó, qué reglas rigen, qué ha cambiado); personajes con arco, motivación y voz; reglas internas que la historia no puede romper | Interrogador | Todos |
| **Escaleta (alto nivel)** | `escaleta.md` | Tres actos (planteamiento, nudo, desenlace). **Arcos**: cada uno con rango de capítulos, objetivo narrativo, sucesos clave que deben ocurrir en él, hilos que abre y cierra. Número total de capítulos. Con pocos capítulos (§4.1) hay un único arco que cubre toda la novela | Interrogador | Todos |
| **Escaleta de arco A** | `arcos/arco-AA.md` | Una entrada por capítulo del arco: título provisional, objetivo narrativo, sucesos clave, personajes presentes, gancho de cierre, **longitud objetivo en palabras** | Interrogador (al empezar el arco) | Todos |
| **Capítulo N, intento K** | `capitulos/NN/intento-K.md` | Texto del capítulo. Se conservan todos los intentos; el aprobado se marca en el Estado | Escritor | Todos |
| **Resumen N, intento K** | `capitulos/NN/resumen-K.md` | Hechos ocurridos; cambios de estado de cada personaje; hilos abiertos y cerrados; objetos, lugares o datos introducidos que condicionan el futuro | Resumidor | Todos |
| **Libro de estado propuesto N, K** | `capitulos/NN/libro-estado-K.md` | El libro de estado tal como quedaría si este intento se aprueba | Resumidor | Harness |
| **Informe N, intento K** | `capitulos/NN/informe-K.md` | Veredicto APROBADO / RECHAZADO y lista de problemas concretos (§5.4). Uno por intento. Los rechazos por longitud los genera el harness sin invocar al revisor | Harness, a partir del JSON del revisor o de su propia comprobación | Todos |
| **Libro de estado** | `libro-estado.md` | **La memoria de la novela.** Personajes: dónde están, qué saben, en qué estado físico y emocional quedan, qué relaciones han cambiado. Hilos abiertos: capítulo de origen y capítulo o arco previsto de cierre según la escaleta. Hilos cerrados. Objetos, lugares y datos introducidos. Reglas del mundo en vigor y excepciones establecidas. Siempre refleja el último capítulo aprobado | Harness, copiando `libro-estado-K.md` del intento aprobado | Escritor, resumidor, revisor |
| **Informe de arco A** | `arcos/informe-arco-AA.md` | Revisión de continuidad sobre los capítulos del arco completo. Informativo | Harness, a partir del JSON del revisor | Usuario |
| **Estado** | `estado.json` | Etapa actual; arco y capítulo en curso; intento en curso; capítulos aprobados con su intento y si fue por agotamiento; invocaciones realizadas; motivo de parada si la hubo | Solo el harness | Harness |
| **Registro (log)** | `registro.md` | Cada invocación a un agente: quién, cuándo, modelo, con qué entradas, volumen (§6.6), resultado; cada decisión del harness | Solo el harness | Usuario |
| **Manuscrito** | `manuscrito.md` | Novela ensamblada en Markdown: título, índice, capítulos aprobados en orden | Harness (al final) | Usuario |
| **Informe global** | `informe-global.md` | Resultado de la revisión final sobre la novela completa (§4.3). Informativo | Harness, a partir del JSON del revisor | Usuario |
| **Informe de cierre** | `informe-cierre.md` | Resultado de la última ejecución: ÉXITO o PARADA, motivo, qué quedó completado, métricas de calidad (§8.3), acción para continuar (§6.5) | Solo el harness | Usuario |

### 3.1 Reglas de escritura

- **Solo el harness escribe.** Cada agente devuelve su salida en el mensaje final con la forma que fija su contrato (§5). El harness valida la forma y la escribe en la ruta que le corresponde. Un agente no tiene, ni necesita, herramientas de escritura. En el hito 1 los subagentes se definen con `tools: Read, Glob, Grep`.
- **Nada aprobado se modifica**: ni la biblia ni la escaleta de alto nivel tras la aprobación del usuario, ni la escaleta de un arco tras validarla el harness, ni un capítulo tras el veredicto APROBADO (o la aceptación por agotamiento), ni el libro de estado salvo por el harness al cerrar un capítulo. El harness crea cada uno de esos ficheros con una escritura completa, una sola vez (o una por versión, en la biblia y la escaleta antes de aprobarse); nunca los edita en sitio. En el hito 1 un hook `PreToolUse` de `.claude/settings.json` bloquea la herramienta `Edit` sobre `biblia.md`, `escaleta.md`, `arco-*.md`, `intento-*.md`, `libro-estado.md` y `manuscrito.md`. No impide una sobreescritura completa: eso lo detecta el criterio 6 de §8.2 con git. En el hito 2 la inmutabilidad es código.
- El **Estado**, el **Registro** y el **Libro de estado** son exclusivos del harness. Un agente nunca decide qué capítulo va ahora ni si algo está aprobado.
- **Escritura atómica** (hito 2): cada fichero se escribe en un temporal y se renombra, para que una interrupción no deje un artefacto a medias con nombre definitivo.

---

## 4. Flujo

```mermaid
flowchart TD
    idea([Usuario: idea])

    subgraph E1["Etapa 1 — Interrogatorio"]
        preg[Harness entrevista al usuario<br/>y cierra la Entrevista]
        prop[Interrogador propone biblia<br/>+ escaleta de alto nivel]
        conf{¿Usuario confirma?}
        preg --> prop --> conf
        conf -- "pide cambios" --> prop
    end

    subgraph E2["Etapa 2 — Bucle por arco y capítulo, sin intervención humana"]
        arco[Interrogador detalla la escaleta del arco A<br/>Harness la valida]
        esc[Escritor escribe capítulo N]
        lon{Harness: ¿longitud<br/>dentro de tolerancia?}
        res[Resumidor: resumen N<br/>+ libro de estado propuesto]
        rev[Revisor emite informe N]
        vered{Veredicto<br/>recalculado por el harness}
        quedan{¿Quedan reescrituras?}
        agot[Harness acepta el mejor intento<br/>y registra aviso]
        cierra[Harness cierra el capítulo:<br/>libro de estado, estado, commit]
        finarco{¿Fin de arco?}
        revarco[Revisor: informe de arco]
        mas{¿Quedan capítulos?}
        arco --> esc --> lon
        lon -- "no" --> quedan
        lon -- "sí" --> res --> rev --> vered
        vered -- "RECHAZADO" --> quedan
        quedan -- "sí: informe al escritor" --> esc
        quedan -- "no" --> agot --> cierra
        vered -- "APROBADO" --> cierra
        cierra --> finarco
        finarco -- "sí" --> revarco --> mas
        finarco -- "no" --> mas
        mas -- "sí, mismo arco" --> esc
        mas -- "sí, arco nuevo" --> arco
    end

    subgraph E3["Etapa 3 — Final"]
        ens[Harness ensambla el manuscrito]
        glob[Revisor: informe global]
        ens --> glob
    end

    idea --> preg
    conf -- "confirma" --> arco
    mas -- "no" --> ens
    glob --> fin([Usuario])
```

### 4.1 Etapa 1 — Interrogatorio

1. El harness crea la carpeta de la novela y guarda la idea.
2. **Entrevista.** El harness pregunta al usuario en **rondas sucesivas, sin límite fijo** (en Claude Code, con la skill `grilling`; en el runner, la entrevista llega ya cerrada en un fichero, §10.2). Pregunta lo que cambia la novela: protagonista y antagonismo, qué versión del mundo post-IA, tono, punto de vista, tipo de final, temas que tocar o evitar, extensión deseada. El resultado se escribe en la **Entrevista**, marcando qué eligió el usuario y qué dejó en "decide tú".
3. **Propuesta.** El harness lanza al interrogador con la idea, la entrevista y los límites. El interrogador devuelve la biblia y la escaleta de alto nivel y **propone el cierre** con un resumen. El harness las escribe, valida la escaleta contra los límites (abajo) y se la presenta al usuario.
4. El usuario **confirma** o **pide cambios**. Si pide cambios, el harness los pasa al interrogador, que corrige solo eso y vuelve a proponer. Nada se aprueba hasta que hay confirmación explícita.
5. Con la confirmación, el harness marca la biblia y la escaleta de alto nivel como aprobadas e inmutables, y pasa a la etapa 2.

Los agentes **no hablan con el usuario**: toda la conversación pasa por el harness. Así la etapa 1 es la misma en Claude Code y en el runner; solo cambia de dónde salen las respuestas.

**Escaleta por arcos.** Ningún modelo produce de una vez 200 entradas de capítulo con objetivo, sucesos y gancho propios, y tampoco puede revisar lo que produjo. Por eso la escaleta tiene dos niveles:

- La **escaleta de alto nivel** divide la novela en arcos de como mucho `formato.capitulos_por_arco` capítulos (15 por defecto). Es lo que aprueba el usuario y lo que queda inmutable.
- La **escaleta de cada arco** se genera al llegar a él (§4.2, "Inicio de arco"), con la biblia, la escaleta de alto nivel, el libro de estado y el informe del arco anterior como entradas. Así el detalle del arco 9 conoce lo que realmente pasó en los arcos 1–8, no solo lo que estaba previsto.

Si el total de capítulos no supera `capitulos_por_arco`, hay **un solo arco** y el interrogador devuelve su escaleta detallada en la misma propuesta que la de alto nivel. El perfil `relato` funciona así; el mecanismo es el mismo, degradado.

Restricciones que el interrogador debe respetar, tomadas del perfil activo de `config.json` (§7.1): número de capítulos entre `capitulos_min` y `capitulos_max`; longitud objetivo de cada capítulo entre `formato.palabras_min_capitulo` y `palabras_max_capitulo`; los arcos cubren todos los capítulos, sin huecos ni solapes; cada arco cabe en `capitulos_por_arco`. Si la propuesta viola un límite, el harness la devuelve al interrogador con el motivo, hasta `limites.escaleta_rechazos_max` veces, antes de presentársela al usuario o, en un arco, antes de parar.

### 4.2 Etapa 2 — Bucle por arco y capítulo

**Inicio de arco A.** Si `arcos/arco-AA.md` no existe, el harness lanza al interrogador en modo arco con: biblia, escaleta de alto nivel (con el arco A destacado), libro de estado, informe del arco anterior si lo hay. El interrogador devuelve la escaleta del arco; el harness comprueba que tiene exactamente los capítulos del rango, que las longitudes están en límites y que los sucesos clave del arco de alto nivel aparecen asignados a algún capítulo. Si no, la devuelve con el motivo, hasta `escaleta_rechazos_max`; después, parada limpia. Validada, se escribe y se commitea. No hay confirmación del usuario: la etapa 2 corre sin intervención humana.

Para cada capítulo N del arco, en orden:

**Escritura.** El escritor recibe:
- la biblia completa,
- la escaleta de alto nivel y la escaleta del arco A (con la entrada de N destacada),
- el **libro de estado**,
- los resúmenes de los últimos `memoria.resumenes_completos_ultimos` capítulos aprobados,
- el **texto íntegro del capítulo N−1** aprobado si `memoria.capitulo_anterior_integro` (para mantener voz y enlace),
- en caso de reescritura, el informe de rechazo del intento anterior y el texto rechazado.

Devuelve el texto del capítulo. El harness lo escribe en `intento-K.md`.

**Comprobación de longitud (harness, sin modelo).** El harness cuenta las palabras del cuerpo (`wc -w` o equivalente). Si la desviación respecto a la longitud objetivo supera `formato.tolerancia_longitud`, el harness genera él mismo el informe K con un único problema de gravedad 3 (palabras contadas, objetivo, margen) y trata el intento como RECHAZADO **sin invocar al resumidor ni al revisor**. Consume un intento como cualquier rechazo.

**Resumen.** El resumidor recibe **solo** el texto del capítulo, el libro de estado vigente y la plantilla de resumen. No recibe la escaleta ni la biblia: su trabajo es decir qué hay en la página, no qué debía haber. Devuelve el resumen N y el libro de estado tal como quedaría si el capítulo se aprueba. El harness escribe ambos como `resumen-K.md` y `libro-estado-K.md`.

**Revisión.** El revisor recibe el capítulo N, su resumen, la biblia, la escaleta de alto nivel y la del arco, el libro de estado vigente y los mismos resúmenes que recibió el escritor. Devuelve el informe N como JSON (§5.4). El harness valida la forma, **recalcula el veredicto** con la regla de §7.5 y escribe `informe-K.md` con el veredicto recalculado. Si el del revisor no coincide, lo registra como `discrepancia_veredicto`.

**Decisión del harness.**
- APROBADO → copia `libro-estado-K.md` sobre `libro-estado.md`, marca el intento como aprobado en el Estado, commitea, avanza a N+1.
- RECHAZADO con reescrituras disponibles → lanza al escritor con el informe. Máximo `limites.reescrituras_max` reescrituras (2 por defecto: 3 intentos en total).
- RECHAZADO sin reescrituras disponibles → **acepta el mejor intento**, no el último: el de menos problemas de gravedad 1–2; a igualdad, el de menos problemas en total; a igualdad, el más reciente. Un intento rechazado por longitud nunca gana frente a uno que pasó al revisor. Registra el aviso con el informe adjunto en el log y en el Estado, adopta su libro de estado, avanza a N+1. La novela no se bloquea por un desacuerdo entre agentes.

**Fin de arco.** Tras cerrar el último capítulo del arco, el revisor recibe el texto de todos los capítulos del arco, la escaleta del arco, la escaleta de alto nivel, la biblia y el libro de estado, y devuelve el **informe de arco**: hilos que el arco debía cerrar y no cerró, contradicciones entre capítulos del arco, personajes desaparecidos, cambios de reglas. Es informativo: nada se reescribe. Se escribe en `arcos/informe-arco-AA.md` y alimenta la escaleta del arco siguiente, que puede compensar lo que faltó. Con un solo arco, este informe y el global de §4.3 son la misma pasada y se hace una sola vez.

**Progreso visible.** El usuario ve una línea por evento: arco detallado, capítulo N escrito, rechazado por longitud, rechazado (motivo resumido), aprobado, aceptado por agotamiento, informe de arco. Puede interrumpir cuando quiera; el estado en disco permite reanudar (§6.2).

### 4.3 Etapa 3 — Final

1. El harness ensambla el **manuscrito** con los capítulos aprobados.
2. **Revisión global.** Si el manuscrito no supera `limites.revision_global_max_palabras` (60.000 por defecto), el revisor hace **una única pasada sobre la novela completa** buscando lo que no puede verse capítulo a capítulo ni arco a arco: hilos prometidos y nunca cerrados, contradicciones entre capítulos lejanos, personajes que desaparecen sin explicación, cambios de reglas del mundo. Si lo supera, el manuscrito no cabe en ningún contexto: la pasada global se hace sobre la **biblia, la escaleta de alto nivel, el libro de estado final, todos los resúmenes y todos los informes de arco**, y el informe global lo dice. Emite el **informe global**. No reescribe nada.
3. El harness calcula las **métricas de calidad** (§8.3) y emite el **informe de cierre** (§6.5) con la ruta del manuscrito y del informe global. Qué hacer con los informes es decisión del usuario, fuera del alcance del sistema.

---

## 5. Contratos de los agentes

Reglas comunes a los cuatro: reciben exactamente las entradas de su contrato; devuelven su salida **en el mensaje final**, con la forma que fija el contrato, sin texto antes ni después; no escriben ficheros; no hablan con el usuario; no deciden nada del flujo. Un mensaje final que no tenga la forma esperada es un **incumplimiento de contrato** (§6.5) y el harness repite la invocación indicando qué faltó.

Forma de los bloques de documento (interrogador, escritor, resumidor): cada documento va entre una línea `=== ARCHIVO: <ruta relativa a la carpeta de la novela> ===` y una línea `=== FIN ===`. El harness extrae cada bloque y lo escribe en su ruta. El revisor no usa bloques: devuelve solo JSON (§5.4).

En el hito 1 los cuatro se definen en `.claude/agents/` con `tools: Read, Glob, Grep` (sin escritura), `maxTurns` igual a `limites.turnos_por_invocacion`, `model` igual a `modelos.<agente>` y **sin** el campo `memory`: los agentes son amnésicos entre novelas, porque una memoria persistente crearía el canon compartido que §1.2 prohíbe.

`maxTurns` y `model` son **estáticos**: el frontmatter no lee `config.json`, así que el valor está escrito dos veces y `comprobar_entorno` comprueba al arrancar que ambas copias coinciden (§6.2). El modelo que manda en cada llamada es el que el harness pasa en el parámetro `model` de la herramienta `Agent` (`invocar.md`), que es lo que permite el escalado de §7.3; el del frontmatter es la red de seguridad para que una llamada a la que se le olvide el parámetro caiga en el modelo declarado y no en el de la sesión.

### 5.1 Agente interrogador

| | |
|---|---|
| **Entrada (propuesta)** | Idea del usuario; Entrevista cerrada; límites de tamaño de la configuración; en una segunda vuelta, el motivo (fuera de límites o cambios pedidos por el usuario) |
| **Entrada (arco)** | Biblia; escaleta de alto nivel con el arco destacado; libro de estado; informe del arco anterior si existe; límites; en una segunda vuelta, el motivo |
| **Salida (propuesta)** | Biblia, escaleta de alto nivel y, si hay un solo arco, su escaleta detallada; propuesta de cierre. Cada documento en un bloque delimitado con la ruta destino como etiqueta |
| **Salida (arco)** | Escaleta del arco, en un bloque |
| **Debe** | Respetar al pie de la letra lo que el usuario eligió en la entrevista; decidir lo que quedó en "decide tú" y anotarlo como decisión propia en la biblia; fijar número de capítulos, arcos y longitudes dentro de los límites; garantizar que la escaleta cubre los tres actos y que cada capítulo tiene un objetivo narrativo propio; en modo arco, asignar a capítulos concretos todos los sucesos clave del arco y recoger lo que el informe del arco anterior dejó pendiente; en una segunda vuelta, corregir solo lo indicado |
| **No debe** | Escribir prosa de la novela; preguntar nada (la entrevista ya está cerrada); modificar la biblia o la escaleta de alto nivel en modo arco; marcar nada como aprobado |

### 5.2 Agente escritor

| | |
|---|---|
| **Entrada** | Biblia; escaleta de alto nivel; escaleta del arco con la entrada N destacada; libro de estado; últimos resúmenes según `memoria`; capítulo anterior íntegro si `memoria` lo indica; en reescritura, informe y texto rechazado |
| **Salida** | Texto del capítulo N, en un único bloque, con título |
| **Debe** | Cumplir el objetivo, los sucesos y el gancho de la entrada N; respetar biblia, libro de estado y resúmenes; ajustarse a la longitud objetivo dentro de la tolerancia; mantener la voz del capítulo anterior; en reescritura, corregir cada problema del informe sin introducir otros |
| **No debe** | Producir resumen ni notas; adelantar sucesos asignados a capítulos posteriores; resolver hilos que la escaleta deja abiertos para más adelante; contradecir el libro de estado |

### 5.3 Agente resumidor

| | |
|---|---|
| **Entrada** | Texto del capítulo N (intento K); libro de estado vigente; plantillas de resumen y de libro de estado |
| **Salida** | Dos bloques: el resumen N y el libro de estado actualizado completo |
| **Debe** | Registrar **solo lo que está en el texto**: hechos ocurridos, cambios de estado de cada personaje que aparece, hilos que se abren o cierran, objetos, lugares y datos introducidos. En el libro de estado, actualizar las entradas afectadas y conservar intactas las demás; marcar en cada hilo abierto el capítulo de origen; mover a cerrados lo que el texto cierra |
| **No debe** | Inferir lo que el autor "quiso decir"; añadir hechos que el texto no muestra; juzgar la calidad; consultar la escaleta ni la biblia (no las recibe, para que no rellene huecos con lo previsto en lugar de con lo escrito) |

### 5.4 Agente revisor

| | |
|---|---|
| **Entrada (por capítulo)** | Capítulo N; resumen N; biblia; escaleta de alto nivel y del arco; libro de estado vigente; últimos resúmenes según `memoria` |
| **Entrada (arco)** | Texto de los capítulos del arco; escaleta del arco y de alto nivel; biblia; libro de estado |
| **Entrada (global)** | Manuscrito completo, o si no cabe (§4.3) biblia, escaleta de alto nivel, libro de estado final, todos los resúmenes y todos los informes de arco |
| **Salida** | Informe en JSON con la forma de abajo |
| **Debe** | Juzgar exclusivamente contra estos criterios, en este orden de gravedad: (1) contradice la biblia, el libro de estado o los resúmenes previos; (2) no cumple la entrada N de la escaleta (objetivo, sucesos, gancho) o adelanta sucesos futuros; (4) ruptura de voz, punto de vista o tono; (5) el resumen no refleja el capítulo. Cada problema debe ser **concreto y accionable** (dónde, qué, por qué) |
| **No debe** | Editar el texto; rechazar por gusto sin señalar un criterio; añadir criterios propios; **contar palabras ni juzgar la longitud**: el criterio 3 (longitud) lo comprueba el harness antes de invocarlo y la numeración se conserva por compatibilidad de los informes |

Forma del mensaje final, la misma en los tres modos:

```json
{
  "veredicto": "RECHAZADO",
  "problemas": [
    {
      "gravedad": 1,
      "donde": "párrafo 14, escena del taller",
      "que": "Marta usa el implante que perdió en el capítulo 2",
      "por_que": "libro de estado, Personajes › Marta: 'sin implante desde el cap. 2 (redada)'"
    }
  ],
  "observaciones": ["El diálogo del final se alarga; no obliga a reescribir"]
}
```

`problemas` puede ser una lista vacía. `gravedad` es un entero en {1, 2, 4, 5}. El harness rechaza como incumplimiento cualquier salida que no sea JSON válido con exactamente esas tres claves. Se usa JSON y no YAML porque los modelos baratos rompen el YAML con más facilidad y porque en el hito 2 se valida con un esquema y, donde el modelo lo admita, se pide salida estructurada.

Un informe es **RECHAZADO** si tiene al menos `veredicto.rechaza_con_graves` problemas de gravedad 1 o 2, o al menos `veredicto.rechaza_con_leves` de gravedad 3–5 (los de gravedad 3 solo los genera el harness). En otro caso es **APROBADO**, con observaciones menores que no obligan a reescribir. El veredicto que vale es el que recalcula el harness.

---

## 6. Contrato del harness

### 6.1 Responsabilidades

- Crear y gestionar la carpeta de la novela.
- Invocar a cada agente con exactamente las entradas de su contrato; ni más (ahorro de contexto) ni menos.
- Validar la forma de cada salida y **escribirla en disco**. Ningún agente escribe.
- Comprobar la longitud de cada capítulo antes de revisarlo.
- Tomar todas las decisiones de flujo: aprobar, reescribir, aceptar por agotamiento, avanzar, detallar arco, parar.
- Recalcular el veredicto y elegir el mejor intento con reglas fijas.
- Mantener el libro de estado.
- Escribir el Estado tras **cada** decisión, no al final.
- Registrar todo (§3, Registro).
- Imponer los límites (§6.3).
- Ensamblar el manuscrito y calcular las métricas de calidad.
- Mostrar el progreso al usuario.

### 6.2 Reanudación

Relanzar el programa sobre una carpeta de novela existente **continúa donde se quedó**:

- Si la escaleta de alto nivel no está aprobada → vuelve al interrogatorio, con lo ya respondido como contexto.
- Si está en el bucle → retoma en el arco, capítulo e intento indicados en el Estado. Nada aprobado se regenera. Un intento a medias (escrito sin cerrar) se considera no existente y se repite con el mismo número. Un arco sin escaleta validada se detalla de nuevo.
- Si el bucle terminó pero falta el informe global → ejecuta solo eso.
- Si la novela está completa → lo indica y no hace nada.

Reanudar es siempre **el mismo comando sobre la misma carpeta** (`/novela continuar <carpeta>`). El usuario no tiene que decir desde dónde: lo sabe el Estado.

### 6.3 Límites

Todos salen de `config.json` (§7); aquí el comportamiento y el valor por defecto.

| Límite | Comportamiento | Variable · por defecto |
|---|---|---|
| Reescrituras por capítulo | Al agotarse, aceptación del mejor intento con aviso | `limites.reescrituras_max` · 2 |
| Capítulos | La escaleta que lo viole se devuelve al interrogador | perfil activo · 3–8 (`relato`) |
| Palabras por capítulo (objetivo) | Ídem, acotado además por el suelo y techo absolutos | perfil activo · 1.500 (`relato`) |
| Capítulos por arco | Un arco más largo se devuelve al interrogador | `formato.capitulos_por_arco` · 15 |
| **Turnos por invocación** de agente | Un agente que no entrega su salida en ese número de turnos incumple el contrato (reintento; parada si persiste). En el hito 1 lo impone Claude Code con `maxTurns` en el frontmatter de cada subagente; el harness comprueba al arrancar que ese valor coincide con el de `config.json` y, si no, `ERROR_CONFIGURACION`. Un resultado marcado como parcial por Claude Code es un incumplimiento. En el hito 2 es el número máximo de llamadas por paso más un tiempo máximo por llamada | `limites.turnos_por_invocacion` · 40 |
| Fallo técnico de un agente (error, respuesta vacía o que no cumple el contrato) | Reintentos del mismo paso; si persiste, parada limpia con el error en el Registro y en el Estado | `limites.reintentos_tecnicos` · 3 |
| Tamaño de la revisión global | Por encima, la pasada global se hace sobre resúmenes, libro de estado e informes de arco (§4.3) | `limites.revision_global_max_palabras` · 60.000 |
| Presupuesto | Hito 2 solo: al superarlo, parada limpia con el acumulado en el informe de cierre. `null` desactiva | `limites.presupuesto_usd_max` · `null` |
| Pausa programada | Cada N capítulos cerrados, parada limpia opcional para no agotar el contexto de la sesión. Hito 1 solo | `limites.pausa_cada_capitulos` · 5 |

"Parada limpia" significa: ningún artefacto a medias marcado como válido, Estado actualizado con el motivo, mensaje claro al usuario de cómo reanudar.

### 6.4 Progreso

Durante la etapa 2 el harness muestra, como mínimo: arco y capítulo en curso y totales, intento, veredicto de cada revisión con motivo resumido, y cualquier aviso (rechazo por longitud, aceptación por agotamiento, discrepancia de veredicto, incumplimiento de contrato).

### 6.5 Fallos: cómo se entera el usuario y cómo se resuelve

Principio: **el programa nunca muere en silencio ni deja el estado a medias.** Toda ejecución, termine bien o mal, acaba con un informe de cierre.

**Cómo se entera el usuario**

1. **Informe de cierre** mostrado en la sesión y guardado en la carpeta de la novela. Contiene: resultado (ÉXITO / PARADA), motivo clasificado (tabla siguiente), etapa, arco y capítulo en que se detuvo, qué quedó completado y aprobado, avisos acumulados, métricas de calidad (§8.3), volumen (§6.6) y **la acción exacta para continuar**.
2. **Comando de estado** (`/novela estado <carpeta>`): resume etapa, arco, capítulo, intento, aprobados, invocaciones y último informe de cierre, sin que el usuario abra ficheros.
3. Durante la ejecución, cada problema recuperable aparece en el progreso en el momento en que ocurre.

**Clasificación de motivos y cómo se resuelve cada uno**

| Motivo | Qué ha pasado | Qué hace el harness solo | Qué tiene que hacer el usuario |
|---|---|---|---|
| **Fallo técnico transitorio** | El agente falla, devuelve vacío o se corta | Hasta `reintentos_tecnicos` reintentos del mismo paso. Si alguno funciona, no hay parada | Nada |
| **Fallo técnico persistente** | Todos los reintentos fallan | Parada limpia. Registra el error completo | **Relanzar sobre la misma carpeta** (`/novela continuar`) |
| **Agente incumple contrato** | La salida no tiene la forma esperada (JSON inválido, falta un bloque, capítulo vacío) o agota los turnos | Se trata como fallo técnico: reintento del paso con la indicación exacta del incumplimiento | Si persiste: relanzar. Si se repite en varias novelas, es un problema de la definición del agente y se anota como incidencia en el CHANGELOG |
| **Escaleta fuera de límites** | El interrogador propone algo fuera de los límites, en la propuesta o en un arco | Se devuelve con el motivo, hasta `escaleta_rechazos_max` veces; después parada limpia | Relajar los límites o ajustar la idea, y relanzar |
| **Presupuesto agotado** (hito 2) | El coste acumulado supera `presupuesto_usd_max` | Parada limpia tras cerrar el paso en curso | Subir el presupuesto y relanzar |
| **Error de configuración** | La carpeta no es válida, el repositorio no está bajo git, faltan ficheros del harness, o el `maxTurns` o el `model` del frontmatter de un agente no coinciden con `config.json` | Parada inmediata antes de invocar a ningún agente, indicando qué falta | Corregir y relanzar |
| **Interrupción del usuario** | Corta la sesión o el comando | El paso en curso se descarta; el Estado queda en el último punto consistente | Relanzar cuando quiera |

Nunca se requiere borrar nada a mano ni editar el Estado para continuar. Si una carpeta quedara en un estado que el harness no reconoce, el informe de cierre lo dice explícitamente y señala el último punto consistente, en lugar de intentar adivinar.

Ya no existe el motivo "escritura fuera de zona": como los agentes no escriben, no puede ocurrir.

### 6.6 Volumen: el dato para decidir el modelo

La decisión que motiva el hito 2 —pasar a un modelo más barato— es económica. El Registro lleva en cada fila `invocacion` las columnas `modelo`, `pal_entrada`, `pal_salida`, `tok_entrada`, `tok_salida` y `coste_usd`, y se rellenan las que estén disponibles:

- **Hito 1**: `pal_entrada` (palabras de los ficheros que el prompt manda leer al agente) y `pal_salida` (palabras de lo que entregó), contadas con `wc -w`. La herramienta de subagentes de Claude Code no devuelve tokens en el resultado; si una invocación en segundo plano los expone en su notificación, se anotan en `tok_*`. `coste_usd` queda vacío.
- **Hito 2**: `tok_*` y `coste_usd` reales de la respuesta de la API. `pal_*` se siguen rellenando para poder comparar con el hito 1.

**Limitación conocida del hito 1**: la columna `modelo` registra el modelo que el harness **pidió** (`elegir_modelo`), no el que atendió la llamada, porque la herramienta `Agent` no devuelve esa información. Las dos defensas contra una divergencia silenciosa son el `model` del frontmatter (§2) y la comprobación de arranque; la verificación a posteriori solo es posible fuera del repositorio, en los transcripts de subagente de Claude Code, y no forma parte del harness. En el hito 2 desaparece: la respuesta de la API dice qué modelo respondió, y esa es la que se registra.

En el informe de cierre: la suma por agente y por modelo. Con eso, tras la novela de 5 capítulos se puede proyectar el coste de 100 o 200 en cualquier modelo, y tras dos novelas con la misma idea y distinto modelo (`/novela comparar`, §8.4) se puede decidir con números si el barato aguanta.

---

## 7. Variables configurables — `config.json`

Todo el comportamiento ajustable del harness vive en **[`config.json`](../config.json)**, en la raíz del repositorio. Es el único fichero que el usuario necesita editar: no hay que tocar la skill, los agentes ni esta especificación.

Al crear una novela, el harness **congela** la configuración efectiva en `novelas/<slug>/config.json`, con el perfil ya resuelto. A partir de ahí esa novela usa su copia, aunque después se edite el fichero raíz. Las variables de tamaño (capítulos, palabras, arcos) quedan además bloqueadas al aprobar la escaleta; el resto (proveedor, modelos, reintentos, reescrituras, memoria, límites, calidad) sí pueden cambiarse al reanudar con `/novela continuar <carpeta> <clave>=<valor>`.

### 7.1 Perfil activo y tamaño de la historia

`perfil_activo` elige uno de los `perfiles`. **Cambiar esa única cadena es lo que escala el proyecto**, de un relato de prueba a una novela larga.

| Perfil | Capítulos (objetivo · min–max) | Palabras/capítulo | Arcos | Páginas aprox. |
|---|---|---|---|---|
| `relato` | 5 · 3–8 | 1.500 | 1 | ~30 |
| `novela_corta` | 12 · 8–15 | 2.000 | 1 | ~96 |
| `novela` | 30 · 20–40 | 2.500 | 2–3 | ~300 |
| `saga` | 100 · 60–200 | 2.500 | 4–14 | ~1.000 (hasta ~2.000) |

Campos de cada perfil:

| Variable | Qué hace |
|---|---|
| `capitulos_objetivo` | Cuántos capítulos debe proponer el interrogador si nada indica otra cosa |
| `capitulos_min` / `capitulos_max` | Límites duros. Una escaleta fuera de rango se devuelve al interrogador (§4.1) |
| `palabras_por_capitulo` | Longitud objetivo de cada capítulo. El interrogador puede variarla por capítulo dentro de `formato.palabras_min_capitulo`–`palabras_max_capitulo` |
| `paginas_objetivo` | **Alternativa a `capitulos_objetivo`.** Si no es `null`, manda: el harness calcula `capitulos = redondeo(paginas × formato.palabras_por_pagina ÷ palabras_por_capitulo)` y comprueba que cae entre `capitulos_min` y `capitulos_max`; si no, para con `ESCALETA_FUERA_LIMITES` antes de empezar |
| `descripcion` | Texto para el usuario; el harness la ignora |

Para añadir un perfil propio basta con añadir una entrada al objeto `perfiles` y apuntar `perfil_activo` a ella.

### 7.2 Formato

| Variable | Por defecto | Qué hace |
|---|---|---|
| `formato.palabras_por_pagina` | 250 | Conversión páginas ↔ palabras. Solo se usa si un perfil fija `paginas_objetivo` y para informar del tamaño |
| `formato.palabras_min_capitulo` | 800 | Suelo absoluto por capítulo, por encima de lo que diga el perfil |
| `formato.palabras_max_capitulo` | 5.000 | Techo absoluto por capítulo |
| `formato.tolerancia_longitud` | 0.2 | Margen que acepta el **harness** sobre la longitud objetivo (±20 %). Ponerlo a `0` fuerza rechazos deterministas: sirve para probar el bucle de reescritura (§8.2, criterio 3) |
| `formato.capitulos_por_arco` | 15 | Tamaño máximo de un arco. Con total ≤ este valor hay un solo arco y la escaleta se detalla entera en la propuesta (§4.1) |

### 7.3 Proveedor y modelos

`proveedor` indica quién ejecuta los agentes: `"claude-code"` (hito 1: subagentes con la herramienta `Agent`) u `"openrouter"` (hito 2: llamadas a la API). Es la única clave que distingue los dos hitos; todo lo demás es común.

Qué modelo usa cada agente, y cuál se usa **cuando algo va mal**. Con `claude-code`, los valores son los alias que acepta la herramienta `Agent`: `"opus"`, `"sonnet"`, `"haiku"`, `"fable"`. Con `openrouter`, identificadores de modelo de OpenRouter. El orquestador pasa el modelo en cada invocación, así que puede cambiar entre un intento y el siguiente del mismo capítulo.

Los valores por defecto corresponden a la **validación** (§7.8, paso 1): todo con el modelo caro y el escalado apagado, para medir el techo del diseño. Para el abaratamiento (paso 2) se baja el modelo base y se enciende el escalado, sin tocar nada más.

| Variable | Por defecto | Qué hace |
|---|---|---|
| `modelos.interrogador` | `opus` | Modelo del agente que construye biblia y escaletas |
| `modelos.escritor` | `opus` | Modelo por defecto del que escribe los capítulos |
| `modelos.resumidor` | `opus` | Modelo del que resume y actualiza el libro de estado. Es la tarea más mecánica: la primera candidata a bajar de modelo |
| `modelos.revisor` | `opus` | Modelo por defecto del que juzga |
| `modelos.temperatura.*` | escritor 0.9 · interrogador 0.7 · resumidor 0.0 · revisor 0.0 | Temperatura por agente. **Hito 2 solo**: la herramienta `Agent` no la expone. Escribir necesita variedad; resumir y juzgar necesitan lo contrario |
| `modelos.escalado.activo` | `false` | Interruptor general del escalado. En `false` se ignora todo lo demás de esta sección |
| `modelos.escalado.modelo` | `opus` | Modelo al que se sube cuando se cumple alguna condición de abajo |
| `modelos.escalado.escritor_desde_intento` | 2 | A partir de ese intento, el escritor usa el modelo escalado. Con 2: el primer intento es barato; si lo rechazan, la reescritura la hace el modelo bueno |
| `modelos.escalado.revisor_desde_intento` | 3 | Ídem para el revisor. Con 3: el juicio del último intento, el que puede acabar aceptado por agotamiento, lo hace el modelo bueno |
| `modelos.escalado.tras_fallo_tecnico` | `true` | Si un agente falla o incumple el contrato, el reintento se hace con el modelo escalado |
| `modelos.escalado.revision_arco_y_global` | `true` | Los informes de arco y la pasada final usan el modelo escalado |

Cada `modelos.<agente>` está escrito dos veces: aquí y en el `model` del frontmatter del agente (§2), porque el frontmatter no puede leer este fichero. `comprobar_entorno` compara ambos y para si difieren. Para cambiar de modelo **en una sola ejecución** sin tocar los cinco ficheros, use la sobreescritura del comando (`modelos.escritor=haiku`), que se aplica después de esa comprobación: es la vía recomendada para el paso 2 de §7.8.

Configuraciones de referencia: **validación** = los cuatro en `opus`, `escalado.activo: false` (la de por defecto). **Abaratamiento** = los cuatro en `haiku` o `sonnet`, `escalado.activo: true` con `escalado.modelo: opus`. **Mínima** = los cuatro en `haiku`, escalado apagado. Subir `modelos.escritor` es lo que más cambia la calidad de la prosa; subir `modelos.revisor` es lo que más cambia la fiabilidad del veredicto; subir `modelos.resumidor` es lo que más cambia la fiabilidad de la memoria a largo plazo.

### 7.4 Límites

| Variable | Por defecto | Qué hace |
|---|---|---|
| `limites.reescrituras_max` | 2 | **Modificaciones máximas** de un capítulo. Con 2 hay 3 intentos; agotados, se acepta el mejor intento con aviso (§4.2) |
| `limites.reintentos_tecnicos` | 3 | **Retries** por invocación de agente ante fallo o incumplimiento de contrato. Agotados, parada limpia |
| `limites.escaleta_rechazos_max` | 3 | Veces que se devuelve una escaleta (de alto nivel o de arco) al interrogador por salirse de los límites antes de parar |
| `limites.turnos_por_invocacion` | 40 | Turnos máximos de un agente por invocación (§6.3). En el hito 1 debe coincidir con `maxTurns` en `.claude/agents/*.md` |
| `limites.revision_global_max_palabras` | 60000 | Por encima, la revisión global no lee el manuscrito sino resúmenes, libro de estado e informes de arco (§4.3) |
| `limites.presupuesto_usd_max` | `null` | Hito 2 solo. Coste acumulado que fuerza parada limpia. `null` = sin límite |
| `limites.pausa_cada_capitulos` | 5 | Hito 1 solo. Cada cuántos capítulos cerrados el harness puede hacer `PAUSA_PROGRAMADA` para no agotar el contexto de la sesión. `null` desactiva |

### 7.5 Regla de veredicto

Traduce a números la regla de §5.4, para poder endurecerla o relajarla sin tocar el agente:

| Variable | Por defecto | Qué hace |
|---|---|---|
| `veredicto.rechaza_con_graves` | 1 | Nº de problemas de gravedad 1 o 2 que bastan para RECHAZADO |
| `veredicto.rechaza_con_leves` | 2 | Nº de problemas de gravedad 3, 4 o 5 que bastan para RECHAZADO |

### 7.6 Memoria (lo que hace posible escalar)

Controla qué recibe el escritor (y el revisor) en cada capítulo (§4.2). El **libro de estado** es lo que da contexto de tamaño constante: sea el capítulo 8 o el 180, el escritor recibe biblia, escaletas, libro de estado, N resúmenes y un capítulo. Los resúmenes recientes dan la textura de lo inmediato; el libro de estado, la verdad acumulada.

| Variable | Por defecto | Qué hace |
|---|---|---|
| `memoria.resumenes_completos_ultimos` | `null` | Cuántos resúmenes previos reciben íntegros el escritor y el revisor. `null` = todos (razonable hasta `novela_corta`). Recomendado 10 desde `novela`. Lo que queda fuera de la ventana está representado en el libro de estado |
| `memoria.capitulo_anterior_integro` | `true` | Si el escritor recibe el texto completo del capítulo anterior (mantiene voz y empalme). Ponerlo a `false` ahorra contexto a costa de continuidad de estilo |
| `memoria.libro_estado_max_palabras` | 4000 | Techo orientativo del libro de estado que se le indica al resumidor. Si lo supera, el harness lo avisa en el progreso; el resumidor debe condensar entradas cerradas, no borrar hechos |

### 7.7 Calidad

Umbrales con los que el harness califica una novela en el informe de cierre y con los que `/novela comparar` decide si el modelo barato "aguanta" (§8.3). Son valores iniciales; se calibran con la ejecución de referencia del paso 1.

| Variable | Por defecto | Métrica |
|---|---|---|
| `calidad.max_graves_por_10_capitulos` | 1 | Problemas de gravedad 1 en informes de arco y global, por cada 10 capítulos (coherencia) |
| `calidad.max_agotamiento_pct` | 10 | Porcentaje de capítulos aceptados por agotamiento (adherencia) |
| `calidad.max_hilos_previstos_sin_cerrar` | 0 | Hilos que la escaleta de alto nivel manda cerrar y el libro de estado final tiene abiertos (cohesión) |
| `calidad.min_aprobados_primer_intento_pct` | 60 | Porcentaje de capítulos aprobados en el intento 1 (adherencia) |
| `calidad.max_rechazos_voz_pct` | 10 | Porcentaje de intentos rechazados con algún problema de gravedad 4 (cohesión de voz) |

### 7.8 Escalar el proyecto

El plan va de una historia pequeña con el modelo caro a 100–200 capítulos con un modelo barato, validando en cada paso contra la **misma idea y la misma entrevista** (`pruebas/referencia/`, §8.1). Cada paso cambia **solo configuración**, salvo el marcado como trabajo de harness.

| Paso | Qué se hace | Configuración | Qué se aprende | Estado |
|---|---|---|---|---|
| 1. **Validar el diseño** | `relato` (5 capítulos de 1.500 palabras) en Claude Code, los cuatro agentes con el modelo caro, escalado apagado, con la idea de referencia | La de por defecto | Si el diseño produce una historia que se lee y cumple el contrato (§8.2) cuando el modelo no es el problema. Fija la línea base de las métricas de §7.7 y la primera proyección de coste (§6.6) | Por ejecutar sobre el harness reconstruido |
| 2. **Abaratar** | Misma referencia, `modelos.*` en `haiku` o `sonnet` con escalado a `opus`. Se compara con el paso 1 (`/novela comparar`, §8.4) | `modelos.*`, `escalado.activo: true` | Si la novela barata pasa los umbrales de `calidad` y qué agente es el que más pierde | Por ejecutar |
| 3. **Portar al runner** | Reimplementar el orquestador como código contra OpenRouter (§10) siguiendo SKILL.md función a función, con los mismos prompts, plantillas, `config.json` y estructura de carpeta. Se valida con la referencia y `/novela comparar` frente al paso 2 | `proveedor: openrouter`, `modelos.*` con identificadores de OpenRouter | Que el runner produce una carpeta que pasa el mismo inventario (`specs/inventario.md`) y umbrales que la de Claude Code | **Trabajo de harness pendiente** |
| 4. **Crecer** | `novela_corta` (12) → `novela` (30) en el runner. Aparecen los arcos y se fija `memoria.resumenes_completos_ultimos` | `perfil_activo`, `memoria.*` | Si la escaleta por arcos aguanta y si los informes de arco detectan contradicciones a media distancia | Configuración |
| 5. **`saga`** (100–200) | Novela larga en el runner | `perfil_activo: saga`, `pausa_cada_capitulos: null` | La novela larga. Si el libro de estado se mantiene fiel a 100 capítulos | Configuración |

---

## 8. Verificación

### 8.1 Modo de prueba y caso de referencia

**Entrevista desde fichero.** `/novela nueva "<idea>" entrevista: <ruta>` toma una entrevista ya cerrada en vez de entrevistar al usuario en la sesión; el usuario sigue confirmando la escaleta. Es el mismo mecanismo con el que el runner recibe la entrevista (§10.2).

**Modo de prueba.** Existe **solo para verificar el harness**, no para uso normal. `/novela nueva modo-prueba: <carpeta>` toma `idea.md` y `entrevista.md` de esa carpeta y **aprueba la escaleta automáticamente** si cumple los límites. Todo lo demás se comporta exactamente igual que en uso normal. El Registro deja constancia de que la ejecución fue en modo de prueba.

**Caso de referencia.** `pruebas/referencia/` contiene una idea y una entrevista **fijas**. Todas las ejecuciones que se comparan entre sí (§7.8) usan esta entrada. Sin una entrada fija, comparar dos configuraciones es comparar dos historias distintas. Cambiar el caso de referencia invalida las comparaciones anteriores y se anota en el CHANGELOG.

### 8.2 Criterios de aceptación

Los ejecuta **Claude Code** sobre el caso de referencia en modo de prueba, y comprueba el resultado leyendo la carpeta. El usuario solo lee la novela al final.

1. **Novela completa.** La ejecución termina con ÉXITO y existen: biblia, escaleta de alto nivel, escaleta del arco, 5 capítulos aprobados con resumen, libro de estado propuesto e informe APROBADO (o aceptación por agotamiento registrada), libro de estado final, manuscrito, informe global e informe de cierre con métricas. Cada capítulo aprobado está dentro de la tolerancia de su longitud objetivo, medido con `wc -w`.
2. **Interrogatorio.** En modo de prueba, el harness toma la entrevista del caso de referencia sin preguntar nada, el interrogador propone el cierre por iniciativa propia y la escaleta resultante respeta los límites y refleja la entrevista (p. ej. el número de capítulos pedido).
3. **Rechazo y reescritura.** Con `formato.tolerancia_longitud: 0`, cada capítulo se rechaza por longitud sin invocar al resumidor ni al revisor, llega a 3 intentos, el harness acepta el mejor intento (el más cercano a la longitud objetivo), y el aviso figura en el progreso, el Registro y el informe de cierre.
4. **Reanudación.** Interrumpiendo el proceso durante el capítulo 2, al relanzar `/novela continuar` sobre la misma carpeta el capítulo 1 y el libro de estado conservan su contenido byte a byte (comprobable con git) y el capítulo 2 se retoma; el resultado final es una novela completa.
5. **Turnos agotados.** Con `maxTurns` deliberadamente bajo en un subagente, el agente no entrega, el harness reintenta 3 veces, hace parada limpia y el informe de cierre dice INCUMPLE CONTRATO con la acción de continuar. Al relanzar con el tope normal, termina con ÉXITO. Además: con `maxTurns` distinto de `limites.turnos_por_invocacion`, el harness para con ERROR_CONFIGURACION antes de invocar a nadie.
6. **Inmutabilidad.** Biblia y escaleta de alto nivel son idénticas antes y después del bucle; cada capítulo aprobado es idéntico al final; el libro de estado solo cambia en los commits de cierre de capítulo.
7. **Registro.** Para cualquier capítulo se puede reconstruir desde el Registro qué agentes se invocaron, cuántas veces, con qué modelo y con qué veredicto, y el número de invocaciones coincide con el del Estado.
8. **Reanudación tras parada.** Tras cualquier parada limpia (criterio 5), el Estado sigue siendo reanudable y `/novela continuar` no regenera nada aprobado.
9. **Comando de estado.** Sobre una novela a medias, `/novela estado` devuelve etapa, arco, capítulo, intento, aprobados e invocaciones coherentes con el Estado.
10. **Salida mal formada.** Si el revisor devuelve algo que no es el JSON del contrato (provocado en la prueba con una instrucción deliberada), el harness lo registra como incumplimiento y repite la invocación; ningún fichero de informe se escribe con contenido inválido.
11. **Arcos.** Con `formato.capitulos_por_arco: 2` sobre el caso de referencia, la escaleta de alto nivel tiene 3 arcos, cada arco se detalla al llegar a él, cada cierre de arco produce su informe, y la escaleta del arco 2 recibe el informe del arco 1.

Qué ficheros debe haber al final, uno a uno, y cómo comprobar que una ejecución está completa: [`specs/inventario.md`](inventario.md). El inventario vale igual para el runner del hito 2: es la definición de "misma salida".

### 8.3 Métricas de calidad

El usuario define "suficientemente buena" como: **coherente** (no se contradice), **cohesionada** (los hilos se cierran, la voz se mantiene, nadie desaparece) y **fiel a lo que se le pidió** (biblia, escaleta, longitudes). El harness lo traduce a números en cada informe de cierre, calculados solo a partir de los informes y el Estado, sin juicio adicional:

| Métrica | Cómo se calcula | Mide |
|---|---|---|
| Graves por 10 capítulos | Problemas de gravedad 1 en informes de arco y global ÷ capítulos × 10 | Coherencia |
| Aceptados por agotamiento | % de capítulos con `por_agotamiento: true` | Adherencia |
| Hilos previstos sin cerrar | Hilos que la escaleta de alto nivel marca como "cierra" y siguen abiertos en el libro de estado final | Cohesión |
| Aprobados en el primer intento | % de capítulos con `aprobado: 1` | Adherencia |
| Rechazos por voz | % de intentos con algún problema de gravedad 4 | Cohesión de voz |
| Desviación de longitud | Media de |palabras − objetivo| ÷ objetivo sobre los aprobados | Adherencia |

Cada métrica se compara con su umbral de `calidad` (§7.7) y el informe de cierre dice **CUMPLE** o **NO CUMPLE** por métrica. Una novela barata "aguanta" si cumple todas las que cumplió la de referencia con el modelo caro.

### 8.4 Comparar dos ejecuciones

Para decidir el paso 2 y validar el 3 (§7.8) hace falta comparar dos novelas generadas con el **mismo caso de referencia** y distinta configuración: modelo caro frente a barato, o Claude Code frente al runner. Es lo que hace `/novela comparar <caso>` sobre una carpeta `comparativa/caso-NN-<slug>/` que referencia las dos novelas (no las copia: viven en `novelas/` con su historial).

La comparación tiene un bloque **medible** —las métricas de §8.3, palabras, artefactos presentes, invocaciones, volumen y coste por modelo— y un bloque de **lectura** donde cada juicio exige una cita concreta. Termina con una lista de cambios accionables para el harness. Ningún dato se estima: lo que no está disponible se escribe `desconocido`. Detalles: [`comparativa/README.md`](../comparativa/README.md).

---

## 9. Dónde está implementado

El harness son estos ficheros; cada uno documenta su parte. El harness se está **reconstruyendo** sobre esta versión de la spec: la implementación anterior (0.4.0) sigue en el historial de git como referencia.

| Qué | Dónde |
|---|---|
| **Variables que puedes editar** (§7) | [config.json](../config.json) |
| Reglas globales y cómo se usa | [CLAUDE.md](../CLAUDE.md) |
| Permisos para que el bucle corra sin confirmaciones y hook de inmutabilidad (§3.1) | [.claude/settings.json](../.claude/settings.json) |
| Orquestador: comandos (`nueva`, `continuar`, `estado`, `verificar`, `comparar`), etapas, reanudación | [.claude/skills/novela/SKILL.md](../.claude/skills/novela/SKILL.md) |
| Etapa 1 (entrevista con grilling + interrogador) | [procedimientos/interrogatorio.md](../.claude/skills/novela/procedimientos/interrogatorio.md) |
| Inicio y cierre de arco | [procedimientos/arco.md](../.claude/skills/novela/procedimientos/arco.md) |
| Etapa 2 (un capítulo) | [procedimientos/capitulo.md](../.claude/skills/novela/procedimientos/capitulo.md) |
| Etapa 3 (manuscrito + informe global + métricas) | [procedimientos/final.md](../.claude/skills/novela/procedimientos/final.md) |
| Invocar un agente, validar su salida y escribirla | [procedimientos/invocar.md](../.claude/skills/novela/procedimientos/invocar.md) |
| Informe de cierre y motivos de parada | [procedimientos/cierre.md](../.claude/skills/novela/procedimientos/cierre.md) |
| Formato de cada artefacto de la novela | [plantillas/](../.claude/skills/novela/plantillas/) |
| Contratos de los cuatro agentes | [.claude/agents/](../.claude/agents/) — `interrogador.md`, `escritor.md`, `resumidor.md`, `revisor.md` |
| Caso de referencia (idea y entrevista fijas), también entrada del modo de prueba | [pruebas/referencia/](../pruebas/referencia/) |
| Qué produce una ejecución completa y cómo comprobarlo (§8) | [specs/inventario.md](inventario.md) |
| Comparar dos ejecuciones (§8.4) | [procedimientos/comparar.md](../.claude/skills/novela/procedimientos/comparar.md) · [comparativa/](../comparativa/README.md) |
| Novelas generadas | `novelas/<slug>/` |
| Visor de novelas (fuera del harness, §9.2) | [frontend/](../frontend/) |

### 9.1 Cómo se escribe el orquestador

El runner del hito 2 lo escribirá Claude Code **a partir de SKILL.md y los procedimientos**. Para que el porte sea traducción y no interpretación, la skill se redacta como **pseudocódigo numerado con nombres de función estables**, y cada procedimiento implementa una o varias de esas funciones. El runner conserva los nombres. Funciones del harness:

| Función | Qué hace | Dónde |
|---|---|---|
| `comprobar_entorno(config)` | Git, ficheros del harness, `maxTurns` = `turnos_por_invocacion` | SKILL.md |
| `crear_novela(idea, sobreescrituras) → carpeta` | Slug, carpeta, plantillas, `resolver_perfil`, commit | SKILL.md |
| `resolver_perfil(config_raiz, sobreescrituras) → config` | Perfil activo, páginas → capítulos, recortes a límites | SKILL.md |
| `entrevistar(carpeta) → entrevista` | Grilling, o entrevista tomada de fichero (`entrevista:` / `modo-prueba:`) | interrogatorio.md |
| `proponer_escaleta(carpeta) → biblia, escaleta[, arco 1]` | Invocar interrogador, validar límites, presentar, iterar cambios, aprobar | interrogatorio.md |
| `detallar_arco(carpeta, A) → escaleta_arco` | Invocar interrogador en modo arco, validar, commit | arco.md |
| `escribir_capitulo(carpeta, N, K) → texto` | Invocar escritor con las entradas de §5.2, escribir `intento-K.md` | capitulo.md |
| `comprobar_longitud(texto, objetivo, tolerancia) → informe \| ok` | `wc -w`, informe de gravedad 3 si falla | capitulo.md |
| `resumir(carpeta, N, K) → resumen, libro_estado_propuesto` | Invocar resumidor, escribir ambos | capitulo.md |
| `revisar(carpeta, N, K) → informe` | Invocar revisor, validar JSON, recalcular veredicto, escribir | capitulo.md |
| `decidir(carpeta, N, K, informe) → aprobar \| reescribir \| agotar` | Regla de §4.2, `mejor_intento` si agota | capitulo.md |
| `cerrar_capitulo(carpeta, N, K)` | Libro de estado, Estado, commit, progreso | capitulo.md |
| `revisar_arco(carpeta, A) → informe_arco` | Invocar revisor en modo arco, escribir | arco.md |
| `ensamblar(carpeta) → manuscrito` | Capítulos aprobados en orden | final.md |
| `revisar_global(carpeta) → informe_global` | Según tamaño (§4.3) | final.md |
| `calcular_metricas(carpeta) → metricas` | §8.3 | final.md |
| `cerrar(carpeta, resultado, motivo)` | Informe de cierre, Estado, commit | cierre.md |
| `reanudar(carpeta)` | §6.2 | SKILL.md |
| `invocar(agente, modo, modelo, entradas) → salida` | Una invocación con reintentos, validación de forma, registro de volumen | invocar.md |
| `elegir_modelo(agente, K, intento_tecnico, modo) → modelo` | §7.3 | invocar.md |

### 9.2 El visor (`frontend/`)

Una novela a medias está repartida en `estado.json`, `registro.md`, un `informe-K.md` por intento y un fichero por capítulo. Leerla con un editor obliga a cruzar todo eso a mano. El **visor** es una aplicación web local que hace ese cruce y lo enseña.

Qué es y qué no es:

- **Solo lee.** No invoca agentes, no decide nada del flujo y no escribe un solo byte en `novelas/`. Todo lo que muestra lo escribió el harness.
- **No es parte del harness.** Ni el hito 1 ni el hito 2 lo necesitan. Si se borra la carpeta `frontend/` entera, la generación de novelas funciona igual. Por eso no aparece en el inventario de [`specs/inventario.md`](inventario.md) ni en los criterios de aceptación de §8.2.
- **No inventa datos.** Las métricas de calidad (§8.3) las calcula el harness y viven en `informe-cierre.md`: el visor las muestra si existen y, si no, dice que aún no las hay. No las recalcula, para que no pueda haber dos cifras distintas para la misma novela. Sí muestra lo que el Estado ya afirma (qué capítulo está aprobado y en qué intento) y el recuento de palabras de cada intento frente a su longitud objetivo.

Cómo obtiene los datos: un servidor local de solo lectura (`frontend/server/`) conoce la estructura de `novelas/<slug>/` descrita en §3, la interpreta y la sirve como JSON; la web solo pinta. La estructura de carpeta es la misma la genere Claude Code o el runner (§10.1), así que el visor funciona sobre las dos sin saber quién la escribió, igual que `/novela estado` (§10.3, punto 2).

Qué muestra, por novela: el texto para leerlo, el progreso (estado, capítulos con sus intentos, veredictos y problemas por gravedad), los documentos de referencia (biblia, escaletas, libro de estado) y el registro de invocaciones.

Reglas de su código y de sus dependencias: [frontend/CLAUDE.md](../frontend/CLAUDE.md).

---

---

## 10. Hito 2 — El runner contra OpenRouter

El destino del proyecto es generar novelas de 100–200 capítulos con un modelo barato, desatendido. Eso no puede hacerlo una sesión de Claude Code: necesita un **runner** propio (un programa) que hable con OpenRouter. Esta sección fija qué se porta tal cual, qué hay que reimplementar y qué contrato debe cumplir el runner para que todo lo anterior siga valiendo.

### 10.1 Qué se porta sin cambios

| Pieza | Dónde está hoy | En el runner |
|---|---|---|
| Contratos de los cuatro agentes (§5): entradas, salidas, debe/no debe, forma del mensaje final | [.claude/agents/](../.claude/agents/) | Son el *system prompt* de cada llamada. Se copian literalmente; solo se quita la línea de herramientas de lectura |
| Plantillas de artefactos (§3) | [plantillas/](../.claude/skills/novela/plantillas/) | Idénticas. El runner las rellena y las valida con los mismos campos |
| Prompts de invocación (qué se le da a cada agente en cada paso) | [procedimientos/](../.claude/skills/novela/procedimientos/) | Mismo texto; el runner sustituye "lee la ruta X" por el contenido de X en el mensaje, porque el modelo no tiene sistema de ficheros |
| Configuración y perfiles (§7) | [config.json](../config.json) | El mismo fichero, mismo `config.json` congelado por novela. `proveedor: openrouter`, `modelos.*` con identificadores de OpenRouter |
| Estructura de la carpeta de la novela, `estado.json`, `registro.md`, motivos de parada (§6.5) | [plantillas/](../.claude/skills/novela/plantillas/), [cierre.md](../.claude/skills/novela/procedimientos/cierre.md) | Idénticos. Es lo que permite que `/novela estado`, `/novela comparar` y el inventario funcionen sobre una novela generada por el runner |
| Regla de veredicto (§7.5), límites (§6.3), memoria (§7.6), métricas (§8.3), mejor intento (§4.2) | spec + config | Mismas reglas, en código |
| **Quién escribe** | El harness, en los dos hitos | Sin cambios: ya es así en el hito 1 |

### 10.2 Qué hay que reimplementar

| Pieza | Cómo lo hace Claude Code | Cómo lo hará el runner |
|---|---|---|
| Orquestador (etapas, bucle, decisiones, reanudación) | La skill `/novela` leída por Claude en la sesión | Las funciones de §9.1, con los mismos nombres, en código |
| Invocar a un agente | Herramienta `Agent` con subagentes | Una llamada a la API de OpenRouter con el contrato como *system* y el prompt de invocación con los ficheros incrustados; `temperatura` por agente; salida estructurada para el revisor donde el modelo lo admita; validación con esquema JSON |
| Entrevista (etapa 1) | Skill `grilling` en la sesión, o `entrevista: <ruta>` | El runner solo admite la segunda forma: toma `entrevista.md` ya cerrada (escrita a mano, con Claude Code, o la del caso de referencia). No hace preguntas |
| Confirmación de la escaleta | Pregunta en la sesión | Parada limpia con `escaleta.md` en `aprobada: false`; el usuario la aprueba editando el frontmatter o con una opción del runner, y relanza |
| Commits | El orquestador commitea en `novelas/` | Ídem, con git desde el runner. Es lo que da la reanudación y la trazabilidad |
| Turnos por invocación | `maxTurns` del subagente | Tiempo máximo por llamada y número máximo de llamadas por paso |
| Pausa programada | `pausa_cada_capitulos` por el contexto de sesión | Innecesaria: `null`. El contexto lo controla `memoria.*` |
| Volumen y coste (§6.6) | Palabras contadas por el orquestador | Tokens y coste reales de la respuesta de la API en las mismas columnas; `presupuesto_usd_max` activo |
| Escritura de ficheros | El orquestador escribe con sus herramientas | Escritura atómica: temporal + renombrado |

### 10.3 Contrato del runner

El runner está bien si, sobre el caso de referencia:

1. Produce una carpeta `novelas/<slug>/` que pasa la comprobación de completitud de [`specs/inventario.md`](inventario.md) sin ninguna adaptación.
2. `/novela estado` y `/novela comparar` desde Claude Code funcionan sobre esa carpeta sin saber quién la generó.
3. Los criterios de aceptación de §8.2 se cumplen (los que dependen de la sesión —turnos, interrupción manual— se traducen a su equivalente: timeout de llamada, señal de parada).
4. Con la misma configuración de modelos que el paso 2 de §7.8, las métricas de §8.3 quedan dentro de los mismos umbrales.

Lo que **no** se decide aquí: lenguaje, librerías y estructura interna del runner. Se decide cuando se llegue al paso 3 de §7.8 y se anota en el CHANGELOG. Lo que sí queda fijado es que el runner no altera ninguno de los contratos de este documento: si algo del diseño no funciona en el runner, se cambia el diseño aquí primero y después en las dos implementaciones.
