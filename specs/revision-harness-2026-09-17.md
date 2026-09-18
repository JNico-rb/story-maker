# Revisión de ingeniería de harness — 2026-09-17

Revisión completa del proyecto a partir de tres entradas: la spec vigente (1.021 líneas), la implementación (skill, procedimientos, agentes, hook, `config.json`), los **30 defectos** encontrados a mano en el manuscrito de `tecnica-ascensores-peticion-ia-20260916-1719`, y el [análisis de traza del 09-17](../herramientas/trazas/analisis-traza-2026-09-17.md).

Este documento es **entrada para reescribir la spec**, no la spec. Cuando sus propuestas se acepten, van al [CHANGELOG](../CHANGELOG.md) y de ahí a [specs/functional.md](functional.md), en ese orden (regla 6 de CLAUDE.md). Después se borra.

---

## Resumen ejecutivo

El diseño del harness es bueno y las partes que se diseñaron como mecánicas aguantaron. Lo que falla es otra cosa, y es más grave que un umbral mal calibrado:

1. **La matriz de criterios no cubre los defectos que la novela tiene de verdad.** De los 30 defectos verificados, **unos 21 pertenecen a clases que ningún agente tiene el encargo de buscar**. La palabra «gramática» no aparece ni una vez en los cinco contratos. El `0 problemas` de los revisores no es solo un fallo de `haiku`: es la respuesta correcta a las preguntas que se les hicieron.
2. **El sistema se corrige a sí mismo los exámenes.** `calcular_metricas` cuenta problemas de los informes; los informes los escriben los revisores; nadie mide a los revisores. El resultado publicado fue **6/6 CUMPLE** sobre un manuscrito con 13 agramaticalidades elementales. Mientras la única fuente de defectos sea el propio bucle, ninguna métrica de `config.calidad` significa nada, y la pregunta del proyecto —«¿aguanta el modelo barato?»— **no se puede contestar con la instrumentación actual**.
3. **El ajuste de longitud fabrica defectos.** Capítulo 5: intento 1, 821 palabras, «treinta años» aparece 1 vez. Intento 2, ampliado a 1.288, aparece 3 veces. Ampliar un 57 % triplicó el motivo repetido. El defecto D2 de la lista (cinco capítulos pisando el mismo pedal) tiene, al menos en parte, causa en el harness, no en el modelo.
4. **La spec va por delante de la implementación en una versión entera y nada lo detecta.** `config.json` no tiene `resumen_max_palabras`, ni `hoja_continuidad_max_palabras`, ni `rechaza_con_gravedad_1/_2`, ni `entrada_max_palabras_invocacion`; `capitulo.md` no compone la hoja de continuidad, no cuenta el resumen y aplica `rechaza_con_graves`. El [TODO](../TODO.md) §2 lo sabe. Lo que falta no es la lista: es el mecanismo que la habría producido sola el mismo día.
5. **En el hito 1 «lo mecánico lo hace el harness» significa «lo hace un modelo con cuidado»**, y la ejecución demostró que se le olvida: un contador de invocaciones desfasado, un `pal_salida` registrado antes de contar, un informe de cierre que copia contadores en vez de recontar. Tres fallos de contabilidad en una novela de cinco capítulos.

Los puntos 1 y 2 son el trabajo de este ciclo. El resto se ordena detrás.

---

## 1. La matriz de criterios: el hallazgo central

### 1.1 Los 30 defectos contra los cinco criterios

Los criterios vigentes son cinco gravedades: **1** contradicción (continuidad), **2** incumple escaleta (encargo), **3** longitud (harness), **4** voz o tono (encargo), **5** resumen infiel (continuidad).

| Clase de defecto | n | ¿Qué criterio lo cubre? | ¿Quién lo vio? |
|---|---:|---|---|
| **A. Coherencia interna** (plazo contradictorio, anclaje arriba/abajo, Roser antes de existir, fotos inexistentes) | 7 | Gravedad 1 — **sí tiene dueño** | Nadie |
| **B. Verosimilitud técnica** (el multímetro mide «integridad estructural»; el cable como pieza única) | 4 | **Ninguno** | — |
| **C. Mundo post-IA ausente y anacronismo social** (una ciudad gestionada por IA cuyo conflicto depende de una gestora que tarda meses en contestar correos) | 2 | **Ninguno** (el criterio 4 es voz y tono, no presencia del mundo) | — |
| **D. Cohesión estructural** (capítulos 2 y 3 son la misma escena; el motivo repetido tres veces) | 2 | **Ninguno** (encargo solo ve el capítulo N; continuidad busca contradicciones, no repeticiones) | — |
| **E. Erratas y agramaticalidades** (laísmo, «la agua», «había fallido», «La conocimiento») | 13 | **Ninguno** | — |
| **E′. Incoherencias locales dentro de E** (vestíbulo y «unos pasos fuera del edificio» en el mismo párrafo; «vecina de cincuenta años») | 2 | Gravedad 1 — sí tiene dueño | Nadie |
| **A7. Título huérfano** | 1 | Gravedad 2 — sí tiene dueño | Nadie |

**Unos 21 de 30 defectos no tienen dueño en el contrato.** Los otros 9 lo tienen y se escaparon.

Esto cambia la conclusión del análisis de traza. Su §3.1 decía «el revisor no discrimina» y proponía reprocesar con `opus`. Sigue siendo buena idea, pero **`opus` también habría devuelto 0 en la clase E**, porque a nadie se le pidió que mirara la lengua. Cambiar de modelo no arregla una pregunta que no se hace.

### 1.2 La frontera problema/observación no está definida, y se usó como escape

El informe global vio el defecto A3 —las fotos que Marisa nunca tomó— y lo clasificó como **observación**, con el argumento textual de que «no contradice el canon o estado, es compresión narrativa». El revisor encontró el defecto y lo degradó.

La spec no define en ningún sitio qué separa `problemas` de `observaciones`. Es la clase de hueco que un modelo pequeño rellena siempre hacia el lado barato.

**Propuesta:** definirla de forma comprobable, no de criterio.
- Es **problema** si se puede citar literalmente el texto que falla y nombrar el fichero o el pasaje con el que choca.
- Es **observación** si no hay cita o no hay contrario: es una impresión.
- «No contradice el canon» deja de ser argumento válido cuando lo que se contradice es **otro capítulo o el propio texto**: eso es exactamente la gravedad 1.

### 1.3 Toda afirmación de un revisor debe traer cita, y la cita la verifica el harness

Hoy un problema lleva `donde`, `que`, `por_que` — tres campos en prosa. Nada obliga a que exista en el texto, y nada lo comprueba.

**Propuesta:** un campo `cita` obligatorio con la cadena literal del capítulo, y un paso mecánico en `revisar()`: el harness hace `grep -F` de cada cita sobre `intento-K.md`; **la que no aparece, se descarta y se registra como `cita_no_verificada`**. Cuesta cero invocaciones, convierte la salida del revisor de opinión en evidencia, y da gratis una métrica nueva —fracción de problemas con cita verificable— que mide la alucinación del revisor.

Es el mismo mecanismo que §4.3 ya exige a `erratas.md` («la cita exacta tal como está en el manuscrito»). Lo que propongo es subirlo aguas arriba, donde todavía sirve para decidir.

### 1.4 Un agente nuevo: el corrector

Las clases B y E comparten tres propiedades: se ven **leyendo solo el capítulo**, son **verificables con una cita**, y no las cubre nadie. Es el perfil de un agente propio, por el mismo argumento que la spec §2 ya usó para partir el revisor en dos: un agente con dos trabajos hace mal los dos.

| | |
|---|---|
| **Nombre** | `corrector` |
| **Pregunta** | *¿Está bien escrito y es creíble lo que afirma?* |
| **Entrada** | Solo `intento-K.md` y la sección «Tono y voz» + «Reglas inviolables» de la biblia. ~1.500 palabras: **la invocación más barata del sistema** |
| **Salida** | El JSON de §5.6, con `cita` obligatoria |
| **Gravedad 6 — lengua** | Agramaticalidad, laísmo/leísmo, concordancia, palabra inexistente, frase sin sentido. Cita literal obligatoria |
| **Gravedad 7 — verosimilitud** | Afirmación técnica o factual que un lector competente en el dominio rechazaría (un multímetro que mide integridad estructural) |
| **No debe** | Juzgar trama, continuidad, escaleta ni longitud; proponer reescrituras; reportar cuestiones de gusto |

Coste: una invocación por intento, la más barata de todas. En la ejecución trazada habrían sido 9 invocaciones más sobre 41, con la entrada más pequeña del sistema.

### 1.5 Dos criterios más, sin agente nuevo

- **Gravedad 8 — repetición y estancamiento**, para el revisor de **encargo**: recibe además la entrada N−1 de la escaleta y el resumen N−1, y contesta si este capítulo repite escena, función o motivo del anterior sin avanzar. Es lo que caza D1.
- **Presencia del mundo**, para el revisor de **encargo** dentro de su criterio 4: la biblia describe un mundo; si fuera de los párrafos expositivos el capítulo transcurre en el presente, es un problema de gravedad 4. Es lo que caza C2.

### 1.6 Las reglas inviolables, como lista de comprobación

El defecto A2 es el más caro de la lista: la premisa —la IA no puede pedir ayuda explícitamente— se desmonta en el clímax. Es una contradicción con la biblia, gravedad 1 pura, y se escapó porque «busca contradicciones en 17.000 palabras» es una tarea sin forma.

La biblia **ya tiene** una sección «Reglas inviolables», numeradas, 3 a 7. **Propuesta:** el revisor de continuidad, en modo capítulo, recorre esa lista y dice de cada regla si el capítulo la respeta, una línea por regla. Es el mismo truco que el revisor de encargo ya aplica a los sucesos («recorre la entrada N suceso por suceso»), y es lo que los modelos pequeños hacen bien: recorrer una lista corta, no buscar en un pajar.

Añadido barato: `validar_canon` hoy solo cuadra números. Debe comprobar también que **las reglas inviolables son compatibles con la escaleta** —si el clímax previsto exige que la IA hable claro, la regla y la escaleta se contradicen antes de escribir una palabra—. A2 se habría cazado en la etapa 1, por cero palabras de manuscrito.

### 1.7 Consecuencia sobre la regla de veredicto

Con ocho gravedades hay que decir cuáles rechazan. Propuesta de partida, para calibrar después con datos y no ahora:

| Gravedad | Rechaza con | Por qué |
|---|---|---|
| 1 contradicción | 1 | Entra en el libro de estado y envenena lo que viene detrás |
| 2 escaleta · 7 verosimilitud · 8 repetición | 2 | Daño acotado al capítulo |
| 4 voz · 5 resumen | 2 | Igual |
| 6 lengua | **3** | Barata de corregir en una reescritura, y es señal dura: tres agramaticalidades en 1.500 palabras no es ruido |
| 3 longitud | 1 | Ya es así; lo genera el harness |

Y una consecuencia que hay que aceptar con los ojos abiertos: **con estos criterios los capítulos de la ejecución trazada habrían sido rechazados casi todos**, y `reescrituras_max: 2` no habría bastado. Eso no es un argumento para relajar los criterios: es el dato que hoy no se tiene.

---

## 2. Medir desde fuera: por qué hacen falta los evaluadores

El punto 2 del resumen es el que sostiene todo lo demás. Hoy el sistema no tiene **ninguna** fuente de defectos que no sea él mismo. Cualquier cambio en los criterios se evaluaría con el instrumento que el cambio pretende arreglar.

Lo que hace falta es una capa de medición **fuera del bucle**, con verdad de campo. Y existe ya: **tus 30 defectos son el primer conjunto etiquetado del proyecto.** Es el activo más valioso que ha producido esta ejecución, más que la novela.

El diseño está en la §5 de este documento. La regla que no se toca: spec §9.3 regla 2, **la observabilidad nunca es puerta del flujo**. Los evaluadores no aprueban ni rechazan capítulos. Miden a los revisores. Y cuando un evaluador queda calibrado, su prompt **asciende** a criterio de un agente del harness. Ese es el circuito de aprendizaje: Langfuse es el laboratorio, el harness es producción.

---

## 3. Lo que sobra, lo que falta y lo que está duplicado

### 3.1 Sobra

| Qué | Por qué | Coste de quitarlo |
|---|---|---|
| **`/novela comparar` y `comparativa/`** | Un comando, un procedimiento de 47 líneas, una carpeta con plantillas y una sección de spec (§8.4) para algo usado **cero veces**. Su trabajo —comparar dos ejecuciones— lo hacen mejor los análisis de traza, que ya existen y son prosa | Bajo. Quitar el comando, dejar el `README.md` como nota de intención |
| **`perfiles.*.paginas_objetivo`** | `null` en los cuatro perfiles. Añade una rama en `resolver_perfil`, un motivo de parada y un párrafo de spec. Nunca se ha usado | Muy bajo |
| **`Edit(/novelas/**)` en `settings.json`** | Contradice la regla que el propio proyecto defiende: los artefactos se escriben enteros, **nunca** se editan en sitio. El permiso abre la puerta a lo que el hook luego tiene que cerrar | Nulo |

No propongo quitar el **estudio** (`frontend/`), pero sí decir en voz alta lo que es: **está compitiendo por el ciclo con el cuello de botella real**. Hace más fácil encargar novelas que todavía no aguantan una lectura. Recomendación: congelarlo donde está —queda su prueba de punta a punta, TODO §3— y gastar el ciclo siguiente en la matriz de criterios y en la medición.

### 3.2 Falta

| Qué | Dónde iría | Impacto |
|---|---|---|
| Criterios de lengua, verosimilitud, repetición y presencia del mundo | §5.4, §5.5, agente `corrector` nuevo | **Alto** |
| `cita` obligatoria verificada con `grep` por el harness | §5.6, `capitulo.md` | **Alto** |
| Definición comprobable de problema vs observación | §5.6 | Alto |
| Reglas inviolables como lista de comprobación por capítulo | §5.5, `capitulo.md` | Alto |
| Conjunto etiquetado de defectos y recall por clase | §8 nueva, `pruebas/defectos/` | **Alto** |
| `desviacion_longitud` **con signo** | Está en spec §8.3, **falta** en `final.md` | Medio |
| Paso de pulido de lengua fuera del bucle (§3.4) | §4.3 | Medio |
| Verificación de deriva spec ↔ implementación | `herramientas/comprobar.sh` | **Alto** |
| Versión de spec enlazada a la de `config.json` | Frontmatter de la spec + `comprobar_entorno` | Medio |

### 3.3 Duplicado

La misma regla de inmutabilidad está escrita **cuatro veces**: spec §3.1, CLAUDE.md regla 2, SKILL.md §9 y las cabeceras de `inmutables.sh`. Las cuatro son correctas hoy; el TODO ya documenta cuatro desincronizaciones encontradas a mano el 17/09.

**Propuesta:** un hogar normativo (la spec) y punteros en el resto. CLAUDE.md y SKILL.md citan la sección, no la reescriben. El hook conserva su comentario, porque el código debe explicarse solo. Una regla escrita en cuatro sitios son cuatro sitios donde puede envejecer.

### 3.4 El agujero de las erratas

`erratas.md` es una buena decisión de diseño con una consecuencia práctica mala: **la novela se entrega con 13 agramaticalidades y el usuario las arregla a mano, sin herramienta**. En esta ejecución ni eso: el informe global devolvió 0 problemas y `erratas.md` salió vacío.

El motivo para no aplicarlas es sólido —reescribir un capítulo cerrado invalida su resumen y en cascada todos los libros de estado—, pero **no vale para la clase E**: cambiar «la agua» por «el agua» no cambia ni un hecho del resumen ni una línea del libro de estado.

**Propuesta: un paso de pulido, fuera del bucle, opcional y determinista.**
- Produce un artefacto **nuevo**, `manuscrito-pulido.md`. No toca ningún capítulo aprobado ni el manuscrito.
- Aplica **solo** erratas de gravedad 6 (lengua), y las aplica el harness con sustitución literal de cadena, verificada con `grep` antes y después. Ningún modelo edita texto.
- Cualquier errata que no sea de lengua se queda en `erratas.md` para el usuario, como ahora.

Así la inmutabilidad sigue intacta, el libro de estado sigue siendo cierto, y el lector recibe un texto limpio.

---

## 4. La orquestación: qué aguanta y qué no

### 4.1 Lo que aguanta, y conviene no tocarlo

Escrito porque una revisión que solo enumera fallos miente por omisión. Estas decisiones son buena ingeniería de harness y se sostuvieron en dos ejecuciones:

- **Solo el harness escribe.** Elimina una clase entera de fallos y es lo que hace portables los contratos.
- **La carpeta como único estado, y git como registro de transacciones.** `descartar()` con `git checkout` es una reanudación que funciona de verdad; la ejecución trazada la ejercitó y no perdió nada aprobado.
- **Contratos como prompts con forma verificable.** Cero fallos de herramienta en 78 invocaciones entre las dos ejecuciones.
- **Ajustes de longitud con presupuesto propio.** 3 de 3 en la ejecución trazada; en la de referencia, ese mismo patrón condenó un capítulo.
- **Partir la revisión en dos preguntas.** La dirección es correcta; lo que este documento dice es que faltan preguntas, no que sobren agentes.

### 4.2 Lo que no aguanta: lo mecánico no es mecánico

La spec dice (regla 4, §1.2) que todo lo decidible sin modelo lo hace el harness. En el hito 1 **el harness también es un modelo**, así que «mecánico» significa «el modelo se acordó de ejecutar `wc -w`». La ejecución trazada demuestra que no siempre se acuerda: contador de `revisor_continuidad` desfasado en uno, `pal_salida` del resumidor registrado antes de contar, informe de cierre copiando contadores en lugar de recontar filas. Coste publicado un 9 % por debajo del real.

**Propuesta: hacer ejecutable lo que hoy es prosa.** No un framework —el TODO ya descartó bien vitest y pytest— sino cuatro guiones pequeños en `herramientas/`, que la skill **llama** en vez de describir:

| Guion | Qué hace | Sustituye a |
|---|---|---|
| `contar.sh <fichero> <objetivo> <tolerancia>` | `wc -w`, compara, devuelve JSON `ok` / `rechazo` con suelo y techo | `comprobar_longitud` en prosa |
| `verificar-citas.sh <informe.json> <capitulo.md>` | `grep -F` de cada `cita`; devuelve las no verificadas | El paso nuevo de §1.3 |
| `metricas.py <carpeta>` | Recuenta **desde `registro.md`**, trata filas `pendiente` y de corrección, calcula la tabla de §8.3 con la desviación con signo | `calcular_metricas` en prosa y los tres fallos de contabilidad |
| `comprobar.sh` | Claves `config.*` citadas ↔ existentes, frontmatter de los cinco agentes ↔ `config.json`, versión de spec ↔ versión de config | La revisión manual del 17/09 |

Esto **no** rompe el no objetivo de §1.3 («código propio en el núcleo del hito 1») más de lo que ya lo hace `inmutables.sh`, y por la misma razón: lo que no debe interpretarse, no se interpreta. Y los cuatro se portan al hito 2 sin tocar una línea, porque leen la carpeta, que §10.1 declara idéntica.

Prioridad dentro de los cuatro: **`comprobar.sh` primero** —es el que impide que vuelva a pasar lo del punto 4 del resumen— y **`metricas.py` después**.

### 4.3 La validación de artefactos es prosa

`invocar.md › extraer()` valida así: «frontmatter con `capitulo`, `intento`, `hilos_abiertos`, `hilos_cerrados`, `personajes`; secciones Hechos, Cambios en personajes…». Eso es un esquema escrito en castellano y comprobado por un modelo. Los siete incumplimientos de contrato de la ejecución trazada son de esta familia.

**Propuesta:** un esquema por artefacto en `plantillas/esquemas/` (JSON Schema para los JSON, lista de campos obligatorios para los frontmatter) y la validación como llamada, no como lectura. Y subir a contrato la tolerancia que el harness ya practicó sobre la marcha —valla de código alrededor del JSON, ruido tras el delimitador—, que es la propuesta 5 del análisis de traza y sigue siendo correcta.

### 4.4 El objetivo de longitud, contra el modelo barato

El análisis de traza recomienda no bajar `palabras_por_capitulo` porque sería tratar el síntoma. **No estoy de acuerdo, y tengo el dato:** el intento 1 del capítulo 5 tenía 821 palabras y una aparición de «treinta años»; ampliado a 1.288, tres. La ampliación no añadió trama: añadió relleno, y el relleno es exactamente el defecto D2 de tu lista.

Si eso se confirma, el objetivo de longitud no es un síntoma: es **una causa**. La prueba es barata y no cuesta invocaciones: comparar motivos repetidos entre el intento corto y el ampliado en los capítulos 1, 2 y 5, que son los tres que se ampliaron.

Propuesta en función del resultado: **tolerancia asimétrica** (por ejemplo −25 % / +10 %) en lugar de bajar el objetivo. Deja al modelo entregar lo que la escena da de sí sin premiar el relleno, y conserva el techo, que sí protege de otra cosa.

---

## 5. Evaluadores en Langfuse

### 5.1 Qué son y qué no son

- **No son puerta del flujo.** El harness no los llama durante la generación (spec §9.3 regla 2). Corren después, sobre ficheros ya escritos.
- **Su sujeto no es la novela: son los revisores.** La pregunta que contestan es *¿vio el revisor lo que ve un juez independiente?* De ahí sale el número que hoy no existe: el **recall del revisor por clase de defecto**.
- **Cuando uno queda calibrado, su prompt asciende** a criterio de un agente del harness. Langfuse es el banco de pruebas de los criterios antes de meterlos en el bucle.

### 5.2 Prerrequisito duro

Los evaluadores en línea de Langfuse puntúan observaciones por su `input`/`output`. Hoy **las 50 generaciones exportadas los traen a `null`** (análisis de traza §4): no hay nada que puntuar. Antes de crear un solo evaluador hay que arreglar el exportador:

1. `input` = rutas y, para lo que se va a evaluar, **el contenido** del capítulo; `output` = el texto entregado o el JSON del informe.
2. `resultado:` con dos puntos en la expresión regular, fusión de las filas `pendiente`, filtro de las filas de corrección.
3. `trace_id` determinista derivado del slug, y `start_time`/`end_time` desde `fecha_hora`.

Sin el punto 1 no hay evaluación posible; los otros dos evitan puntuar dos veces la misma invocación. Son los ítems 9 del análisis de traza y están fuera del harness: se pueden hacer sin riesgo.

Nota: subir el texto del capítulo a Langfuse es publicarlo en un servicio externo. Es tu propio contenido y el proyecto ya sube trazas, pero conviene que la decisión sea explícita en el CHANGELOG.

### 5.3 El conjunto etiquetado

`pruebas/defectos/ascensores-20260916.md`: un ítem por defecto, con **clase, cita literal, capítulo y por qué es un defecto**. Tus 30, tal cual. Sube a Langfuse como dataset `defectos-ascensores-v1`, con `expectedOutput` = clase + cita.

Es lo que convierte «el revisor no discrimina» en un número por clase. Y es reutilizable: cada novela nueva que revises a mano añade ítems.

### 5.4 Los evaluadores

Nombrados por lo que miden, no por quién lo mide. Los dos primeros son **deterministas**: no todo evaluador tiene que ser un juez LLM, y donde una cuenta basta, una cuenta es mejor.

| # | Score | Tipo | Sobre qué corre | Qué mide |
|---|---|---|---|---|
| 1 | `cita_verificable` | Determinista | Informes de los revisores | Fracción de `problemas` cuya cita aparece literalmente en el capítulo. Mide alucinación del revisor |
| 2 | `redundancia_resumen` | Determinista | Resúmenes N y N−1 | Solapamiento de sucesos entre capítulos consecutivos. Caza D1 sin modelo |
| 3 | `lengua_erratas` | Juez | Texto del capítulo | Agramaticalidades por cada 1.000 palabras, **con cita obligatoria**. Clase E |
| 4 | `verosimilitud_dominio` | Juez | Texto del capítulo | Afirmaciones técnicas que un competente rechazaría. Clase B |
| 5 | `coherencia_interna` | Juez | Capítulo + libro de estado + resúmenes previos | Contradicciones, con cita. Clase A |
| 6 | `mundo_presente` | Juez | Capítulo + sección «El mundo» de la biblia | 0–1: ¿se nota el mundo fuera de los párrafos expositivos? Clase C2 |
| 7 | `recall_revisor` | Derivado | Informes + salidas de 3–6 | Defectos que el evaluador encuentra **y** el informe también ÷ los que encuentra el evaluador. **Es el número que decide si `haiku` puede revisar** |

Reglas de construcción, sacadas de la propia skill de Langfuse:

- **El juez nunca es del mismo modelo que escribió.** Escritor `haiku`, jueces `opus` o `sonnet`. Un modelo que se evalúa a sí mismo es el fallo que esta ejecución ya cometió dentro del bucle.
- **Antes de crear cada evaluador, comprobar qué observaciones alcanza su filtro**, para no puntuar dos veces la misma invocación: con las filas `pendiente` sin fusionar, la inflación es del 22 %.
- **Calibrar antes de usar.** Modo simple del `judge-calibration`: exactitud contra el dataset. Un juez de lengua que no marca «la agua» no sirve, y se sabe en una pasada.
- **Un score, una cosa medible.** Nada de un `calidad_global` de 1 a 10: no cambia ninguna decisión.

### 5.5 Orden de trabajo

1. Arreglar el exportador (`input`/`output`, `resultado:`, `pendiente`, `trace_id`). Sin esto no hay nada que puntuar.
2. Escribir `pruebas/defectos/ascensores-20260916.md` con tus 30 y subirlo como dataset.
3. Evaluadores 1 y 2, deterministas: dan señal el mismo día y no cuestan tokens.
4. Evaluador 3 (`lengua_erratas`), calibrado contra el dataset. Es el que tiene verdad de campo más limpia: 13 ítems verificables uno a uno.
5. Evaluadores 4–6 y el derivado 7.
6. **Ascenso:** los prompts de 3 y 4 calibrados pasan a ser el contrato del agente `corrector` (§1.4). El de 6, criterio del revisor de encargo.

Nota de esta sesión: no hay servidor MCP de Langfuse conectado ni acceso a las credenciales (`.claude/settings.local.json` está denegado por `settings.json`, y con razón). Todo lo anterior es diseño; la creación de los evaluadores requiere una sesión con acceso.

---

## 6. Cómo debería quedar la spec

Es el objetivo final que planteaste, así que va como propuesta concreta y no como principios sueltos.

### 6.1 El problema de la spec actual

No es que esté mal escrita: es de las mejores que he leído en un proyecto de este tamaño, y su costumbre de explicar el porqué de cada regla es lo que hace que el proyecto se pueda retomar. El problema es que **son dos documentos en uno**:

- **La ley**: qué hace el sistema, qué contrato cumple cada pieza, qué límites hay. Es lo que un agente debe poder consultar mientras trabaja.
- **El cuaderno de laboratorio**: §8.5, §8.6 y los párrafos de motivación incrustados en las tablas. 250 líneas de hallazgos de ejecuciones concretas.

Mezclados, la ley pesa 1.021 líneas. Ningún agente la lee entera mientras hace otra cosa, y lo que no se lee, se incumple.

### 6.2 La reorganización que propongo

| Fichero | Qué lleva | Tamaño objetivo |
|---|---|---|
| `specs/functional.md` | Solo normativo: glosario, artefactos, flujo, contratos, límites, configuración, verificación. Cada regla con un puntero de una línea al hallazgo que la motivó | ~500 líneas |
| `specs/hallazgos.md` | §8.5, §8.6, los diagnósticos de volumen y los análisis de traza resumidos. Es el «por qué» completo | libre |
| `CHANGELOG.md` | Sigue igual: decisiones y descartes | libre |

Nada del porqué se pierde: cambia de sitio y se enlaza. Es la diferencia entre una ley con exposición de motivos aparte y una ley con la exposición dentro de cada artículo.

### 6.3 Las tres cosas que la spec nueva debe tener y hoy no tiene

1. **Columna de quién impone cada regla.** Hoy una regla que bloquea el hook y una regla que solo está escrita en un prompt se leen igual. Propuesta: cada regla normativa lleva una marca — `hook` · `guion` · `harness` · `prompt` — y el orden es también el de fiabilidad. Todo lo marcado `prompt` es, por definición, lo que puede derivar sin que nadie se entere: es la lista de lo que hay que vigilar.
2. **Modos de fallo observados por contrato.** Cada agente de §5 termina con una tabla corta: qué se le ha visto hacer mal, en qué ejecución. Es lo que hace que un prompt mejore en vez de crecer.
3. **Versión.** La spec lleva `spec_version` en frontmatter, `config.json` lleva el mismo número, y `comprobar_entorno` los compara. Hoy la spec está en «0.8.0 + parches» y el `config.json` en `version: 4`, y averiguarlo cuesta leer el CHANGELOG entero.

### 6.4 Lo que la spec debe dejar de prometer

Dos cosas que hoy afirma y la ejecución no sostiene:

- «El harness comprueba la forma de cada salida», «el harness cuenta», «el harness recalcula»: verdad en el hito 2, **aspiración en el hito 1** mientras esos pasos sean prosa. O se hacen ejecutables (§4.2) o la spec dice que en el hito 1 son responsabilidad del orquestador-modelo y pueden fallar. Lo segundo es peor pero es honesto; lo primero es mejor y cuesta cuatro guiones.
- Las métricas de `calidad` como respuesta a «¿aguanta el modelo barato?». Mientras se calculen sobre los informes de los propios revisores, miden al revisor. La spec debería decirlo donde las define, y apuntar a la medición externa (§5) como la que contesta esa pregunta.

---

## 7. Orden de trabajo propuesto

| # | Qué | Impacto | Coste | Toca |
|---|---|---|---|---|
| 1 | `herramientas/comprobar.sh` (claves de config, frontmatter de agentes, versiones) | Alto | Bajo | `herramientas/` |
| 2 | Cerrar el arrastre de la 0.8.0 del TODO §2, con el `comprobar.sh` ya puesto | Alto | Medio | config, SKILL, capitulo, agentes |
| 3 | Matriz de criterios: `corrector`, gravedades 6–8, `cita` verificada, problema vs observación, reglas inviolables como checklist | **Alto** | Medio | spec §5, §7.5, agentes, `capitulo.md` |
| 4 | Conjunto etiquetado con tus 30 defectos | Alto | Bajo | `pruebas/defectos/` |
| 5 | Arreglo del exportador y evaluadores 1–3 en Langfuse | Alto | Medio | `herramientas/trazas/` |
| 6 | `metricas.py` recontando desde `registro.md`, con desviación con signo | Medio-alto | Bajo | `herramientas/`, `final.md` |
| 7 | Reorganización de la spec (normativo / hallazgos, columna de enforcement, versión) | Medio-alto | Medio | `specs/` |
| 8 | Paso de pulido de lengua fuera del bucle | Medio | Bajo | spec §4.3, `final.md` |
| 9 | Prueba de la hipótesis de la ampliación y, si se confirma, tolerancia asimétrica | Medio | Muy bajo | `config.json`, spec §4.2 |
| 10 | Quitar `comparar`, `paginas_objetivo` y `Edit(/novelas/**)` | Bajo | Muy bajo | skill, config, settings |

Del 1 al 9, primero CHANGELOG y spec, después implementación (regla 6 de CLAUDE.md). El 5 está fuera del harness y no necesita ese paso.

---

## 8. Lo que no propongo, y por qué

- **Volver a `opus` en todo.** El problema no es solo el modelo: 21 de 30 defectos no los habría visto tampoco, porque nadie los busca. Primero los criterios, después el modelo.
- **Subir `reescrituras_max`.** En la ejecución trazada se consumió **una** reescritura en toda la novela. El presupuesto sobra; lo que falta es que alguien pida corregir algo.
- **Que el harness aplique las erratas sobre capítulos aprobados.** La razón de la spec es correcta y no ha cambiado. El pulido de §3.4 es otra cosa: artefacto nuevo, sustitución literal, cero modelos.
- **Meter los evaluadores en el bucle.** Añadiría red y latencia a un bucle cuyo mérito medido es no tener ninguna de las dos. Y un evaluador que decide es un revisor: entonces va en el harness, con contrato, no en Langfuse.
- **Un framework de tests.** Cuatro guiones y quince líneas de CI, como ya decía el TODO. Lo que cambia respecto al TODO es que dejo de considerarlo «sin decidir»: es el punto 1 de la lista.
- **Tocar los prompts de los agentes por gusto.** Todo lo que propongo sobre ellos sale de un defecto concreto y verificado, con su cita.
