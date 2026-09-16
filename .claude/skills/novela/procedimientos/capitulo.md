# Etapa 2 — Un capítulo (N, intento K)

Implementa `escribir_capitulo`, `comprobar_longitud`, `resumir`, `revisar`, `decidir`, `mejor_intento` y `cerrar_capitulo` de SKILL.md §3. `NN` = N con dos dígitos; `A` = arco que contiene N; `entrada` = la entrada nº N de `arcos/arco-AA.md`. Al empezar un capítulo la carpeta está limpia (el anterior se commiteó al cerrarse); dentro del capítulo conviven `intento-K.md`, `resumen-K.md`, `libro-estado-K.md`, `informe-K.md`, `estado.json` y `registro.md` sin commitear, y eso es normal.

**Qué resúmenes previos se pasan** (escritor y revisor): si `memoria.resumenes_completos_ultimos` es `null`, los resúmenes aprobados de todos los capítulos anteriores; si es un número M, los de los M últimos. Ruta de cada uno: `capitulos/XX/resumen-<estado.capitulos[X].aprobado>.md`. Para N = 1 no hay ninguno y el prompt lo dice.

## escribir_capitulo(carpeta, N, K) → capitulos/NN/intento-K.md

```
entradas = [biblia.md, escaleta.md, arcos/arco-AA.md, libro-estado.md, resúmenes previos según memoria,
            capitulos/<N-1>/intento-<aprobado>.md si memoria.capitulo_anterior_integro y N > 1,
            capitulos/NN/informe-<K-1>.md y capitulos/NN/intento-<K-1>.md si K > 1]
invocar(escritor, capitulo, K, entradas,
        validacion = bloque {capitulos/NN/intento-K.md} (título + cuerpo no vacío),
        destinos   = capitulos/NN/intento-K.md)
progreso "[cap NN/<total>] intento K · escrito (<wc -w> palabras)"
```

### Prompt del escritor

> Carpeta de la novela: `novelas/<slug>/`. Vas a escribir el **capítulo N, intento K**. Lee `biblia.md`; `escaleta.md`; `arcos/arco-AA.md` (tu entrada es la nº N); `libro-estado.md`; los resúmenes previos: <rutas, o "no hay: es el primer capítulo">; <el capítulo anterior íntegro: `capitulos/<N−1>/intento-<k>.md`, si procede>. Longitud objetivo: <palabras_objetivo> palabras, tolerancia ±<tolerancia×100> %: el harness cuenta las palabras con `wc -w` y rechaza sin revisar lo que se salga. Devuelve solo el capítulo en un bloque `=== ARCHIVO: capitulos/NN/intento-K.md ===` … `=== FIN ===`, empezando por una línea `# <título>`. No escribas ningún fichero ni produzcas resumen.
>
> (K > 1) Tu intento anterior fue RECHAZADO. Lee `capitulos/NN/informe-<K−1>.md` y `capitulos/NN/intento-<K−1>.md`. Corrige cada problema del informe en el lugar que señala, sin introducir otros; conserva lo que estaba bien.

## comprobar_longitud(carpeta, N, K) → ok | informe

Lo haces **tú, sin modelo**:

```
palabras  = wc -w capitulos/NN/intento-K.md            # el título cuenta; es despreciable
objetivo  = entrada.palabras_objetivo
margen    = objetivo × config.formato.tolerancia_longitud
si |palabras − objetivo| ≤ margen: registra longitud(ok, palabras); return ok
informe = { veredicto: RECHAZADO,
            problemas: [{ gravedad: 3,
                          donde: "capítulo completo",
                          que: "<palabras> palabras; objetivo <objetivo>, margen ±<margen>",
                          por_que: "formato.tolerancia_longitud = <tolerancia>; entrada N de arcos/arco-AA.md" }],
            observaciones: ["Rechazo generado por el harness; el capítulo no ha pasado por el resumidor ni el revisor"] }
escribe capitulos/NN/informe-K.md desde plantillas/informe.md con ese contenido y `origen: harness`
registra longitud(rechazo, palabras, objetivo); registra veredicto(RECHAZADO, 1 problema, gravedad 3, origen harness)
progreso "[cap NN/<total>] intento K · RECHAZADO por longitud (<palabras> palabras, objetivo <objetivo> ±<tolerancia×100> %)"
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

```
salida = invocar(revisor, capitulo, K,
        entradas   = [capitulos/NN/intento-K.md, capitulos/NN/resumen-K.md, biblia.md, escaleta.md, arcos/arco-AA.md,
                      libro-estado.md, resúmenes previos según memoria],
        validacion = JSON del revisor,
        destinos   = ninguno)
veredicto = recalcular(salida.problemas)          # abajo
si veredicto != salida.veredicto: registra discrepancia_veredicto(revisor: <suyo>, harness: <tuyo>)
escribe capitulos/NN/informe-K.md desde plantillas/informe.md: frontmatter con el veredicto recalculado
    (y veredicto_revisor si hubo discrepancia), problemas y observaciones; cuerpo en prosa legible; `origen: revisor`
registra veredicto(<veredicto>, nº problemas, gravedad máx.)
progreso "[cap NN/<total>] intento K · <APROBADO | RECHAZADO (gravedad <máx>: <que del primer problema, recortado>)>"
return informe
```

**recalcular(problemas)**: `graves = |{gravedad ∈ {1,2}}|`, `leves = |{gravedad ∈ {3,4,5}}|`. RECHAZADO si `graves ≥ config.veredicto.rechaza_con_graves` o `leves ≥ config.veredicto.rechaza_con_leves`; APROBADO en otro caso. El veredicto que queda en disco es siempre el recalculado.

### Prompt del revisor (modo capítulo)

> Carpeta de la novela: `novelas/<slug>/`. Modo **capítulo**: revisa el **capítulo N, intento K**. Lee `capitulos/NN/intento-K.md`, `capitulos/NN/resumen-K.md`, `biblia.md`, `escaleta.md`, `arcos/arco-AA.md` (entrada nº N y las posteriores, para detectar adelantos), `libro-estado.md` y los resúmenes previos: <rutas, o "no hay">. La longitud ya la ha comprobado el harness: no la juzgues. Devuelve únicamente el JSON de tu definición. No escribas ningún fichero.

## decidir(carpeta, N, K, informe) → aprobar | reescribir | agotar

```
si informe.veredicto == APROBADO:                 registra decision_harness(aprobar);     return aprobar
si K ≤ config.limites.reescrituras_max:           registra decision_harness(reescribir → intento K+1); return reescribir
registra decision_harness(aceptar_por_agotamiento); return agotar
```

## mejor_intento(carpeta, N) → K

Entre los intentos 1..K del capítulo, leyendo sus `informe-k.md`:

1. Descarta los rechazados por longitud (`origen: harness`) si hay alguno que pasó al revisor.
2. Menos problemas de gravedad 1–2.
3. A igualdad, menos problemas en total.
4. A igualdad, el más reciente.

Si todos fueron rechazados por longitud, gana el más cercano a `palabras_objetivo`. Registra `decision_harness(mejor_intento = k, motivo)`.

## cerrar_capitulo(carpeta, N, K, por_agotamiento)

1. Si `por_agotamiento`: si el intento K pasó por el resumidor, sigue; si fue rechazado por longitud y no tiene `resumen-K.md`, ejecuta `resumir(carpeta, N, K)` ahora (el libro de estado necesita el capítulo que se queda).
2. Copia `capitulos/NN/libro-estado-K.md` sobre `libro-estado.md` (escritura completa).
3. `estado.capitulos[N] = { "aprobado": K, "por_agotamiento": <bool>, "intentos": <K máximo alcanzado> }`. Si por agotamiento, añade a `estado.avisos`: `"Capítulo N aceptado por agotamiento (mejor intento: K de <intentos>); ver capitulos/NN/informe-K.md"`.
4. `estado.capitulo_actual = N + 1`; `estado.intento_actual = 1`; si N es el último del arco A, `estado.arco_actual = A + 1` (salvo que sea el último arco). Guarda.
5. Commit `novela <slug>: cap NN cerrado (intento K)`.
6. Progreso: `[cap NN/<total>] intento K · APROBADO` o `… · RECHAZADO · aceptado por agotamiento (mejor intento: K) ⚠`.
