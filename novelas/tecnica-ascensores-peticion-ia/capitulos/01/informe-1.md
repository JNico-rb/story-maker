---
capitulo: 1
intento: 1
origen: revisor
base: null
veredicto: RECHAZADO
veredicto_revisor: null
problemas:
  - gravedad: 1
    donde: "párrafo 1 ('Reme lo había desmontado cuatro veces en veintiséis años') y diálogo en cabina ('Mantenimiento de este aparato soy yo desde el noventa y ocho. No hay otro.')"
    que: "Las dos cifras de antigüedad son incompatibles entre sí y con la edad de la protagonista: en 2049, llevar el 38 'desde el noventa y ocho' son 51 años de servicio, lo que situaría a Reme empezando el oficio con un año de edad; el mismo capítulo dice 'veintiséis años'"
    por_que: "biblia, Personajes › Remedios 'Reme' Alcaraz Vidal: 'cincuenta y dos años, técnica de mantenimiento de ascensores'; y biblia, El mundo: 'Corre el otoño de 2049'. Con 52 años en 2049 (nacida en 1997) no puede haber asumido el mantenimiento del 38 en 1998. El resumen propaga el error en 'Cambios en personajes' ('veintiséis años de oficio; lleva el mantenimiento del 38 desde 1998')"
  - gravedad: 4
    donde: "párrafo que empieza 'Tardaron hora y media': 'Pablo aprendió lo que se aprende mirando, que es más de lo que él creía y menos de lo que ella decía'"
    que: "El narrador informa de lo que Pablo creía y de lo que Pablo aprendió, contenidos a los que Reme no tiene acceso"
    por_que: "biblia, Tono y voz › Punto de vista: 'tercera persona limitada, pegada a Reme Alcaraz... No se sale nunca de su cabeza: lo que ella no ve, no se cuenta'"
  - gravedad: 5
    donde: "cabecera YAML del resumen, campo 'hilos_abiertos'"
    que: "Los hilos abiertos no se corresponden con los nombres fijados por la escaleta y falta uno que debía abrirse en este capítulo: aparecen 'La voz que dice llamarse Mantenimiento', 'Reme oculta el contacto', 'La sexta parada que Pablo contó' y 'Julia Bandrés, la maestra ausente', pero no figura 'Pablo, el aprendiz que no quiere', y 'La petición de la voz' aparece renombrado"
    por_que: "escaleta de alto nivel, tabla de Hilos: 'La petición de la voz | Arco 1 (cap. 1)', 'Pablo, el aprendiz que no quiere | Arco 1 (cap. 1)', 'La herencia de Julia Bandrés | Arco 1 (cap. 1)'. El material del capítulo sí abre el hilo de Pablo (se le niega probar el aparato dos semanas seguidas y calla ante la discrepancia de las paradas), pero el resumen no lo registra con el nombre que el libro de estado y los arcos deben rastrear"
observaciones:
  - "Reme dice 'Esto no es mío' en la cabina del 38. La escaleta del arco reserva esa frase literal para el rechazo de la petición en el capítulo 2 ('Reme dice que no, en voz alta y con las manos ocupadas: \"esto no es mío\"'). Aquí no adelanta ningún suceso, porque todavía no hay petición, pero gasta la línea que debía marcar el no del capítulo siguiente."
  - "'Trabajo correcto' roza el arco de la voz, cuyo cierre es 'haber entregado lo único que podía entregar: el reconocimiento del trabajo de Reme'. En este capítulo funciona como frase de registro técnico y no lo considero adelanto, pero conviene no repetir el gesto hasta el capítulo 4."
  - "El capítulo fija 'El cuaderno era de papel y el lápiz era un lápiz' y 'nada de asistente en la furgoneta'. El gancho previsto para el capítulo 2 es una impresora térmica del cuaderno de partes en la furgoneta: habrá que resolver la fricción ahí, no aquí."
---

# Informe del capítulo 1 (intento 1)

**Veredicto: RECHAZADO** (1 problema de gravedad 1–2, 2 de gravedad 3–5; regla: `veredicto.rechaza_con_graves` = 1 / `rechaza_con_leves` = 2). El veredicto del revisor coincide con el recalculado por el harness.

## Problemas

1. **[gravedad 1]** Párrafo 1 y diálogo en cabina — las cifras de antigüedad de Reme se contradicen entre sí y con la biblia. El texto dice «veintiséis años» de oficio y, poco después, que lleva el mantenimiento del 38 «desde el noventa y ocho», que en 2049 serían cincuenta y un años: Reme habría empezado con un año de edad. Choca con la biblia, que la fija en cincuenta y dos años en el otoño de 2049. El resumen arrastra el error.

2. **[gravedad 4]** Párrafo «Tardaron hora y media» — el narrador entra en la cabeza de Pablo («más de lo que él creía»), contenido al que Reme no tiene acceso. La biblia impone tercera persona limitada pegada a Reme, sin salir nunca de su cabeza.

3. **[gravedad 5]** Frontmatter del resumen, campo `hilos_abiertos` — los hilos registrados no usan los nombres que fija la tabla de Hilos de la escaleta y falta «Pablo, el aprendiz que no quiere», que el capítulo sí abre en el texto. El libro de estado necesita rastrearlos con el nombre canónico.

## Observaciones

- «Esto no es mío» aparece aquí; la escaleta reserva esa frase literal para el rechazo de la petición en el capítulo 2. No es adelanto de suceso, pero gasta la línea.
- «Trabajo correcto» roza el cierre del arco de la voz (el reconocimiento del trabajo, previsto para el capítulo 4). Aquí pasa como frase de registro; conviene no repetir el gesto hasta entonces.
- El capítulo fija que Reme trabaja con cuaderno de papel y sin asistente en la furgoneta. El gancho del capítulo 2 es una impresora térmica del cuaderno de partes: la fricción se resuelve allí, no aquí.
