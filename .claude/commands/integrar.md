---
description: Solo el integrador, en V2 — integra con merge --no-ff las specs cerradas de los carriles y comprueba la suite completa.
argument-hint: "[carril-<x>]"
---

# Integrar en V2

1. Rama `V2`, checkout principal y `git status` limpio. Si no, para.
2. **Candidatos.** En `$ARGUMENTS` o, si viene vacío, en cada rama `carril-<x>`: los commits de cierre `NNN: <nombre>` de `git log --oneline V2..carril-<x>` (no los `NNN: spec`, `NNN: plan` ni `NNN paso <k>: …`) cuya spec no está cerrada en V2.
3. Por cada commit de cierre, del más antiguo al más nuevo:
   1. `git show <hash>:TODO.md`: las tres casillas de cierre del bloque NNN están `[x]` con el acta del verificador. Si no, sáltalo y avisa al carril.
   2. `git merge --no-ff -m "Integra NNN (carril-<x>)" <hash>`. Se integra el commit de cierre, no la cabeza de la rama, para no traer a medias la spec siguiente.
   3. **Conflictos.** En `TODO.md`, conserva los bloques de cada lado (cada carril edita solo los suyos). «Los dos añaden una línea» (registro de routers, comandos de la CLI, exportaciones): conserva ambas. Cualquier otro → `git merge --abort` y pide al carril que haga `git rebase V2` y lo resuelva en su rama.
   4. **Suite completa** en V2, los dos lados (comandos de `CLAUDE.md`).
   5. Rojo → `git reset --hard ORIG_HEAD` (el árbol estaba limpio: solo deshace este merge) y avisa al carril con la salida del fallo. Verde → siguiente.
4. **Registro de proceso.** Lo que el carril reportó va a `docs/verification.md`: resultado de eval a §4.2, caso adversarial a §4.9, cambio tras una eval, TLC o Lean a §8, inspección con el browser MCP a §9.3, uso de subagente o comando a §9.4. Las decisiones para §18, a `architecture.md` §18. Commit: `docs: registro de NNN`.
5. **Tabla.** Estado de la tabla de carriles al día; commit.
6. **Aviso.** A cada carril que dependa de lo integrado: «haz `git rebase V2`». `git push origin V2` solo si el usuario lo autorizó en esta sesión, y nunca forzado.

Hecho cuando cada cierre candidato está integrado con la suite verde en tu salida, o devuelto a su carril con el motivo.
