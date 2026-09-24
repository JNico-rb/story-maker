---
description: Sesión integradora en el checkout principal (V2) — estado, specs y planes por delante, worktrees, terminales de los carriles e integración.
argument-hint: "[sin-terminales]"
---

# Orquestar story-maker

Eres el integrador (AGENTS.md → *Parallel lanes*), en el checkout principal, rama `V2`. `$ARGUMENTS` = `sin-terminales` → paso 7 por 7b; si no, por 7a.

1. **Sitio.** `git branch --show-current` es `V2` y el directorio es el checkout principal, no un `../sm-*`. Si no, para y dilo.
2. **Estado.** Lee la cabecera de `TODO.md` (hasta `## 000`; sus bloques, con `awk -f .claude/scripts/resumen-todo.awk TODO.md`). Por rama `carril-<x>`: `git worktree list`, `git log --oneline V2..carril-<x>`, `git show carril-<x>:TODO.md | awk -f .claude/scripts/resumen-todo.awk`. Hecho: sabes por spec sin escribir · spec/plan aprobados · pasos hechos/total · cerrada en su rama · integrada en V2.
3. **Spec 000 primero.** La haces tú y bloquea lo demás hasta cerrarla: `/spec 000` y `/plan 000` si faltan; verifica el scaffolding ya escrito contra la spec (pasa → `[x]`; si no, corrige); `verificador`; commit `000: scaffolding`. Pasos D al lote final.
4. **Integrar.** Por cada carril con spec cerrada que falte en V2, sigue `.claude/commands/integrar.md`.
5. **Specs y planes por delante.** Specs sin aprobar (siguientes de cada carril; frontend del carril E desde 022): `/spec NNN` con un `redactor-specs` por spec; añades el bloque a `TODO.md`, marcas spec y plan (`/plan NNN`) y commiteas. Spec de frontend nueva → fila en `TODO.md` y en la propiedad de `frontend/AGENTS.md`.
6. **Worktrees.** Por cada carril con spec desbloqueada y sin worktree: `git worktree add ../sm-<x> -b carril-<x> V2` (rama existente: `git worktree add ../sm-<x> carril-<x>`).
7. **Lanzar los carriles.**
   - **7a. Con terminales.** Da al usuario, solo con los carriles desbloqueados:

     > Un terminal por carril (VS Code: Terminal → New Terminal, se abre en `story-maker`); en cada uno, `cd ..\sm-<x>; claude --permission-mode auto` y, dentro, `/carril <X>`. Orden: A, C, D, B (tras integrar 001), E (con specs de frontend aprobadas).
     >
     > Sin `auto`: `--permission-mode acceptEdits` (pide permiso fuera de lo permitido). Primera vez, acepta confiar en la carpeta y los MCP. Cada carril termina con `LISTO <rama> <NNN> <hash> [parcial|cerrada]` o `BLOQUEADO <motivo>`: relánzalo con `/carril <X>` para su siguiente spec. Este terminal, para `/orquestar`: relánzalo cuando un carril avise, o `/loop 30m /orquestar`.

   - **7b. Sin terminales.** Por carril con spec desbloqueada y sin implementador en curso (uno por carril; dos subagentes en el mismo worktree chocan en el índice de git): worktree listo (paso 2 de `/carril`, `cd <worktree> &&` por orden); `git -C <worktree> rebase V2`; `implementador` en segundo plano con NNN, ruta y rama (sonnet, salvo 012 y 014 en opus). Al terminar, `verificador` sobre ese worktree. PASS → commit `NNN: <nombre>` y paso 4. FAIL → relanza (≤2 veces) y escala.
8. **Tabla.** Pon al día la columna Estado de la tabla de carriles y haz commit en V2: `orquestar: estado`.

Hecho: nada cerrado sin integrar, cada carril desbloqueado con terminal o implementador en marcha, y la tabla dice la verdad.

## Informe al usuario (≤10 líneas)

Integrado en esta pasada · en marcha · bloqueado y a qué espera · escalados (FAIL persistente del verificador, preguntas del usuario en lote) · tareas solo humanas pendientes (revisión humana de una novela, vídeo de demo, cuentas y tokens).
