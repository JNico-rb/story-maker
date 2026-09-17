# Etapa 2 — Un capítulo (N, intento K)

Implementa `escribir_capitulo`, `comprobar_longitud`, `resumir`, `revisar`, `decidir`, `mejor_intento` y `cerrar_capitulo` de SKILL.md §3. `NN` = N con dos dígitos; `A` = arco que contiene N; `entrada` = la entrada nº N de `arcos/arco-AA.md`. Al empezar un capítulo la carpeta está limpia (el anterior se commiteó al cerrarse); dentro del capítulo conviven `intento-K.md`, `resumen-K.md`, `libro-estado-K.md`, `informe-K.md`, `estado.json` y `registro.md` sin commitear, y eso es normal.

**Dos presupuestos distintos, y no se mezclan** (spec §4.2):

- `e.reescrituras_usadas[N]` — correcciones de **contenido**. Tope `config.limites.reescrituras_max`.
- `e.ajustes_usados[N]` — rechazos **solo por longitud**. Tope `config.limites.ajustes_longitud`.

El número de intento `K` avanza con los dos, porque es el nombre del fichero. Los dos empiezan en 0 en cada capítulo.

**Qué resúmenes previos se pasan** (escritor y revisor de continuidad): si `memoria.resumenes_completos_ultimos` es `null`, los resúmenes aprobados de todos los capítulos anteriores; si es un número M, los de los M últimos. Ruta de cada uno: `capitulos/XX/resumen-<estado.capitulos[X].aprobado>.md`. Para N = 1 no hay ninguno y el prompt lo dice.

## escribir_capitulo(carpeta, N, K) → capitulos/NN/intento-K.md

```
entradas = [biblia.md, escaleta.md, arcos/arco-AA.md, libro-estado.md, resúmenes previos según memoria,
            capitulos/<N-1>/intento-<aprobado>.md si memoria.capitulo_anterior_integro y N > 1,
            capitulos/NN/informe-<J>.md y capitulos/NN/intento-<J>.md si K > 1]
```

donde `J` es el intento anterior, `K−1`. Si ese intento fue un rechazo **solo por longitud** y antes había un informe de contenido sin corregir (el del último intento que llegó a los revisores), pásale **los dos** informes: el de longitud no corrige nada y lo que quedó pendiente sigue pendiente.

```
invocar(escritor, capitulo, K, entradas,
        validacion = bloque {capitulos/NN/intento-K.md} (título + cuerpo no vacío),
        destinos   = capitulos/NN/intento-K.md)
progreso "[cap NN/<total>] intento K · escrito (<wc -w> palabras)"
```

### Prompt del escritor

Calcula antes `suelo = redondeo(objetivo × (1 − tolerancia))` y `techo = redondeo(objetivo × (1 + tolerancia))`, y pásalos **en palabras**, nunca como porcentaje: un modelo pequeño maneja mucho peor «±20 %» que «entre 1.200 y 1.800» (spec §4.2).

> Carpeta de la novela: `novelas/<slug>/`. Vas a escribir el **capítulo N, intento K**. Lee `biblia.md` (incluida su sección «Cronología y datos fijos»: esos números no se tocan); `escaleta.md`; `arcos/arco-AA.md` (tu entrada es la nº N); `libro-estado.md`; los resúmenes previos: <rutas, o "no hay: es el primer capítulo">; <el capítulo anterior íntegro: `capitulos/<N−1>/intento-<k>.md`, si procede>. **Longitud: entre <suelo> y <techo> palabras** (objetivo <objetivo>). El harness las cuenta con `wc -w` y rechaza sin que nadie lo lea lo que se salga. Devuelve solo el capítulo en un bloque `=== ARCHIVO: capitulos/NN/intento-K.md ===` … `=== FIN ===`, empezando por una línea `# <título>`. No escribas ningún fichero ni produzcas resumen.
>
> (K > 1, rechazo de contenido) Tu intento anterior fue RECHAZADO. Lee `capitulos/NN/informe-<J>.md` y `capitulos/NN/intento-<J>.md`. Tenía **<palabras_J> palabras** y el techo son <techo>. Corrige cada problema del informe en el lugar que señala, sin introducir otros y conservando lo que estaba bien. **Corregir no puede alargar**: si una corrección añade líneas, recorta lo que sobre en otro sitio.
>
> (K > 1, rechazo por longitud) Tu intento anterior tenía **<palabras_J> palabras** y el margen es <suelo>–<techo>: <sobran X | faltan X>. Lee `capitulos/NN/intento-<J>.md` y devuélvelo <recortado | ampliado> hasta entrar en el margen, **sin perder nada de lo que ya estaba corregido** <y corrigiendo además los problemas de `capitulos/NN/informe-<I>.md`, que siguen pendientes>.

## comprobar_longitud(carpeta, N, K) → ok | informe

Lo haces **tú, sin modelo**, y en este orden: primero cuentas, después registras. (En la ejecución de referencia se registró `ok` antes de comparar y hubo que corregir la fila.)

```
palabras  = wc -w capitulos/NN/intento-K.md            # el título cuenta; es despreciable
objetivo  = entrada.palabras_objetivo
margen    = objetivo × config.formato.tolerancia_longitud
si |palabras − objetivo| ≤ margen: registra longitud(ok, palabras); return ok
informe = { veredicto: RECHAZADO,
            problemas: [{ gravedad: 3,
                          donde: "capítulo completo",
                          que: "<palabras> palabras; objetivo <objetivo>, margen <suelo>-<techo>",
                          por_que: "formato.tolerancia_longitud = <tolerancia>; entrada N de arcos/arco-AA.md" }],
            observaciones: ["Rechazo generado por el harness; el capítulo no ha pasado por el resumidor ni por los revisores"] }
escribe capitulos/NN/informe-K.md desde plantillas/informe.md con ese contenido y `origen: harness`
registra longitud(rechazo, palabras, objetivo); registra veredicto(RECHAZADO, 1 problema, gravedad 3, origen harness)
progreso "[cap NN/<total>] intento K · RECHAZADO por longitud (<palabras> palabras; margen <suelo>-<techo>)"
return informe
```

## resumir(carpeta, N, K) → resumen-K.md, libro-estado-K.md

```
invocar(resumidor, capitulo, K,
        entradas   = [capitulos/NN/intento-K.md, libro-estado.md, plantillas/resumen.md, plantillas/libro-estado.md],
        validacion = bloques {capitulos/NN/resumen-K.md, capitulos/NN/libro-estado-K.md},
        destinos   = las mismas rutas)
```

El resumidor **no** recibe biblia, escaletas ni resúmenes previos. Si el libro de estado propuesto supera `memoria.libro_estado_max_palabras`, muestra un aviso en el progreso (invocar.md fija en 1,5× el punto en que pasa a ser incumplimiento).

### Prompt del resumidor

> Carpeta de la novela: `novelas/<slug>/`. Resume el **capítulo N, intento K**. Lee solo `capitulos/NN/intento-K.md` y `libro-estado.md` (estado hasta el capítulo N−1). Plantillas: `.claude/skills/novela/plantillas/resumen.md` y `libro-estado.md`. Registra únicamente lo que está en el texto. El libro de estado actualizado debe ocupar como mucho <libro_estado_max_palabras> palabras; si se acerca, condensa entradas cerradas sin borrar hechos. Devuelve dos bloques: `=== ARCHIVO: capitulos/NN/resumen-K.md ===` y `=== ARCHIVO: capitulos/NN/libro-estado-K.md ===`, cada uno cerrado con `=== FIN ===`. No escribas ningún fichero.

## revisar(carpeta, N, K) → informe

**Dos agentes, una sola invocación de herramienta con dos llamadas**: lánzalos en el mismo mensaje para que corran en paralelo. Cada uno recibe **solo** sus ficheros; no le pases al de encargo el libro de estado ni al de continuidad la escaleta del arco.

```
enc = invocar(revisor-encargo, capitulo, K,
        entradas   = [capitulos/NN/intento-K.md, escaleta.md, arcos/arco-AA.md, biblia.md],
        validacion = JSON del revisor (gravedades permitidas: 2, 4),
        destinos   = ninguno)
con = invocar(revisor-continuidad, capitulo, K,
        entradas   = [capitulos/NN/intento-K.md, capitulos/NN/resumen-K.md, biblia.md, libro-estado.md,
                      resúmenes previos según memoria],
        validacion = JSON del revisor (gravedades permitidas: 1, 5),
        destinos   = ninguno)

problemas     = enc.problemas + con.problemas          # unión, con el origen de cada uno
observaciones = enc.observaciones + con.observaciones
si dos problemas señalan lo mismo: conserva el de mayor gravedad y registra el otro como duplicado
veredicto = recalcular(problemas)                      # abajo
si veredicto != enc.veredicto: registra discrepancia_veredicto(revisor: encargo, suyo: <…>, harness: <…>)
si veredicto != con.veredicto: registra discrepancia_veredicto(revisor: continuidad, suyo: <…>, harness: <…>)
escribe capitulos/NN/informe-K.md desde plantillas/informe.md: frontmatter con el veredicto recalculado,
    cada problema con su `origen` (encargo | continuidad), observaciones; cuerpo en prosa legible
registra veredicto(<veredicto>, nº problemas, gravedad máx., desglose por revisor)
progreso "[cap NN/<total>] intento K · <APROBADO | RECHAZADO (gravedad <máx>: <que del primer problema, recortado>)> [continuidad <n> · encargo <m>]"
return informe
```

Si **uno** de los dos falla técnicamente o incumple el contrato, `invocar` reintenta **solo ese**: el otro ya entregó y su salida se conserva (spec §6.5). Solo si el que falla agota sus reintentos hay parada.

**recalcular(problemas)**: `graves = |{gravedad ∈ {1,2}}|`, `leves = |{gravedad ∈ {3,4,5}}|`. RECHAZADO si `graves ≥ config.veredicto.rechaza_con_graves` o `leves ≥ config.veredicto.rechaza_con_leves`; APROBADO en otro caso. El veredicto que queda en disco es siempre el recalculado sobre la **unión**.

### Prompt del revisor de encargo (modo capítulo)

> Carpeta de la novela: `novelas/<slug>/`. Modo **capítulo**: revisa el **capítulo N, intento K**. Lee `capitulos/NN/intento-K.md`, `escaleta.md`, `arcos/arco-AA.md` (tu entrada es la nº N; mira también las posteriores, para detectar adelantos) y `biblia.md`. Contesta solo a *¿está escrito lo que se pidió?*: recorre la entrada N suceso por suceso y di de cada uno si está; comprueba el objetivo, el gancho, los hilos que esta entrada manda cerrar y que no se adelante nada de capítulos posteriores; y la voz y el tono contra la biblia. No juzgues contradicciones con capítulos anteriores ni con el libro de estado: no los recibes, son de otro agente. La longitud ya la ha comprobado el harness: no la juzgues. Devuelve únicamente el JSON de tu definición, con gravedades 2 o 4. No escribas ningún fichero.

### Prompt del revisor de continuidad (modo capítulo)

> Carpeta de la novela: `novelas/<slug>/`. Modo **capítulo**: revisa el **capítulo N, intento K**. Lee `capitulos/NN/intento-K.md`, `capitulos/NN/resumen-K.md`, `biblia.md` (con su sección «Cronología y datos fijos»), `libro-estado.md` y los resúmenes previos: <rutas, o "no hay">. Contesta solo a *¿se contradice algo?*: contrasta el texto con el canon, el libro de estado y los resúmenes; rehaz las cuentas de días y de plazos; contrasta cada afirmación absoluta con el libro de estado; y comprueba que el resumen refleja lo que el capítulo muestra. No juzgues si el capítulo cumple su entrada de escaleta ni si el tono es el previsto: es de otro agente. La longitud ya la ha comprobado el harness. Devuelve únicamente el JSON de tu definición, con gravedades 1 o 5. No escribas ningún fichero.

## decidir(carpeta, N, K, informe) → aprobar | ajustar | reescribir | agotar

El orden importa: la rama de longitud va antes que la de contenido.

```
si informe.veredicto == APROBADO:
    registra decision_harness(aprobar); return aprobar

solo_longitud = (informe.origen == harness y todos sus problemas son de gravedad 3)

si solo_longitud y e.ajustes_usados[N] < config.limites.ajustes_longitud:
    e.ajustes_usados[N] += 1; guardar(e)
    registra decision_harness(ajuste_longitud <n>/<max> → intento K+1 · no consume reescritura)
    progreso "… · ajuste <n>/<max>, no gasta reescritura"
    return ajustar

si e.reescrituras_usadas[N] < config.limites.reescrituras_max:
    e.reescrituras_usadas[N] += 1; guardar(e)
    motivo = "agotados los ajustes de longitud" si solo_longitud si no "rechazo de contenido"
    registra decision_harness(reescribir <n>/<max> → intento K+1 · <motivo>)
    return reescribir

registra decision_harness(aceptar_por_agotamiento)
return agotar
```

Así un rechazo por longitud no se lleva por delante las correcciones pendientes, y el bucle sigue terminando siempre: como mucho `ajustes_longitud + reescrituras_max` intentos por capítulo.

## mejor_intento(carpeta, N) → K

Entre los intentos 1..K del capítulo, leyendo sus `informe-k.md` y sus `resumen-k.md`. Los cinco pasos de la spec §4.2, **en este orden**:

1. **Descarta los rechazados por longitud** (`origen: harness`) si hay alguno que llegó a los revisores. Si todos fueron rechazados por longitud, gana el más cercano a `palabras_objetivo` y aquí acaba.
2. **Cumple los cierres que la escaleta manda para N.** Sea `debidos` = los hilos que `escaleta.md` (tabla de hilos) y `arcos/arco-AA.md` (entrada N) marcan como cerrados en el capítulo N. Para cada intento, `cerrados_k` = la lista `hilos_cerrados` del frontmatter de su `resumen-k.md`. Gana el intento que contenga **todos** los de `debidos`; si ninguno los contiene todos, el que contenga más. Si `debidos` está vacío o todos empatan, pasa al 3.
3. Menos problemas de gravedad 1–2.
4. Menos problemas en total.
5. El más reciente.

El paso 2 es una comparación de listas que haces **tú**, no un juicio: `hilos_cierra` de la escaleta contra `hilos_cerrados` del resumen. Va antes que el recuento porque contar problemas premia al texto que hace menos —omitir un suceso genera un problema, incluirlo y fallar en un detalle genera dos— y porque un hilo sin cerrar en el último capítulo donde podía cerrarse ya no se arregla nunca, mientras que una contradicción de detalle acaba en `erratas.md` (spec §8.5).

Registra `decision_harness(mejor_intento = k, motivo: "paso <n> de la regla: <detalle>")`. Si decidió el paso **4 o el 5** —es decir, sin razón fuerte—, añade además a `estado.avisos`: `"Capítulo N: mejor intento elegido sin criterio fuerte (empate entre los intentos <lista>)"`, y que salga en el informe de cierre.

## cerrar_capitulo(carpeta, N, K, por_agotamiento)

1. Si `por_agotamiento`: si el intento K pasó por el resumidor, sigue; si fue rechazado por longitud y no tiene `resumen-K.md`, ejecuta `resumir(carpeta, N, K)` ahora (el libro de estado necesita el capítulo que se queda).
2. Copia `capitulos/NN/libro-estado-K.md` sobre `libro-estado.md` (escritura completa).
3. `estado.capitulos[N] = { "aprobado": K, "por_agotamiento": <bool>, "intentos": <K máximo alcanzado>, "reescrituras": <e.reescrituras_usadas[N]>, "ajustes_longitud": <e.ajustes_usados[N]> }`. Si por agotamiento, añade a `estado.avisos`: `"Capítulo N aceptado por agotamiento (mejor intento: K de <intentos>); ver capitulos/NN/informe-K.md"`.
4. `estado.capitulo_actual = N + 1`; `estado.intento_actual = 1`; si N es el último del arco A, `estado.arco_actual = A + 1` (salvo que sea el último arco). Guarda.
5. Commit `novela <slug>: cap NN cerrado (intento K)`.
6. Progreso: `[cap NN/<total>] intento K · APROBADO` o `… · RECHAZADO · aceptado por agotamiento (mejor intento: K) ⚠`.
