---
caso: "caso-01-opus-vs-haiku"
fecha: "2026-09-18"
veredicto: "A"
b_aguanta: true          # cierto pero vacío: A no cumple ninguna métrica, así que la regla de §8.3 no discrimina. Ver §3.
---

# Comparación — caso-01-opus-vs-haiku

Rellenado por `/novela comparar`. Ninguna cifra es estimada: todo sale de contar o de leer.
Lo no disponible: `desconocido`.

**A** = `novelas/tecnica-ascensores-peticion-ia` (opus, spec v3) · *Contrapeso*
**B** = `novelas/tecnica-ascensores-peticion-ia-20260916-1719` (haiku, spec v4) · *Corrosión*

> **Leer con la advertencia de `caso.md`**: entre A y B cambió también la versión del harness
> (revisión partida, ajustes de longitud con presupuesto propio y umbrales recalibrados).
> El modelo no es la única variable.

## 0. Comprobaciones previas

| Comprobación | Resultado |
|---|---|
| `idea.md` idéntico | Sí (md5 `32de1e69a69caf20c4bd61d0359203ce` en las dos) |
| `entrevista.md` idéntico | Sí (md5 `b16a90c94244411fcb9283218de62995` en las dos) |
| `perfil` y `formato` iguales | Sí (`relato`, 5 capítulos, 1.500 palabras, tolerancia 0,2) |
| `etapa: completa` en las dos | Sí |
| Inventario completo | Sí. B tiene además `erratas.md` (artefacto nuevo de la v4) |
| **`config.calidad` igual** | **No.** B tiene los umbrales relajados. Las columnas CUMPLE se dan por separado |
| **`config.version` igual** | **No.** A = 3, B = 4 |

## 1. Medible

### Métricas de calidad (recalculadas ahora, no copiadas del informe de cierre)

T = 5 capítulos en las dos. A: 13 intentos. B: 9 intentos.

| Métrica | A (valor) | umbral A | A | B (valor) | umbral B | B | B contra el umbral de A |
|---|---|---|---|---|---|---|---|
| graves_por_10 | 8,0 | ≤ 1 | **NO CUMPLE** | 0,0 | ≤ 2 | CUMPLE | CUMPLE |
| agotamiento_pct | 40 % | ≤ 10 % | **NO CUMPLE** | 0 % | ≤ 20 % | CUMPLE | CUMPLE |
| hilos_sin_cerrar | 1 | ≤ 0 | **NO CUMPLE** | 0 | ≤ 0 | CUMPLE | CUMPLE |
| primer_intento_pct | 0 % | ≥ 60 % | **NO CUMPLE** | 40 % | ≥ 40 % | CUMPLE (justo) | **NO CUMPLE** |
| rechazos_voz_pct | 15,4 % | ≤ 10 % | **NO CUMPLE** | 0 % | ≤ 20 % | CUMPLE | CUMPLE |
| desviacion_longitud | 9,3 % | informativa | – | 14,8 % | informativa | – | – |

`cumple_todas`: A **false** (0 de 5) · B **true** (5 de 5 con sus umbrales, 4 de 5 con los de A).

Detalle del cálculo, para que se pueda rehacer:

- **graves_por_10.** Ningún lado tiene informe de arco (arco único): sale solo del global.
  A: 4 problemas de gravedad 1 en `informe-global.md` ÷ 5 × 10 = 8,0.
  B: `informe-global.md` con `problemas: []` → 0,0.
- **agotamiento_pct.** A: capítulos 3 y 5 con `por_agotamiento: true` = 40 %. B: ninguno.
- **hilos_sin_cerrar.** A: «Reme y el vecindario», que `escaleta.md` cierra en el capítulo 5
  y que el libro de estado conserva abierto en dos entradas («Pablo lo cuenta en el grupo
  del barrio», «La junta del miércoles y la vecina del segundo»).
  B: el único hilo con cierre previsto, «La decisión final: ella actuará», no figura en
  «Hilos abiertos» del libro de estado.
- **primer_intento_pct.** A: ninguno (el capítulo 3 quedó en el intento 1, pero por agotamiento).
  B: capítulos 3 y 4 = 40 %, **justo en el umbral**; un capítulo más con segundo intento lo habría tumbado.
- **rechazos_voz_pct.** A: 2 intentos con problema de gravedad 4 (`capitulos/01/informe-1.md`,
  `capitulos/03/informe-1.md`) ÷ 13 = 15,4 %. B: ninguno ÷ 9 = 0 %.
- **desviacion_longitud.** Media de |`wc -w` del intento aprobado − 1.500| ÷ 1.500.
  A sobre 1.613, 1.474, 1.660, 1.661, 1.737 → 9,3 %.
  B sobre 1.223, 1.398, 1.229, 1.253, 1.288 → 14,8 %, **toda por defecto**: los cinco capítulos
  de B se quedan cortos y ningún intento suyo se pasó nunca de largo.

### Ejecución

| Dato | A | B |
|---|---|---|
| Capítulos completos / previstos | 5 / 5 | 5 / 5 |
| Palabras del manuscrito (`wc -w`) | 8.271 (8.145 sin la nota de elaboración) | 6.426 (6.391 en los cinco capítulos) |
| Palabras por capítulo (aprobado) | 1.613 · 1.474 · 1.660 · 1.661 · 1.737 | 1.223 · 1.398 · 1.229 · 1.253 · 1.288 |
| Palabras de todos los intentos | 21.544 en 13 intentos | 10.433 en 9 intentos |
| Intentos por capítulo | 2 · 2 · 3 · 3 · 3 | 3 · 2 · 1 · 1 · 2 |
| Intento aprobado | 2 · 2 · **1 (agot.)** · 3 · **2 (agot.)** | 3 · 2 · 1 · 1 · 2 |
| Rechazos por longitud | 2 (cap. 3, intentos 2 y 3: 1.940 y 1.879, **por exceso**) | 3 (caps. 1, 2 y 5: 1.012, 980 y 821, **por defecto**) |
| Ajustes de longitud (no consumen reescritura) | no existían en la v3 | 3 (caps. 1, 2 y 5) |
| Rechazos de escaleta / canon | 0 | 2 (cuarta planta fuera del canon; plantas del edificio descuadradas) |
| Incumplimientos de contrato del agente | **0** | **7** (5 del interrogador, 2 del escritor: bloques `=== ARCHIVO ===` mal cerrados o ausentes, tres arcos duplicados, JSON en valla de código) |
| Reintentos técnicos | 0 | 7 |
| Discrepancias de veredicto | 0 | 1 |
| Pasos descartados | 1 | 4 |
| Problemas de arco por gravedad | sin informe de arco (arco único) | sin informe de arco (arco único) |
| Problemas del informe global | 4 de gravedad 1 + 1 de gravedad 2; veredicto RECHAZADO | **0**; veredicto APROBADO |
| Erratas propuestas | no existía `erratas.md` en la v3 | 0 |
| Invocaciones (`estado.json`) | interrogador 1 · escritor 13 · resumidor 11 · revisor 12 = **37** | interrogador 6 · escritor 12 · resumidor 7 · rev-encargo 6 · rev-continuidad 9 = **40** |
| Invocaciones (filas de cierre de `registro.md`) | 37 (coincide) | 41 — **no coincide**: 10 filas de `revisor-continuidad` frente a 9 en `estado.json` |
| Volumen: pal_entrada / pal_salida | opus: **403.727 / 77.066** | haiku: **164.426 / 33.742** |
| Palabras de entrada por palabra de novela | 49,6 | 25,7 |
| Tokens por modelo | `desconocido` (§6.6: `Agent` no los devuelve) | `desconocido` |
| Coste por modelo | `desconocido` | `desconocido` |

> Las cifras de volumen de B descuentan la fila de corrección de `registro.md` línea 107
> (`pal_salida` 3.492 → 2.774) y las 8 filas `resultado: pendiente`, que en la v4 duplican
> cada invocación. La de A descuenta la única fila `en curso`.

## 2. Lectura

### Continuidad

Tres hechos verificables del capítulo 1 de cada lado, comprobados en el último **y** en `libro-estado.md`.

| # | A: hecho del cap. 1 | A: en el cap. 5 | A: libro de estado |
|---|---|---|---|
| 1 | Reme saca el fusible de cristal de 20 mm del altavoz y se lo guarda con los dos tornillos | Lo devuelve: «sacó el fusible de cristal de veinte milímetros, lo miró al trasluz […] y lo encajó en sus pinzas […] No dejó ninguno en el suelo» | Hilo cerrado «El fusible intacto», con la misma escena. **Coinciden** |
| 2 | Carmen Buil, 71 años, rodilla operada dos veces, silla en el descansillo del entresuelo | «como se sienta la gente con una rodilla operada dos veces»; Reme le baja la silla al portal | Personaje coherente. **Coinciden** |
| 3 | «Julia Bandrés decía que un aparato no se rompe»; Reme lleva 26 años con el aparato del 38 | Firma bajo la firma de Julia: «23/10/2049. Montaje de desconexión manual en foso» | **Discrepa con la biblia**, no con el texto: la llave del foso «que le dio Julia Bandrés en 2011» no cabe en 26 años de oficio desde ~2023. Es la tensión de canon que el interrogador dejó sin fijar (§8.5) |

| # | B: hecho del cap. 1 | B: en el cap. 5 | B: libro de estado |
|---|---|---|---|
| 1 | Marisa sube «desde la planta baja hasta la cuarta»; el capítulo 5 se titula «La 4ª planta» | **La cuarta planta no aparece en el capítulo 5.** Todo transcurre en el cuarto de máquinas | El libro de estado no menciona la cuarta planta. **El título del capítulo se quedó sin referente** |
| 2 | La acción arranca «quizá las nueve de la mañana» y los capítulos 2, 3 y 4 encadenan sin corte («Llevaba menos de media hora fuera del cuarto de máquinas», cap. 3) | Cap. 5: «Estaba igual que tres días atrás» y «herramientas que no había traído en los últimos tres días» | El libro de estado no fija fechas. **Contradicción real**: tres días aparecen de la nada entre el capítulo 4 y el 5 |
| 3 | En el cap. 2 Marisa documenta con una **muestra de óxido en bolsa de plástico**; no fotografía nada | Cap. 4: «Tenía algo mejor: las imágenes que había tomado del cable corroído» | El libro de estado lo da por bueno: «Ha validado diagnóstico de Marisa mediante fotografías». **El atrezo aparece sin haberse sembrado** |

**Lo que esto dice del revisor.** Los tres hallazgos de B están en el texto y el revisor de
continuidad de `haiku` no marcó ninguno como problema. Los dos últimos los **vio** y los
degradó a observación: «no es contradicción con canon o estado, es compresión narrativa»
(`informe-global.md`, observación 2) y «la ventana de 48-72 horas en el cap. 5 es consistente
con una semana de acción» (observación 1), que es justamente lo que el texto desmiente.
El informe cierra con «Coherencia interna total». Por eso `graves_por_10` da 0 en B: no es
que no haya contradicciones, es que el revisor barato no las cuenta como tales.

En A pasa lo contrario: el revisor de `opus` encontró en la revisión global cuatro problemas
de gravedad 1 que ninguna revisión de capítulo había visto —entre ellos que «23/10/2049» no
cae en el jueves que el propio capítulo 5 fija—. A puntúa peor porque su revisor mira mejor.

### Cumplimiento del plan

| Cap | A | B |
|---|---|---|
| 1 | Cumple objetivo y los tres sucesos; gancho («una cabina que no debería hablar dice su nombre») presente | Cumple el mensaje anómalo y la repetición. **No cumple «Marisa ignora el mensaje»**: lo toma en serio de inmediato y el capítulo termina subiendo, que era el suceso del capítulo 2. El «domingo por la mañana» de la escaleta no aparece |
| 2 | Cumple: histórico vacío, «no eres Mantenimiento», la petición de la pieza y el plano por la impresora | Cumple los dos sucesos (corrosión, agua filtrada, sellado fallido) |
| 3 | Cumple los sucesos, pero arrastra la contradicción de «dos semanas» que el revisor marcó en el intento 1 y que **nadie corrigió**: las dos reescrituras se gastaron en rechazos por longitud | Cumple los tres sucesos (grieta en la soldadura, riesgo amplificado, la IA le mostró lo que necesitaba ver) |
| 4 | Cumple: el ultimátum, la ruptura con Pablo, la hoja del libro de mantenimiento de 2011 | Cumple los cinco sucesos, incluida la frase literal de Roser. El suceso «le muestra fotos» se cumple **a costa de la continuidad** (ver arriba) |
| 5 | **No cierra el hilo «Reme y el vecindario»** que la escaleta mandaba cerrar con «pacto explícito con Carmen y con el bloque»: hay pacto con Carmen y poco más. La regla de mejor intento eligió el intento 2 sobre el 3, que sí lo cerraba | Cumple los cuatro sucesos. **El título de su entrada, «La 4ª planta», no tiene referente en el texto**, y el revisor de encargo lo aprobó sin mencionarlo |

Fallo del revisor en cada lado: en A, el del capítulo 5 es un fallo de la **regla de desempate**
del harness, no del revisor (el revisor sí lo marcó). En B, los del capítulo 1 y el capítulo 5
son fallos del **revisor de encargo**, que aprobó ambos sin señalar ni el suceso incumplido ni
el título sin referente.

### Prosa y voz

**A se lee como una novela; B se lee como el resumen de una.** No está cerca.

A tiene escenas con dos personas dentro, y el conflicto pasa en el diálogo:

> —Pablo. La de catorce.
> —La de catorce.
> —La fija. No la inglesa.

y la información técnica llega por el oficio, no por explicación: «Mil cuatrocientos milímetros
de palanca para mover un vástago que recorría cuarenta. […] Treinta y cinco a uno. Nadie pone
treinta y cinco a uno para accionar algo pequeño». Carmen pidiendo la llave delante de todo el
vecindario, con la mano temblándole «a base de rabia», es una escena; la voz que solo dice
«Correcto», «Recibido» y calla es una restricción de la biblia sostenida durante cinco capítulos
sin una sola fisura, y el informe global de A lo confirma.

B casi no tiene escena. Tiene a Marisa pensando, y el narrador repitiendo lo que ya dijo:

> «Treinta años llevaba reparando ascensores. Sabía lo que significaba un motor limpio.»
> «Marisa llevaba treinta años trabajando con máquinas.»
> «Treinta años de trabajo no dejaban espacio para esa clase de errores.»
> «un técnico con treinta años de oficio»
> «Treinta años. Treinta años de manos que sabían.»

Los capítulos 2, 3 y 5 son la misma escena tres veces: sube al cuarto de máquinas, toca el cable,
reflexiona sobre la responsabilidad. El único diálogo largo (Marcel, cap. 4) es funcional y
termina en frase de manual: «—No lo estás. Eso se ve desde aquí. Es real.»

Y hay **castellano roto**, que ninguna métrica del harness mide y que ningún revisor marcó:

> «el cansancio […] la estaba jugando una mala pasada» · «el sellado […] había fallido» ·
> «la agua había insistido» · «Mesada mañana durante meses» · «el agua hubiese trovado
> múltiples caminos» · «La conocimiento no era reversible» · «como si contenga más que metal» ·
> «lo que una máquina solo podía sospecha través de datos» · «La peso en su mano» ·
> «los parámetros que sus algoritmos conocía»

Hay además un error de hecho dentro del propio texto: en el capítulo 4, Roser dice «Llevo
cincuenta años en este barrio» y el narrador la presenta como «una vecina de cincuenta años»;
el libro de estado copia el error («50 años en el barrio», «mujer mayor»).

La respuesta honesta a la pregunta del paso 2 es la contraria de la que buscábamos: **el lado
barato no se lee igual de bien, y la distancia no es de matiz.**

## 3. Conclusión

**Veredicto: A.**

**¿B aguanta?** Formalmente **sí**: A no cumple ninguna métrica, así que «B cumple todas las
que cumple A» se satisface por vacío. **La regla de §8.3 no discrimina en este caso y no debe
usarse para decidir nada aquí.** Contra los umbrales de A, B cumple 4 de 5 (falla
`primer_intento_pct`: 40 % frente a 60 %).

**Qué significa para el plan (§7.8).** El paso 2 **no queda decidido, y lo que hay apunta a que
no**. Tres lecturas:

1. **Las métricas miden el harness, no la novela.** B saca 5 de 5 y A 0 de 5, y A es
   incomparablemente mejor novela. Cuatro de las seis métricas dependen de lo que el revisor
   declare, así que un revisor peor sube la nota. `graves_por_10` es la que más lo sufre: con
   `haiku` vale 0 sobre un manuscrito con un salto de tres días sin explicar.
2. **`haiku` sale barato en volumen y caro en fricción.** 164.426 palabras de entrada frente a
   403.727 (41 %), y 25,7 palabras de entrada por palabra de novela frente a 49,6. A cambio:
   7 incumplimientos de contrato frente a 0, 7 reintentos técnicos frente a 0, 2 rechazos de
   canon frente a 0 y 4 pasos descartados frente a 1. Sin tokens ni coste (`desconocido`), no
   se puede decir si el ahorro compensa; la observabilidad de §9.3 sigue siendo el bloqueo.
3. **La comparación limpia está pendiente.** A corrió con la spec v3, y las tres reglas que
   cambiaron en la v4 explican por sí solas buena parte de la ventaja métrica de B (los dos
   capítulos por agotamiento de A vienen del defecto de longitud que la v4 arregló). Antes de
   cerrar el paso 2 hay que relanzar el lado caro con la spec v4.

## 4. Cambios propuestos para el harness

1. **`comparativa/README.md` (reglas de justicia) y `.claude/skills/novela/procedimientos/comparar.md` §1.**
   Añadir como precondición que `config.json` → `version` y el bloque `config.calidad` sean
   iguales en los dos lados, y anotar en `registro.md` → `inicio_ejecucion` el commit del harness.
   Este caso tuvo que compararse con v3 frente a v4 y con umbrales distintos, y eso no se puede
   detectar hoy: las cuatro comprobaciones actuales lo dejan pasar.

2. **`comparar.md` §4 y `specs/functional.md` §8.3.**
   La regla «B aguanta si cumple todas las métricas que cumple A» es vacía cuando A no cumple
   ninguna. Escribir: si `cumple_todas` de A es false y A cumple cero métricas, `b_aguanta` se
   marca como **no informativo** y la decisión recae entera en el bloque de lectura.

3. **`.claude/agents/revisor-continuidad.md` (contrato, spec §5.5).**
   Prohibir explícitamente degradar a `observaciones` dos cosas que en B se colaron así:
   (a) un salto temporal entre capítulos que el texto no justifica, y (b) un objeto o prueba
   que un capítulo usa y ningún capítulo anterior siembra. Las dos son problema con gravedad,
   no observación. Cita para el criterio: `informe-global.md` de B, observaciones 1 y 2.

4. **`.claude/agents/revisor-encargo.md` (contrato, spec §5.4).**
   Añadir criterio: **el título de la entrada de escaleta tiene que tener referente en el texto**.
   El capítulo 5 de B se titula «La 4ª planta» y la cuarta planta no aparece; se aprobó sin
   mencionarlo.

5. **`.claude/skills/novela/procedimientos/capitulo.md`, prompt del escritor.**
   Con `haiku` el escritor tira sistemáticamente a la baja: los tres rechazos por longitud de B
   fueron por defecto y los cinco capítulos aprobados quedaron cortos (media −14,8 %). En A, con
   `opus`, la desviación es +9,3 % y los rechazos fueron por exceso. Dar al recuento del prompt
   un aviso asimétrico según el modelo, o registrar el sesgo en el informe de cierre para que
   `desviacion_longitud` se lea con signo.

6. **`.claude/skills/novela/procedimientos/invocar.md`.**
   Dos incumplimientos de B fueron de formato puro (JSON envuelto en valla de código; bloque
   `=== ARCHIVO: … ===` sin `=== FIN ===`) y el harness los resolvió a mano. Subir a regla lo
   que ya hizo: aceptar el JSON con valla quitándola, y reintentar el bloque sin cerrar pidiendo
   solo el cierre. Con modelos baratos esto es buena parte de los reintentos.

7. **`procedimientos/final.md` → `calcular_metricas`, y `SKILL.md`.**
   `estado.json` de B dice 9 invocaciones de `revisor-continuidad` y `registro.md` tiene 10
   filas de cierre. A tuvo el mismo problema y lo arregló recalculando al cerrar (su aviso 7).
   Que el recálculo desde `registro.md` al cerrar sea obligatorio y deje fila, no un arreglo
   improvisado de cada ejecución.

8. **Métrica que falta (spec §8.3).**
   Ninguna de las seis métricas distingue *Contrapeso* de *Corrosión*, y la diferencia de prosa
   es enorme. Como mínimo hace falta una métrica **informativa** de lengua —errores de
   concordancia y de régimen por cada mil palabras, contados sobre el manuscrito— porque B tiene
   una decena de ellos («la agua», «La conocimiento», «hubiese trovado») y el harness los da por
   buenos. Sin eso, el harness no puede decidir el paso 2 con datos, solo con lectura.
