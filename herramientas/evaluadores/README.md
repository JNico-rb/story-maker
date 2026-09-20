# Evaluadores de Langfuse

Los siete evaluadores de [specs/technical.md](../../specs/technical.md) §9.3.1, tal como están creados en el proyecto de Langfuse.

**Fuera del harness.** `/novela` no los llama nunca (spec §9.3 regla 2). Corren después, sobre observaciones ya exportadas. Miden a los revisores, no a la novela.

```
python herramientas/evaluadores/crear.py --dry-run   # imprime qué crearía
python herramientas/evaluadores/crear.py             # crea evaluadores y reglas
```

## Qué hay creado

| Score | Tipo | Regla | Corre sobre |
|---|---|---|---|
| `lengua_erratas` | juez | escritor / capítulo — jueces de texto | `output` del escritor |
| `verosimilitud_dominio` | juez | ídem | ídem |
| `coherencia_interna` | juez | ídem | `output` + `input` (contexto previo) |
| `mundo_presente` | juez | ídem | `output` + `input` (sección «El mundo») |
| `cita_verificable` | código | revisores — cita verificable | `output` (informe) + `input` (capítulo) |
| `redundancia_resumen` | código | resumidor — redundancia entre capítulos | `output` (resumen N) + `input` (resumen N−1) |
| `recall_revisor` | código | — (experimento) | `expectedOutput` del dataset + informe |

**Las tres reglas están desactivadas.** Activarlas hoy puntuaría el vacío: el exportador manda `input`/`output` a `null` (revisión §5.2). Se activan cuando el exportador esté arreglado.

## Contrato con el exportador

Los filtros de las reglas no pueden usar el nombre de la observación —el API no lo permite— y usan `metadata`, que `exportar.py` ya escribe:

- `metadata.agente` ∈ {`escritor`, `resumidor`, `revisor-encargo`, `revisor-continuidad`, `interrogador`}
- `metadata.modo` — se filtra con `starts with capitulo`, porque en reescritura vale `capitulo (reescritura)`
- `metadata.resultado = ok` — descarta las filas `pendiente` y las de corrección, que son la inflación del 22 %

Lo que falta en `exportar.py` para que esto funcione:

1. **`resultado`** se calcula con `"resultado ok"` sin dos puntos, y el registro escribe `resultado: ok`. Hoy todas las observaciones traen `resultado: "desconocido"` y el filtro no casa con ninguna. Es el ítem 2 de la revisión §5.2.
2. **`input` / `output`** están a `null` en las 50 generaciones. Sin ellos no hay nada que puntuar. Lo que cada evaluador espera está documentado en la cabecera de su `.py`.

## Modelo de los jueces

`openrouter / openrouter/free`, que es la única conexión LLM del proyecto. **Esto incumple la regla de §5.4**: el juez nunca debe ser el modelo que escribió, y `openrouter/free` no garantiza cuál toca. Antes de calibrar, añadir una conexión a `opus` o `sonnet` y cambiar `MODELO_JUEZ` en `crear.py`.
