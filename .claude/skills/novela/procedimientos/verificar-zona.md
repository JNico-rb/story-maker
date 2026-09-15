# Invocar un subagente y verificar su zona

Se aplica a **cada** invocación de subagente. Entrada: nombre del subagente, prompt, zona permitida (lista de rutas relativas a `novelas/<slug>/`), validación de artefactos.

```
para intento_tecnico en 1..reintentos_tecnicos:
    a. git status --porcelain novelas/<slug>   → debe estar vacío. Si no: git checkout -- novelas/<slug>; git clean -fd novelas/<slug>; registra paso_descartado.
    b. registra invocacion(subagente, modelo, N, K, intento_tecnico, inicio)
    c. Agent(subagent_type = <subagente>, model = <SKILL.md §8>, prompt = <prompt> [+ "Motivo del reintento: <motivo>" si intento_tecnico > 1])
       estado.invocaciones[<subagente>] += 1
    d. Si la herramienta falla o el mensaje final está vacío → motivo = "fallo técnico"; ir a f.
    e. git status --porcelain novelas/<slug>   → lista de ficheros cambiados/creados.
       fuera = los que NO están en la zona permitida (compara rutas relativas exactas).
       Si fuera no está vacío:
           para cada fichero en fuera: si estaba versionado → git checkout -- <fichero>; si es nuevo → borrarlo.
           registra escritura_fuera_de_zona(subagente, ficheros, revertido=true)
           motivo = "ESCRITURA FUERA DE ZONA: <ficheros>. Solo puedes escribir en: <zona>."
           ir a f.
       Comprueba el mensaje final y los artefactos según la validación indicada.
       Si falla → motivo = "INCUMPLE CONTRATO: <qué falta o qué está mal>"; ir a f.
       ÉXITO → registra invocacion(resultado=ok); guarda estado.json; return.
    f. registra invocacion(resultado = fallo | incumple, motivo)
       Si hay artefactos a medias dentro de la zona (p. ej. intento-K.md escrito pero sin resumen), déjalos: el reintento del mismo subagente los sobreescribe. Si el motivo fue "fallo técnico" y prefieres partir limpio: git checkout/clean de la zona.
       registra decision_harness(reintento, intento_tecnico)
       continuar el bucle

agotados:
    motivo_parada = FALLO_TECNICO_PERSISTENTE si el último motivo fue fallo técnico, si no INCUMPLE_CONTRATO
    git checkout -- novelas/<slug>; git clean -fd novelas/<slug>     (nada a medias)
    → cierre.md con ese motivo, fase_previa = fase actual
```

Notas:

- La zona se pasa **con N y K concretos**: `capitulos/03/intento-2.md`, no un patrón. Un escritor nunca puede tocar `intento-1.md`.
- `estado.json`, `registro.md`, `entrevista.md`, `informe-*.md`, `manuscrito.md`, `config.json`, `idea.md` y todo lo aprobado están **siempre** fuera de zona para cualquier subagente.
- Registra `estado.json` y `registro.md` como tuyos: si aparecen en `git status` es porque los has escrito tú en este paso; no cuentan como fuera de zona.
- El límite de turnos (`turnos_por_invocacion`) va en el prompt; si el subagente vuelve sin entregar, es incumplimiento y sigue este mismo circuito.
