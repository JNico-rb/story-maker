# verification.md

Catálogo de métodos de verificación aplicables a esta solución: cómo se comprueba que **el código es correcto** y que **el sistema de agentes se comporta de forma fiable**. El vocabulario está en `definitions.md`; las decisiones de diseño, en `architecture.md`; las razones de dominio, en `domain-knowledge.md`.

---

## 1. Qué verifica este documento y qué no

Conviene no confundir dos cosas que en este proyecto se parecen mucho:

| Objeto | Pregunta | Dónde vive |
|---|---|---|
| **La obra generada** | ¿Es buena y coherente esta novela? | Marco de calidad — las cuatro puertas (`architecture.md` §4) |
| **El sistema que la genera** | ¿Funciona el código? ¿Se comporta el agente como debe? | Este documento |

Las puertas son **parte del producto**: se ejecutan en cada escena, en producción, y son código que también hay que verificar. Los métodos de este documento son **parte del desarrollo**: se ejecutan sobre el sistema, no sobre el manuscrito.

> **Test de frontera:** si el fallo que detecta el método aparece en el informe de ejecución de una novela concreta, es una puerta de calidad. Si aparece en CI, es verificación de sistema.

Hay un caso que cruza la frontera y es el más importante del documento: la **puerta dura** y el **validador de config** son código determinista cuyo fallo silencioso invalida todas las novelas a la vez. Son el objetivo prioritario de los métodos de la §3.

---

## 2. Marco de clasificación (Trust Spec)

Todo requisito, invariante o componente recibe **una letra**. La letra dice *cómo* se gana la confianza, no *cuánta* confianza hay.

| Clase | Nombre | Se verifica… | Ejemplo en este sistema |
|---|---|---|---|
| **T** | Test | Ejecutando el sistema con entradas concretas | El validador de config rechaza `capitulos = 0` |
| **A** | Analysis | Razonando estáticamente: tipos, SAST, ejecución simbólica, prueba formal | El aplicador de deltas nunca recibe un estado nulo |
| **I** | Inspection | Leyendo y juzgando: una persona o un modelo crítico | La rúbrica de la puerta de juicio mide lo que dice medir |
| **D** | Demonstration | Observando la operación correcta en un escenario realista | Una ejecución completa de prompt vacío termina y produce informe |
| **U** | Unverifiable | No hay método aplicable, o no compensa su coste | La plausibilidad especulativa de un novum inventado |

Dos reglas de uso:

- **U es una decisión, no un olvido.** Se escribe en el documento con nombre y motivo. Un requisito sin letra es un supuesto silencioso, y los supuestos silenciosos son los que rompen los sistemas autónomos.
- **La letra no es un ascenso.** A no es «mejor» que T. Un invariante aritmético se prueba por análisis; un flujo de extremo a extremo, por demostración. Aplicar el método caro donde basta el barato es el mismo error económico que ordenar mal las puertas.

---

## 3. Verificación de producto: ¿es correcto el código?

### 3.1 Comprobación de tipos — clase A

Comprobación automática de que los valores se usan de forma consistente con lo que las operaciones esperan: nunca un texto donde se requiere un número.

- **Dónde aplica:** en todo el backend, y especialmente en las fronteras entre capas —`ContratoDeBrief`, `DeltaDeEstado`, `EstadoDelMundo`, `Criterio`— donde una estructura mal formada se propaga en silencio durante ochenta escenas.
- **En este stack:** Python con anotaciones y comprobador estricto; modelos de datos validados en tiempo de ejecución en los bordes (entrada HTTP y salida de modelo). TypeScript en modo estricto en el frontend.
- **Límite:** un tipo dice que el campo `orden` es un entero, no que valga 1, 2 o 3. Los tipos cubren forma, no dominio.

### 3.2 Análisis estático / SAST — clase A

Escaneo del código fuente sin ejecutarlo, contrastándolo con patrones conocidos como malos: vulnerabilidades, *code smells*, antipatrones.

- **Dónde aplica:** el sistema recibe texto libre del usuario y lo incorpora a prompts. Interesa el escaneo de secretos, de construcción dinámica de consultas y de manejo de rutas de fichero al escribir el manuscrito.
- **Valor real en este proyecto:** medio en seguridad —la superficie es pequeña—, alto en higiene: detectar una captura genérica de excepciones o un resultado ignorado en el orquestador vale más que cualquier regla de inyección.
- **Límite:** reconoce patrones, no intenciones. No detectará que la puerta dura se saltó una comprobación.

### 3.3 Ejecución simbólica — clase A

Ejecutar el código con entradas simbólicas y derivar, mediante un solucionador SMT, las condiciones exactas que lo rompen, con contraejemplo concreto.

- **Dónde aplica:** en la aritmética de factibilidad (`architecture.md` §6.2). Palabras totales, capítulos, escenas por capítulo y densidad narrativa forman un sistema de desigualdades con un espacio de entrada acotado; es exactamente el tipo de código donde el solucionador encuentra el caso límite que nadie escribiría a mano.
- **Coste:** alto en esfuerzo de integración, muy bajo en superficie objetivo. Se aplica a dos o tres funciones, no al sistema.
- **Límite:** inútil sobre código que llama a un modelo. Todo lo que cruza una frontera no determinista queda fuera.

### 3.4 Verificación formal / demostración de teoremas — clase A

Demostrar matemáticamente que el código satisface una especificación para *todas* las entradas posibles, no solo para las probadas o exploradas.

- **Dónde aplicaría:** el invariante 5 —`EstadoDelMundo` en la escena *n* es la aplicación ordenada de los deltas 1..*n*−1— es una propiedad de plegado sobre una secuencia, y admite prueba.
- **Decisión:** **no se adopta.** El mismo invariante se cubre casi por completo con pruebas basadas en propiedades (§3.6) a una fracción del coste, y el margen restante no justifica introducir un lenguaje de especificación en un proyecto de este tamaño.
- **Se registra aquí porque la alternativa elegida debe ser explícita**, no porque el método se haya pasado por alto.

### 3.5 Pruebas unitarias y de integración — clase T

Comprobación del comportamiento frente a entradas de ejemplo concretas y salidas esperadas.

- **Unitarias:** los siete componentes de código (`architecture.md` §8.5). Son deterministas y no necesitan modelo: se prueban como cualquier función.
- **Integración:** el flujo por fases con los agentes sustituidos por dobles. Verifica el orquestador —orden de puertas, punto de control por escena, reanudación tras caída— sin gastar presupuesto de modelo.
- **Regla:** ninguna prueba del pipeline llama a un modelo real. Si necesita al modelo, no es una prueba: es una eval (§4.2).

### 3.6 Pruebas basadas en propiedades — clase T

Se enuncia una propiedad general que debe cumplirse para cualquier entrada y se generan muchas entradas automáticamente buscando una violación.

Es el método de mayor rendimiento en este sistema, porque los invariantes de `architecture.md` §7 **ya están escritos como propiedades**:

| Invariante | Propiedad generable |
|---|---|
| 1 | Para todo grafo de consecuencias generado, toda consecuencia es alcanzable desde algún novum |
| 3 | Para toda secuencia de escenas, ningún personaje actúa sobre información ausente de su estado epistémico |
| 5 | Para toda secuencia de deltas, aplicarlos en orden *n* veces equivale al estado de la escena *n* |

- **En este stack:** generadores de propiedades en Python para el backend; equivalente en TypeScript si alguna lógica de forma acaba en el frontend.
- **Límite:** la propiedad solo es tan buena como su enunciado. Una propiedad trivialmente cierta pasa siempre y no informa de nada.

### 3.7 Pruebas de mutación — clase T aplicada sobre las propias pruebas

Introducir deliberadamente pequeños fallos en el código para comprobar si la batería de pruebas existente los detecta.

- **Dónde aplica:** de forma prioritaria sobre la **puerta dura** y el **validador de config**. Es el punto donde una prueba que no prueba nada cuesta más caro: una puerta que siempre acepta pasa desapercibida indefinidamente, porque su salida correcta y su salida rota se parecen.
- **Coste:** alto en tiempo de ejecución. Se ejecuta en cadencia semanal o bajo demanda, nunca en cada *commit*.
- **Métrica de salida:** mutantes supervivientes en las rutas de rechazo, no porcentaje global de cobertura.

### 3.8 Pruebas de contrato — clase T

Verificar que la interfaz entre dos servicios —forma de petición y respuesta— se mantiene consistente, con independencia de los internos de cada lado.

- **Dónde aplica:** la frontera FastAPI ↔ React del contrato mínimo de API (`architecture.md` §9.4). El frontend es delgado y la especificación OpenAPI se genera sola, así que el contrato puede derivarse del esquema en vez de mantenerse a mano.
- **Caso que justifica el método:** el flujo SSE de progreso. Un cambio en el nombre de un campo de evento rompe la vista de avance sin romper ninguna prueba de backend.
- **Ampliación útil:** tratar también como contrato el **esquema de salida estructurada de cada llamada a modelo**. Es la misma clase de frontera y la que más se mueve.

---

## 4. Verificación de proceso: ¿se comporta el agente de forma fiable?

### 4.1 Observabilidad y trazas en ejecución — clase D

Instrumentar el agente para que su trayectoria real —llamadas a herramientas, tokens, latencia, errores— sea visible y consultable a posteriori.

- **Por qué es el cimiento:** sin trazas, todo lo demás de esta sección es opinión. Las evals no tienen de dónde salir, el red-teaming no se puede reproducir y el presupuesto consumido no se puede atribuir.
- **Dónde aplica:** una traza por ejecución, con un tramo por escena y un subtramo por puerta. La unidad de correlación es el `run_id` del contrato de API.
- **Relación con el diseño:** el **informe de ejecución** (`architecture.md` §8.10) es la vista de producto sobre estos datos. La traza es la vista de ingeniería. Comparten origen y no deben duplicar el registro.

### 4.2 Evals — clase T o I según el método de puntuación

Pruebas estructuradas del comportamiento del modelo o del agente frente a un conjunto de datos y un método de puntuación.

| Tipo de eval | Qué mide aquí | Clase |
|---|---|---|
| **Conjunto dorado** | Extractor de brief: prompts con su `ContratoDeBrief` esperado | T |
| **Modelo como juez** | Crítico de oficio y crítico de canon frente a escenas con defectos sembrados | I |
| **Completitud de tarea** | Porcentaje de ejecuciones que llegan a manuscrito sin intervención | D |
| **Adversarial** | Prompts contradictorios, imposibles o casi vacíos | T |
| **En vivo** | Muestreo de ejecuciones reales puntuadas a posteriori | I |

Dos consecuencias directas del diseño:

- **Todo evaluador declara su fiabilidad conocida** (`architecture.md` §4.2). Esa fiabilidad se mide precisamente aquí: la eval del crítico *es* la calibración del juez. Un juez sin eval es ruido con formato de métrica.
- **El caso de prompt casi vacío** (`architecture.md` §8.11) es el primer conjunto de evals que hay que construir, no el último. Es el que más se usará y el que menos margen deja.

### 4.3 Ejecución en sandbox — clase D

Ejecutar el código del agente en un entorno aislado —contenedor, microVM— para que una acción mala falle sin alcanzar producción.

- **Aplicabilidad en este proyecto: baja.** Los agentes no ejecutan código arbitrario ni tocan sistemas externos; escriben Markdown y consultan canon. La superficie que justifica una microVM no existe.
- **Lo que sí aplica:** aislamiento de sistema de ficheros y de red para los *workers*, y cuota de presupuesto por ejecución. El riesgo real no es la acción destructiva, es el **agente en bucle sin techo** (`architecture.md` §9.5).

### 4.4 Guardarraíles — clase A en tiempo de ejecución

Políticas o filtros que restringen qué acciones o salidas puede producir un agente, **antes** de que actúe.

- **Ya existen en el diseño y no se llaman así:** la puerta 0 es un guardarraíl sobre config; el bloqueo ante imposible —«nunca degradar»— es un guardarraíl sobre el orquestador; el límite de tiempo por agente es un guardarraíl sobre el bucle.
- **Lo que falta declarar explícitamente:** techo de reintentos por escena, techo de tokens por ejecución y prohibición de escritura fuera del directorio de la ejecución.
- **Distinción que importa:** el guardarraíl impide; la puerta juzga. Un guardarraíl que necesita un modelo para decidir es una puerta mal colocada.

### 4.5 Revisión con humano en el bucle — clase I

Una persona aprueba, rechaza o edita las acciones de alta consecuencia, y la decisión se realimenta como señal.

- **Está descartada en ejecución por decisión cerrada:** autonomía total de extremo a extremo (`architecture.md` §8.1). El frontend no tiene pantallas de aprobación por diseño.
- **Sigue aplicando en desarrollo, y es imprescindible:** las etiquetas del conjunto dorado, la rúbrica de la puerta de juicio y el catálogo de tropos curado los produce y los revisa una persona. La supervisión no desaparece: **se desplaza del tiempo de ejecución al tiempo de construcción**.
- **Cómo se realimenta:** las ejecuciones puntuadas a mano entran en el conjunto de evals; no reentrenan nada.

### 4.6 Verificación multiagente — clase I

Un crítico o verificador (un segundo modelo comprueba al primero), autoconsistencia (voto mayoritario entre repeticiones), debate (dos modelos discuten y un juez decide), reflexión (autocrítica y revisión) y conjuntos (varios modelos combinados).

Es la familia con **mayor presencia ya en el diseño**:

| Patrón | Dónde está en el diseño |
|---|---|
| Crítico / verificador | Crítico de canon y crítico de oficio, separados del escritor |
| Autoconsistencia | Selección de novum: N candidatos puntuados, no uno pedido |
| Reflexión | Editor separado del escritor, con los defectos como entrada |
| Verificación reconstructiva | Verificador de contrato: paráfrasis contrastada con el prompt original |

- **Patrón no adoptado:** el debate. Añade dos llamadas y un juez a cambio de una mejora que en tareas de coherencia narrativa no está demostrada.
- **Regla que sostiene todo lo anterior:** el crítico nunca es el autor. Escritor y editor se mantienen separados precisamente para poder medirlos por separado.

### 4.7 Integración en CI/CD — clase T

Encaminar los cambios generados por un agente por el mismo *pipeline*, pruebas y revisión que el código escrito por una persona, con marcado de procedencia.

- **Qué entra en CI en cada cambio:** tipos, análisis estático, unitarias, propiedades y contrato de API. Rápido y determinista.
- **Qué no entra en cada cambio:** mutación, ejecución simbólica y evals con modelo. Cadencia programada o disparo manual, por coste y por no determinismo.
- **Procedencia:** los cambios de este repositorio generados por agente se marcan en el *commit*. Es trazabilidad, no desconfianza.

### 4.8 Despliegue progresivo — clase D

Publicar un cambio tras una bandera de funcionalidad, dirigido a un porcentaje pequeño de tráfico y vigilado antes de la liberación completa.

- **Aplicabilidad actual: baja.** Sin tráfico de producción no hay porcentaje que segmentar.
- **Adaptación que sí tiene sentido desde el primer día:** ejecutar el cambio de prompt, rúbrica o umbral sobre un lote fijo de ejecuciones de referencia y comparar informes antes de adoptarlo. Es el mismo principio —exposición limitada y comparación previa— con el lote de evals en el papel del porcentaje de tráfico.
- **Candidatos naturales a bandera:** umbral de densidad narrativa y umbrales de los criterios de juicio, ambos decisiones abiertas (`architecture.md` §10.2).

### 4.9 Red-teaming / pruebas adversarias — clase T

Sondear deliberadamente en busca de fallos bajo un modelo de amenaza adversario —inyección de prompt, cadenas de uso indebido de herramientas, deriva de objetivos, exfiltración— y no solo el error ordinario.

El modelo de amenaza de este sistema es **peculiar y hay que enunciarlo**: no hay datos de terceros, ni herramientas con efectos externos, ni multiusuario. El adversario realista es el **usuario que escribe el prompt**.

| Vector | Qué se prueba |
|---|---|
| Inyección vía prompt | Instrucciones en el prompt de novela que intentan redirigir al orquestador o a un crítico |
| Deriva de objetivos | Ejecuciones largas en las que el manuscrito se aleja progresivamente del contrato |
| Abuso de recursos | Prompts que maximizan reintentos y agotan el presupuesto |
| Degradación encubierta | Casos en los que el sistema debería bloquear y en su lugar produce algo peor |

El último es el que más importa: la decisión cerrada es **bloquear, nunca degradar**, y una degradación silenciosa es indistinguible del éxito para quien solo lee el manuscrito.

### 4.10 Comprobación de modelos — clase A

Explorar exhaustivamente los estados y transiciones alcanzables del agente para verificar invariantes del tipo «nunca X antes de Y». Es el análogo, en flujos multiagente, de la ejecución simbólica sobre código.

- **Dónde aplica:** el orquestador es una máquina de estados finita y pequeña —fases, puertas, veredictos, punto de control, reanudación— y por tanto es comprobable de verdad, no metafóricamente.
- **Invariantes candidatos:**
  - Ninguna escena se genera antes de aplicar el delta de la anterior (invariante 5).
  - Ninguna escena aceptada omite la actualización de canon, estado y resumen (invariante 6).
  - Ninguna ruta alcanza la puerta de juicio sin haber pasado la puerta dura.
  - Ninguna reanudación desde punto de control duplica un delta ya aplicado.
- **Nota:** el último solo se rompe al reanudar, que es precisamente el camino que las pruebas manuales no recorren. Es el argumento a favor del método.

---

## 5. Cobertura: qué método verifica qué

| Elemento del diseño | Método principal | Clase |
|---|---|---|
| Validador de config | Unitarias + ejecución simbólica + mutación | T, A |
| Aritmética de factibilidad (puerta 0) | Ejecución simbólica | A |
| Puerta dura | Propiedades + mutación | T |
| Invariantes 1, 3 y 5 | Pruebas basadas en propiedades | T |
| Invariantes 2, 4 y 6 | Comprobación de modelos sobre el orquestador | A |
| Orquestador, fases y reanudación | Integración con dobles + comprobación de modelos | T, A |
| Extractor de brief | Eval de conjunto dorado | T |
| Verificador de contrato | Eval adversaria + revisión humana de la muestra | T, I |
| Selector de novum | Eval contra el catálogo de tropos + inspección | T, I |
| Críticos de canon y de oficio | Eval de juez calibrada con defectos sembrados | I |
| Agentes escritor y editor | Evals + trazas + inspección muestreada | I, D |
| Contrato de API y SSE | Pruebas de contrato derivadas del esquema | T |
| Fronteras de datos entre capas | Tipos + validación en los bordes | A |
| Ejecución completa de prompt casi vacío | Demostración de extremo a extremo | D |
| Presupuesto y límites de tiempo | Guardarraíles + trazas | A, D |
| Plausibilidad especulativa del novum | — | **U** |
| Calidad literaria de la prosa | Juicio con rúbrica, sin patrón de referencia | **U** parcial |
| Compromisos no verificables | Declarados como tales en el informe | **U** |

---

## 6. Riesgo aceptado (U), por escrito

1. **La plausibilidad especulativa no se verifica, se aproxima.** No existe patrón de referencia para «este futuro es creíble». Lo que se comprueba es la propiedad sustituta: alcanzabilidad en el grafo causal. Se acepta la brecha entre ambas.
2. **La calidad literaria depende de un juez con fiabilidad conocida pero imperfecta.** Se mide su acuerdo con etiquetas humanas; no se elimina su error.
3. **Los compromisos no verificables siguen sin método.** La política es no fingir: o se convierten en criterio con rúbrica, o se descartan del contrato, o se listan en el informe como no verificados.
4. **La ausencia de supervisión en ejecución no se compensa del todo.** El informe de ejecución es el sustituto funcional del revisor, y un sustituto funcional no es un equivalente.
5. **La verificación formal no se adopta.** Decisión de coste, registrada en §3.4.

---

## 7. Orden de adopción

No todo vale lo mismo al principio. El orden sigue el mismo criterio económico que las puertas: primero lo barato que detecta lo caro.

1. **Tipos, análisis estático, unitarias y contrato de API en CI.** Coste casi nulo, cobertura inmediata de las fronteras.
2. **Propiedades sobre los invariantes 1, 3 y 5.** Están escritos como propiedades; traducirlos es mecánico.
3. **Trazas por ejecución.** Sin ellas no hay evals posibles.
4. **Evals del extractor de brief y del caso de prompt casi vacío.** Es el caso que más se usará.
5. **Guardarraíles explícitos de presupuesto y reintentos.** Antes de la primera ejecución larga sin vigilancia.
6. **Mutación sobre la puerta dura y el validador de config.** Cuando ya haya pruebas que merezca la pena auditar.
7. **Comprobación de modelos del orquestador y ejecución simbólica de la factibilidad.** Cuando la máquina de estados y la aritmética estén estables.
8. **Red-teaming y lote de referencia para cambios de prompt o umbral.** Cuando exista una versión que defender.
