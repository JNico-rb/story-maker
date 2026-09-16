---
capitulo: 2
intento: 1
origen: revisor
base: null
veredicto: RECHAZADO
veredicto_revisor: null
problemas:
  - gravedad: 1
    donde: "párrafo del punto de servicio: 'una lista larga de partes que había metido ella misma, todos a lápiz primero y al terminal después, uno por año'"
    que: "Se establece que Reme vuelca sus partes en el terminal del sistema, es decir, que su registro de trabajo existe dentro de la red consultable"
    por_que: "libro de estado, Reglas en vigor: 'Reme trabaja deliberadamente desconectada: sin asistente, sin partes en la nube, sin consultar al sistema dónde hay una pieza; papel, lápiz e impresora térmica (cap. 1)'. También choca con la biblia, Decisiones del interrogador: la voz la elige porque 'Reme es de las poquísimas personas del distrito que nunca ha pedido nada al sistema: no tiene historial'"
  - gravedad: 5
    donde: "resumen-1.md, bloque 'hilos_abiertos' del front matter"
    que: "Desaparece el hilo 'La junta del miércoles y la vecina del segundo', abierto en el capítulo 1 y no cerrado, justo en el capítulo en el que la vecina del segundo entra en escena con la bolsa de la analítica; en su lugar se añade 'La vecina del segundo' solo como personaje"
    por_que: "libro de estado, tabla de Hilos abiertos: 'La junta del miércoles y la vecina del segundo | cap. 1 | no consta'. El resumen debe arrastrar los hilos abiertos que el capítulo no cierra; sí arrastra correctamente 'Julia Bandrés' y 'La petición de que Reme enseñe', pero pierde este"
  - gravedad: 5
    donde: "resumen-1.md, 'hilos_cerrados: - La comprobación del histórico de avisos'"
    que: "Se declara cerrado un hilo que nunca estuvo abierto: no figura en el libro de estado ni en el resumen del capítulo 1; es una acción interna de este capítulo, no un hilo de la novela"
    por_que: "libro de estado, tablas de Hilos abiertos y Hilos cerrados: el único hilo cerrado registrado es 'Sustitución del limitador de velocidad del nº 38'. Clasificar como hilo cerrado un suceso que no se abrió previamente corrompe la contabilidad de hilos que hereda el capítulo 3"
observaciones:
  - "La consola del punto de servicio interviene con guion de diálogo ('—¿Quiere una copia impresa? —dijo la pantalla'). El texto se cubre expresamente ('en letras, porque aquella consola no tenía voz'), de modo que no cuenta como ruptura de la regla inviolable 3, pero es el único punto del capítulo donde una máquina participa en un diálogo fuera de una cabina."
  - "La nota del plano, 'acero, sin electrónica', y la mención de 'una palanca larga' entregan ya al lector dos de los tres rasgos que la escaleta reserva al capítulo 3 ('palanca puramente mecánica, sin electrónica'). No se considera adelanto porque el acto dramático del capítulo 3 —que Reme descifre el plano y entienda que es un freno que corta la tracción de un tramo— no ocurre aquí: ella declara no haber visto la pieza nunca."
  - "Deslices de tiempo verbal hacia el presente en la voz narrativa ('Los papeles se piden en el punto de servicio…', 'una consola de consulta que lleva allí desde que Reme tiene furgoneta'), frente a la biblia, Tono y voz: 'tercera persona limitada, pegada a Reme Alcaraz, en pasado'. Son presentes habituales integrados en el estilo indirecto libre y no rompen el punto de vista, pero destacan sobre el resto del capítulo."
  - "Ambigüedad técnica al abrir: Reme tiene 'la mano dentro del cuadro de la Schindler' y a la vez la cabina se desplaza con ella dentro hasta el bajo. Por el léxico del oficio, 'cuadro' remite al cuadro de maniobra del cuarto de máquinas; el texto aclara después que está en la cabina, pero la primera lectura chirría."
  - "La escaleta del arco dice 'ni ningún técnico asignado a esas cabinas' y el capítulo lo resuelve como 'Técnico asignado: Alcaraz Vidal, R. Único'. La variación sirve mejor al objetivo de la entrada y no cuenta como incumplimiento."
  - "'Ese vacío con cuerpo' y 'aquello callaba teniendo' rozan lo que la biblia pide evitar (metáforas sobre almas y conciencias, frases sentenciosas); están dentro de la cabeza de Reme y no obligan a reescribir."
---

# Informe del capítulo 2 (intento 1)

**Veredicto: RECHAZADO** (1 problema de gravedad 1–2, 2 de gravedad 3–5; regla: `rechaza_con_graves` = 1 / `rechaza_con_leves` = 2). El revisor propuso RECHAZADO y el recálculo del harness coincide.

## Problemas

1. **[gravedad 1]** En el párrafo del punto de servicio, al listar el histórico de cinco años, el texto dice que los partes los había metido Reme «todos a lápiz primero y al terminal después, uno por año». Eso contradice una regla en vigor del libro de estado y una decisión de la biblia: Reme trabaja deliberadamente desconectada —papel, lápiz e impresora térmica, sin partes en la nube— y precisamente por no tener historial en el sistema es a quien la voz elige. Si sus partes están en el terminal, se cae el motivo por el que la eligen.

2. **[gravedad 5]** El front matter de `resumen-1.md` pierde el hilo «La junta del miércoles y la vecina del segundo», abierto en el capítulo 1 y no cerrado aquí, justo en el capítulo donde esa vecina entra en escena. El resumen debe arrastrar todos los hilos abiertos que el capítulo no cierra.

3. **[gravedad 5]** El mismo front matter declara cerrado «La comprobación del histórico de avisos», que nunca estuvo abierto como hilo: es una acción interna del capítulo. Contabilizarla como hilo cerrado corrompe el recuento que hereda el capítulo 3.

## Observaciones

- La consola del punto de servicio interviene con guion de diálogo, aunque el texto aclara que contesta en letras y no tiene voz; es el único punto del capítulo donde una máquina dialoga fuera de una cabina.
- «Acero, sin electrónica» y «una palanca larga» adelantan dos rasgos que la escaleta reserva al capítulo 3, pero no el acto dramático de descifrar el plano, que sigue pendiente.
- Deslices al presente en la voz narrativa («Los papeles se piden…»), frente al pasado que fija la biblia.
- «La mano dentro del cuadro» de una cabina en movimiento chirría en primera lectura por el léxico del oficio.
- La escaleta dice «ningún técnico asignado» y el capítulo lo resuelve como «Alcaraz Vidal, R. Único»: variación admisible.
- «Ese vacío con cuerpo» y «aquello callaba teniendo» rozan lo sentencioso, dentro de la cabeza de Reme.
