---
description: Sesión de un carril en su worktree — implementa la primera spec desbloqueada de su cola con TDD, verifica, commitea en su rama y termina con una línea.
argument-hint: <A|B|C|D|E>
---

# Carril $ARGUMENTS

Eres la sesión del carril $ARGUMENTS; `<x>` es esa letra en minúscula. Tu sitio: worktree `../sm-<x>`, rama `carril-<x>`. El integrador trabaja en `../story-maker`, rama V2.

1. **Sitio.** `git branch --show-current` es `carril-<x>` y el directorio termina en `sm-<x>`. Si no, para y dile al usuario el `cd` correcto.
2. **Primera vez.** Si falta `backend/.venv`: `cd backend && uv sync`. Si falta `frontend/node_modules`: `cd frontend && pnpm.cmd install`. Si falta `.env`: `cp ../story-maker/.env .env`, sin leerlo ni mostrarlo.
3. **Elige una spec.** De la tabla de carriles (`git show V2:TODO.md | sed -n '/^## Carriles/,/^## Specs/p'`; nunca `TODO.md` entero), toma la primera de tu cola sin cerrar con dependencias cerradas (cierre 3/3 en `git show V2:TODO.md | awk -f .claude/scripts/resumen-todo.awk`, o en tu rama si es tuya; una *parcial* deja empezar los pasos que no la usan) y con la 000 cerrada en V2. Ninguna elegible → `BLOQUEADO <spec y de qué depende>`.
4. **Rebase.** Árbol limpio, `git rebase V2`. Conflicto fuera de tus módulos o bloques → `git rebase --abort` y `BLOQUEADO rebase: <conflicto>`.
5. **Spec y plan.** En tu bloque `## NNN` de `TODO.md` (léelo solo: `sed -n '/^## NNN /,/^## [0-9]/p' TODO.md`), las dos casillas de arriba están `[x]`. Si falta alguna: `BLOQUEADO spec o plan sin aprobar: pide /spec o /plan al integrador`.
6. **TDD.** `/implementar NNN` en esta sesión, o subagente `implementador` si el contexto se llena (012 y 014 en opus, resto sonnet; uno a la vez en este worktree, los commits chocan en el índice de git). Paso a paso: prueba que falla por el motivo correcto → código mínimo → suite completa → `[x]` → commit. Pruebas T con los dobles siempre. Pasos D quedan `[ ]` (`D, al final`): nada de modelo real antes.
7. **Cierre.** Suite completa verde y todos los pasos no D en `[x]` → `verificador` con NNN y la ruta del worktree. FAIL → corrige y repite (≤3 veces); si persiste, `BLOQUEADO verificador: <hallazgo>`. PASS → commit `NNN: <nombre>` en `carril-<x>`, con hallazgos (TLC, Lean, evals, browser MCP) y decisiones §18 en el cuerpo. Spec probada mal por el código → corrígela y dilo en el commit; el integrador remarca sus casillas.

Termina siempre con una sola línea: `LISTO carril-<x> NNN <hash> cerrada` (o `parcial` si el paso no cerró la spec) — o `BLOQUEADO <motivo>` en cualquier punto anterior.

## Límites

Solo los módulos y bloques de `TODO.md` de tus specs (ver AGENTS.md → *Parallel lanes*). Nunca merge en V2 ni push.
