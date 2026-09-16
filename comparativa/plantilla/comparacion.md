---
caso: ""
fecha: ""
veredicto: ""            # A | B | empate — una palabra; el matiz va abajo
b_aguanta: null          # true si B cumple todas las métricas que cumple A (spec §8.3)
---

# Comparación — <caso>

Rellenado por `/novela comparar`. Ninguna cifra es estimada: todo sale de contar o de leer. Lo no disponible: `desconocido`.

## 1. Medible

### Métricas de calidad (recalculadas ahora)

| Métrica | Umbral | A | B |
|---|---|---|---|
| graves_por_10 | | | |
| agotamiento_pct | | | |
| hilos_sin_cerrar | | | |
| primer_intento_pct | | | |
| rechazos_voz_pct | | | |
| desviacion_longitud | informativa | | |

### Ejecución

| Dato | A | B |
|---|---|---|
| Capítulos completos / previstos | | |
| Palabras totales (contadas) | | |
| Palabras por capítulo (lista) | | |
| Intentos por capítulo (lista) | | |
| Rechazos por longitud | | |
| Reintentos técnicos | | |
| Discrepancias de veredicto | | |
| Problemas de arco por gravedad | | |
| Problemas del informe global por gravedad | | |
| Invocaciones por agente | | |
| Volumen por modelo: pal_entrada / pal_salida | | |
| Tokens y coste por modelo (si hay) | | |

## 2. Lectura

Cada casilla lleva **una cita o referencia concreta** (capítulo y párrafo). Sin ejemplo, la casilla no vale.

### Continuidad
Tres hechos verificables del capítulo 1 de cada lado, comprobados en el último capítulo **y en `libro-estado.md` final**.

| Hecho | A: texto | A: libro de estado | B: texto | B: libro de estado |
|---|---|---|---|---|
| | | | | |

### Cumplimiento del plan
Por capítulo: ¿cumplió `objetivo` y `sucesos` de su entrada en la escaleta de arco? Si el revisor lo aprobó y no lo cumple, es un fallo del revisor: va a la lista de cambios.

| Cap | A | B |
|---|---|---|
| | | |

### Prosa y voz
Juicio honesto, con citas. Si el lado barato se lee igual o mejor, escríbelo tal cual.

## 3. Conclusión

**Veredicto:** …

**¿B aguanta?** (cumple todas las métricas que cumple A): …

**Qué significa para el plan (§7.8):** …

## 4. Cambios propuestos para el harness
Cada uno accionable: qué fichero y qué cambiar. Vacío si no hay nada, y dilo.

-
