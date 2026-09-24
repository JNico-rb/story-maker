---
description: Implementa con TDD el plan aprobado de una spec en el checkout actual, paso a paso y con commit por paso verde.
argument-hint: <NNN>
---

# Implementar la spec $ARGUMENTS

1. En el `TODO.md` de este checkout, el bloque `## $ARGUMENTS` tiene spec y plan `[x]`. Si no, para: toca `/spec` o `/plan`.
2. Lee `AGENTS.md` proceso 4, `backend/AGENTS.md` o `frontend/AGENTS.md` (los módulos de esta spec), la spec y el bloque. Hecho cuando puedes nombrar cada paso pendiente y los módulos que puedes tocar.
3. Por cada paso `[ ]`, en orden: prueba con nombre de comportamiento → **rojo por la razón correcta** (la aserción del caso, no un import ni una fixture) → código mínimo → suite completa del lado → refactor en verde → `[x]` → commit `$ARGUMENTS paso <k>: <nombre del caso>`.
4. Las pruebas T usan siempre los dobles: el falso del puerto de agente y el nulo de observabilidad. Las demostraciones D con modelo real van al final, agrupadas y una sola vez: gastan cuota de la suscripción.
5. Si el plan resulta equivocado, para y dilo: el plan se corrige y se vuelve a auditar; nunca se improvisa un paso. Un rechazo de `guard-plan` o `guard-secretos` es la puerta funcionando: informa.

Hecho cuando cada paso está `[x]`, la suite completa, el lint, el formato y los tipos del lado están verdes en tu salida y `git status` no muestra nada sin commit. Las casillas de cierre las marca el `verificador`, no tú.
