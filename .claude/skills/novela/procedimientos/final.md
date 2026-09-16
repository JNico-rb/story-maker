# Etapa 3 — Final

Precondición: `estado.etapa == final` (todos los capítulos cerrados). Implementa `ensamblar`, `revisar_global` y `calcular_metricas` de SKILL.md §3. `calcular_metricas` también la usa `/novela verificar` (SKILL.md §8).

## ensamblar(carpeta) → manuscrito.md

Lo escribes tú, sin agente:

- Título: `titulo` del frontmatter de `escaleta.md`.
- Índice: lista de capítulos con el título de la primera línea de cada intento aprobado.
- Cuerpo: para cada N en orden, `## Capítulo N — <título>` seguido del texto de `capitulos/NN/intento-<estado.capitulos[N].aprobado>.md` sin su línea de título.
- Al final, una nota si algún capítulo fue aceptado por agotamiento, con enlace a su informe.

Registra `manuscrito(palabras = wc -w)`.

## revisar_global(carpeta) → informe-global.md

```
palabras = wc -w manuscrito.md
si palabras ≤ config.limites.revision_global_max_palabras:
    entradas = [manuscrito.md, biblia.md, escaleta.md, libro-estado.md, todos los resúmenes aprobados]; modo_texto = manuscrito
si no:
    entradas = [biblia.md, escaleta.md, libro-estado.md, todos los resúmenes aprobados, todos los arcos/informe-arco-*.md]; modo_texto = resúmenes
salida = invocar(revisor, global, K = –, entradas, validacion = JSON del revisor, destinos = ninguno)
escribe informe-global.md desde plantillas/informe.md: frontmatter con capitulo: "global", intento: –, base: <modo_texto>,
    el JSON tal cual (veredicto informativo), y el cuerpo en prosa legible
estado.informe_global = true; guardar
registra veredicto(GLOBAL informativo, veredicto, nº problemas, gravedad máx., base)
progreso "[final] revisión global (<base>): <n> problemas de gravedad 1–2"
```

**No reescribas nada** aunque haya problemas: quedan para el usuario.

### Prompt del revisor (modo global)

> Carpeta de la novela: `novelas/<slug>/`. Modo **global**: revisión de continuidad de la novela completa. Lee <`manuscrito.md`, | como el manuscrito no cabe: todos los informes de arco `arcos/informe-arco-*.md`,> `biblia.md`, `escaleta.md`, `libro-estado.md` y todos los resúmenes aprobados: <rutas>. Busca solo lo que no se ve capítulo a capítulo: hilos prometidos (sección Hilos de `escaleta.md`) y nunca cerrados, contradicciones entre capítulos lejanos, personajes que desaparecen sin explicación, cambios en las reglas del mundo. El veredicto es informativo: nadie reescribe. Devuelve únicamente el JSON de tu definición. No escribas ningún fichero.

## calcular_metricas(carpeta) → metricas

Todo sale de contar sobre los ficheros; ningún juicio. `T` = total de capítulos.

| Métrica | Cálculo | Umbral (`config.calidad`) | Cumple si |
|---|---|---|---|
| `graves_por_10` | problemas de gravedad 1 en `arcos/informe-arco-*.md` e `informe-global.md` ÷ T × 10 | `max_graves_por_10_capitulos` | ≤ |
| `agotamiento_pct` | capítulos con `por_agotamiento: true` ÷ T × 100 | `max_agotamiento_pct` | ≤ |
| `hilos_sin_cerrar` | hilos que `escaleta.md` (sección Hilos / `hilos_cierra` de los arcos) marca como cerrados en algún arco y siguen en "Hilos abiertos" de `libro-estado.md` | `max_hilos_previstos_sin_cerrar` | ≤ |
| `primer_intento_pct` | capítulos con `aprobado: 1` y `por_agotamiento: false` ÷ T × 100 | `min_aprobados_primer_intento_pct` | ≥ |
| `rechazos_voz_pct` | intentos cuyo `informe-K.md` tiene algún problema de gravedad 4 ÷ intentos totales × 100 | `max_rechazos_voz_pct` | ≤ |
| `desviacion_longitud` | media de \|`wc -w` intento aprobado − `palabras_objetivo`\| ÷ `palabras_objetivo`, en % | sin umbral: informativa | – |

Devuelve la tabla con valor, umbral y CUMPLE / NO CUMPLE por fila, más `cumple_todas` (bool). Va al informe de cierre (cierre.md) y a la salida de `/novela verificar`. Con un solo arco no hay informes de arco: `graves_por_10` sale solo del global.
