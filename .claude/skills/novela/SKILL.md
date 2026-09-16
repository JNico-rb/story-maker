---
name: novela
description: Orquestador del harness story-maker. Usar cuando el usuario quiera generar una novela ("/novela nueva <idea>", "genera una novela sobre…", "haz lo de las especificaciones"), continuar una a medias, ver su estado, verificar una carpeta generada o comparar dos ejecuciones.
argument-hint: nueva "<idea>" | continuar <carpeta> | estado <carpeta> | verificar <carpeta> | comparar <caso>
---

# /novela — orquestador

Eres el **harness** (`specs/functional.md` §6). Coordinas cuatro agentes —`interrogador`, `escritor`, `resumidor`, `revisor`—, **escribes todos los ficheros**, guardas el estado, impones los límites y tomas todas las decisiones de flujo. Tú no escribes prosa de la novela ni juzgas capítulos. La spec manda sobre este fichero; el vocabulario es su §0.

Este fichero es **pseudocódigo**. Cada función lleva el nombre de la spec §9.1 y su detalle está en un procedimiento de `procedimientos/`. El runner del hito 2 implementa estas mismas funciones con estos mismos nombres.

Argumentos recibidos: `$ARGUMENTS`

## 0. Comandos

| Forma | Hace |
|---|---|
| `nueva "<idea>" [entrevista: <ruta>] [modo-prueba: <carpeta>] [<clave>=<valor> …]` | `comprobar_entorno` → `crear_novela` → `ejecutar` |
| `continuar <carpeta> [<clave>=<valor> …]` | `comprobar_entorno` → `reanudar` → `ejecutar` |
| `estado <carpeta>` | §7, solo lectura |
| `verificar <carpeta>` | §8, solo lectura: inventario + métricas |
| `comparar <caso>` | `procedimientos/comparar.md` |
| Texto libre ("genera una novela sobre…", "haz lo de las especificaciones") | Trátalo como `nueva "<texto>"`. Sin idea reconocible, pide la idea en una frase y sigue |

- `entrevista: <ruta>`: toma esa entrevista ya cerrada en vez de entrevistar al usuario. El usuario sigue confirmando la escaleta.
- `modo-prueba: <carpeta>`: toma `idea.md` y `entrevista.md` de esa carpeta y **aprueba la escaleta solo** si pasa la validación. Solo para verificar el harness (spec §8.1). Con este flag la idea entre comillas es opcional.
- `<clave>=<valor>` sobreescribe `config.json` para esta novela, con ruta por puntos: `perfil_activo=novela_corta`, `limites.pausa_cada_capitulos=null`, `formato.tolerancia_longitud=0`, `modelos.escritor=sonnet`.

## 1. comprobar_entorno(config) → ok | ERROR_CONFIGURACION

Antes de invocar a ningún agente:

1. `git rev-parse --is-inside-work-tree` responde `true`.
2. `config.json` de la raíz parsea, tiene `version: 3` y `perfil_activo` apunta a una entrada de `perfiles`.
3. Existen `.claude/agents/{interrogador,escritor,resumidor,revisor}.md`, y en cada uno el frontmatter coincide con la config de la raíz: `maxTurns` igual a `limites.turnos_por_invocacion`, y `model` igual a `modelos.<agente>`. Si algo no coincide, es ERROR_CONFIGURACION indicando fichero, campo, valor declarado y valor esperado: lo que anuncia la config no es lo que se aplicaría. La comparación es contra la config **de la raíz**, antes de las sobreescrituras; una sobreescritura `modelos.<agente>=<valor>` es un acto deliberado de esta ejecución y no dispara el error.
4. Existen `procedimientos/` y `plantillas/` de esta skill.
5. En `continuar`, `estado` y `verificar`: la carpeta existe y `estado.json` parsea con `version: 3` y una `etapa` conocida. Si no → PARADA `ESTADO_NO_RECONOCIDO` señalando el último commit de la carpeta como punto consistente.

Si algo falla: muestra (y si hay carpeta, escribe) el informe de cierre con `ERROR_CONFIGURACION` y qué falta exactamente (`procedimientos/cierre.md`). No sigas.

## 2. crear_novela(idea, flags, sobreescrituras) → carpeta

1. Slug: minúsculas, sin acentos, palabras unidas por guiones, máximo 40 caracteres, a partir de la idea. Si `novelas/<slug>` existe, añade `-AAAAMMDD-HHMM`.
2. Crea `novelas/<slug>/`, `capitulos/` y `arcos/`. Copia de `plantillas/`: `estado.json` (con `slug`), `registro.md`, `libro-estado.md` (vacío de contenido, solo la estructura). Escribe `idea.md` con la idea literal (en modo de prueba, copiada de la carpeta indicada).
3. `config = resolver_perfil(config_raiz, sobreescrituras)`; escríbelo en `novelas/<slug>/config.json`. **A partir de aquí solo se lee ese fichero.**
4. Flags: `entrevista:` → comprueba que la ruta existe. `modo-prueba:` → comprueba que la carpeta tiene `idea.md` y `entrevista.md`; `estado.modo_prueba = true`, `estado.carpeta_prueba = <carpeta>`.
5. Registra `inicio_ejecucion` (comando, perfil, sobreescrituras, flags). Commit `novela <slug>: carpeta creada`.

### 2.1 resolver_perfil(config_raiz, sobreescrituras) → config

1. Aplica las sobreescrituras sobre una copia de la config raíz (`perfil_activo` primero, después el resto).
2. `perfil = perfiles[perfil_activo]` (si no existe → ERROR_CONFIGURACION). Añade `perfil.nombre`.
3. Si `perfil.paginas_objetivo` no es `null`: `capitulos_objetivo = redondeo(paginas_objetivo × formato.palabras_por_pagina ÷ palabras_por_capitulo)`. Fuera de `capitulos_min`–`capitulos_max` → PARADA `ESCALETA_FUERA_LIMITES` antes de invocar a nadie, explicando el cálculo.
4. Recorta `perfil.palabras_por_capitulo` a `formato.palabras_min_capitulo`–`palabras_max_capitulo` si se sale, y regístralo.
5. El fichero congelado lleva: `version`, `proveedor`, `perfil` (resuelto), `formato`, `modelos`, `limites`, `veredicto`, `memoria`, `calidad`, y `origen` = { `perfil_activo`, `sobreescrituras` }. No lleva `perfiles`.

## 3. ejecutar(carpeta)

```
config = leer(carpeta/config.json); e = leer(carpeta/estado.json)

si e.etapa == interrogatorio:                                  # procedimientos/interrogatorio.md
    entrevistar(carpeta)
    proponer_escaleta(carpeta)                                  # termina con e.etapa = capitulos

si e.etapa == capitulos:
    para N desde e.capitulo_actual hasta e.total_capitulos:
        A = arco_de(N)                                          # el arco cuyo rango contiene N
        si no e.arcos[A].escaleta_validada:
            detallar_arco(carpeta, A)                           # procedimientos/arco.md
        K = e.intento_actual
        bucle:                                                  # procedimientos/capitulo.md
            escribir_capitulo(carpeta, N, K)
            informe = comprobar_longitud(carpeta, N, K)
            si informe == ok:
                resumir(carpeta, N, K)
                informe = revisar(carpeta, N, K)
            decision = decidir(carpeta, N, K, informe)          # aprobar | reescribir | agotar
            si decision == reescribir:
                K += 1; e.intento_actual = K; guardar(e); continuar
            K_final = K si aprobar, si no mejor_intento(carpeta, N)
            cerrar_capitulo(carpeta, N, K_final, por_agotamiento = (decision == agotar))
            salir del bucle
        si N == e.arcos[A].hasta:
            revisar_arco(carpeta, A)                            # procedimientos/arco.md
        si pausa_programada(N): cerrar(carpeta, PARADA, PAUSA_PROGRAMADA); return
    e.etapa = final; guardar(e)

si e.etapa == final:                                            # procedimientos/final.md
    ensamblar(carpeta)
    revisar_global(carpeta)
    metricas = calcular_metricas(carpeta)
    e.etapa = completa; guardar(e); commit "novela <slug>: novela completa"
    cerrar(carpeta, EXITO, metricas)                            # procedimientos/cierre.md

si e.etapa == completa:
    muestra dónde están manuscrito.md, informe-global.md e informe-cierre.md; no hagas nada más
```

`pausa_programada(N)` es cierto si `limites.pausa_cada_capitulos` no es `null`, `N % pausa_cada_capitulos == 0` y `N < total_capitulos`. Con un solo arco, `revisar_arco` y `revisar_global` son la misma pasada: se hace solo la global.

Toda invocación de agente pasa por `invocar(...)` de `procedimientos/invocar.md`, que reintenta, valida la forma de la salida, la escribe y registra el volumen. Toda parada pasa por `cerrar(...)` de `procedimientos/cierre.md`.

## 4. Progreso

Una línea por evento, en la sesión, en el momento en que ocurre:

```
[arco 1/1] escaleta del arco validada (5 capítulos)
[cap 02/05] intento 1 · escrito (1.612 palabras)
[cap 02/05] intento 1 · RECHAZADO por longitud (2.104 palabras, objetivo 1.500 ±20 %)
[cap 02/05] intento 2 · RECHAZADO (gravedad 1: contradice libro de estado › Marta)
[cap 02/05] intento 3 · APROBADO
[cap 04/05] intento 3 · RECHAZADO · aceptado por agotamiento (mejor intento: 2) ⚠
[arco 1/1] informe de arco: 0 problemas graves
[final] revisión global: 1 problema de gravedad 1 · métricas: 5/6 CUMPLE
```

## 5. reanudar(carpeta)

1. Si `git status --porcelain novelas/<slug>` no está vacío, hay un paso a medias: `descartar(carpeta)` (`procedimientos/invocar.md`) y registra `paso_descartado`.
2. Aplica las `<clave>=<valor>` del comando: las de `proveedor`, `modelos`, `limites`, `veredicto`, `memoria` y `calidad` siempre (actualiza `config.json` y registra el cambio). Las de tamaño (`perfil_activo`, `perfil.*`, `formato.*`) solo si la escaleta **no** está aprobada; después están congeladas y se rechazan con un aviso.
3. Registra `inicio_ejecucion` (comando: continuar) y pasa a `ejecutar(carpeta)`. `ejecutar` retoma por `e.etapa`, `e.capitulo_actual` y `e.intento_actual`; un arco sin `escaleta_validada` se detalla de nuevo; si `e.etapa == parada`, usa `e.ultima_parada.etapa_previa` como etapa.

## 6. Qué modelo usa cada invocación

`elegir_modelo(agente, K, intento_tecnico, modo)` en `procedimientos/invocar.md`, con `config.modelos`. Con la configuración por defecto (validación) los cuatro van con el modelo caro y el escalado está apagado.

## 7. estado <carpeta>

Lee `estado.json` y, si existe, `informe-cierre.md`. Muestra: etapa, arco actual y total, capítulo actual y total, intento, capítulos cerrados (y cuáles por agotamiento), invocaciones por agente, avisos, último motivo de parada y la acción para continuar. No modificas nada.

## 8. verificar <carpeta>

Solo lectura. Ejecuta los seis pasos de `specs/inventario.md` §4 y, si la novela está completa, `calcular_metricas(carpeta)` (`procedimientos/final.md`). Muestra una tabla: cada comprobación con OK / FALLA y el detalle, y cada métrica con su valor, su umbral y CUMPLE / NO CUMPLE. Sirve sobre cualquier carpeta con la estructura de la spec, la haya generado Claude Code o el runner.

## 9. Reglas del orquestador (siempre)

- **Solo tú escribes.** Cada salida de agente la validas y la escribes tú en su ruta. Los ficheros inmutables (`biblia.md`, `escaleta.md`, `arcos/arco-*.md`, `intento-*.md`, `libro-estado.md`, `manuscrito.md`) se crean con una escritura completa; nunca `Edit` sobre ellos.
- **Estado tras cada decisión**: reescribe `estado.json` completo tras aprobar, reescribir, aceptar por agotamiento, avanzar, validar un arco o parar. Nunca al final.
- **Registro**: una fila en `registro.md` por cada evento (plantilla). Textos completos no; rutas sí.
- **Commits** solo dentro de `novelas/<slug>`, en estos puntos: carpeta creada · escaleta aprobada · arco AA detallado · cap NN cerrado (intento K) · arco AA revisado · novela completa · PARADA <motivo>. Siempre `git add -A novelas/<slug>` seguido de `git commit -m "novela <slug>: <punto>"`. Nunca fuera de esa carpeta, nunca `push`.
- **Lo mecánico lo haces tú con herramientas, no con criterio**: palabras con `wc -w`, veredicto con la regla de `config.veredicto`, mejor intento con la regla de §4.2, forma de las salidas con los delimitadores exactos.
- **Nunca terminas sin informe de cierre.** Éxito o parada, siempre `cerrar(...)`.
