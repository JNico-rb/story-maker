# story-maker

Generador agéntico de novelas en castellano sobre el mundo tras la revolución de la IA. Un harness (la skill `/novela`) coordina cinco agentes: interrogador, escritor, resumidor, revisor de encargo (¿está lo que se pidió?) y revisor de continuidad (¿se contradice algo?).

**La especificación manda**: [specs/functional.md](specs/functional.md). Si la skill, un agente o este fichero la contradicen, gana la spec y se corrige el otro. El vocabulario del proyecto está en su §0: un término nuevo entra ahí antes de usarse en cualquier otro fichero.

## Reglas que valen siempre

1. **Solo el harness escribe en disco.** Los agentes devuelven su salida en el mensaje final; el harness la valida y la escribe. Los subagentes llevan `tools: Read, Glob, Grep` y `maxTurns` igual a `limites.turnos_por_invocacion` de `config.json`.
2. **Nada aprobado se modifica**: biblia, escaleta de alto nivel, escaletas de arco validadas, capítulos aprobados, manuscrito, y el libro de estado salvo al cerrar un capítulo. `.claude/hooks/inmutables.sh` bloquea `Edit` sobre ellos siempre, y el `Write` con dos reglas (spec §3.1): la biblia, la escaleta y las escaletas de arco admiten una escritura por versión mientras no lleven `aprobada: true` / `validada: true`, porque la propuesta se rehace a propósito y aprobarla consiste en reescribirla con la marca puesta; los demás se escriben una sola vez y bloquean en cuanto el fichero existe. El libro de estado es la excepción: su `Write` siempre pasa, porque se sustituye entero al cerrar cada capítulo. La garantía cubre `Edit` y `Write`, **no Bash**.
3. **Commits automáticos solo dentro de `novelas/`**, en los puntos consistentes que fija la skill. Fuera de esa carpeta, nunca sin que el usuario lo pida. `git push`, nunca.
4. **Lo mecánico lo hace el harness, no un agente**: contar palabras (`wc -w`), unir los problemas de los dos revisores y recalcular el veredicto, validar la forma de una salida, elegir el mejor intento (cierres de escaleta antes que recuento de problemas), actualizar `estado.json`.

5. **La observabilidad nunca entra en el bucle.** Las trazas se exportan después, desde `registro.md`, con una herramienta de solo lectura (spec §9.3). `registro.md` es la fuente de verdad; Langfuse es una proyección suya. Las credenciales van en `.claude/settings.local.json`, que está ignorado: nunca en `.claude/settings.json`, que sí se versiona.
6. **Todo cambio de diseño pasa por [CHANGELOG.md](CHANGELOG.md)**: qué, por qué y qué se descartó. Primero la spec, después la implementación.
7. **Todo lo que se diseñe tiene que poder portarse al runner del hito 2** (spec §10). Si algo solo funciona en Claude Code, se anota en el CHANGELOG.

## Dónde está cada cosa

- **Qué hace el sistema y cómo** (decisiones de diseño vigentes): [specs/functional.md](specs/functional.md). Mapa de ficheros en su §9.
- **Por qué se decidió así y qué se descartó**: [CHANGELOG.md](CHANGELOG.md). Antes de proponer un cambio de arquitectura, comprueba ahí que no está ya descartado.
- **Qué falta por hacer**: [TODO.md](TODO.md). El CHANGELOG cuenta lo ya decidido; el pendiente vive ahí y no se mezcla con el historial.
- **Lo único que el usuario edita a mano**: [config.json](config.json) (spec §7).
- **Qué salió de la primera ejecución completa y qué reglas cambió**: spec §8.5. Antes de tocar las reglas de flujo de §4.2, léela.
- **Trazas de una ejecución**: [herramientas/trazas/](herramientas/trazas/), fuera del harness.
