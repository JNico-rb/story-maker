---
validada: false
arco: 1
desde: 1
hasta: 5
entradas:
  - n: 1
    titulo: ""                    # provisional
    objetivo: ""                  # qué debe conseguir narrativamente este capítulo
    sucesos: []                   # 2–5 hechos clave que ocurren; los sucesos_clave del arco deben aparecer repartidos aquí
    personajes: []                # quiénes aparecen
    gancho: ""                    # cómo termina, qué deja abierto
    palabras_objetivo: 1500       # entre formato.palabras_min_capitulo y palabras_max_capitulo
---

# Escaleta del arco A — Título (capítulos desde–hasta)

Detalle capítulo a capítulo del arco. Se genera al llegar al arco, con el libro de estado y el informe del arco anterior como entrada, y la valida el harness sin intervención del usuario. Una vez validada es inmutable.

## Qué recoge del arco anterior
Lo que el informe del arco anterior dejó pendiente y cómo se compensa aquí. "Nada" si es el primer arco.

## Capítulos
Una sección por capítulo, en prosa breve, ampliando el frontmatter:

### 1. Título
Objetivo · sucesos · personajes · gancho · palabras.
