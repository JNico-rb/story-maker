# La entrega es una V1 descrita por una sola spec, porque el plazo bajó a menos de 24 horas

Status: superseded by [ADR 0006](0006-diseno-lean.md), 2026-09-24

El 2026-09-23 el plazo de entrega pasó a menos de 24 horas. En ese momento había 483 RF en 18 specs, todos Obligatorio, y ningún código del producto integrado. La revisión de ese día, cinco subagentes de solo lectura, estimó entre 45 y 60 días-persona ([informe](../../.scratch/revision/2026-09-23.md) (rama V2-test, no conservada)). Además, el gate de gap cero ya se había saltado una vez: el código de 001 empezó con tres diferencias bloqueantes abiertas.

Se construye una V1 descrita por una sola spec, [019-v1-entrega](../../specs/019-v1-entrega/spec.md) (rama V2-test, no conservada). Cumple el encargo al pie de la letra con el diseño más simple que funciona. `architecture.md` y las specs 001–018 quedan como el diseño completo (V2): la V1 remite a sus secciones donde coincide y dice dónde simplifica. Lo que exige el encargo es Obligatorio. Lo que solo sirve a un opcional es Deseable y va al final, así que si se acaba el tiempo la entrega sigue siendo válida.

Es lo único que cabe en el plazo sin perder requisitos del encargo, y conserva como evidencia el razonamiento de diseño, que es lo que se corrige.

## Consecuencias

- **Simplificaciones frente a `architecture.md`:**
  - el techo de 100.000 tokens es una sola cuenta global en memoria;
  - el mundo es un novum con fecha y consecuencias, sin grafo causal;
  - el writer entrega solo texto y el registrador extrae usos y eventos;
  - el worker es una tarea dentro del único proceso de uvicorn;
  - se reanuda solo desde `interrupted`;
  - las cifras sin calibrar reciben valores provisionales;
  - el coste se registra sin bloquear;
  - el progreso se consulta por sondeo, sin SSE.
- **Pasan a Deseable**: el RAG híbrido, la edición manual con propagación, el revisor visual del producto, la mutación, el sexto brief y los marcos.
- **Se mantienen**: el frontend React + Vite y todos los opcionales del encargo, como Deseable.
- **Cuatro carriles** de Claude Code trabajan en paralelo en worktrees `v2-test-019-*`, sobre los contratos de `specs/019-v1-entrega/design.md` (rama V2-test, no conservada). El orquestador es el único que escribe `docs/` e integra en V2-test. El carril formal arrancó antes de aprobarse la spec 019, por decisión del usuario, porque solo toca `lean/` y `tla/`.
- **El gate deja de ser prosa.** Un hook de Claude Code impide marcar casillas de aprobación y editar `backend/` o `frontend/` sin el plan aprobado ([AGENTS.md](../../AGENTS.md)).
