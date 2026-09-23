# 017 — EVL · Evaluación del sistema

- [ ] Spec approved   <- only the user marks this

## Objetivo

Que el sistema demuestre con resultados medibles que funciona de principio a fin: la novela de ejemplo, los seis briefs de prueba con su tabla de validadores, las evals de cada rol, la revisión humana frente al juez, una iteración de ajuste, los cambios reales y el coste por novela y por revisión.

## Alcance

Cubre:

- los seis briefs de prueba, ficticios —los cinco que pide el encargo y uno que prueba los marcos—, y el brief de ejemplo del README;
- la reproducción del brief de ejemplo de extremo a extremo y `ejemplos/novela-ejemplo.pdf`;
- la evaluación del sistema: la tabla por brief y el caso de Lean;
- las evals de rol: extractor, registrador y entrevistador con conjuntos dorados; crítico y juez con defectos sembrados; observación del revisor visual, con el caso RT11 de un fallo visual que vuelve al rol correspondiente; writer y editor con los datos de ejecución;
- la revisión humana en la cola de anotación y su comparación con el juez;
- la calibración ligera de los umbrales de la rúbrica;
- la iteración de ajuste, con las versiones de prompt;
- los cambios reales del lector;
- el protocolo de coste, contrastado con OpenRouter;
- los resultados en `verification.md` §4.2 y §8.

Órdenes de la CLI (`example`, `evals`): [001 design.md](../001-base/design.md) §10; colas de anotación de Langfuse y consulta de coste de OpenRouter: §11.

Depende de 004, 005, 014 y 015, y de todo lo que ejercita la generación completa.

**Fuera de alcance:**

- La presentación —el deck, sus anexos, el README de `presentacion/`, el vídeo de demo y la slide de presupuesto y coste—: el usuario la aplazó, y no tiene requisitos todavía.
- Dar valor a las demás cifras de `architecture.md` §15.2 —límites, cuotas, presupuesto, umbrales de los linters y objetivos de legibilidad—: la calibración de esta spec es solo la de los umbrales de la rúbrica (§10.3), y ningún doc dice todavía quién asigna las demás.
- Las pruebas adversariales de cada vector, que viven en la spec de su detector, y la auditoría de seguridad (018). La excepción es RT11, que es un caso de la eval del revisor visual (RF-EVL-14); su prueba con el doble es la de `revision-visual` en 014.
- Correr las evals en cada cambio: van bajo demanda, no en CI (`verification.md` §4.7).

## Requisitos

Todos son **Obligatorio**.

### Briefs de prueba

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-1 | El repositorio contiene seis briefs de prueba, todos ficticios —ejemplo, infantil, adversarial, temporal, prohibidas y fuera de ambientación—, y cada uno se importa (005) sin error de schema, sin datos faltantes y sin contradicciones | Obligatorio | T |
| RF-EVL-2 | Cada brief cumple su propósito de `verification.md` §4.2: el de ejemplo es el caso nominal; el infantil tiene un destinatario de siete años, fábula y tono tierno; el adversarial, un texto libre con instrucciones dirigidas al sistema; el temporal, recuerdos, edades y allegados preparados para que un plan ingenuo viole un invariante temporal; el de prohibidas, entradas de nivel novela y de nivel cliente que la historia tiende a usar, con variantes de acento y de plural; y el de fuera de ambientación, un deseo de trama en la prehistoria con el marco libre. Las entradas de nivel cliente se cargan en la lista del cliente de evaluación antes de importar su brief | Obligatorio | I |
| RF-EVL-3 | El README de la raíz → muestra el brief de ejemplo y la orden de la CLI que lo reproduce | Obligatorio | I |

### Novela de ejemplo

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-4 | La orden `example` de la CLI → importa el brief de ejemplo, lanza su generación, espera a que termine y escribe el PDF de la versión publicada en la ruta que recibe. Si la ejecución se detiene, sale con error, su estado y su motivo. Se prueba con el doble del agente | Obligatorio | T |
| RF-EVL-5 | Con el proveedor y Langfuse reales → `example` genera de extremo a extremo una novela de 10 capítulos y deja `ejemplos/novela-ejemplo.pdf`, que se commitea | Obligatorio | D |

### Evaluación del sistema

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-6 | La orden `evals` de la CLI → reproduce los seis briefs, con una ejecución de generación por brief, y produce la tabla por brief: qué validadores pasaron y cuáles fallaron en cada uno, con sus scores leídos de Langfuse. La imprime en Markdown, lista para `verification.md` §4.2, con el commit y la versión de prompt de cada rol. Se prueba con los dobles del agente y de Langfuse | Obligatorio | T |
| RF-EVL-7 | La tabla de los seis briefs reales → queda en `verification.md` §4.2, y de ella sale la eval del planner: sus salidas juzgadas por `outline`, `grafo-causal` y `cronologia-lean`. En el brief adversarial, ninguna instrucción llega al brief ni a la novela. En el de fuera de ambientación, el planner enmarca el deseo, nada de la prehistoria entra en la cronología y pasan todos los validadores | Obligatorio | D |
| RF-EVL-8 | El brief temporal → la evaluación muestra si `cronologia-lean` detectó una incoherencia que ningún otro validador detectó. Si no apareció, `verification.md` §4.2 dice por qué, con la ejecución que lo intentó | Obligatorio | D |

### Evals de rol

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-9 | Eval dorada del extractor → sobre textos libres con sus hechos esperados —sujeto, atributo, valor y cita—, cuenta los omitidos y los descartados por cita inexistente o por sujeto desconocido | Obligatorio | T |
| RF-EVL-10 | Eval dorada del registrador → sobre capítulos con su delta real esperado —eventos con todos sus atributos, usos de hechos, hechos nuevos, arcos resueltos y resumen—, cuenta los alucinados y los omitidos de cada tipo, y los atributos de evento erróneos | Obligatorio | T |
| RF-EVL-11 | Eval dorada del entrevistador → sobre conversaciones guionizadas con su brief esperado, comprueba que plantea cada dato faltante y cada contradicción —también C6 sobre un deseo de trama—, que pregunta siempre por las prohibidas, que anota los deseos de trama, que propone un marco al deseo que no cabe en el presente post-IA sin rechazar ninguno por su ambientación, y que no da por completo un brief inválido: lo confirma el cliente, no el entrevistador | Obligatorio | T |
| RF-EVL-12 | Eval del crítico y del juez con defectos sembrados → capítulos y novelas con un defecto sembrado por criterio —inconsistencia de personaje, salto temporal, contradicción entre capítulos, prosa repetitiva, final abrupto y personalización forzada—; cada uno debe bajar su criterio, y ni un tropo pedido en los deseos de trama ni el marco de un deseo deben bajar ninguno. Por cada defecto que el crítico no detecta, la eval dice si la tarjeta que lo revelaba estaba en su ventana o entre los negados: es la medida de la elección de cuotas | Obligatorio | I |
| RF-EVL-13 | Eval de observación del revisor visual → sobre vistas previas con defectos de estructura y de enlaces sembrados, cuenta lo que ve y lo que se le escapa frente a la estructura esperada | Obligatorio | I |
| RF-EVL-14 | Uno de los casos de esa eval es una candidata con un enlace de la ficha sembrado que falta (RT11) → con el revisor visual y el registrador reales, el gate no publica, el fallo vuelve al registrador y queda corregido en el ciclo siguiente del gate. Es la evidencia de que un fallo visual vuelve al rol correspondiente (`architecture.md` §9.4), y su resultado rellena la fila RT11 de `verification.md` §4.9 | Obligatorio | D |
| RF-EVL-15 | Datos de ejecución del writer y el editor → de los intentos, veredictos y defectos guardados de las ejecuciones de los seis briefs, la tasa de aceptación del writer al primer intento y los defectos resueltos por corrección del editor, más una inspección muestreada de sus trazas | Obligatorio | D |

### Revisión humana y calibración

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-16 | La CLI → crea por API una cola de anotación de Langfuse cuyas configuraciones de score son los criterios de la rúbrica de novela, y un ítem por novela que revisar. Se prueba con el doble de Langfuse | Obligatorio | T |
| RF-EVL-17 | Una persona → revisa al menos una novela completa con la rúbrica de novela en esa cola | Obligatorio | I |
| RF-EVL-18 | La comparación entre la persona y el juez → da, criterio a criterio, la diferencia absoluta media de sus puntuaciones y la tasa de acuerdo exacto. Con puntuaciones de fixture, da las cifras calculadas a mano | Obligatorio | T |
| RF-EVL-19 | La calibración de un criterio de rúbrica → elige el corte que separa los capítulos y novelas con su defecto sembrado de los limpios y, entre los cortes que lo hacen, el más parecido al juicio de la revisión humana. Si ningún corte separa, lo informa en vez de elegir uno. Se prueba con puntuaciones de fixture | Obligatorio | T |
| RF-EVL-20 | Los umbrales calibrados → pasan a `quality.thresholds`. Un criterio que no separa lo sembrado de lo limpio se reescribe o se retira de `quality.active_criteria`, con su motivo en `verification.md` §8. La fiabilidad medida del crítico y del juez queda en `verification.md` §4.2 | Obligatorio | I |

### Ajuste, cambios reales y coste

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-21 | Una iteración de ajuste —de prompt, de rúbrica o de umbral— → corre sobre los seis briefs antes y después. Un prompt nuevo se sube sin etiqueta, las evals lo corren con `latest` como etiqueta de los prompts, y solo recibe la etiqueta de producción si pasa (004). Los resultados, con la versión de prompt de cada uno, van a `verification.md` §4.2, y el cambio, a §8 con su efecto medido | Obligatorio | D |
| RF-EVL-22 | Cambios reales → sobre las novelas de la evaluación se piden cambios reales del lector, que miden los capítulos afectados, la continuidad tras la propagación y el coste de cada revisión, y sirven de demo de la propagación | Obligatorio | D |
| RF-EVL-23 | El coste → la CLI calcula el de una novela —su entrevista, o su importación si el brief se importó, más su ejecución de generación— y el de una revisión —la interpretación de la solicitud más su ejecución de cambio—, sumando el coste guardado de sus sesiones de rol: el uso exacto por `operation.pricing`. El coste de una entrevista sale de las conversaciones de la eval del entrevistador. Se prueba con sesiones de fixture | Obligatorio | T |
| RF-EVL-24 | La consulta del coste facturado por OpenRouter para un id `gen-…` → usa la consulta de generación de 004 (RF-OBS-8), y la que no se resuelve a tiempo la informa sin inventar la cifra. Se prueba con un doble de OpenRouter | Obligatorio | T |
| RF-EVL-25 | Una vez, con ejecuciones reales → el coste calculado se contrasta con lo que factura OpenRouter por cada generación de al menos una novela, y la diferencia va a `verification.md` §4.2 | Obligatorio | D |

### Registro y explainer

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-EVL-26 | Al cerrar 017 → cada resultado de `verification.md` §4.2 —tabla por brief, iteración de ajuste, evals de rol, juez frente a revisión humana, caso de Lean, cambios reales y coste— deja de estar pendiente, con el commit y las versiones de prompt que lo produjeron; lo que cambió tras cada eval tiene su fila en §8, con causa y efecto | Obligatorio | I |
| RF-EVL-27 | Al cerrar 017 → la cabecera de `architecture.md` §10.7 lleva el explainer de la evaluación humana frente al juez | Obligatorio | I |

## Docs de referencia

- `architecture.md` §3.4, §9.4 (rol correspondiente de un fallo visual), §10.3 («Calibración de los umbrales» y fiabilidad), §10.7, §10.8, §11.5, §12.3, §12.4, §14.2 (CLI), §15.2 y §16 («Calibración de los umbrales», «Revisión humana», «Cálculo del coste»).
- `definitions.md` §5 (CLI), §6 (`RevisionHumana`, `Validador`) y §12.
- `domain-knowledge.md` §2.3, §4.5 y §6.
- `verification.md` §4.2, §4.5, §4.8, §4.9 (RT11), §5 («Extractor», «Registrador», «Entrevistador», «Planner», «Crítico y juez», «Writer y editor», «Elección de cuotas», «Coste por novela y por revisión», «Generación completa del brief de ejemplo», «Los cinco briefs de prueba», «CLI»), §6 (riesgos 1, 8 y 15) y §8.
