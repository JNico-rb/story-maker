# Fase 2 — Un capítulo (N)

Precondición: `estado.fase == capitulos`, `git status` limpio en la carpeta. `K = estado.intento_actual` (1 si empieza). `NN` = N con dos dígitos.

## Bucle de intentos

```
repetir:
    1. ESCRITOR   → intento-K.md + resumen-K.md
    2. REVISOR    → informe (YAML en su mensaje) → tú lo escribes en informe-K.md
    3. veredicto = recalcular(problemas)          (regla en config.json: veredicto)
    4. APROBADO                → cerrar(N, K, por_agotamiento=false)
       RECHAZADO y K ≤ reescrituras_max → K += 1; estado.intento_actual = K; guardar estado; seguir
       RECHAZADO y K > reescrituras_max → cerrar(N, K, por_agotamiento=true) con aviso
```

### 1. Escritor

Modelo: según SKILL.md §8. Construye el prompt con **exactamente** esto (rutas, no contenidos):

> Carpeta: `novelas/<slug>/`. Vas a escribir el **capítulo N (intento K)**. Lee: `biblia.md`; `escaleta.md` (tu entrada es la nº N); los resúmenes aprobados según `config.json` → `memoria` (todos si `resumenes_completos_ultimos` es `null`; si no, solo los N últimos): `capitulos/01/resumen-<k1>.md` … `capitulos/<N-1>/resumen-<k>.md`; si `memoria.capitulo_anterior_integro` es `true`, el capítulo anterior aprobado íntegro `capitulos/<N-1>/intento-<k>.md`. Longitud objetivo: <palabras_objetivo> palabras (tolerancia ±<tolerancia>%). Escribe SOLO `capitulos/NN/intento-K.md` y `capitulos/NN/resumen-K.md`. Termina con `ENTREGA: intento-K.md (<palabras> palabras), resumen-K.md`. Máximo <turnos_por_invocacion> acciones.
>
> (Si K > 1) Tu intento anterior fue RECHAZADO. Lee `capitulos/NN/informe-<K-1>.md` y `capitulos/NN/intento-<K-1>.md`. Corrige cada problema del informe sin introducir otros; puedes reutilizar lo que no estaba mal.

Para N = 1 no hay resúmenes ni capítulo anterior: dilo explícitamente en el prompt.

`verificar-zona.md` con zona = {`capitulos/NN/intento-K.md`, `capitulos/NN/resumen-K.md`}. Validación: ambos existen y no están vacíos; `intento-K.md` tiene frontmatter `palabras`; `resumen-K.md` tiene frontmatter `hilos_abiertos`, `hilos_cerrados`, `personajes`. Cuenta las palabras tú mismo por encima (aprox.) para el registro; el juicio de longitud es del revisor.

### 2. Revisor

> (Modelo según SKILL.md §8.) Carpeta: `novelas/<slug>/`. Revisa el **capítulo N, intento K**. Lee `capitulos/NN/intento-K.md`, `capitulos/NN/resumen-K.md`, `biblia.md`, `escaleta.md` (entrada nº N) y los resúmenes aprobados anteriores: <lista de rutas>. Longitud objetivo <palabras_objetivo> ±<tolerancia>%. No escribas ningún fichero salvo, si lo necesitas, `capitulos/NN/notas-revisor-K.md`. Devuelve el informe como bloque YAML según tu definición. Máximo <turnos_por_invocacion> acciones.

`verificar-zona.md` con zona = {`capitulos/NN/notas-revisor-K.md`}. Validación: el mensaje final contiene un bloque YAML con `veredicto` ∈ {APROBADO, RECHAZADO}, `problemas` (lista, puede estar vacía) donde cada uno tiene `gravedad` 1-5, `donde`, `que`, `por_que`; y `observaciones` (lista).

### 3. Veredicto

Aplica la regla de `config.json` (`veredicto.rechaza_con_graves` problemas de gravedad 1-2, o `veredicto.rechaza_con_leves` de gravedad 3-5 → RECHAZADO) a `problemas`. Si difiere del `veredicto` del revisor, manda el tuyo y registra `discrepancia_veredicto`. Escribe `capitulos/NN/informe-K.md`: el YAML como frontmatter (con el veredicto final y, si hubo discrepancia, `veredicto_revisor`), y en el cuerpo la lista de problemas en prosa legible.

Registra `veredicto` (veredicto, nº problemas, gravedad máx.) y `decision_harness` (aprobar | reescribir | aceptar_por_agotamiento).

### 4. cerrar(N, K, por_agotamiento)

1. `estado.capitulos[N] = { "aprobado": K, "por_agotamiento": <bool> }`. Si por agotamiento, añade a `estado.avisos`: `"Capítulo N aceptado por agotamiento tras K intentos; ver capitulos/NN/informe-K.md"`.
2. `estado.capitulo_actual = N + 1`, `estado.intento_actual = 1`. Si N era el último → `estado.fase = final`.
3. Guarda `estado.json`. Commit `novela <slug>: cap NN cerrado (intento K)`.
4. Línea de progreso en la sesión (formato en SKILL.md §4).
5. Si `N % pausa_cada_capitulos == 0` y N no es el último y la sesión va cargada → PARADA `PAUSA_PROGRAMADA` (cierre.md), pidiendo `/novela continuar`.
