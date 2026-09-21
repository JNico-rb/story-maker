---
spec_version: 1.0.0
config_version_requerida: 4
fecha: 2026-09-19
deriva_de: functional.md 1.0.0
sustituye_a: "hallazgos.md, inventario.md, functional.md §9"
caracter: mixto
---

# story-maker — Especificación técnica

Dónde vive cada regla de [functional.md](functional.md) y con qué datos se decidió. Dos partes con **estatus distinto**, y conviene no confundirlas:

- **§9 — Dónde está implementado.** Es **normativa**, igual que el resto de functional.md: §9.3 fija las seis reglas de observabilidad, §9.5 lo que el optimizador puede y no puede hacer, §9.6 las precondiciones de `/validar`. Conserva la numeración `§9.x` que tenía en functional.md: una referencia a `§9.5` escrita en cualquier parte del repositorio sigue resolviendo sin cambios.
- **Evidencia `E1`–`E7`.** **No manda sobre nada**: es el *porqué*, con la cifra que lo sostiene y de dónde salió. Si una cifra no está, es que no se tiene (`desconocido`); ninguna se estima.

Si esta spec y functional.md discrepan sobre una regla de flujo, gana functional.md. Si discrepan sobre dónde está implementada, gana esta.

---

## 9. Dónde está implementado

| Qué | Dónde |
|---|---|
| Especificación normativa (§0–§8, §10) | [functional.md](functional.md) |
| Variables (§7) | [config.json](../config.json) |
| Reglas globales | [CLAUDE.md](../CLAUDE.md) |
| Permisos y registro del hook | [.claude/settings.json](../.claude/settings.json) |
| Hook de inmutabilidad | [.claude/hooks/inmutables.sh](../.claude/hooks/inmutables.sh) |
| Orquestador | [SKILL.md](../.claude/skills/novela/SKILL.md) |
| Etapa 1 · arco · capítulo · final · invocar · cierre | [procedimientos/](../.claude/skills/novela/procedimientos/) |
| Formato de artefactos | [plantillas/](../.claude/skills/novela/plantillas/) |
| Contratos | [.claude/agents/](../.claude/agents/) |
| Caso de referencia | [pruebas/referencia/](../pruebas/referencia/) |
| Visor y estudio | [frontend/](../frontend/) · `encargos/<slug>/` |
| Observabilidad y evaluadores | [herramientas/trazas/](../herramientas/trazas/) · [herramientas/evaluadores/](../herramientas/evaluadores/) |
| Bucle de optimización (§9.5) | [.claude/skills/optimizar/](../.claude/skills/optimizar/SKILL.md) · [.claude/agents/optimizador.md](../.claude/agents/optimizador.md) · [herramientas/optimizacion/](../herramientas/optimizacion/) · `optimizaciones/` |
| Validador de manuscrito (§9.6) | [.claude/skills/validar/](../.claude/skills/validar/SKILL.md) · [herramientas/validacion/](../herramientas/validacion/) · `validaciones/` |
| Evidencia (E-n) | [Evidencia](#evidencia-e1e7), en este mismo fichero |
| Diagramas del flujo | [architecture.md](architecture.md) |

### 9.1 Cómo se escribe el orquestador

SKILL.md es **pseudocódigo numerado con nombres de función estables**; cada procedimiento implementa una o varias. En el hito 2 **el mismo texto** lo ejecuta el orquestador LLM de la cáscara: no se traduce a código (decisión 2026-09-18; SKILL.md e `invocar.md` aún dicen lo contrario → consolidación §6).

`comprobar_entorno` · `crear_novela` · `resolver_perfil` · `entrevistar` · `proponer_escaleta` · `validar_canon` · `detallar_arco` · `escribir_capitulo` · `comprobar_longitud` · `resumir` · `revisar` · `decidir` · `mejor_intento` · `cerrar_capitulo` · `revisar_arco` · `ensamblar` · `revisar_global` · `escribir_erratas` · `calcular_metricas` · `cerrar` · `reanudar` · `invocar` · `elegir_modelo` · `commitear` · `descartar`. Dónde vive cada una: SKILL.md §0–§9 y los procedimientos.

### 9.2 El visor (`frontend/`)

Aplicación web local que cruza los ficheros de una novela. **Solo lee**; no es parte del harness (borrar `frontend/` no cambia nada); no inventa datos (las métricas las muestra de `informe-cierre.md` o dice que no las hay). Servidor local sin dependencias que interpreta §3 y sirve JSON; la web pinta. Funciona sobre carpetas de los dos hitos. Reglas de código: [frontend/CLAUDE.md](../frontend/CLAUDE.md).

### 9.3 Observabilidad (Langfuse)

Mismo estatus que el visor: **fuera del harness, solo lectura, borrable**. Reglas por orden `[harness · ambos]`:
1. **Nunca fuente de verdad**: manda `registro.md`.
2. **Nunca puerta del flujo**: ni un `curl` dentro de `invocar()`.
3. **Fail-open**.
4. **No escribe en `novelas/`**.
5. **Credenciales fuera del repositorio**: `.claude/settings.local.json` y `.env`, ignorados.
6. **Credenciales no legibles desde la sesión**: `deny` de `Read` sobre ambos, **y** `PreToolUse` sobre `Bash` (`.claude/hooks/rutas-protegidas.sh`), porque el `deny` de `Read` no gobierna lo que lee un comando `[hook · ambos]`.

| Nivel | Qué | Cómo | Marca |
|---|---|---|---|
| Traza de sesión | Cada prompt y herramienta del orquestador, tokens del orquestador; subagentes sin tokens | Hook `Stop` fuera del repositorio, `TRACE_TO_LANGFUSE` | **CC**. En la cáscara, instrumentación nativa |
| Traza de dominio | novela › capítulo › intento › invocación desde `registro.md` | `herramientas/trazas/exportar.py`, después, a mano | ambos |

**Estado del exportador a 2026-09-18** (E6): `input`/`output` a `null` en todas las generaciones; `metadata.resultado` siempre `desconocido` (busca `"resultado ok"` y el registro escribe `resultado: ok`); filas `pendiente` exportadas como generaciones (+22 %); fila de corrección exportada como agente; `trace_id` no determinista (cuatro trazas para dos novelas); todas las observaciones con el instante de la exportación. Lectura de vuelta: la API legada responde 410; `GET /api/public/v2/observations` con `fields=core,io,metadata`, sin `name`, con retardo de ingesta (~45 s) y 30 peticiones/minuto. Arreglos → A13; ninguno toca el harness.

#### 9.3.1 Evaluadores (estado a 2026-09-18)

Siete evaluadores creados en Langfuse por `herramientas/evaluadores/crear.py`, fuera del harness, que **miden a los revisores**, no a la novela (E5):

| Score | Tipo | Sobre |
|---|---|---|
| `lengua_erratas` · `verosimilitud_dominio` · `coherencia_interna` · `mundo_presente` | Juez LLM | `output` del escritor (+ contexto) |
| `cita_verificable` | Código | Informe + capítulo |
| `redundancia_resumen` | Código | Resumen N + N−1 |
| `recall_revisor` | Código, experimento | Dataset etiquetado + informe; **sin regla** |

**Las tres reglas están DESACTIVADAS** (`enabled: false`): activarlas puntuaría el vacío mientras el exportador mande `input`/`output` a `null` y `resultado` mal calculado. Filtros por `metadata.agente`, `metadata.modo starts with capitulo`, `metadata.resultado = ok`. El juez configurado es `openrouter/free`, que **incumple** la regla "el juez nunca es el modelo que escribió" → A14. El dataset de 30 defectos etiquetados **no está en el repositorio** → A24. Circuito **diseñado en §9.5** (2026-09-18): Langfuse es el laboratorio; un prompt calibrado **asciende** a producción. Los evaluadores **nunca** entran en el bucle de la novela.

### 9.4 El estudio (`frontend/`)

Recoge los inputs y arranca el harness. **Fachada, no camino alternativo**: compone texto, ejecuta el mismo `/novela` y enseña lo que el harness escribe.

| Puede | No puede |
|---|---|
| Escribir `encargos/<slug>/` (idea, `entrevista-previa.md`, `decision.md`, `sesion.json`) | Escribir, borrar o mover nada en `novelas/` |
| Lanzar `/novela nueva … precarga:` y `/novela continuar` | Invocar un agente |
| Enseñar lo que el harness pregunta y mandar la respuesta | Contestar o aprobar por el usuario |
| Leer artefactos para pintar progreso | Calcular métricas, elegir intento, recalcular veredicto |
| Relanzar solo tras `PAUSA_PROGRAMADA` | Relanzar tras otra parada sin que el usuario lo pida |

- **`encargos/`** existe porque `novelas/` es del harness en exclusiva y el hook no distingue quién escribe `[harness+hook · ambos]`.
- **Entrevista precargada**: el formulario precarga el grilling, que sigue; `entrevista.md` sale con `origen: formulario+grilling`. Es un camino nuevo en `entrevistar`, distinto de `entrevista:` que cierra `[harness · ambos]`.
- **`ESPERA_APROBACION`**: sin nadie en la sesión, biblia y escaleta se escriben sin marca y el harness para; el estudio pinta, el usuario decide, `decision.md` en `encargos/<slug>/`, `/novela continuar` retoma `proponer_escaleta` sin rehacer la propuesta `[harness · ambos]`. Igual para la cáscara.
- **Cómo lanza el harness**: `harness.mjs` ejecuta `claude --print --input-format stream-json --output-format stream-json --verbose --permission-prompts none --disallowed-tools AskUserQuestion [--resume <id>]`, guarda el `session_id` en `sesion.json`, y traduce intenciones (`empezar`, `responder`, `continuar`) a comandos. Nunca `bypassPermissions` `[cáscara · CC en el binario; el protocolo es ambos, §10.3]`.
- **Qué cuesta `--permission-prompts none`**: en esa sesión no hay a quién preguntar, así que toda herramienta fuera del `allow` se deniega sola. Con `Bash` la lista no basta: un bucle, una expansión `$var` o una tubería piden aprobación **aunque cada parte esté permitida**, y un prefijo no puede cubrirlas. Denegar no rompe la ejecución —el harness sigue por `Read`/`Grep`— pero deja en el estudio un aviso técnico que el usuario no puede accionar. Por eso el orquestador lee con herramientas y reserva `Bash` para los literales de la lista (`SKILL.md` §9) `[harness · ambos]`.
- **Qué no cambia**: la etapa 2 sin intervención humana; ningún botón de reescribir, aprobar intento o cambiar biblia.
- Congelar el estudio hasta la prueba de punta a punta: → A18.

### 9.5 El bucle de optimización de prompts

**Estado a 2026-09-18: diseñado y no ejecutado.** Es el «circuito previsto» que §9.3.1 dejaba sin diseñar: Langfuse es el laboratorio y un prompt calibrado **asciende** a producción. Nace de E5(c) —el sistema se corrige a sí mismo los exámenes— y su única razón de ser es romper ese lazo.

**Mismo estatus que el visor (§9.2) y la observabilidad (§9.3): fuera del harness, borrable, nunca dentro de `/novela`.** Se invoca a mano con `/optimizar`. No lee ni escribe `novelas/`. Decide qué prompt usará un agente **la próxima vez**, no si un capítulo se aprueba: por eso las seis reglas de §9.3 siguen en pie sin excepción, y en particular la 2 —Langfuse nunca es puerta del flujo—, porque el prompt de producción se sirve de `.claude/agents/`, no de Langfuse.

**Tres papeles, y no se mezclan** `[harness · ambos]`:

| Papel | Quién | Qué hace |
|---|---|---|
| Optimizado | el agente cuyo prompt cambia | nada: se le ejecuta |
| Juez | evaluador de `herramientas/evaluadores/` + conjunto etiquetado | puntúa contra verdad de campo; no opina |
| Optimizador | agente `optimizador` | propone variantes; **nunca** puntúa, y **nunca ve el conjunto etiquetado** |

Que el optimizador no vea el conjunto no es prosa, pero tampoco lo daba el `deny` a solas: `permissions.deny` corta `Read` sobre la carpeta del conjunto, y `.claude/hooks/rutas-protegidas.sh` (`PreToolUse` sobre `Bash`, falla en cerrado) corta `cat`, `head` y las redirecciones, que el `deny` **no** cubría `[cáscara · ambos]`. Las dos capas tienen fixtures en `herramientas/pruebas/hook.sh`. Ninguna de las dos es un sandbox contra una ruta ofuscada: el aislamiento que de verdad sostiene el bucle es que el orquestador nunca pone el conjunto en el prompt del optimizador.

#### 9.5.1 TRIGGER

`/optimizar <agente> --metrica <score> --vueltas N [--tope-invocaciones M]`. Manual, nunca dentro de `/novela`, nunca automático.

Cinco requisitos. Si falta uno, el bucle **no arranca** y dice cuál, antes de gastar una invocación `[harness+guion · ambos]`:

| # | Requisito | Cómo se comprueba |
|---|---|---|
| 1 | Conjunto etiquetado con **≥ 30 defectos puntuables para ese agente**, repartidos en **casos**, y `split` por caso (≈ 2/3 búsqueda, 1/3 control) escrito en el propio fichero y versionado en git | `preparar.py --comprobar` |
| 2 | La métrica existe en `herramientas/evaluadores/` y su exactitud contra el conjunto está medida y escrita | `calibracion.md` del evaluador |
| 3 | El prompt vive en `.claude/agents/<agente>.md` y el árbol de git está limpio | `git status --porcelain` |
| 4 | Modelo del juez distinto del optimizado. **N/A si la métrica es de código** | tipo del evaluador |
| 5 | Presupuesto declarado: tope de vueltas y tope de invocaciones | argumentos |

**Dos unidades, y no se confunden.** Un **caso** es una invocación del agente sobre un capítulo; un **defecto** es una etiqueta dentro de un caso. El recall se calcula sobre defectos, pero el `split` se fija **por caso**: si dos defectos del mismo capítulo cayeran en lados distintos, el optimizador habría visto en búsqueda el mismo texto con el que se decide en control, y el control dejaría de ser independiente. El reparto 20/10 es la proporción objetivo de defectos, no un recuento de casos.

**«Defectos puntuables para ese agente» y no «defectos»**: cada revisor solo emite sus gravedades (§5.6), así que un defecto de gravedad 1 no puede contar contra el revisor de encargo. El conjunto guarda los treinta y la puntuación filtra por contrato. Con el conjunto de E5, los puntuables para `revisor-encargo` son **1 de 30** (A7, título huérfano) y el requisito 1 falla: es el comportamiento correcto, no un fallo del bucle.

**El tope es de invocaciones, no de dinero** `[harness · CC]`. En el hito 1 la herramienta `Agent` no devuelve tokens de subagente (§9.3), así que un tope en dólares no es comprobable. En el hito 2 sí, porque la cáscara devuelve `coste_usd` (§10.2), y entonces el tope pasa a ser de coste.

#### 9.5.2 GOAL

**Un objetivo por ejecución, con restricciones.** Nunca varios objetivos: con dos, cualquier resultado es defendible.

```
maximizar   recall_revisor   del agente revisor-encargo
sujeto a    cita_verificable >= 0,90
            palabras_prompt  <= 1,3 x línea base
```

Cada restricción tapa un camino barato: sin la primera, subir el recall se consigue inventando problemas; sin la segunda, con un prompt de tres mil palabras. **Se miden palabras (`wc -w`) y no tokens**, porque el harness no tiene tokenizador; es una aproximación declarada, no un descuido.

**Vuelta 0 obligatoria.** Antes de la primera variante se mide el prompt de producción sobre los dos splits. Sin línea base, «mejora ≥ 0,10» no tiene contra qué medirse.

#### 9.5.3 VERIFY

| Regla | Por qué |
|---|---|
| La decisión de aceptar se toma **siempre** en control; búsqueda solo alimenta al optimizador | Un prompt ajustado a los casos que vio no ha mejorado: los ha memorizado |
| Se acepta si control mejora **≥ 0,10** absoluto sobre la mejor aceptada hasta ahora | Con 10 ítems, 0,05 es un ítem: es ruido |
| El juez se congela toda la ejecución: ni el evaluador ni el conjunto ni el split cambian | Cambiarlo a mitad hace incomparables las vueltas anteriores |
| Cada vuelta deja un experiment run en Langfuse, y antes una línea en `vueltas.jsonl` | Para ver la curva y abrir el caso concreto que falló |

**La puntuación se calcula en local y después se publica** `[harness+guion · ambos]`. `puntuar.py` importa el emparejamiento de `herramientas/evaluadores/<metrica>.py` —una sola fuente de verdad para esa lógica— y escribe el resultado en disco; la subida a Langfuse es posterior y **fail-open**: si Langfuse no responde, el bucle sigue y solo se pierde la curva. Es la regla 3 de §9.3 aplicada aquí.

**Control se consulta en todas las vueltas** (decisión del usuario, 2026-09-18). Limitación conocida y aceptada: con 10 ítems y hasta 10 consultas, la variante ganadora puede estar ajustada a esos 10 casos. El informe de cierre lo declara siempre, con el número de consultas gastadas.

**La «segunda semilla» no está**: los revisores corren a `temperatura: 0.0` (§7.3) y repetir a temperatura 0 no es una muestra independiente. La regla queda en el umbral solo.

#### 9.5.4 STOP

Dos paradas, que dejan resultado:

1. `recall_revisor >= 0,80` en control → la versión se marca `candidato`.
2. N vueltas hechas → devuelve la mejor probada.

Tres abortos, que **no** son lo mismo:

- tope de invocaciones agotado;
- 3 vueltas seguidas sin mejora en control;
- una variante incumple una restricción dura o rompe el formato de salida.

**Nada se promueve solo** `[harness · ambos]`. El bucle deja un `candidato` y un informe; mover el prompt a producción es un commit que hace el usuario.

**Invariante de restauración** `[harness+guion · ambos]`: el bucle instala cada variante copiando sobre `.claude/agents/<agente>.md` y **restaura siempre** el original, también al abortar y también si falla. Al arrancar guarda `produccion.md` con su hash; al terminar comprueba que el fichero del repositorio vuelve a tener ese hash y lo escribe en el informe. Si no coincide, es PARADA y lo dice: un repositorio con una variante instalada generaría novelas con un prompt que nadie aprobó.

#### 9.5.5 MEMORY

**Una operación por vuelta**, de una taxonomía cerrada, para saber qué causó el cambio:

| # | Operación |
|---|---|
| 1 | añadir un criterio nuevo, con definición y un ejemplo |
| 2 | convertir una instrucción vaga en procedimiento enumerado |
| 3 | añadir una regla de exclusión: qué **no** cuenta |
| 4 | endurecer el formato de salida (campo obligatorio, cita obligatoria) |
| 5 | borrar una instrucción que no se activó en ningún caso |

Prohibido, y **comprobado por `comprobar_variante.py` antes de instalar**, no confiado al modelo `[harness+guion · ambos]`:

| Prohibición | Por qué | Comprobación |
|---|---|---|
| Copiar citas del conjunto en el prompt | Es memorizar el examen | `grep -F` de cada cita del conjunto sobre la variante |
| Nombrar la métrica o el evaluador | Si el agente sabe cómo lo puntúan, optimiza al juez | `grep -iE` de los nombres de score |
| Cambiar el rol o la pregunta del agente | Es cambio de contrato, y lo decide el usuario | frontmatter idéntico + frase de contrato literal |
| Romper el esquema JSON de §5.6 | El harness no sabría leer el informe | tres claves y gravedades del contrato presentes |
| Tocar cualquier otro fichero | Un bucle que edita a un tercero deja de ser comparable | `git status --porcelain` acotado a un solo fichero |

Dónde vive cada cosa:

| Qué | Dónde | Marca |
|---|---|---|
| Prompt en producción | `.claude/agents/<agente>.md`, en git | fuente de verdad `[cáscara · ambos]` |
| Variantes y candidatos | `optimizaciones/<agente>-<fecha>/variante-NN.md` y Langfuse Prompt Management, etiqueta `candidato` | archivo `[ninguno · ambos]` |
| Resultado por vuelta | `optimizaciones/<agente>-<fecha>/vueltas.jsonl`: operación, score búsqueda, score control, aceptada, motivo, invocaciones | `[harness+guion · ambos]` |
| Memoria acumulada entre ejecuciones | `optimizaciones/<agente>/lecciones.md`, una línea por variante probada | `[harness · ambos]` |
| Conjunto etiquetado | `herramientas/optimizacion/conjuntos/<nombre>.jsonl`, espejo en Langfuse | `[cáscara · ambos]` |

**Langfuse archiva, git manda.** El candidato se publica en Prompt Management para tener el historial junto a los scores, pero ningún agente lo lee nunca en ejecución: eso convertiría a Langfuse en fuente de verdad y en puerta del flujo, y rompería además §10.1, que porta los contratos byte a byte desde `.claude/agents/`.

**El optimizador lee `lecciones.md` antes de proponer y tiene prohibido repetir una variante ya descartada.** Es lo único que impide que el bucle dé vueltas sobre la misma idea cuando el modelo no recuerda las vueltas anteriores.

#### 9.5.6 Qué es solo del hito 1

| Pieza | Hito 1 | Hito 2 |
|---|---|---|
| Ejecutar una variante | `cp` sobre `.claude/agents/<agente>.md` + herramienta `Agent`, porque `Agent` lee el contrato del disco y no admite un prompt inyectado | La cáscara pasa el system prompt al subagente; no hace falta tocar el repositorio ni restaurar |
| Presupuesto | Tope de invocaciones: no hay tokens de subagente | Tope de coste, con `coste_usd` de §10.2 |
| Todo lo demás | Markdown, JSONL y guiones | Idéntico |

### 9.6 El validador de manuscrito

**Estado a 2026-09-18: implementado y ejecutado.** Puntúa el **texto producido**, no lo que los revisores declararon. Nace del mismo hallazgo que §9.5 pero por el otro lado: E5(c) dice que cuatro de las seis métricas de §8.3 dependen de lo que el revisor declare, y `erratas.md` de la novela B dice `total: 0` sobre el manuscrito donde E5 contó 13 agramaticalidades a mano.

**Mismo estatus que §9.2–§9.5: fuera del harness, borrable, nunca dentro de `/novela`.** Se invoca a mano con `/validar`. Solo lee `novelas/`; escribe en `validaciones/`.

**No es un bucle.** Mide una vez y devuelve un número: no tiene condiciones de parada ni vectores de mejora, y eso es una decisión, no un olvido. Si algún día se itera sobre `config.json` usando esto como juez, ese bucle traerá su propio STOP.

**§8.3 y §9.6 conviven, con nombres distintos** `[harness · ambos]`. §8.3 son métricas de **proceso**, y quedan declaradas como **autoinformadas**: las calcula el harness a partir de lo que los revisores dijeron. §9.6 son métricas de **producto**, medidas sobre el texto. Cada informe dice de dónde sale cada número; cuando discrepen, decide el usuario. Ninguna se retira: §8.3 ve cosas que el texto no muestra (agotamientos, reintentos) y §9.6 ve cosas que ningún revisor declaró.

#### 9.6.1 TRIGGER

`/validar <carpeta> [--congelar-base] [--publicar]`. Manual, nunca automático. Tres precondiciones; si falta una, no mide y dice cuál `[harness+guion · ambos]`:

| # | Requisito | Por qué |
|---|---|---|
| 1 | La carpeta pasa §8.7: `etapa: completa` y `manuscrito.md` | Un manuscrito a medias no se compara con uno entero |
| 2 | El **detector** está congelado: su hash coincide con el de la línea base | Un delta entre dos detectores distintos mide el detector, no el texto |
| 3 | La **escala** está congelada: misma versión de topes y pesos | Ídem |

#### 9.6.2 GOAL

Un número **reproducible** sobre el texto. Dos dimensiones, ambas por mil palabras —los manuscritos miden 8.145 y 6.391 palabras y sin normalizar el más largo saldría penalizado por serlo—, ambas normalizadas a 0–1 con 1 = mejor, más un índice global ponderado:

| Dimensión | Qué cuenta | Tope 0,0 | Peso |
|---|---|---:|---:|
| `lengua` | Aciertos del detector de agramaticalidades | 2,0 /mil | 0,87 |
| `repeticion` | 6-gramas compartidos entre pares de capítulos | 16,0 /mil | 0,13 |

**Ni los pesos ni los topes son intuición.** Los pesos salen del recuento de E5: de los 15 defectos que caen en estas dos dimensiones, 13 son de lengua y 2 de cohesión. Los topes salen de la regla «el doble de la peor tasa observada vale 0,0», aplicada a las tasas que midió el propio guion. Todo declarado con su dato en `herramientas/validacion/escala.json`. Con dos manuscritos la regla de topes es débil y se revisa con el tercero.

#### 9.6.3 VERIFY

Delta contra una **línea base congelada** en `validaciones/_base.json`. Eje declarado por ejecución; todo lo demás igual.

La medición es determinista: re-puntuar el mismo manuscrito da el mismo número. **El ruido no está en la medición, está en la generación.** Con `n=1` por configuración no se puede separar el efecto de la config del azar de esa generación, así que el informe lo escribe siempre y **ninguna mejora se declara establecida** `[harness · ambos]`.

#### 9.6.4 STOP — no aplica

No itera. Declarado aquí para que no se rellene por inercia.

#### 9.6.5 MEMORY

No hay vectores de mejora, por lo mismo. Lo que sí hay son reglas y sitio:

| Regla | Cómo se impone |
|---|---|
| Ningún patrón puede llevar dentro **tres palabras seguidas** de una cita del etiquetado | `comprobar_patrones.py`, sale 1. Una palabra suelta del léxico sí vale: es miembro de la clase, no la instancia |
| Cada clase viaja con ejemplos **positivos y negativos inventados**, que no están en ningún manuscrito | Ídem: el patrón debe casar los positivos y respetar los negativos |
| Cambiar `patrones.py` o `escala.json` obliga a re-puntuar la línea base | El hash y la versión viajan en cada resultado; la precondición 2 y 3 lo cortan |

Es la misma regla que §9.5.5 impone al optimizador —quien escribe el examen no copia las respuestas— y la misma que §9.5.3 impone al juez: congelado durante toda la comparación.

**Dónde vive**: `herramientas/validacion/` (detector, escala, calibración, etiquetado) y `validaciones/<slug>/` (`score.json`, `informe.md`), versionado en git. Publicación en Langfuse posterior y **fail-open**.

#### 9.6.6 Alcance declarado de la v1

| Medida | Valor | Qué significa |
|---|---:|---|
| Precisión | **1,000** | De lo que marca, todo es un error real: 6 de 6 |
| Recall | **0,462** | De los 13 defectos etiquetados, ve 6 |
| Recall sobre el techo | **1,000** | De los 6 que alguna clase del v1 puede expresar, los ve todos |

Los 7 que no ve están declarados uno a uno en el etiquetado: tres son palabras inexistentes (exigen un léxico), dos son tiempo verbal y uno concordancia compleja (exigen análisis morfosintáctico), uno es laísmo idiomático. Subir ese recall exige spaCy o language-tool, y eso ata la línea base a una versión externa que al actualizarse cambiaría los números.

**Fuera de la v1**: las clases A, B y C de E5 —coherencia interna, verosimilitud técnica, mundo post-IA, 13 de los 30 defectos— porque no son contables y exigen un juez LLM independiente, que hoy no existe (`openrouter/free` no garantiza qué modelo contesta → A14).

#### 9.6.7 Primera medición (2026-09-18)

| | Lengua | Repetición | Global |
|---|---:|---:|---:|
| **A** (opus, 8.145 palabras) — línea base | 0,00 /mil → 1,000 | 8,10 /mil → 0,494 | **0,934** |
| **B** (haiku, 6.391 palabras) | 0,94 /mil → 0,531 | 2,82 /mil → 0,824 | **0,569** |
| Delta | −0,469 | **+0,330** | −0,365 |

Dos lecturas que ninguna métrica anterior daba. La primera: **la novela de opus pierde en repetición**, y por bastante; sus capítulos 3 y 4 comparten muchas secuencias literales. §8.3 le da CUMPLE y no lo ve. La segunda: el delta global de −0,365 **no autoriza a decir «haiku escribe peor»**, con n=1 y sin poder separar config de azar; autoriza a decir que esta novela de haiku puntuó 0,365 menos que esta novela de opus.

---

## Evidencia (E1–E7)

Cada regla de [functional.md](functional.md) que nació de un dato apunta aquí con `E-n`. **Esta parte no manda sobre nada.**

Fuentes: `novelas/tecnica-ascensores-peticion-ia/` (A, opus, spec v3), `novelas/tecnica-ascensores-peticion-ia-20260916-1719/` (B, haiku, spec v4), sus `registro.md`, los análisis de traza del 09-16 y del 09-17, `comparativa/caso-01-opus-vs-haiku/`, la revisión de ingeniería del 09-17 y el CHANGELOG 0.8.1 (en `git show HEAD:CHANGELOG.md`).

| E | Qué | Fecha | Reglas que motivó |
|---|---|---|---|
| E1 | La ejecución de referencia (opus) | 2026-09-16 | §2, §4.1 canon, §4.2 ajustes de longitud, mejor intento, revisión partida, §7.7 |
| E2 | Diagnóstico de volumen | 2026-09-17 | §4.2 hoja de continuidad y tope del resumen, §7.5, §7.6 |
| E3 | La ejecución con haiku | 2026-09-17 | §1.2 limitación, §5 tolerancia de formato, §6.1, §6.6, §8.3 signo |
| E4 | Comparativa caso-01 (A frente a B) | 2026-09-18 | §7.3, §7.7 limitación, §8.3 regla vacía, §5.4–5.5 fallos |
| E5 | La matriz de criterios no cubre los defectos reales | 2026-09-17 | §5 modos de fallo, §9.3.1 evaluadores |
| E6 | Estado de la observabilidad | 2026-09-17 | §9.3 |
| E7 | Revisión del repositorio: hook, deriva, duplicación | 2026-09-17 | §3.1, marcas `pendiente` |

---

<a id="e1"></a>
## E1 — La ejecución de referencia (A, opus)

`novelas/tecnica-ascensores-peticion-ia/`, 2026-09-16 10:38 → 14:21, perfil `relato`, 5 capítulos, un arco, los agentes en `opus`, spec v3 (revisor único, sin ajustes de longitud, umbrales viejos).

**Qué funcionó.** 37 invocaciones (38 en la traza: una fila `en curso` duplicada), **cero** fallos técnicos, **cero** incumplimientos de contrato, **cero** discrepancias de veredicto. Novela completa, 8.271 palabras, revisión global sobre el texto entero.

**Qué falló: las reglas de flujo, no los agentes.**

| Qué pasó | Por qué | Regla que salió |
|---|---|---|
| Cap. 3 cerrado con una contradicción de cronología («dos semanas» cuando habían pasado seis días) que el revisor había señalado | Sus dos reescrituras se gastaron en rechazos por longitud (1.940 y 1.879 palabras: 140 y 79 sobre el techo). Cada reescritura añade texto y el margen no da de sí | §4.2 ajustes de longitud con presupuesto propio; suelo y techo en palabras absolutas en el prompt |
| Cap. 5 cerrado con el intento 2, que dejaba abierto «Reme y el vecindario» (la escaleta mandaba cerrarlo), descartando el intento 3 que lo cerraba, tenía los cinco sucesos y acertaba una fecha que el 2 erraba | Empatados a un grave, desempató «menos problemas en total» (1 frente a 2). Esa regla premia al texto que hace menos | §4.2 mejor intento por cierres de escaleta antes que por recuento. Produjo solo `hilos_sin_cerrar: 1` y uno de los graves del global |
| La revisión global encontró 4 problemas de gravedad 1 (5 según la traza) que ninguna revisión de capítulo vio; tres, contradicciones a distancia | El revisor único recibía ~19.000 palabras para un capítulo de 1.700 con cinco criterios | §2, §5.4–5.5 revisión partida en dos agentes |
| Dos incoherencias venían de la biblia: una llave entregada en 2011 a quien lleva 26 años de oficio con 52 años en 2049; un ascensor con menos paradas que plantas | El interrogador no las fijó; ningún revisor de capítulo puede verlas porque la biblia es su vara de medir | §4.1 canon explícito y validación en modo `canon` |
| Dos fechas atadas a un día de la semana equivocado | Un modelo no calcula días de la semana con fiabilidad | §4.1 regla derivada |

**Capítulo a capítulo.** Intentos 2 · 2 · 3 · 3 · 3 = 13. Los cinco intentos nº 1 recibieron **exactamente 3 problemas**; los aprobados, 0–1 leves. Caps. 3 y 5 por agotamiento. Minutos: 17 · 20 · 17 · 33 · 44, creciendo con el contexto, no con la longitud.

**Longitud.** 13 mediciones, objetivo 1.500: media 1.657, **+10,5 %**, 11 de 13 por encima, dos sobre el techo. La métrica absoluta (9,3 %) lo escondía → §8.3 con signo.

**Métricas: 0 de 5** con los umbrales viejos (`graves_por_10` 8,0 ≤ 1; agotamiento 40 % ≤ 10; hilos 1 ≤ 0; primer intento 0 % ≥ 60; voz 15,4 % ≤ 10). Tres umbrales eran inalcanzables por construcción a 5 capítulos (un grave = 2,0 puntos; un agotamiento = 20 puntos) → §7.7 recalibrado a 2 · 20 · 0 · 40 · 20.

**Volumen.** 403.727 palabras de entrada, 77.066 de salida (traza: 412.877; el registro manda). **49,6 palabras leídas por palabra publicada.** Revisor 38 % de la entrada, escritor 45 %. Ni un token: `Agent` no los devuelve.

**Fugas de integridad.** `estado.json` se desincronizó y hubo que recontar desde `registro.md` al cerrar; un `paso_descartado` al reanudar se llevó un `intento-1.md` de 1.333 palabras (**resuelto el 2026-09-19**: `descartar()` ahora copia a `.descartado/` antes de borrar, functional §6.2; cierra A21).

---

<a id="e2"></a>
## E2 — Diagnóstico de volumen (A releída con la traza)

Pregunta: de las 403.727 palabras de entrada, cuáles sobraban.

**1. El 58,4 % se gastó en reintentos.** Primeros intentos 143.664; reintentos **235.763**; interrogatorio y global 24.300.

**2. El umbral de veredicto no es la causa.** Reprocesados los 13 informes con tres reglas (`rechaza_con_graves: 1`, `graves ≥ 2`, y gravedad 1 separada de la 2): aprobados al primer intento **0 de 5 con las tres**. Los cinco primeros intentos traían al menos una gravedad 1. Donde sí ahorra separar 1 de 2: el tercer intento del cap. 5, rechazado por una sola gravedad 2, costó **43.625 palabras (10,8 %)**. `graves ≥ 2` ahorraría además el tercero del cap. 4 (38.190) dando por bueno un intento que contradecía el libro de estado → descartado (§7.5).

**3. La causa real es mecánica.** De 9 problemas de gravedad 1, **7** son aritmética temporal o estado de un objeto:

| Clase | Casos | Ejemplo |
|---|---:|---|
| Fechas, edades, plazos | 5 | «desde el noventa y ocho» contra 52 años en 2049; «dos semanas» por seis días; resina atornillada antes de sus 36 horas |
| Estado de un objeto | 2 | Altavoz sonando con el fusible sin reponer; cuadro operado sin la llave, que tenía otra persona |
| Regla del mundo | 1 | Registro de trabajo dentro de una red que la biblia dice que no lo tiene |
| Trama | 1 | |

Todos estaban en el contexto (libro de estado, resúmenes), diluidos en 17.000 palabras → §4.2 hoja de continuidad. Descartado decírselo al escritor en el prompt (ya lo hace implícitamente y no bastó con opus) y un agente «continuista» (una invocación más para algo que no requiere juicio).

**4. El resumen no resume.** Media **1.785 palabras para capítulos de 1.629 (110 %)**, porque el contrato viejo pedía al resumidor lo mismo que al libro de estado. En el cap. 5 el escritor leyó 16.875 palabras: resúmenes 7.373 (**crece sin tope**), libro de estado 3.138, biblia+escaletas 4.378, capítulo anterior 1.612.

**5. Proyección** (solo el término que crece), entrada del escritor por invocación:

| Capítulo | Resumen como estaba | Resumen a 350 |
|---|---:|---:|
| 5 | 16.306 | 10.366 (−36 %) |
| 12 | 28.801 | 12.466 (−57 %) |
| 30 | 60.931 | 17.866 (−71 %) |
| 200 | 364.381 | 68.866 (−81 %) |

`saga` era inviable por el contrato del resumidor, no por el modelo → §7.6 `resumen_max_palabras`, `resumenes_completos_ultimos` por perfil, aviso de proyección. Descartado recortar la ventana (tira capítulos enteros para un problema de redundancia) y digestos por arco (una pieza de memoria más; con 350 palabras, 200 capítulos caben en 70.000).

**6. La entrada por invocación se multiplicó por 3,7** en cinco capítulos (4.594 → 16.875) con `resumenes_completos_ultimos: null`. La nota de `config.json` que lo avisaba no impidió nada → mecanismo, no nota.

---

<a id="e3"></a>
## E3 — La ejecución con haiku (B)

`novelas/tecnica-ascensores-peticion-ia-20260916-1719/`, 2026-09-16 17:19 → 2026-09-17 11:58, **dos sesiones** (reanudación en el cap. 4), `relato`, los cinco agentes en `haiku`, spec v4. Traza Langfuse `a64d7a26…`, 125 observaciones.

**Cambiaron dos variables a la vez**: las correcciones de flujo (E1) y el modelo. Casi todo lo que mejoró se explica por la segunda.

**Capítulo a capítulo.** Intentos 3 · 2 · 1 · 1 · 2 = 9. Ningún agotamiento. **Un solo intento rechazado por contenido** en toda la novela (cap. 1, int. 2, una gravedad 1 de continuidad que encargo no vio: la única `discrepancia_veredicto`). Los otros tres rechazos, por longitud, los tres **por defecto** (1.012, 980, 821). Interrogatorio: 39 minutos y 6 de 41 invocaciones (2 rechazos de canon buenos, 3 reintentos de contrato); a un rechazo de abortar.

**1. La puerta de veredicto no se abrió: se desactivó.** 6 revisiones de contenido → 1 problema. Global sobre 6.426 palabras → 0 problemas, 4 observaciones. Con opus, cinco intentos nº 1 con 3 problemas cada uno y 5 graves en la global. `graves_por_10 = 0,0` mide al revisor, no al manuscrito. El propio informe global de B describe un hueco real (fotos que nadie tomó) y lo clasifica como observación «porque no contradice el canon». **Invalida** recalibrar umbrales con estos datos y hace que el plan del análisis anterior (reprocesar informes de A) no se pueda comparar con B.

**2. El sesgo de longitud se invirtió con el modelo.** haiku: media 1.159, **−22,7 %**, **9 de 9 por debajo**, 3 bajo el suelo; aprobados 1.223–1.398, media 1.278 (−14,8 %). opus: +10,5 %, 11 de 13 por encima. Mismo prompt. La corrección `objetivo × (1 − sesgo)` habría pedido 1.350 a un escritor que entrega 1.159: tres rechazos se habrían convertido en cinco. Retirada (→ A11). El sesgo es del modelo.

**3. Modo de fallo nuevo: 7 reintentos técnicos en 41 invocaciones (17 %)**, 0 en 37 con opus. Interrogador 3 (2 sin bloques, 1 arcos duplicados), escritor 3 (2 sin bloques, 1 sin `=== FIN ===`), resumidor 1. Cinco de siete: el agente **describe el fichero en vez de emitirlo**. Además, absorbidos sin reintento: JSON en valla de código (2), comilla tras el delimitador, `**` sobrantes. Tolerancia improvisada, no contrato → A8.

**4. Correcciones de E1 ejercitadas.** Ajustes de longitud: 3 de 3, reescrituras intactas. Split de revisores: 6 veces, funciona, produjo la única discrepancia y el harness impuso su recálculo. Mejor intento por cierres: **nunca** (sin agotamiento). «Primero cuentas, después registras»: **falló otra vez**, en el resumidor del cap. 5 (`pal_salida` 3.492 registrado antes de contar; real 2.774).

**5. Contabilidad.** `estado.json` e informe de cierre: 40 invocaciones, revisor-continuidad 9; `registro.md`: **41 y 10**. Falta la revisión global (14.455 palabras de entrada, la invocación más cara, 8,8 % del total). Entrada publicada 149.971; real **164.426**. Salida publicada 34.460; real **33.742** (corrección no propagada). Coste de contexto publicado un 9 % bajo. **25,6 palabras leídas por palabra publicada** (la mitad que A, porque todo es más corto, no por la política de memoria).

**6. Filas `pendiente`.** La herramienta `Agent` devolvió todas las salidas en segundo plano y no expone `run_in_background`; cada invocación ocupó **dos** filas (13 `pendiente` sobre 50). Cualquier consumidor que cuente filas se infla un 22 %. Es un defecto de Claude Code, no del diseño → A9.

**Volumen por agente (recontado):** interrogador 6 / 8.346 / 11.672 · escritor 12 / 56.551 / 10.433 · resumidor 7 / 17.306 / 11.637 · revisor-encargo 6 / 26.837 / — · revisor-continuidad 10 / 55.386 / — · **total 41 / 164.426 / 33.742**.

---

<a id="e4"></a>
## E4 — Comparativa caso-01: A (opus, v3) frente a B (haiku, v4)

`comparativa/caso-01-opus-vs-haiku/`, 2026-09-18. `idea.md` y `entrevista.md` idénticos byte a byte. **No aísla el modelo**: entre A y B cambiaron revisión partida, ajustes de longitud y umbrales; las dos primeras favorecen a B por diseño.

**Métricas (recalculadas).** A: 0 de 5 con sus umbrales. B: **5 de 5** con los suyos, 4 de 5 con los de A (falla primer intento: 40 % frente a 60 %). `b_aguanta: true` **por vacío**: A no cumple ninguna, así que la regla de §8.3 no discrimina → A6.

| | A | B |
|---|---|---|
| Palabras del manuscrito | 8.271 | 6.426 |
| Intentos | 13 | 9 |
| Rechazos por longitud | 2, por exceso | 3, por defecto |
| Incumplimientos de contrato / reintentos técnicos | 0 / 0 | 7 / 7 |
| Rechazos de canon | 0 | 2 |
| Problemas del global | 4 de gravedad 1 + 1 de 2 | **0** |
| Invocaciones (registro) | 37 | 41 |
| Entrada / salida (palabras) | 403.727 / 77.066 | 164.426 / 33.742 |
| Tokens, coste | desconocido | desconocido |

**Lectura.** «A se lee como una novela; B como el resumen de una.» B: tres contradicciones verificables que el revisor de haiku **vio y degradó a observación** (título «La 4ª planta» sin referente; tres días que aparecen de la nada entre el cap. 4 y el 5; fotos que nadie tomó); un suceso de escaleta incumplido aprobado por encargo; el motivo «treinta años» repetido cinco veces; castellano roto no marcado por nadie («la agua», «había fallido», «La conocimiento», «hubiese trovado», «La peso», «sospecha través de datos»); un error de hecho copiado al libro de estado («vecina de cincuenta años» / «cincuenta años en el barrio»). A: canon de la biblia con la tensión de la llave de 2011 (previo al canon explícito); voz de la IA sostenida sin fisura; escenas con dos personas dentro.

**Conclusiones.** (1) Las métricas miden el harness, no la novela: cuatro de seis dependen de lo que el revisor declare. (2) haiku sale barato en volumen (41 % de la entrada de A) y caro en fricción (7 reintentos, 2 rechazos de canon, 4 pasos descartados). (3) La comparación limpia exige relanzar A con la spec v4. **El paso 2 de §7.8 no queda decidido y lo que hay apunta a que no** → A19.

**Cambios propuestos por el caso** (a decidir, consolidación §3): precondición de misma `config.version` y `calidad` + commit del harness en el registro (A7); `b_aguanta` no informativo si A cumple cero (A6); prohibir al revisor de continuidad degradar saltos temporales y objetos no sembrados (A12); título con referente para encargo (A12); aviso asimétrico de longitud según modelo (A11); tolerancia de formato en `invocar.md` (A8); recuento obligatorio desde `registro.md` al cerrar (A10); métrica informativa de lengua (A5).

---

<a id="e5"></a>
## E5 — La matriz de criterios no cubre los defectos reales

Revisión de ingeniería del 2026-09-17 sobre **30 defectos encontrados a mano** en el manuscrito de B. **La lista itemizada no está en el repositorio**; solo esta clasificación (→ A24).

| Clase | n | ¿Qué criterio lo cubre? | ¿Quién lo vio? |
|---|---:|---|---|
| A. Coherencia interna (plazo contradictorio, personaje antes de existir, fotos inexistentes) | 7 | Gravedad 1: **tiene dueño** | Nadie |
| B. Verosimilitud técnica (multímetro que mide «integridad estructural») | 4 | **Ninguno** | — |
| C. Mundo post-IA ausente, anacronismo social | 2 | **Ninguno** | — |
| D. Cohesión estructural (caps. 2 y 3 son la misma escena; motivo repetido) | 2 | **Ninguno** | — |
| E. Erratas y agramaticalidades («la agua», laísmo, «La conocimiento») | 13 | **Ninguno** | — |
| E′. Incoherencias locales | 2 | Gravedad 1 | Nadie |
| A7. Título huérfano | 1 | Gravedad 2 | Nadie |

**Unos 21 de 30 no tienen dueño en ningún contrato.** La palabra «gramática» no aparece en los cinco. `0 problemas` no es solo un fallo de haiku: es la respuesta correcta a las preguntas que se hicieron; opus también habría devuelto 0 en la clase E.

**Corolarios.** (a) La frontera problema/observación no está definida y un modelo pequeño la rellena hacia el lado barato. (b) Nada obliga a que un problema cite texto que existe. (c) **El sistema se corrige a sí mismo los exámenes**: `calcular_metricas` cuenta lo que los revisores declaran y nadie mide a los revisores; 6/6 CUMPLE sobre un manuscrito con 13 agramaticalidades. La pregunta del proyecto no se puede contestar con la instrumentación actual. (d) El ajuste de longitud **fabrica** defectos: cap. 5, 821 → 1.288 palabras, «treinta años» 1 → 3 veces. (e) Con criterios que cubrieran las clases B–E, casi todos los capítulos de B habrían sido rechazados y `reescrituras_max: 2` no habría bastado; es el dato que hoy no se tiene.

Propuestas derivadas, todas abiertas (A4, A5, A28): agente `corrector` (gravedades 6 lengua, 7 verosimilitud), gravedad 8 repetición para encargo, presencia del mundo dentro del criterio 4, `cita` obligatoria verificada con `grep`, reglas inviolables como lista de comprobación por capítulo, y evaluadores en Langfuse (§9.3.1) como fuente de verdad externa cuyo prompt calibrado **asciende** a criterio.

---

<a id="e6"></a>
## E6 — Estado de la observabilidad (2026-09-17 / 18)

**Langfuse**: 59 trazas, 4 de dominio (dos novelas: A por triplicado por `trace_id` no determinista, B una vez) y 55 de sesión (hook `Stop`). Las de sesión no aportan coste ni tokens (`inputPrice`, `outputPrice`, `modelId` a `null` en 1.540 observaciones); sí latencias reales.

**Exportador `herramientas/trazas/exportar.py`**, defectos verificados:

| Defecto | Consecuencia |
|---|---|
| `resultado_invocacion()` busca `"resultado ok"` y el registro escribe `resultado: ok` | `metadata.resultado = "desconocido"` en el 100 % de las generaciones; los filtros de los evaluadores no casan con ninguna |
| `input`/`output` nunca se rellenan | `null` en las 50 generaciones: nada que puntuar |
| Filas `pendiente` emitidas como generaciones | 50 generaciones para 41 invocaciones (+22 %) |
| Fila de corrección exportada como agente | `metadata.agente` = «correccion de la fila anterior…» |
| Todas las observaciones con el instante de la exportación | Latencias 0–0,015 s; Langfuse no ordena ni mide |
| `trace_id` no determinista | Reexportar duplica |
| Sin `encoding="utf-8"` explícito | Mojibake en cuanto un aviso lleve tilde |

**Lectura de vuelta**: `/api/public/traces` y `/observations` responden **410** para organizaciones creadas desde el 16-09-2026; `GET /api/public/v2/observations?…&fields=core,io,metadata` responde 200 (sin `fields`, `input`/`output`/`metadata` **no vienen**); la v2 no devuelve `name` (el agente se lee de `metadata.agente`); retardo de ingesta de ~45 s; límite de 30 peticiones/minuto (una descarga sin backoff se corta a las 600 observaciones en silencio).

**Evaluadores** (`herramientas/evaluadores/`): siete creados, tres reglas `enabled: false`, juez `openrouter/free`. Detalle en functional.md §9.3.1. Ninguno de los arreglos toca el harness (→ A13, A14).

---

<a id="e7"></a>
## E7 — Revisión del repositorio (2026-09-17): hook, deriva, duplicación

**El hook bloqueaba tres pasos que el flujo exige.** `inmutables.sh` decidía por existencia del fichero, y `aprobar()`, el bucle de `proponer_escaleta` y `detallar_arco` reescriben `biblia.md`, `escaleta.md` y `arco-AA.md` a propósito: **ninguna novela nueva podía aprobar su escaleta**. No se vio antes porque el hook es posterior a A. Arreglo (0.8.1): decidir **por aprobación** (frontmatter `aprobada`/`validada`) en esos tres y por existencia en el resto. Verificado a mano contra **28 casos** con código de salida. Descartados: que el interrogador devuelva ya `aprobada: true` (quien aprueba es el usuario, después), borrar antes de reescribir (ventana sin artefacto), extender el hook a Bash (parser nuevo dentro del bucle; queda como limitación conocida).

**Permisos**: `Write(/novelas/**)` y `Write(/comparativa/**)` no se consultan nunca en Claude Code (solo las reglas `Edit(ruta)` y `Read(ruta)` cubren rutas) y provocaban un aviso al arrancar; fuera. `Edit(/novelas/**)` es la que autoriza `Write`: **quitarla rompería el bucle** (consolidación §4). Entran `deny` de `Read(.env)` y `Read(.claude/settings.local.json)`; los cinco subagentes tienen `Read`.

**Deriva spec ↔ implementación.** La spec 0.8.0 declara hoja de continuidad, `resumen_max_palabras`, `hoja_continuidad_max_palabras`, `rechaza_con_gravedad_1/_2`, `resumenes_completos_ultimos` por perfil y `entrada_max_palabras_invocacion`; `config.json` (`version: 4`) no tiene ninguna, `capitulo.md` aplica `rechaza_con_graves` y `plantillas/informe.md` la cita. Los tres son coherentes entre sí; cambiar solo uno dejaría tres ficheros contradiciéndose. Nada lo detectó salvo una lectura manual → marcas `pendiente` en functional.md y A2, A3 (`comprobar.sh`).

**Duplicación.** La regla de inmutabilidad está escrita en cuatro sitios (spec §3.1, CLAUDE.md, SKILL.md §9, cabecera del hook) → A27.

**Lo que aguantó** y conviene no tocar: solo el harness escribe; la carpeta como único estado con git como registro de transacciones (`descartar()` reanudó sin perder nada aprobado); contratos con forma verificable (cero fallos de herramienta en 78 invocaciones entre A y B); ajustes de longitud (3 de 3); revisión partida.
