---
hasta_capitulo: 0         # último capítulo aprobado que refleja este libro
---

# Libro de estado

La memoria de la novela: cómo están las cosas **después del último capítulo aprobado**. Lo propone el resumidor en cada intento (`capitulos/NN/libro-estado-K.md`) y el harness lo adopta al aprobar. Siempre completo: cada versión sustituye a la anterior. Tamaño orientativo: `memoria.libro_estado_max_palabras`; para no crecer, se condensan las entradas cerradas, nunca se borran hechos.

## Personajes
Una entrada por personaje que ha aparecido. Solo estado actual, no historia.

## Hilos abiertos
| Hilo | Abierto en | Cierre previsto (según escaleta) | Estado actual |
|---|---|---|---|

## Hilos cerrados
| Hilo | Abierto en | Cerrado en | Cómo |
|---|---|---|---|

## Elementos
Objetos, lugares y datos introducidos que condicionan el futuro: qué es, dónde está o quién lo tiene, desde qué capítulo.

## Reglas en vigor
Las reglas inviolables de la biblia tal como se han concretado en el texto, más cualquier regla o excepción que la novela haya establecido después, con el capítulo donde quedó fijada.
