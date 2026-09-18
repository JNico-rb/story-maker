# Informe — revisor-encargo-20260918-1600

**Motivo de cierre: VUELTAS_PARCIALES.** Presupuestadas 4 vueltas; se ejecutaron 2 (vuelta 0 = línea base, vuelta 1 = una variante) y se detuvo aquí por decisión del usuario, no por STOP ni por ABORTO del bucle. Esto es una demostración del mecanismo con datos reales, no una optimización completa. Ver la limitación de fondo más abajo antes de leer cualquier número.

## Configuración

| | |
|---|---|
| Agente | `revisor-encargo` |
| Métrica | `recall_revisor` (calibrada: `herramientas/evaluadores/calibracion-recall_revisor.md`, exactitud 0,969, sin falsos positivos) |
| Conjunto | `ascensores-v1` — 9 casos, 32 defectos puntuables (20 búsqueda / 12 control), generados por **mutación controlada** de 9 capítulos reales y aprobados de dos novelas del repositorio (`herramientas/optimizacion/casos/generar.py`) |
| Objetivo | `recall_revisor >= 0,80` en control |
| Restricciones | `cita_verificable >= 0,90` — **no aplicable**: el contrato de `revisor-encargo` (spec §5.6) no tiene campo `cita` obligatorio, así que no se le puede exigir; `palabras_prompt <= 1,3×` línea base (989) |

## Curva

| Vuelta | Operación | Búsqueda | Control | Aceptada | Motivo |
|---:|---|---:|---:|---|---|
| 0 | — (línea base) | 0,400 | 0,500 | — | línea base |
| 1 | 2 — recorrido en 4 pasos, con paso dedicado a entradas posteriores | 0,200 | 0,500 | **No** | control +0,00 < 0,10; búsqueda además regresó |

**Mejor variante: ninguna.** La línea base (`produccion.md`) sigue siendo la mejor probada. `mejor.md` = `produccion.md`.

## Invocaciones

18 invocaciones de `revisor-encargo` (9 por vuelta × 2 vueltas) + 1 del agente `optimizador`. Tope declarado: 60. Consumido: 31 %.

## Consultas al split de control

**2 de 2 vueltas ejecutadas** (vuelta 0 y vuelta 1). Con 12 defectos de control, cada consulta es una mirada completa al conjunto de decisión. **Reserva declarada por diseño (spec §9.5.3):** con tan pocas vueltas la contaminación es mínima aquí, pero si esta ejecución se retomara hasta las 4 vueltas presupuestadas, la cuarta consulta ya estaría leyendo un control mirado 4 veces sobre 12 ítems — hay que leer cualquier "mejora" aceptada en una vuelta tardía con esa reserva.

## Integridad del agente

`.claude/agents/revisor-encargo.md` restaurado y verificado por hash en las dos vueltas (`git hash-object` = `57ee40d452b63dc17b1ab982fb9dc18c054241d0`, igual a `produccion.hash`). El repositorio queda exactamente como estaba antes de la ejecución.

## Lo que se aprendió (más allá del número)

1. **El vector de "convertir en procedimiento" (operación 2) no bastó por sí solo.** La hipótesis del optimizador —que faltaba un paso explícito para recorrer las entradas posteriores— era razonable, pero el resultado no confirma que faltara *detección*: leyendo los tres informes de búsqueda que peor puntuaron, el revisor **sí señaló** varios de los adelantos etiquetados; lo que cambió fue el **estilo de cita**. Con el prompt de producción citaba frases completas de la entrada de escaleta; con la variante, en varios casos parafraseó o truncó con puntos suspensivos (p. ej. "Ahora bajo las escaleras y noto..." en vez de la frase completa), y el emparejador por subcadena —que exige la cita literal— no lo contó como acierto.
2. Esto es exactamente la propiedad documentada en `calibracion-recall_revisor.md`: el evaluador mide "lo mencionó citando" y no "lo detectó". La vuelta 1 puede ser una regresión real de detección, o puede ser una regresión de *estilo de cita* con la misma detección de fondo — **este experimento, con 2 vueltas, no permite distinguir las dos explicaciones.**
3. **Consecuencia para la próxima vuelta**, ya anotada en `optimizaciones/revisor-encargo/lecciones.md`: no repetir "procedimiento de 4 pasos monolítico"; si se retoma el vector de adelantos, aislar esa variable sin tocar el resto del método de recorrido, y considerar mirar primero si el problema está en el evaluador (exigir cita literal) antes de seguir gastando vueltas en el prompt.

## Limitación de fondo, para leer los números de esta ejecución con la reserva correcta

El conjunto `ascensores-v1` es de **defectos inyectados por mutación**, no naturales. Se probó primero con los 9 capítulos reales tal cual (dos novelas completas, una en opus y otra en haiku) y solo se encontraron 3 defectos naturales de gravedad 2 o 4 en total — el mismo hallazgo que E5: los defectos reales de estos manuscritos casi nunca son del contrato de `revisor-encargo`. Con 3 no hay nada que medir, así que se inyectaron 32 defectos declarados (inserciones o sustituciones del párrafo final, nunca borrados) sobre esos mismos textos reales, de forma que cada mutación produce a la vez el capítulo mutado y su etiqueta.

Un defecto inyectado por inserción es, en general, **más visible** que uno natural por omisión (falta un párrafo entero de más, no falta un matiz). Es razonable esperar que el `recall_revisor` medido aquí sea **optimista** frente al que daría un conjunto de defectos naturales del mismo tamaño. Los números de esta ejecución (0,400 / 0,200 / 0,500) sirven para demostrar que el mecanismo funciona de punta a punta con datos reales — invocaciones reales del agente, puntuación real, puerta real, restauración real — pero **no deben leerse como una medida fiable de qué tan bueno es `revisor-encargo` en producción.**

## Qué es candidato y qué no

**Nada se promueve.** La línea base sigue siendo la mejor, así que no hay nada nuevo que copiar sobre `.claude/agents/revisor-encargo.md`, y no se publicó ningún candidato en Langfuse (no había credenciales en esta sesión, y tampoco había nada que superara la línea base). Retomar esta ejecución significa una vuelta 2 con una hipótesis distinta a la de la vuelta 1, partiendo de `mejor.md` (que hoy es idéntico a `produccion.md`).
