# CLAUDE - Story Maker Instructions

Generador agéntico de novelas en castellano sobre el mundo tras la revolución de la IA. Un harness (la skill `/novela`) coordina cinco agentes: interrogador, escritor, resumidor, revisor de encargo (¿está lo que se pidió?) y revisor de continuidad (¿se contradice algo?).

**La especificación manda**: [specs/functional.md](specs/functional.md). Si la skill, un agente o este fichero la contradicen, gana la spec y se corrige el otro.

## Dónde está cada cosa

- **Qué hace el sistema y cómo** (decisiones de diseño vigentes): [specs/functional.md](specs/functional.md). Mapa de ficheros en su §9.
- **Por qué se decidió así y qué se descartó**: [CHANGELOG.md](CHANGELOG.md). Antes de proponer un cambio de arquitectura, comprueba ahí que no está ya descartado.
- **Qué falta por hacer**: [TODO.md](TODO.md). El CHANGELOG cuenta lo ya decidido; el pendiente vive ahí y no se mezcla con el historial.
- **Lo único que el usuario edita a mano**: [config.json](config.json) (spec §7).
- **Qué salió de la primera ejecución completa y qué reglas cambió**: spec §8.5. Antes de tocar las reglas de flujo de §4.2, léela.
- **Trazas de una ejecución**: [herramientas/trazas/](herramientas/trazas/), fuera del harness.
- **El visor y el estudio**: [frontend/](frontend/), con sus reglas en [frontend/CLAUDE.md](frontend/CLAUDE.md) y su contrato en spec §9.2 y §9.4. El estudio lanza el harness, pero **no escribe en `novelas/` ni decide nada del flujo**: la regla 1 y la 4 valen ahí igual que aquí.
