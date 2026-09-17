# invocar — una invocación de agente, con reintentos, validación y registro

Toda llamada a un agente pasa por aquí. Entrada: agente, modo, K (intento del capítulo, o `–`), entradas (rutas que el prompt manda leer), validación (qué forma debe tener la salida), destinos (a qué ruta va cada bloque). Salida: la salida ya validada y escrita en disco, o una PARADA.

## invocar(agente, modo, K, entradas, validacion, destinos) → salida

```
para intento_tecnico en 1..config.limites.reintentos_tecnicos:
    modelo = elegir_modelo(agente, K, intento_tecnico, modo)
    pal_entrada = suma de `wc -w` sobre las rutas de `entradas`
    registra invocacion(agente, modo, modelo, intento_tecnico, inicio, pal_entrada)
    prompt = <prompt del procedimiento que llama> + (si intento_tecnico > 1) "\n\nMotivo del reintento: <motivo>. Corrige exactamente eso."
    resultado = Agent(subagent_type = agente, model = modelo, prompt = prompt,
                      run_in_background = false)          # ver abajo: el bucle es secuencial
    e.invocaciones[agente] += 1; guardar(e)

    si la herramienta falla o el mensaje final está vacío:
        motivo = "fallo técnico: <error>"; tipo = fallo
    si el resultado viene marcado como parcial (agotó maxTurns):
        motivo = "incumple contrato: agotó los turnos sin entregar"; tipo = incumple
    si no:
        salida = extraer(resultado, validacion)             # bloques o JSON, abajo
        si extraer falla: motivo = "incumple contrato: <qué falta o qué está mal>"; tipo = incumple
        si no:
            escribe cada parte de `salida` en su ruta de `destinos` (escritura completa del fichero)
            pal_salida = suma de `wc -w` sobre lo escrito
            registra invocacion(resultado = ok, pal_salida, tok_* si la herramienta los devolvió)
            return salida

    registra invocacion(resultado = tipo, motivo)
    registra decision_harness(reintento, intento_tecnico, motivo)
    muestra "[…] reintento <intento_tecnico>/<max>: <motivo resumido>"

agotados:
    motivo_parada = FALLO_TECNICO_PERSISTENTE si el último tipo fue fallo, si no INCUMPLE_CONTRATO
    descartar(carpeta)
    cerrar(carpeta, PARADA, motivo_parada, detalle = último motivo)      # cierre.md
```

**`run_in_background = false` siempre, y explícito.** La herramienta `Agent` corre en segundo plano por defecto y devuelve un identificador en vez de la salida; el paso siguiente de `invocar` es `extraer(resultado, validacion)`, así que una invocación en segundo plano no te daría nada que validar y el bucle avanzaría sobre un resultado que no existe. Es la única excepción a la norma general de Claude Code de no bloquear la sesión: aquí la acción siguiente **siempre** depende del resultado. Nunca des por hecha la salida de un agente que aún no ha terminado. (Detalle de Claude Code: en el hito 2 el runner espera la respuesta de la API y no hay nada que declarar.)

Cada agente recibe **exactamente** las rutas de su contrato (spec §5): ni una más para "dar contexto", ni una menos. En el prompt van rutas, no contenidos; el agente las lee. Todos los prompts terminan con: "Devuelve tu salida en el mensaje final con la forma exacta de tu definición. No escribas ningún fichero."

## elegir_modelo(agente, K, intento_tecnico, modo) → modelo

```
base = config.modelos[clave(agente)]              # interrogador | escritor | resumidor |
                                                  # revisor_encargo | revisor_continuidad
esc  = config.modelos.escalado
si no esc.activo                                                          → base
si intento_tecnico > 1 y esc.tras_fallo_tecnico                           → esc.modelo
si agente == revisor-continuidad y modo ∈ {canon, arco, global}
        y esc.revision_arco_y_global                                      → esc.modelo
si agente == escritor y K >= esc.escritor_desde_intento                   → esc.modelo
si agente es un revisor y K >= esc.revisor_desde_intento                  → esc.modelo
en otro caso                                                              → base
```

`clave(agente)` traduce el nombre del fichero a la clave de `config.modelos`: los guiones pasan a guion bajo (`revisor-encargo` → `revisor_encargo`). `escritor_desde_intento` y `revisor_desde_intento` miran el intento **K del capítulo**, que cuenta también los ajustes de longitud: es deliberado, porque un capítulo que va por el intento 3 necesita el modelo bueno se haya gastado en corregir o en recortar.

Con `proveedor: claude-code` el valor va tal cual al parámetro `model` de la herramienta `Agent` (`opus`, `sonnet`, `haiku`, `fable`). El modelo elegido se registra en la fila `invocacion`.

## extraer(resultado, validacion)

**Bloques** (interrogador, escritor, resumidor). Cada documento está entre una línea exactamente igual a `=== ARCHIVO: <ruta> ===` y una línea exactamente igual a `=== FIN ===`. Reglas:

- Deben aparecer **todos** los bloques que la validación exige, con la ruta esperada, y ninguno vacío. Un bloque de más se ignora y se anota como observación en el registro.
- El contenido es lo que hay entre las dos líneas, sin ellas. Si el agente envolvió el bloque en una valla de código, quítala.
- Validación de contenido por agente:
  - `biblia.md`: frontmatter parseable; secciones Premisa, El mundo, Tono y voz, Personajes, Reglas inviolables (numeradas, 3–7), Decisiones del interrogador.
  - `escaleta.md`: frontmatter con `titulo`, `capitulos`, `arcos` (lista con `n, titulo, acto, desde, hasta, objetivo, sucesos_clave, hilos_abre, hilos_cierra`). Los rangos cubren 1..`capitulos` sin huecos ni solapes; ningún arco supera `formato.capitulos_por_arco`; `capitulos` entre `perfil.capitulos_min` y `capitulos_max`; los tres actos aparecen.
  - `arcos/arco-AA.md`: frontmatter con `arco`, `desde`, `hasta`, `entradas` (una por capítulo del rango, con `n, titulo, objetivo, sucesos, personajes, gancho, palabras_objetivo`); cada `palabras_objetivo` entre `formato.palabras_min_capitulo` y `palabras_max_capitulo`; cada `suceso_clave` del arco en la escaleta de alto nivel aparece en los `sucesos` de alguna entrada.
  - `intento-K.md`: empieza por una línea `# ` (título) y tiene cuerpo no vacío.
  - `resumen-K.md`: frontmatter con `capitulo`, `intento`, `hilos_abiertos`, `hilos_cerrados`, `personajes`; secciones Hechos, Cambios en personajes, Elementos introducidos, Enlace.
  - `libro-estado-K.md`: secciones Personajes, Hilos abiertos, Hilos cerrados, Elementos, Reglas en vigor; `wc -w` ≤ `memoria.libro_estado_max_palabras` × 1,5 (por encima, incumplimiento: "condensa"). Entre 1,0 y 1,5 veces, aviso en el progreso.

**JSON** (los dos revisores). El mensaje final, sin vallas de código, debe parsear como un objeto con exactamente las claves `veredicto` ∈ {APROBADO, RECHAZADO}, `problemas` (lista; cada elemento con `gravedad`, `donde`, `que`, `por_que` no vacíos) y `observaciones` (lista de cadenas). La `gravedad` permitida depende de quién responde:

| Agente | Gravedades que puede emitir |
|---|---|
| `revisor-encargo` | 2, 4 |
| `revisor-continuidad` | 1, 5 (y solo 1 en modo `canon`) |

Cualquier otra cosa es incumplimiento con el motivo exacto ("falta la clave observaciones", "gravedad 3 no la emite ningún revisor: la longitud la comprueba el harness", "gravedad 1 no es del revisor de encargo", "texto fuera del JSON").

## Los dos revisores de un mismo intento

Se lanzan **en el mismo mensaje**, en dos llamadas a la herramienta `Agent`, para que corran en paralelo. Las dos llevan `run_in_background = false` igual que el resto: dos llamadas en un mismo mensaje ya corren a la vez, y el paralelismo que hace falta aquí es ese, no el de segundo plano. Cada uno recibe solo las rutas de su contrato (spec §5.4, §5.5): no le des al de encargo el libro de estado ni al de continuidad la escaleta del arco. Tienen sus propias filas en el registro, con su propio `pal_entrada` y su propio modelo.

Si uno falla y el otro entrega, **reintenta solo el que falló** con su propio contador de `reintentos_tecnicos`; la salida del que entregó se conserva y no se vuelve a pedir. Solo si el que falla agota sus reintentos se llega a la parada.

## descartar(carpeta)

Devuelve la carpeta al **último commit**. Solo se usa al reanudar (SKILL.md §5) y al parar por agotamiento de reintentos.

```
git reset -q HEAD -- novelas/<slug>
git checkout -- novelas/<slug>
git clean -fdq novelas/<slug>
```

Registra `paso_descartado` con las rutas que se han perdido. Como nada aprobado está sin commitear, nunca se pierde nada aprobado.

## Volumen

`pal_entrada` y `pal_salida` van en todas las filas `invocacion`, contadas con `wc -w`. `tok_entrada`, `tok_salida` y `coste_usd` se rellenan solo si la herramienta los devuelve (en el hito 1 normalmente no; en el runner siempre). Es el dato de `specs/functional.md` §6.6.
