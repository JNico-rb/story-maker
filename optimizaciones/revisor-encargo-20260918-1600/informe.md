# Informe — optimizacion revisor-encargo (revisor-encargo-20260918-1600)

Ejecucion iniciada el 2026-09-18 y **reanudada el 2026-09-20** con `continuar`. Este informe se reescribe
entero e incluye las cuatro vueltas mas la linea base, no solo las de la reanudacion.

- **Motivo de cierre**: ESTANCAMIENTO (4 vueltas consecutivas sin mejora sobre control). Coincide con el
  agotamiento del presupuesto: se hicieron las 4 vueltas presupuestadas mas la linea base.
- **Metrica**: recall_revisor. **Objetivo**: >= 0,80 en control. **Conjunto**: ascensores-v1 (hash
  d69413ab6bff).
- **Restricciones**: cita_verificable_min 0,90 (no aplicable, el contrato de este agente no tiene campo de
  cita) y tope de palabras (factor 1,3 sobre produccion = 989). Ninguna vuelta incumplio el tope.

## Linea base (vuelta 0, produccion.md instalado)

| split | recall_revisor |
|---|---|
| busqueda | 0,400 (8/20) |
| control  | 0,500 (6/12) |

## Vueltas

| vuelta | operacion | busqueda | control | mejor_control | aceptada | motivo |
|---|---|---|---|---|---|---|
| 0 | — (base) | 0,400 | 0,500 | 0,500 | — | linea base |
| 1 | 2 (procedimiento de 4 pasos para adelantos) | 0,200 | 0,500 | 0,500 | no | control +0,00 < 0,10; busqueda regresa |
| 2 | 4 (cita literal obligatoria en `donde`) | 0,150 | 0,250 | 0,500 | no | control -0,250 |
| 3 | 3 (prohibir mandar desajustes a `observaciones`) | 0,200 | 0,083 | 0,500 | no | control -0,417; la peor de todas |
| 4 | 5 (**recortar**: borrar la vineta de no duplicar) | 0,200 | 0,333 | 0,500 | no | control -0,167; 4ª sin mejora |

**Mejor score en control: 0,500, en la vuelta 0 (linea base).** Ninguna variante la supero ni la igualo. El
objetivo de 0,80 no se alcanzo en ningun momento.

## Por que se rechazo cada vuelta

- **v1 (op2)**: procedimiento de 4 pasos para el vector de adelantos. La deteccion no bajo, pero el informe se
  volvio mas parafraseado y el emparejador (exige cita literal) dejo de contar defectos igualmente vistos.
- **v2 (op4)**: cita literal entrecomillada obligatoria. Efecto contrario al buscado: ante el coste de citar
  con exactitud el agente se callo en mas casos (3 de 6 en busqueda pasaron a "sin problemas"). Peor variante
  probada en busqueda.
- **v3 (op3)**: retirar la valvula de escape de `observaciones`. Busqueda mejoro algo frente a v2, pero
  control fue el peor de toda la ejecucion (0,083).
- **v4 (op5)**: borrar la vineta "no duplicar el mismo problema en varias entradas". Primera y unica variante
  que RECORTA. Rechazada por -0,167 en control, pero es la mas informativa de las cuatro (ver abajo).

## La vuelta 4, que es lo que anade esta reanudacion

La hipotesis de v4 era falsable y **se falso en su propia prediccion**, que es el unico resultado limpio de la
ejecucion. Predijo que borrar la vineta subiria `suceso-adelantado` y dejaria quieto `gancho-distinto`:

| clase | base (busqueda) | v4 (busqueda) | base (control) | v4 (control) |
|---|---|---|---|---|
| suceso-adelantado | 4/10 | **1/10** | 2/4 | **0/4** |
| gancho-distinto   | 2/5  | 2/5   | 3/3 | 3/3 |
| ruptura-voz       | 2/5  | 1/5   | 1/4 | 1/4 |
| hilo-cerrado-antes| —    | —     | 0/1 | 0/1 |

Paso lo contrario en la clase que importaba: `suceso-adelantado` bajo en las dos particiones, y
`gancho-distinto` se quedo clavado en el mismo numero. En control, **toda** la caida de v4 es
`suceso-adelantado`: las otras tres clases dan exactamente la cifra de la linea base.

## Leccion transversal a las cuatro vueltas

Las cuatro direcciones posibles sobre el texto del prompt se han probado y las cuatro han dado peor que
produccion: anadir procedimiento (v1), anadir exigencia de forma (v2), anadir una prohibicion (v3) y quitar
una linea (v4). Ninguna movio `gancho-distinto` ni `ruptura-voz` en control.

Un prompt cuyo recall baja se le haga lo que se le haga, y que en control solo se mueve en una clase, es la
firma de que lo que varia no es la deteccion sino el **emparejamiento**. La recomendacion que deja esta
ejecucion es no gastar una quinta vuelta en el prompt y **auditar antes `recall_revisor`**: empareja por
subcadena literal contra el capitulo o la entrada de escaleta, y su propio generador de casos
(`herramientas/optimizacion/casos/generar.py`) declara que mide "lo menciono", no "lo detecto". El detalle
esta en `optimizaciones/revisor-encargo/lecciones.md`.

## Invocaciones y presupuesto

- Gastadas: 47 de 60 (tope). No se agoto el tope; el cierre fue por estancamiento y por agotar las 4 vueltas.
- **Consultas al split de control: 5 en total** (vuelta 0 y las cuatro variantes). Con 5 consultas sobre 12
  defectos y 3 casos, la reserva de la spec §9.5.3 vale entera: lo que sostiene este resultado es la
  **direccion** (ninguna modificacion del prompt mejora, y el fallo se concentra en una clase), no la
  magnitud exacta de cada caida. Una diferencia de un solo defecto mueve el score 0,083.

## Estado del agente y del conjunto

- `.claude/agents/revisor-encargo.md` restaurado a produccion y verificado por hash
  (`57ee40d452b63dc17b1ab982fb9dc18c054241d0`) tras la vuelta 4. El arbol de trabajo queda limpio en
  `.claude/agents/`.
- **El hash del conjunto no se ha podido comparar desde la sesion**: el hook `rutas-protegidas.sh` impide
  tocar el directorio del conjunto etiquetado (y hace bien; tampoco hay guion que publique ese hash). Lo que
  si consta: ningun commit desde 2026-09-17 toca ese directorio y el arbol de trabajo no tiene
  modificaciones ahi, asi que el conjunto es, con toda probabilidad, el mismo con el que se midio la linea
  base. **No es la comprobacion de hash que pide §0.1.3**, y queda dicho aqui como tal.
- Publicacion en Langfuse de la vuelta 4: **fallo** (HTTP 400 al postear el score). Fail-open por spec §9.3
  regla 3: la vuelta esta medida y escrita en disco; lo que falta es la curva en Langfuse.

## Candidato

No hay candidato: ninguna variante supero la linea base.
`optimizaciones/revisor-encargo-20260918-1600/mejor.md` sigue siendo una copia byte a byte de
`produccion.md`. No se publica nada con etiqueta `candidato` porque el motivo de cierre no fue
METRICA_ALCANZADA.
