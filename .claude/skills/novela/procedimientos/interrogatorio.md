# Fase 1 — Interrogatorio

Objetivo: `biblia.md` y `escaleta.md` aprobadas por el usuario, dentro de límites. Las preguntas al usuario **no se saltan** salvo en modo de prueba.

## A. Entrevista (la hace el orquestador, no un subagente)

1. Si `entrevista.md` ya existe con `cerrada: true`, salta a B (reanudación).
2. **Uso normal**: invoca la skill `mattpocock-skills:grilling` con estos argumentos:

   > Diseñar una novela en castellano sobre el mundo tras la revolución de la IA a partir de esta idea: «<idea>». Hay que cerrar, como mínimo: qué versión del mundo post-IA es (qué pasó, qué reglas rigen ahora, qué ha cambiado en la vida diaria); protagonista (quién es, qué quiere, qué le falta) y antagonismo; tono y registro; punto de vista y persona narrativa; tipo de final; temas a tocar y temas a evitar; extensión (entre <capitulos_min> y <capitulos_max> capítulos de <palabras_min>–<palabras_max> palabras). Cada novela inventa su propio mundo; no hay canon previo.

   La skill hace rondas de preguntas numeradas con recomendación y termina cuando el usuario confirma el entendimiento compartido. Tú no añades preguntas fuera de la skill.
3. **Modo de prueba**: no invoques grilling. Lee el fichero de respuestas (`pruebas/respuestas-prueba.md` o el indicado) y toma su tabla como si fueran las respuestas del usuario; para lo que no cubra, usa su `por_defecto`. Registra `modo_prueba: entrevista desde fichero`.
4. Escribe `entrevista.md` (plantilla en `plantillas/`; frontmatter `cerrada: true`) con **todas** las decisiones en forma pregunta → respuesta, marcando cuáles eligió el usuario y cuáles quedaron en "decide tú". Registra `entrevista_cerrada`.

## B. Biblia y escaleta (subagente `interrogador`)

5. Invoca `Agent(subagent_type: "interrogador", model: <SKILL.md §8>)` con este prompt (rellena las rutas):

   > Carpeta de la novela: `novelas/<slug>/`. Lee `idea.md`, `entrevista.md` y `config.json`. Escribe `biblia.md` y `escaleta.md` siguiendo el formato de tu definición. Puedes escribir SOLO esos dos ficheros. Objetivo orientativo: <capitulos_objetivo> capítulos de ~<palabras_por_capitulo> palabras. Límites duros: <capitulos_min>–<capitulos_max> capítulos; cada `palabras_objetivo` entre <formato.palabras_min_capitulo> y <formato.palabras_max_capitulo>. Termina tu mensaje con `PROPUESTA_DE_CIERRE:` y un resumen de 5 líneas. Máximo <turnos_por_invocacion> acciones.
   >
   > (Si es una segunda vuelta) Motivo de la vuelta anterior: <FUERA_DE_LIMITES: … | CAMBIOS: …>. Corrige solo eso.

   Pasa la invocación por `verificar-zona.md` con zona = {`biblia.md`, `escaleta.md`}.
6. Valida `escaleta.md`: frontmatter parsea; `capitulos` dentro de límites; una entrada por capítulo con `n, titulo, acto, objetivo, sucesos, personajes, gancho, palabras_objetivo`; cada `palabras_objetivo` dentro de límites; los tres actos aparecen. Si falla → `SendMessage` al mismo subagente con `FUERA_DE_LIMITES: <motivo concreto>`; cuenta en `estado.escaleta_rechazos`. Al superar `escaleta_rechazos_max` → PARADA `ESCALETA_FUERA_LIMITES`.
7. **Confirmación**:
   - Uso normal: muestra al usuario la biblia resumida (premisa, mundo, personajes) y la escaleta completa (tabla capítulo · acto · objetivo · palabras). Pregunta: "¿Confirmas la escaleta o quieres cambios?". Si pide cambios → `SendMessage` al mismo subagente con `CAMBIOS: <texto del usuario>` → vuelve a 6. Registra `propuesta_cierre` y `decision_usuario`.
   - Modo de prueba: auto-confirma si pasó la validación. Registra `decision_usuario: auto (modo prueba)`.
8. Al confirmar: pon `aprobada: true` en el frontmatter de ambos ficheros (esto lo haces tú, el orquestador). `estado.escaleta_aprobada = true`, `estado.total_capitulos = capitulos`, `estado.capitulo_actual = 1`, `estado.intento_actual = 1`, `estado.fase = capitulos`. Commit `novela <slug>: escaleta aprobada`.

## Reanudación

- Si `entrevista.md` no existe o no está cerrada → empieza en A; grilling puede leer lo que haya en `registro.md`/`entrevista.md` para no repetir.
- Si existe y está cerrada pero la escaleta no está aprobada → B desde el paso 5 (subagente nuevo; le llegan `entrevista.md` y, si los hay, los ficheros a medias).
