# Etapa 1 — Interrogatorio

Objetivo: `biblia.md` y `escaleta.md` aprobadas por el usuario, dentro de límites, **con el canon validado**, y `estado.etapa = capitulos`. Implementa `entrevistar`, `proponer_escaleta` y `validar_canon` de SKILL.md §3.

## entrevistar(carpeta) → entrevista.md

La hace el **orquestador**, no un agente. Los agentes nunca hablan con el usuario.

1. Si `entrevista.md` existe con `cerrada: true`, no hagas nada (reanudación).
2. Si el comando trae `entrevista: <ruta>` o `modo-prueba: <carpeta>`: copia esa `entrevista.md` a la carpeta de la novela, pon `cerrada: true` y `origen: fichero` en el frontmatter, registra `entrevista_cerrada (origen: <ruta>)` y termina. Esto es lo mismo que hará el runner: la entrevista le llega hecha.

   **`precarga: <ruta>` no es esto.** Si el comando trae `precarga: <carpeta>` (lo que manda el estudio, spec §9.4), lee ahí `entrevista-previa.md` y **no cierres nada**: sus respuestas son el punto de partida del paso 3, no la entrevista. Sigue al paso 3 con ellas en la mano. La diferencia importa: `entrevista:` se salta el grilling —correcto para el modo de prueba y para el runner, que no tienen a quién preguntar—, y aquí hay un usuario al otro lado esperando a que le repregunten.
3. **Uso normal**: invoca la skill `mattpocock-skills:grilling` con este encargo:

   > Diseñar una novela en castellano sobre el mundo tras la revolución de la IA a partir de esta idea: «<idea>». Hay que cerrar, como mínimo: qué versión del mundo post-IA es (qué pasó, qué reglas rigen ahora, qué ha cambiado en la vida diaria); protagonista (quién es, qué quiere, qué le falta) y antagonismo; tono y registro; punto de vista y persona narrativa; tipo de final; temas a tocar y temas a evitar; extensión (entre <capitulos_min> y <capitulos_max> capítulos de <palabras_min>–<palabras_max> palabras; sugerido <capitulos_objetivo> × <palabras_por_capitulo>). Cada novela inventa su propio mundo; no hay canon previo.

   La skill pregunta en rondas, con recomendación, y termina cuando el usuario confirma el entendimiento compartido. No añadas preguntas fuera de ella.

   **Con precarga**, añade al encargo: «El usuario ya ha contestado por adelantado lo siguiente: <contenido de `entrevista-previa.md`>. **No vuelvas a preguntar lo que ya está contestado.** Pregunta solo lo que falta, lo que quede ambiguo y lo que esas respuestas abran; lo marcado *decide tú* se deja abierto a propósito y tampoco se pregunta.» Un usuario que acaba de rellenar doce campos y al que se le vuelven a preguntar los doce cierra la pestaña.
4. Escribe `entrevista.md` desde `plantillas/entrevista.md` con **todas** las decisiones en pregunta → respuesta, cada una marcada **[usuario]**, **[recomendación aceptada]** o **[decide tú]**. `cerrada: true`, `origen: grilling` (o `formulario+grilling` si hubo precarga). Registra `entrevista_cerrada (N preguntas, M rondas)`.

## proponer_escaleta(carpeta) → biblia.md, escaleta.md [, arcos/arco-01.md]

```
vuelta = 0; motivo = null
# Reanudación tras ESPERA_APROBACION: la propuesta ya está escrita y solo falta la decisión.
# No se vuelve a invocar al interrogador: gastaría una invocación para producir otra propuesta
# distinta de la que el usuario tiene delante en el estudio.
si existen biblia.md y escaleta.md sin `aprobada: true`:
    decision = confirmar_con_usuario(problemas_canon del último informe, si lo hay)
    si decision == confirma: aprobar(); return
    vuelta = 1; motivo = "CAMBIOS: <texto del usuario>"
bucle:
    salida = invocar(interrogador, propuesta, K = –,
        entradas   = [idea.md, entrevista.md, config.json, plantillas/biblia.md, plantillas/escaleta.md, plantillas/arco.md],
        validacion = bloques {biblia.md, escaleta.md} + arcos/arco-01.md si un solo arco,
        destinos   = las mismas rutas dentro de la carpeta)
    # invocar ya ha comprobado límites y forma (invocar.md › extraer). Si falló por límites, invocar reintentó
    # con el motivo; si agotó reintentos, ya paró con INCUMPLE_CONTRATO. Aquí solo llega una propuesta válida.
    problemas_canon = validar_canon(carpeta)                       # abajo
    si problemas_canon y vuelta < config.limites.escaleta_rechazos_max:
        vuelta += 1; motivo = "CANON: <lista de problemas>"; continuar   # sin molestar al usuario
    registra propuesta_cierre(título, capítulos, arcos)
    si modo_prueba: decision = confirma; registra decision_usuario(auto, modo prueba)
    si no: decision = confirmar_con_usuario(problemas_canon)       # los que quedaran sin resolver, a la vista
    si decision == confirma: salir
    vuelta += 1; motivo = "CAMBIOS: <texto del usuario>"           # vuelve a invocar con el motivo en el prompt
aprobar()
```

**Un solo arco** cuando `perfil.capitulos_objetivo ≤ formato.capitulos_por_arco` (y el interrogador debe mantener el total dentro de ese tope; si propone más capítulos que `capitulos_por_arco` en un perfil pequeño, la validación exige entonces varios arcos y la escaleta de arco no va en la propuesta).

### Prompt del interrogador (modo propuesta)

> Carpeta de la novela: `novelas/<slug>/`. Modo **propuesta**. Lee `idea.md`, `entrevista.md` y `config.json` (sección `perfil` y `formato`). Plantillas: `.claude/skills/novela/plantillas/biblia.md`, `escaleta.md` y `arco.md`. La biblia debe llevar su sección «Cronología y datos fijos» completa y cuadrada: haz las restas antes de entregar. Objetivo orientativo: <capitulos_objetivo> capítulos de ~<palabras_por_capitulo> palabras. Límites duros: <capitulos_min>–<capitulos_max> capítulos; cada longitud objetivo entre <palabras_min_capitulo> y <palabras_max_capitulo>; arcos de como mucho <capitulos_por_arco> capítulos que cubran todos los capítulos sin huecos ni solapes. <Si un solo arco: "Como la novela cabe en un arco, devuelve también `arcos/arco-01.md` con la entrada de cada capítulo."> Devuelve los documentos en bloques `=== ARCHIVO: <ruta> ===` … `=== FIN ===` y después una propuesta de cierre de 3–5 líneas. No escribas ningún fichero.
>
> (Vuelta > 0) Vuelta anterior devuelta por: <motivo>. Corrige solo eso y conserva el resto.

## validar_canon(carpeta) → problemas

La biblia es la única cosa que nadie vuelve a cuestionar: a partir de la aprobación, todos los agentes la usan como vara de medir. Este es el único momento en que se comprueba que **no se contradice a sí misma** (spec §4.1). En la ejecución de referencia dos incoherencias de canon —una edad incompatible con una fecha, un edificio con menos paradas que plantas— envenenaron los cinco capítulos sin que ninguna revisión pudiera verlas.

```
salida = invocar(revisor-continuidad, canon, K = –,
        entradas   = [biblia.md, escaleta.md],
        validacion = JSON del revisor (gravedades permitidas: 1),
        destinos   = ninguno)
registra veredicto(CANON, <veredicto>, nº problemas, gravedad máx.)
progreso "[interrogatorio] canon: <n> problemas<· devuelto al interrogador (vuelta/max) si los hay>"
return salida.problemas
```

Si quedan problemas después de `escaleta_rechazos_max` vueltas, **no pares**: enséñaselos al usuario junto con la propuesta. Quien aprueba la biblia es él, y una biblia con una tensión que él acepta a conciencia es legítima; lo que no es legítimo es que no la vea.

### confirmar_con_usuario(problemas_canon)

Muestra al usuario, en la sesión: la premisa, el mundo en tres líneas, la lista de personajes con una línea cada uno, las reglas inviolables, la sección «Cronología y datos fijos», y la escaleta como tabla (arco · capítulos · acto · objetivo; con un solo arco, también la tabla capítulo · título · objetivo · palabras). Si `problemas_canon` no está vacío, enséñalos antes de preguntar, con el aviso de que el interrogador no los resolvió en <max> vueltas. Pregunta: **"¿Confirmas biblia y escaleta, o quieres cambios?"**. Registra `decision_usuario(confirma | cambios: <texto>)`. Nada se aprueba sin confirmación explícita.

**Si `estado.encargo` no es `null`, no hay nadie escuchando en esta sesión.** Es la señal, y es exacta: `estado.encargo` solo lo escribe `crear_novela` cuando el comando trajo `precarga:`, y eso solo lo manda el estudio (spec §9.4). No preguntes al vacío ni te apruebes tú la propuesta:

1. Si `estado.encargo` no es `null` y existe `<estado.encargo>/decision.md`, léelo: `confirma` cierra el bucle, `cambios: <texto>` es el motivo de la vuelta siguiente. **Renómbralo** a `decision-aplicada-<fecha>.md` después de leerlo, para que no se aplique dos veces, y registra `decision_usuario(<decisión>, origen: encargo)`.
2. Si no, `cerrar(carpeta, PARADA, ESPERA_APROBACION)` con el detalle: qué propone (título, capítulos, arcos), los `problemas_canon` que queden y dónde están `biblia.md` y `escaleta.md`. **No las marques como aprobadas**: se quedan sin `aprobada: true`, que es lo que hace que el hook de inmutabilidad las deje reescribir en la vuelta siguiente (spec §3.1).

`decision.md` vive en **`encargos/<slug>/`, nunca en la carpeta de la novela**, y no es un detalle: `novelas/` es del harness en exclusiva (spec §3.1, §9.4), y además `reanudar` paso 1 descarta todo lo que encuentre sin commitear dentro de `novelas/<slug>`, así que una decisión dejada ahí se borraría antes de leerse.

Al reanudar, `proponer_escaleta` vuelve a entrar por aquí y encuentra la decisión que el estudio —o el usuario con un editor— haya dejado.

### aprobar()

1. Reescribe `biblia.md` y `escaleta.md` con `aprobada: true` en el frontmatter (escritura completa, lo haces tú). Si hay `arcos/arco-01.md`, ponle `validada: true`.
2. `estado.escaleta_aprobada = true`; `estado.total_capitulos = escaleta.capitulos`; `estado.arcos = { "1": {desde, hasta, escaleta_validada: <true si vino en la propuesta>, informe: false}, … }` a partir de `escaleta.arcos`; `estado.arco_actual = 1`; `estado.capitulo_actual = 1`; `estado.intento_actual = 1`; `estado.etapa = capitulos`. Guarda.
3. Commit `novela <slug>: escaleta aprobada`.
4. Progreso: `[etapa 1] escaleta aprobada: <título>, <capítulos> capítulos en <arcos> arco(s)`.

## Reanudación

- `entrevista.md` no existe o no está cerrada → `entrevistar` desde el principio; grilling puede leer lo que haya para no repetir preguntas.
- Cerrada pero escaleta no aprobada → `proponer_escaleta` desde el principio (los ficheros a medias fueron descartados al reanudar).
