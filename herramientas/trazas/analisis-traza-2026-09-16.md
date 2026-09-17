# Análisis de la traza `novela tecnica-ascensores-peticion-ia`

**Traza**: `89766b6a9c669d06a49d8d38fe047775` (Langfuse, proyecto «My Project») · 122 observaciones · exportada el 2026-09-16 a las 16:25.
**Ejecución trazada**: 2026-09-16, 10:38 → 14:21. Perfil `relato`, 5 capítulos, 1 arco, los cinco agentes en `opus`. Es la **ejecución de referencia** de [spec §8.5](../../specs/functional.md).
**Alcance**: la traza es una proyección de `registro.md` (100 filas). Donde traza y registro discrepen, manda el registro; aquí no he encontrado discrepancias de contenido, sí de forma (§4).

> **Nota de método**: el MCP de Langfuse no estaba disponible en la sesión (`MCP_DOCKER` cerró la conexión). Los datos se recuperaron contra la API REST. Los endpoints `/api/public/traces` y `/api/public/observations` devuelven ahora **410 Gone** para esta organización; el sustituto es `GET /api/public/v2/observations?fromStartTime=…&toStartTime=…&traceId=…`, y **hay que pedir `&fields=core,io,metadata`**: sin ese parámetro `input`, `output` y `metadata` vuelven a `null` y la traza parece vacía. Conviene anotarlo en el README de la herramienta.

---

## Resumen ejecutivo

La ejecución terminó en **ÉXITO técnico y 0/5 en calidad**: 38 invocaciones, cero fallos técnicos, cinco capítulos cerrados, ninguna métrica de calidad cumplida. El harness funcionó; lo que falló fue el **bucle de decisión** que rodea a los agentes.

Tres cosas que la traza deja ver y que el informe de cierre no:

1. **Ningún capítulo se aprobó al primer intento, y no por casualidad**: los cinco intentos nº 1 recibieron *exactamente* 3 problemas. Con `veredicto.rechaza_con_graves = 1` la puerta rechaza con un solo hallazgo grave, así que el 0 % de aprobación al primer intento no mide la calidad del escritor: mide el umbral. Es el hallazgo de más impacto.
2. **El escritor se pasa de largo de forma sistemática**: 11 de 13 intentos por encima del objetivo, media +10,5 %. No es ruido, es sesgo, y dos intentos murieron por eso.
3. **El coste de contexto crece con el capítulo y ya es 50:1**: 412.877 palabras leídas para producir un manuscrito de 8.271. En perfil `relato` (5 capítulos) se aguanta; en `novela` (30) no.

Las tres correcciones de flujo que la traza justifica (longitud, mejor intento, dos revisores) **ya están en el árbol de trabajo sin commitear** (§2). Este informe las valida contra los datos y se centra en lo que sigue abierto.

---

## 1. Los hechos

### 1.1 Capítulo a capítulo

| Cap | Intentos | Cierre | Veredicto del intento 1 | Minutos |
|---|---|---|---|---|
| 01 | 2 | aprobado (2) | RECHAZADO · 3 problemas (1 grave, 2 leves) | 17 |
| 02 | 2 | aprobado (2) | RECHAZADO · 3 problemas (1 grave, 2 leves) | 20 |
| 03 | 3 | **agotamiento** (1) | RECHAZADO · 3 problemas (1 grave, 2 leves) | 17 |
| 04 | 3 | aprobado (3) | RECHAZADO · 3 problemas (3 graves, 0 leves) | 33 |
| 05 | 3 | **agotamiento** (2) | RECHAZADO · 3 problemas (2 graves, 1 leve) | 44 |

Los tres capítulos que llegaron a aprobarse lo hicieron con la misma puntuación: **1 problema leve, 0 graves** (el 04 con cero). No hay ningún caso intermedio. La puerta es binaria en la práctica.

Los minutos por capítulo crecen a partir del 03 (17 → 33 → 44) mientras la longitud del capítulo no crece. Lo que crece es el contexto de entrada.

### 1.2 Volumen por agente

| Agente / modo | n | Palabras entrada | Palabras salida | Entrada por invocación |
|---|---:|---:|---:|---:|
| escritor / capítulo | 6 | 65.789 | 7.811 | 10.964 |
| escritor / capítulo (reescritura) | 8 | 119.268 | 13.733 | 14.908 |
| interrogador / propuesta | 1 | 1.201 | 4.378 | 1.201 |
| resumidor / capítulo | 11 | 46.217 | 51.144 | 4.201 |
| revisor / capítulo | 11 | 157.303 | — | 14.300 |
| revisor / global | 1 | 23.099 | — | 23.099 |
| **Total** | **38** | **412.877** | **77.066** | |

**49,9 palabras leídas por cada palabra de manuscrito.** El revisor se lleva el 38 % de la entrada total; el escritor, el 45 %. Reducir contexto hay que hacerlo en los dos, no solo en uno.

La entrada por invocación crece con el capítulo: el escritor pasó de ~16.900 palabras en el cap. 05 intento 1 a 19.410 en el intento 2; el revisor, de 18.570 a 19.161 dentro del mismo capítulo. Con `memoria.resumenes_completos_ultimos = null` y `capitulo_anterior_integro = true`, ese crecimiento es lineal en el número de capítulos.

### 1.3 Longitud

13 mediciones, objetivo 1.500, margen 1.200–1.800:

`1500 · 1613 · 1433 · 1474 · 1660 · 1940 · 1879 · 1606 · 1687 · 1661 · 1612 · 1737 · 1742`

- Media **1.657** (+10,5 % sobre el objetivo), mediana 1.660.
- **11 de 13 por encima del objetivo**; solo dos por debajo, los dos en el capítulo 02.
- Dos por encima del techo (1.940 y 1.879), ambos en el capítulo 03.
- El margen de ±20 % absorbe el sesgo, pero lo absorbe *por arriba*: el sistema opera de hecho en la franja 1.500–1.800, no en 1.200–1.800.

---

## 2. Lo que la traza confirma y ya está corregido en el árbol de trabajo

Estas cuatro correcciones están escritas en `SKILL.md` y `procedimientos/capitulo.md` pero **sin commitear**. La traza es la evidencia de que apuntan al sitio correcto; lo que falta es una ejecución que lo demuestre.

| Lo que pasó | Dónde se ve | Corrección presente |
|---|---|---|
| El rechazo por longitud consumía presupuesto de reescritura. En el cap. 03 los intentos 2 y 3 murieron por longitud (1.940 y 1.879) sin llegar al revisor, y el capítulo se cerró con el intento 1, **con su problema de gravedad 1 sin corregir**. Se gastaron dos invocaciones del escritor para acabar peor que antes de empezar. | `03 · 12:53` y `03 · 12:56` | `limites.ajustes_longitud = 2` y la rama `ajustar` de `decidir`, que no consume reescritura. Además el prompt del escritor pasa ahora **los dos** informes (el de longitud y el de contenido pendiente), que era el fallo real: el intento 2 del cap. 03 recortó sin corregir. |
| La regla de mejor intento premiaba contar problemas. En el cap. 05 eligió el intento 2 (1 problema) sobre el 3 (2 problemas), y el 3 era el que **cerraba el hilo «Reme y el vecindario»**. De ahí sale directamente `hilos_sin_cerrar = 1`. | `05 · 14:16 · mejor_intento = 2` | Paso 2 de `mejor_intento`: los cierres de escaleta antes que el recuento, comparando `hilos_cierra` de la escaleta contra `hilos_cerrados` del frontmatter del resumen. |
| Un único agente `revisor` mezclaba «¿está lo que se pidió?» con «¿se contradice algo?». En la traza **no hay forma de saber qué revisor encontró qué**: 11 generaciones idénticas llamadas `revisor / capitulo`. | Toda la traza | Split en `revisor-encargo` (gravedades 2, 4) y `revisor-continuidad` (1, 5), en paralelo, con unión de problemas y veredicto recalculado por el harness. |
| El harness registró `longitud: ok` antes de comparar y tuvo que corregir la fila. | `03 · 12:53 · CORRIGE la fila anterior` | `comprobar_longitud` fija el orden explícitamente: «primero cuentas, después registras». |

**Riesgo residual del split de revisores**: con dos revisores independientes el número de problemas por intento sube mecánicamente (dos fuentes, sin deduplicar más allá de los duplicados exactos). Si el umbral de veredicto no se toca a la vez (§3.1), el split **empeora** la tasa de aprobación al primer intento en lugar de mejorarla. Las dos cosas hay que calibrarlas juntas, no una detrás de otra.

---

## 3. Lo que sigue abierto, por impacto

### 3.1 La puerta de veredicto es prácticamente inalcanzable · impacto alto

`veredicto.rechaza_con_graves = 1` significa: **un solo hallazgo de gravedad 1 o 2 rechaza el capítulo**. Con dos revisores que siempre encuentran algo en un texto de 1.600 palabras recién escrito, el resultado no es una medida de calidad, es una constante.

La evidencia: cinco intentos nº 1, cinco veces exactamente 3 problemas. Y los tres capítulos aprobados lo fueron con 0–1 problemas leves. No existe la zona intermedia porque el umbral no la permite.

El coste es todo el bucle: **8 de 14 invocaciones del escritor fueron reescrituras** (119.268 de las 185.057 palabras de entrada del escritor). Es el gasto dominante de la ejecución y lo produce el umbral, no el texto.

Propuesta, en orden de preferencia:

1. **Separar gravedad 1 de gravedad 2.** Ahora las dos son «grave» y pesan igual, pero una contradicción de canon (1) y un suceso de escaleta que falta (2) no son lo mismo: la primera envenena los capítulos siguientes a través del libro de estado, la segunda no. Sustituir `rechaza_con_graves: 1` por dos claves, `rechaza_con_gravedad_1: 1` y `rechaza_con_gravedad_2: 2`. Es un cambio en `recalcular(problemas)` y en `config.veredicto`; no toca a los agentes.
2. Si se prefiere no tocar la forma del veredicto: subir `rechaza_con_graves` a 2 y medir. Más barato de implementar, menos informativo.

En los dos casos, **medir antes de decidir**: reprocesar los `informe-K.md` de la ejecución de referencia con el umbral nuevo cuesta cero invocaciones y dice exactamente cuántos capítulos habrían cerrado al primer intento. Ese cálculo encaja bien dentro de `/novela verificar`.

### 3.2 Sesgo sistemático de longitud · impacto medio-alto

11 de 13 por encima, media +10,5 %. El prompt ya hace lo correcto (da suelo y techo en palabras absolutas, no en porcentaje), y aun así el modelo apunta alto. Es un sesgo conocido: los modelos tratan el objetivo como mínimo.

Propuesta: **pedir el objetivo corregido por el sesgo medido**. Pasar al escritor `objetivo × (1 − sesgo)` con `sesgo` calculado de las ejecuciones anteriores (aquí, 0,10), manteniendo suelo y techo reales. Es una línea en `escribir_capitulo` y una clave nueva en `formato`. Con 1.350 pedidos, la media caería a ~1.490 y los dos desbordes del cap. 03 no habrían ocurrido.

Alternativa más conservadora: dejar el prompt y añadir al informe de cierre la **desviación media firmada**. Ahora solo se publica `desviacion_longitud` en valor absoluto (9,3 %), que esconde que el error es todo en la misma dirección. Sin el signo, el dato no es accionable.

### 3.3 El coste de contexto no está acotado · impacto medio ahora, alto en `novela`

50:1 con 5 capítulos. La entrada crece con cada capítulo cerrado porque `resumenes_completos_ultimos = null` da todos los resúmenes previos y `capitulo_anterior_integro = true` añade el capítulo anterior entero.

El comentario de `config.json` ya avisa («a partir de aquí conviene fijar `memoria.resumenes_completos_ultimos` a 10» en el perfil `novela`), pero es una nota, no un mecanismo: nada impide lanzar 30 capítulos con `null`.

Propuesta: mover `resumenes_completos_ultimos` **dentro de cada perfil**, con el valor por defecto ya puesto (`relato`: null, `novela_corta`: null, `novela`: 10, `saga`: 10), y que `comprobar_entorno` avise si la combinación perfil/memoria proyecta una entrada por invocación por encima de un techo configurable. El dato para proyectarla ya está en el registro: `pal_entrada` por invocación.

### 3.4 El informe global no realimenta nada · impacto medio

El revisor global encontró **5 problemas, los 5 de gravedad 1**, y la ejecución terminó en `ÉXITO`. Es coherente con el diseño (los capítulos aprobados son inmutables) y `erratas.md` ya recoge los arreglos de una línea. Pero el ciclo se cierra sobre el usuario, no sobre el sistema: nada de lo que el revisor global aprende entra en la siguiente novela.

Propuesta barata: que `escribir_erratas` clasifique además los problemas globales por **tipo recurrente** (cronología, canon de la biblia, hilo sin cerrar, voz) y que el informe de cierre publique ese recuento. Con dos o tres ejecuciones se ve si el escritor falla siempre en lo mismo, y eso sí es accionable sobre el prompt o sobre la sección «Cronología y datos fijos» de la biblia. La traza ya sugiere el candidato: dos de los avisos son de cronología (las «dos semanas» del cap. 3, la llave del foso en 2011 contra la edad de Reme).

### 3.5 Dos fugas menores de integridad · impacto bajo, coste de arreglo bajo

- **`estado.json` se desincronizó** durante la ejecución y hubo que recalcular las invocaciones desde `registro.md` al cerrar (aviso en la traza). `invocar.md` incrementa el contador y guarda, así que la pérdida ocurrió en algún punto de reanudación. Arreglo: recalcular desde `registro.md` **al cerrar cada capítulo**, no solo al final; es un recuento de filas y elimina la clase entera de fallo.
- **Se perdió trabajo al reanudar**: el `paso_descartado` del cap. 02 se llevó `intento-1.md` con 1.333 palabras ya escritas, por reanudar con la carpeta sucia. El comportamiento es correcto por diseño (nada aprobado se pierde), pero tirar una invocación completa del escritor es caro. Arreglo: antes de `descartar(carpeta)`, mover lo no commiteado a `novelas/<slug>/.descartado/<timestamp>/` en vez de borrarlo. No cambia ninguna garantía y deja la puerta abierta a recuperarlo a mano.

---

## 4. Lo que la traza no pudo decirme

Esto no es sobre la novela, es sobre la herramienta. Cada punto me costó tiempo en este análisis.

| Problema | Consecuencia | Arreglo |
|---|---|---|
| **Todas las observaciones comparten el mismo instante** (16:25:40.301–305, el momento de la exportación). Duraciones = 0 ms. | Langfuse no puede ordenar hermanos ni medir nada. Los 17/20/33/44 minutos por capítulo los he tenido que reconstruir a mano desde `fecha_hora` del metadata. | `fecha_hora` ya viaja en el metadata de cada fila. Usarla como `start_time`, y como `end_time` la de la fila siguiente del mismo span. La resolución es de minuto, que para esto sobra. |
| **Mojibake en los avisos**: `Cap�tulo`, `cronolog�a`, `Bandr�s`. | El texto más valioso de la traza (los avisos del cierre) llega ilegible. | `registro.md` / `estado.json` se están leyendo sin `encoding="utf-8"` explícito; en Windows `open()` usa cp1252. Un parámetro. |
| **Una invocación del escritor aparece dos veces** (cap. 02: la fila `en curso` y la fila que la cierra generan dos observaciones). La traza cuenta 38 generaciones; las invocaciones reales son 37. | Cualquier métrica de coste calculada sobre la traza sale inflada. | Fusionar la fila `en curso` con su fila de cierre antes de emitir. |
| **Tres trazas idénticas** de la misma novela (`67651ff3…`, `868bf07a…`, `89766b6a…`), de tres exportaciones seguidas. | No hay forma de saber cuál es «la última» sin mirar las tres. | `trace_id` determinista derivado del slug, para que reexportar **sustituya** en vez de duplicar. |
| **Los nombres de agente son los viejos** (`revisor / capitulo`). | En cuanto se ejecute el split, la traza no distinguirá encargo de continuidad salvo que se actualice el exportador a la vez. | Emitir el nombre real del subagente y el campo `origen` de cada problema. |
| **La API legada devuelve 410** para esta organización. | `exportar.py` usa el SDK, así que probablemente sigue funcionando para *escribir*; pero cualquier lectura de vuelta (la que haría falta para un `--verificar`) está rota. | Documentar en el README el endpoint v2 y `fields=core,io,metadata`. |

Ninguno de estos arreglos toca el harness: `herramientas/trazas/` está fuera del bucle y es borrable sin consecuencias ([spec §9.3](../../specs/functional.md)). Se pueden hacer todos sin riesgo.

---

## 5. Propuesta priorizada

| # | Cambio | Impacto | Coste | Toca |
|---|---|---|---|---|
| 1 | Separar gravedad 1 de gravedad 2 en `veredicto`, y reprocesar los informes de referencia con el umbral nuevo antes de fijarlo | Alto | Bajo | spec §4.2, `config.json`, `capitulo.md` |
| 2 | Calibrar el umbral **a la vez** que se estrena el split de revisores, nunca después | Alto | Ninguno | orden de trabajo |
| 3 | Corregir el sesgo de longitud en el objetivo que se pide, y publicar la desviación **con signo** | Medio-alto | Bajo | `capitulo.md`, `final.md` |
| 4 | `resumenes_completos_ultimos` dentro de cada perfil + aviso de proyección de contexto | Medio | Bajo | `config.json`, `comprobar_entorno` |
| 5 | Arreglar la exportación: timestamps reales, encoding, fusión de filas `en curso`, `trace_id` determinista, nombres de los dos revisores | Medio | Bajo | `herramientas/trazas/` |
| 6 | Recalcular invocaciones desde `registro.md` al cerrar cada capítulo | Bajo | Muy bajo | `capitulo.md` |
| 7 | `.descartado/<timestamp>/` en vez de borrar al reanudar | Bajo | Muy bajo | `invocar.md` |
| 8 | Clasificar las erratas globales por tipo recurrente y publicarlo en el cierre | Medio a 3 ejecuciones | Medio | `final.md`, `plantillas/erratas.md` |

Según la regla 6 de `CLAUDE.md`, del 1 al 4 y del 6 al 8 pasan por `CHANGELOG.md` y por la spec antes que por la implementación. El 5 no: está fuera del harness.

---

## 6. Lo que no propongo, y por qué

- **Mover el resumidor detrás del revisor** para ahorrar invocaciones. No se puede: el revisor de continuidad recibe `resumen-K.md` como entrada. Las 11 invocaciones del resumidor no son desperdicio, son dependencia.
- **Subir `reescrituras_max`**. Con el umbral actual solo compraría más reescrituras al mismo precio; con el umbral corregido probablemente sobre. Primero el umbral, después este número.
- **Meter la exportación de trazas en el bucle** para tener datos en vivo. Está descartado por escrito y la traza le da la razón: 37 invocaciones sin un solo fallo técnico es justo lo que no conviene poner en riesgo por una llamada de red.
- **Tocar los prompts de los agentes a partir de esta única ejecución.** Cinco capítulos con un solo perfil y un solo modelo no bastan para atribuir nada al prompt. Los cambios que propongo son todos del harness, que es donde los datos sí son concluyentes.
