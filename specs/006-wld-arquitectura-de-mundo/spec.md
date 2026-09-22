# 006 — WLD · Arquitectura de mundo

- [ ] Spec approved   <- only the user marks this

## Objetivo

Inventar un mundo derivable de un novum y no trillado.

## Alcance

Arquitectura de mundo: candidatos de `Novum`, selección por puntuación, derivación de consecuencias, canon inicial, y promoción del canon a la biblioteca al terminar.

**Fuera de alcance:** la promoción de canon a la biblioteca **al cancelar**. Depende del diseño de orquestación, declarado sin escribir (`architecture.md` §12.1). Promover al terminar bien sí entra en V1 (RF-WLD-11).

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-WLD-1 | El arquitecto recibe como restricción de entrada un techo de elementos estructurales inventables | Obligatorio | T |
| RF-WLD-2 | El arquitecto produce N candidatos de `Novum`, nunca uno solo | Obligatorio | T |
| RF-WLD-3 | El auditor de tropos puntúa el solapamiento de cada candidato con el `CatalogoDeTropos` | Obligatorio | T, I |
| RF-WLD-4 | El selector puntúa cada candidato en derivabilidad, ajuste a los compromisos y distancia al catálogo, y elige por puntuación | Obligatorio | T |
| RF-WLD-5 | El catálogo de tropos existe curado desde la primera ejecución; sin él no se puede puntuar originalidad | Obligatorio | T |
| RF-WLD-6 | Las consecuencias se derivan hasta que no queda ninguna huérfana: toda `Consecuencia` es alcanzable desde al menos un `Novum` | Obligatorio | T |
| RF-WLD-7 | El orden de una `Consecuencia` se limita a 1.º, 2.º o 3.º | Obligatorio | A |
| RF-WLD-8 | Al cerrar la fase, el arquitecto escribe el canon inicial y su índice en la misma transacción | Obligatorio | T |
| RF-WLD-9 | El arquitecto admite el modo «reutilizar canon», que parte de un storyworld de la biblioteca en vez de inventarlo | Deseable | T |
| RF-WLD-10 | La biblioteca de canon guarda entidades, aristas y vigencias, nunca vectores | Obligatorio | T |
| RF-WLD-11 | Una ejecución que termina y entrega manuscrito promueve su canon a la biblioteca como versión nueva que apunta a la anterior. Ninguna versión se sobrescribe | Obligatorio | T |

## Docs de referencia

`architecture.md` §6.3, §8.3, §8.6, §9.5; `domain-knowledge.md` §2, §3
