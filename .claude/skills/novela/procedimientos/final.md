# Fase 3 — Final

Precondición: `estado.fase == final` (todos los capítulos cerrados).

1. **Ensamblar `manuscrito.md`** (lo escribes tú, el orquestador):
   - Título: `titulo` del frontmatter de `escaleta.md`.
   - Índice: lista de capítulos con su `titulo`.
   - Cuerpo: para cada N en orden, `## Capítulo N — <titulo>` seguido del cuerpo (sin frontmatter) de `capitulos/NN/intento-<estado.capitulos[N].aprobado>.md`.
   - Al final, una nota si algún capítulo fue aceptado por agotamiento, con enlace a su informe.
2. **Revisión global** (subagente `revisor`; modelo escalado si `modelos.escalado.revision_global`, ver SKILL.md §8):

   > Carpeta: `novelas/<slug>/`. Revisión GLOBAL de la novela completa. Lee `manuscrito.md`, `biblia.md`, `escaleta.md` y todos los resúmenes aprobados: <rutas>. Busca solo lo que no se ve capítulo a capítulo: hilos prometidos y nunca cerrados, contradicciones entre capítulos lejanos, personajes que desaparecen sin explicación, cambios en las reglas del mundo. No escribas ficheros salvo `notas-revisor-global.md` si lo necesitas. Devuelve el informe como bloque YAML según tu definición; el veredicto aquí es informativo. Máximo <turnos_por_invocacion> acciones.

   `verificar-zona.md` con zona = {`notas-revisor-global.md`}. Validación como en un informe de capítulo. Escribe `informe-global.md` con el YAML como frontmatter y los problemas en prosa. **No reescribas nada** aunque haya problemas: quedan para el usuario.
3. `estado.informe_global = true`, `estado.fase = completa`. Guarda. Commit `novela <slug>: novela completa`.
4. `cierre.md` con resultado ÉXITO, indicando rutas de `manuscrito.md` e `informe-global.md` y cuántos problemas globales hay por gravedad.
