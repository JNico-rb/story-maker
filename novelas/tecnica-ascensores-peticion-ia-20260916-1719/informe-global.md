---
capitulo: "global"
intento: –
origen: revisores
base: manuscrito
veredicto: APROBADO
veredicto_encargo: null
veredicto_continuidad: APROBADO
problemas: []
observaciones:
  - "El manuscrito no marca explícitamente los días transcurridos entre capítulos, pero la escaleta promete '5 días' sin fijar fechas concretas en la biblia. La ventana de 48-72 horas en el cap. 5 es consistente con una semana de acción."
  - "Brecha narrativa menor: Cap. 4 muestra que Marisa envía imágenes ('las imágenes que había tomado') a Marcel, pero Caps. 2-3 no describen explícitamente cuándo las tomó. El texto no lo prohíbe (ella porta teléfono en Cap. 4), solo no lo muestra. No es contradicción con canon o estado, es compresión narrativa."
  - "Todos los hilos cerrados en escaleta están cerrados. Los abiertos a propósito ('¿Caerá el ascensor?', '¿Funcionará la reparación?', etc.) quedan intencionalmente abiertos según la premisa de desenlace abierto en Cap. 5."
  - "Coherencia interna total en personajes, reglas del mundo, estructura de edificio, y timeline de corrosión (0,3% por 24h antes del punto de no retorno)."
---

# Informe global de continuidad

**Veredicto: APROBADO** — informativo. La revisión global no reescribe nada; su valor es señalar lo que no se ve capítulo a capítulo.

Base: `manuscrito.md` completo (6.426 palabras, por debajo de `limites.revision_global_max_palabras` = 60.000), junto con la biblia, la escaleta, el libro de estado final y los cinco resúmenes aprobados. Revisor: continuidad, modo global.

## Problemas
- Ninguno de gravedad 1 ni 5.

## Observaciones
1. El manuscrito no marca explícitamente los días transcurridos entre capítulos. La escaleta promete «5 días» sin fijar fechas concretas en la biblia, y la ventana de 48–72 horas del capítulo 5 es consistente con una semana de acción.
2. Brecha narrativa menor: el capítulo 4 da por hecho que Marisa tiene imágenes del cable («las imágenes que había tomado»), pero los capítulos 2 y 3 no muestran cuándo las tomó. No contradice el canon ni el libro de estado; es compresión narrativa.
3. Todos los hilos que la escaleta manda cerrar están cerrados. Los que quedan abiertos —«¿caerá el ascensor?», «¿funcionará la reparación?»— lo están a propósito: la entrada 5 pide desenlace abierto.
4. Coherencia interna completa en personajes, reglas del mundo, estructura del edificio y cronología de la corrosión.

## Hilos de la escaleta

`escaleta.md` marca un único hilo con cierre previsto: **«La decisión final: ella actuará»**. Está cerrado en el capítulo 5. Los tres restantes (`hilos_abre` sin `hilos_cierra` correspondiente) quedan abiertos por diseño.

## Qué queda para el usuario

Nada obligatorio. Las observaciones 1 y 2 son huecos, no contradicciones: no se arreglan cambiando una línea, así que no entran en `erratas.md`. Si se quisieran cerrar, harían falta una o dos frases nuevas en los capítulos 2 o 3, y eso es reescribir un capítulo aprobado, cosa que el harness no hace.
