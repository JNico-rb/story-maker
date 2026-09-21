# Taxonomía de verificación

Dos familias de técnicas y un marco de clasificación. Elige **una técnica** y **una letra** por elemento verificado.

Cada técnica lleva su **fuente** —la referencia canónica de la literatura, para citar o para desempatar un término— y **en este proyecto**, la sección de `docs/verification.md` donde ya está razonada. Esa columna importa: cuatro técnicas están **descartadas con motivo escrito**, y proponerlas de nuevo sin leer el motivo es reabrir una decisión cerrada.

Las URLs se verificaron una a una el 2026-09-21. Si añades una técnica, verifica su fuente antes de escribirla; no inventes enlaces.

> El nombre de técnica se da en inglés porque es como aparece en la literatura. El término válido para escribir specs y docs es el del encabezado de su sección en `docs/verification.md`, que manda sobre este fichero: si divergen, el documento gana y esta taxonomía está desactualizada.

## 1. Verificación de producto (¿el código es correcto?)

| Técnica | Definición | Fuente | En este proyecto |
|---|---|---|---|
| **Type checking** | Comprobación automática de que los valores se usan de forma consistente con lo que las operaciones esperan de ellos (p. ej. nunca pasar un string donde se requiere un número) | [Type system — Wikipedia](https://en.wikipedia.org/wiki/Type_system) | §3.1, clase A |
| **Static analysis / SAST** | Escanear el código fuente sin ejecutarlo, buscando coincidencias con patrones conocidos como malos (vulnerabilidades, code smells, antipatrones) | [Static program analysis — Wikipedia](https://en.wikipedia.org/wiki/Static_program_analysis) | §3.2, clase A |
| **Symbolic execution** | Ejecutar el código con entradas simbólicas para derivar, mediante un solver SMT, las condiciones exactas y los contraejemplos concretos que lo romperían | [Symbolic execution — Wikipedia](https://en.wikipedia.org/wiki/Symbolic_execution) | §3.3, clase A — sobre la aritmética de factibilidad |
| **Formal verification / theorem proving** | Demostrar matemáticamente que el código satisface una especificación para *todas* las entradas posibles, no solo las probadas o exploradas | [Formal verification — Wikipedia](https://en.wikipedia.org/wiki/Formal_verification) | §3.4 — **descartada**: la cubren las propiedades a una fracción del coste |
| **Unit / integration testing** | Comprobar el comportamiento contra entradas de ejemplo concretas y salidas esperadas | [Unit testing — Wikipedia](https://en.wikipedia.org/wiki/Unit_testing) | §3.5, clase T |
| **Property-based testing** | Especificar una propiedad general que debe cumplirse para cualquier entrada, y generar muchas entradas automáticamente buscando una violación | [QuickCheck — Claessen & Hughes, 2000](https://dl.acm.org/doi/10.1145/351240.351266) | §3.6, clase T — el método de mayor rendimiento aquí |
| **Mutation testing** | Introducir bugs pequeños a propósito para comprobar si la suite de tests existente realmente los caza | [Mutation testing — Wikipedia](https://en.wikipedia.org/wiki/Mutation_testing) | §3.7 — sobre puerta dura y validador de config |
| **Contract testing** | Verificar que la interfaz (forma de request/response) entre dos servicios se mantiene consistente, con independencia de las tripas de cada lado | [Contract Test — Martin Fowler](https://martinfowler.com/bliki/ContractTest.html) | §3.8, clase T |

## 2. Verificación de proceso (¿el agente se comporta de forma fiable?)

| Técnica | Definición | Fuente | En este proyecto |
|---|---|---|---|
| **Runtime observability / tracing** | Instrumentar un agente para que su trayectoria real (llamadas a herramientas, tokens, latencia, errores) sea visible y consultable a posteriori | [Observability primer — OpenTelemetry](https://opentelemetry.io/docs/concepts/observability-primer/) | §4.1 — cimiento: sin trazas, el resto de §4 es opinión |
| **Evals** | Tests estructurados del comportamiento de un modelo o agente contra un dataset y un método de puntuación: golden-dataset, LLM-as-judge, task-completion, adversarial, live/online | [HELM — Liang et al., 2022](https://arxiv.org/abs/2211.09110) | §4.2, clase T o I según se puntúe |
| **Sandboxed execution** | Ejecutar el código del agente en un entorno aislado (contenedor, microVM) para que una acción mala falle sin consecuencias en vez de llegar a producción | [Sandbox (computer security) — Wikipedia](https://en.wikipedia.org/wiki/Sandbox_(computer_security)) | §4.3 — aplicabilidad baja; el riesgo real es el bucle sin techo |
| **Guardrails** | Políticas o filtros que restringen qué acciones o salidas puede producir un agente, *antes* de que actúe | [AI Risk Management Framework — NIST](https://www.nist.gov/itl/ai-risk-management-framework) | §4.4 — ya existen en el diseño sin ese nombre |
| **Human-in-the-loop review** | Una persona aprueba, rechaza o edita las acciones de alta consecuencia, y esa decisión se realimenta como señal | [Human-in-the-loop — Wikipedia](https://en.wikipedia.org/wiki/Human-in-the-loop) | §4.5 — **descartada en ejecución**; se desplaza a tiempo de construcción |
| **Multi-agent verification** | Critic/verifier (un segundo modelo revisa al primero), self-consistency (voto mayoritario entre repeticiones), debate (dos modelos discuten y un juez decide), reflection (autocrítica y revisión), ensembles | [AI Safety via Debate — Irving, Christiano & Amodei, 2018](https://arxiv.org/abs/1805.00899) | §4.6 — presente ya en el diseño; el **debate, no adoptado** |
| **CI/CD integration** | Pasar los cambios generados por agentes por el mismo pipeline, tests y revisión que el código humano, más etiquetado de procedencia | [Continuous integration — Wikipedia](https://en.wikipedia.org/wiki/Continuous_integration) | §4.7 — define qué entra en cada cambio y qué no |
| **Progressive rollout** | Desplegar un cambio tras un feature flag a un pequeño porcentaje del tráfico, monitorizado antes del despliegue completo | [Feature toggle — Wikipedia](https://en.wikipedia.org/wiki/Feature_toggle) | §4.8 — adaptado: lote fijo de ejecuciones de referencia |
| **Red-teaming / adversarial testing** | Sondear deliberadamente en busca de fallos bajo un modelo de amenaza adversarial (prompt injection, mal uso de herramientas, goal drift, exfiltración), no solo el error ordinario | [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) | §4.9 — el adversario aquí es quien escribe el prompt |
| **Model checking** | Explorar exhaustivamente los estados y transiciones alcanzables de un agente para verificar invariantes (p. ej. «nunca borrar antes de hacer backup») | [Model checking — Wikipedia](https://en.wikipedia.org/wiki/Model_checking) | §4.10 — el orquestador es una máquina de estados pequeña y real |

## 3. Marco de clasificación (Trust Spec)

Una letra por requisito. La letra dice **cómo** se gana la confianza, no **cuánta** hay. Referencia general: [Verification and validation — Wikipedia](https://en.wikipedia.org/wiki/Verification_and_validation). Desarrollo en `docs/verification.md` §2.

- **T — Test** — verificado ejecutando el sistema contra entradas concretas.
- **A — Analysis** — verificado por razonamiento estático: tipos, SAST, symbolic execution o demostración formal.
- **I — Inspection** — verificado por un humano o un modelo crítico que lo lee y lo juzga.
- **D — Demonstration** — verificado observando el funcionamiento correcto en un escenario realista (staging, sandbox).
- **U — Unverifiable / Accepted Risk** — no aplica ningún método, o no compensa el coste; se nombra explícitamente en vez de dejarlo como una asunción silenciosa.

## Correspondencia técnica → clase (por defecto)

| Técnica | Clase |
|---|---|
| Type checking, SAST, symbolic execution, formal verification, model checking, guardrails | A |
| Unit/integration, property-based, mutation, contract testing, evals de golden-dataset y task-completion | T |
| Human-in-the-loop, LLM-as-judge, critic/verifier, reflection, code review | I |
| Sandboxed execution, progressive rollout, observability/tracing, red-teaming en staging | D |

Esta tabla es el punto de partida, no una regla. Una eval adversarial ejecutada en staging es `D`; la misma eval en CI es `T`. Justifica la letra cuando te apartes de la tabla.
