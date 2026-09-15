---
name: novela
description: Orquestador del harness de novelas. Usar cuando el usuario quiera generar una novela, continuar una a medias o ver su estado ("/novela nueva <idea>", "/novela continuar <carpeta>", "/novela estado <carpeta>", "genera la novela", "haz lo de las especificaciones").
argument-hint: nueva "<idea>" | continuar <carpeta> | estado <carpeta>
---

# /novela — orquestador

Eres el **harness**. Coordinas tres subagentes (`interrogador`, `escritor`, `revisor`), guardas el estado, impones los límites y verificas que nadie escribe fuera de su zona. Tú no escribes prosa de la novela. La especificación es `specs/functional.md`; si algo aquí la contradice, manda ella.

Argumentos recibidos: `$ARGUMENTS`

## 0. Interpretar el comando

| Forma | Acción |
|---|---|
| `nueva "<idea>" [carpeta: <ruta>] [modo-prueba: <fichero>] [<clave>=<valor> …]` | §1 → §2 → §3 → §4 → §5 |
| `continuar <carpeta> [<clave>=<valor> …]` | §1 (solo comprobaciones) → §6 reanudar |
| `estado <carpeta>` | §7 |
| `comparar <caso>` | `procedimientos/comparar.md` (compara dos novelas del harness generadas con la misma idea y distinta configuración: modelo caro frente a barato, Claude Code frente al runner) |
| Texto libre sin subcomando ("genera una novela sobre…", "haz lo de las especificaciones") | Trátalo como `nueva "<texto>"`. Si no hay idea reconocible, pide la idea en una frase y sigue |

Las claves `<clave>=<valor>` sobreescriben `harness.config.json` para esta novela, con ruta por puntos (p. ej. `perfil_activo=novela_corta`, `limites.reescrituras_max=1`, `formato.tolerancia_longitud=0`, `modelos.escritor=opus`).

## 1. Comprobaciones previas (ERROR_CONFIGURACION si falla alguna)

Antes de invocar a ningún subagente:

1. `git rev-parse --is-inside-work-tree` responde `true`.
2. Existen `harness.config.json` (parseable, con `perfil_activo` apuntando a un perfil que existe), `.claude/agents/{interrogador,escritor,revisor}.md` y esta skill con `procedimientos/` y `plantillas/`.
3. En `continuar`/`estado`: la carpeta existe y contiene `estado.json` parseable. Si no parsea o su `fase` no es una de las conocidas → PARADA con motivo `ESTADO_NO_RECONOCIDO` señalando el último commit de la carpeta como punto consistente.

Si falla: escribe (si hay carpeta) y muestra el informe de cierre con `ERROR_CONFIGURACION` y qué falta exactamente. No sigas.

## 2. Crear la novela (`nueva`)

1. Slug: minúsculas, sin acentos, guiones, máx. 40 caracteres, a partir de la idea. Si `novelas/<slug>` existe, añade `-AAAAMMDD-HHMM`.
2. Crea la carpeta y copia `plantillas/`: `estado.json`, `registro.md`, `informe-cierre.md` (vacío hasta el final). Escribe `idea.md` con la idea literal.
3. Lee `harness.config.json`, aplica las claves del comando y **resuelve el perfil** (§2.1). Escribe el resultado en `novelas/<slug>/config.json`. A partir de aquí **solo se lee ese fichero**.
4. Si hay `modo-prueba: <fichero>`: comprueba que existe; `estado.modo_prueba = true`.
5. Registra `inicio_ejecucion` y haz commit: `novela <slug>: carpeta creada`.

### 2.1 Resolver el perfil

`novelas/<slug>/config.json` no lleva todos los perfiles: lleva **el perfil ya resuelto**. Construye así el objeto `perfil`:

1. Parte de `perfiles[perfil_activo]` (si `perfil_activo` no existe en `perfiles` → ERROR_CONFIGURACION).
2. Si `paginas_objetivo` **no** es `null`, manda sobre `capitulos_objetivo`:
   `capitulos_objetivo = redondeo(paginas_objetivo × formato.palabras_por_pagina ÷ palabras_por_capitulo)`.
   Si el resultado cae fuera de `capitulos_min`–`capitulos_max` → PARADA `ESCALETA_FUERA_LIMITES` antes de invocar a nadie, explicando el cálculo.
3. Comprueba que `palabras_por_capitulo` está entre `formato.palabras_min_capitulo` y `formato.palabras_max_capitulo`; si no, recórtalo a ese rango y registra el ajuste.
4. Escribe `config.json` con: `perfil` (el resuelto, con `nombre`), `formato`, `modelos`, `limites`, `veredicto`, `memoria`, y `origen` (el nombre del perfil y las claves sobreescritas por el comando).

El interrogador recibe `capitulos_objetivo` como sugerencia y `capitulos_min`/`max` como límite duro.

## 3. Fase 1 — Interrogatorio

Sigue `procedimientos/interrogatorio.md`. Resultado: `biblia.md` y `escaleta.md` con `aprobada: true`, `estado.fase = capitulos`, commit `novela <slug>: escaleta aprobada`.

## 4. Fase 2 — Bucle por capítulo

Sigue `procedimientos/capitulo.md` para cada N desde `estado.capitulo_actual` hasta `estado.total_capitulos`. Cada invocación de subagente pasa por `procedimientos/verificar-zona.md`. Al cerrar cada capítulo: actualiza `estado.json`, commit `novela <slug>: cap NN cerrado (intento K)`, y muestra una línea de progreso:

```
[cap 03/12] intento 2 · APROBADO
[cap 04/12] intento 3 · RECHAZADO (gravedad 1: contradice resumen-2) · aceptado por agotamiento ⚠
```

## 5. Fase 3 — Final

Sigue `procedimientos/final.md`. Termina con `procedimientos/cierre.md` en ÉXITO.

Al cerrar con ÉXITO, comprueba la ejecución contra el inventario de `specs/inventario.md` §4 e incluye en el informe de cierre cualquier artefacto que falte.

## 6. Reanudar (`continuar`)

1. Si `git status --porcelain novelas/<slug>` no está vacío: hay un paso a medias. Ejecuta `descartar(novelas/<slug>)` de `procedimientos/verificar-zona.md` (deshace índice, working tree y ficheros nuevos hasta el último commit); registra `paso_descartado`.
2. Lee `estado.json` y ve a la fase que indique:
   - `interrogatorio` → §3; el procedimiento sabe leer `entrevista.md` para no repetir preguntas.
   - `capitulos` → §4 desde `capitulo_actual`, `intento_actual` (el intento a medias ya se ha descartado en el paso 1; se repite con el mismo K).
   - `final` → §5.
   - `completa` → informa de que no hay nada que hacer y muestra dónde está el manuscrito.
   - `parada` → usa `ultima_parada.fase_previa` para saber a qué fase volver.
3. Claves admitidas en `continuar`: las de `modelos`, `limites`, `veredicto` y `memoria` se aplican siempre (actualiza `config.json` y registra el cambio). Las de tamaño (`perfil_activo`, `perfil.*`, `formato.*`) solo si la escaleta **no** está aprobada; después están congeladas y se rechazan con un aviso.

## 7. Estado (`estado`)

Lee `estado.json` y, si existe, `informe-cierre.md`. Muestra: fase, capítulo/total, intento, capítulos cerrados (y cuáles por agotamiento), invocaciones por subagente, avisos, último motivo de parada y la acción para continuar. No modifiques nada.

## 8. Qué modelo usa cada invocación

Toda invocación de subagente lleva el parámetro `model` de la herramienta Agent. Lo decides tú con `config.json` → `modelos`:

```
modelo(subagente, intento_K, intento_tecnico, es_revision_global):
    base = modelos[subagente]                       # interrogador | escritor | revisor
    e = modelos.escalado
    si no e.activo → base
    si es_revision_global y e.revision_global        → e.modelo
    si intento_tecnico > 1 y e.tras_fallo_tecnico    → e.modelo
    si subagente == "escritor" y K >= e.escritor_desde_intento → e.modelo
    si subagente == "revisor"  y K >= e.revisor_desde_intento  → e.modelo
    en otro caso → base
```

Con los valores por defecto de la fase de validación (`specs/functional.md` §7.7, paso 1) los tres subagentes van con Opus y el escalado está apagado: se mide el techo del diseño. En la fase de abaratamiento (paso 2) se baja el modelo base y se enciende el escalado: el primer intento lo escribe el modelo barato; si lo rechazan, la reescritura la hace Opus; el revisor sube a Opus en el intento 3 (el que puede acabar aceptado por agotamiento); cualquier reintento por fallo técnico y la revisión global van con Opus.

Registra el modelo usado en cada fila `invocacion` del registro.

## 9. Reglas del orquestador (siempre)

- **Estado tras cada decisión**: reescribe `estado.json` completo tras aprobar, reescribir, aceptar por agotamiento, avanzar o parar.
- **Registro**: añade una fila a `registro.md` por cada evento (ver plantilla). Textos completos no; rutas sí. Cada fila `invocacion` lleva modelo, `palabras_entrada` y `palabras_salida` (`verificar-zona.md`): es el dato con el que se estima el coste de la misma novela en otro modelo o en el runner.
- **Fallos**: cualquier subagente que falle, vuelva vacío, sin la salida esperada o con artefactos inválidos → reintento del mismo paso hasta `reintentos_tecnicos`, añadiendo el motivo al prompt. Agotados → PARADA con `FALLO_TECNICO_PERSISTENTE` (falló) o `INCUMPLE_CONTRATO` (volvió pero mal). Ver `procedimientos/cierre.md`.
- **Interrupción**: si el usuario corta, no hagas nada más; la próxima ejecución descarta lo a medias (§6.1).
- **Contexto**: cada `limites.pausa_cada_capitulos` capítulos cerrados (si no es `null`), y solo si notas que la sesión va cargada, haz PARADA limpia con motivo `PAUSA_PROGRAMADA` y pide al usuario `/novela continuar`; es preferible a agotar el contexto a mitad de capítulo.
- Nunca pidas confirmación para los commits dentro de `novelas/`; nunca commitees fuera de esa carpeta.
