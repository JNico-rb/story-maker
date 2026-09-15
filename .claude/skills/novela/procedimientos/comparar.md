# Comparar un caso

`/novela comparar comparativa/caso-NN-<slug>`

Compara **dos novelas generadas con la misma idea y distinta configuración** (modelo caro frente a barato; Claude Code frente al runner). Rellena `comparacion.md` del caso con datos reales. **No inventes ninguna cifra**: toda casilla sale de contar o de leer. Si un dato no está disponible, escribe `desconocido`, nunca una estimación.

## 1. Comprobaciones previas

1. El caso existe y tiene `caso.md` con frontmatter `lado_a` y `lado_b`.
2. Las dos carpetas existen, tienen `estado.json` con `fase: completa`, `manuscrito.md`, `informe-global.md`, `registro.md` y `config.json`.
3. `idea.md` es la misma en las dos carpetas (si no, dilo y para: no es un caso comparable).
4. `config.json` → `perfil` y `formato` iguales en las dos (si no, no se comparan longitudes; anótalo).

Si falta algo, dilo y para: indica qué falta y qué tiene que hacer el usuario. No compares a medias.

## 2. Bloque medible

Para **cada lado**, leyendo su carpeta:

| Dato | De dónde |
|---|---|
| Capítulos completos / previstos | `estado.json` → `capitulos` frente a `escaleta.md` → `capitulos` |
| Palabras totales y por capítulo | Cuéntalas tú sobre `manuscrito.md` (`wc -w` por sección); no te fíes de ningún frontmatter |
| Fuera de tolerancia | Compara con `palabras_objetivo` de cada entrada ± `formato.tolerancia_longitud` |
| Intentos por capítulo, aceptados por agotamiento | `estado.json` → `capitulos[*].aprobado`, `por_agotamiento`, `avisos` |
| Reintentos técnicos, escrituras fuera de zona, discrepancias de veredicto | `registro.md` → filas `decision_harness(reintento)`, `escritura_fuera_de_zona`, `discrepancia_veredicto` |
| Problemas del informe global por gravedad | `informe-global.md` frontmatter |
| Artefactos que faltan | Lista de `specs/inventario.md` §1 |
| Invocaciones por subagente | `estado.json` → `invocaciones` |
| Volumen por modelo | Suma de `pal_entrada` y `pal_salida` de las filas `invocacion` de `registro.md`, agrupadas por `modelo` |

## 3. Bloque de lectura

Lee los dos manuscritos enteros. Para cada criterio, una frase con **una cita o una referencia concreta** que la justifique; sin ejemplo, la casilla no vale.

**Continuidad**: elige tres hechos verificables del primer capítulo de cada manuscrito (un nombre, un objeto, un estado de un personaje) y compruébalos en el último. Anota cada contradicción con dónde aparece y qué la contradice.

**Cumplimiento del plan**: para cada capítulo de cada lado, ¿cumplió el `objetivo` y los `sucesos` de su entrada en `escaleta.md`? Si el revisor lo aprobó pero tú ves que no, dilo: es un fallo del revisor (con ese modelo) y va a la lista de cambios.

**Prosa y voz**: juicio honesto. Si el lado barato se lee igual o mejor, escríbelo tal cual; esa es la respuesta que decide el paso 2 del plan.

## 4. Conclusión

Veredicto en una palabra (A, B o empate) y qué significa para el plan de escalado (`specs/functional.md` §7.7): si el lado barato aguanta, con qué configuración; si no, qué es lo que pierde. Después la lista de cambios propuestos para el harness. Cada cambio debe ser accionable: qué fichero tocar y qué cambiar (p. ej. "endurecer el criterio 4 del revisor: con `haiku` no detectó el cambio de tono del capítulo 3"). Si no hay nada que cambiar, déjalo vacío y dilo.

## 5. Cierre

Escribe `comparacion.md` desde `comparativa/plantilla/comparacion.md`, muéstralo resumido en la sesión y haz commit `comparativa <caso>: comparación`. No toques `novelas/`: la comparación no modifica ninguna novela.
