---
description: Sesión de un carril en su worktree — implementa sus specs en orden con TDD, verifica, commitea en su rama y avisa.
argument-hint: <A|B|C|D|E>
---

# Carril $ARGUMENTS

Eres la sesión del carril $ARGUMENTS; `<x>` es esa letra en minúscula. Tu sitio es el worktree `../sm-<x>` en la rama `carril-<x>`. El integrador trabaja en `../story-maker`, rama V2.

1. **Sitio.** `git branch --show-current` es `carril-<x>` y el directorio termina en `sm-<x>`. Si no, para y dile al usuario el `cd` correcto.
2. **Primera vez.** Si falta `backend/.venv`: `cd backend && uv sync`. Si falta `frontend/node_modules`: `cd frontend && pnpm.cmd install`. Si falta `.env`: `cp ../story-maker/.env .env`, sin leerlo ni mostrarlo.
3. **Tu cola.** De la tabla de carriles de `git show V2:TODO.md`: tus specs en orden y sus dependencias. La spec 000 tiene que estar cerrada en V2; si no, para: esperas a la 000.
4. Por cada spec de tu cola sin cerrar, en orden:
   1. **Dependencias.** Cada una cerrada (sus tres casillas de cierre `[x]`) en `git show V2:TODO.md`, o en tu rama si es de tu carril. Una dependencia marcada *parcial* en la tabla deja empezar los pasos que no la usan. Si falta alguna, pasa a la siguiente spec de tu cola que esté desbloqueada; si no queda ninguna, para y di a qué esperas (spec y carril).
   2. **Rebase.** Con el árbol limpio, `git rebase V2`. Un conflicto fuera de tus módulos o de tus bloques → `git rebase --abort` y avisa.
   3. **Spec y plan.** En tu `TODO.md`, las dos casillas `[x]` con acta del auditor. Si falta la spec, `/spec NNN`; si falta el plan, `/plan NNN`. Solo en tus bloques; las decisiones para §18 van al aviso del paso 8, no a `docs/`.
   4. **TDD.** Sigue `/implementar NNN` en esta sesión, o delega en el subagente `implementador` si el contexto se llena: paso a paso, `[x]` al ponerse verde, commit por paso. Las pruebas T usan siempre los dobles; las demostraciones D con modelo real van al final, agrupadas y una sola vez, porque gastan cuota de la suscripción.
   5. **Suite completa** verde: los comandos de `CLAUDE.md` de cada lado que toques.
   6. **Verificador.** Subagente `verificador` con NNN y la ruta absoluta del worktree. FAIL → corrige y repite (≤3 veces); después, escala al usuario.
   7. **Cierre.** Si el código probó que la spec estaba mal, corrígela, desmarca sus dos casillas y vuelve a pasar el `auditor` antes del verificador. Con PASS (el verificador marcó el cierre): commit `NNN: <nombre>` en `carril-<x>`.
   8. **Aviso.** Una línea al usuario: `Carril <X>: NNN cerrada en carril-<x> (<hash>). Lanza /orquestar en el checkout principal para integrarla.` Debajo, los hallazgos para el registro de proceso (TLC, Lean, evals, browser MCP) y las decisiones para §18.

Hecho cuando cada spec de tu cola está cerrada en tu rama o parada con el motivo dicho.

## Límites

Solo los módulos de tus specs y sus bloques en `TODO.md`. Ni `docs/`, ni `.claude/`, ni `CLAUDE.md`, ni la cabecera de `TODO.md`. Nunca merge en V2 ni push. Nunca leas `.env`.
