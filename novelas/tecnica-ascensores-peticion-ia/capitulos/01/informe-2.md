---
capitulo: 1
intento: 2
origen: revisor
base: null
veredicto: APROBADO
veredicto_revisor: null
problemas:
  - gravedad: 5
    donde: "resumen-2.md, sección 'Elementos introducidos' ('El fusible de cristal de veinte milímetros... en el bolsillo de Reme desde este capítulo, junto con los dos tornillos de la placa') y 'Cambios en personajes' › Remedios ('Tiene ahora el fusible y los dos tornillos en el bolsillo')"
    que: "El resumen registra como estado final que Reme conserva en el bolsillo los dos tornillos de la placa del altavoz, además del fusible"
    por_que: "El capítulo dice lo contrario: tras retirar el fusible, 'Volvió a poner la placa. Apretó los dos tornillos'. Solo el fusible queda en el bolsillo. Al ser un elemento que el libro de estado arrastrará a capítulos siguientes, el inventario de objetos queda mal fijado (criterio 5: estado de personajes y elementos incorrectos)"
observaciones:
  - "En el hecho 9 del resumen se altera el orden del diálogo: sitúa el 'Correcto' de la voz después de la réplica de Reme sobre los veintiséis años, cuando en el capítulo es anterior y es justamente lo que provoca esa réplica ('No, correcto no.'). No cambia los hechos, pero desdibuja la causalidad de la escena."
  - "El campo 'estado' de Remedios en el frontmatter empieza por 'En su casa al final del capítulo', cuando la última posición real al cerrar el capítulo es dentro de la Schindler del 12 de Miguel Servet, dos días después. La frase aclara después el salto, pero el orden invita a confusión."
  - "La voz de Pablo aquí es más lacónica que el perfil de la biblia ('rápida, con muletillas, pregunta tres veces lo mismo'): apenas hay muletillas y abundan los monosílabos. El texto lo compensa señalando que siete segundos callado 'para él era un récord', así que no lo considero ruptura, pero conviene recuperar ese registro en el capítulo 2."
  - "Las intervenciones de la voz son de una o dos palabras ('Mantenimiento.', 'Correcto.'), por debajo del rango 'de tres a nueve palabras' de la biblia; la propia biblia ejemplifica con 'Recibido.', de modo que la desviación es admisible, pero el margen está en el límite inferior."
  - "Errata de puntuación en el diálogo de la calle: '—¿Qué.' sin signo de cierre de interrogación."
  - "Los hilos del resumen se nombran de forma distinta a los de la escaleta ('La voz que llama a Remedios Alcaraz' frente a 'La petición de la voz'; 'Pablo como aprendiz y la prueba que no le dejan hacer' frente a 'Pablo, el aprendiz que no quiere'). No es un error de contenido, pero dificultará el seguimiento de cierres en el libro de estado si la divergencia se mantiene."
---

# Informe del capítulo 1 (intento 2)

**Veredicto: APROBADO** (0 problemas de gravedad 1–2, 1 de gravedad 3–5; regla: `veredicto.rechaza_con_graves` = 1 / `rechaza_con_leves` = 2). El veredicto del revisor coincide con el recalculado por el harness.

Los tres problemas del intento 1 quedan corregidos: la antigüedad de Reme es ahora coherente («de este aparato llevo yo veintiséis años»), el narrador no vuelve a entrar en la cabeza de Pablo, y el texto retira «Esto no es mío» y «Trabajo correcto», reservados para los capítulos 2 y 4.

## Problemas

1. **[gravedad 5]** `resumen-2.md`, «Elementos introducidos» y «Cambios en personajes» — el resumen dice que Reme se queda con el fusible **y los dos tornillos** en el bolsillo. El capítulo dice que volvió a poner la placa y apretó los dos tornillos: solo el fusible queda en el bolsillo. El libro de estado arrastra ese inventario a los capítulos siguientes, así que queda anotado aquí.

## Observaciones

- El hecho 9 del resumen invierte el orden del diálogo: el «Correcto» de la voz es anterior a la réplica de Reme, y es lo que la provoca.
- El frontmatter sitúa a Reme «en su casa al final del capítulo» cuando su última posición real es dentro de la Schindler de Miguel Servet, dos días después.
- La voz de Pablo es más lacónica que el perfil de la biblia (rápida, con muletillas). No es ruptura; conviene recuperar el registro en el capítulo 2.
- Las frases de la voz están en el límite inferior del rango de 3–9 palabras de la biblia.
- Errata: «—¿Qué.» sin signo de cierre de interrogación.
- Los hilos del resumen no usan los nombres de la escaleta; si la divergencia se mantiene, dificultará seguir los cierres en el libro de estado.
