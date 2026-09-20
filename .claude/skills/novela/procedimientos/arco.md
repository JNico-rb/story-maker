# Arcos — detallar al empezar, revisar al cerrar

Implementa `detallar_arco` y `revisar_arco` de SKILL.md §3. `AA` = número de arco con dos dígitos. Con un solo arco, la escaleta de arco llegó con la propuesta (interrogatorio.md) y la revisión de arco se funde con la global (final.md): ninguna de las dos funciones se ejecuta.

## detallar_arco(carpeta, A) → arcos/arco-AA.md

Precondición: `estado.arcos[A].escaleta_validada == false` y `estado.capitulo_actual == estado.arcos[A].desde`.

```
salida = invocar(interrogador, arco, K = –,
    entradas   = [biblia.md, escaleta.md, libro-estado.md, arcos/informe-arco-<AA-1>.md si A > 1, config.json, plantillas/arco.md],
    validacion = bloque {arcos/arco-AA.md} con las reglas de invocar.md › extraer (rango exacto, longitudes, sucesos clave cubiertos),
    destinos   = arcos/arco-AA.md)
escribe arcos/arco-AA.md con `validada: true` en el frontmatter
estado.arcos[A].escaleta_validada = true; guardar
registra escaleta_validada(arco A, <desde>–<hasta>)
commitear(carpeta, "arco AA detallado")
progreso "[arco A/<total>] escaleta del arco validada (<n> capítulos)"
```

Las devoluciones por límites las gestiona `invocar` como incumplimiento de contrato con el motivo exacto ("la entrada 7 tiene 6.000 palabras; máximo 5.000", "el suceso clave 'X' no aparece en ninguna entrada"). Cuentan contra `limites.reintentos_tecnicos`; en el registro llevan además `escaleta_rechazos += 1`. No hay confirmación del usuario: la etapa 2 corre sin intervención humana.

### Prompt del interrogador (modo arco)

> Carpeta de la novela: `novelas/<slug>/`. Modo **arco**: detalla la escaleta del **arco A** (capítulos <desde>–<hasta>). Lee `biblia.md`, `escaleta.md` (tu arco es el nº A; no lo modifiques), `libro-estado.md` (lo que ha pasado de verdad hasta el capítulo <desde−1>) <y `arcos/informe-arco-<AA−1>.md` (lo que el arco anterior dejó pendiente)>, y `config.json` (`perfil`, `formato`). Plantilla: `.claude/skills/novela/plantillas/arco.md`. Una entrada por capítulo del rango, con título provisional, objetivo, sucesos, personajes, gancho y longitud objetivo (~<palabras_por_capitulo> palabras; entre <palabras_min_capitulo> y <palabras_max_capitulo>). Todos los sucesos clave del arco en `escaleta.md` deben quedar asignados a un capítulo concreto. Devuelve el documento en un bloque `=== ARCHIVO: arcos/arco-AA.md ===` … `=== FIN ===`. No escribas ningún fichero.

## revisar_arco(carpeta, A) → arcos/informe-arco-AA.md

Precondición: el capítulo `estado.arcos[A].hasta` acaba de cerrarse. Se ejecuta **antes** de `pausa_programada` y solo si hay más de un arco.

```
salida = invocar(revisor-continuidad, arco, K = –,
    entradas   = [intento aprobado de cada capítulo del arco, arcos/arco-AA.md, escaleta.md, biblia.md, libro-estado.md],
    validacion = JSON del revisor (gravedades 1 y 5),
    destinos   = ninguno (el informe lo escribes tú, abajo))
escribe arcos/informe-arco-AA.md desde plantillas/informe.md: frontmatter con capitulo: "arco-AA", intento: –,
    el JSON (veredicto tal cual, es informativo), y el cuerpo en prosa legible
estado.arcos[A].informe = true; guardar
registra veredicto(ARCO A informativo, veredicto, nº problemas, gravedad máx.)
commitear(carpeta, "arco AA revisado")
progreso "[arco A/<total>] informe de arco: <n> problemas de gravedad 1"
```

Nada se reescribe. El informe alimenta `detallar_arco(A+1)` y las métricas de calidad (final.md).

### Prompt del revisor de continuidad (modo arco)

> Carpeta de la novela: `novelas/<slug>/`. Modo **arco**: revisión de continuidad del **arco A** completo (capítulos <desde>–<hasta>). Lee los capítulos aprobados: <rutas `capitulos/NN/intento-K.md`>, la escaleta del arco `arcos/arco-AA.md`, `escaleta.md`, `biblia.md` y `libro-estado.md`. Busca solo lo que no se ve capítulo a capítulo: hilos que el arco debía cerrar (según `escaleta.md`) y no cerró, contradicciones entre capítulos del arco, personajes que desaparecen sin explicación, cambios de reglas del mundo. El veredicto es informativo: nadie reescribe. Devuelve únicamente el JSON de tu definición. No escribas ningún fichero.
