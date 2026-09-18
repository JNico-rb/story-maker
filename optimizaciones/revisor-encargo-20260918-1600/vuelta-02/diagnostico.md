# Diagnostico — vuelta 02 (split de busqueda, 6 casos)

Solo agregados por clase. Sin casos, sin capitulos, sin citas.

## Perfil de fallos del prompt vigente (mejor.md = produccion, medido en la vuelta 0)

| clase de defecto | esperados | vistos | recall de clase |
|---|---|---|---|
| suceso-adelantado | 10 | 4 | 0,40 |
| gancho-distinto   |  5 | 2 | 0,40 |
| ruptura-voz       |  5 | 2 | 0,40 |
| **total**         | 20 | 8 | **0,400** |

## La variante de la vuelta 1 (rechazada, para no repetirla)

| clase de defecto | esperados | vistos | recall de clase |
|---|---|---|---|
| suceso-adelantado | 10 | 2 | 0,20 |
| gancho-distinto   |  5 | 1 | 0,20 |
| ruptura-voz       |  5 | 1 | 0,20 |
| **total**         | 20 | 4 | **0,200** |

La perdida fue uniforme en las tres clases, no concentrada en la que la hipotesis atacaba.

## Lo que el perfil dice

1. Las tres clases fallan por igual (0,40 cada una en la linea base). No hay una clase dominante que justifique un
   procedimiento dedicado a una sola: el fallo es transversal.
2. Ningun caso se quedo sin informe en ninguna de las dos vueltas: el agente siempre responde y siempre cumple el
   esquema. El problema no es cobertura de ejecucion, es que la mitad de los defectos presentes no se reportan.
3. En la vuelta 1, endurecer el recorrido bajo la forma de los defectos reportados: el contenido se volvio mas
   parafraseado y menos pegado al texto del capitulo. El emparejador de la metrica solo cuenta un defecto cuando el
   informe reproduce literalmente el fragmento del capitulo en el que se apoya. Cualquier variante que reduzca la
   literalidad de la evidencia pierde puntos aunque el revisor haya visto el defecto.

## Restricciones

- Tamano: el prompt de produccion tiene 761 palabras; el tope es 989. La variante de la vuelta 1 llego a 965 y se quedo
  a 24 palabras del tope. Queda poco margen para crecer: prefiere reescribir antes que añadir.
- No hay restriccion de cita verificable aplicable en este contrato.
