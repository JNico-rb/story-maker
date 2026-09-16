---
aprobada: false
titulo: ""
capitulos: 0                      # total de capítulos de la novela
arcos:
  - n: 1
    titulo: ""
    acto: planteamiento           # planteamiento | nudo | desenlace
    desde: 1                      # primer capítulo del arco
    hasta: 5                      # último capítulo del arco (hasta − desde + 1 ≤ formato.capitulos_por_arco)
    objetivo: ""                  # qué debe conseguir narrativamente este arco
    sucesos_clave: []             # 2–6 hechos que tienen que ocurrir dentro del arco; la escaleta de arco los asigna a capítulos
    hilos_abre: []                # nombres de hilos que este arco abre
    hilos_cierra: []              # nombres de hilos que este arco cierra
---

# Escaleta de alto nivel

Es el plan que aprueba el usuario y lo que queda inmutable. El detalle capítulo a capítulo va en `arcos/arco-AA.md`, uno por arco, generado al llegar a él. Con pocos capítulos hay un solo arco.

## Estructura
- **Planteamiento** (arcos …, capítulos …): qué se establece.
- **Nudo** (arcos …, capítulos …): qué se complica y cómo escala.
- **Desenlace** (arcos …, capítulos …): qué se resuelve y qué queda abierto a propósito.

## Arcos
Una sección por arco, en prosa breve, ampliando el frontmatter:

### Arco 1 — Título (capítulos desde–hasta)
Objetivo · sucesos clave · qué hilos abre y cierra · con qué situación termina.

## Hilos
Lista de todos los hilos narrativos de la novela. Para cada uno: nombre, arco donde se abre, arco donde se cierra o "queda abierto a propósito". Es contra lo que se mide `hilos_sin_cerrar` al final.

| Hilo | Se abre en | Se cierra en |
|---|---|---|
| | | |
