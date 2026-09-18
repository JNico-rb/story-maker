# Bucle de optimización de prompts

Los guiones del bucle de [specs/functional.md](../../specs/functional.md) §9.5. Quien los llama es la skill [`/optimizar`](../../.claude/skills/optimizar/SKILL.md); aquí solo está el código.

**Fuera del harness.** `/novela` no los llama nunca. No escriben en `novelas/`: leen capítulos como entrada de un caso y nada más.

```
# ¿puede arrancar el bucle?
python herramientas/optimizacion/preparar.py --comprobar \
    --agente revisor-encargo --metrica recall_revisor --conjunto defectos-v1

# espejo del conjunto en Langfuse (la fuente de verdad sigue siendo el .jsonl)
python herramientas/optimizacion/preparar.py --subir-conjunto --conjunto defectos-v1
```

| Guion | Qué hace | Cuándo lo llama la skill |
|---|---|---|
| `preparar.py --comprobar` | Los cinco requisitos del TRIGGER. Sale 1 si falta alguno | §1, antes de gastar una invocación |
| `comprobar_variante.py` | Las cinco prohibiciones del MEMORY. Sale 1 si la variante no puede instalarse | §6, antes de instalar |
| `puntuar.py` | Calcula el score **en local** y lo escribe en `score.json` | §4, tras cada split |
| `puntuar.py --publicar` | Sube la vuelta a Langfuse | §4, con `\|\| true` |
| `preparar.py --publicar-candidato` | Publica `mejor.md` con etiqueta `candidato` | §9, solo al alcanzar la métrica |

## Por qué esto es código y no prosa de la skill

Las prohibiciones de §9.5.5 —no copiar citas del conjunto, no nombrar la métrica, no cambiar el rol— protegen la validez del experimento entero. Una regla escrita solo en la skill la ejecuta un modelo leyendo instrucciones y **puede olvidarse** (evidencia E3); la misma regla en un guion que devuelve 1 no. Es la diferencia entre las marcas `harness` y `guion` de la spec.

Lo que el guion **no** arregla: solo actúa si alguien lo llama. Que la skill lo llame sigue siendo prosa.

## Por qué la puntuación se calcula en local

`puntuar.py` importa el emparejamiento de `herramientas/evaluadores/<metrica>.py` en vez de copiarlo, para que lo que puntúa en Langfuse y lo que puntúa aquí sea literalmente la misma función. Si cambias `_normalizar` allí, cambia aquí sola.

El número sale en local y **después** se publica. Si Langfuse no responde, el bucle sigue y solo se pierde la curva: Langfuse proyecta, no decide (spec §9.3 regla 3).

## Dos límites que conviene conocer

- **El optimizador no puede leer el conjunto** porque `permissions.deny` corta `Read` sobre `herramientas/optimizacion/conjuntos/**`, y con él `cat`, `head` y las redirecciones de Bash. Estos guiones sí lo leen, porque un `python guion.py` no es una lectura reconocible de esa ruta. Es la misma frontera que documenta el CHANGELOG 0.8.1 para las credenciales.
- **`cita_verificable` se calcula sobre los capítulos del conjunto**, que están en `novelas/`. Si esa carpeta se reescribe, el conjunto apunta a un texto distinto y las vueltas dejan de ser comparables. Por eso `ejecucion.json` congela el hash del conjunto y el informe de cierre lo comprueba.
