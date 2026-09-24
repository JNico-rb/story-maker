# Revisión humana — novela del brief 1

Qué es: plantilla para que una persona puntúe la versión publicada de la novela del brief 1 (`ejemplos/briefs/`) con la misma rúbrica que aplica `juez-novela`, para compararla con el juez (`RevisionHumana`, spec `020-C12`, `docs/verification.md` §4.2 (d)).

Cómo se usa:

1. Lee la novela completa en `ejemplos/novela-ejemplo.pdf` cuando exista (o la `VistaDeVersion` publicada del brief 1).
2. Puntúa **sin mirar antes** Langfuse ni la salida de `evals table`: ni las puntuaciones de `juez-novela`, ni las de otro validador.
3. Rellena las dos columnas vacías de cada fila; una frase por justificación.
4. Entrega este fichero al integrador, que lo compara con el juez y calcula el acuerdo.

## Rúbrica de novela (7 criterios, escala 1–5, no compensatoria)

Cada criterio se puntúa por separado, de 1 (inaceptable) a 5 (excelente); no hay media entre criterios ni veredicto global a mano — un bloqueante (**B**) por debajo del umbral (`quality.thresholds`, provisional 3) bloquea aunque el resto puntúe alto, y la personalización nunca compensa la calidad narrativa ni al revés.

| Criterio | B | Qué juzga (ancla) | Escala | Puntuación | Justificación (1 frase) |
|---|---|---|---|---|---|
| `continuidad` | sí | Sin contradicciones entre capítulos ni saltos temporales sin sentido; los hechos de la story bible se respetan | 1–5 | | |
| `coherencia-personajes` | sí | Cada personaje actúa y habla de forma consistente con lo que se sabe de él | 1–5 | | |
| `arco-y-final` | sí | La historia tiene un arco completo y el final no es abrupto ni queda colgando | 1–5 | | |
| `ritmo` | no | El ritmo entre capítulos: ni tramos vacíos ni atropellos | 1–5 | | |
| `tono` | no | El tono es el que pide el brief | 1–5 | | |
| `personalizacion-natural` | no | Los datos del destinatario están integrados en la historia, no insertados a la fuerza | 1–5 | | |
| `no-cliche` | no | La novela no cae en los tropos del `CatalogoDeTropos` por inercia; un tropo pedido en los deseos de trama no penaliza | 1–5 | | |

## Veredicto (calculado igual que el código, no a ojo)

El código, nunca la persona ni el juez, decide el veredicto a partir de las puntuaciones y el umbral: `accept` si ningún bloqueante queda por debajo del umbral; si alguno lo hace, no hay «accept».

| Criterio bloqueante | Puntuación | ¿≥ umbral (3)? |
|---|---|---|
| `continuidad` | | |
| `coherencia-personajes` | | |
| `arco-y-final` | | |
| **Veredicto** (accept si las tres son sí) | | |

## Comparación con el juez (la rellena el integrador)

| Criterio | Humano (1–5) | Juez (1–5) | \|Δ\| |
|---|---|---|---|
| `continuidad` | | | |
| `coherencia-personajes` | | | |
| `arco-y-final` | | | |
| `ritmo` | | | |
| `tono` | | | |
| `personalizacion-natural` | | | |
| `no-cliche` | | | |
| **Agregado** | | diferencia absoluta media: | |

Acuerdo (`docs/verification.md` §4.2 (d)): acuerdo exacto (mismas puntuaciones), acuerdo en bloqueantes (mismo lado del umbral en `continuidad`, `coherencia-personajes`, `arco-y-final`) y diferencia absoluta media entre las dos columnas. Regla: `|Δ| ≥ 2` en cualquier criterio, o un desacuerdo sobre si un bloqueante pasa el umbral, abre una iteración de tuning sobre el prompt o la rúbrica del juez.
