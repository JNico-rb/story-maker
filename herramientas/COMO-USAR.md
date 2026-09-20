# Cómo usar las herramientas de medida

**Para quién es este fichero:** para ti, y para Claude Code en una sesión futura que tenga que usar `/optimizar` o `/validar` sin haber estado el día que se montaron. Aquí va el *cómo*; el *qué* y el *por qué* están en `specs/technical.md` §9.5 y §9.6, y lo descartado en el CHANGELOG 0.9.0 y 0.10.0. **La spec manda sobre este fichero.**

Las dos herramientas están **fuera del harness**: `/novela` no las llama nunca, no escriben en `novelas/`, y si borras `herramientas/validacion/`, `herramientas/optimizacion/`, `validaciones/` y `optimizaciones/` el sistema sigue generando novelas igual.

---

# 0. Referencia de comandos

## Skills (desde Claude Code)

| Comando | Qué hace | Qué escribe |
|---|---|---|
| `/validar <carpeta>` | Puntúa el manuscrito de una novela terminada y da el delta contra la línea base | `validaciones/<slug>/score.json` e `informe.md` |
| `/validar <carpeta> --congelar-base` | Lo mismo, y fija esa medición como línea base | Además `validaciones/_base.json` |
| `/validar <carpeta> --publicar` | Lo mismo, y publica las puntuaciones en Langfuse (fail-open) | Ídem + Langfuse |
| `/validar estado` | Resume las validaciones hechas. Solo lectura | Nada |
| `/optimizar <agente> --metrica <score> --vueltas N` | Arranca un bucle de mejora del prompt de ese agente | `optimizaciones/<agente>-<fecha>/` |
| `/optimizar <agente> … --tope-invocaciones M` | Ídem con tope explícito (por defecto `(N+1) × casos × 1,2`) | Ídem |
| `/optimizar <agente> … --conjunto <nombre>` | Ídem eligiendo conjunto (por defecto, el único que haya) | Ídem |
| `/optimizar continuar <carpeta>` | **Retoma** una ejecución parada, sin repetir lo ya medido | Añade vueltas a la carpeta existente |
| `/optimizar continuar <carpeta> --vueltas N` | Ídem ampliando el presupuesto (solo amplía; bajarlo es ERROR) | Ídem |
| `/optimizar estado <carpeta>` | Tabla vuelta a vuelta. Solo lectura | Nada |

## Guiones (desde la terminal, sin pasar por la skill)

| Comando | Cuándo |
|---|---|
| `python herramientas/validacion/comprobar_patrones.py` | Siempre que toques `patrones.py`. Sale 1 si el detector no es usable |
| `python herramientas/validacion/calibrar.py [--escribir]` | Tras tocar el detector. `--escribir` actualiza `calibracion.md` |
| `python herramientas/validacion/validar.py <carpeta> [--congelar-base] [--publicar]` | Lo que hace `/validar` por dentro |
| `python herramientas/optimizacion/preparar.py --comprobar --agente A --metrica M --conjunto C` | Antes de arrancar un bucle. Sale 1 si falta un requisito |
| `python herramientas/optimizacion/preparar.py --subir-conjunto --conjunto C` | Espejo del conjunto en Langfuse |
| `python herramientas/optimizacion/preparar.py --publicar-candidato --carpeta <c>` | Publica `mejor.md` con etiqueta `candidato` |
| `python herramientas/optimizacion/comprobar_variante.py --variante V --produccion P --conjunto C --metrica M` | La puerta antes de instalar una variante |
| `python herramientas/optimizacion/puntuar.py --carpeta <c> --vuelta NN --split busqueda\|control --agente A --metrica M --conjunto C` | Puntúa un split |
| `python herramientas/optimizacion/puntuar.py --publicar --carpeta <c> --vuelta NN` | Sube esa vuelta a Langfuse |
| `python herramientas/optimizacion/casos/generar.py` | Regenera los casos mutados y su etiquetado |

## Estado actual del repositorio

| | |
|---|---|
| Línea base de `/validar` | Novela A (opus), índice **0,934** |
| Detector de lengua | `v1`, hash `59ca75b`, precisión **1,000**, recall **0,462** |
| Conjunto de `/optimizar` | `ascensores-v1` — 9 casos, 32 defectos (20 búsqueda / 12 control) |
| Ejecución de `/optimizar` parada | `optimizaciones/revisor-encargo-20260918-1600`, 2 vueltas de 4, mejor control 0,500 |

---

# 1. Si eres Claude Code, lee esto antes de ejecutar nada

Cinco reglas que **no** están en tu criterio, están en la spec, y que romperlas invalida el resultado entero:

1. **Nunca juzgues tú una variante ni un manuscrito.** Ni «esta se ve mejor», ni «el texto ha mejorado». Quien puntúa es un guion contra verdad de campo. Ese lazo cerrado —el que propone también corrige— es el que produjo `6/6 CUMPLE` sobre un manuscrito con 30 defectos verificados (E5c), y es la razón de existir de las dos herramientas.
2. **Si un guion sale con código 1, para y muestra su salida tal cual.** No arregles el conjunto, no propongas un rodeo, no ejecutes «solo la vuelta 0 para ver». La puerta existe para ahorrarte descubrir en la vuelta 8 que la métrica no medía lo que creías.
3. **Repite al usuario las reservas, no las dejes solo en el fichero.** Sobre todo `n=1` en `/validar`: nunca digas «haiku escribe peor», di «esta novela de haiku puntuó 0,365 menos que esta de opus».
4. **El prompt del agente se restaura siempre** en `/optimizar`, también al abortar y también si algo falla. Antes de terminar cualquier camino de salida, `git hash-object .claude/agents/<agente>.md` contra `produccion.hash`. Si no coincide es PARADA: el repositorio tendría instalado un prompt que nadie aprobó y la próxima novela saldría con él.
5. **Langfuse es fail-open.** Se calcula en local y se publica después, con `|| true`. Si falla la publicación, anótalo y sigue: perder la curva no es perder el experimento.

Y una que es de sentido común pero se olvida: **nunca pases el conjunto etiquetado al agente optimizado ni al optimizador.** El `deny` de `Read` sobre `herramientas/optimizacion/conjuntos/**` lo impide, pero no confíes en eso como única barrera.

---

# 2. `/validar` — puntuar un manuscrito

## Uso normal

```bash
python herramientas/validacion/validar.py novelas/<slug>
```

Salida:

```
precondiciones
  OK    ejecucion completa (8.7): etapa=completa, manuscrito.md=si
  OK    detector congelado: base 59ca75b / ahora 59ca75b
  OK    escala congelada: base v1 / ahora v1

tecnica-ascensores-peticion-ia-20260916-1719  ·  6391 palabras en 5 capitulos
  lengua         0.94 /mil  ->  0.531     base 1.000   -0.469
  repeticion     2.82 /mil  ->  0.824     base 0.494   +0.330
  GLOBAL                           0.569     base 0.934   -0.365
  n=1 por configuracion: no se declara mejora ni regresion establecida
```

## Las tres precondiciones

Si falta una, no mide y dice cuál:

1. La carpeta pasa §8.7: `etapa: completa` y `manuscrito.md` presente.
2. El **detector** está congelado: su hash coincide con el de la línea base.
3. La **escala** está congelada: misma versión de topes y pesos.

Las dos últimas existen porque un delta entre dos detectores distintos mide el detector, no el texto.

## Cambiar la línea base

```bash
python herramientas/validacion/validar.py novelas/<slug> --congelar-base
```

**Hoy la base es la novela A (opus), 0,934.** Cambiarla invalida la lectura de todos los deltas anteriores; hazlo solo sabiendo por qué.

## Cómo leer el número

Tres reservas que cambian lo que puedes afirmar:

1. **n=1.** La medición es determinista —re-medir da el mismo número—, así que el ruido no está en la medición sino en la generación: otra ejecución con la misma config daría otro manuscrito. Para afirmar «el modelo X escribe peor» hacen falta 3 ejecuciones por configuración.
2. **Recall 0,462.** El detector ve 6 de los 13 defectos etiquetados a mano. «0 hallazgos» significa «ninguno de los que sabe ver». El nivel absoluto es optimista; los deltas entre manuscritos no, porque el sesgo es el mismo en los dos.
3. **Tres clases fuera.** Coherencia interna, verosimilitud técnica y mundo post-IA (13 de los 30 defectos de E5) exigen un juez LLM independiente, que hoy no existe (`openrouter/free` no garantiza cuál contesta → A14).

## Si tocas el detector

```bash
python herramientas/validacion/comprobar_patrones.py       # 1. la puerta
python herramientas/validacion/calibrar.py --escribir      # 2. nueva precision/recall
python herramientas/validacion/validar.py novelas/tecnica-ascensores-peticion-ia --congelar-base   # 3. re-congelar
```

Saltarte el paso 3 no rompe nada: `/validar` te parará solo en la precondición 2.

## Añadir una clase de error

En `herramientas/validacion/patrones.py`, una entrada más en `CLASES`:

- `patron`: la **clase** de error, nunca la frase concreta. Un patrón con tres palabras seguidas de una cita del etiquetado se rechaza. Una palabra suelta del léxico sí vale: es miembro de la clase, no la instancia.
- `positivos`: al menos dos ejemplos **inventados por ti**, que no estén en ningún manuscrito, y que el patrón debe cazar.
- `negativos`: castellano correcto de forma parecida, que el patrón **no** debe cazar.

Después, los tres pasos de arriba. Si la precisión baja, la clase sobra: se prefiere ver menos con certeza que más con ruido.

---

# 3. `/optimizar` — mejorar el prompt de un agente

## Antes de nada

```bash
python herramientas/optimizacion/preparar.py --comprobar \
    --agente revisor-encargo --metrica recall_revisor --conjunto ascensores-v1
```

Los cinco requisitos del TRIGGER. Sale 1 si falta uno, antes de gastar una sola invocación.

## Arrancar uno nuevo

```
/optimizar revisor-encargo --metrica recall_revisor --vueltas 4
```

Por vuelta: el agente `optimizador` propone **una** operación de una taxonomía cerrada; `comprobar_variante.py` la deja pasar o no; se instala; se ejecutan los dos splits; se puntúa; se restaura el prompt original.

## Continuar uno parado

```
/optimizar continuar optimizaciones/revisor-encargo-20260918-1600
```

Retoma en la vuelta siguiente **sin repetir la línea base ni las vueltas hechas**: ya están puntuadas en disco y repetirlas gastaría invocaciones para obtener el mismo número. Hereda de `ejecucion.json` el agente, la métrica, el conjunto y el objetivo —**no se cambian**: otro objetivo es otra ejecución—, y arrastra `mejor_control`, `mejor.md` y el contador de estancamiento.

Antes de seguir comprueba que el fichero del agente está restaurado, que el `conjunto_hash` no ha cambiado, y los cinco prerrequisitos.

## Lo que hay que vigilar

- **La restauración**, regla 4 de §1. Comprobación manual: `git status --porcelain .claude/agents/` debe salir vacío.
- **Nada se promueve solo.** El bucle deja un candidato en `mejor.md`. Moverlo a producción es `cp` sobre `.claude/agents/<agente>.md` y un commit, y lo haces tú.
- **`lecciones.md` es la única memoria** entre ejecuciones. Está en `optimizaciones/<agente>/lecciones.md`, se versiona en git, y el optimizador la lee antes de proponer. Si se pierde, volverá a proponer variantes ya descartadas.

## Añadir casos al conjunto

`herramientas/optimizacion/casos/generar.py` construye los casos mutados **y sus etiquetas a la vez**, para que la etiqueta no pueda desviarse del defecto. Añade una entrada a `CASOS` con sus mutaciones y ejecútalo; si un ancla no aparece en el texto, falla en vez de generar una etiqueta que no corresponde a nada.

El `split` se escribe a mano en el fichero y **no se re-sortea nunca** entre vueltas.

---

# 4. Errores que vas a ver

| Mensaje | Qué pasa | Qué hacer |
|---|---|---|
| `FALTA 1. N defectos puntuables para <agente>` | El conjunto no tiene 30 defectos de las gravedades que ese agente emite | Etiquetar más casos de **su** contrato; un defecto de gravedad 1 no cuenta contra el revisor de encargo |
| `FALTA 2. ... no esta calibrada` | Falta `calibracion-<metrica>.md` | Calibrar antes de medir. Medir sin calibrar es lo que hacía `erratas.md` |
| `FALTA 3. ... tiene cambios sin commitear` | El prompt del agente está sucio y el bucle lo sobrescribiría | Commitear o descartar esos cambios |
| `RECHAZA sin citas del conjunto` | La variante copió texto del conjunto: memorizar el examen | Nada: la vuelta se anota rechazada y sigue |
| `RECHAZA rol y pregunta intactos` | La variante cambió el primer párrafo del agente | Ídem. Cambiar el rol es cambio de contrato y se decide en la spec |
| `RECHAZA no copia el examen` (en `comprobar_patrones`) | Un patrón lleva tres palabras seguidas de una cita etiquetada | Reescribir el patrón como clase, no como instancia |
| `FALTA detector congelado` | Tocaste `patrones.py` y no re-puntuaste la base | Los tres pasos de §2 |
| `No se valida: falta una precondicion` | La novela no está completa o no tiene `manuscrito.md` | Terminarla, o validar otra |
| `AGENTE_NO_RESTAURADO` | El repositorio tiene instalada una variante | **Parar.** `cp <carpeta>/produccion.md .claude/agents/<agente>.md` y verificar el hash |

---

# 5. Lo que ninguna de las dos hace, nunca

- **Entrar en el bucle de `/novela`.** Ni un `curl` dentro de `invocar()`. Los evaluadores nunca deciden si un capítulo se aprueba.
- **Escribir en `novelas/`.** Solo leen; el hook lo impone para `Edit` y `Write`.
- **Promover nada.** Dejan un resultado y una recomendación; mover un fichero o una etiqueta a producción lo haces tú.
- **Depender de Langfuse.** Todo se calcula en local. Sin red, pierdes la curva y nada más.
- **Declarar mejoras.** `/validar` da un delta con `n=1`; `/optimizar` solo acepta una variante si control mejora ≥ 0,10, y anota el motivo cuando no.
- **Sustituir a §8.3.** Aquellas son métricas de **proceso**, autoinformadas; estas son de **producto**. Conviven, y cuando discrepen el informe dice de dónde sale cada número.

---

# 6. Mapa de ficheros

```
herramientas/validacion/
  patrones.py              las clases de error, con ejemplos positivos y negativos
  comprobar_patrones.py    la puerta: patrones generales, nunca instancias
  calibrar.py              precision y recall contra el etiquetado
  calibracion.md           el resultado, y el techo declarado de la v1
  escala.json              topes y pesos, cada uno con el dato que lo sostiene
  validar.py               la medicion
  etiquetado/              verdad de campo etiquetada a mano (cierra A24)

herramientas/optimizacion/
  preparar.py              los cinco requisitos; --subir-conjunto; --publicar-candidato
  comprobar_variante.py    las cinco prohibiciones, antes de instalar
  puntuar.py               el score local, y --publicar a Langfuse
  casos/generar.py         casos mutados y etiquetas, de una sola fuente
  conjuntos/               los conjuntos etiquetados (no legibles desde la sesion)

.claude/skills/validar/    la skill /validar
.claude/skills/optimizar/  la skill /optimizar
.claude/agents/optimizador.md   el agente que propone variantes

validaciones/              resultados de /validar; _base.json es la linea base
optimizaciones/            resultados de /optimizar; lecciones.md es la memoria
```
