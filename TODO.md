# TODO

Lo pendiente. Lo ya decidido vive en [CHANGELOG.md](CHANGELOG.md); lo vigente, en [specs/functional.md](specs/functional.md) y [specs/technical.md](specs/technical.md).

# Auditoría y plan de estabilización de story-maker

**Fecha:** 2026-09-19 · **Modo:** solo lectura. No he editado, escrito, copiado, añadido al
índice ni commiteado nada, ni he ejecutado `/novela`, `/optimizar` ni `/validar`.
**Escrito para:** el dueño del repositorio, que decide qué se commitea y qué se borra.

## Contexto

El repositorio tenía 51 entradas sin commitear, cuatro specs borradas, dos carpetas retiradas
y una novela a medias. El requisito 3 del TRIGGER (`technical.md` §9.5.1) exige árbol limpio,
así que ese estado bloquea el bucle de optimización. El encargo pedía el estado real, los
hallazgos clasificados y un plan ordenado por dependencias.

Regla aplicada en todo el documento: **la especificación manda**. Cuando el repositorio la
contradice, el hallazgo es «el repositorio está mal», salvo donde la spec hace una afirmación
de estado fechada; ahí lo que caduca es la afirmación, no la regla.

> ## Actualización del 2026-09-20 — deja obsoleto el aviso de abajo
>
> 1. **La sesión concurrente murió** el 2026-09-19 a las 19:31, a mitad del capítulo 1
>    (dejó `capitulos/01/intento-2.md` sin trackear). Nada se movió en 17 horas. **R0 cerrado,
>    P1 contestada**: el bloque de git de este plan vuelve a ser aplicable.
> 2. **El usuario ha borrado del disco dos novelas a medias**: `ha-habido-un-apagon-masivo-y-ya-estaba`
>    y `una-persona-que-desde-los-10-anos-se-des`. **Cierra R2 e I16, y contesta P2 por la
>    opción (c)**; el paso 9 decae salvo su segunda mitad (el agujero de `validar_canon`, que
>    sigue en el harness y entra con el paso 11). Los borrados están **en disco, no commiteados**:
>    los 9 ficheros de la primera viven en `f22ff8e` y se recuperan con `git checkout --` hasta
>    que el paso 8 los commitee. **E4 sigue vivo**: es un defecto de diseño del harness, no de
>    esa novela.
> 3. Con `una-persona-…` fuera, **B7 pierde su motivo**: su `encargos/` ya no respalda ninguna
>    novela viva. Ver la nota en la lista de borrados.
> 4. **Resueltos ya** (2026-09-20): el **paso 10** (R4) y el **paso 12 entero** (R6, R11, I9,
>    I10, I11, I12), más S2 (`git rm --cached` de los 5 `.pyc`). R11 trae fixture: `hook.sh`
>    gana una tercera sección, «permisos vs procedimientos», que compara los 6 comandos git
>    que `invocar.md` prescribe contra la lista `allow` — 27 casos, y con el permiso viejo
>    falla. `comprobar_punteros.sh` deja de gritar en falso sobre citas en bloque y ejemplos
>    en código en línea, y vuelve a **EXIT=0**. Nada de esto está commiteado: va en el paso 8.
> 5. **Paso 2 cerrado** (2026-09-20): **R3** resuelto sin tocar los 30 sitios. El `python` de la
>    máquina funciona y la documentación vuelve a ser cierta tal como está escrita. De propina,
>    `preparar.py --comprobar` ya se puede ejecutar: sale 0, cierra una fila de «No verificado»
>    y **confirma R8 e I6 en vivo**, que hasta ahora eran lectura de código. Eso es evidencia
>    directa para los pasos 5 y 6.
> 6. **Paso 3 cerrado** (2026-09-20): **I5** resuelto. `comprobar_punteros.sh` gana las
>    comprobaciones 4 y 5 y **pasa a salir 1 a propósito**, acusando R1 (26 tokens `A-n` sin
>    destino, 82 apariciones) e I4 (`comparativa/`). Vuelve a 0 con los pasos 4 y 6, no antes.
>    **El paso 4 tiene que respetar el contrato de formato** que el paso 3 deja escrito, o
>    escribirá el backlog entero y la comprobación seguirá en rojo.

> ## ⚠️ Léelo antes que nada: el repositorio se ha movido durante la auditoría
>
> A las **19:25:16** ha aparecido el commit `f22ff8e` *«novela ha-habido-un-apagon-masivo-y-ya-estaba:
> escaleta aprobada»*. No lo he hecho yo. **Hay otra sesión ejecutando `/novela` sobre este
> repositorio ahora mismo**, y ha avanzado la novela de etapa 1 a etapa 2 mientras yo auditaba.
>
> Consecuencias inmediatas:
> 1. **Todo el bloque de git de este plan es inaplicable mientras esa sesión corra.** Un
>    `git add`/`commit` desde aquí chocaría con `commitear()`, que exige que
>    `git status --porcelain novelas/<slug>` quede vacío (`functional.md:192`), y podría
>    disparar `COMMIT_NO_LIMPIO` o, peor, un `descartar()` que se lleve trabajo bueno.
> 2. **El diagnóstico de la novela que tenía escrito ha quedado obsoleto en 20 minutos**, y lo
>    he rehecho contra el disco (§A.6). El veredicto es el contrario del que iba a darte.
> 3. Ha congelado un defecto: ver **R2**, que es el hallazgo más urgente del informe.
>
> **Primera acción, antes de cualquier paso del plan: averiguar qué sesión es y pararla o
> dejarla terminar.** Todo lo demás espera.

---

## Fase A — Inventario del estado real

### A.1 Las dos líneas rojas: **pasan**

```
$ bash herramientas/pruebas/hook.sh
== inmutables.sh ==        9 casos ok
== rutas-protegidas.sh ==  12 casos ok
OK: 21 casos, ninguno falla                                   EXIT=0
```

Verificado además **tres veces en vivo y sin buscarlo**: el hook me bloqueó comandos por
*nombrar* las rutas protegidas — un `grep` que las excluía con `--exclude-dir`, un `git show`
que citaba un fichero de credenciales, y dos intentos de un subagente. Falla en cerrado, como
exige `functional.md:195`. Es el subsistema más sano del repositorio y no lo toca este plan
salvo para añadirle fixtures.

`bash herramientas/comprobar_punteros.sh` → **EXIT=0**. Ese 0 es engañoso: ver **I5**.

### A.2 El intérprete de Python — el bloqueo operativo

| Comando | Resultado |
|---|---|
| `python --version` | **EXIT=49** · «no se encontró Python» (alias de Microsoft Store) |
| `python herramientas/validacion/comprobar_patrones.py` (el que manda `validar/SKILL.md:29`) | **EXIT=49** |
| `~/.local/bin/python3.14.exe -B` sobre el mismo guion | **EXIT=0** · `Detector v1 (hash 59ca75b) apto: 7 clases, 14 positivos, 26 negativos.` |

Hay intérprete: **Python 3.14.7**, gestionado por `uv`, en `~/.local/bin/python3.14.exe`. No
está en el PATH de Bash; el que sí está es el alias de la Store, que falla. Los `__pycache__`
son **cpython-312**: el intérprete con el que se ejecutó esto por última vez ya no existe en
la máquina (`uv python list` da 3.12 como «download available»).

Los 13 guiones **parsean y arrancan bajo 3.14.7**: los 7 que tienen `main` devuelven `--help`
con código 0. Dependencias externas: **ninguna**, salvo `langfuse==4.15.3` para
`herramientas/trazas/exportar.py`, que no está instalado pero tiene el import diferido
(`exportar.py:219`), así que `--dry-run` sigue arrancando.

**El código no es decorativo. Lo decorativo es la cadena `python ` escrita en 30 sitios.**

### A.3 El árbol de git

`main`, **2 commits por delante de `origin/main`**, sin stashes. **46 entradas** (eran 51 al
empezar; la diferencia son los 5 ficheros de la novela que la otra sesión commiteó). Tres
capas que no se pueden confundir:

**Capa 1 — índice (37 ficheros, +1.284/−1.772).** La consolidación documental del 2026-09-19:
nacen `specs/technical.md` y `specs/architecture.md`, muere `functional.md §9`, se retiran
cuatro specs, `comparativa/` y la skill `caveman`. Trabajo **terminado y coherente**.

**Capa 2 — encima del índice (20 ficheros, +125/−90).** También **terminado**, pero sin
añadir: el registro del hook `rutas-protegidas.sh` en `settings.json`, el estrechamiento de
`Bash(cat *)` a cuatro rutas, `Read(frontend/.env)` en `deny`, el perfil `relato` a 3·1–5 (que
`functional.md:517` ya declara), y la sección «Antes de cerrar un cambio» de `CLAUDE.md`.
**Única excepción:** `TODO.md` −15 líneas, que no es trabajo: es pérdida (**R1**).

**Capa 3 — sin trackear.** Ya no queda nada de la novela (lo commiteó la otra sesión). Siguen
dos borrados de disco vivos en el índice: `novelas/.gitkeep` y los tres ficheros de
`encargos/una-persona-que-desde-los-10-anos-se-des/`.

### A.4 El backlog `A-n` se ha evaporado

`specs/functional.md:21` es normativa:

> «Lo **sin decidir** vive en [TODO.md](../TODO.md) (preguntas `A-n`); una regla marcada
> `→ A-n` está en discusión y **no debe implementarse** hasta que se decida.»

| Dónde | Qué hay |
|---|---|
| `specs/functional.md` | **52** referencias `A-n` |
| `specs/technical.md` | **30** referencias `A-n` |
| `TODO.md` **en disco** | **3 líneas · cero `A-n`** |
| `TODO.md` en el índice | 18 líneas, 9 ítems (A2×2, A20, A22, A19, A10, A21 …) |
| `TODO.md` en HEAD | 30 líneas, 4 bloques sin numerar |
| Definiciones de A1–A28 | **solo** en `specs/consolidacion-2026-09-18.md`, borrada (26 entradas con opciones y recomendación) |

Se citan A1–A24, A27 y A28. Ninguna tiene hoy destino: **82 punteros normativos a la nada**, y
el comprobador dice OK.

### A.5 El bucle de optimización

`technical.md:103` dice «diseñado y **no ejecutado**». En disco hay una ejecución completa:
`optimizaciones/revisor-encargo-20260918-1600/`, cierre `ESTANCAMIENTO`, 3 de 4 vueltas,
`mejor_control 0.5`.

**El informe cuadra con `vueltas.jsonl` en lo que importa.** Cuatro líneas contrastadas contra
los 8 `score.json`:

| vuelta | búsqueda | control | ¿informe? |
|---|---|---|---|
| 0 | 0,400 (8/20) | 0,500 (6/12) | sí |
| 1 | 0,200 (4/20) | 0,500 (6/12) | sí |
| 2 | 0,150 (3/20) | 0,250 (3/12) | sí |
| 3 | 0,200 (4/20) | 0,083 (1/12) | sí |

El invariante de restauración se cumple: `git hash-object .claude/agents/revisor-encargo.md`
= `57ee40d…` = `produccion.hash` = lo que declara el informe. **No cuadran** las invocaciones
(**I2**) y una frase que sostiene una lección (**I3**).

Y la observación del encargo queda confirmada en los datos: el recall **solo baja** en las tres
vueltas, la hipótesis de la v1 queda refutada por búsqueda, y el informe cierra sospechando del
evaluador. La métrica no discrimina en la dirección en que se la empuja.

### A.6 La novela — diagnóstico rehecho a las 19:26

**No está corrupta y sí se puede continuar.** De hecho se está continuando: `estado.json` dice
`etapa: capitulos`, `capitulo_actual: 1`, `escaleta_aprobada: true`, `escaleta_rechazos: 2`,
`invocaciones: interrogador 3 + revisor_continuidad 3`, que cuadra exactamente con las 6 filas
`invocacion` de `registro.md`. `git status` de la carpeta: **vacío**. Dos commits correctos
(`carpeta creada`, `escaleta aprobada`). `capitulos/` todavía vacío.

Lo que el registro cuenta es un interrogatorio sano: entrevista cerrada, propuesta, **dos
rechazos de canon** por aritmética (tanque de 3 días vs 1,5 días; hora 6 del agua vs 24 h del
generador), corregidos, tercera validación APROBADA, confirmación del usuario y aprobación. El
mecanismo de canon de `functional.md:274` funcionó y es visible en `biblia.md:104-112`.

**Pero se ha congelado un defecto (R2).** `escaleta.md` se contradice a sí misma y está
`aprobada: true`, o sea **inmutable por hook**.

| Fuente | Cuántos arcos |
|---|---|
| `escaleta.md` **frontmatter** (líneas 6, 21, 36) | **3** — `1→1`, `2→2`, `3→3` |
| `escaleta.md` cuerpo, «### Arco 1 … (capítulos 1–3)» | **1** |
| `arcos/arco-01.md:3-5` (`validada: true`) | **1** — `desde: 1, hasta: 3` |
| `estado.json` → `"arcos": {"1": {desde:1, hasta:3}}` | **1** |
| `registro.md:26` | **1** |
| `config.json` `capitulos_por_arco: 15` + `functional.md:272` | **1** (obligatorio con 3 ≤ 15) |

Cinco fuentes dicen 1; el frontmatter dice 3. Importa porque el frontmatter es lo que lee la
máquina: `functional.md:165` exige un `arco-AA.md` **por arco**, y §8.7 punto 2 exige
`escaleta_validada` **en todos los arcos**. Al terminar, `/novela verificar` leerá 3 arcos y
encontrará 1 validado, y fallará. `validar_canon` no lo cazó porque compara biblia contra
escaleta (`interrogatorio.md:65`), no el frontmatter contra su propio cuerpo.

Tres desviaciones menores, todas ya commiteadas:
- `registro.md`: las 6 filas `invocacion` tienen `pal_entrada` y `pal_salida` **vacías**;
  `functional.md:495` las exige con `wc -w` en el hito 1.
- Las horas del registro van de `00:00:00` a `00:31:00`; las mtime reales, de 17:56 a 19:25.
  Rompe el registro como traza temporal, que es de donde §6.6 manda recontar el volumen.
- Entre «carpeta creada» y «escaleta aprobada» **no hay punto de commit** (`SKILL.md:150`), así
  que durante toda la etapa 1 `entrevista.md` está sin versionar. Si la sesión hubiera muerto
  20 minutos antes, `reanudar` → `descartar()` se la habría llevado y la rama de
  `interrogatorio.md:98` («cerrada pero escaleta no aprobada → `proponer_escaleta`») habría
  sido inalcanzable. Es un hueco de diseño del harness, no de esta novela (**E4**).

### A.7 El frontend: **cumple** las dos reglas que le importan

- **No escribe en `novelas/`.** Ocho escrituras en todo `frontend/`, las ocho bajo `encargos/`
  (`server/encargos.mjs:116-127,160-164,192,201` y `server/harness.mjs:227-231`).
  `server/novelas.mjs:8` importa solo `readdir, readFile, stat`, y `server/index.mjs:219-226`
  responde **405** a cualquier método que no sea `GET`/`HEAD` sobre `novelas/`. Confinamiento
  con doble cinturón en `encargos.mjs:51-55` (regex de slug + `resolve` + `startsWith`).
- **No decide flujo.** No recalcula métricas (`novelas.mjs:358`), no elige intento, lee
  `veredicto` literal del frontmatter (`novelas.mjs:284-287`), no hay botón de aprobar ni
  reescribir. Un solo `spawn` (`harness.mjs:215`), sin `bypassPermissions`.

Tres cosas a anotar, ninguna bloqueante: **I8** (validación asimétrica en `harness.mjs`),
**I9** (`frontend/CLAUDE.md:54` desfasado) y el hecho de que `encargos/` no exista confirma que
**el estudio no se ha ejecutado nunca**, coherente con `technical.md:99` («congelar hasta la
prueba de punta a punta → A18»).

### A.8 El terreno del anexo A.2

```
~/.claude/projects/c--Users-jaime-rodriguez-repos-story-maker/<id-sesion>/subagents/
```
**2 de ~20** sesiones del proyecto tienen esa carpeta. Hay **9** `meta.json` y 9 `.jsonl` —
eran 6; los 3 nuevos son los exploradores de esta auditoría, y **los tres corrieron en segundo
plano**, así que la incógnita del `requestShape` en primer plano sigue abierta. Confirma de paso
el punto 3 del encargo: la carpeta **no siempre existe**, y el fail-open no es teórico.

---

## Fase B — Hallazgos por gravedad

**Roto** = no funciona, viola una línea roja o contradice la spec · **Incoherente** = funciona,
pero documentación y código dicen cosas distintas · **Sucio** = trabajo sin cerrar ·
**Enfoque** = decisión de diseño a cambiar.

### Roto

| # | Qué | Evidencia | Por qué importa |
|---|---|---|---|
| ~~**R0**~~ ✅ | Una segunda sesión escribe en el repositorio ahora mismo | commit `f22ff8e` a las 19:25:16, no hecho por mí; mtimes 19:24–19:25 | Invalida cualquier operación de git de este plan y puede disparar `COMMIT_NO_LIMPIO` o un `descartar()` sobre trabajo bueno · **CERRADO 2026-09-20: la sesión murió el 19-09 a las 19:31.** |
| **R1** | El backlog `A1`–`A28` no existe. `functional.md:21` manda que viva en `TODO.md`; `TODO.md` tiene 0. Se cita 82 veces | `TODO.md` (3 líneas) vs 52 + 30 referencias en `specs/`. Definiciones solo en `specs/consolidacion-2026-09-18.md`, borrada | 82 punteros normativos a la nada, y reglas marcadas «no implementar hasta decidir» sin sitio donde decidirlas |
| ~~**R2**~~ ✅ | `escaleta.md` declara 3 arcos en el frontmatter y 1 en el cuerpo; las otras cinco fuentes dicen 1. Está `aprobada: true`, o sea **inmutable por hook**, y **commiteada** | `escaleta.md:6,21,36` vs `escaleta.md` §Arcos, `arcos/arco-01.md:3-5`, `estado.json`, `registro.md:26`, `functional.md:272` | La ejecución **en curso** terminará y fallará §8.7 punto 2. Arreglarlo exige saltarse la inmutabilidad, que es la garantía central del sistema · **CERRADO 2026-09-20: el usuario borró la novela (P2 opción c). El agujero de `validar_canon` que lo permitió sigue abierto → paso 11.** |
| ~~**R3**~~ ✅ | Ningún comando documentado de `/validar` ni `/optimizar` arranca: los 30 sitios escriben `python …` | `python herramientas/validacion/comprobar_patrones.py` → **EXIT=49**; el mismo guion con `python3.14.exe` → **EXIT=0** | Las dos herramientas de medida son inejecutables tal como están escritas. Bloquea el anexo entero · **RESUELTO 2026-09-20: el diagnóstico de P3(a) era falso — `~/.local/bin` ya iba la primera del PATH; lo que faltaba eran los shims `python.exe`/`python3.exe`, que solo tenía `python3.14.exe`. `uv python install 3.14 --default` los crea. Los 30 sitios funcionan sin tocarse.** |
| ~~**R4**~~ ✅ | En revisión global con manuscrito que cabe, el harness pasa **5 entradas** al revisor de continuidad; §5.5 dice «el manuscrito» | `procedimientos/final.md:21` vs `functional.md:403`; viola `invocar.md:48` («ni una más para "dar contexto"») | Rompe la regla que hace comparables las invocaciones — y es justo el invariante que A.1 quiere medir · **RESUELTO 2026-09-20.** |
| **R5** | Las devoluciones de escaleta por límites gastan `reintentos_tecnicos` y **paran**; §4.1 manda `escaleta_rechazos_max` y **presentar al usuario** | `arco.md:21` e `interrogatorio.md:38-39` vs `functional.md:276,280,479`. `escaleta_rechazos` existe en `plantillas/estado.json:10` | Una propuesta fuera de límites aborta la ejecución en vez de llegar a ti. (En la novela auditada el contador llegó a 2 y se salvó por poco) |
| ~~**R6**~~ ✅ | El contrato del escritor autoriza una línea de aviso **fuera** del bloque; §5 lo prohíbe sin matices | `.claude/agents/escritor.md:40,44` vs `functional.md:320,351` | Un contrato que autoriza lo que la spec prohíbe, y es un invariante binario de A.1 · **RESUELTO 2026-09-20: se retira la autorización; el escritor sigue al libro de estado y calla.** |
| **R7** | La 5ª prohibición del MEMORY («tocar cualquier otro fichero», con `git status`) **no está implementada** | `technical.md:203` dice que la comprueba `comprobar_variante.py`; su 5ª comprobación es `# 5. tamano` (`comprobar_variante.py:139`) | Una variante que edite un tercer fichero pasa la puerta e invalida la comparación |
| **R8** | TRIGGER requisito 3: la spec exige **árbol limpio**; el guion comprueba solo el fichero del prompt | `technical.md:127` vs `preparar.py:164-166` (`git status --porcelain -- <prompt>`) | Hoy el guion **pasa** con 46 entradas sucias. La puerta que debía bloquear el bucle no bloquea · **CONFIRMADO EN VIVO 2026-09-20**: con 71 entradas sucias imprime «3. `.claude/agents/revisor-encargo.md` en git y limpio» y sale 0 |
| **R9** | La restricción dura `cita_verificable >= 0,90` **nunca se evalúa** para `revisor-encargo` | `puntuar.py:119-124` marca `"aplicable": false` si ningún problema trae cita; §5.6 no tiene campo `cita` (→A4). Los 8 `score.json`: `false` | De las dos restricciones del GOAL solo opera una. El camino barato «subir recall inventando problemas» queda abierto — y es lo que el anexo quiere cerrar |
| **R10** | `puntuar.py` **reimplementa** el recall en vez de importar el evaluador; `technical.md:160` promete «una sola fuente de verdad» | `puntuar.py:30` importa `recall_revisor` pero solo usa `_a_json`, `_texto_problemas`, `_normalizar`, `MIN_CARACTERES_CITA` (líneas 41, 59, 68). `evaluate()` no se llama nunca. Además `puntuar.py:61` filtra por gravedad y `evaluate()` no | Dos implementaciones que dan números distintos. **Bloquea A.1 tal como está redactado:** hoy no hay dónde «enchufar» un evaluador |
| ~~**R11**~~ ✅ | El permiso no cubre el comando que el procedimiento prescribe | `invocar.md:129` (`git clean -fdq -e .descartado novelas/<slug>`) vs `settings.json:19` (`Bash(git clean -fdq novelas/*)`) | `descartar()` pediría permiso justo en la reanudación. **No verificado en ejecución** · **RESUELTO 2026-09-20: `settings.json:19` pasa al literal exacto, y `hook.sh` gana una tercera seccion («permisos vs procedimientos») que comprueba los 6 comandos git que `invocar.md` prescribe contra la lista `allow`. Con el permiso viejo, falla.** |

### Incoherente

| # | Qué | Evidencia |
|---|---|---|
| **I1** | `technical.md:103` dice del bucle «diseñado y **no ejecutado**»; hay una ejecución completa en disco | `optimizaciones/revisor-encargo-20260918-1600/ejecucion.json` |
| **I2** | Tres recuentos de invocaciones, ninguno coincide: **38 / 37 / 36** | `ejecucion.json:15` e `informe.md:39` → 38; `vueltas.jsonl` suma 9+9+10+9 = 37; en disco hay 36 ficheros de caso. `vuelta-02` declara 10 y tiene 9 |
| **I3** | El informe dice «3 de 6 en búsqueda pasaron a "sin problemas"» en la v2; en la v0 ya había 2, luego la transición real es **1** | `informe.md:30` vs `vuelta-00/busqueda/` y `vuelta-02/busqueda/`. Y esa frase sostiene la lección de `lecciones.md:6` |
| **I4** | La evidencia E4 cita como fuente `comparativa/caso-01-opus-vs-haiku/`, carpeta borrada; y cinco referencias textuales a «consolidación §3/§4/§5/§6», spec borrada | `technical.md:310,418` · `functional.md:17,684`, `technical.md:44,438,493` |
| ~~**I5**~~ ✅ | `comprobar_punteros.sh` sale **0** con R1 e I4 dentro | Su cabecera (líneas 2-5) declara solo 3 comprobaciones: enlaces `[x](y.md)`, nombres de specs retiradas y `§`. No cubre tokens `A-n`, rutas de carpeta ni menciones sin nombre de fichero · **RESUELTO 2026-09-20: comprobaciones 4 (tokens `A-n`) y 5 (rutas de carpeta). Ahora sale 1 y nombra R1 e I4. Lo que sigue sin cubrir, y se queda así a propósito: las menciones sin nombre de fichero, que no resuelven sin ambigüedad.** |
| **I6** | `technical.md:133` dice que los defectos puntuables para `revisor-encargo` son **1 de 30** y que el requisito 1 **falla**; con `ascensores-v1` son **32** y pasa | `technical.md:133` vs `calibracion-recall_revisor.md:5` y los `esperados` de los `score.json`. **CONFIRMADO EN VIVO 2026-09-20**: `preparar.py --comprobar` imprime «1. 32 defectos puntuables … (busqueda 20d/6c, control 12d/3c)» y pasa |
| **I7** | La spec sitúa las variantes en `optimizaciones/<agente>-<fecha>/variante-NN.md`; el disco usa `vuelta-NN/variante.md`. Y «cada vuelta deja un **experiment run**» es falso: solo hay `POST /api/public/scores` con `traceId: None` | `technical.md:210,158` vs el árbol y `puntuar.py:183-210` |
| **I8** | El servidor valida el `slug` con `SLUG_VALIDO` (`index.mjs:171`) pero **no valida** `intencion.novela` ni `intencion.ajustes`, que se concatenan al prompt | `harness.mjs:283-286` (`/novela continuar novelas/${novela} …`) y `:259-262`. Inyección de prompt, no de shell (va por stdin). Servidor en `127.0.0.1:5170`, contención real = `settings.json` + los dos hooks. Matiza `frontend/CLAUDE.md:54` («el navegador nunca decide qué comando se ejecuta») |
| ~~**I9**~~ ✅ | `frontend/CLAUDE.md:54` lista intenciones `empezar/responder/confirmar/pedir cambios`; el código implementa `empezar/responder/continuar` y las otras dos van por `POST /decision` | `harness.mjs:257,271,282` vs `encargos.mjs:175-194`. `technical.md:89` coincide con el código: manda la spec, el desfase está en `CLAUDE.md` · **RESUELTO 2026-09-20.** |
| ~~**I10**~~ ✅ | `arco.md:41` y `final.md:29` cuentan «problemas de gravedad 1–2» donde solo interviene continuidad, que emite 1 y 5 | `functional.md:405`, `revisor-continuidad.md:65`, `invocar.md:88` · **RESUELTO 2026-09-20.** |
| ~~**I11**~~ ✅ | `SKILL.md:120` enseña `[arco 1/1] informe de arco: …`, evento imposible: con un arco no hay informe de arco | `SKILL.md:102`, `arco.md:29`, `functional.md:171` · **RESUELTO 2026-09-20.** |
| ~~**I12**~~ ✅ | §0 declara «Cáscara, antes llamada *runner*»; «runner» sigue vivo en el harness y en `config.json` | `SKILL.md:11,143`, `invocar.md:46,141`, `interrogatorio.md:10,12`, `config.json:2,35,53` vs `functional.md:55` · **RESUELTO 2026-09-20.** |
| **I13** | Los docstrings de los 4 guiones del bucle citan «functional.md §9.5» (vive en `technical.md`) y los ejemplos usan `--conjunto defectos-v1` (es `ascensores-v1`) | `puntuar.py:2`, `preparar.py:2,7`, `comprobar_variante.py:2`, `generar.py:2`, `optimizacion/README.md:10,13` |
| **I14** | El `TODO.md` del índice lista **A21** como pendiente; `CHANGELOG.md` 0.12.0 y `functional.md:446` dicen «cierra A21» | Tres ficheros, dos versiones |
| **I15** | El split real es 20/12 (62,5/37,5), no el 20/10 de la spec, y nada comprueba la proporción | `technical.md:131` vs `preparar.py:142-143` (solo comprueba que ningún split quede a 0) |
| ~~**I16**~~ ✅ | El registro de la novela lleva horas `00:00`–`00:31` frente a mtimes reales 17:56–19:25, y las 6 filas `invocacion` tienen `pal_entrada`/`pal_salida` vacías | `registro.md:15-26` vs `find -printf %T` y `functional.md:495` · **CERRADO 2026-09-20 con el borrado de la novela; el defecto del harness (`pal_*` vacías) sigue → paso 11.** |

### Sucio

| # | Qué | Evidencia |
|---|---|---|
| **S1** | **Commitear solo el índice desactivaría la segunda línea roja.** El `settings.json` del índice no registra `rutas-protegidas.sh`, mantiene `Bash(cat *)` abierto y no tiene `Read(frontend/.env)` — pero el guion del hook **sí** está en el índice | `git show :.claude/settings.json \| grep -c rutas-protegidas` → **0**; `git ls-files --stage .claude/hooks/` lista los dos |
| ~~**S2**~~ ✅ | 5 `.pyc` **trazados en git** pese a `.gitignore:14-15`, y de un Python que ya no existe | `git ls-files \| grep pycache` → 5, todos `cpython-312` · **RESUELTO 2026-09-20.** |
| **S3** | Borrados de disco vivos en el índice: `novelas/.gitkeep` y los 3 ficheros de `encargos/una-persona-…/` | `git ls-files encargos/` los lista; `ls encargos/` → no existe |
| **S4** | 46 entradas sin commitear en dos capas mezcladas; `TODO.md` pierde 15 líneas en la capa de encima | `git status --porcelain`, `git diff --stat` |
| **S5** | 2 commits por delante de `origin/main` sin empujar | `git status -sb` |

### Enfoque

| # | Qué | Por qué |
|---|---|---|
| **E1** | **El anexo**: invariantes binarios junto a la métrica difusa. Pasos 13–18 | El bucle cuelga entero de `recall_revisor`; la única ejecución acabó en estancamiento sospechando del evaluador (§A.5) |
| **E2** | `recall_revisor.evaluate()` usa `EvaluationResult` y `Score` como **globales inyectados por Langfuse**: no se importan en ninguna línea. Fuera de Langfuse, `NameError` | Condiciona A.1: el evaluador nuevo debe poder importarse y ejecutarse en local, porque `puntuar.py` lo llamará sin Langfuse delante |
| **E3** | `ascensores-v1` es **32 defectos inyectados**; los naturales hallados fueron **3** y se descartaron. `generar.py:18-22` ya declara que el recall medido «es probable que sea **OPTIMISTA**» | Problema de validez real. Fuera del anexo por decisión tuya: solo se anota en `TODO.md` (paso 7) |
| **E4** | Entre «carpeta creada» y «escaleta aprobada» no hay punto de commit (`SKILL.md:150`): durante toda la etapa 1, `entrevista.md` y la propuesta están sin versionar y una interrupción los pierde vía `descartar()` | La rama de reanudación de `interrogatorio.md:98` es inalcanzable tras cualquier corte que no pase por `cerrar()`. Esta novela se salvó por 20 minutos |

> Corrección sobre el encargo, sin consecuencias para el plan: `generar.py` **no** dice «0
> naturales», dice **3** (líneas 6-11); y el número **32** no está escrito en ese fichero — se
> computa al ejecutarlo, y sí está escrito en `calibracion-recall_revisor.md:5`.

### No verificado

| Qué | Por qué no | Qué haría falta |
|---|---|---|
| Contenido de `herramientas/optimizacion/conjuntos/` y el `conjunto_hash` `d69413ab6bff` | Bloqueado a propósito, y el bloqueo funcionó las tres veces | `preparar.py --comprobar`, que lo lee sin que el comando nombre la ruta |
| ~~Que `preparar.py --comprobar` salga 0 hoy~~ ✅ | Sin `python` utilizable hasta el paso 2 | **HECHO 2026-09-20: sale 0, los cinco requisitos están.** De paso confirma **R8** e **I6** en ejecución, no por lectura de código |
| ~~**R11**~~ ✅: que el permiso `git clean` falle de verdad | Análisis del literal; depende del motor de prefijos de Claude Code | Un fixture nuevo en `herramientas/pruebas/hook.sh`, o una reanudación real · **HECHO 2026-09-20: el fixture existe y reproduce el fallo.** |
| El origen de la invocación nº 38 (**I2**) | Ningún fichero la registra | Preguntarte, o un log por invocación (lo trae A.2) |
| Si `comprobar_variante.py` aprobó realmente las 3 variantes | Su salida no se guarda | Un log por vuelta (paso 17) |
| Que los 7 evaluadores existan en Langfuse y sus 3 reglas sigan desactivadas | Credenciales y red | `crear.py --dry-run` con credenciales |
| **A.2 incógnita 1**: forma de `toolUseResult` / `is_error` en una invocación fallida | Ninguna invocación de esta máquina ha fallado | Provocar un fallo real (paso 15) |
| **A.2 incógnita 2**: si en **primer plano** se escribe `meta.json` | Los 9 `meta.json` son de segundo plano, incluidos los 3 de esta auditoría | Una invocación con `run_in_background: false` (paso 15) — **punto de parada** |
| Compilación y tipos del frontend | Exige `pnpm install` + `tsc -b`, que escriben | Fuera del encargo de solo lectura |
| Por qué la etapa 1 tardó de 17:56 a 19:25 con horas de registro `00:00`–`00:31` | El registro no lo dice | El log de la sesión, fuera del repositorio |
| Los criterios de aceptación §8.2 | `functional.md:627` dice que ninguno se ejecuta de forma automatizada | Es el guion de A3, fuera de este plan |

---

## Fase C — El plan

**Estabilización** = obligatorio para volver a ejecutar el harness con confianza.
**Mejora** = aplazable. Nada del anexo empieza hasta cerrar el paso 8.

### Bloque 0 — Recuperar el control del repositorio (estabilización)

**1. Resolver la sesión concurrente.** → **R0**
*Toca:* nada del repositorio. Es una decisión operativa.
*Qué hacer:* identificar la sesión que hizo `f22ff8e`, y o dejarla terminar los 3 capítulos o
pararla limpiamente. Mientras corra, **ningún paso de git de este plan es seguro**.
*Terminado cuando:* `git log -1` no cambia en 10 minutos y `git status --porcelain -- novelas/`
está vacío.
*Reversible:* sí. *Decisión previa:* **P1**.

> Si decides dejarla terminar, **R2** te va a estallar en `/novela verificar`. Merece la pena
> mirarlo antes de que gaste 3 capítulos: ver paso 9 y **P2**.

### Bloque 1 — Desbloquear (estabilización)

**2. Fijar el intérprete de Python.** → **R3** · ✅ **HECHO 2026-09-20**
*Tocó:* `herramientas/COMO-USAR.md`, una línea de requisito previo. **Ningún otro fichero.**
*Por qué no los 30 sitios:* el diagnóstico de P3 era erróneo. `~/.local/bin` **ya iba la primera**
del PATH de usuario, por delante de WindowsApps: no había nada que reordenar. Lo que faltaba era
que esa carpeta solo contenía `python3.14.exe`, sin `python.exe` ni `python3.exe`, así que para
esos dos nombres el redirector de la Store ganaba por falta de rival. `uv python install 3.14
--default` crea los dos shims, y los 30 sitios pasan a funcionar **tal como están escritos**.
*Comprobado:* `python --version` → 3.14.7 en Bash y en PowerShell; el comando exacto de
`validar/SKILL.md:29` → EXIT=0; los **8** guiones con `main` responden `--help` con 0 (el plan
decía 7); `preparar.py --comprobar` → EXIT=0.
*Lo que queda vivo:* la documentación asume un `python` utilizable. Eso está escrito ahora en
`COMO-USAR.md`, en la cabecera de la tabla de guiones, con el comando que lo consigue.
*Reversible:* sí, borrando los dos shims de `~/.local/bin`. *Decisión previa:* **P3**, contestada.

**3. Cerrar el punto ciego del comprobador de punteros.** → **I5**; habilita 4, 5 y 6 · ✅ **HECHO 2026-09-20**
*Tocó:* `herramientas/comprobar_punteros.sh`, +56 líneas, dos comprobaciones nuevas.
*Resultado de hoy, que es el que el paso pedía:* **EXIT=1**, y nombra las dos cosas:
- comprobación 4 → `26 sin destino de 26 citados, 82 apariciones`. Eso es **R1** entero.
- comprobación 5 → `comparativa/` en `functional.md` y `comparativa/caso-01-opus-vs-haiku/`
  en `technical.md`. Eso es la mitad de carpetas de **I4**.

**CONTRATO DE FORMATO — lo tiene que respetar el paso 4.** La comprobación 4 da por buena una
entrada solo si la línea **empieza** por el token en negrita, en tabla o en lista. En tabla,
`| **A7** | la pregunta | abierta |`; en lista, `- **A7** la pregunta`. Está anclado a propósito:
este mismo documento ya nombra A2, A10, A19, A20, A21 y A22 de pasada al contar lo que se perdió,
y un patrón suelto habría dado por bueno el backlog entero sin que exista. Si el paso 4 escribe
las entradas de otra forma, la comprobación seguirá en rojo con el trabajo ya hecho.

*Qué se salta la comprobación 5, y por qué* (o gritaría en falso, que es como se muere un
comprobador): la barra suelta de construcciones como `` `input`/`output` ``; los marcadores tipo
`encargos/<slug>/`; las que se crean a demanda — `encargos/` la crea el estudio y `.descartado/`
la crea `descartar()`; y `procedimientos/` y `plantillas/`, que en `functional.md:690-692` se
citan en una tabla cuya columna de ubicación es `.claude/skills/novela/`.

*Comprobado que no es un detector que solo sabe decir que no* — cuatro pruebas, con copia y
restauración de `TODO.md`: una mención en prosa de A7 **no** lo satisface (sigue reclamado);
una entrada de tabla en regla **sí**; una de lista **también**; y creando `comparativa/` la
comprobación 5 pasa a «(ninguna)».

*Nota de rendimiento, que no es de este paso:* el guion tarda **39 s**. Las dos comprobaciones
nuevas cuestan **0,8 s** de ese total; el resto ya estaba en las 1–3, que recorren la lista de
ficheros de git una vez por spec retirada. Molesta porque `CLAUDE.md` manda ejecutarlo antes de
cerrar cualquier cambio de documentación. No lo he tocado: no toca ahora.

*Reversible:* sí. *Decisión previa:* ninguna.
*Ojo al orden:* a partir de ahora `comprobar_punteros.sh` **sale 1 a propósito** y no vuelve a 0
hasta que cierren los pasos 4 (backlog) y 6 (referencias muertas). Es lo diseñado, no una avería.

**4. Reconstruir el backlog `A-n` en `TODO.md`.** → **R1**, e **I14** de paso
*Toca:* `TODO.md`. *Fuente:* `git show HEAD:specs/consolidacion-2026-09-18.md`, que tiene las
26 entradas con opciones y recomendación.
*Produce:* una entrada por cada `A-n` citado (A1–A24, A27, A28) con su pregunta en una línea y
su estado (`abierta` / `cerrada por <versión>`). A21 entra ya como **cerrada** (CHANGELOG 0.12.0).
*Terminado cuando:* la comprobación 4 del paso 3 sale 0.
*Reversible:* sí. *Decisión previa:* **P4**.

**5. Decidir el requisito 3 del TRIGGER.** → **R8**
*Toca:* `herramientas/optimizacion/preparar.py:164-166` **o** `specs/technical.md:127`.
*Terminado cuando:* con el árbol sucio, `preparar.py --comprobar` **falla** por el requisito 3
(si gana la spec), o `technical.md:127` describe lo que el guion hace.
*Reversible:* sí. *Decisión previa:* **P5**.

### Bloque 2 — Árbol limpio (estabilización)

**6. Reparar las referencias documentales muertas y las afirmaciones caducadas.** → **I4, I1, I6**
*Toca:* `specs/technical.md:44,103,133,310,418,438,493` y `specs/functional.md:17,684`.
*Qué hace:* sustituye «`comparativa/caso-01-opus-vs-haiku/`» por «la comparativa del
2026-09-18, retirada en 0.11.0; su resultado es E4»; «consolidación §N» por el `A-n`
correspondiente del `TODO.md` del paso 4; «diseñado y no ejecutado» por «ejecutado una vez el
2026-09-18, resultado ESTANCAMIENTO»; y corrige el «1 de 30» que `ascensores-v1` superó.
*Terminado cuando:* `bash herramientas/comprobar_punteros.sh` → 0.
*Reversible:* sí.

**7. Sacar los `.pyc` del índice y anotar lo que queda fuera del anexo.** → **S2, E3**
*Toca:* 5 rutas bajo `__pycache__` (`git rm --cached`, siguen en disco) y `TODO.md`, con una
entrada sobre la validez de `ascensores-v1`.
*Terminado cuando:* `git ls-files | grep -c pycache` → 0 y el paso 3 sigue en 0.
*Reversible:* sí. *Decisión previa:* **B1** de la lista de borrados.

**8. Commitear, por capas y en este orden.** → **S1, S3, S4, S5**
   a. `git checkout -- novelas/.gitkeep encargos/` → deshace **S3** restaurando lo que el
      índice ya tiene.
   b. **Un solo commit** con `.claude/settings.json` + `.claude/hooks/rutas-protegidas.sh`,
      las dos capas juntas, seguido de `bash herramientas/pruebas/hook.sh`. Es el commit que
      **no se puede partir** (**S1**).
   c. Commit de la consolidación documental (specs, borrados de `comparativa/`, `caveman`, las
      cuatro specs retiradas) con los arreglos de los pasos 3–7 encima.
*Terminado cuando:* `git status --porcelain` vacío **y** `hook.sh` sigue en 21/21 **y**
`preparar.py --comprobar` pasa el requisito 3.
*Reversible:* los commits sí; no hay `push` (está en `deny`). *Decisión previa:* la lista de
borrados, y el paso 1 cerrado.

### Bloque 3 — Coherencia spec ↔ skill ↔ agentes (estabilización)

**9. Decidir qué hacer con la escaleta congelada.** → **R2** · *el más urgente de este bloque*
*Toca:* `novelas/ha-habido-un-apagon-masivo-y-ya-estaba/escaleta.md`, y quizá `estado.json`.
*El problema:* el fichero es inmutable por hook y está commiteado. Arreglarlo exige una
excepción deliberada a la garantía central del sistema, y `functional.md:672` dice «nunca se
repara a mano».
*Opciones y recomendación:* ver **P2**.
*Terminado cuando:* o `/novela verificar` pasa el punto 2 de §8.7 al terminar, o la novela está
declarada como no verificable con su motivo escrito.
*Reversible:* sí mientras no se reescriba el fichero aprobado.
*Y en paralelo, para que no vuelva a pasar:* que `validar_canon` compruebe el frontmatter de
`escaleta.md` contra su propio cuerpo y contra `capitulos_por_arco` — hoy
`interrogatorio.md:65` solo compara biblia contra escaleta. Eso es un cambio de harness y entra
con el paso 11.

**10. `final.md`: la revisión global recibe lo que dice el contrato.** → **R4**
*Toca:* `procedimientos/final.md:21`. En la rama «cabe el manuscrito», `entradas = [manuscrito.md]`.
*Terminado cuando:* `final.md:21` y `functional.md:403` dicen lo mismo, y el invariante «rutas
leídas == contrato» de A.1 pasa sobre esa invocación.
*Reversible:* sí. *Decisión previa:* ninguna — la spec ya decidió.

**11. Las devoluciones de escaleta vuelven a su contador.** → **R5**, y el canon de **R2**
*Toca:* `arco.md:21`, `interrogatorio.md:38-39,65`, `cierre.md:12`.
*Qué hace:* cuentan contra `escaleta_rechazos_max`, usan `estado.escaleta_rechazos`
(`plantillas/estado.json:10`, hoy muerto salvo que esta novela lo dejó en 2), y en modo
propuesta **presentan al usuario** en vez de parar; `ESCALETA_FUERA_LIMITES` cubre las dos
vías, no solo `paginas_objetivo`.
*Terminado cuando:* los tres ficheros citan `escaleta_rechazos_max` y ninguno
`reintentos_tecnicos` para este caso.
*Reversible:* sí.

**12. Los seis arreglos de una línea.** → **R6, R11, I9, I10, I11, I12**
`escritor.md:40,44` (el aviso va dentro del bloque) · `settings.json:19` (el literal exacto de
`invocar.md:129`) · `arco.md:41` y `final.md:29` («gravedad 1») · `SKILL.md:120` (ejemplo con
dos arcos) · `frontend/CLAUDE.md:54` (las intenciones reales) · «runner» → «cáscara» en
`SKILL.md`, `invocar.md`, `interrogatorio.md` y los tres `_nota` de `config.json`.
*Terminado cuando:* `hook.sh` sigue en 21/21 y `grep -rn runner .claude/ config.json` sale vacío.
*Reversible:* sí. *Nota:* el de `settings.json` **exige** un fixture nuevo en `hook.sh`, porque
toca `permissions` (regla de `CLAUDE.md`).

### Bloque 4 — Anexo: invariantes mecánicos (mejora)

**No empieza hasta que el paso 8 cierre con `git status --porcelain` vacío.**

Los pasos 13 y 14 son el precio de entrada que el encargo no contemplaba: **hoy no hay dónde
enchufar un evaluador** (**R10**), así que A.1 no se puede escribir sobre lo que existe.

**13. Hacer enchufable el banco de evaluadores.** → **R10, E2** · *prerrequisito de A.1*
*Toca:* `herramientas/optimizacion/puntuar.py:26-83`, `herramientas/evaluadores/recall_revisor.py`.
*Qué hace:* (a) `importlib.import_module(args.metrica)` en vez de los dos `import` cableados de
`puntuar.py:30-31`; (b) subir a función **pública** del evaluador el emparejamiento que hoy
vive en `_a_json`/`_texto_problemas`/`_normalizar`, y que `puntuar.py` la llame en vez de
reescribir el bucle de `puntuar.py:55-83`; (c) el filtro por gravedad (`CONTRATO`,
`preparar.py:36-39`) pasa a parámetro de esa función, para que Langfuse y local den el mismo
número; (d) el evaluador importa y ejecuta **sin** el runtime de Langfuse (**E2**):
`EvaluationResult`/`Score` quedan tras un adaptador.
*Terminado cuando:* re-puntuar `vuelta-00` con el código nuevo reproduce
`busqueda 0,400 / control 0,500` contra los `score.json` de disco. **Es una prueba de regresión
gratis que deja la ejecución existente.**
*Reversible:* sí.

**14. El evaluador de invariantes de disco — 3 de los 5.** → **A.1**
*Toca:* `herramientas/evaluadores/invariantes_revisor.py` (nuevo) + su `calibracion-*.md`.
Cabecera que documente qué espera de `input`/`output`, como los tres existentes.
*Qué mide, todo de ficheros en disco y sin una sola llamada a modelo:*
   1. la salida es el JSON de `functional.md` §5.6 y parsea, con exactamente tres claves;
   2. las gravedades emitidas están en las del contrato (`CONTRATO`, `preparar.py:36-39`);
   3. no hay fuga de vocabulario de esquema en campos de prosa.
*Por qué solo 3:* los otros dos («rutas leídas == contrato» y `tool_errors = 0`) necesitan A.2,
que tiene un punto de parada. **Estos 3 no dependen de ninguna incógnita y se pueden construir
hoy** — ése es el valor de partir el paso: el anexo deja de ser todo-o-nada.
*Terminado cuando:* corre sobre las 36 invocaciones de `revisor-encargo-20260918-1600` y
devuelve un vector 0/1 por invocación, y marca en rojo la v2 (**I3**).
*Reversible:* sí, es un fichero nuevo.

**15. Resolver las dos incógnitas de A.2 — punto de parada.**
*Toca:* nada del repositorio. Dos experimentos.
   a. **Primer plano.** Una invocación `Agent` con `run_in_background: false` y comprobar si
      aparece `meta.json` en `…/<id-sesion>/subagents/`. Los 9 de esta máquina son de segundo
      plano, incluidos los 3 que dejó esta auditoría.
   b. **Fallo real.** Provocar un error de herramienta en un subagente (un `Read` de ruta
      inexistente) y leer la forma de `toolUseResult` y si aparece `is_error`.
*Terminado cuando:* las dos formas están escritas en `herramientas/optimizacion/README.md`.
*Si (a) sale que en primer plano no se escribe `meta.json`:* **se para aquí.** A.2 no sirve
para `/optimizar`, que exige primer plano; los pasos 16 y 18 decaen y el 14 se queda como el
anexo entero. No es un fracaso: son 3 invariantes binarios más de los que hay hoy.
*Reversible:* no escribe nada.

**16. El lector de transcripciones.** → **A.2** · *solo si el paso 15 no para*
*Toca:* `herramientas/optimizacion/transcripciones.py` (nuevo); `.claude/skills/optimizar/SKILL.md`.
*Qué hace:* empareja por `agentType` + `description` (dos coincidencias = **ERROR**, no se
elige una); de ahí salen `llm_calls` (filas `assistant`), latencia, **coste real** con tabla de
precios por modelo dentro del guion, `tool_calls` y la lista de `file_path` leídos, que alimenta
los 2 invariantes que faltan del paso 14. **Fail-open** como Langfuse: sin carpeta, el bucle
sigue, lo anota y se pierde la métrica de proceso, no el experimento — confirmado necesario:
solo 2 de ~20 sesiones tienen `subagents/`.
*Cambio en la skill:* `/optimizar` pasa a `Agent` una `description` única por caso y vuelta,
`"opt <agente> <ejecucion> v<NN> <split> <id_caso>"`.
*Terminado cuando:* sobre las 9 transcripciones existentes devuelve coste y `tool_calls` sin
excepción, y sobre una sesión sin `subagents/` devuelve `None` sin romper.
*Reversible:* sí. *Decisión previa:* el resultado del paso 15.

**17. La regla de hipótesis falsable.** → **A.3**, y **R7** de paso
*Toca:* `.claude/skills/optimizar/SKILL.md` §8, `.claude/agents/optimizador.md`, la línea de
`vueltas.jsonl`, `specs/technical.md` §9.5.3.
*Qué hace:* `propuesta.json` gana `invariante_objetivo`; si ese invariante **no se mueve**, la
vuelta se revierte pase lo que pase con la métrica global. El optimizador sigue sin puntuar y
sin ver el conjunto etiquetado: los invariantes le llegan **agregados** en `diagnostico.md`,
nunca por caso.
*De paso, misma zona de código:* implementar la 5ª prohibición del MEMORY (**R7**) y guardar la
salida de `comprobar_variante.py` por vuelta, que hoy no se guarda.
*Terminado cuando:* una vuelta de prueba con un invariante que no se mueve queda revertida
aunque el recall suba.
*Reversible:* sí.

**18. Consecuencia documental del anexo.**
*Toca:* `specs/technical.md` §9.5.1 y §9.5.6, que justifican el tope **de invocaciones** porque
«en el hito 1 la herramienta `Agent` no devuelve tokens de subagente». Con el paso 16 sí los
hay: escribir qué deja de ser cierto y desde cuándo, sin borrar el motivo histórico.
*Terminado cuando:* `comprobar_punteros.sh` → 0 y ninguna de las dos secciones afirma que no
hay tokens de subagente.
*Reversible:* sí.

### Qué dejo fuera a propósito

- **R9** (`cita_verificable` inoperante) depende de **A4**, una de las preguntas que el paso 4
  reconstruye: no se puede resolver antes de que A4 exista otra vez.
- **I2** e **I3** son de una ejecución cerrada y archivada. Corregir un informe de cierre a
  posteriori es peor que anotarlo: van como nota al pie en `lecciones.md`, con el paso 17.
- **I8** (validación asimétrica del servidor) y **E4** (sin punto de commit en la etapa 1) son
  hallazgos reales que **no** he metido en el plan porque cambian diseño y son tuyos de
  decidir. Van a `TODO.md` con el paso 4, como `A-n` nuevos.
- **I16** (horas y `pal_*` del registro) está commiteado y es inmutable; se anota, no se repara.

---

## Lista de borrados — apruébalos uno a uno

**No se borra nada sin tu sí explícito, fichero a fichero.** Nada de esta lista se ha tocado.

| # | Qué | Qué es exactamente | Recomendación |
|---|---|---|---|
| **B1** | 5 ficheros `herramientas/*/__pycache__/*.pyc` | Bytecode de Python 3.12, intérprete que ya no existe. Trazados pese a `.gitignore:14-15` | **`git rm --cached`, no borrar del disco.** Se regeneran solos |
| **B2** | `specs/hallazgos.md`, `specs/inventario.md`, `specs/revision-harness-2026-09-17.md` | Ya borrados en el índice. Contenido absorbido en `technical.md` (E1–E7) y declarado en los `sustituye_a` | **Confirmar.** Recuperables con `git show HEAD:<ruta>` |
| **B3** | `specs/consolidacion-2026-09-18.md` | Ya borrado en el índice. **Es la única fuente de A1–A28** | **Confirmar solo DESPUÉS del paso 4.** Si el borrado se commitea antes de rescatar el backlog, quedan 82 punteros huérfanos y un `git show` como única memoria |
| **B4** | `comparativa/` (5 ficheros) | Retirada a propósito en CHANGELOG 0.11.0; `functional.md:651` lo declara | **Confirmar**, y con ella el paso 6 |
| **B5** | `.claude/skills/caveman/SKILL.md` | Skill ajena al proyecto, borrada en el índice | **Confirmar** |
| **B6** | `.claude/skills/novela/procedimientos/comparar.md` | Va con B4. Verificado: **nadie lo cita** en todo el repositorio | **Confirmar** |
| **B7** | `encargos/una-persona-que-desde-los-10-anos-se-des/` (3 ficheros) | Borrados del **disco**, vivos en el índice. Son el encargo de una novela que sigue en `novelas/`; `functional.md:61` dice que el encargo se versiona a propósito | **Ya no aplica el motivo original: la novela `una-persona-…` se borró el 2026-09-20, así que el encargo no respalda nada vivo. Confirmar el borrado o restaurar, da igual** |
| **B8** | `novelas/.gitkeep` | Borrado del disco, vivo en el índice. `novelas/` ya tiene 4 carpetas | **Restaurar o confirmar**, da igual |

---

## Preguntas que necesito que contestes antes de empezar

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| **P1** | La sesión concurrente que hizo `f22ff8e`: ¿la paro, la dejas terminar, o no sabías que estaba? | (a) dejarla terminar los 3 capítulos; (b) pararla ya; (c) averiguar primero qué es | **(c) y luego (b).** Va a chocar con R2 al verificar, y mientras corra no puedo tocar git · **CONTESTADA: la sesión murió sola el 19-09 a las 19:31.** |
| **P2** | **R2**, la escaleta congelada con 3 arcos en el frontmatter y 1 en todo lo demás | (a) dejarla correr y aceptar que §8.7 falle, documentándolo; (b) corregir el frontmatter saltándose la inmutabilidad, con la excepción anotada en el registro; (c) descartar la novela y relanzarla con el canon ya arreglado | **(c) si la ejecución no ha gastado aún capítulos** — es la única que no rompe una garantía ni deja una novela invalidada. Si ya hay capítulos escritos, **(b)** con la excepción por escrito · **CONTESTADA por (c): novela borrada el 2026-09-20.** |
| **P3** | ¿Cómo se arregla `python`? | (a) arreglar la máquina: `~/.local/bin` delante del alias de la Store en el PATH; (b) resolver el intérprete en documentación y skills (`$PY`); (c) las dos | **(c)**: (a) arregla hoy, (b) sobrevive a la próxima máquina, que es el punto entero del hito 2 · **CONTESTADA 2026-09-20 por (a) sola, y la premisa de (a) era falsa**: el PATH ya estaba bien ordenado, faltaban los shims. Con `python` funcionando, (b) se descartó — la documentación ya no se contradice con la máquina, y `$PY` no sobrevive entre llamadas a Bash porque cada una abre un shell nuevo |
| **P4** | ¿Cuánto del backlog `A-n` se rescata al `TODO.md`? | (a) las 26 entradas completas con opciones y recomendación; (b) una línea por `A-n` con la pregunta y un puntero a `git show`; (c) solo las que siguen citadas | **(b)**: `TODO.md` es un índice de pendientes, no un archivo de deliberación; (a) lo convierte otra vez en la spec borrada |
| **P5** | Requisito 3 del TRIGGER: ¿árbol limpio entero o solo el prompt? | (a) el guion se ajusta a la spec (árbol entero); (b) la spec se ajusta al guion (solo el prompt, motivo ya escrito en `preparar.py:168`) | **(a)**, porque el motivo declarado de la regla es que la ejecución sea reproducible desde un commit y eso el fichero suelto no lo da. Es tu llamada: (b) está razonada en el código |
| **P6** | ¿Empujo los 2 commits a `origin/main` al cerrar el bloque 2? | (a) no, los dejas tú; (b) sí | **(a)**: `Bash(git push*)` está en `deny` de `settings.json:38` a propósito |
