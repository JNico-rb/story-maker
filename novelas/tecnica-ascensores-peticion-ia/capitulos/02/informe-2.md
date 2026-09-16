---
capitulo: 2
intento: 2
origen: revisor
base: null
veredicto: APROBADO
veredicto_revisor: null
problemas:
  - gravedad: 5
    donde: "resumen-2.md, front-matter `hilos_abiertos`"
    que: "No se registra el hilo con el nombre canónico 'Reme y el vecindario'; su contenido queda disperso en dos etiquetas nuevas ('Pablo lo cuenta en el grupo del barrio', 'La junta del miércoles y la vecina del segundo'), lo que impide que el libro de estado enlace el hilo con su cierre previsto"
    por_que: "escaleta.md, tabla de Hilos: 'Reme y el vecindario | Arco 1 (cap. 2) | Arco 1 (cap. 5)'; y arcos/arco-01.md, entrada 2, suceso 'Pablo la oye hablando sola dentro de una cabina y lo comenta en el bloque; el rumor arranca'"
observaciones:
  - "El resumen, en 'Cambios en personajes' › Reme, califica de mentira la respuesta 'con el contacto de la segunda'; en el texto esa frase es literalmente veraz (Reme llevaba treinta minutos con el contacto de la segunda) y funciona como ambigüedad deliberada, no como mentira. La otra respuesta ('con nadie') sí lo es."
  - "Varias entradas de `hilos_abiertos` son sucesos del capítulo más que hilos ('La negativa de Reme a montar la pieza', 'El plano salido solo de la impresora térmica'); la lista crecerá mucho si se mantiene ese criterio."
  - "La escena del engrase de guías se cuenta desde dentro de la cabina; el detalle técnico no contradice nada de la biblia, pero es el único momento del capítulo donde el oficio se describe con menos precisión que el resto."
---

# Informe del capítulo 2 (intento 2)

**Veredicto: APROBADO** (0 problemas de gravedad 1–2, 1 de gravedad 3–5; regla: `rechaza_con_graves` = 1 / `rechaza_con_leves` = 2). El revisor propuso APROBADO y el recálculo del harness coincide.

El problema de gravedad 1 del intento anterior —los partes de Reme volcados al terminal, que contradecía que trabaje desconectada— queda corregido: el histórico de cinco años sale vacío y el texto subraya que lo hecho allí dentro solo está en su cuaderno de lápiz.

## Problemas

1. **[gravedad 5]** El front matter de `resumen-2.md` no usa el nombre canónico del hilo «Reme y el vecindario», que la escaleta abre en el capítulo 2 y cierra en el 5; su contenido queda repartido entre dos etiquetas nuevas, lo que dificulta enlazar el hilo con su cierre previsto. No afecta al texto del capítulo.

## Observaciones

- El resumen llama mentira a «con el contacto de la segunda», que en el texto es literalmente cierto y funciona como ambigüedad deliberada; «con nadie» sí lo es.
- Varias entradas de `hilos_abiertos` son sucesos del capítulo más que hilos; con ese criterio la lista crecerá mucho.
- La escena del engrase de guías es el punto del capítulo donde el oficio se describe con menos precisión.
