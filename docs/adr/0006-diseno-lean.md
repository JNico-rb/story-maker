# V2 construye el diseño lean: lo más fácil posible, tan difícil como haga falta

Status: accepted, 2026-09-24

Es la spec inicial de V2: qué se decidió construir y por qué, escrita el 2026-09-24, antes de cualquier código del producto. Cada decisión, con sus opciones y su criterio, está en [architecture.md §18](../architecture.md); aquí va el conjunto y su razón.

## Contexto

[ADR 0003](0003-pivote-al-encargo.md) fijó el producto el 2026-09-23: el encargo (`project-constraints.md`) con el tema post-IA. Su diseño —nueve roles, mundo en grafo causal, RAG de dos colecciones con cuotas, API y worker separados, SSE, reanudación por tramos— costaba entre 45 y 60 días-persona. [ADR 0005](0005-entrega-v1-en-24-horas.md) lo recortó a una V1 de una sola spec en una rama, V2-test, que se abandonó. V2 vuelve a empezar solo con los docs: nada del código de V2-test es referencia ([ADR 0002](0002-v2-desde-cero.md)).

## Decisión

El producto es el de ADR 0003: una entrevista que acaba en una novela de 10 capítulos de 1.000–1.500 palabras, ambientada en el presente post-IA, que se mantiene viva tras publicarla. Cambian los mecanismos:

1. **Siete roles:** entrevistador, extractor, planner, writer, editor, juez y revisor visual. El editor critica con rúbrica y registra usos de hechos, eventos y resumen; no reescribe: el writer reescribe con los defectos.
2. **Flujo:** entrevista → brief confirmado → planificación (un novum con fecha y 2–4 consecuencias, reparto, outline de 10 capítulos × 3–6 beats, StyleSheet) → producción por capítulo (writer, hook de policy, hook de validación, editor, veredicto por código, punto de control) → gate → versión publicada.
3. **Story bible en SQLite**, copiada por versión: personajes, lugares, hechos con sus usos por capítulo y la cronología que alimenta Lean. Esquema completo con `create_all`, sin migraciones.
4. **Contexto por construcción** (residentes fijos por rol) y **RAG híbrido de una colección** (`CanonCards`: BM25 sobre FTS5 + denso con `sqlite-vec`, RRF, corte temporal, sin re-ranking).
5. **Un proceso:** FastAPI con el worker como tarea asyncio, cola FIFO global y una ejecución activa; progreso por sondeo. El techo de 100.000 tokens es un contador global en memoria con reserva por sesión de rol. Se reanuda solo desde `interrupted`.
6. **Gate de publicación:** validadores de novela en orden económico (deterministas → Lean ∥ juez → revisión visual → PDF); un fallo atribuible a capítulos los reescribe, con ciclos acotados.
7. **Cambios del lector:** el planner propone, el código calcula los capítulos afectados (usos del hecho ∪ coincidencia literal del valor antiguo), el lector confirma con código, se regeneran solo esos y la versión nueva conserva la anterior. La edición manual lleva lint en vivo y pasa el gate completo, Lean incluido.
8. **Validadores de las cuatro familias**, cada uno con nombre, punto de ejecución y score en Langfuse: programáticos (schemas, nombres exactos, longitud, elementos obligatorios, prohibidas, revisión visual por browser MCP, PDF), semánticos (rúbrica del editor, juez, revisión humana), formal de la historia (Lean, T1–T5) y formal del sistema (TLA+ `Harness.tla` y `Regenerations.tla`, en CI).
9. **Todo lo opcional del encargo:** servidor MCP con FastMCP (lectura, `request_change` y `confirm_change`), linters de prosa heurísticos, linter de edición manual, demostraciones generales en Lean, TLA+ de regeneraciones simultáneas, login con JWT y bcrypt, y auditoría de seguridad por agente.
10. **Sin gasto en APIs:** el LLM de todos los roles es el login de Claude Code de la máquina, con la suscripción de la organización (`LLM_PROVIDER=claude_login`, por defecto); `anthropic_compatible` apunta por configuración a cualquier endpoint compatible con Anthropic: su API, OpenRouter, Ollama o un proxy. El coste por novela son los tokens reales × el precio de lista de la API de Anthropic. Los servicios externos van en plan gratuito (Langfuse Hobby, GitHub Free); fastembed, Playwright y TLC corren en local, y ningún test ni la CI llaman a un modelo.

Se mantienen de ADR 0003: el Claude Agent SDK como runtime de todos los roles, la orquestación propia, «el código decide y el modelo propone», el extractor aislado con citas verificadas, los tres niveles de prohibidas, Langfuse con máscara y Lean en GitHub Actions ([ADR 0004](0004-lean-en-github-actions.md)).

## Por qué así

- **La máxima del proyecto: lo más fácil posible, tan difícil como haga falta.** La dificultad deliberada va solo en RAG, Langfuse, MCP, Agent SDK, Lean y TLA+, la tecnología que el curso evalúa. En todo lo demás se elige la opción más simple que cumple el encargo.
- **Cada recorte quita un mecanismo, no un requisito del encargo.** El encargo pide planner, writer y editor/critic: un editor que critica y registra los cubre sin dos sesiones más por capítulo, y writer y editor siguen separados porque el que escribe no se evalúa a sí mismo.
- **Un novum con pocas consecuencias.** En una novela de regalo el mundo es escenario ([domain-knowledge.md §3.2](../domain-knowledge.md)); el grafo causal y su invariante verificaban lo que el lector apenas ve.
- **Sin marcos.** El planner adapta el deseo dentro del mundo post-IA, así que todo lo narrado es verdad en la historia y T1–T5 lo cubren sin excepciones ([domain-knowledge.md §4.5](../domain-knowledge.md)).
- **Un proceso, un contador.** El techo es global; en un solo proceso es una variable en memoria, sin reconciliar dos cuentas.
- **Cero euros de créditos para APIs.** El login de Claude Code es el único LLM disponible sin gasto, y `anthropic_compatible` deja el cambio de proveedor en la configuración, sin tocar los roles. El coste va a precio de lista de la API porque es lo que costaría cada novela en producción, la cifra que pide la slide de presupuesto.
- **Lo que choca con el entorno se evita:** `create_all` en vez de Alembic (sin heads en conflicto entre carriles paralelos) y linters en Python puro en vez de spaCy (Smart App Control bloquea sus DLL).

## Fuera de alcance

Por el encargo: pagos, cuentas más allá del registro y el acceso, impresión física, ilustraciones, audio y despliegue en producción. Por decisión: grafo causal, restricciones y T6; marcos; segunda colección, cuotas por consumidor, prosa recuperada y deltas de estado; presupuesto en dinero que bloquea (el coste se registra); SSE; reanudación desde `blocked` y por tramos; Alembic; spaCy; CI de deriva del cliente de API; vista previa con cookie; una tercera especificación TLA+.

## Cómo se sabrá que funciona

Cada validador envía su resultado a Langfuse. Cinco briefs ficticios —el de ejemplo del README, uno infantil, uno de boda o aniversario, uno adversarial con inyección en el texto libre y uno de incoherencia temporal pensado para que solo Lean la detecte— dan la tabla brief × validador, generada desde SQLite y Langfuse. Una iteración de tuning se documenta con los resultados de antes y después y la versión de prompt de cada uno. Una persona revisa al menos una novela completa con la misma rúbrica que el juez para comparar ambos juicios ([verification.md §4.2](../verification.md)). `ejemplos/novela-ejemplo.pdf` es la evidencia de extremo a extremo.

## Consecuencias

- Los cuatro docs de referencia se reescriben al diseño lean con numeración nueva: en `architecture.md` las decisiones abiertas están en §17 y las cerradas en §18. ADR 0003 queda superada en parte y ADR 0005, entera.
- Las specs van en `specs/backend/NNN-nombre.md` (001–021, numeración global) y en `specs/frontend/`, con los números siguientes.
- Las aprobaciones de spec y plan se delegan en agentes, por decisión del usuario: `auditor` aprueba con gap cero y `verificador` cierra. El usuario solo atiende los escalados y lo que solo puede hacer una persona: la revisión humana, el vídeo de demo, las cuentas y la comprobación final.
- La suscripción tiene límites de uso. Alcanzar uno a mitad de una ejecución es un fallo del proveedor, no un intento: la ejecución queda `interrupted` y se reanuda desde el último punto de control cuando el límite se renueva, como mucho `max_resumes` veces.
- Cuatro carriles de Claude Code trabajan en worktrees hermanos: A núcleo de generación, B plataforma y observabilidad, C entrada y política, D formal y calidad. El checkout principal integra cada spec cerrada en V2 y ejecuta la suite completa. Cada contrato entre carriles nace con su doble en la spec más temprana que lo necesita.
