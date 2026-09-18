# Informe — optimizacion revisor-encargo (revisor-encargo-20260918-1600)

- **Motivo de cierre**: ESTANCAMIENTO (3 vueltas consecutivas sin mejora sobre control; presupuesto era de 4 vueltas, se hicieron 3 mas la linea base).
- **Metrica**: recall_revisor. **Objetivo**: >= 0,80 en control. **Conjunto**: ascensores-v1 (hash d69413ab6bff, sin cambios durante toda la ejecucion).
- **Restricciones**: cita_verificable_min 0,90 (no aplicable, el contrato no tiene ese campo) y tope de palabras (factor 1,3 sobre produccion = 989). Ninguna vuelta incumplio el tope.

## Linea base (vuelta 0, produccion.md instalado)

| split | recall_revisor |
|---|---|
| busqueda | 0,400 (8/20) |
| control  | 0,500 (6/12) |

Perfil por clase (busqueda): suceso-adelantado 4/10, gancho-distinto 2/5, ruptura-voz 2/5 — las tres al 0,40, sin clase dominante.

## Vueltas

| vuelta | operacion | busqueda | control | mejor_control | aceptada | motivo |
|---|---|---|---|---|---|---|
| 0 | — (base) | 0,400 | 0,500 | 0,500 | — | linea base |
| 1 | 2 (procedimiento de 4 pasos para adelantos) | 0,200 | 0,500 | 0,500 | no | control +0,00 < 0,10; busqueda regresa |
| 2 | 4 (cita literal obligatoria en `donde`) | 0,150 | 0,250 | 0,500 | no | control -0,250; peor variante probada |
| 3 | 3 (prohibir mandar desajustes a `observaciones`) | 0,200 | 0,083 | 0,500 | no | control -0,417; la peor de las tres; dispara ESTANCAMIENTO |

**Mejor score en control: 0,500, en la vuelta 0 (linea base).** Ninguna variante la superó ni la igualó.

## Por que se rechazo cada vuelta

- **v1 (op2)**: aislar un procedimiento de 4 pasos para el vector de adelantos. La deteccion no bajo, pero el informe se volvio mas parafraseado y el emparejador (exige cita literal) dejo de contar los defectos igualmente vistos.
- **v2 (op4)**: en respuesta a v1, se exigio cita literal entrecomillada. Efecto contrario al buscado: el agente, ante el coste de citar con exactitud, se callo en mas casos (3 de 6 en busqueda pasaron a "sin problemas"). Peor que v1 en las dos particiones.
- **v3 (op3)**: hipotesis de que el problema era una valvula de escape (`observaciones`) y no la exigencia de forma. Se retiro esa valvula con una sola vineta. Busqueda mejoro algo frente a v2 pero control fue el peor de los tres (0,083).

## Leccion transversal a las tres vueltas

Las tres direcciones probadas fueron variantes de **anadir** al prompt de haiku: mas procedimiento (v1), mas exigencia de forma (v2), mas prohibicion (v3). Las tres empeoraron control. Ninguna direccion de "anadir" ha funcionado; queda sin probar "recortar" y, sobre todo, queda sin descartar que el propio evaluador `recall_revisor` (emparejamiento por subcadena literal contra el capitulo) este subcontando defectos que el revisor si detecta pero no cita de la forma exacta que el evaluador exige. El detalle esta en `optimizaciones/revisor-encargo/lecciones.md`.

## Invocaciones y presupuesto

- Gastadas: 38 de 60 (tope). No se agoto el tope; el cierre fue por estancamiento, no por presupuesto.
- Consultas al split de control: 4 (vuelta 0 y las tres vueltas propuestas). Con solo 4 consultas, cualquier lectura fina de la curva de control tiene poca base estadistica; el resultado que sostiene con mas confianza es la direccion (anadir empeora), no la magnitud exacta de cada caida.

## Estado del agente

- `revisor-encargo.md` restaurado a produccion y verificado por hash (`57ee40d452b63dc17b1ab982fb9dc18c054241d0`) tras cada vuelta, incluida esta ultima. El repositorio queda exactamente como estaba.

## Candidato

No hay candidato: ninguna variante supero la linea base. `optimizaciones/revisor-encargo-20260918-1600/mejor.md` sigue siendo una copia de `produccion.md`. No se publica nada en Langfuse con etiqueta `candidato` porque el motivo de cierre no fue METRICA_ALCANZADA.
