# Decisiones de la V1 (entrega en menos de 24 h)

Fichero de trabajo. Fuente única para escribir `specs/019-v1-entrega/`; se borra cuando la spec, su design y el ADR 0005 recojan su contenido. Tomadas por el usuario el 2026-09-23 y el 2026-09-24, tras la revisión de `.scratch/revision/2026-09-23.md`.

## Marco

- **Una sola spec**, `specs/019-v1-entrega/` (spec, design y plan), cumple `project-constraints.md` al pie de la letra con el diseño más simple que funciona. Las specs 001–018 y `docs/architecture.md` quedan como diseño completo (V2). La V1 remite a sus secciones cuando coincide y dice en qué simplifica. El ADR 0005 registra la decisión.
- **Prioridad:**
  - **Obligatorio** es lo que el encargo exige.
  - **Deseable** es lo que solo sirve a un opcional del encargo, o a algo que el encargo no pide.
  - Orden de ejecución: esqueleto de extremo a extremo → resto obligatorio → evals y docs → opcionales.
- **Nombres:** los términos, de `docs/definitions.md`; los identificadores, de su §12; los validadores, de `architecture.md` §10.2, cuando existan.
- **Stack** (`architecture.md` §14.1):
  - Backend: Python 3.12 con uv, FastAPI y uvicorn en un solo proceso, Pydantic v2, SQLite en WAL y Claude Agent SDK sobre OpenRouter.
  - Frontend: React + Vite, TypeScript estricto y pnpm 10.
  - Langfuse Cloud.
  - Lean 4 con Lake, solo en GitHub Actions (ADR 0004).
  - TLA+ con TLC, en local con JDK portable.
  - PDF con Playwright.
  - Se reutiliza lo que ya sirve del worktree de 001: `platform/sqlite.py`, `execution/settings.py`, `pyproject.toml` y `uv.lock`.

## Producto

1. **Entrevista.**
   - Página web de chat. El rol entrevistador pide nombre, edad, rasgos, recuerdos, género, tono y extensión, y las palabras o temas que no deben aparecer.
   - El cliente puede pegar texto libre. El rol extractor, aislado, saca de él hechos con cita literal; el código comprueba que cada cita existe en el texto y descarta las que no.
   - El texto libre es no confiable: nunca es instrucción. Un detector marca las frases dirigidas al sistema y las deja en el audit log.
   - El brief es un schema Pydantic validado por código: datos que faltan y al menos las contradicciones «edad frente a género o tono» y «recuerdo con edad mayor que la actual».
   - Confirma el cliente.
2. **Planificación.** El planner escribe la story bible inicial:
   - personajes con fecha de nacimiento;
   - lugares;
   - hechos (los del brief, marcados como elementos obligatorios);
   - un novum post-IA con fecha y 3–5 consecuencias, sin grafo causal;
   - el outline de 10 capítulos, con beats, elementos obligatorios asignados y eventos planificados (momento, personajes y lugar).
   Lo valida `outline`.
3. **Bucle por capítulo.**
   1. El writer entrega solo el texto.
   2. El hook de validación, `PostToolUse` sobre la tool de entrega, pasa `schema-salida`, `longitud-capitulo` (1.000–1.500 palabras), `nombres-exactos` y `palabras-prohibidas`. Un fallo vuelve al writer como lista de defectos, con límite de intentos.
   3. El crítico puntúa con la rúbrica del capítulo.
   4. Por debajo del umbral, el editor corrige, con límite de intentos.
   5. El registrador extrae el resumen, los usos de hechos y los eventos (momento, personajes y lugar), validados contra la story bible.
   6. Se acepta en una transacción, que es el punto de control.
   Si se agota un límite, la ejecución queda `blocked` con su informe. Contexto del writer: la story bible completa, los resúmenes de los capítulos anteriores, el capítulo anterior literal y el plan del capítulo. El RAG híbrido es Deseable.
4. **Gate de publicación.**
   1. Primero los deterministas sobre la novela entera: `elementos-obligatorios` contra la tabla de usos, `nombres-exactos` y `palabras-prohibidas`.
   2. Después `cronologia-lean`: la cronología sale de SQLite a JSON y va al workflow remoto de GitHub Actions. Su formato lo define `lean/README.md` del carril formal.
   3. Después el juez de novela: rúbrica de continuidad, tono, calidad narrativa (arco, coherencia de personajes, ritmo) y personalización natural, con puntuación por criterio y justificación.
   Un fallo de Lean o del juez vuelve al editor como feedback, en ciclos acotados. Si se agotan, `blocked`. Si pasa todo: versión nueva e inmutable, y PDF.
5. **Versiones y cambios del lector.**
   1. En la lectura web, el lector selecciona un fragmento y pide un cambio («el perro se llama Nala»).
   2. Se propone qué hecho cambia, con su valor antiguo y el nuevo.
   3. El cliente confirma.
   4. Los capítulos afectados son los de la tabla de usos más los que contienen el valor antiguo.
   5. Solo esos se regeneran, con los mismos validadores, y el gate pasa sobre la novela entera.
   6. Se publica la versión n+1 con los capítulos cambiados marcados, y la anterior se conserva y se puede leer.
6. **Memoria.**
   - Story bible en SQLite: personajes, lugares, hechos con los capítulos en que se usa cada uno, y la tabla de cronología (evento, momento, personajes y lugar).
   - Resúmenes por capítulo.
   - Punto de control por capítulo: al arrancar, una ejecución `running` pasa a `interrupted` y se reanuda desde el último capítulo aceptado.
7. **Harness.**
   - Roles: entrevistador, extractor, planner, writer, crítico, editor, registrador y juez. Cada uno es una sesión del Agent SDK.
   - Workspace `backend/harness_workspace/` con su `CLAUDE.md` y la skill `personalizacion-natural`, que usan el writer y el editor. Hay que excluir los `CLAUDE.md` de los directorios padre.
   - Tools propias con schema Pydantic y las integradas desactivadas.
   - Hook de policy (`PreToolUse`): lista blanca de tools por rol y prohibidas en los campos de texto narrativo.
   - Hook de validación del capítulo.
   - Límites de reintentos, turnos y tiempo.
   - Modelos por rol en `config.json`, con valores provisionales marcados como tales. Hechos medidos del SDK: `.claude/memory/` y `verification.md` §8, filas 11–14.
8. **Validadores**, cada uno con nombre, punto de ejecución y score en Langfuse:
   - programáticos: `schema-brief`, `citas-verificadas`, `schema-salida`, `outline`, `longitud-capitulo`, `nombres-exactos`, `palabras-prohibidas` y `elementos-obligatorios`;
   - semánticos: rúbrica del crítico, juez de novela, y revisión humana de una novela con la misma rúbrica, comparada con el juez;
   - formales: `cronologia-lean` en el gate y `harness-tla` en desarrollo y CI.
   Deseable: la revisión visual con browser MCP como validador del producto, `pdf-enlaces` y los linters de prosa.
9. **Guardarraíles.**
   - Palabras prohibidas en SQLite en tres niveles: global, cliente y novela.
   - Normalización: mayúsculas, acentos, plurales y variantes simples de género.
   - Se aplican en código a cada capítulo antes de aceptarlo y en el gate. Una coincidencia hace reescribir con límite; agotado, se detiene la ejecución y se informa.
   - Cada coincidencia va al audit log y a Langfuse.
   - Tests de cada nivel y de variante, con acento y con plural.
   - Audit log de toda decisión de la policy.
   - Techo de 100.000 tokens de entrada concurrentes: una cuenta global en memoria. Cada sesión reserva su estimación antes de abrirse y espera si no cabe.
10. **Observabilidad (Langfuse).**
    - Una sesión por novela.
    - Una traza por entrevista, por ejecución y por cambio.
    - Un span por sesión de rol, por llamada a tool y por validador.
    - Una generation por sesión de rol, con su uso exacto, su coste (uso × precio de `config.json`) y su latencia. El detalle por turno es Deseable.
    - Scores de todos los validadores, salvo TLC.
    - Prompts de los roles versionados en Langfuse: la ejecución anota la versión que usó.
11. **Frontend.**
    - Páginas: entrevista, progreso (por sondeo, sin SSE), mis novelas, lectura (portada con dedicatoria personalizada, índice navegable, capítulos, ficha de personajes y lugares con enlaces a los capítulos en que aparece cada uno, selector de versión y marcas de cambio) y petición de cambio.
    - Imagen corporativa: logotipo de `images/`, paleta y tipografía coherentes.
    - Una vista de impresión que Playwright convierte en el PDF.
    - Sin login en el núcleo: un cliente por defecto.
12. **CLI:** migrar; `example`, que reproduce el brief de ejemplo y deja `ejemplos/novela-ejemplo.pdf`; `evals`; reanudar; y subir prompts a Langfuse.
13. **Evals.**
    - Cinco briefs ficticios: el ejemplo; uno infantil; uno adversarial, con inyección en el texto libre; uno temporal, pensado para que solo Lean vea la incoherencia; y uno de prohibidas con variantes. El sexto brief y los marcos son Deseable.
    - Tabla por brief de validadores que pasan y fallan, con sus scores.
    - Una iteración de ajuste de prompt, antes y después, con la versión de prompt de cada resultado.
    - Revisión humana de una novela, comparada con el juez: diferencia absoluta media y acuerdo exacto.
14. **Formal.**
    - Lean: cuatro invariantes (orden temporal, edad y nacimiento, dos lugares a la vez, aparición tras un evento excluyente). Pasan de los dos que exige el encargo y cubren el opcional «invariantes adicionales». Las demostraciones generales son Deseable.
    - TLA+: `Harness.tla` con cuatro invariantes de seguridad y la vivacidad, modelo de 5 capítulos y 2 reintentos, y una configuración rota que da contraejemplo. El README mapea cada acción al código. `Regenerations.tla` es Deseable.
15. **Opcionales**, todos Deseable, en este orden:
    1. Servidor MCP de solo lectura con FastMCP montado en FastAPI (`list_novels`, `get_chapter`, `list_versions`, `query_story_bible`, `download_novel`): schemas validados, cada llamada en Langfuse y el README explica cómo conectarlo.
    2. Login con SQLite: bcrypt, JWT, propiedad y test de aislamiento; MCP respeta la identidad.
    3. Subagente y skill de auditoría de seguridad, con `docs/security-report.md`.
    4. Linters de prosa.
    5. Tools MCP de escritura con permisos y confirmación.
    6. Edición manual con linter en vivo.
    7. `Regenerations.tla`.
    8. Demostraciones generales en Lean.
    9. Revisor visual del producto.
16. **Entregables:**
    - README con el brief de ejemplo reproducible, cómo arrancar, la conexión MCP y el mapeo TLA+;
    - `.env.example`;
    - la documentación de proceso en `docs/`;
    - `presentacion/`: deck en PDF y PPTX, anexos en PDF con nombre descriptivo, README con contenido e idioma (castellano, términos técnicos en inglés), slide de presupuesto con coste de Langfuse y vídeo, que graba el usuario;
    - `ejemplos/`;
    - `.claude/` con memoria, comandos, agentes y skills;
    - `.mcp.json` con Playwright MCP, y el uso del browser MCP documentado.

## Simplificaciones frente a `architecture.md` (paquete A)

Guardián de ventana → una cuenta global. Grafo causal → novum con consecuencias. Delta declarado del writer → solo el registrador. Revisor visual que sigue cada enlace → Deseable. Worker en proceso propio → tarea asyncio dentro del único uvicorn. Reanudar desde `blocked` → solo desde `interrupted`. 48 cifras `null` → valores provisionales. Edición manual con propagación → Deseable. Presupuesto en dinero que bloquea → coste registrado y mostrado. Mutación → solo sobre el motor de políticas y el gate, y Deseable. SSE → sondeo.

## Carriles

| Carril | Posee | Entrega |
|---|---|---|
| 1 · harness | `backend/` salvo lo de los carriles 2 y 4; `backend/harness_workspace/` | Esqueleto del backend, esquema y repositorios, puerto de agente y roles, tools, hooks, orquestador y máquina de estados, punto de control, entrevista, cambios, CLI |
| 2 · calidad | `backend/src/story_maker/{validators,policy,observability}/` | Validadores, motor de políticas y normalización, audit log, techo de tokens, Langfuse, rúbricas y juez, evals y comparación humana |
| 3 · web | `frontend/`, `backend/src/story_maker/api/reading*` | React + Vite con todas las páginas, imagen corporativa, endpoints de lectura, versiones y cambios del lado web, vista de impresión y PDF |
| 4 · formal | `lean/`, `tla/`, `.github/workflows/lean-verify.yml`, `backend/src/story_maker/formal/` | Lean, verificador remoto, TLA+ con TLC y mapeo |
| orquestador | `docs/`, `specs/`, `.claude/`, `CLAUDE.md`, `workflow/`, `README.md`, `presentacion/`, CI común | Contratos, integración en V2-test, registros de proceso, presentación |
