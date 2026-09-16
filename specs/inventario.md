# Inventario de salidas

Qué produce el harness en una ejecución completa. Sirve para tres cosas:

1. **Saber qué vas a recibir** antes de lanzarlo.
2. **Comprobar que una ejecución está completa**: `/novela verificar <carpeta>` ejecuta la lista de §4. Si falta algo, algo se detuvo (mira `informe-cierre.md`).
3. **Definir "la misma salida"** para comparar dos ejecuciones ([comparativa/](../comparativa/README.md)) y para el runner del hito 2 (`specs/functional.md` §10.3): una carpeta generada por el runner tiene que pasar esta misma lista sin adaptación.

Los números concretos dependen del perfil activo de [`config.json`](../config.json). Las tablas usan el perfil por defecto, `relato` (5 capítulos × 1.500 palabras, un arco). Vocabulario: `specs/functional.md` §0.

---

## 1. Lo que entrega, fichero a fichero

Todo vive en `novelas/<slug>/`. **Todo lo escribe el harness**; la columna "Contenido de" dice qué agente produjo el contenido. "DdH" = definición de hecho: cuándo ese artefacto está bien.

### Entrada y configuración

| Artefacto | Cuántos | Contenido de | DdH |
|---|---|---|---|
| `idea.md` | 1 | Usuario | La idea literal, sin reinterpretar |
| `config.json` | 1 | Harness | `version: 3`; perfil ya resuelto (con `nombre`) + `proveedor`, `formato`, `modelos`, `limites`, `veredicto`, `memoria`, `calidad`, y `origen` con lo sobreescrito por comando. Sin `perfiles` |
| `entrevista.md` | 1 | Usuario (vía grilling) o fichero | `cerrada: true`, `origen: grilling | fichero`; todas las decisiones en pregunta → respuesta, cada una marcada [usuario], [recomendación aceptada] o [decide tú] |

### Plan

| Artefacto | Cuántos | Contenido de | DdH |
|---|---|---|---|
| `biblia.md` | 1 | Interrogador | `aprobada: true`; premisa, mundo post-IA, **3–7 reglas inviolables numeradas**, tono/PDV/estilo, personajes (quién es, qué quiere, arco, voz), decisiones del interrogador |
| `escaleta.md` | 1 | Interrogador | `aprobada: true`; `capitulos` dentro de límites; `arcos` que cubren 1..`capitulos` sin huecos ni solapes, ninguno mayor que `formato.capitulos_por_arco`, cada uno con `acto, objetivo, sucesos_clave, hilos_abre, hilos_cierra`; los tres actos presentes; sección Hilos |
| `arcos/arco-AA.md` | 1 por arco | Interrogador | `validada: true`; una entrada por capítulo del rango con `n, titulo, objetivo, sucesos, personajes, gancho, palabras_objetivo`; cada `palabras_objetivo` dentro de límites; todos los `sucesos_clave` del arco asignados a alguna entrada |

### Por capítulo (carpeta `capitulos/NN/`)

| Artefacto | Cuántos por capítulo | Contenido de | DdH |
|---|---|---|---|
| `intento-K.md` | 1 a 3 | Escritor | Sin frontmatter: primera línea `# <título>`, después el texto. El aprobado cumple objetivo, sucesos y gancho de su entrada y está dentro de la tolerancia de longitud (`wc -w`) |
| `resumen-K.md` | 1 por intento que pasó la longitud | Resumidor | Frontmatter con `capitulo, intento, hilos_abiertos, hilos_cerrados, personajes`; secciones Hechos, Cambios en personajes, Elementos introducidos, Enlace |
| `libro-estado-K.md` | 1 por intento que pasó la longitud | Resumidor | Libro de estado completo tal como quedaría si se aprueba este intento |
| `informe-K.md` | 1 por intento | Revisor (o harness si rechazo por longitud) | `veredicto` recalculado por el harness; `origen: revisor | harness`; cada problema con `gravedad ∈ {1,2,3,4,5}, donde, que, por_que` |

Un capítulo rechazado por longitud tiene `intento-K.md` e `informe-K.md` pero no `resumen-K.md` ni `libro-estado-K.md`: no llegó al resumidor. Con el perfil `relato`: **mínimo 20 ficheros** de capítulo (5 aprobados al primer intento) y **máximo 60**. Que haya varios intentos no es un fallo: es el bucle de revisión funcionando, y los rechazados se conservan a propósito.

### Memoria y revisiones intermedias

| Artefacto | Cuántos | Contenido de | DdH |
|---|---|---|---|
| `libro-estado.md` | 1 | Resumidor (adoptado por el harness) | `hasta_capitulo` = último capítulo aprobado; copia exacta del `libro-estado-K.md` del intento aprobado de ese capítulo; secciones Personajes, Hilos abiertos, Hilos cerrados, Elementos, Reglas en vigor |
| `arcos/informe-arco-AA.md` | 1 por arco, **solo si hay más de un arco** | Revisor | `capitulo: arco-AA`; veredicto informativo; problemas con la forma estándar |

### Salida

| Artefacto | Cuántos | Contenido de | DdH |
|---|---|---|---|
| `manuscrito.md` | 1 | Harness | Título, índice y los capítulos **aprobados** en orden; nota final si alguno se aceptó por agotamiento |
| `informe-global.md` | 1 | Revisor | `capitulo: global`; `base: manuscrito | resumenes`; veredicto informativo. Puede estar vacío de problemas: eso es buena señal |
| `informe-cierre.md` | 1 (se reescribe cada ejecución) | Harness | `resultado: EXITO | PARADA` con motivo, qué quedó hecho, volumen, **métricas de calidad** con CUMPLE / NO CUMPLE, inventario y la acción para continuar |

### Trazabilidad

| Artefacto | Cuántos | Contenido de | DdH |
|---|---|---|---|
| `estado.json` | 1 | Harness | `version: 3`; refleja el último punto consistente; `etapa: completa` al terminar; `capitulos[N]` con `aprobado, por_agotamiento, intentos` para todo N; `arcos[A]` con `escaleta_validada: true` |
| `registro.md` | 1 | Harness | Una fila por evento; cada `invocacion` con `modelo`, `pal_entrada`, `pal_salida` y, si los hay, `tok_*` y `coste_usd` |
| Commits en git | ≥ 3 + 1 por capítulo + 2 por arco extra | Harness | `novela <slug>: carpeta creada` · `escaleta aprobada` · `arco AA detallado` · `cap NN cerrado (intento K)` · `arco AA revisado` · `novela completa` |

---

## 2. Cuánto texto, por perfil

| Perfil | Capítulos | Palabras/capítulo | Arcos | Manuscrito | Páginas (250 p/pág) | Ficheros de capítulo (mín–máx) |
|---|---|---|---|---|---|---|
| `relato` | 5 | 1.500 | 1 | ~7.500 | ~30 | 20–60 |
| `novela_corta` | 12 | 2.000 | 1 | ~24.000 | ~96 | 48–144 |
| `novela` | 30 | 2.500 | 2 | ~75.000 | ~300 | 120–360 |
| `saga` | 100 (hasta 200) | 2.500 | 7 (hasta 14) | ~250.000 (hasta ~500.000) | ~1.000 (hasta ~2.000) | 400–1.200 (hasta 800–2.400) |

Cada capítulo aprobado está dentro de `palabras_objetivo ± formato.tolerancia_longitud` (±20 % por defecto), medido con `wc -w`. A partir de `novela` la revisión global se hace sobre resúmenes e informes de arco, no sobre el manuscrito (`limites.revision_global_max_palabras`).

---

## 3. Lo que NO genera

PDF, DOCX, EPUB ni HTML (spec §1.3); ilustraciones; portada; traducciones; coste en dinero en el hito 1 (sí el **volumen**, en `registro.md` y en el informe de cierre; en el hito 2 también el coste real). Tampoco una novela **corregida** tras las revisiones de arco y global: esos informes se entregan tal cual y decides tú qué hacer con ellos.

---

## 4. Comprobar que una ejecución está completa

Es lo que ejecuta `/novela verificar <carpeta>`, de lo más barato a lo más caro:

1. `informe-cierre.md` dice `resultado: EXITO`.
2. `estado.json` tiene `version: 3`, `etapa: completa`, `informe_global: true`, una entrada en `capitulos` por cada capítulo de `escaleta.md` y `escaleta_validada: true` en todos los arcos.
3. Existen `biblia.md` y `escaleta.md` con `aprobada: true`, un `arcos/arco-AA.md` con `validada: true` por arco, `libro-estado.md` con `hasta_capitulo` = total, `manuscrito.md` e `informe-global.md`. Si hay más de un arco, un `arcos/informe-arco-AA.md` por arco.
4. Para cada capítulo N: existen `intento-K.md`, `resumen-K.md`, `libro-estado-K.md` e `informe-K.md` para la K que `estado.capitulos[N].aprobado` señala, y ese informe tiene `veredicto: APROBADO` o el capítulo tiene `por_agotamiento: true`.
5. `wc -w` de cada capítulo aprobado está dentro de la tolerancia de su `palabras_objetivo`.
6. `git log -- novelas/<slug>` muestra los commits esperados y `git status --porcelain novelas/<slug>` está vacío.

Después, si la novela está completa, `calcular_metricas` (`procedimientos/final.md`). Si algo falla, `informe-cierre.md` dice el motivo y la acción; nunca hay que reparar la carpeta a mano.

---

## 5. Señales de calidad

Lo anterior dice si la ejecución terminó. Las **métricas de §8.3 de la spec** dicen si salió bien, con umbrales en `config.calidad`. Además de ellas, tres señales que no tienen umbral pero conviene mirar:

| Señal | Dónde se ve | Qué es buena señal |
|---|---|---|
| Problemas de gravedad 1–2 en los informes de capítulo | `capitulos/*/informe-*.md` | Que aparezcan en el intento 1 y desaparezcan en el 2: el bucle hace su trabajo |
| Discrepancias de veredicto | `registro.md` (`discrepancia_veredicto`) | Pocas. Muchas significan que el revisor no aplica su propia regla |
| Fidelidad del libro de estado | Tres hechos del capítulo 1 comprobados en `libro-estado.md` final (comparar.md) | Los tres coinciden. Si no, el resumidor está inventando o perdiendo |
