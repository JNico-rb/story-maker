---
description: Solo el integrador: merge --no-ff de specs cerradas y suite completa.
argument-hint: "[carril-<x>]"
---

# Integrar en V2

1. `V2`, checkout principal, `git status` limpio; si no, para.
2. **Candidatos.** En `$ARGUMENTS`, o si falta en cada rama `carril-<x>`: commits de cierre `NNN: <nombre>` de `git log --oneline V2..carril-<x>` (no `NNN: spec`, `NNN: plan` ni `NNN paso <k>: …`) cuya spec siga sin cerrar en V2. Una línea `LISTO <rama> <NNN> <hash> parcial` también es candidata: se integra ese hash, sin la comprobación 3.1, con el mensaje «Integra NNN parcial (carril-<x>)».
3. Por commit de cierre, del más antiguo al más nuevo:
   1. `git show <hash>:TODO.md`: tres casillas de cierre `[x]` con acta del verificador; si no, salta y avisa al carril.
   2. `git merge --no-ff -m "Integra NNN (carril-<x>)" <hash>`: el commit de cierre, no la cabeza de la rama, para no traer a medias la siguiente.
   3. **Conflictos** en `TODO.md`: conserva los bloques de cada lado; «los dos añaden una línea» (routers, CLI, exportaciones), ambas; cualquier otro → `git merge --abort`, pide rebase y resolver en su rama.
   4. **Suite completa** en V2, los dos lados.
   5. Rojo → `git reset --merge ORIG_HEAD`, avisa con la salida del fallo. Verde → siguiente.
4. **Registro de proceso.** Lo del carril → `docs/verification.md` (eval §4.2, adversarial §4.9, cambio tras eval/TLC/Lean §8, browser MCP §9.3, subagente o comando §9.4); decisiones → `architecture.md` §18; commit `docs: registro de NNN`.
5. **Tabla y aviso.** Tabla de carriles al día; commit. A cada carril que dependa de lo integrado: «haz `git rebase V2`». `git push origin V2`, nunca forzado.

Hecho: cada candidato integrado en verde o devuelto con el motivo.
