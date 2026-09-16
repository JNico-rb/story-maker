---
caso: ""                 # caso-NN-<slug>
fecha: ""
tipo: ""                 # modelo-caro-vs-barato | claude-code-vs-runner | otro
referencia: "pruebas/referencia"
lado_a: "novelas/<slug-a>"
lado_b: "novelas/<slug-b>"
---

# Caso NN — <título>

## Qué se compara y por qué
Una o dos frases: qué decisión depende de este caso (p. ej. "si `haiku` con escalado pasa los umbrales de `calidad` en el perfil `relato`, es la configuración del paso 2").

## Lados

| | A | B |
|---|---|---|
| Carpeta | `novelas/<slug-a>` | `novelas/<slug-b>` |
| Generado por | Claude Code / runner | Claude Code / runner |
| Qué difiere en `config.json` | (p. ej. `modelos.* = opus`, escalado off) | (p. ej. `modelos.* = haiku`, escalado on → opus) |

## Diferencias respecto al caso de referencia
"Ninguna" o la lista. Cualquier diferencia de idea o entrevista invalida el caso.
