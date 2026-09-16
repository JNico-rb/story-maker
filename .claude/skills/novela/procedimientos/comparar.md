# Comparar un caso

`/novela comparar comparativa/caso-NN-<slug>`

Compara **dos novelas generadas con el mismo caso de referencia y distinta configuración** (modelo caro frente a barato; Claude Code frente al runner). Rellena `comparacion.md` del caso con datos reales. **No inventes ninguna cifra**: toda casilla sale de contar o de leer. Si un dato no está disponible, escribe `desconocido`, nunca una estimación.

## 1. Comprobaciones previas

1. El caso existe y tiene `caso.md` con frontmatter `lado_a` y `lado_b`.
2. Las dos carpetas existen y pasan `/novela verificar` (inventario completo, `etapa: completa`).
3. `idea.md` y `entrevista.md` son idénticos en las dos carpetas (comparación byte a byte, ignorando el frontmatter de la entrevista). Si no, dilo y para: no es un caso comparable.
4. `config.json` → `perfil` y `formato` iguales en las dos. Si no, no se comparan longitudes; anótalo.

Si falta algo, dilo y para: indica qué falta y qué tiene que hacer el usuario. No compares a medias.

## 2. Bloque medible

Para **cada lado**, leyendo su carpeta:

| Dato | De dónde |
|---|---|
| Métricas de calidad (las seis, con CUMPLE / NO CUMPLE) | `calcular_metricas(carpeta)` (final.md), recalculadas ahora, no copiadas del informe de cierre |
| Capítulos completos / previstos | `estado.json` → `capitulos` frente a `escaleta.md` → `capitulos` |
| Palabras totales y por capítulo | `wc -w` sobre cada intento aprobado; no te fíes de ningún frontmatter |
| Intentos por capítulo | `estado.json` → `capitulos[*].intentos` |
| Reintentos técnicos, discrepancias de veredicto, rechazos por longitud | `registro.md` → filas `decision_harness(reintento)`, `discrepancia_veredicto`, `longitud(rechazo)` |
| Problemas de arco y global por gravedad | frontmatter de `arcos/informe-arco-*.md` e `informe-global.md` |
| Invocaciones por agente | `estado.json` → `invocaciones` |
| Volumen y coste por modelo | Suma de `pal_*`, `tok_*` y `coste_usd` de las filas `invocacion` de `registro.md`, agrupadas por `modelo` |

## 3. Bloque de lectura

Lee los dos manuscritos enteros. Para cada criterio, una frase con **una cita o una referencia concreta** que la justifique; sin ejemplo, la casilla no vale.

**Continuidad**: elige tres hechos verificables del primer capítulo de cada manuscrito (un nombre, un objeto, un estado de un personaje) y compruébalos en el último. Anota cada contradicción con dónde aparece y qué la contradice. Comprueba además que `libro-estado.md` final refleja esos tres hechos: si el texto y el libro discrepan, es un fallo del resumidor (con ese modelo) y va a la lista de cambios.

**Cumplimiento del plan**: para cada capítulo de cada lado, ¿cumplió el `objetivo` y los `sucesos` de su entrada en la escaleta de arco? Si el revisor lo aprobó pero tú ves que no, dilo: es un fallo del revisor (con ese modelo) y va a la lista de cambios.

**Prosa y voz**: juicio honesto. Si el lado barato se lee igual o mejor, escríbelo tal cual; esa es la respuesta que decide el paso 2 del plan.

## 4. Conclusión

Veredicto en una palabra (A, B o empate) y qué significa para el plan de escalado (`specs/functional.md` §7.8). La regla de decisión es la de la spec §8.3: el lado barato **aguanta** si cumple todas las métricas que cumplió el lado caro. Después la lista de cambios propuestos para el harness, cada uno accionable: qué fichero tocar y qué cambiar (p. ej. "endurecer el criterio 4 del revisor: con `haiku` no detectó el cambio de tono del capítulo 3"). Si no hay nada que cambiar, déjalo vacío y dilo.

## 5. Cierre

Escribe `comparacion.md` desde `comparativa/plantilla/comparacion.md`, muéstralo resumido en la sesión y haz commit `comparativa <caso>: comparación`. No toques `novelas/`: la comparación no modifica ninguna novela.
