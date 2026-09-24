---
description: Tabla breve del estado de las specs y de los carriles, derivada de git y de TODO.md.
allowed-tools: Bash(git *), Read, Grep, Glob
---

# Estado

Deriva cada cifra de los ficheros, nunca de la memoria de la conversación.

1. `git show V2:TODO.md` y, por cada rama de `git branch --list "carril-*"`, `git show carril-<x>:TODO.md`: por spec, casilla de spec, casilla de plan, pasos `[x]`/total y cierre, en V2 y en su rama.
2. `git worktree list`; por rama, `git rev-list --left-right --count V2...carril-<x>` y el asunto de su último commit.

Informe: una tabla de ≤15 líneas `NNN · carril · spec · plan · pasos · cierre en rama · en V2` (las specs sin empezar, agrupadas en una línea por carril) y una línea por carril con su siguiente acción.
