---
caso: ""                 # caso-NN-<slug>
fecha: ""
tipo: ""                 # modelo-caro-vs-barato | claude-code-vs-runner | otro
lado_a: "novelas/<slug-a>"
lado_b: "novelas/<slug-b>"
---

# Caso NN — <título>

## Idea
La idea literal con la que se generaron los dos lados (debe coincidir con `idea.md` de ambas carpetas).

## Qué se compara y por qué
Una o dos frases: qué decisión depende de este caso (p. ej. "si `haiku` con escalado aguanta el perfil `relato`, es la configuración del paso 2").

## Lados

| | A | B |
|---|---|---|
| Carpeta | `novelas/<slug-a>` | `novelas/<slug-b>` |
| Generado por | Claude Code / runner | Claude Code / runner |
| Qué difiere en `config.json` | (p. ej. `modelos.* = opus`, escalado off) | (p. ej. `modelos.* = haiku`, escalado on → opus) |

## Diferencias de entrevista
"Ninguna: se copió `entrevista.md` de A a B" o la lista de respuestas que cambiaron.
