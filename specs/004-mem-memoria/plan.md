# 004 — MEM · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: pruebas doradas, clase T (`docs/verification.md` §5).

Determinista de principio a fin: ningún paso de este plan llama a un modelo de lenguaje. Sus pruebas corren sobre un índice de fixture con vectores almacenados; la cuota entra como dato del caso y los costes en tokens los declara el propio caso.

### Steps

**Escritura**

- [ ] Solo el arquitecto de mundo en la fase 1 y el registrador de estado en la fase 3 escriben en el índice (RF-MEM-7 · clase A)
- [ ] Cada entidad del canon inicial produce una `CanonCard` con `desde_escena` = 1 y `hasta_escena` abierto, consultable de inmediato (RF-MEM-1)
- [ ] Un cambio en una entidad cierra la tarjeta vigente y añade otra: el índice es append-only, sin `UPDATE` ni `DELETE` (RF-MEM-4)
- [ ] Al aceptar una escena, su delta se indexa en la misma transacción que el canon: no hay instante observable en que canon e índice discrepen (RF-MEM-2)
- [ ] Una escena rechazada no deja rastro: el índice queda idéntico al anterior a generarla (RF-MEM-3)
- [ ] Aceptar una escena escribe su resumen y una fila por párrafo, cada una con su escena y su capítulo (RF-MEM-5)
- [ ] Un vector almacenado nunca se recalcula (RF-MEM-6)
- [ ] El índice es función pura del canon aceptado: reconstruirlo desde el canon produce el mismo contenido (RF-MEM-8)

**Residentes y proyección**

- [ ] Los residentes no se indexan nunca (RF-MEM-10 · clase A)
- [ ] La ventana lleva siempre los residentes que existan: proyección del outline, `EstadoDelMundo`, `ResumenRodante`, `StyleSheet`, compromisos inviolables y `CatalogoDeTropos` (RF-MEM-9)
- [ ] La proyección del outline contiene los capitulares de toda la obra, las escenas del capítulo actual y la lista explícita de lo que aún no puede revelarse (RF-MEM-11)
- [ ] La proyección no contiene las escenas de otros capítulos, ni siquiera resumidas (RF-MEM-12)
- [ ] La lista de lo no revelable nombra los hechos de outline posteriores a la escena actual, sin exponer su contenido (RF-MEM-13)
- [ ] Una escena que no existe en el outline produce ventana sin proyección de capítulo, con causa raíz `contexto ausente`, sin bloquear (RF-MEM-14)

**Consultas y recuperación**

- [ ] No existe re-ranking por modelo en ninguna colección (RF-MEM-22 · clase A)
- [ ] El corte temporal filtra antes de puntuar: para la escena *n* solo son candidatas las unidades con `desde_escena` ≤ *n* < `hasta_escena` (RF-MEM-18)
- [ ] Cada colección se puntúa por separado: ningún ranking mezcla unidades de dos colecciones (RF-MEM-19)
- [ ] `CanonCards` y resúmenes se recuperan por canal léxico y canal denso, fundidos por rango recíproco dentro de la colección (RF-MEM-20)
- [ ] La prosa se recupera solo por canal léxico, sin incrustaciones, y su unidad es el párrafo (RF-MEM-21)
- [ ] Los empates se desempatan por identificador, de forma estable entre ejecuciones (RF-MEM-23)
- [ ] El escritor consulta de forma prospectiva, desde la entrada de outline de la escena que va a escribir (RF-MEM-15)
- [ ] El crítico de canon consulta de forma retrospectiva, desde el texto que el escritor acaba de producir (RF-MEM-16)
- [ ] Las dos consultas sobre la misma escena son distintas; ninguna reutiliza la otra (RF-MEM-17)
- [ ] Una `Consecuencia` recuperada arrastra sus ancestros hasta el `Novum` como enunciado de una línea, sin consumir cuota y sin entrar como tarjeta completa (RF-MEM-24)
- [ ] Un resumen recuperado arrastra el anterior y el siguiente, y consume tres plazas (RF-MEM-25)
- [ ] El arrastre temporal respeta el corte: no arrastra resúmenes de escenas posteriores a la actual (RF-MEM-26)
- [ ] Recuperación vacía o escasa no bloquea: se genera con lo que haya y se registra causa raíz `contexto ausente` (RF-MEM-27)

**Cuotas, ensamblado y tope**

- [ ] El guardián de presupuesto lo invoca el código, nunca el modelo: el agente no ve su presupuesto ni decide qué pedir (RF-MEM-34 · clase A)
- [ ] Cada par (colección, consumidor) entrega como mucho sus plazas; el sobrante se registra como negado (RF-MEM-28)
- [ ] Las plazas sobrantes no se prestan entre colecciones (RF-MEM-29)
- [ ] Con cuota 0, esa colección no se consulta ni aparece en la ventana de ese consumidor (RF-MEM-30)
- [ ] El escritor nunca recibe prosa recuperada; el crítico de oficio sí (RF-MEM-31)
- [ ] El orden de las piezas en la ventana es declarado y estable: mismas entradas, misma ventana, pieza por pieza (RF-MEM-32)
- [ ] El conteo de entrada usa el tokenizador del modelo congelado al crear la ejecución (RF-MEM-40)
- [ ] La cuota de entrada de la etapa la calcula el orquestador dividiendo el techo entre las llamadas realmente en vuelo (RF-MEM-33)
- [ ] Lo ensamblado nunca supera la cuota de entrada de la etapa (RF-MEM-35)
- [ ] Si no cabe, se recorta en el orden declarado —prosa, resúmenes de escena, `CanonCards`, `ResumenRodante`— y dentro de cada colección por rango inverso (RF-MEM-36)
- [ ] Residentes y arrastres no se recortan, salvo el `ResumenRodante`, que es la última válvula (RF-MEM-37)
- [ ] Si lo intocable ya supera la cuota, se recorta el `ResumenRodante` y se entrega igual, con causa raíz `contexto ausente`, sin bloquear (RF-MEM-38)
- [ ] Lo negado se descuenta antes de cerrar la ventana y no llega al consumidor de ninguna forma (RF-MEM-39)
- [ ] Deriva de conteo por encima de `umbral_deriva_conteo` anota causa raíz `presupuesto excedido`, que no bloquea ni reintenta (RF-MEM-41 · deseable)

**Trazabilidad y determinismo**

- [ ] La ventana registra qué entró y qué quedó fuera: identificador de cada residente y de cada unidad recuperada, más los negados con su motivo —cuota o recorte— (RF-MEM-42)
- [ ] Todo fragmento generado registra las `CanonCard` que lo justificaron, derivadas de la ventana con la que se generó (RF-MEM-43)
- [ ] Con el mismo índice, la misma configuración y la misma escena, la ventana es idéntica pieza por pieza, sin ninguna llamada a modelo (RNF-1)
- [ ] Una ejecución cuyo modelo de incrustación ya no exista no se reanuda sin reconstruir el índice (RNF-2)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
