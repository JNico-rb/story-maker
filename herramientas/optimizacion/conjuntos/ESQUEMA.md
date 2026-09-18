# Conjuntos etiquetados — esquema

La **verdad de campo** del bucle de `specs/functional.md` §9.5. Un fichero `<nombre>.jsonl` por conjunto, **versionado en git**: si la verdad de campo solo viviera en Langfuse no sería reproducible, y el hito 2 no podría usarla (A24).

Langfuse guarda un **espejo**, que se sube con `preparar.py --subir-conjunto`. La fuente de verdad es el fichero.

## Una línea por caso

Un **caso** es una invocación del agente sobre un capítulo. Un **defecto** es una etiqueta dentro de un caso. El recall se calcula sobre defectos; el `split` se fija por caso.

```json
{"id": "b-cap-03",
 "split": "busqueda",
 "entradas": {"capitulo": "novelas/<slug>/capitulos/capitulo-03.md",
              "escaleta": "novelas/<slug>/escaleta.md",
              "arco": "novelas/<slug>/arcos/arco-01.md",
              "biblia": "novelas/<slug>/biblia.md"},
 "defectos": [
   {"clase": "A7", "gravedad": 2, "cita": "La 4ª planta",
    "por_que": "el título no tiene referente en el texto del capítulo"},
   {"clase": "E", "gravedad": null, "cita": "la agua subía",
    "por_que": "agramaticalidad; ningún contrato la cubre hoy"}
 ]}
```

| Campo | Qué es |
|---|---|
| `id` | Único en el fichero. Es el nombre del `.json` con el informe de cada vuelta |
| `split` | `busqueda` o `control`. **Se escribe a mano y no se re-sortea nunca**: un split que se recalcula entre vueltas hace incomparables las vueltas |
| `entradas` | Rutas relativas a la raíz, exactamente las que pide el contrato del agente (spec §5). Ni una más |
| `defectos[].clase` | La clase de E5 (`A`, `B`, `C`, `D`, `E`, `E′`, `A7`) u otra tuya. Solo informativa: sirve para el diagnóstico agregado |
| `defectos[].gravedad` | La gravedad de §5.6 cuyo contrato es dueño del defecto, o **`null` si ningún agente puede verlo hoy**. Es lo que decide si cuenta |
| `defectos[].cita` | Literal del capítulo, ≥ 8 caracteres. Es la clave del emparejamiento: el informe acierta si la cita aparece, normalizada, en alguno de sus campos |
| `defectos[].por_que` | Para ti y para quien revise el etiquetado. El bucle no lo usa |

## La gravedad es lo que decide, no la clase

`revisor-encargo` emite 2 y 4; `revisor-continuidad`, 1 y 5. Un defecto con `gravedad: null` **no cuenta ni a favor ni en contra** de nadie: no es un fallo del agente, es una pregunta que nadie le hizo. De los 30 defectos de E5, 21 están así.

Etiquetar un defecto con una gravedad que su agente no emite es el error caro: hunde el denominador y hace parecer malo a un agente al que se le está preguntando por lo que no es suyo.

## Antes de usarlo

```
python herramientas/optimizacion/preparar.py --comprobar \
    --agente revisor-encargo --metrica recall_revisor --conjunto <nombre>
```

Valida la forma, cuenta los defectos puntuables para ese agente y dice si el bucle arranca.
