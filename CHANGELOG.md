# story-maker

Historial de cambios del harness. **Para qué sirve este fichero:** aquí se anota *qué* cambió en el harness y *por qué*, de forma que cualquiera (tú dentro de tres meses, o Claude Code en otra sesión) pueda entender una decisión sin reconstruirla del historial de git ni releer las specs enteras.

Cómo se escribe:

- Una sección `## <versión>` por versión, **de la más reciente a la más antigua**, con versionado semántico: **Major** = cambia el contrato del harness o rompe novelas existentes · **Minor** = capacidad nueva compatible · **Patch** = arreglo o ajuste de redacción.
- Dentro, `### Major Changes` / `### Minor Changes` / `### Patch Changes`.
- Cada entrada: una línea con el **resumen en negrita** y, debajo, viñetas anidadas con el detalle y el motivo. Si hay commit, se cita al principio entre corchetes.
- Las decisiones descartadas también se anotan: saber qué *no* se hizo y por qué evita volver a proponerlo. Pero solo las que alguien volvería a proponer: descartar por escrito una opción que nadie iba a defender es ruido.

Lo que **no** entra aquí:

- Trabajo pendiente. Va en [TODO.md](TODO.md); este fichero cuenta lo ya decidido, no lo que falta.
- Erratas, desincronizaciones entre dos ficheros y ajustes que no protegen ninguna decisión: eso lo cuenta mejor `git log`.
- Constancia de que se siguió una regla del proyecto (glosario actualizado, diagrama redibujado, inventarios de ficheros tocados). La spec es la fuente de verdad; si el término está en §0, está.

---

## 0.8.1

Versión de **revisión del repositorio** (17/09/2026): ninguna ejecución nueva, solo una lectura cruzada de spec, skill, procedimientos, hook y `settings.json` buscando sitios donde dos ficheros digan cosas distintas. Lo que salió: el hook de inmutabilidad **prohíbe tres pasos que los procedimientos exigen**, y por tanto ninguna novela nueva puede aprobar su escaleta. No se vio antes porque el hook es posterior a la ejecución de referencia: la novela de §8.5 se generó sin él.

### Patch Changes

- **Las credenciales dejan de ser legibles para los agentes.** (spec §9.3; `.claude/settings.json`)

  - Entran dos reglas `deny`: `Read(.env)` y `Read(.claude/settings.local.json)`. La regla 5 de CLAUDE.md fijaba **dónde** viven las claves de Langfuse y `.gitignore` impedía publicarlas, pero nada impedía **leerlas**, y los cinco subagentes llevan `tools: Read, Glob, Grep`.
  - Un `deny` de `Read` cubre además `cat`, `head`, `sed` y las redirecciones de Bash sobre esas rutas: no hace falta un hook de Bash aparte para lo mismo.

- **El hook de inmutabilidad decide por la existencia del fichero y debe decidir por su aprobación.** (spec §3.1; `.claude/hooks/inmutables.sh`)

  - Hoy `inmutables.sh` bloquea `Write` sobre `biblia.md`, `escaleta.md` y `arco-AA.md` **cuando el fichero ya existe**. Pero el flujo los escribe dos veces a propósito, y los tres sitios están bloqueados: `aprobar()` (`procedimientos/interrogatorio.md`, paso 1) los reescribe con `aprobada: true` —camino feliz, en todas las novelas—; el bucle de `proponer_escaleta` los reescribe en cada vuelta > 0, que es lo que pasa cuando `validar_canon` devuelve problemas o el usuario pide cambios; y `detallar_arco` (`procedimientos/arco.md`) reescribe `arco-AA.md` con `validada: true` justo después de que `invocar` lo haya creado.
  - Comprobado ejecutando el hook a mano: `Write` sobre un `biblia.md` que ya existe sale con código 2.
  - La spec ya contempla el caso —§3.1 dice «o una por versión, en la biblia y la escaleta antes de aprobarse»—, así que lo que está mal es el hook, no el flujo.
  - Arreglo: para `biblia.md`, `escaleta.md` y `arco-AA.md`, el hook mira el **frontmatter del fichero que ya existe**: con `aprobada: true` o `validada: true` bloquea; sin ellos deja pasar. `intento-*.md`, `libro-estado-*.md`, `informe-arco-*.md` y `manuscrito.md` siguen con la regla de existencia, porque esos sí se escriben una sola vez en la vida. Hay que reescribir antes el párrafo del hook en spec §3.1, que describe la regla vieja.
  - Descartado: **que el interrogador devuelva ya `aprobada: true` y así baste una escritura.** No se puede: quien aprueba es el usuario, después de ver la propuesta (§4.1), así que en el momento de la primera escritura el valor no se conoce.
  - Descartado: **borrar el fichero antes de reescribirlo.** Deja una ventana en la que el artefacto no existe; una interrupción o un `descartar()` ahí pierden la propuesta entera, que es justo lo que el hook existe para evitar.
  - Descartado: **extender el hook a `Bash`.** `cerrar_capitulo` paso 2 copia `libro-estado-K.md` sobre `libro-estado.md`, y filtrar comandos de shell por ruta es un parser nuevo dentro del bucle. Queda como **limitación conocida**: la garantía del hook cubre `Edit` y `Write`, no Bash; el criterio 6 de §8.2 sigue siendo el que la demuestra a posteriori con git.

- **Dos reglas de permisos que Claude Code acepta y nunca consulta.** (`.claude/settings.json`)

  - Fuera `Write(/novelas/**)` y `Write(/comparativa/**)`. Claude Code comprueba las rutas solo contra reglas `Edit(...)` y `Read(...)`; una regla de ruta sobre `Write` se acepta, no se consulta nunca y provoca un aviso al arrancar. `Edit(/novelas/**)` ya cubre la herramienta `Write` sobre esa carpeta.
  - Comprobado de paso que la **barra inicial es correcta** y no hay que tocarla: en un `settings.json` de proyecto, `/novelas/**` ancla en el directorio de trabajo, no en la raíz del disco. Una ruta absoluta necesitaría dos barras.

---

## 0.8.0

Versión salida del **diagnóstico de volumen** de la ejecución de referencia (spec §8.6): la misma novela de la 0.7.0, releída con la traza de Langfuse y los trece informes en la mano para contestar una sola pregunta —de las 403.727 palabras de entrada, cuáles sobraban—. La respuesta: **el 58,4 % se gastó en reintentos**, y la causa no es la que decía §8.5.

### Major Changes

- **El resumen deja de repetir el libro de estado y pasa a tener tope.** (spec §0.2, §4.2, §5.3, §7.6, §8.6; `config.json`)

  - `memoria.resumen_max_palabras` (350) acota el resumen de cada capítulo; el harness lo cuenta con `wc -w` igual que cuenta el capítulo, y el contrato del resumidor (§5.3) reparte de forma estricta: en el **resumen** van los hechos y el frontmatter; el **estado** —personajes, objetos, lugares, datos, reglas— va solo en el libro de estado.
  - Motivo, medido: el resumen pesaba **1.785 palabras de media para capítulos de 1.629**, el 110 % del capítulo que resumía, y suponía el 44 % de lo que leía el escritor en el capítulo 5. La causa era el contrato viejo, que pedía al resumidor exactamente el mismo contenido que al libro de estado: la información se pagaba dos veces y una de las dos copias crecía con cada capítulo. El libro de estado tiene tope (4.000) y la biblia no crece; **el resumen era el único término sin acotar de toda la entrada**.
  - Lo que compra: la entrada por invocación del escritor baja un **36 % a 5 capítulos, un 57 % a 12, un 71 % a 30 y un 81 % a 200**. Dicho al revés: con el resumen como estaba, el capítulo 30 exigiría 60.931 palabras por invocación y el 200 exigiría 364.381. `saga` no era inviable por el modelo, era inviable por el contrato del resumidor.
  - Si el resumidor se pasa del tope, el harness lo reinvoca **una sola vez** con el recuento y el tope en palabras absolutas, y si el segundo también se pasa lo acepta con un aviso. No rechaza el capítulo: el texto no tiene la culpa del tamaño de su resumen, y un bucle de reintentos por esto costaría más de lo que ahorra.
  - Descartado: **recortar la ventana de resúmenes y dejar el resumen como estaba** (`resumenes_completos_ultimos: 3`). Es una línea de configuración y ataca el mismo término, pero tira información de capítulos enteros para arreglar un problema que es de redundancia, no de cantidad. Primero se deja de pagar dos veces lo mismo; si después sigue sin caber, se recorta la ventana.
  - Descartado: **comprimir los resúmenes antiguos con otra invocación** (un digesto por arco). Es lo que ya se descartó en la 0.5.0 por añadir una pieza de memoria más; y con el resumen acotado a 350 palabras, 200 capítulos caben en 70.000 palabras sin comprimir nada.

- **Hoja de continuidad: el harness calcula los datos mecánicos en vez de esperar que el escritor los deduzca.** (spec §0.2, §4.2, §5.2, §5.3, §5.5, §6.1, §7.6)

  - Antes de invocar al escritor y al revisor de continuidad, el harness compone una ficha de como mucho 200 palabras con campos fijos: fecha de ficción del capítulo anterior y del actual y **días transcurridos**, **edad** de cada personaje presente calculada a esa fecha desde el canon, **objetos** con quién los tiene y dónde, **plazos en curso** con su vencimiento, e **hilos que este capítulo debe cerrar**. Va la primera de todas sus entradas.
  - Motivo, medido: de los **nueve problemas de gravedad 1** de la ejecución de referencia, **siete son aritmética temporal o estado de un objeto** —«desde el noventa y ocho» contra los 52 años de la protagonista en 2049; «dos semanas» cuando habían pasado seis días; una resina atornillada antes de cumplir sus 36 horas de fraguado; una voz sonando por un altavoz cuyo fusible nadie repuso; un cuadro de maniobra operado sin la llave, que tenía otra persona—. Ninguno es de estilo ni de criterio, y **todos esos datos estaban ya en el contexto**: en el libro de estado y en los resúmenes, diluidos en 17.000 palabras. Un dato calculado y puesto arriba no es el mismo dato que uno deducible.
  - No lo hace ningún modelo: es copiar campos y restar fechas, como el recuento de palabras. Regla 4 de CLAUDE.md, y por eso se porta al runner sin cambios (regla 7). Si falta el dato, la hoja dice `desconocido`; no se inventa ni se le pregunta a un agente.
  - Obliga a ampliar el frontmatter del resumen con `fecha_ficcion_inicio`, `fecha_ficcion_fin`, `plazos` y `objetos` (objeto, poseedor, ubicación). Es cambio de contrato, de ahí que sea Major: un resumen de la 0.7.x no trae esos campos y la hoja saldría con `desconocido` en casi todo.
  - Es la única de las tres palancas que ataca **la causa** de los reintentos en vez de su precio. Las otras dos abaratan el bucle; esta pretende que no haga falta darlo. Cuánto lo consigue no se sabrá hasta la siguiente ejecución completa: es una hipótesis con una causa medida detrás, no un ahorro demostrado.
  - Descartado: **decírselo al escritor en el prompt** («comprueba las fechas antes de escribir»). Es gratis y es lo que ya hace implícitamente el contrato; la ejecución de referencia demuestra que no basta, con un modelo caro y cinco capítulos. Pedirle a un modelo que haga aritmética sobre 17.000 palabras es exactamente lo que la regla 4 de CLAUDE.md dice que no se haga.
  - Descartado: **un agente «continuista» que prepare la ficha**. Añade una invocación por capítulo y un contrato más para producir algo que no requiere juicio. Si un dato se puede calcular, no se pregunta.

### Minor Changes

- **`veredicto.rechaza_con_graves` se parte en `rechaza_con_gravedad_1` y `rechaza_con_gravedad_2`.** (spec §0.2, §7.5, §8.6; `config.json`)

  - Valores: 1 y 2. Una contradicción rechaza sola, porque entra en el libro de estado y contamina lo que viene detrás; un incumplimiento de escaleta necesita dos, porque el daño se queda en su capítulo y `erratas.md` le da salida.
  - **Corrige el diagnóstico de la nota de análisis, que atribuía al umbral el 0 % de aprobados al primer intento.** Reprocesar los trece informes de la referencia con las tres reglas —la actual, `graves ≥ 2` y esta— da **0 de 5 con todas**: los cinco primeros intentos traían al menos una gravedad 1. Ningún umbral defendible los aprueba, así que el umbral no era la causa de nada.
  - Lo que sí ahorra está al final del ciclo: el tercer intento del capítulo 5, rechazado por una sola gravedad 2 (un hilo cerrado a medias), costó **43.625 palabras, el 10,8 % de la ejecución**. Ese intento no debía haber existido.
  - Descartado: **subir `rechaza_con_graves` a 2**, que era la opción barata. Ahorraría además el tercer intento del capítulo 4 (38.190 palabras), pero dando por bueno un intento cuya gravedad 1 contradecía el libro de estado. Es comprar contexto a cambio de meter una contradicción en la memoria de la novela: exactamente el gasto que la 0.7.0 intentaba evitar.

- **`resumenes_completos_ultimos` se muda dentro de cada perfil y la entrada proyectada se comprueba al arrancar.** (spec §7.1, §7.6; `config.json`)

  - Valores por perfil: `null` en `relato` y `novela_corta`, 10 en `novela` y `saga`. Y `limites.entrada_max_palabras_invocacion` (25.000): `comprobar_entorno` proyecta la entrada del **último** capítulo del perfil —bloque fijo + libro de estado + (N−1) × `resumen_max_palabras` + capítulo anterior— y **avisa** si lo supera.
  - Motivo: el aviso ya estaba escrito, pero como comentario dentro de `config.json`, y no impidió nada. La referencia corrió con `null` y la entrada por invocación del escritor pasó de 4.594 palabras en el capítulo 1 a 16.875 en el 5: por 3,7 en cinco capítulos. Una nota no es un mecanismo.
  - Avisa, no para. La decisión de gastar sigue siendo del usuario; lo que cambia es que deja de tomarse a ciegas.

- **La desviación de longitud se publica también con signo.** (spec §8.3, §8.6)

  - La métrica en valor absoluto daba 9,3 % y parecía ruido. Con signo son **+10,5 %, con 11 de 13 intentos por encima del objetivo** y dos muertos por pasarse del techo: un sesgo en una sola dirección, que es lo único accionable de ese número.
  - Descartado **por ahora**: pedir al escritor el objetivo corregido por el sesgo (`objetivo × (1 − sesgo)`). Probablemente funcione, y la aritmética dice que con 1.350 pedidos la media caería a ~1.490; pero calibrar una constante que se realimenta al prompt con **una sola ejecución** es ajustar a un punto. Se publica el signo ahora y se decide con la segunda ejecución.

### Patch Changes

- **§8.6 nueva: el diagnóstico de volumen completo**, con las tablas de dónde se va la entrada, la clasificación de las nueve gravedades 1 y la proyección a 12, 30 y 200 capítulos. Cierra explícitamente lo que corrige de §8.5.
- **Criterios de aceptación 16, 17 y 18** (§8.2): hoja de continuidad verificable campo a campo contra sus fuentes; tope del resumen con reinvocación única y sin bucle; aviso de proyección de entrada que no para la ejecución.
---

## 0.7.3

### Patch Changes

- **El README de `herramientas/trazas/` documenta cómo se leen las trazas ahora que la API legada devuelve 410.** (`herramientas/trazas/README.md`)

  - Langfuse retira `/api/public/traces` y `/api/public/observations` para las organizaciones creadas a partir del 16-09-2026; esta es una de ellas. Comprobado el 2026-09-17: las dos responden **410 `LEGACY_API_UNAVAILABLE_FOR_NEW_ORGANIZATION`** y `/api/public/v2/observations` responde 200.
  - El sustituto se documenta con el parámetro que de verdad importa: **`fields=core,io,metadata`**. Sin él la respuesta omite las claves `input`, `output` y `metadata` —no las devuelve a `null`, no las devuelve—, que es donde va todo lo que esta herramienta sube. El síntoma es una traza aparentemente vacía, y se diagnostica como «no se exportó nada» en vez de como «faltó un parámetro»: por eso merece estar escrito y no solo vivido.
  - El hallazgo venía de la nota de método de `analisis-traza-2026-09-16.md`, que ya pedía anotarlo. Estaba en el informe de una ejecución, que nadie relee; ahora está donde lo busca quien va a usar la herramienta.
  - No toca `exportar.py`: la herramienta solo **escribe**, y por el SDK, así que el 410 no la afecta. Lo que queda roto es cualquier lectura de vuelta, que es la que haría falta para un `--verificar`. Ese `--verificar` sigue sin existir y no se añade aquí.
  - No toca el harness ni entra en el bucle: regla 5 de CLAUDE.md y §9.3 de la spec siguen valiendo tal cual. Es documentación de una herramienta de solo lectura que vive fuera.
  - Descartado: **escribir el detalle en la spec**. §9.3 fija el contrato de la observabilidad, no la forma concreta de una API de terceros que cambia sola; si mañana Langfuse retira también la v2, la spec no debería enterarse.

---

## 0.7.2

Cuatro huecos entre lo que las reglas dicen y lo que de verdad pasaría al ejecutarlas, encontrados revisando la orquestación. Ninguno se vio en la ejecución de referencia porque los tres primeros solo se manifiestan en condiciones que no se dieron.

### Major Changes

- **Toda invocación de agente lleva `run_in_background = false`, y está escrito.** (`procedimientos/invocar.md`, spec §6.1)

  - La herramienta `Agent` de Claude Code corre en segundo plano **por defecto** y devuelve un identificador en vez de la salida del agente. El paso siguiente de `invocar` es `extraer(resultado, validacion)`: con una invocación en segundo plano no hay nada que extraer, la validación fallaría contra un identificador y el harness lo registraría como incumplimiento de contrato de un agente que en realidad está trabajando. Tres reintentos después, parada.
  - Es el fallo más grave de los cuatro porque es **silencioso y sistemático**: no rompe nada, produce una parada perfectamente formada con el motivo equivocado, y la culpa recae sobre el agente.
  - En la spec entra como responsabilidad del harness, no como detalle de herramienta: «esperar la salida de cada agente antes de seguir». Así el runner del hito 2 hereda el requisito y no la sintaxis.
  - Los dos revisores en paralelo también van con `false`: dos llamadas en un mismo mensaje ya corren a la vez. El paralelismo que hace falta es ese, no el de segundo plano.

- **El hook de inmutabilidad pasa a cubrir `Write`, y se muda a un fichero propio.** (`.claude/hooks/inmutables.sh`, spec §1.3 y §3.1)

  - Antes solo miraba `Edit`, y §3.1 lo asumía a conciencia: la sobreescritura completa se detectaba **después**, con el criterio 6 de §8.2 y git. Pero el riesgo real sobre un artefacto aprobado no es editarlo, es reescribirlo entero, que es justo lo que la regla 2 de CLAUDE.md prohíbe y lo único que el hook no miraba.
  - La regla que impone es una sola y vale para las dos herramientas: **si el artefacto ya existe, no se toca.** `Edit` siempre llega sobre algo que existe, así que siempre bloquea. `Write` bloquea a partir de la segunda vez; la primera es el harness creando el artefacto y debe pasar. Esa condición de existencia es lo que permite cubrir `Write` sin impedir que el harness haga su trabajo.
  - Excepción declarada: `libro-estado.md` (el de la raíz de la novela), que el harness sustituye entero al cerrar cada capítulo. Su `Write` siempre pasa; su `Edit` no, porque nunca se edita en sitio. `libro-estado-K.md` sí es de una sola escritura.
  - Ahora solo actúa **dentro de `novelas/`**. La versión anterior casaba por subcadena y bloqueaba también `plantillas/biblia.md` y `plantillas/escaleta.md`, que son el código fuente del harness y sí se editan.
  - Falla en abierto: si no logra leer la ruta de su entrada, deja pasar. Un hook que bloquea porque no entiende su propia entrada pararía el bucle sin motivo, y el criterio 6 sigue ahí para demostrar la inmutabilidad a posteriori. El hook previene; el criterio demuestra.
  - Se probó contra 18 casos: los seis artefactos, las dos excepciones de `libro-estado`, `registro.md` y `estado.json` (que sí se editan), la plantilla de la skill, rutas de Windows con barras invertidas, JSON con espacios tras los dos puntos, un `Edit` cuyo texto contiene otra clave `file_path`, y entrada vacía.
  - Cuesta una línea de §1.3: el hook deja de ser «de una línea» y pasa a ser un guion de unas cuarenta. Sigue sin ser una pieza del harness y el hito 1 sigue funcionando sin él, que es lo que la excepción de §1.3 protege.
  - Descartado: **dejarlo en una sola línea dentro de `settings.json`**. La comprobación de existencia cabe, pero produce una línea que no se puede leer ni probar por partes; un backstop de seguridad ilegible es peor que uno ausente, porque se confía en él.
  - Descartado: **no tocarlo** y seguir con la detección a posteriori. Es la decisión que §3.1 ya había tomado, y sigue siendo defendible; se cambia porque prevenir sale ahora barato y porque el criterio 6 no se pierde.

### Minor Changes

- **`limites.pausa_cada_capitulos` baja de 5 a 3, y reanudar tras una pausa exige sesión nueva.** (spec §6.2, §6.3, §7.4; `SKILL.md`, `procedimientos/cierre.md`)

  - La pausa no tenía ningún mecanismo que impidiera al orquestador encadenar `continuar` en la misma sesión nada más mostrar el informe. Si lo hace, el paso se gasta sin recuperar contexto y el bucle se queda donde estaba: la pausa se anula a sí misma. Queda prohibido explícitamente en `SKILL.md` y en el paso 6 de `cierre.md`, y es el único motivo de parada con esa condición.
  - La plantilla `informe-cierre.md` cerraba con un **Para continuar** fijo que perdía el «en una sesión nueva» que la tabla de motivos de `cierre.md` sí tenía. El informe es lo único que el usuario lee al final, así que el matiz se perdía justo donde importaba.
  - El 5 baja a 3 por lo medido, no por teoría: en la ejecución de referencia, con `pausa_cada_capitulos` desactivada, la sesión no llegó entera ni al capítulo 2 —hubo que reanudar a mano— así que una pausa cada 5 nunca habría llegado a dispararse. El 3 sigue siendo un número elegido a ojo y se recalibrará con la siguiente ejecución completa.
  - No se toca la config congelada de las novelas ya generadas: `novelas/<slug>/config.json` es inmutable por diseño.

### Patch Changes

- **`Bash(git reset -q HEAD -- novelas/*)` entra en los permisos.** `descartar(carpeta)` de `invocar.md` lo ejecuta, y la lista `allow` tenía `git checkout --` y `git clean -fdq` pero ningún `git reset`. El bucle se paraba a pedir confirmación justo en el peor momento: al reanudar tras un fallo, que es cuando menos se está mirando. `git reset --hard` sigue en `deny`.
---

## 0.7.1

### Minor Changes

- **El visor lleva la identidad de Qaracter.**

  - `frontend/`: los dos colores del logotipo entran como tokens en `src/index.css` —el azul `#233441` pasa a ser la tinta de todo el visor, y el naranja `#ff7932` es el color de marca—, aparece una `BarraMarca` con el logotipo en todas las pantallas, y `public/` guarda los tres recursos derivados del original (logotipo, isotipo y favicon). Reglas de uso en `frontend/CLAUDE.md` › Marca.
  - **El naranja es cromo, nunca estado**: regla de la barra de marca, subrayado de la pestaña activa, barra de progreso, pulso del refresco y foco. Los estados ya tienen verde (aprobado), rojo (rechazado) y ámbar (aviso); meter un cuarto color cálido con significado haría que «en curso», «por agotamiento» y «rechazado» se confundieran de un vistazo, que es justo lo que el visor existe para evitar. Para naranja como texto hay un tono aparte (`--color-marca-fuerte`), el único que llega a contraste AA sobre fondo claro.
  - En la pestaña **Leer** la marca se reduce al isotipo centrado al abrir y al cerrar: el registro de papel manda sobre el de panel, como se decidió en 0.6.0, y ahí no entra cromo naranja.
  - El original (`images/qaracter-logo.png`) vive en la raíz, no dentro de `frontend/`: es el activo de la empresa. Los tres ficheros de `public/` se derivaron de él recortando, quitando el fondo blanco y reduciendo; si el logotipo cambia, se vuelven a derivar en lugar de repintarse.
  - No toca la spec: §9.2 define qué es el visor y qué tiene prohibido, y el aspecto no entra ahí. Tampoco toca el harness: sigue siendo cierto que borrar `frontend/` entera no cambia lo que el harness produce.
  - Descartado: **usar el naranja como color de acento general** (enlaces, pestañas, etiqueta «en curso»). Es más vistoso y era la lectura literal de «poner los colores de la empresa», pero deja tres tonos cálidos compitiendo en la misma tarjeta y baja el contraste del texto de enlace a 2,5:1, por debajo de AA.
  - Descartado: **apuntar `publicDir` a `images/`** para no duplicar el binario. Ahorra un fichero y a cambio publica en la web cualquier cosa que alguien deje en esa carpeta, y obliga a servir el PNG de 2972 px a un `<img>` de 24 px de alto.

---

## 0.7.0

Versión salida entera de la **primera ejecución de referencia completa** (`novelas/tecnica-ascensores-peticion-ia`, perfil `relato`, 5 capítulos, los agentes en `opus`): 37 invocaciones, cero fallos técnicos, cero incumplimientos de contrato y cero discrepancias de veredicto, y una novela terminada con dos capítulos cerrados por agotamiento y las cinco métricas de calidad en NO CUMPLE. Los contratos aguantaron; lo que falló fueron las reglas de flujo y los umbrales. El resultado está documentado en `specs/functional.md` §8.5 y cada cambio de abajo apunta a un fallo concreto de esa ejecución.

### Major Changes

- **La revisión se parte en dos agentes: `revisor-encargo` y `revisor-continuidad`.**

  - Spec §2, §5.4, §5.5, §5.6 y §4.2. El de **encargo** contesta *¿está escrito lo que se pidió?* (criterios 2 y 4: entrada de escaleta, adelantos, voz y tono) y recibe capítulo, escaletas y biblia. El de **continuidad** contesta *¿se contradice algo?* (criterios 1 y 5: biblia, canon, libro de estado, resúmenes, fidelidad del resumen) y se queda además con los modos `canon`, arco y global. El harness une sus dos listas de problemas y aplica la regla de veredicto de §7.5 **sin cambiarla**.
  - Motivo, medido: en la ejecución de referencia el revisor único recibía ~19.000 palabras para juzgar un capítulo de 1.700 con cinco criterios a la vez, y la revisión global encontró al final cuatro problemas de gravedad 1 que ninguna revisión de capítulo había visto, tres de ellos contradicciones a distancia. Partido, cada agente recibe la mitad del contexto y tiene la mitad de los criterios. Con modelos baratos esto pasa de conveniente a necesario: un agente con dos trabajos hace mal los dos.
  - Coste: las invocaciones de revisión se duplican, con la entrada partida por la mitad. En el hito 1 se lanzan en paralelo (dos llamadas en el mismo mensaje) y en el hito 2 concurrentes, así que no cuesta tiempo de reloj. Riesgo asumido y a vigilar: dos revisores encuentran más problemas, luego más rechazos; por eso los arreglos del agotamiento y del mejor intento van en esta misma versión y no después.
  - Cada revisor solo puede emitir sus gravedades (encargo 2 y 4, continuidad 1 y 5). Una gravedad que no le toca es incumplimiento de contrato: así los criterios no se solapan y la unión no puede contar dos veces lo mismo.
  - Descartado: **un solo agente invocado dos veces con modos distintos**. Menos ficheros y un solo contrato que portar, pero obliga al prompt a explicar dos trabajos, que es exactamente lo que confunde a los modelos pequeños, que son el objetivo del proyecto.
  - Descartado: **seguir con un revisor y reforzar su prompt**. Es el cambio más barato y no toca nada, pero no reduce las 19.000 palabras de entrada, que es la causa probable de lo que se le escapó.

- **El mejor intento se decide por los cierres de escaleta, antes que por el recuento de problemas.** (§4.2)

  - Regla nueva: 1) descartar los rechazados por longitud si alguno llegó a los revisores; 2) **cumplir los cierres que la escaleta manda para ese capítulo**, comparando `hilos_cierra` de la escaleta con `hilos_cerrados` del frontmatter del resumen; 3) menos problemas de gravedad 1–2; 4) menos problemas en total; 5) el más reciente.
  - Motivo: el paso «menos problemas en total» premia sistemáticamente al texto que **hace menos**. Un capítulo que omite un suceso obligatorio genera un problema; uno que lo incluye y falla en un detalle genera dos, y ganaba el que lo omitió. En la ejecución de referencia eso cerró el capítulo 5 con el intento 2 —que dejaba abierto el hilo «Reme y el vecindario», que la escaleta mandaba cerrar— descartando el intento 3, que lo cerraba, tenía los cinco sucesos de su entrada y además acertaba el día de la semana de una fecha que el ganador erraba. Ese único desempate produjo por sí solo el `hilos_sin_cerrar: 1` y uno de los cuatro graves del informe global.
  - El paso 2 lo calcula el harness comparando campos, no un modelo (regla 4 de CLAUDE.md), y por eso se porta al runner sin cambios.
  - Cuando decide el paso 4 o el 5 —es decir, sin razón fuerte— queda un aviso en el Estado y en el informe de cierre. Se resuelve, pero se deja por escrito.
  - Descartado: **ordenar estrictamente por gravedad** (menos gravedad 1, luego menos gravedad 2, luego total). Parece la corrección natural y **no arregla el caso**: el intento 2 tenía una gravedad 2 y el 3 una gravedad 1, así que «menos gravedad 1 primero» vuelve a elegir el intento 2. El eje correcto no es la severidad, es lo estructural frente a lo reparable.
  - Descartado: **puntuación por pesos** por gravedad y tipo. Más expresivo, pero exige añadir un campo al JSON de los revisores, y ese contrato es lo que §10.1 porta literalmente al runner. Se puede recuperar si la regla de cinco pasos se queda corta.
  - Descartado: **que el harness pare y pregunte al usuario** ante un empate. Resuelve el caso concreto y rompe «la etapa 2 corre sin intervención humana» (§4.2), que es justo lo que hace posible el bucle desatendido de 200 capítulos del hito 2. Un mecanismo que solo funciona en Claude Code, además, incumple la regla 6 de CLAUDE.md.

- **Un rechazo por longitud ya no consume reescritura: consume un ajuste de longitud.** (§4.2, §6.3, §7.4)

  - `limites.ajustes_longitud` (2 por defecto) es un presupuesto aparte de `reescrituras_max`. El número de intento K sigue avanzando, pero el presupuesto de corrección de contenido no se toca, y el informe de contenido pendiente se vuelve a pasar al escritor junto con el de longitud. Agotados los ajustes, un rechazo por longitud vuelve a consumir reescritura, de modo que el bucle siempre termina.
  - Motivo: un rechazo por longitud no corrige nada. El capítulo 3 de la referencia perdió sus dos reescrituras por pasarse 140 y 79 palabras del techo, y con ellas la corrección de la contradicción de cronología que el revisor había señalado: el texto cerrado fue el intento 1, con el problema dentro. Es estructural, no mala suerte: cada reescritura añade texto para corregir y el margen no da de sí.
  - Además, el prompt del escritor lleva **siempre** el recuento del intento anterior y el suelo y el techo **en palabras absolutas**, no en porcentaje, con la instrucción de que corregir no puede alargar. Durante la ejecución se hizo a mano a partir del capítulo 4 y no volvió a pasar. Un modelo pequeño maneja mucho peor «±20 %» que «entre 1.200 y 1.800».
  - Descartado: **relajar `formato.tolerancia_longitud`**. Haría desaparecer el síntoma, pero la desviación de longitud es una métrica de calidad declarada y subir el margen es maquillar el número, no arreglar nada.

- **La biblia lleva un canon explícito y se valida antes de aprobarla.** (§4.1, §5.1, §5.5)

  - Sección obligatoria **«Cronología y datos fijos»**: año de arranque, edad de cada personaje con su año de referencia, fechas que la trama menciona, geometría del escenario. Y una validación nueva: antes de enseñarle la propuesta al usuario, el revisor de continuidad la revisa en modo `canon` y el harness devuelve los problemas al interrogador, con el mismo mecanismo y el mismo tope (`escaleta_rechazos_max`) que ya existía para los límites de tamaño.
  - Motivo: dos de las incoherencias de la ejecución de referencia no venían de ningún capítulo sino de la biblia —una llave entregada en un año incompatible con la edad y los años de oficio de quien la recibe; un ascensor de menos paradas que plantas tienen los vecinos que lo usan— y **ninguna revisión de capítulo podía verlas**, porque para el revisor la biblia es la vara de medir y no se le ocurre medir la vara. Cada capítulo tropezó con ellas.
  - Por qué explícito y no inferido: con los datos dispersos en prosa, comprobar la coherencia es interpretación; en una tabla, es restar. Y con `haiku` importa el doble, porque el escritor no infiere el canon leyendo la biblia entera, lo consulta.
  - Regla derivada que la biblia debe recoger: si una fecha no está en el canon, el texto no la ata a un día de la semana. Calcular el día de la semana de una fecha no es algo que un modelo haga con fiabilidad, y es una contradicción que la revisión global sí caza (pasó dos veces en la referencia).

- **`config.json` versión 4 y modelos por defecto en `haiku`.** (§7, §7.3)

  - `modelos.revisor` se desdobla en `modelos.revisor_encargo` y `modelos.revisor_continuidad`; aparece `limites.ajustes_longitud`; los umbrales de `calidad` cambian. Los comandos que generan exigen la versión 4; los de solo lectura (`estado`, `verificar`) aceptan también la 3, para poder seguir consultando las novelas ya generadas.
  - Los cinco agentes pasan a `haiku` con el escalado apagado. El paso 1 de §7.8 ya está ejecutado: el caso por defecto pasa a ser el barato, y el caro es el que hay que justificar. Es la tesis del proyecto —un harness lo bastante bueno para que el modelo barato baste— puesta en la configuración.
  - Queda escrito en §7.3 algo que no lo estaba y que confunde: **el orquestador no está en `config.json`**. En el hito 1 es la sesión de Claude Code, y `modelos.*` gobierna solo a los agentes. La recomendación es lanzar `/novela` con el modelo bueno aunque los agentes vayan en `haiku`: el orquestador es prosa interpretada y un error suyo corrompe el estado, mientras que un error de agente lo caza el contrato. La pregunta «¿aguanta el modelo barato?» se contesta de verdad en el hito 2.

### Minor Changes

- **`erratas.md`: la revisión global propone arreglos de una línea y no aplica ninguno.** (§3, §4.3)

  - De los problemas del informe global, el harness separa los que se arreglan cambiando una línea —una fecha, un número, una frase que contradice un hecho— con capítulo, ruta, cita literal y cambio propuesto. Lo que exija reescribir una escena no es una errata y se queda solo en el informe.
  - Motivo: la pasada global encontró cuatro problemas reales que nadie podía usar para nada. Esto les da salida sin tocar nada aprobado.
  - Descartado: **reescrituras acotadas de los capítulos que señala la global.** Era la petición inicial y la respuesta es que no, por una razón que no es de esfuerzo: **la cadena de memoria es secuencial**. Reescribir el capítulo 1 invalida su resumen y, en cascada, todos los libros de estado posteriores; el libro de estado dejaría de ser cierto, y es lo único que sostiene una novela de 200 capítulos. §1.3 ya lo listaba como no objetivo y sigue haciéndolo.

- **Observabilidad con Langfuse, explícitamente fuera del harness.** (§9.3, §6.6, §10.1)

  - Mismo estatus que el visor: solo lectura, borrable sin consecuencias, no aparece en el inventario ni en los criterios de §8.2. Cinco reglas, por orden: no es fuente de verdad (manda `registro.md`), no es puerta del flujo, es *fail-open*, no escribe en `novelas/`, y las credenciales no entran en el repositorio.
  - Dos niveles que no se sustituyen: **traza de sesión** (hook `Stop` fuera del repositorio, para ver la ejecución en vivo y depurar el orquestador, que es la pieza frágil) y **traza de dominio** (un exportador de solo lectura que proyecta `registro.md` como novela › capítulo › intento › invocación, para entender y comparar ejecuciones).
  - Limitación conocida y anotada: el hook de sesión solo lee el transcript principal, así que los subagentes aparecen con su prompt y su mensaje final pero **sin sus tokens**. El coste por agente sigue sin medirse en el hito 1, igual que en §6.6.
  - Descartado: **llamar a Langfuse desde `invocar()`** en cada invocación. Es la forma obvia de tener trazas en vivo con forma de dominio, y mete turnos extra y un modo de fallo nuevo —la red— en un bucle cuyo mérito medido es tener cero fallos técnicos en 37 invocaciones. Todo sube después, desde ficheros ya escritos.
  - Descartado: **extender el hook para leer los transcripts de subagente** (`~/.claude/projects/<proy>/<sesión>/subagents/*.jsonl`) y atribuir tokens por agente. Es la única vía de medir el coste por agente en el hito 1, y depende de rutas y de un formato interno que Claude Code no garantiza —lo mismo que ya descartó la 0.5.1 para verificar el modelo—. En el hito 2 la API devuelve tokens y coste por llamada y el problema desaparece solo; no vale la deuda.
  - Descartado: **poner las credenciales en `.claude/settings.json` y añadirlo al `.gitignore`**, que es lo que dice la guía oficial. En este repositorio ese fichero está versionado porque lleva los permisos del harness y el hook de inmutabilidad (§3.1): sacarlo del repositorio sería sacar la configuración del harness. Van en `.claude/settings.local.json`, ignorado.

- **Umbrales de `calidad` recalibrados con la ejecución de referencia.** (§7.7)

  - `max_graves_por_10_capitulos` 1 → 2, `max_agotamiento_pct` 10 → 20, `min_aprobados_primer_intento_pct` 60 → 40, `max_rechazos_voz_pct` 10 → 20. `max_hilos_previstos_sin_cerrar` se queda en 0 y no se toca: es la única que mide un daño irreparable, y la regla nueva de mejor intento la protege de forma explícita.
  - Motivo: tres de ellos eran inalcanzables **por construcción** a 5 capítulos. Con esa N, un solo problema de gravedad 1 vale 2,0 puntos de `graves_por_10` y un solo capítulo por agotamiento vale 20 de `agotamiento_pct`: los umbrales de 1 y de 10 exigían cero de cada cosa. No eran exigentes, eran aritméticamente imposibles en la escala en la que se valida, y §7.7 ya decía que se calibraban con el paso 1. `min_aprobados_primer_intento_pct` baja por un motivo distinto y más discutible —60 % con `rechaza_con_graves: 1` y dos revisores es un objetivo, no una línea base— y queda marcado como suelo provisional.
  - La señal que decide de verdad sigue siendo la comparación entre dos ejecuciones del mismo caso de referencia (§8.4), no el valor absoluto.

- **§8.5 nueva: la ejecución de referencia, qué salió y qué cambió por ella.** Qué funcionó (los contratos), qué falló (las reglas de flujo), la tabla de los tres defectos con su corrección, y por qué el «0 de 5» no significa lo que parece. Motivo: es la única fuente de datos del proyecto y estaba solo en la carpeta de la novela; cualquier cambio futuro de las reglas de §4.2 tiene que pasar por ella.

### Patch Changes
- Criterios de aceptación nuevos en §8.2: 12 (dos revisores, reintento del que falla sin repetir el otro), 13 (canon sembrado a propósito), 14 (mejor intento por cierres de escaleta), 15 (erratas sin tocar ningún capítulo aprobado). El criterio 3 se actualiza para distinguir ajuste de longitud de reescritura.
- §6.5: un fallo técnico durante la revisión reintenta **solo el revisor que falló**; el otro ya entregó.
---

## 0.6.0

### Minor Changes

- **Visor web de solo lectura sobre `novelas/`, explícitamente fuera del harness.**

  - Motivo: una novela a medias está repartida entre `estado.json`, `registro.md`, un `informe-K.md` por intento y un fichero por capítulo. Entender por qué el revisor tumbó un intento obliga a abrir cuatro ficheros y cruzarlos a mano, y eso es justo lo que hay que hacer decenas de veces durante los pasos 1 y 2 de §7.8. El visor hace el cruce.
  - Spec: §1.3 pasa de prohibir "interfaz web o gráfica" a prohibirla **como parte del harness**, y §9.2 define qué es el visor y qué tiene prohibido. La frontera es que **solo lee**: no invoca agentes, no decide flujo y no escribe en `novelas/`. Borrar `frontend/` entera no cambia lo que el harness produce, y por eso el visor no aparece en `specs/inventario.md` ni en los criterios de §8.2.
  - Dos puntos más de §1.3 se ajustaron por coherencia: "código propio en el hito 1" pasa a tener dos excepciones declaradas (el hook de inmutabilidad y el visor, ninguna pieza del harness), y "formatos de salida distintos de Markdown" se precisa como "el sistema no escribe ningún artefacto que no sea Markdown o JSON", porque pintar Markdown en un navegador no produce ficheros.
  - Reparto: un servidor local de solo lectura (`frontend/server/`, Node sin dependencias) conoce la estructura de §3, la interpreta y la sirve como JSON; la web solo pinta. Así el conocimiento de rutas y nombres de fichero vive en un único sitio, y cuando llegue el runner del hito 2 se reaprovecha en vez de reescribirse.
  - Portabilidad al hito 2 (regla 6 de CLAUDE.md): el visor lee la estructura de carpeta, que §10.1 declara idéntica en los dos hitos. Funciona sobre una novela del runner sin saber quién la generó, igual que `/novela estado` (§10.3, punto 2). Nada del visor depende de Claude Code.
  - Dependencias aprobadas para `frontend/`: `vite`, `react`, `tailwindcss`, `marked` y `@tailwindcss/typography`. El servidor no lleva ninguna. El harness sigue sin dependencias de ningún tipo.
  - Descartado: **que el visor calcule las métricas de calidad de §8.3**. Tendría números también para novelas a medias, pero duplicaría una regla de la spec en dos implementaciones: si el visor y el `informe-cierre.md` dieran cifras distintas, no habría forma de saber cuál miente. El visor muestra las oficiales si existen y, si no, dice que aún no las hay.
  - Descartado: **que el visor lance o continúe generaciones**. En el hito 1 el harness es una sesión de Claude Code y una web no puede invocarla. Tendrá sentido cuando exista el runner, y entonces el visor ya estará construido.
  - Descartado: **volcado estático de `novelas/` a un JSON dentro del frontend**. Evita el servidor, pero hay que relanzarlo a mano y no deja ver el progreso mientras `/novela` corre, que es la mitad del valor.
  - Descartado: **el frontend en un repositorio aparte**. El visor lee `novelas/` de este repo; separarlos obligaría a configurar rutas entre dos sitios y a mantener dos historiales para una sola cosa.

## 0.5.1

### Patch Changes

- **El modelo de cada agente se declara también en el frontmatter, y el arranque comprueba que coincide con `config.json`.**

  - Motivo: los cuatro ficheros de `.claude/agents/` no declaraban `model`. El harness sí pasa `model` en cada llamada a `Agent` (`invocar.md`), así que una ejecución normal usa el modelo de `config.json` —comprobado en la primera ejecución de referencia: las 10 invocaciones corrieron en `claude-opus-5`—, pero si el orquestador, que es prosa, omitiera ese parámetro una vez, el subagente heredaría el modelo de la sesión **en silencio** y `registro.md` seguiría anotando el de `config.json`. En un proyecto cuyo §7.8 paso 2 es una comparación entre modelos, un modelo equivocado con el log diciendo lo contrario invalidaría la comparación sin dejar rastro.
  - Cambios: `model: opus` en los cuatro agentes; `comprobar_entorno` (SKILL.md §1, spec §6.2 y §6.5) compara `maxTurns` **y** `model` con la config de la raíz y para con `ERROR_CONFIGURACION` indicando fichero, campo, valor declarado y esperado; spec §2, §7.3 y §6.6 lo documentan.
  - El modelo que manda sigue siendo el del parámetro `model` de la llamada: es lo que permite el escalado de §7.3. El frontmatter es solo la red de seguridad.
  - La comparación es contra la config **de la raíz**, antes de las sobreescrituras, para que `modelos.escritor=haiku` en la línea de comando siga siendo un acto deliberado y no un error. Esa es la vía recomendada para el paso 2 de §7.8, en lugar de editar cinco ficheros.
  - Descartado: **pinchar el modelo solo en el frontmatter** y quitar el parámetro de la llamada. Es una única fuente de verdad, pero el frontmatter es estático y mataría el escalado de §7.3, que necesita decidir el modelo por invocación.
  - Descartado: **verificar a posteriori qué modelo respondió** leyendo los transcripts de subagente de Claude Code (`~/.claude/projects/<proyecto>/<sesión>/subagents/*.jsonl`). Funciona —así se comprobó esta incidencia— pero depende de rutas fuera del repositorio y de un formato interno que Claude Code no garantiza. Queda anotado en §6.6 como limitación conocida del hito 1; en el hito 2 la respuesta de la API dice qué modelo contestó y se acabó el problema.

## 0.5.0

### Major Changes

- **Solo el harness escribe en disco; los agentes devuelven su salida en el mensaje final.**

  - `specs/functional.md` §1.2, §3.1, §5 y §6.1. Los subagentes del hito 1 se definen con `tools: Read, Glob, Grep`, sin herramientas de escritura. El harness valida la forma de cada salida y la escribe en su ruta.
  - Motivo: es lo que §10.2 ya preveía para el runner. Hacerlo igual en los dos hitos deja los contratos de los agentes idénticos y elimina `verificar-zona.md`, la pieza con el bug más grave de la 0.4.0 (borraba el capítulo antes de revisarlo). La zona de escritura queda garantizada por construcción y desaparece el motivo de parada `ESCRITURA_FUERA_DE_ZONA`.
  - Descartado: `permissions.deny` con patrones de ruta. Se aplica a toda la sesión, no por subagente, y bloquearía también al interrogador cuando escribe la biblia.

- **Cuarto agente: `resumidor`. El escritor ya no escribe el resumen.**

  - El resumidor recibe **solo** el texto del capítulo y el libro de estado vigente, y devuelve el resumen y el libro de estado actualizado. No ve la escaleta ni la biblia, para que registre lo que hay en la página y no lo que debía haber.
  - Motivo: en la ejecución 0.4.0 el resumen del capítulo 1 afirmaba un hecho que el texto no mostraba. A 200 capítulos los resúmenes son la memoria del sistema; el escritor es parte interesada.

- **Libro de estado (`libro-estado.md`) como memoria de tamaño constante.** §3, §7.6.

  - Personajes (dónde, qué saben, estado), hilos abiertos con capítulo de origen y cierre previsto, hilos cerrados, objetos/lugares/datos, reglas en vigor. El resumidor propone la versión nueva en cada intento (`libro-estado-K.md`); el harness la adopta solo al aprobar. Escritor y revisor lo reciben siempre.
  - Sustituye a `memoria.digesto_por_acto`, que nunca se implementó y no resolvía el problema: una ventana de resúmenes pierde estado, no solo texto. `memoria.libro_estado_max_palabras` (4000) acota su tamaño.

- **Escaleta en dos niveles: alto nivel (arcos) + escaleta de cada arco generada al llegar a él.** §4.1, §4.2.

  - `formato.capitulos_por_arco` (15). Con total ≤ 15 hay un solo arco y el comportamiento es el de antes. La escaleta de alto nivel es lo que aprueba el usuario y lo inmutable; la de cada arco la valida el harness sin intervención humana, con el libro de estado y el informe del arco anterior como entrada.
  - Motivo: ningún modelo produce 200 entradas de capítulo coherentes de una vez, y el arco 9 debe conocer lo que realmente pasó en los arcos 1–8. `saga` es una sola novela con una sola trama, no una serie.

- **La longitud la comprueba el harness, no el revisor.** §4.2, §5.4.

  - `wc -w` antes de invocar a nadie más. Si se sale de la tolerancia, el harness genera el informe (gravedad 3) y consume el intento sin llamar al resumidor ni al revisor. El criterio 3 desaparece del contrato del revisor; la numeración se conserva.
  - Motivo: los modelos no saben contar palabras, y el revisor de la 0.4.0 tenía la instrucción "cuenta tú las palabras". El criterio de aceptación 3 (tolerancia 0) pasa a ser determinista.

- **Vocabulario: `hito` para las fases del proyecto, `etapa` para las del flujo.** La palabra "fase" desaparece de la spec: significaba dos cosas distintas en el mismo documento.

### Minor Changes

- **Revisión por arco y revisión global acotada.** Al cerrar cada arco, el revisor emite `arcos/informe-arco-AA.md`, que alimenta la escaleta del arco siguiente. La pasada global sobre el manuscrito completo solo se hace si no supera `limites.revision_global_max_palabras` (60000); por encima, se hace sobre biblia, escaleta, libro de estado, resúmenes e informes de arco. Motivo: 200 × 2500 palabras no caben en ningún contexto.
- **El revisor devuelve JSON, no YAML**, con exactamente tres claves; el harness lo valida y cualquier otra cosa es incumplimiento de contrato. En el hito 2 se valida con esquema y se pide salida estructurada donde el modelo lo admita. Motivo: los modelos baratos rompen el YAML con más facilidad.
- **Aceptación por agotamiento elige el mejor intento, no el último**: menos problemas de gravedad 1–2, luego menos problemas en total, luego el más reciente. Un rechazo por longitud nunca gana frente a uno que pasó al revisor.
- **Métricas de calidad (§8.3) y umbrales `calidad.*` (§7.7)**: graves por 10 capítulos, % por agotamiento, hilos previstos sin cerrar, % aprobados en el primer intento, % rechazos por voz, desviación de longitud. El informe de cierre dice CUMPLE / NO CUMPLE por métrica. Es la traducción medible de "coherente, cohesionada y fiel a lo pedido", que es la definición del usuario de "suficientemente buena" para decidir si el modelo barato aguanta.
- **Caso de referencia fijo en `pruebas/referencia/`** (idea + entrevista + respuestas). Todas las comparaciones de §7.8 usan esa entrada. Motivo: sin entrada fija, comparar dos configuraciones es comparar dos historias distintas. `pruebas/respuestas-prueba.md` pasa a `pruebas/referencia/respuestas.md`.
- **`config.json` versión 3**: `proveedor` (`claude-code` | `openrouter`), `modelos.resumidor`, `modelos.temperatura.*` (hito 2), `modelos.escalado.revision_arco_y_global`, `formato.capitulos_por_arco`, `limites.revision_global_max_palabras`, `limites.presupuesto_usd_max` (hito 2), `memoria.libro_estado_max_palabras`, bloque `calidad`. Se elimina `memoria.digesto_por_acto`. `relato` pasa a 5 capítulos (3–8): la 0.4.0 se validó con capítulos de 350 palabras, así que el perfil a 1500 palabras aún no está validado.
- **§9.1: el orquestador se escribe como pseudocódigo con nombres de función estables** (`crear_novela`, `detallar_arco`, `escribir_capitulo`, `comprobar_longitud`, `resumir`, `revisar`, `decidir`, `cerrar_capitulo`, `revisar_arco`, `invocar`, `elegir_modelo`…). Motivo: el runner del hito 2 lo escribirá Claude Code a partir de SKILL.md; así el porte es traducción, no interpretación.
- **Volumen (§6.6)**: el registro lleva `pal_*`, `tok_*` y `coste_usd`; se rellena lo disponible en cada hito. En el hito 2 OpenRouter devuelve coste real y `presupuesto_usd_max` es un límite efectivo.

### Patch Changes

- **Glosario en `specs/functional.md` §0**: qué es y para qué sirve cada término del proyecto (harness, agente, hito, etapa, biblia, escaleta de alto nivel y de arco, arco, acto, hilo, gancho, intento, resumen, libro de estado, informe, veredicto, gravedad, aceptación por agotamiento, parada limpia…). Motivo: el usuario pidió un sitio único donde se defina el vocabulario antes de reconstruir la implementación.

- **Nuevo subcomando `/novela verificar <carpeta>`**: inventario §4 + métricas, solo lectura. Y `intento-K.md` deja de llevar frontmatter —es título y texto— para que `wc -w` se aplique directo.

- **El modo de prueba toma `idea.md` y `entrevista.md` de una carpeta** (`modo-prueba: pruebas/referencia`) en vez de emparejar palabras clave con una tabla de respuestas. Nuevo flag `entrevista: <ruta>` para la ejecución de referencia con confirmación manual. Motivo: es exactamente el mecanismo con el que el runner recibe la entrevista, así que el hito 1 lo prueba gratis; y el caso de referencia queda escrito una vez, no reconstruido en cada ejecución. `pruebas/referencia/respuestas.md` se elimina; su contenido pasa a `entrevista.md`.

- **Reconstruidos `CLAUDE.md`, `README.md`, `.claude/settings.json` y los cuatro agentes.** `CLAUDE.md` queda en seis reglas y un puntero a la spec. `settings.json` lleva la lista de permisos (lectura, escritura en `novelas/` y `comparativa/`, `git` acotado a `novelas/`, `wc`, `mkdir`, `cp`) para que el bucle corra sin confirmaciones, y deniega `git push`, `--amend`, `reset --hard` y `rebase`. Los agentes llevan `tools: Read, Glob, Grep`, `maxTurns: 40` y no llevan `memory`. La forma de los bloques de salida (`=== ARCHIVO: ruta ===` … `=== FIN ===`) queda fijada en la spec §5.

- **Hook `PreToolUse` que bloquea `Edit` sobre artefactos inmutables** (`biblia.md`, `escaleta.md`, `arco-*.md`, `intento-*.md`, `libro-estado.md`, `manuscrito.md`). Una línea de shell en `.claude/settings.json`, sin `jq`. Es la única excepción a "sin código en el hito 1" y se anota como tal en la spec §1.3 y §3.1. Motivo: el harness nunca necesita `Edit` sobre esos ficheros (los crea con `Write`), así que cualquier `Edit` es un error del orquestador y se puede cortar en seco sin conocer el estado. No protege contra una sobreescritura completa; eso lo detecta el criterio 6 con git. En el hito 2 la inmutabilidad es código.

- Descartado: `permissions.deny` con patrones de ruta para lo mismo. Las reglas `Edit(...)` de permisos se aplican también a `Write`, así que bloquearían la creación legítima del fichero.

- **`harness.config.json` pasa a llamarse `config.json`** en la raíz. La copia congelada por novela sigue siendo `novelas/<slug>/config.json`.
- **`limites.turnos_por_invocacion` es realmente aplicable**: `maxTurns` en el frontmatter del subagente (Claude Code ≥ 2.1.246). Como es estático, el harness comprueba al arrancar que coincide con `config.json` y para con `ERROR_CONFIGURACION` si no. Un resultado marcado como parcial se trata como incumplimiento de contrato. Verificado contra la documentación: la herramienta `Agent` no devuelve tokens en el resultado.
- **Criterios de aceptación nuevos** (§8.2): 10, salida mal formada del revisor; 11, arcos con `capitulos_por_arco: 2`. El 6 pasa de "permisos" a "inmutabilidad".
- **Reconstrucción**: la implementación 0.4.0 (skill, agentes, plantillas, procedimientos, inventario, comparativa) se retira del árbol de trabajo y se reconstruye sobre esta spec. Sigue en el historial de git como referencia. Se quita la referencia al `.drawio` archivado.

---

## 0.4.0

### Major Changes

- **El proyecto tiene dos fases y la spec lo dice: Claude Code ahora, runner contra OpenRouter después.**

  - `specs/functional.md` §1 deja de afirmar "no hay código" como decisión fija y pasa a describir dos fases: (1) validar el diseño en Claude Code con el modelo caro e historias de 3 capítulos; (2) portar ese mismo diseño a un runner propio contra OpenRouter con un modelo barato para llegar a 100–200 capítulos. Nueva §10 con qué se porta sin cambios (contratos de los agentes, plantillas, prompts, configuración, carpeta y estado), qué se reimplementa (orquestador, invocación, zona de escritura, entrevista, confirmación) y el contrato que debe cumplir el runner (pasar el inventario y los criterios de aceptación sin adaptación).
  - `CLAUDE.md` añade la regla: todo lo que se diseñe tiene que poder portarse; si algo solo funciona en Claude Code, se anota.
  - Motivo: el objetivo del usuario siempre fue montar la solución agéntica con el modelo caro y pasarla después a uno barato en OpenRouter. La 0.1.0 había abandonado la línea OpenRouter por completo y la spec, que manda sobre todo, prohibía el código; con eso el destino era inalcanzable y cualquier sesión futura lo habría defendido. La decisión de 0.1.0 se reinterpreta: se abandonó **empezar** por el código, no llegar a él.
  - Descartado: seguir en Claude Code con modelos baratos como fase final. Funciona para abaratar (paso 2 del plan), pero no da el bucle desatendido de 200 capítulos (una pausa cada 5 capítulos son 40 relanzamientos a mano).

### Minor Changes

- **Volumen por invocación: el dato para decidir el modelo.**

  - Cada fila `invocacion` de `registro.md` lleva `modelo`, `pal_entrada` (palabras de los ficheros que se le mandó leer) y `pal_salida` (lo que entregó). El informe de cierre suma por subagente y por modelo. `specs/functional.md` §6.6.
  - Motivo: Claude Code no expone el coste, pero la decisión de pasar a un modelo barato es económica. Volumen × tarifa = coste, para cualquier modelo y para el runner (que registrará tokens reales en las mismas columnas).

- **Inventario de salidas: `specs/inventario.md`.**

  - Lista, fichero a fichero, lo que debe producir una ejecución completa: qué es, cuántos hay, quién lo escribe y su definición de hecho. Incluye la cuenta por perfil, lo que **no** genera, un procedimiento de 6 pasos para comprobar que una ejecución está completa, y señales de calidad distintas de la completitud.
  - Es además la definición de "misma salida" para el runner de la fase 2 (§10.3).

- **Carpeta `comparativa/` y comando `/novela comparar <caso>`: dos ejecuciones del harness con la misma idea.**

  - Un caso = `caso.md` (idea, qué se compara, lados A y B como rutas a `novelas/<slug>/`, qué difiere en `config.json`) + `comparacion.md` (lo rellena el comando). Las novelas se referencian, no se copian: su historial de git es parte de lo que se mide. `plantilla/` se copia para crear un caso.
  - El comando llena un bloque medible (capítulos, palabras contadas, intentos, agotamientos, reintentos, problemas globales, artefactos, volumen por modelo) y otro de lectura donde cada casilla exige una cita. Nada se estima; lo no disponible es `desconocido`. Termina con el veredicto y una lista de cambios accionables para el harness.
  - Motivo: es lo que decide el paso 2 (modelo caro frente a barato) y valida el paso 3 (Claude Code frente al runner) del plan de §7.7.
  - Descartado: la versión anterior de esta carpeta comparaba el harness con un **prompt suelto** a OpenRouter. Medía si el harness aporta algo frente a no tener harness, que no es la decisión pendiente; y además nunca llegó a crearse en disco aunque la 0.3.0 la daba por hecha. Se sustituye por esta.

- **Plan de escalado en cinco pasos (`specs/functional.md` §7.7)**: validar (relato, opus) → abaratar (mismo harness, haiku/sonnet con escalado) → portar al runner → crecer (12, 30) → saga (100–200). Cada paso cambia solo configuración salvo los dos marcados como trabajo de harness: el runner y `memoria.digesto_por_acto`.

- **`saga` llega a 200 capítulos** (`capitulos_max: 200`). El objetivo declarado es 100–200; el techo anterior de 120 lo hacía inalcanzable por configuración.

### Patch Changes

- **Arreglado el bug de `verificar-zona.md` que borraba el capítulo antes de revisarlo.** El paso (a) exigía `git status` vacío antes de *cada* invocación y, si no lo estaba, hacía `git checkout` + `git clean` de la carpeta. Al invocar al revisor, `intento-K.md` y `resumen-K.md` recién escritos están sin commitear: el procedimiento los habría eliminado. Ahora el orquestador **fija el índice** (`git add -A`) antes de invocar y, al volver, lo que difiere del índice es exactamente lo que tocó el subagente; los ficheros fuera de zona se restauran desde el índice. La limpieza total pasa a `descartar()`, que solo se usa al reanudar o al parar, y deshace también el índice (`git reset -q HEAD --`) antes de `checkout` y `clean`.
- **La spec dice quién escribe los informes.** `functional.md` §3 y §5.3 afirmaban que el revisor escribía `informe-N.md` e `informe-global.md`; `CLAUDE.md`, el inventario, `revisor.md` y `capitulo.md` decían que los escribe el orquestador a partir del YAML del revisor. Gana lo segundo (el veredicto en disco es el recalculado por el harness) y la spec queda corregida.
- **Configuración por defecto = fase de validación**: los tres agentes en `opus`, `escalado.activo: false`. Antes era `sonnet` con escalado a `opus`, un híbrido que no respondía ni a "cuál es el techo del diseño" ni a "aguanta el modelo barato". Las configuraciones de abaratamiento y mínima quedan documentadas en §7.3 y se aplican por comando sin editar el fichero.
- **`README.md` explica el proyecto**: las dos fases, cómo se lanza, dónde está cada cosa. Antes eran tres líneas.
- **El cierre en ÉXITO comprueba la ejecución contra el inventario** y avisa en el informe de cierre de cualquier artefacto que falte.
- **`functional.md` §9 referencia el inventario y la comparativa**; antes eran un comando y un documento que la spec que manda no conocía.

## 0.2.0

### Minor Changes

- **Toda la configuración ajustable pasa a `harness.config.json`**, en la raíz del repositorio.

  - Es el único fichero que hay que editar para cambiar el comportamiento del harness: tamaño de la historia, modelos, reintentos, reescrituras, memoria y regla de veredicto. Documentado en `specs/functional.md` §7.
  - Sustituye a `.claude/skills/novela/config.md`, que se elimina. Los procedimientos y los subagentes leen ahora `config.json`.
  - Al crear una novela, la configuración efectiva se **congela** en `novelas/<slug>/config.json`. Editar el fichero global después no afecta a las novelas ya empezadas.
  - Motivo: el usuario quería poder tocar páginas, capítulos, reintentos, modelos y límites desde un sitio, sin abrir la skill ni las specs.

- **Perfiles de tamaño: `relato`, `novela_corta`, `novela`, `saga`.**

  - `perfil_activo` es una sola cadena y es lo que escala el proyecto: de 3 capítulos de prueba a 100. Por defecto, `relato`.
  - Cada perfil fija `capitulos_objetivo`, `capitulos_min`/`max` y `palabras_por_capitulo`.
  - Alternativa por páginas: si un perfil define `paginas_objetivo`, manda sobre `capitulos_objetivo` y el harness deriva los capítulos con `formato.palabras_por_pagina` (250 por defecto). Si el resultado se sale del rango, para antes de invocar a nadie.
  - Motivo: el plan es validar con pocos capítulos y escalar; así el salto es cambiar un valor, no reescribir la spec.

- **Modelo configurable por subagente, con escalado cuando algo va mal.**

  - `modelos.interrogador` / `escritor` / `revisor` fijan el modelo base (`sonnet` por defecto).
  - `modelos.escalado` sube a un modelo mejor (`opus` por defecto) en las situaciones que lo merecen: reescritura tras un rechazo (`escritor_desde_intento: 2`), juicio del último intento (`revisor_desde_intento: 3`), reintento tras fallo técnico, y revisión global final.
  - El orquestador pasa el modelo en cada invocación (SKILL.md §8) y lo registra en `registro.md`.
  - Motivo: el primer intento no necesita el modelo caro; el que arregla un capítulo rechazado, sí.

- **`memoria` como palanca de escalado.**

  - `resumenes_completos_ultimos` (por defecto `null` = todos), `capitulo_anterior_integro` y `digesto_por_acto` controlan cuánto contexto recibe el escritor.
  - Pendiente y anotado como tal: `digesto_por_acto` **no está implementado**. Hasta que lo esté, limitar la ventana de resúmenes pierde información de los capítulos antiguos, así que el perfil `saga` (100 capítulos) todavía no es viable. Es el siguiente trabajo del harness.

### Patch Changes

- **La regla de veredicto pasa a ser numérica y configurable**: `veredicto.rechaza_con_graves` (1) y `veredicto.rechaza_con_leves` (2). Antes estaba escrita en prosa en `config.md`. El orquestador la sigue recalculando él, sin fiarse del veredicto que escriba el revisor.
- **`limites.pausa_cada_capitulos` admite `null`** para desactivar la pausa programada.
- **`specs/changes.md` se elimina**: su contenido vive aquí. `specs/functional.md` §9 y `CLAUDE.md` apuntan a este fichero.

## 0.1.0

### Minor Changes

- **Harness montado sobre Claude Code, sin código.**

  - Creados `CLAUDE.md`, `.claude/skills/novela/` (SKILL.md, procedimientos/, plantillas/), `.claude/agents/{interrogador,escritor,revisor}.md`, `pruebas/respuestas-prueba.md` y `novelas/`.
  - El harness es la skill `/novela` ejecutada por Claude en la sesión; interrogador, escritor y revisor son subagentes. No hay programas, librerías ni servicios propios.
  - Motivo: el usuario quiere decirle a Claude Code "haz lo de las especificaciones" y que con eso genere la novela.

- **El interrogatorio inicial se mantiene y se hace con `mattpocock-skills:grilling`.**

  - El orquestador hace de intermediario: los subagentes no hablan con el usuario. El resultado se escribe en `entrevista.md` y el subagente `interrogador` lo convierte en biblia y escaleta.
  - El usuario confirma la escaleta antes de que se escriba una sola línea de novela.

- **Zonas de escritura verificadas con git.**

  - Cada subagente declara en qué ficheros puede escribir; al volver, el orquestador compara `git status` y revierte con `git checkout` lo que se haya salido, registrando el incidente y repitiendo la invocación.
  - Descartado: un hook `PreToolUse` que bloqueara las escrituras. Era más fuerte, pero exige un comando de shell y el usuario no quiere código de ningún tipo.

- **Commits automáticos dentro de `novelas/`** en los puntos consistentes (carpeta creada, escaleta aprobada, capítulo cerrado, novela completa, parada), sin pedir confirmación. Fuera de esa carpeta, nunca sin que el usuario lo pida. Es lo que hace posible la reanudación y la verificación de zonas.

### Major Changes

- **Se abandona la implementación en Python + OpenRouter + Pydantic AI.**

  - Toda la línea de trabajo anterior (CLI, SDK, modelos configurables por API, exportación con librerías, tests en pytest) se descarta a favor del harness en Claude Code.
  - Consecuencias: desaparecen el presupuesto en dinero (Claude Code no expone el coste; los límites pasan a ser estructurales), la exportación a PDF y DOCX (solo Markdown) y los códigos de salida (no hay proceso).
  - Motivo: decisión del usuario. Quiere el harness, no un programa, y que sea Claude Code quien escriba las historias con él.
