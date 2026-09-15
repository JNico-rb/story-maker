# story-maker — Especificación funcional

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. El usuario aporta una idea; tres agentes (interrogador, escritor, revisor) coordinados por un **harness** la convierten en una novela completa.

Este documento describe **qué** hace el sistema y cómo se comportan sus partes. Las decisiones de software (lenguaje, librerías, formatos de fichero, modelos concretos) se recogen aparte en `specs/implementation.md`.

Esquema de referencia: [novela-agentica.drawio](../novela-agentica.drawio).

---

## 1. Alcance

### 1.1 Objetivo

A partir de una idea inicial del usuario, producir una novela completa —biblia, escaleta, capítulos aprobados y manuscrito ensamblado— con continuidad interna verificada, sin intervención humana desde la aprobación de la escaleta hasta el final.

### 1.2 Decisiones fijas

| Aspecto | Decisión |
|---|---|
| Género | Fijo: ficción especulativa sobre el mundo posterior a la revolución de la IA |
| Universo | Cada novela inventa su propio mundo post-IA. No existe canon compartido entre novelas |
| Idioma | Castellano, en todo: interrogatorio, artefactos internos y novela |
| Interacción | Terminal, conversacional durante el interrogatorio; solo progreso después |

### 1.3 No objetivos

Quedan explícitamente fuera:

- Exportación a EPUB, PDF u otros formatos de publicación (solo texto).
- Interfaz web o gráfica.
- Ilustraciones.
- Otros idiomas.
- Canon o universo compartido entre novelas.
- Modo de ejecución desatendido para el interrogatorio (respuestas predefinidas). Las pruebas son manuales (ver §8).
- Volver atrás a un capítulo anterior ya aprobado y regenerar desde ahí.
- Reescritura automática tras la revisión global final.

---

## 2. Actores

| Actor | Tipo | Responsabilidad |
|---|---|---|
| **Usuario** | Persona | Aporta la idea, responde al interrogatorio, aprueba la escaleta, observa el progreso, decide qué hacer con el informe final |
| **Harness** | Programa determinista | Orquesta el flujo, invoca a los agentes, guarda el estado, impone límites, reanuda, ensambla |
| **Agente interrogador** | Agente LLM | Convierte la idea en biblia y escaleta mediante preguntas al usuario |
| **Agente escritor** | Agente LLM | Escribe cada capítulo y su resumen |
| **Agente revisor** | Agente LLM | Juzga cada capítulo y, al final, la novela completa. Nunca edita |

---

## 3. Artefactos

Todos los artefactos de una novela viven en **una carpeta propia de esa novela**. Son el único estado del sistema: no hay nada en memoria que no esté también en disco tras cada paso completado.

| Artefacto | Contenido | Lo escribe | Lo leen |
|---|---|---|---|
| **Idea** | Texto libre inicial del usuario | Harness (al arrancar) | Todos |
| **Biblia** | Premisa; tono y estilo; el mundo post-IA de esta novela (qué pasó, qué reglas rigen, qué ha cambiado); personajes con arco, motivación y voz; reglas internas que la historia no puede romper | Interrogador | Todos |
| **Escaleta** | Estructura en tres actos (planteamiento, nudo, desenlace). Una entrada por capítulo: título provisional, acto al que pertenece, objetivo narrativo, sucesos clave, personajes presentes, gancho de cierre, **longitud objetivo en palabras**. Número total de capítulos | Interrogador | Todos |
| **Capítulo N** | Texto del capítulo. Se conservan todas las versiones (intento 1, 2, 3), marcada la aprobada | Escritor (solo el suyo) | Todos |
| **Resumen N** | Hechos ocurridos; cambios de estado de cada personaje; hilos abiertos y cerrados; objetos, lugares o datos introducidos que condicionan el futuro | Escritor (junto con el capítulo) | Todos |
| **Informe N** | Veredicto APROBADO / RECHAZADO y lista de problemas concretos (ver §5.3). Uno por intento | Revisor (solo el suyo) | Todos |
| **Estado** | Fase actual; capítulo en curso; intento en curso; capítulos aprobados; coste acumulado; motivo de parada si la hubo | **Solo el harness** | Harness |
| **Registro (log)** | Cada invocación a un agente: quién, cuándo, con qué entradas, tokens/coste, resultado; cada decisión del harness (aprobar, reintentar, aceptar por agotamiento, parar) | **Solo el harness** | Usuario |
| **Manuscrito** | Novela ensamblada: título, índice, capítulos aprobados en orden | Harness (al final) | Usuario |
| **Informe global** | Resultado de la revisión de continuidad sobre la novela completa | Revisor | Usuario |

### 3.1 Reglas de escritura

- Cada agente escribe **únicamente en su zona** (columna "Lo escribe"). Los agentes tienen herramientas de lectura y escritura de ficheros, pero el harness restringe la escritura a esa zona.
- **Nada aprobado se modifica**: ni la biblia ni la escaleta tras la aprobación del usuario, ni un capítulo tras el veredicto APROBADO (o la aceptación por agotamiento).
- El **Estado** y el **Registro** son exclusivos del harness. Un agente nunca decide qué capítulo va ahora ni si algo está aprobado.

---

## 4. Flujo

```
Usuario: idea
   │
   ▼
[1] INTERROGATORIO ──► biblia + escaleta ──► usuario confirma ──┐
   ▲                                              │              │
   └──────────── usuario pide cambios ◄───────────┘              │
                                                                 ▼
[2] BUCLE POR CAPÍTULO (N = 1..total), sin intervención humana
   ├─ escritor escribe capítulo N + resumen N
   ├─ revisor emite informe N
   ├─ RECHAZADO y quedan reescrituras → escritor reescribe con el informe
   ├─ RECHAZADO y no quedan → harness acepta la última versión, registra aviso
   └─ APROBADO → harness guarda estado, N = N+1
                                                                 │
                                                                 ▼
[3] FINAL: harness ensambla manuscrito ──► revisor: informe global ──► usuario
```

### 4.1 Fase 1 — Interrogatorio

1. El harness crea la carpeta de la novela, guarda la idea y lanza al interrogador.
2. El interrogador hace preguntas al usuario en **rondas sucesivas, sin límite fijo**. Pregunta lo que cambia la novela: protagonista y antagonismo, qué versión del mundo post-IA, tono, punto de vista, tipo de final, temas que tocar o evitar, extensión deseada.
3. Cuando el interrogador considera que no le quedan huecos, **propone el cierre**: presenta la biblia y la escaleta completas y pide confirmación.
4. El usuario **confirma** o **pide cambios**. Si pide cambios, el interrogador reabre preguntas y vuelve a proponer cierre. Nada se escribe hasta que hay confirmación explícita.
5. Con la confirmación, el harness marca la biblia y la escaleta como aprobadas e inmutables, y pasa a la fase 2.

Restricciones que el interrogador debe respetar al proponer la escaleta (impuestas por el harness, configurables):

| Parámetro | Valor por defecto |
|---|---|
| Capítulos | mínimo 3, máximo 30 |
| Longitud objetivo por capítulo | entre 1.500 y 4.000 palabras |

Si la escaleta propuesta viola un límite, el harness la devuelve al interrogador con el motivo antes de presentársela al usuario.

### 4.2 Fase 2 — Bucle por capítulo

Para cada capítulo N, en orden:

**Escritura.** El escritor recibe:
- la biblia completa,
- la escaleta completa (con la entrada de N destacada),
- los resúmenes de todos los capítulos aprobados anteriores,
- el **texto íntegro del capítulo N−1** aprobado (para mantener voz y enlace),
- en caso de reescritura, el informe de rechazo del intento anterior y el texto rechazado.

Entrega el capítulo N y su resumen N.

**Revisión.** El revisor recibe el capítulo N, su resumen, la biblia, la escaleta y los resúmenes previos. Emite el informe N (§5.3).

**Decisión del harness.**
- APROBADO → marca el intento como aprobado, actualiza el estado, avanza a N+1.
- RECHAZADO con reescrituras disponibles → lanza al escritor con el informe. **Máximo 2 reescrituras** (3 intentos en total).
- RECHAZADO sin reescrituras disponibles → **acepta la última versión**, registra el aviso con el informe adjunto en el log y en el estado, avanza a N+1. La novela no se bloquea por un desacuerdo entre agentes.

**Progreso visible.** El usuario ve una línea por evento: capítulo N escrito, rechazado (motivo resumido), aprobado, aceptado por agotamiento, coste acumulado. Puede interrumpir cuando quiera; el estado en disco permite reanudar (§6.2).

### 4.3 Fase 3 — Final

1. El harness ensambla el **manuscrito** con los capítulos aprobados.
2. El revisor hace **una única pasada sobre la novela completa** buscando solo lo que no puede verse capítulo a capítulo: hilos prometidos y nunca cerrados, contradicciones entre capítulos lejanos, personajes que desaparecen sin explicación, cambios de reglas del mundo. Emite el **informe global**. No reescribe nada.
3. El harness presenta al usuario el manuscrito y el informe global. Qué hacer con él es decisión del usuario, fuera del alcance del programa.

---

## 5. Contratos de los agentes

### 5.1 Agente interrogador

| | |
|---|---|
| **Entrada** | Idea del usuario; respuestas del usuario en cada ronda; límites de tamaño del harness |
| **Salida** | Biblia y escaleta (§3); propuesta de cierre; preguntas al usuario |
| **Puede escribir** | Biblia, escaleta |
| **Debe** | Preguntar solo lo que cambia la novela; proponer el cierre cuando no le queden huecos; fijar número de capítulos y longitud objetivo dentro de los límites; garantizar que la escaleta cubre los tres actos y que cada capítulo tiene un objetivo narrativo propio |
| **No debe** | Escribir prosa de la novela; cerrar sin confirmación del usuario; tomar decisiones que el usuario ha dejado explícitamente abiertas sin marcarlas como propias |

### 5.2 Agente escritor

| | |
|---|---|
| **Entrada** | Biblia; escaleta; resúmenes previos; capítulo anterior íntegro; en reescritura, informe y texto rechazado |
| **Salida** | Capítulo N; resumen N |
| **Puede escribir** | Capítulo N (intento en curso) y resumen N. Nada más |
| **Debe** | Cumplir el objetivo, los sucesos y el gancho de la entrada N de la escaleta; respetar biblia y resúmenes previos; ajustarse a la longitud objetivo (±20 %); mantener la voz del capítulo anterior; en reescritura, corregir cada problema del informe sin introducir otros |
| **No debe** | Tocar capítulos, resúmenes o informes anteriores; modificar la biblia o la escaleta; adelantar sucesos asignados a capítulos posteriores; resolver hilos que la escaleta deja abiertos para más adelante |

El resumen N lo escribe el escritor **en la misma entrega** que el capítulo. Si el capítulo se rechaza, su resumen se descarta con él.

### 5.3 Agente revisor

| | |
|---|---|
| **Entrada (por capítulo)** | Capítulo N; resumen N; biblia; escaleta; resúmenes previos |
| **Entrada (global)** | Manuscrito completo; biblia; escaleta; todos los resúmenes |
| **Salida** | Informe con veredicto y lista de problemas |
| **Puede escribir** | Informe N (o informe global). Nada más |
| **Debe** | Juzgar exclusivamente contra estos criterios, en este orden de gravedad: (1) contradice la biblia o los resúmenes previos; (2) no cumple la entrada N de la escaleta (objetivo, sucesos, gancho) o adelanta sucesos futuros; (3) longitud fuera de ±20 % del objetivo; (4) ruptura de voz, punto de vista o tono; (5) el resumen no refleja el capítulo. Cada problema debe ser **concreto y accionable** (dónde, qué, por qué) |
| **No debe** | Editar el texto; rechazar por gusto sin señalar un criterio; añadir criterios propios |

Un informe es **RECHAZADO** si tiene al menos un problema de gravedad 1 o 2, o dos o más de gravedad 3-5. En otro caso es **APROBADO** (puede llevar observaciones menores que no obligan a reescribir).

---

## 6. Contrato del harness

### 6.1 Responsabilidades

- Crear y gestionar la carpeta de la novela.
- Invocar a cada agente con exactamente las entradas de su contrato; ni más (ahorro de contexto) ni menos.
- Restringir la zona de escritura de cada agente (§3.1).
- Tomar todas las decisiones de flujo: aprobar, reescribir, aceptar por agotamiento, avanzar, parar.
- Escribir el Estado tras **cada** decisión, no al final.
- Registrar todo (§3, Registro).
- Imponer los límites (§6.3).
- Ensamblar el manuscrito.
- Mostrar el progreso al usuario.

### 6.2 Reanudación

Relanzar el programa sobre una carpeta de novela existente **continúa donde se quedó**:

- Si la escaleta no está aprobada → vuelve al interrogatorio, con lo ya respondido como contexto.
- Si está en el bucle → retoma en el capítulo y el intento indicados en el Estado. Nada aprobado se regenera. Un intento a medias (escrito sin revisar) se considera no existente y se repite.
- Si el bucle terminó pero no hay informe global → ejecuta solo la fase 3.
- Si la novela está completa → lo indica y no hace nada.

### 6.3 Límites

| Límite | Comportamiento | Por defecto |
|---|---|---|
| Reescrituras por capítulo | Al agotarse, aceptación de la última versión con aviso | 2 |
| Capítulos | La escaleta que lo viole se devuelve al interrogador | 3–30 |
| Palabras por capítulo (objetivo) | Ídem | 1.500–4.000 |
| **Presupuesto de coste** por novela | Aviso al usuario al 80 %; al 100 %, **parada limpia**: el estado queda consistente y la novela es reanudable con más presupuesto | configurable; obligatorio fijarlo |
| Fallo técnico de un agente (error de red, respuesta vacía o que no cumple el contrato) | Hasta 3 reintentos del mismo paso; si persiste, parada limpia con el error en el Registro y en el Estado | 3 |

"Parada limpia" significa: ningún artefacto a medias marcado como válido, Estado actualizado con el motivo, mensaje claro al usuario de cómo reanudar.

### 6.4 Progreso

Durante la fase 2 el harness muestra, como mínimo: capítulo en curso y total, intento, veredicto de cada revisión con motivo resumido, coste acumulado frente al presupuesto, y cualquier aviso (aceptación por agotamiento, 80 % de presupuesto).

---

## 7. Parámetros configurables

Todos con valor por defecto; el usuario puede cambiarlos al arrancar una novela nueva. Una vez aprobada la escaleta, los límites de tamaño quedan congelados para esa novela.

- Mínimo y máximo de capítulos.
- Rango de longitud objetivo por capítulo.
- Tolerancia de longitud del revisor (±20 %).
- Número máximo de reescrituras por capítulo.
- Presupuesto de coste.
- Número de reintentos ante fallo técnico.

---

## 8. Criterios de aceptación (verificación manual)

No hay modo de ejecución desatendido; estas comprobaciones las hace una persona.

1. **Novela completa.** Con una idea sencilla y una escaleta de 3 capítulos de 1.500 palabras, el programa termina con: biblia, escaleta, 3 capítulos aprobados con sus resúmenes e informes, manuscrito e informe global. Cada capítulo cumple su entrada de la escaleta y no contradice los anteriores.
2. **Interrogatorio.** El interrogador hace preguntas pertinentes, propone el cierre por iniciativa propia y no arranca la escritura hasta la confirmación. Si el usuario pide un cambio, la escaleta presentada después lo refleja.
3. **Rechazo y reescritura.** Forzando un fallo (p. ej. una entrada de escaleta imposible de cumplir con la biblia), el revisor rechaza con problemas concretos, el escritor reescribe, y tras 2 reescrituras el harness acepta con aviso visible en el progreso y en el Registro.
4. **Reanudación.** Interrumpiendo la ejecución durante el capítulo 2, al relanzar sobre la misma carpeta el capítulo 1 no se regenera y el capítulo 2 se retoma.
5. **Presupuesto.** Con un presupuesto deliberadamente bajo, aparece el aviso al 80 % y la parada limpia al 100 %; al relanzar con más presupuesto la novela continúa.
6. **Permisos.** Ningún agente ha modificado artefactos fuera de su zona: la biblia y la escaleta son idénticas antes y después del bucle; cada capítulo aprobado es idéntico al final.
7. **Registro.** Para cualquier capítulo se puede reconstruir desde el Registro qué agentes se invocaron, cuántas veces, con qué veredicto y coste.

---

## 9. Pendiente para `specs/implementation.md`

Decisiones deliberadamente no tomadas aquí:

- Lenguaje, runtime y SDK/harness concreto.
- Modelo(s) LLM por agente y cómo se mide el coste.
- Formato de cada artefacto en disco (Markdown, JSON, YAML…) y estructura exacta de la carpeta.
- Mecanismo concreto de restricción de escritura por agente.
- Forma de la interfaz de terminal.
- Cómo se pasan los parámetros configurables.
