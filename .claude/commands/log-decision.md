---
description: Apunta una decisión en el registro de iteraciones (docs/verification.md §8) con disparador, cambio, efecto y dónde quedó.
argument-hint: "<disparador>: <qué cambió y por qué>"
allowed-tools: Bash(git *), Bash(grep *), Bash(sed *), Read, Edit
---

# Registrar una decisión

Solo el integrador, en V2 (`docs/` tiene un único escritor). `$ARGUMENTS` = disparador y decisión; si falta el disparador o el porqué, pregunta una vez.

1. `grep -n '^## 8\|^| [0-9]* | 20' docs/verification.md`: localiza la tabla numerada de §8 y su última fila. No leas el doc entero.
2. Añade una fila al final de esa tabla: `| <n+1> | <hoy> | <disparador> | <cambio, con su causa> | <efecto medido, o «pendiente»> | <doc y sección que ahora poseen la decisión> |`. El disparador es uno de `eval` · `TLC` · `Lean` · `browser MCP` · `auditoría` · `entorno`, con su detalle entre paréntesis.
3. Si la decisión cierra un trade-off de diseño y aún no tiene fila en `architecture.md` §18, dilo: la fila de §8 remite, no sustituye.
4. Commit: `log-decision: <resumen de ≤8 palabras>`.

Log de decisiones con causa y efecto, no un diario: nada de pasos rutinarios ni de resultados sin cambio.
