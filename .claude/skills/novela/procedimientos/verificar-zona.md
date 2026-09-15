# Invocar un subagente y verificar su zona

Se aplica a **cada** invocación de subagente. Entrada: nombre del subagente, prompt, zona permitida (lista de rutas relativas a `novelas/<slug>/`), validación de artefactos.

## Idea

Antes de invocar, el orquestador **fija en el índice de git** (`git add`) todo lo que hay en la carpeta: sus propios ficheros (`estado.json`, `registro.md`) y los artefactos de pasos anteriores del mismo capítulo que aún no se han commiteado (p. ej. `intento-K.md` cuando se va a invocar al revisor). Así, al volver el subagente, **lo que difiere del índice es exactamente lo que ha tocado él**, y `git checkout -- <ruta>` devuelve cualquier fichero a como estaba justo antes de la invocación. No hace falta que la carpeta esté limpia: solo que esté fijada.

Nunca uses `git checkout -- novelas/<slug>` ni `git clean` en mitad de un capítulo para "limpiar": borrarías el trabajo de los pasos anteriores. Eso solo se hace en `descartar()` (abajo), al reanudar o al parar.

## Procedimiento

```
para intento_tecnico en 1..reintentos_tecnicos:
    a. git add -A novelas/<slug>                  → fija el estado previo en el índice
    b. registra invocacion(subagente, modelo, N, K, intento_tecnico, inicio, palabras_entrada)
       palabras_entrada = suma de palabras de los ficheros que el prompt manda leer
    c. Agent(subagent_type = <subagente>, model = <SKILL.md §8>, prompt = <prompt> [+ "Motivo del reintento: <motivo>" si intento_tecnico > 1])
       estado.invocaciones[<subagente>] += 1
    d. Si la herramienta falla o el mensaje final está vacío → motivo = "fallo técnico"; ir a f.
    e. cambios = git diff --name-only -- novelas/<slug>                         (modificados respecto al índice)
              ∪ git ls-files --others --exclude-standard novelas/<slug>          (nuevos)
       quita de cambios estado.json y registro.md: los has tocado tú en b.
       fuera = cambios − zona                     (rutas relativas exactas)
       Si fuera no está vacío:
           para cada ruta en fuera: si estaba en el índice → git checkout -- <ruta>; si es nueva → borrarla.
           registra escritura_fuera_de_zona(subagente, rutas, revertido=true)
           motivo = "ESCRITURA FUERA DE ZONA: <rutas>. Solo puedes escribir en: <zona>."
           ir a f.
       Comprueba el mensaje final y los artefactos según la validación indicada.
       Si falla → motivo = "INCUMPLE CONTRATO: <qué falta o qué está mal>"; ir a f.
       ÉXITO → palabras_salida = palabras de los ficheros de la zona que ha escrito (o del YAML devuelto, si no escribe ficheros)
               registra invocacion(resultado=ok, palabras_salida); guarda estado.json; return.
    f. registra invocacion(resultado = fallo | incumple, motivo)
       Los artefactos a medias dentro de la zona se dejan: el reintento del mismo subagente los sobreescribe.
       registra decision_harness(reintento, intento_tecnico)
       continuar el bucle

agotados:
    motivo_parada = FALLO_TECNICO_PERSISTENTE si el último motivo fue fallo técnico, si no INCUMPLE_CONTRATO
    descartar(novelas/<slug>)                     → nada a medias
    → cierre.md con ese motivo, fase_previa = fase actual
```

## descartar(carpeta)

Devuelve la carpeta al **último commit**. Solo se usa al reanudar (`SKILL.md` §6.1) y al parar por agotamiento de reintentos. Como puede haber ficheros fijados en el índice por el paso (a), hay que deshacer el índice antes:

```
git reset -q HEAD -- <carpeta>
git checkout -- <carpeta>
git clean -fd <carpeta>
```

Registra `paso_descartado` con la lista de rutas que se han perdido.

## Notas

- La zona se pasa **con N y K concretos**: `capitulos/03/intento-2.md`, no un patrón. Un escritor nunca puede tocar `intento-1.md`.
- `estado.json`, `registro.md`, `entrevista.md`, `informe-*.md`, `manuscrito.md`, `config.json`, `idea.md` y todo lo aprobado están **siempre** fuera de zona para cualquier subagente.
- El límite de turnos (`turnos_por_invocacion`) va en el prompt; si el subagente vuelve sin entregar, es incumplimiento y sigue este mismo circuito.
- `palabras_entrada` y `palabras_salida` son recuentos aproximados (`wc -w` sirve). Son el dato que permite estimar cuánto costaría la misma novela con otro modelo o en otro runner (`specs/functional.md` §6.6). No hace falta precisión; hace falta que estén en todas las filas.
