# story-maker

Generador agéntico de novelas en castellano sobre el mundo tras la revolución de la IA. Un harness (la skill `/novela`) coordina cuatro agentes: interrogador, escritor, resumidor y revisor.

**La especificación manda**: [specs/functional.md](specs/functional.md). Si la skill, un agente o este fichero la contradicen, gana la spec y se corrige el otro. El vocabulario del proyecto está en su §0: un término nuevo entra ahí antes de usarse en cualquier otro fichero.

## Reglas que valen siempre

1. **Solo el harness escribe en disco.** Los agentes devuelven su salida en el mensaje final; el harness la valida y la escribe. Los subagentes llevan `tools: Read, Glob, Grep` y `maxTurns` igual a `limites.turnos_por_invocacion` de `config.json`.
2. **Nada aprobado se modifica**: biblia, escaleta de alto nivel, escaletas de arco validadas, capítulos aprobados, manuscrito, y el libro de estado salvo al cerrar un capítulo. El harness crea cada uno de esos ficheros con `Write` una sola vez; un hook de `.claude/settings.json` bloquea `Edit` sobre ellos.
3. **Commits automáticos solo dentro de `novelas/`**, en los puntos consistentes que fija la skill. Fuera de esa carpeta, nunca sin que el usuario lo pida. `git push`, nunca.
4. **Lo mecánico lo hace el harness, no un agente**: contar palabras (`wc -w`), recalcular el veredicto, validar la forma de una salida, elegir el mejor intento, actualizar `estado.json`.
5. **Todo cambio de diseño pasa por [CHANGELOG.md](CHANGELOG.md)**: qué, por qué y qué se descartó. Primero la spec, después la implementación.
6. **Todo lo que se diseñe tiene que poder portarse al runner del hito 2** (spec §10). Si algo solo funciona en Claude Code, se anota en el CHANGELOG.

## Dónde está cada cosa

- **Qué hace el sistema y cómo** (decisiones de diseño vigentes): [specs/functional.md](specs/functional.md). Mapa de ficheros en su §9.
- **Por qué se decidió así y qué se descartó**: [CHANGELOG.md](CHANGELOG.md). Antes de proponer un cambio de arquitectura, comprueba ahí que no está ya descartado.
- **Lo único que el usuario edita a mano**: [config.json](config.json) (spec §7).
