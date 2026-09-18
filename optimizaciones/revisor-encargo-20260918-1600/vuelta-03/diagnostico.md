# Diagnostico — vuelta 03 (split de busqueda, 6 casos)

Solo agregados por clase. Sin casos, sin capitulos, sin citas.

## Prompt vigente (mejor.md = produccion, medido en la vuelta 0)

| clase de defecto | esperados | vistos | recall de clase |
|---|---|---|---|
| suceso-adelantado | 10 | 4 | 0,40 |
| gancho-distinto   |  5 | 2 | 0,40 |
| ruptura-voz       |  5 | 2 | 0,40 |
| **total**         | 20 | 8 | **0,400** |

## Las dos variantes ya probadas y rechazadas

| clase | base | v1 (op2) | v2 (op4) |
|---|---|---|---|
| suceso-adelantado | 4/10 | 2/10 | 1/10 |
| gancho-distinto   | 2/5  | 1/5  | 2/5  |
| ruptura-voz       | 2/5  | 1/5  | 0/5  |
| **total busqueda**| **0,400** | **0,200** | **0,150** |
| **control**       | **0,500** | **0,500** | **0,250** |

## Lo que dicen dos vueltas fallidas seguidas

1. **Las dos variantes empeoraron, y la segunda mas que la primera.** Ambas anadian exigencia: v1 un
   procedimiento de busqueda mas largo, v2 un requisito de forma mas duro sobre cada problema emitido. La
   direccion "pedir mas al prompt" esta refutada dos veces.
2. **El modo de fallo de v2 es informativo.** Al encarecer la emision de un problema, la mitad de los casos
   pasaron a devolver la lista de problemas VACIA. El agente no gasto el esfuerzo extra en citar mejor: se
   callo. Es decir, el agente prefiere no reportar antes que reportar de una forma que le cuesta.
3. **Ningun caso se queda sin informe y el esquema siempre se cumple.** El cuello de botella no es la
   ejecucion ni el formato: es el umbral con el que el agente decide que algo merece ser un problema.
4. **La clase ruptura-voz es la mas fragil**: cayo a 0 con v2. Es la unica que no depende de comparar con la
   escaleta, sino de comparar con la biblia.

## Direccion sugerida por el perfil, no por el gusto

El vector no explorado es el contrario al de v1 y v2: **bajar el umbral de emision**, no subirlo. Decirle
explicitamente que ante la duda emita el problema y deje que el harness lo filtre, en vez de callarse. El
agente ya sabe donde mirar (base 0,40 en las tres clases por igual, no 0); lo que no hace es reportar lo que
ve cuando no esta seguro.

## Restricciones

- Tamano: produccion 761 palabras, tope 989. v2 uso 878. Hay margen, pero las dos veces que se crecio se
  empeoro: preferible una variante corta.
- No hay restriccion de cita verificable aplicable en este contrato.
