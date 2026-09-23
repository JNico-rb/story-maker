# El encargo del examen fija qué se construye; el tema post-IA se mantiene

Es la spec inicial del proyecto: qué se decidió construir y por qué, escrita el 2026-09-23, antes de la primera línea de código. Cada decisión, con sus alternativas y su criterio, está en [architecture.md §16](../architecture.md#16-decisiones-cerradas); aquí va el conjunto y su razón.

## Contexto

El 2026-09-23 llegó el encargo del examen (`project-constraints.md`): novelas personalizadas de regalo, con entrevista, versiones, cambios del lector, Lean, TLA+, Langfuse y servidor MCP. El diseño vigente —una novela de ciencia ficción autónoma de 90.000 palabras a partir de un único prompt, sin interacción y solo en Markdown— lo contradecía en la raíz.

El encargo pide dos cosas de igual peso. **Personalización:** el destinatario tiene que reconocerse en la novela. **Calidad narrativa mínima:** no se aceptan personajes inconsistentes, saltos temporales sin sentido, capítulos que se contradicen, prosa mecánica ni finales abruptos. Un sistema que solo optimiza que los datos aparezcan fracasa en la segunda; uno que solo escribe bien fracasa en la primera.

## Decisión

Un harness agéntico que convierte una entrevista en una novela de **10 capítulos de 1.000–1.500 palabras, siempre ambientada en un mundo posterior a la revolución de la IA**, y que la mantiene viva tras publicarla:

1. **Entrevista.** Un entrevistador conversa con el cliente y produce un brief validado con schema. Detecta los datos que faltan y siete tipos de contradicción. Si el cliente pega un texto libre, un extractor aislado saca hechos con cita literal y el código verifica que cada cita existe.
2. **Planificación.** El código convierte el brief en story bible. El planner inventa el mundo post-IA —un novum y sus consecuencias—, los personajes y lugares secundarios, un outline de 10 capítulos con beats y la hoja de estilo.
3. **Producción por capítulo.** El writer escribe cada capítulo y dos hooks lo validan: el de policy y el de validación. Un crítico lo puntúa con rúbrica, el editor corrige y el registrador extrae qué cambió. Cada capítulo aceptado deja un punto de control.
4. **Publicación.** Un gate ejecuta los validadores de la novela entera antes de publicar una versión: elementos obligatorios, nombres, prohibidas, arcos, Lean, juez y revisión visual por browser MCP.
5. **Lectura y cambios.** Una lectura web con índice, ficha de personajes y lugares, y portada con dedicatoria. Desde ella el lector pide un cambio («el perro se llama Nala») o edita a mano. El sistema regenera solo los capítulos afectados y publica una versión nueva, conservando la anterior.

Alrededor van el login por cliente, el servidor MCP para consultar, descargar y pedir cambios, los linters de prosa, la observabilidad completa en Langfuse y una auditoría de seguridad. El encargo marca parte de esto como opcional; se hace entero.

El tema post-IA se mantiene porque es el tema del curso y conserva el trabajo de dominio sobre el novum y los tropos. Sobreviven del diseño anterior el flujo de trabajo, el vocabulario de calidad, el RAG híbrido sin re-ranking, el guardián de ventana y los invariantes que siguen aplicando.

## Por qué así

- **Nueve roles y no un agente.** El que escribe no se evalúa a sí mismo, y separarlos permite medir aparte la escritura, la crítica y la corrección.
- **El Claude Agent SDK como runtime de los roles.** Aporta de forma nativa el `CLAUDE.md`, las skills, los hooks y las tools con schema que pide el encargo. La orquestación sigue siendo propia, porque es la que modela TLA+.
- **El código decide y el modelo propone.** La validez del brief, la verificación de las citas, qué entra en la ventana, el veredicto, qué se publica y qué capítulos afecta un cambio son código: lo que se puede calcular no se le pregunta a un modelo.
- **Story bible en SQLite con RAG híbrido sin re-ranking.** Cada hecho registra en qué capítulos se usa, y eso hace exacto el cálculo de capítulos afectados por un cambio. La recuperación determinista se prueba sin modelo.
- **Lean para la historia y TLA+ para el sistema.** Las edades, las fechas y quién está dónde son propiedades decidibles: no hay por qué dejárselas a un juez. La máquina de estados del harness se especifica en TLA+ antes de escribir el orquestador.
- **Datos personales minimizados.** Langfuse recibe las trazas con máscara y Lean, un fichero seudonimizado. Todos los briefs de prueba son ficticios.
- **Lo más fácil posible, tan difícil como haga falta.** La dificultad deliberada está en la tecnología que el curso quiere ver: RAG, Langfuse, MCP, Agent SDK, Lean y TLA+. En todo lo demás se elige la opción más simple que cumple el encargo.

## Fuera de alcance

Por el encargo: los pagos, la gestión de cuentas más allá del registro y el acceso, la impresión física, las ilustraciones, el audio y el despliegue en producción. Por decisión: lo que [architecture.md §16](../architecture.md#16-decisiones-cerradas) descarta, cada cosa con su motivo.

## Cómo se sabrá que funciona

Cada validador envía su resultado a Langfuse. Cinco briefs de prueba, uno adversarial y otro diseñado para provocar una incoherencia temporal, dan la tabla de qué validadores pasan y cuáles fallan. Una iteración de ajuste se documenta con los resultados de antes y después, y al menos una novela completa se revisa a mano con la misma rúbrica que el juez ([verification.md §4.2](../verification.md#42-evals--clase-t-i-o-d-según-el-método-de-puntuación)).

## Consecuencias

- `definitions.md`, `domain-knowledge.md`, `architecture.md` y `verification.md` se reescribieron con numeración nueva, y las specs 001–011 se sustituyen por un conjunto nuevo, una carpeta por feature en `specs/`. Las anteriores quedan solo en el historial de git y no son referencia.
- [ADR 0001](0001-decisiones-en-architecture.md) sigue vigente con otra numeración: las decisiones abiertas están en `architecture.md` §15 y las cerradas en §16, que recoge además las opciones y el criterio de cada una.
