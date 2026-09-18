# Cómo usar las dos herramientas de medida

Guía de uso de lo que se montó el 18/09/2026: el **bucle de optimización de prompts** (`/optimizar`, spec §9.5) y el **validador de manuscrito** (`/validar`, spec §9.6). Las dos están **fuera del harness**: `/novela` no las llama nunca, no escriben en `novelas/` y si las borras el sistema sigue generando novelas igual.

La spec manda sobre este fichero. Aquí va el *cómo*; el *qué* y el *por qué* están en §9.5 y §9.6, y lo descartado en el CHANGELOG 0.9.0 y 0.10.0.

---

## Cuál de las dos necesitas

| Si tu pregunta es… | Usa | Qué te da |
|---|---|---|
| «¿este prompt detecta más problemas que el anterior?» | `/optimizar` | Un recall contra defectos etiquetados, vuelta a vuelta |
| «¿esta novela está mejor escrita que aquella?» | `/validar` | Un índice 0–1 sobre el texto, con delta contra una base |
| «¿el modelo barato escribe peor?» | `/validar` | Lo mismo, midiendo las dos novelas |
| «¿mi agente revisor se está inventando problemas?» | `/optimizar` | La restricción `cita_verificable` |

Regla corta: **`/optimizar` mide agentes, `/validar` mide manuscritos.**

---

# 1. `/validar` — puntuar un manuscrito

## Uso normal

```bash
# 1. comprobar que el detector es usable (hazlo si tocaste patrones.py)
python herramientas/validacion/comprobar_patrones.py

# 2. puntuar una novela terminada
python herramientas/validacion/validar.py novelas/<slug>
```

O desde Claude Code: `/validar novelas/<slug>`.

Sale algo así:

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

Escribe `validaciones/<slug>/score.json` (los datos) e `informe.md` (legible, con cada hallazgo y su cita).

## Congelar o cambiar la línea base

```bash
python herramientas/validacion/validar.py novelas/<slug> --congelar-base
```

Guarda esa medición en `validaciones/_base.json`. Todo lo que valides después se compara contra ella.

**Hoy la base es la novela A (opus), con 0,934.** Cámbiala solo si sabes por qué: cambiar la base invalida la lectura de todos los deltas anteriores.

## Publicar en Langfuse

```bash
python herramientas/validacion/validar.py novelas/<slug> --publicar
```

Necesita `LANGFUSE_PUBLIC_KEY` y `LANGFUSE_SECRET_KEY`. Si falla, **el resultado ya está en disco**: la publicación es fail-open a propósito (§9.3 regla 3).

## Cómo leer el número (esto es lo importante)

Tres reservas. No son letra pequeña; cambian lo que puedes afirmar:

1. **n=1.** El validador es determinista: re-medir da el mismo número. Pero otra ejecución con la misma config daría otro manuscrito. Con una novela por configuración **no puedes decir «haiku escribe peor»**; puedes decir «esta novela de haiku puntuó 0,365 menos que esta de opus». Para afirmar lo primero hacen falta 3 ejecuciones por configuración.
2. **Recall 0,462.** El detector ve 6 de los 13 defectos etiquetados a mano. «0 hallazgos» significa «ninguno de los que sabe ver». El nivel absoluto es optimista; los deltas entre manuscritos no, porque el sesgo es el mismo en los dos.
3. **Tres clases fuera.** Coherencia interna, verosimilitud técnica y mundo post-IA (13 de los 30 defectos de E5) no se miden: exigen un juez LLM independiente que hoy no existe.

## Si tocas el detector

Cambiar `patrones.py` o `escala.json` **invalida las comparaciones anteriores**. La secuencia correcta:

```bash
python herramientas/validacion/comprobar_patrones.py          # la puerta
python herramientas/validacion/calibrar.py --escribir         # nueva precision/recall
python herramientas/validacion/validar.py novelas/<base> --congelar-base
```

Si te saltas el paso 3, `/validar` te parará solo: la precondición 2 compara el hash del detector con el de la base y no deja comparar peras con manzanas.

## Añadir una clase de error nueva

En `herramientas/validacion/patrones.py`, una entrada más en `CLASES` con:

- `patron`: la **clase** de error, nunca la frase concreta. Un patrón con tres palabras seguidas de una cita del etiquetado se rechaza.
- `positivos`: al menos dos ejemplos **inventados por ti**, que no estén en ningún manuscrito, y que el patrón debe cazar.
- `negativos`: castellano correcto de forma parecida, que el patrón **no** debe cazar. Aquí es donde se atrapan los falsos positivos antes de que contaminen una medición.

Después, `comprobar_patrones.py` y `calibrar.py --escribir`. Si la precisión baja, la clase sobra.

---

# 2. `/optimizar` — mejorar el prompt de un agente

## Antes de nada: ¿puede arrancar?

```bash
python herramientas/optimizacion/preparar.py --comprobar \
    --agente revisor-encargo --metrica recall_revisor --conjunto ascensores-v1
```

Comprueba los cinco requisitos y **sale 1 si falta uno**, antes de gastar una sola invocación. Es el bloque que te ahorra descubrir en la vuelta 8 que la métrica no medía lo que creías.

## Lanzarlo

```
/optimizar revisor-encargo --metrica recall_revisor --vueltas 4
```

Por vuelta: el agente `optimizador` propone **una** operación de una taxonomía cerrada, `comprobar_variante.py` la deja pasar o no, se instala, se ejecutan los dos splits, se puntúa y se restaura el prompt original.

## Lo que hay que vigilar

- **La restauración.** El bucle copia la variante sobre `.claude/agents/<agente>.md` y la restaura siempre, comparando hashes. Si alguna vez ves `AGENTE_NO_RESTAURADO`, para: el repositorio tendría instalado un prompt que nadie aprobó. Comprobación manual: `git status --porcelain .claude/agents/`.
- **Nada se promueve solo.** El bucle deja un candidato en `mejor.md`. Moverlo a producción es copiarlo sobre `.claude/agents/<agente>.md` y hacer commit, y lo haces tú.
- **`lecciones.md` es la única memoria.** Está en `optimizaciones/<agente>/lecciones.md`, se versiona en git y el optimizador la lee antes de proponer. Si se pierde, volverá a proponer variantes ya descartadas.

## Añadir casos al conjunto

`herramientas/optimizacion/casos/generar.py` construye los casos mutados **y sus etiquetas a la vez**, para que la etiqueta no pueda desviarse del defecto. Añade una entrada a `CASOS` con sus mutaciones y ejecútalo; si un ancla no aparece en el texto, falla en vez de generar una etiqueta que no corresponde a nada.

Recuerda el `split`: se escribe a mano en el fichero y **no se re-sortea nunca** entre vueltas.

---

# 3. Errores que vas a ver, y qué significan

| Mensaje | Qué pasa |
|---|---|
| `FALTA 1. N defectos puntuables para <agente>` | El conjunto no tiene 30 defectos **de las gravedades que ese agente emite**. Un defecto de gravedad 1 no cuenta contra el revisor de encargo: no es su pregunta |
| `FALTA 2. ... no esta calibrada` | Falta `calibracion-<metrica>.md`. Medir con una métrica sin calibrar es lo que hacía `erratas.md` |
| `RECHAZA sin citas del conjunto` | La variante copió texto del conjunto etiquetado: memorizar el examen |
| `RECHAZA rol y pregunta intactos` | La variante cambió el primer párrafo del agente. Eso es cambio de contrato y se decide en la spec |
| `FALTA detector congelado` | Tocaste `patrones.py` y no re-puntuaste la base |
| `no se valida: falta una precondicion` | La novela no está completa, o no tiene `manuscrito.md` |

---

# 4. Lo que ninguna de las dos hace

- **Entrar en el bucle de `/novela`.** Ni un `curl` ni una llamada dentro de `invocar()`. Los evaluadores nunca deciden si un capítulo se aprueba.
- **Escribir en `novelas/`.** Solo leen. El hook lo impone para `Edit` y `Write`.
- **Promover nada.** Las dos dejan un resultado y una recomendación; mover una etiqueta o un fichero a producción lo haces tú.
- **Depender de Langfuse.** Todo se calcula en local y se publica después. Sin red, pierdes la curva y nada más.
- **Declarar mejoras.** `/validar` da un delta con `n=1`; `/optimizar` solo acepta una variante si control mejora ≥ 0,10 y lo anota con su motivo.

---

# 5. Mapa de ficheros

```
herramientas/validacion/
  patrones.py              las clases de error, con ejemplos positivos y negativos
  comprobar_patrones.py    la puerta: patrones generales, nunca instancias
  calibrar.py              precision y recall contra el etiquetado
  calibracion.md           el resultado, y el techo declarado de la v1
  escala.json              topes y pesos, cada uno con el dato que lo sostiene
  validar.py               la medición
  etiquetado/              verdad de campo etiquetada a mano (cierra A24)

herramientas/optimizacion/
  preparar.py              los cinco requisitos; --subir-conjunto; --publicar-candidato
  comprobar_variante.py    las cinco prohibiciones, antes de instalar
  puntuar.py               el score local, y --publicar a Langfuse
  casos/generar.py         casos mutados y etiquetas, de una sola fuente
  conjuntos/               los conjuntos etiquetados (no legibles desde la sesión)

validaciones/              resultados de /validar; _base.json es la línea base
optimizaciones/            resultados de /optimizar; lecciones.md es la memoria
```
