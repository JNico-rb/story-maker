# Tablero V1: de las specs al código

Temporal: se borra cuando las 18 specs estén hechas. Cada chat actualiza solo la fila de su spec.

## Flujo por spec: tres chats

1. **Spec** (grill, sin `/goal`). Escribe `spec.md`, lo pasa por el `auditor`, se para en la casilla y entrega la línea del chat de plan.
2. **Plan** (`/goal`). Escribe `plan.md` y cierra su gap en `docs/relational-matrix.md` hasta cero ([proceso 3](../../workflow/3-plan.md), bucle de gap). Avisa con `PushNotification` y entrega la línea del chat de código en `prompts/NNN-codigo.md`.
3. **Código** (`/goal`). TDD según el [proceso 4](../../workflow/4-code.md).

Entre un chat y el siguiente, marcas tú la casilla de aprobación. Conviene no tener más de tres chats de spec o de plan a la vez, porque cada grill pasa por ti.

## Antes de la oleada 1 (chat central)

- [ ] La fase 1 de docs está cerrada y hay commit de control.
- [ ] `git rm -r` de las specs viejas 002–011; la 001 se reescribe en su chat.
- [ ] §1 de `docs/relational-matrix.md` rellena: cada sección de `architecture.md` con su spec.
- [ ] Decidido cómo se aíslan los chats de código (worktrees con ramas `v2-test/NNN`, o todo en V2-test).

## Specs

Estado: `pendiente` → `spec` → `plan` → `código` → `hecha`. La columna «Depende de» es orientativa: indica qué código tiene que existir antes.

| # | Carpeta | MÓD | Oleada | Depende de | Estado |
|---|---|---|---|---|---|
| 001 | `001-base` | BAS | 1 | — | pendiente |
| 002 | `002-aut-autenticacion` | AUT | 2 | 001 | pendiente |
| 003 | `003-pol-politica-y-guardarrailes` | POL | 2 | 001 | pendiente |
| 004 | `004-obs-observabilidad` | OBS | 2 | 001 | pendiente |
| 005 | `005-ent-entrevista-y-brief` | ENT | 3 | 002, 003, 004 | pendiente |
| 006 | `006-tla-especificacion-del-harness` | TLA | 2 | 001 | pendiente |
| 007 | `007-run-ejecuciones` | RUN | 3 | 004, 006 | pendiente |
| 008 | `008-mem-memoria` | MEM | 2 | 001 | pendiente |
| 009 | `009-lea-validador-formal-de-la-historia` | LEA | 2 | 001 | pendiente |
| 010 | `010-pln-planificacion` | PLN | 4 | 007, 008, 009 | pendiente |
| 011 | `011-cap-produccion-por-capitulo` | CAP | 4 | 003, 010 | pendiente |
| 012 | `012-lin-linters-de-prosa` | LIN | 2 | 001 | pendiente |
| 013 | `013-lec-lectura-web-y-pdf` | LEC | 3 | 002 | pendiente |
| 014 | `014-pub-publicacion-y-versiones` | PUB | 5 | 011, 012, 013 | pendiente |
| 015 | `015-cam-cambios-y-edicion-manual` | CAM | 5 | 014 | pendiente |
| 016 | `016-mcp-servidor-mcp` | MCP | 6 | 002, 014, 015 | pendiente |
| 017 | `017-evl-evaluacion-del-sistema` | EVL | 6 | 014, 015 | pendiente |
| 018 | `018-sec-auditoria-de-seguridad` | SEC | 6 | 016 | pendiente |

## Líneas para pegar

Sustituye `NNN-slug` por la carpeta de la tabla.

**Chat de spec:**

```
Spec NNN-slug de .scratch/v1/tablero.md. Sigue CLAUDE.md y workflow/2-specs.md: grill con la skill grill-me sobre esta spec y después escríbela. Al acabar, pasa el subagente auditor sobre specs/NNN-slug/ y corrige en la spec lo que encuentre. Deja la casilla sin marcar, pon su fila del tablero en «spec» y dame la línea del chat de plan de ese tablero, ya rellenada.
```

**Chat de plan** (una sola línea, porque `/goal` solo admite una):

```
/goal Spec NNN-slug: comprueba que la casilla de specs/NNN-slug/spec.md está marcada (si no, para y avísame); escribe su plan.md y cierra su gap con el bucle de workflow/3-plan.md, siguiendo CLAUDE.md. Termina cuando el último informe del subagente auditor en esta conversación dé 0 diferencias, el apartado NNN-slug de docs/relational-matrix.md no tenga filas abiertas, la línea del chat de código esté en .scratch/v1/prompts/NNN-codigo.md y en tu mensaje final, la fila del tablero esté en «plan» y me hayas avisado con PushNotification. Si una diferencia pide cambiar un doc, hazme el grill del proceso 1 y espera mi respuesta.
```

**Chat de código:** la línea que entrega el chat de plan, con la plantilla de `workflow/3-plan.md`.
