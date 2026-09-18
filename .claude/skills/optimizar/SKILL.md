---
name: optimizar
description: Bucle de mejora automática del prompt de un agente del harness. Usar cuando el usuario pida optimizar, calibrar o mejorar el prompt de un agente ("/optimizar revisor-encargo --metrica recall_revisor --vueltas 10"), o ver el resultado de una optimización anterior. Nunca dentro de /novela.
argument-hint: <agente> --metrica <score> --vueltas N [--tope-invocaciones M] [--conjunto <nombre>] | continuar <carpeta> [--vueltas N] | estado <carpeta>
---

# /optimizar — bucle de optimización de prompts

Eres el **orquestador del bucle** de `specs/functional.md` §9.5. Coordinas un agente que propone (`optimizador`), un agente que se ejecuta (el optimizado) y unos guiones que puntúan. Escribes todos los ficheros del bucle, impones los límites y decides parar.

**Este bucle está fuera del harness de la novela.** No lo llama `/novela` nunca, no escribe en `novelas/` (solo lee capítulos como entrada de un caso) y no decide si un capítulo se aprueba. La spec manda sobre este fichero.

**Tres papeles, y tú no mezclas ninguno**: el optimizador propone y **nunca** puntúa; el juez es `puntuar.py` contra el conjunto etiquetado; el agente optimizado solo se ejecuta. Si en algún momento te ves tentado de juzgar tú una variante —«esta se ve mejor»—, para: ese es exactamente el lazo cerrado que el bucle existe para romper (E5c).

Argumentos recibidos: `$ARGUMENTS`

## 0. Comandos

| Forma | Hace |
|---|---|
| `<agente> --metrica <score> --vueltas N [--tope-invocaciones M] [--conjunto <nombre>]` | §1 → §9 |
| `continuar <carpeta> [--vueltas N]` | §0.1 → §8 → §9: retoma una ejecución parada |
| `estado <carpeta>` | §10, solo lectura |

Por defecto `--tope-invocaciones` = `(N + 1) × casos_del_conjunto × 1,2`, redondeado hacia arriba. `--conjunto` por defecto es el único `.jsonl` de `herramientas/optimizacion/conjuntos/`; si hay más de uno, es ERROR y pides cuál.

**Nunca infieras un argumento que falte.** Sin `--metrica` o sin `--vueltas`, para y pídelos: un bucle que se inventa su propio objetivo no demuestra nada.

## 0.1 continuar(carpeta) → sigue donde lo dejó

Una ejecución que paró sin agotar su presupuesto se retoma sin repetir nada de lo ya medido. **La línea base y las vueltas hechas no se vuelven a ejecutar**: ya están puntuadas en disco y repetirlas gastaría invocaciones para obtener el mismo número.

1. Lee `carpeta/ejecucion.json`: de ahí salen `agente`, `metrica`, `conjunto`, `objetivo` y los topes. **No los vuelvas a pedir ni los cambies**; si el usuario quiere otro objetivo, es otra ejecución, porque mezclar dos objetivos en una curva la hace ilegible.
2. `--vueltas N` solo **amplía** el presupuesto. Bajarlo por debajo de las vueltas ya hechas es ERROR.
3. Comprueba, y para si falla alguna:
   - `git hash-object .claude/agents/<agente>.md` coincide con `carpeta/produccion.hash`. Si no, la ejecución anterior dejó una variante instalada: restaura desde `carpeta/produccion.md` y dilo en el progreso antes de seguir.
   - El hash del conjunto sigue siendo el de `ejecucion.json`. Si cambió, **para**: las vueltas nuevas no serían comparables con las viejas.
   - `preparar.py --comprobar` con los valores de `ejecucion.json`.
4. `vuelta_inicial` = última línea de `carpeta/vueltas.jsonl` + 1. `mejor_control` y `mejor.md` salen de disco, no se recalculan.
5. Recupera el contador de estancamiento contando hacia atrás las líneas consecutivas con `aceptada: false` desde el final. Sin eso, el aborto por 3 vueltas sin mejora se reiniciaría y el bucle daría vueltas de más.
6. Sigue en §8 desde `vuelta_inicial`.

Al cerrar, `informe.md` se **reescribe entero** con todas las vueltas, no solo las nuevas, y dice cuántas veces se ha consultado el control **en total** — que es la cifra con la que hay que leer el resultado (§9.5.3).

## 1. comprobar_prerrequisitos(agente, metrica, conjunto) → ok | FALTA

```
Bash: python herramientas/optimizacion/preparar.py --comprobar \
        --agente <agente> --metrica <metrica> --conjunto <conjunto>
```

El guion comprueba los cinco requisitos del TRIGGER (spec §9.5.1) y sale con código 0 o 1 imprimiendo, requisito a requisito, `OK` o `FALTA` con el detalle.

Si sale 1: **muestra su salida tal cual y termina.** No arregles nada, no propongas un rodeo, no ejecutes «solo la vuelta 0 para ver». El bucle no arranca sin sus cinco requisitos, y ese es el valor del bloque: te ahorra descubrir en la vuelta 8 que la métrica no medía lo que creías.

## 2. preparar_ejecucion(agente, …) → carpeta

1. `carpeta = optimizaciones/<agente>-<AAAAMMDD-HHMM>/`. Créala.
2. Copia `.claude/agents/<agente>.md` a `carpeta/produccion.md`. Guarda su hash:
   `Bash: git hash-object .claude/agents/<agente>.md > carpeta/produccion.hash`
3. Copia `produccion.md` a `carpeta/mejor.md` (en la vuelta 1 la mejor es la de producción).
4. Si no existe, crea `optimizaciones/<agente>/lecciones.md` con su cabecera.
5. Escribe `carpeta/ejecucion.json`: agente, métrica, conjunto y su `conjunto_hash` (sha256 del `.jsonl`, 12 caracteres), vueltas, tope de invocaciones, objetivo, restricciones, instante de inicio, y `invocaciones: 0`.
6. Escribe la primera línea de `carpeta/vueltas.jsonl` cuando termine la vuelta 0, no antes.

**El hash del conjunto se congela aquí.** Si el fichero del conjunto cambia a mitad, las vueltas dejan de ser comparables; §9 lo comprueba al cerrar y lo dice en el informe.

## 3. ejecutar_split(carpeta, split, etiqueta) → informes

Para cada caso del `split` (`busqueda` o `control`) del conjunto:

```
Agent(subagent_type = <agente>, model = <el del frontmatter>,
      prompt = <las rutas de entradas[] del caso, tal como las pide su contrato>,
      run_in_background = false)
```

- `run_in_background = false` **siempre y explícito**, por lo mismo que en `/novela`: el paso siguiente es validar la salida, y una invocación en segundo plano no te da nada que validar.
- Los casos de un mismo split son independientes: puedes lanzarlos de varios en varios en un mismo mensaje para que corran en paralelo. **No mezcles splits en un mismo mensaje**, para que el recuento de invocaciones por split quede limpio.
- Cada salida se escribe tal cual en `carpeta/vuelta-NN/<split>/<id_caso>.json`, sin retocarla. Si un agente devuelve algo que no es el JSON de §5.6, **guárdalo igual** y anota `contrato: incumple` en el índice: un incumplimiento de formato es un resultado del experimento, no un error que tapar.
- Suma cada invocación a `ejecucion.invocaciones` y guárdalo. Si supera el tope → ABORTO `TOPE_INVOCACIONES` (§8).

Nunca pases al agente optimizado nada que no pida su contrato (spec §5), y **nunca** el conjunto etiquetado.

## 4. puntuar(carpeta, vuelta, split) → score

```
Bash: python herramientas/optimizacion/puntuar.py \
        --carpeta <carpeta> --vuelta <NN> --split <split> \
        --agente <agente> --metrica <metrica> --conjunto <conjunto>
```

Escribe `carpeta/vuelta-NN/<split>/score.json` con el valor, el desglose por clase y las restricciones. **Tú no calculas el score**: lo lees de ahí.

La publicación en Langfuse va aparte y es **fail-open**:

```
Bash: python herramientas/optimizacion/puntuar.py --publicar --carpeta <carpeta> --vuelta <NN> || true
```

Si falla, anótalo en el progreso y **sigue**. Perder la curva no es perder el experimento (spec §9.3 regla 3).

## 4.1 vuelta 0 — línea base

Con `produccion.md` instalado (es decir, el repositorio tal cual): `ejecutar_split(busqueda)`, `ejecutar_split(control)`, `puntuar` los dos. Escribe la línea 0 de `vueltas.jsonl` con `operacion: null` y `aceptada: null`.

Sin esta vuelta no hay contra qué medir «mejora ≥ 0,10». Si la saltas, el bucle entero no significa nada.

## 5. proponer_variante(carpeta, vuelta) → variante | INCUMPLE

1. Escribe `carpeta/vuelta-NN/diagnostico.md` a partir de los `score.json` del split de **búsqueda** de la vuelta anterior: defectos esperados y vistos **por clase**, y nada más. **Sin citas, sin capítulos, sin casos concretos.** Si copias un caso ahí, has filtrado el examen.
2. Invoca:

```
Agent(subagent_type = optimizador, model = opus, run_in_background = false,
      prompt = rutas de: carpeta/produccion.md, carpeta/mejor.md,
               carpeta/vuelta-NN/diagnostico.md,
               optimizaciones/<agente>/lecciones.md)
```

3. Extrae los dos bloques (`propuesta.json`, `variante.md`) con las reglas de bloques de `/novela` (`procedimientos/invocar.md`). Si falta uno, o `operacion` no está en 1..5, o `hipotesis` está vacía → incumplimiento: reintenta una vez con el motivo exacto; si vuelve a fallar, ABORTO `INCUMPLE_CONTRATO`.
4. Escribe `carpeta/vuelta-NN/variante.md` y `carpeta/vuelta-NN/propuesta.json`.

## 6. comprobar_variante(carpeta, vuelta) → ok | RECHAZADA

```
Bash: python herramientas/optimizacion/comprobar_variante.py \
        --variante <carpeta>/vuelta-NN/variante.md \
        --produccion <carpeta>/produccion.md \
        --conjunto <conjunto> --metrica <metrica>
```

Comprueba las cinco prohibiciones de §9.5.5 —citas del conjunto, nombre de la métrica, frontmatter y frase de contrato, esquema de salida, tamaño— y sale con 0 o 1.

**Esto es una puerta, no un consejo.** Si sale 1, la variante **no se instala**: se anota como vuelta rechazada con el motivo del guion, se suma al contador de estancamiento y se pasa a la vuelta siguiente sin gastar una sola invocación del agente optimizado. El bucle no discute con el guion ni le pide al optimizador que «lo arregle un poco».

## 7. instalar / restaurar

```
instalar:   cp <carpeta>/vuelta-NN/variante.md .claude/agents/<agente>.md
restaurar:  cp <carpeta>/produccion.md         .claude/agents/<agente>.md
```

**Invariante: el fichero del agente se restaura siempre**, al aceptar, al rechazar, al parar, al abortar y si algo falla por el camino. Antes de terminar cualquier camino de salida:

```
Bash: git hash-object .claude/agents/<agente>.md
```

y compara con `produccion.hash`. Si no coincide → PARADA `AGENTE_NO_RESTAURADO`, dilo en el informe y no hagas nada más: un repositorio con una variante instalada generaría novelas con un prompt que nadie aprobó.

Es la pieza más frágil del hito 1 y solo existe aquí: la herramienta `Agent` lee el contrato del disco y no admite un prompt inyectado. En el hito 2 desaparece (spec §9.5.6).

## 8. Una vuelta

```
para vuelta en vuelta_inicial..N:          # vuelta_inicial = 1, o §0.1 al continuar
    variante = proponer_variante(carpeta, vuelta)
    si comprobar_variante(...) == RECHAZADA:
        anota(vuelta, aceptada = false, motivo = <el del guion>, invocaciones = 0)
        sin_mejora += 1; continuar

    instalar(variante)
    ejecutar_split(carpeta, busqueda, vuelta); s_busqueda = puntuar(..., busqueda)
    ejecutar_split(carpeta, control,  vuelta); s_control  = puntuar(..., control)
    restaurar()

    si alguna restriccion dura incumple (score.json lo dice):
        anota(aceptada = false, motivo = "restriccion: <cual>"); sin_mejora += 1
    si no si s_control >= mejor_control + 0,10:
        cp variante -> carpeta/mejor.md; mejor_control = s_control
        anota(aceptada = true); sin_mejora = 0
    si no:
        anota(aceptada = false, motivo = "control +<delta> < 0,10"); sin_mejora += 1

    añade la linea `leccion` de propuesta.json a optimizaciones/<agente>/lecciones.md
    publica en Langfuse (fail-open)

    si mejor_control >= <objetivo>:   PARADA METRICA_ALCANZADA
    si sin_mejora >= 3:               ABORTO ESTANCAMIENTO
    si invocaciones > tope:           ABORTO TOPE_INVOCACIONES
PARADA VUELTAS_AGOTADAS
```

Una línea de `vueltas.jsonl` por vuelta, **siempre**, también en las rechazadas y en los abortos:

```json
{"vuelta": 3, "operacion": 2, "hipotesis": "…", "score_busqueda": 0.55, "score_control": 0.40,
 "mejor_control": 0.40, "aceptada": false, "motivo": "control +0,05 < 0,10", "invocaciones": 13,
 "restricciones": {"cita_verificable": 0.93, "palabras_prompt": 812, "tope_palabras": 940}}
```

`aceptada` se escribe **después** de mirar control, no antes. Anotarla por lo que se espera en vez de por lo que salió es cómo se fabrica una curva bonita.

## 9. cerrar_optimizacion(carpeta, motivo)

1. `restaurar()` y comprueba el hash (§7).
2. Comprueba que el hash del conjunto sigue siendo el de `ejecucion.json`. Si cambió, dilo en el informe: las vueltas no son comparables entre sí.
3. Si el motivo es `METRICA_ALCANZADA`, publica `mejor.md` en Langfuse Prompt Management con etiqueta `candidato`, fail-open:
   `Bash: python herramientas/optimizacion/preparar.py --publicar-candidato --carpeta <carpeta> || true`
4. Escribe `carpeta/informe.md`: motivo, línea base, mejor score en control y en qué vuelta, operación que lo consiguió, vueltas rechazadas y por qué, invocaciones gastadas contra el tope, estado del hash del agente, y **cuántas veces se consultó el split de control** con la reserva de §9.5.3.
5. **No promuevas nada.** Termina diciendo al usuario, en una línea, cuál es el fichero candidato y que moverlo a producción es un commit suyo.

## 10. estado <carpeta>

Solo lectura: lee `ejecucion.json`, `vueltas.jsonl` e `informe.md` si existe, y resume en una tabla vuelta a vuelta. No ejecutas nada, no restauras nada, no tocas el agente.

## 11. Lo que este bucle no hace, nunca

- No se invoca desde `/novela`, ni al revés.
- No escribe en `novelas/`. Lee capítulos como entrada de un caso y nada más.
- No promueve un prompt a producción: deja un candidato.
- No puntúa con tu criterio. Si `puntuar.py` no puede dar un número, la vuelta no tiene score y se anota así.
- No sigue adelante con un prerrequisito a medias.
