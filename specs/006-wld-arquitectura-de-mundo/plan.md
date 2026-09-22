# 006 — WLD · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: eval del selector contra el catálogo de tropos, más inspección, clases T e I (`docs/verification.md` §5).

### Steps

- [ ] El orden de una `Consecuencia` se limita a 1.º, 2.º o 3.º (RF-WLD-7 · clase A)
- [ ] El catálogo de tropos existe curado desde la primera ejecución; sin él no se puede puntuar originalidad (RF-WLD-5)
- [ ] La biblioteca de canon guarda entidades, aristas y vigencias, nunca vectores (RF-WLD-10)
- [ ] El arquitecto recibe como restricción de entrada un techo de elementos estructurales inventables (RF-WLD-1)
- [ ] El arquitecto produce N candidatos de `Novum`, nunca uno solo (RF-WLD-2)
- [ ] El auditor de tropos puntúa el solapamiento de cada candidato con el `CatalogoDeTropos` (RF-WLD-3 · clases T e I)
- [ ] El selector puntúa cada candidato en derivabilidad, ajuste a los compromisos y distancia al catálogo, y elige por puntuación (RF-WLD-4)
- [ ] Las consecuencias se derivan hasta que no queda ninguna huérfana: toda `Consecuencia` es alcanzable desde al menos un `Novum` (RF-WLD-6)
- [ ] Al cerrar la fase, el arquitecto escribe el canon inicial y su índice en la misma transacción (RF-WLD-8)
- [ ] Una ejecución que entrega manuscrito promueve su canon a la biblioteca como versión nueva que apunta a la anterior; ninguna versión se sobrescribe (RF-WLD-11)
- [ ] El arquitecto admite el modo «reutilizar canon», que parte de un storyworld de la biblioteca en vez de inventarlo (RF-WLD-9 · deseable)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
