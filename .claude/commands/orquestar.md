---
description: Sesión integradora en el checkout principal (V2) — estado, specs y planes por delante, worktrees, terminales de los carriles e integración.
argument-hint: "[sin-terminales]"
---

# Orquestar story-maker

Eres el integrador: la única sesión que trabaja en el checkout principal (rama `V2`), la única que hace merge en V2 y la única que escribe `docs/`, `.claude/`, `CLAUDE.md`, `README.md` y la cabecera de `TODO.md`. Modo: si `$ARGUMENTS` es `sin-terminales`, el paso 7 va por 7b; si no, por 7a.

1. **Sitio.** `git branch --show-current` es `V2` y el directorio es el checkout principal, no un `../sm-*`. Si no, para y dilo.
2. **Estado.** Lee `TODO.md` (tabla de carriles, tabla de specs y bloques), `git worktree list` y, por cada rama `carril-<x>`, `git log --oneline V2..carril-<x>` y `git show carril-<x>:TODO.md`. Hecho cuando sabes, por spec: sin escribir · spec aprobada · plan aprobado · pasos hechos/total · cerrada en su rama · integrada en V2.
3. **Spec 000 primero.** Mientras no esté cerrada en V2 es el único trabajo, y lo haces tú en V2: `/spec 000` y `/plan 000` si faltan; el scaffolding ya escrito se verifica paso a paso contra la spec (pasa → `[x]`; no pasa → se corrige); después `verificador` sobre el checkout principal y commit `000: scaffolding`. Sus pasos D quedan para el lote final. Ningún carril arranca antes.
4. **Integrar.** Por cada carril con una spec cerrada que V2 aún no tiene, sigue `.claude/commands/integrar.md`.
5. **Specs y planes por delante.** Para las specs sin aprobar (las siguientes de cada carril, y las de frontend del carril E, desde 022): `/spec NNN …` con **un `redactor-specs` por spec, en paralelo**; tú añades cada bloque a `TODO.md` de uno en uno, marcas tú spec y plan sin revisión (`/plan NNN`) y commiteas cada aprobación (`NNN: spec aprobada`, `NNN: plan aprobado`). Las decisiones que cierre un redactor van a `architecture.md` §18. Al añadir una spec de frontend, añade su fila a las tablas de `TODO.md` y a la de propiedad de `frontend/AGENTS.md`.
6. **Worktrees.** Por cada carril con una spec desbloqueada y sin worktree: `git worktree add ../sm-<x> -b carril-<x> V2` (si la rama ya existe, `git worktree add ../sm-<x> carril-<x>`).
7. **Lanzar los carriles.**
   - **7a. Con terminales.** Da al usuario este texto, con solo los carriles que tienen trabajo desbloqueado, en el orden A, C, D, B, E:

     > Abre un terminal nuevo por carril (en VS Code, Terminal → New Terminal; se abre en `story-maker`), en este orden:
     >
     > 1. `cd ..\sm-a; claude --permission-mode auto` y, dentro, `/carril A`
     > 2. `cd ..\sm-c; claude --permission-mode auto` y, dentro, `/carril C`
     > 3. `cd ..\sm-d; claude --permission-mode auto` y, dentro, `/carril D`
     > 4. `cd ..\sm-b; claude --permission-mode auto` y, dentro, `/carril B` (en cuanto 001 esté integrada)
     > 5. `cd ..\sm-e; claude --permission-mode auto` y, dentro, `/carril E` (en cuanto haya specs de frontend aprobadas)
     >
     > Si tu plan no admite el modo `auto`, usa `--permission-mode acceptEdits` (pedirá permiso para los comandos que no estén en la lista de permitidos). La primera vez Claude Code pide confiar en la carpeta y aprobar los MCP del proyecto: acepta. Deja este terminal (checkout principal, V2) para `/orquestar`: vuelve a lanzarlo cada vez que un carril avise de que cerró una spec, o déjalo en marcha con `/loop 30m /orquestar`.

   - **7b. Sin terminales.** Por cada carril con una spec desbloqueada y sin implementador en curso (como mucho uno por carril): prepara el worktree como `/carril` paso 2, con cada orden precedida de `cd <worktree> &&`; `git -C <worktree> rebase V2`; y lanza en segundo plano el subagente `implementador` con NNN, la ruta absoluta del worktree y la rama. Cuando termine: `verificador` sobre ese worktree. PASS → commit `NNN: <nombre>` en la rama del carril y paso 4. FAIL → relanza el implementador con los hallazgos (≤2 veces) y después escala.
8. **Tabla.** Pon al día la columna Estado de la tabla de carriles y haz commit en V2: `orquestar: estado`.

Hecho cuando nada cerrado queda sin integrar, cada carril con trabajo desbloqueado tiene su terminal indicado o su implementador en marcha, y la tabla dice la verdad.

## Informe al usuario (≤10 líneas)

Integrado en esta pasada · en marcha · bloqueado y a qué espera · escalados (FAIL persistente del verificador, preguntas del usuario en lote) · tareas solo humanas pendientes (revisión humana de una novela, vídeo de demo, cuentas y tokens).
