---
description: Implementa con TDD el plan aprobado de una spec en el checkout actual, paso a paso y con commit por paso verde.
argument-hint: <NNN>
---

# Implementar la spec $ARGUMENTS

El bucle TDD tiene **una sola fuente**: `.claude/agents/implementador.md` (que sigue `AGENTS.md` proceso 4). Este comando no lo repite.

1. En el `TODO.md` de este checkout, el bloque `## $ARGUMENTS` tiene spec y plan `[x]`. Si no, para: faltan `/spec` o `/plan`, que ejecuta el integrador.
2. Lanza el subagente `implementador` con $ARGUMENTS, la ruta absoluta de este checkout y su rama; o, si prefieres hacerlo en esta sesión, sigue sus pasos y sus límites tal cual.
3. Cuando termine, lanza el `verificador` con $ARGUMENTS y la misma ruta. Las casillas de cierre las marca él.

Hecho cuando el implementador informa cada paso `[x]` con su commit y el verificador da PASS, o cuando uno de los dos para con un motivo que hay que resolver (plan equivocado, rechazo de `guard-plan` o `guard-secretos`, suite en rojo).
