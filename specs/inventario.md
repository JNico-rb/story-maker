# Inventario de salidas

Qué se espera que produzca el harness en una ejecución completa. Sirve para tres cosas:

1. **Saber qué vas a recibir** antes de lanzarlo.
2. **Comprobar que una ejecución está completa**: si falta algo de aquí, algo se detuvo (mira `informe-cierre.md`).
3. **Comparar** dos ejecuciones con la misma idea y distinta configuración (ver [comparativa/](../comparativa/README.md)), y definir qué significa "la misma salida" cuando el runner de la fase 2 sustituya a Claude Code (`specs/functional.md` §10.3): una carpeta generada por el runner tiene que pasar esta misma lista.

Los números concretos corresponden al perfil activo de [`harness.config.json`](../harness.config.json). Las tablas usan el perfil por defecto, `relato` (3 capítulos × 1.500 palabras).

---

## 1. Lo que entrega, fichero a fichero

Todo vive en `novelas/<slug>/`. "DdH" = definición de hecho: cuándo ese artefacto está bien.

### Entrada y configuración

| Artefacto | Cuántos | Lo escribe | DdH |
|---|---|---|---|
| `idea.md` | 1 | Orquestador | Contiene la idea literal del usuario, sin reinterpretar |
| `config.json` | 1 | Orquestador | Perfil ya resuelto + formato, modelos, límites, veredicto, memoria, y `origen` con lo sobreescrito por comando |
| `entrevista.md` | 1 | Orquestador | `cerrada: true`; todas las decisiones en pregunta → respuesta, marcando cuáles eligió el usuario y cuáles quedaron en "decide tú" |

### Plan

| Artefacto | Cuántos | Lo escribe | DdH |
|---|---|---|---|
| `biblia.md` | 1 | Interrogador | `aprobada: true`; premisa, mundo post-IA, **3–7 reglas inviolables numeradas**, tono/PDV/estilo, y por personaje: quién es, qué quiere, arco y voz. Más la lista de decisiones que tomó él |
| `escaleta.md` | 1 | Interrogador | `aprobada: true`; `capitulos` dentro de límites; una entrada por capítulo con `n, titulo, acto, objetivo, sucesos (2–5), personajes, gancho, palabras_objetivo`; los tres actos presentes; sección "Hilos" con dónde abre y cierra cada uno |

### Por capítulo (carpeta `capitulos/NN/`)

| Artefacto | Cuántos por capítulo | Lo escribe | DdH |
|---|---|---|---|
| `intento-K.md` | 1 a 3 | Escritor | Frontmatter con `palabras`; cumple objetivo, sucesos y gancho de su entrada de la escaleta |
| `resumen-K.md` | 1 por intento | Escritor | Frontmatter con `hilos_abiertos`, `hilos_cerrados`, `personajes` con estado; cuerpo con hechos, cambios, elementos nuevos y enlace |
| `informe-K.md` | 1 por intento | Orquestador (con el YAML del revisor) | `veredicto` recalculado por el harness; cada problema con `gravedad`, `donde`, `que`, `por_que` |
| `notas-revisor-K.md` | 0 o 1 | Revisor | Opcional; solo si necesitó apuntes |

Con el perfil `relato`: **mínimo 9 ficheros** de capítulo (3 capítulos aprobados al primer intento) y **máximo 27** (3 intentos cada uno). Que haya varios intentos no es un fallo: es el bucle de revisión funcionando, y los rechazados se conservan a propósito.

### Salida

| Artefacto | Cuántos | Lo escribe | DdH |
|---|---|---|---|
| `manuscrito.md` | 1 | Orquestador | Título, índice y los capítulos **aprobados** en orden; nota final si alguno se aceptó por agotamiento |
| `informe-global.md` | 1 | Orquestador (con el YAML del revisor) | Hilos sin cerrar, contradicciones entre capítulos lejanos, personajes desaparecidos, cambios en las reglas del mundo. Puede estar vacío de problemas: eso es buena señal |
| `informe-cierre.md` | 1 (se reescribe cada ejecución) | Orquestador | `resultado: EXITO` o `PARADA` con motivo, qué quedó hecho y la acción para continuar |

### Trazabilidad

| Artefacto | Cuántos | Lo escribe | DdH |
|---|---|---|---|
| `estado.json` | 1 | Orquestador | Refleja el último punto consistente; `fase: completa` al terminar |
| `registro.md` | 1 | Orquestador | Una fila por evento: invocaciones (con modelo, `pal_entrada` y `pal_salida`), veredictos, decisiones, reintentos, escrituras revertidas, commits |
| Commits en git | ≥ 3 + 1 por capítulo | Orquestador | `novela <slug>: carpeta creada` · `escaleta aprobada` · `cap NN cerrado (intento K)` · `novela completa` |

---

## 2. Cuánto texto, por perfil

| Perfil | Capítulos | Palabras/capítulo | Manuscrito | Páginas (250 p/pág) | Ficheros de capítulo (mín–máx) |
|---|---|---|---|---|---|
| `relato` | 3 | 1.500 | ~4.500 | ~18 | 9–27 |
| `novela_corta` | 12 | 2.000 | ~24.000 | ~96 | 36–108 |
| `novela` | 30 | 2.500 | ~75.000 | ~300 | 90–270 |
| `saga` | 100 (hasta 200) | 2.500 | ~250.000 (hasta ~500.000) | ~1.000 (hasta ~2.000) | 300–900 (hasta 600–1.800) |

Cada capítulo aprobado debe caer dentro de `palabras_objetivo ± formato.tolerancia_longitud` (±20 % por defecto). El manuscrito hereda esa tolerancia.

---

## 3. Lo que NO genera

Para que no lo busques: PDF, DOCX, EPUB ni HTML (§1.3 de la funcional); ilustraciones; portada; traducciones; coste en dinero. Sí genera el **volumen** (palabras de entrada y salida por invocación y modelo, en `registro.md` y en el informe de cierre): con la tarifa del modelo que quieras, el coste sale de ahí. El manuscrito es Markdown y lo conviertes tú con lo que prefieras.

Tampoco genera una novela **corregida** tras la revisión global: ese informe se entrega tal cual y decides tú qué hacer con él.

---

## 4. Comprobar que una ejecución está completa

Orden de comprobación, de lo más barato a lo más caro:

1. `informe-cierre.md` dice `resultado: EXITO`.
2. `estado.json` tiene `fase: completa`, `informe_global: true` y una entrada en `capitulos` por cada capítulo de la escaleta.
3. Existen `manuscrito.md` e `informe-global.md`.
4. Para cada capítulo N: existe el `intento-K.md` que `estado.capitulos[N].aprobado` señala, con su `resumen-K.md` e `informe-K.md`.
5. El recuento de palabras de cada capítulo aprobado está dentro de la tolerancia.
6. `git log` muestra los commits esperados y `git status` está limpio.

Si algo falla, `informe-cierre.md` dice el motivo y la acción; nunca hay que reparar la carpeta a mano.

---

## 5. Señales de calidad (no de completitud)

Lo anterior dice si la ejecución terminó. Esto dice si salió *bien*:

| Señal | Dónde se ve | Qué es buena señal |
|---|---|---|
| Capítulos aceptados por agotamiento | `estado.avisos`, informe de cierre | Cero. Uno o dos es tolerable; muchos indican que la escaleta o la biblia piden algo imposible |
| Problemas de gravedad 1–2 en los informes | `capitulos/*/informe-*.md` | Que aparezcan en el intento 1 y desaparezcan en el 2: el bucle está haciendo su trabajo |
| Problemas en el informe global | `informe-global.md` | Ninguno de gravedad 1–2. Hilos sin cerrar solo si la escaleta los dejaba abiertos a propósito |
| Discrepancias de veredicto | `registro.md` (`discrepancia_veredicto`) | Pocas. Muchas significan que el revisor no está aplicando bien su propia regla |
| Escrituras fuera de zona | `registro.md` | Cero. Cualquiera indica que hay que endurecer la definición de ese subagente |
| Desviación de longitud | Frontmatter `palabras` de cada intento aprobado | Dentro de ±20 % sin necesidad de reescritura |
