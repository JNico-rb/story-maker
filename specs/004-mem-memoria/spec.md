# 004 — MEM · Memoria de la ejecución

- [ ] Spec approved   <- only the user marks this

## Objetivo

Escribir el índice de la ejecución y ensamblar la `VentanaDeContexto` de cada consumidor en cada escena. Todo el módulo es determinista y no llama a ningún modelo de lenguaje.

## Alcance

Índice híbrido, recuperación determinista y ensamblado de la `VentanaDeContexto`: escritura del índice, proyección, consultas, recuperación, cuotas, recorte y trazabilidad.

**Fuera de alcance:** el re-ranking de la recuperación y la expansión de consulta. Cuestan el determinismo que mantiene la memoria en clase T.

## Requisitos

### Escritura

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-1 | Cada entidad del canon inicial produce una `CanonCard` con `desde_escena` = 1 y `hasta_escena` abierto, consultable de inmediato | Obligatorio | T |
| RF-MEM-2 | Al aceptar una escena, su delta se indexa en la misma transacción que el canon. No existe instante observable en que canon e índice discrepen | Obligatorio | T |
| RF-MEM-3 | Una escena rechazada no deja rastro: el índice queda idéntico al anterior a generarla | Obligatorio | T |
| RF-MEM-4 | Un cambio en una entidad cierra la tarjeta vigente y añade otra. Ninguna tarjeta se modifica ni se borra: el índice es append-only | Obligatorio | T |
| RF-MEM-5 | Aceptar una escena escribe su resumen y una fila por párrafo, cada una con su escena y su capítulo | Obligatorio | T |
| RF-MEM-6 | Un vector almacenado nunca se recalcula | Obligatorio | T |
| RF-MEM-7 | Solo dos componentes escriben en el índice: el arquitecto de mundo en la fase 1 y el registrador de estado en la fase 3 | Obligatorio | A |
| RF-MEM-8 | El índice es función pura del canon aceptado: reconstruirlo desde el canon produce el mismo contenido | Obligatorio | T |

### Residentes y proyección

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-9 | La ventana lleva siempre los residentes que existan: proyección del outline, `EstadoDelMundo`, `ResumenRodante`, `StyleSheet`, compromisos inviolables y `CatalogoDeTropos` | Obligatorio | T |
| RF-MEM-10 | Los residentes no se indexan nunca | Obligatorio | A |
| RF-MEM-11 | La proyección del outline contiene los capitulares de toda la obra, las escenas del capítulo actual y la lista explícita de lo que aún no puede revelarse | Obligatorio | T |
| RF-MEM-12 | La proyección no contiene las escenas de otros capítulos, ni siquiera resumidas | Obligatorio | T |
| RF-MEM-13 | La lista de lo no revelable nombra los hechos de outline posteriores a la escena actual, sin exponer su contenido | Obligatorio | T |
| RF-MEM-14 | Una escena que no existe en el outline produce ventana sin proyección de capítulo, con causa raíz `contexto ausente`, sin bloquear | Obligatorio | T |

### Consultas y recuperación

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-15 | El escritor consulta de forma prospectiva, desde la entrada de outline de la escena que va a escribir | Obligatorio | T |
| RF-MEM-16 | El crítico de canon consulta de forma retrospectiva, desde el texto que el escritor acaba de producir | Obligatorio | T |
| RF-MEM-17 | Las dos consultas sobre la misma escena son distintas; ninguna reutiliza la otra | Obligatorio | T |
| RF-MEM-18 | El corte temporal filtra antes de puntuar: para la escena *n* solo son candidatas las unidades con `desde_escena` ≤ *n* < `hasta_escena` | Obligatorio | T |
| RF-MEM-19 | Cada colección se puntúa por separado. Ningún ranking mezcla unidades de dos colecciones | Obligatorio | T |
| RF-MEM-20 | `CanonCards` y resúmenes se recuperan por canal léxico y canal denso, fundidos por rango recíproco dentro de la colección | Obligatorio | T |
| RF-MEM-21 | La prosa se recupera solo por canal léxico, sin incrustaciones, y su unidad es el párrafo | Obligatorio | T |
| RF-MEM-22 | No existe re-ranking por modelo en ninguna colección | Obligatorio | A |
| RF-MEM-23 | Los empates se desempatan por identificador, de forma estable entre ejecuciones | Obligatorio | T |
| RF-MEM-24 | Una `Consecuencia` recuperada arrastra sus ancestros hasta el `Novum` como enunciado de una línea, sin consumir cuota y sin entrar como tarjeta completa | Obligatorio | T |
| RF-MEM-25 | Un resumen recuperado arrastra el anterior y el siguiente, y consume tres plazas | Obligatorio | T |
| RF-MEM-26 | El arrastre temporal respeta el corte: no arrastra resúmenes de escenas posteriores a la actual | Obligatorio | T |
| RF-MEM-27 | Recuperación vacía o escasa no bloquea: se genera con lo que haya y se registra causa raíz `contexto ausente` | Obligatorio | T |

### Cuotas, ensamblado y tope

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-28 | Cada par (colección, consumidor) entrega como mucho sus plazas; el sobrante se registra como negado | Obligatorio | T |
| RF-MEM-29 | Las plazas sobrantes no se prestan entre colecciones | Obligatorio | T |
| RF-MEM-30 | Con cuota 0, esa colección no se consulta ni aparece en la ventana de ese consumidor | Obligatorio | T |
| RF-MEM-31 | El escritor nunca recibe prosa recuperada; el crítico de oficio sí | Obligatorio | T |
| RF-MEM-32 | El orden de las piezas en la ventana es declarado y estable: mismas entradas, misma ventana, pieza por pieza | Obligatorio | T |
| RF-MEM-33 | La cuota de entrada de la etapa la calcula el orquestador dividiendo el techo entre las llamadas realmente en vuelo | Obligatorio | T |
| RF-MEM-34 | El guardián de presupuesto lo invoca el código, nunca el modelo. El agente no ve su presupuesto ni decide qué pedir | Obligatorio | A |
| RF-MEM-35 | Lo ensamblado nunca supera la cuota de entrada de la etapa | Obligatorio | T |
| RF-MEM-36 | Si no cabe, se recorta en el orden declarado: prosa, resúmenes de escena, `CanonCards`, `ResumenRodante`; dentro de cada colección, por rango inverso | Obligatorio | T |
| RF-MEM-37 | Residentes y arrastres no se recortan, salvo el `ResumenRodante`, que es la última válvula | Obligatorio | T |
| RF-MEM-38 | Si lo intocable ya supera la cuota, se recorta el `ResumenRodante` y se entrega igual, con causa raíz `contexto ausente`. No hay bloqueo por esta vía | Obligatorio | T |
| RF-MEM-39 | Lo negado se descuenta antes de cerrar la ventana y no llega al consumidor de ninguna forma | Obligatorio | T |
| RF-MEM-40 | El conteo de entrada usa el tokenizador del modelo congelado al crear la ejecución | Obligatorio | T |
| RF-MEM-41 | Se registra además el uso de entrada real del proveedor; si diverge por encima de `umbral_deriva_conteo`, se anota causa raíz `presupuesto excedido`, que no bloquea ni reintenta | Deseable | T |

### Trazabilidad

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-MEM-42 | La ventana registra qué entró y qué quedó fuera: identificador de cada residente y de cada unidad recuperada, más los negados con su motivo —cuota o recorte— | Obligatorio | T |
| RF-MEM-43 | Todo fragmento generado registra las `CanonCard` que lo justificaron, derivadas de la ventana con la que se generó | Obligatorio | T |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | **Determinismo de la memoria.** Con el mismo índice, la misma configuración y la misma escena, la ventana es idéntica pieza por pieza, sin ninguna llamada a modelo | T |
| RNF-2 | **Reproducibilidad de los vectores.** El modelo de incrustación se congela por ejecución; los vectores se guardan y no se recalculan. Una ejecución cuyo modelo ya no exista no se reanuda sin reconstruir el índice | T |

## Docs de referencia

`architecture.md` §3.1–§3.15, §7; `definitions.md` §4
