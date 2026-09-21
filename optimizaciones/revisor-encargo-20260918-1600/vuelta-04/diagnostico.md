# Diagnostico — vuelta 04 (split de busqueda, 6 casos)

Solo agregados por clase. Sin casos, sin capitulos, sin citas.

## Prompt vigente (mejor.md = produccion, medido en la vuelta 0)

| clase de defecto | esperados | vistos | recall de clase |
|---|---|---|---|
| suceso-adelantado | 10 | 4 | 0,40 |
| gancho-distinto   |  5 | 2 | 0,40 |
| ruptura-voz       |  5 | 2 | 0,40 |
| **total**         | 20 | 8 | **0,400** |

La linea base sigue siendo la mejor marca de toda la ejecucion. Ninguna de las tres variantes la ha igualado.

## Las tres variantes ya probadas y rechazadas

| clase | base | v1 (op2) | v2 (op4) | v3 (op3) |
|---|---|---|---|---|
| suceso-adelantado | 4/10 | 2/10 | 1/10 | 2/10 |
| gancho-distinto   | 2/5  | 1/5  | 2/5  | 1/5  |
| ruptura-voz       | 2/5  | 1/5  | 0/5  | 1/5  |
| **total busqueda**| **0,400** | **0,200** | **0,150** | **0,200** |
| **control**       | **0,500** | **0,500** | **0,250** | **0,083** |

## Lo que dicen tres vueltas fallidas seguidas

1. **Las tres variantes empeoraron busqueda, y ninguna mejoro control.** Las tres eran, en el fondo, la misma
   maniobra: **anadir texto al prompt**. v1 anadio procedimiento, v2 anadio exigencia de forma, v3 anadio una
   prohibicion. La direccion "escribir mas instrucciones" esta refutada tres veces, con tres contenidos
   distintos y con hipotesis que en los tres casos sonaban razonables antes de medirse.
2. **v3 refuta ademas su propia hipotesis de umbral.** Se retiro la valvula de escape de `observaciones`
   esperando que lo detectado saliera por `problemas`; el resultado fue el peor de control de toda la
   ejecucion. Bajar el umbral por via de una prohibicion nueva tampoco funciona.
3. **El perfil por clase de v1 y v3 es identico** (2/10, 1/5, 1/5) pese a ser cambios sin nada en comun. Dos
   intervenciones distintas producen la misma perdida: lo que degrada el recall no parece ser *que* se anade,
   sino *que se anade*, sea lo que sea.
4. **Ningun caso se queda sin informe, el esquema siempre se cumple y no hay problema de ejecucion.** Todas
   las perdidas son defectos que el informe no recoge, no fallos de formato ni de contrato.
5. **Las tres clases caen juntas y en la misma proporcion en todas las vueltas.** No hay una clase que se
   pueda atacar por separado: cualquier cambio global las mueve a las tres en el mismo sentido.

## Direccion sugerida por el perfil, no por el gusto

Queda un unico vector sin probar, y es el contrario a los tres intentos: **recortar**. Menos vinetas, menos
condiciones, menos casuistica; dejar el criterio de que es un problema lo mas corto y directo posible. Es
coherente con el unico patron estable de la ejecucion: cada capa de instruccion anadida sobre este prompt de
haiku ha reducido lo que el agente reporta.

## Restricciones

- Tamano: produccion 761 palabras, tope 989 (no hay minimo). Las tres variantes crecieron (965, 878, 859) y
  las tres empeoraron. Una variante mas corta que produccion no incumple ninguna restriccion.
- No hay restriccion de cita verificable aplicable en este contrato.
