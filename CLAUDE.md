# CLAUDE - Story Maker Instructions

Generador agéntico de novelas en castellano sobre el mundo tras la revolución de la IA. Un harness (la skill `/novela`) coordina cinco agentes: interrogador, escritor, resumidor, revisor de encargo (¿está lo que se pidió?) y revisor de continuidad (¿se contradice algo?).

**La especificación manda**: [specs/functional.md](specs/functional.md) (qué hace) y [specs/technical.md](specs/technical.md) (§9: dónde está implementado, y la evidencia E-n). Si la skill, un agente o este fichero la contradicen, gana la spec y se corrige el otro.

## Dónde está cada cosa

- **Qué hace el sistema y cómo** (decisiones de diseño vigentes): [specs/functional.md](specs/functional.md), §0–§8 y §10. Es la fuente de verdad.
- **Dónde está implementado y con qué datos se decidió**: [specs/technical.md](specs/technical.md). Contiene el §9 completo (mapa de ficheros, observabilidad, `/optimizar`, `/validar`) y la evidencia `E1`–`E7`. El §9 sigue siendo normativo: solo cambió de fichero.
- **Los diagramas del flujo**: [specs/architecture.md](specs/architecture.md), descriptivo. Si un diagrama y la spec discrepan, gana la spec.
- **Por qué se decidió así y qué se descartó**: [CHANGELOG.md](CHANGELOG.md). Antes de proponer un cambio de arquitectura, comprueba ahí que no está ya descartado.
- **Qué falta por hacer**: [TODO.md](TODO.md). El CHANGELOG cuenta lo ya decidido; el pendiente vive ahí y no se mezcla con el historial.
- **Lo único que el usuario edita a mano**: [config.json](config.json) (spec §7).
- **Qué salió de la primera ejecución completa y qué reglas cambió**: functional §8.5 y technical E1. Antes de tocar las reglas de flujo de §4.2, léela.
- **Trazas de una ejecución**: [herramientas/trazas/](herramientas/trazas/), fuera del harness.
- **Cómo medir**: [herramientas/COMO-USAR.md](herramientas/COMO-USAR.md). Dos herramientas, las dos fuera del harness: `/validar` puntúa un manuscrito (technical §9.6) y `/optimizar` mejora el prompt de un agente (technical §9.5). **Léelo antes de usarlas**: su §1 tiene las cinco reglas que no son criterio tuyo, y la primera es que tú nunca puntúas.
- **El visor y el estudio**: [frontend/](frontend/), con sus reglas en [frontend/CLAUDE.md](frontend/CLAUDE.md) y su contrato en technical §9.2 y §9.4. El estudio lanza el harness, pero **no escribe en `novelas/` ni decide nada del flujo**: la regla 1 y la 4 valen ahí igual que aquí.
