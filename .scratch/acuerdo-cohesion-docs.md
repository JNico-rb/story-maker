# Acuerdo de cohesión: docs antes de las specs (2026-09-23)

Fichero de trabajo temporal. Lo aplica un chat nuevo de Claude Code y se borra al terminar la fase 2: `CLAUDE.md` manda borrar un fichero de trabajo cuando ha cumplido su función.

## 0. Punto de partida

- El encargo es `project-constraints.md`. Las reglas están en `CLAUDE.md`, que el usuario fusionó con el antiguo `AGENTS.md`, ya borrado.
- `docs/` contiene solo los cuatro docs de referencia y `adr/`. Los registros de proceso son secciones de `verification.md`:
  - §4.2, resultados de las evals;
  - §4.9, casos de red-team;
  - §8, registro de iteraciones;
  - §9, Claude Code en el desarrollo.
- Cuatro auditorías de solo lectura y dos investigaciones encontraron unos 270 problemas. Se resolvieron así:
  - las decisiones de §1, en cinco rondas de grill con el usuario;
  - el resto, con la opción más simple, en §2.
- **El grill de esta tarea está hecho y el usuario pidió aplicarlo.** No repitas estas preguntas. Usa `AskUserQuestion` solo si al aplicar aparece un conflicto nuevo que este fichero no resuelve.
- **Ya aplicado; no lo rehagas:**
  - Atributos nuevos de `Evento`: personaje excluido, edades declaradas, consecuencias de las que depende y origen `brief | planificado | registrado`. Los nacimientos son la fecha de nacimiento del `Personaje`.
  - Fechado de los recuerdos en `domain-knowledge.md` §5.2.
  - Arcos resueltos en el delta real y en `submit_record`, y `arcos-cerrados` leyéndolos.
  - Tool `Skill` para el writer y el editor.
  - Hook de validación que sustituye la salida de la tool por los defectos.
  - Fila de §16 sobre el instrumentador de Langfuse.
  - §12.1: una observación por sesión de rol.
  - README raíz con el mapa de entregables y la lista de explainers.
  - ADR 0003 como spec inicial.
  - Registros de proceso trasladados a `verification.md`, con las filas 6 y 7 del §8.

## 1. Decisiones del usuario

Cada una va a su sección y a una fila de `architecture.md` §16: opciones, criterio y elección.

1. **Techo de 100.000 tokens.**
   - Cuenta solo la entrada; la salida no computa.
   - Vale **por ejecución**, y hay **una sola ejecución activa en todo el servidor**: una cola global en orden de llegada, así que las novelas se generan de una en una.
   - Dentro de una ejecución se mantiene el paralelismo fácil: el juez, la revisión visual y Lean en el gate, y los editores en un cambio. Se reparten el techo.
   - Las sesiones que no pertenecen a una ejecución (entrevista, interpretación de un cambio) respetan el techo cada una por sí sola.
2. **Cambios del lector.**
   - La interpretación se muestra **antes de confirmar**, con el mismo flujo en web y en MCP.
   - El planner en modo cambio corre en el proceso de la API al pedirse, y el código valida la propuesta.
   - El lector ve los hechos que cambian y los capítulos afectados, y recibe un código.
   - Al confirmar se encola una ejecución con su versión base; al arrancar, esa ejecución revalida la propuesta contra la versión vigente.
3. **`EstadoDelMundo` compacto.**
   - Contiene el momento actual de la historia; por personaje, su último lugar, si está excluido y los hechos que cambió algún delta real; y el estado de los arcos.
   - Pesa unos cientos de tokens. El detalle estable llega por las CanonCards recuperadas.
4. **Lectura servida por FastAPI.** El frontend compilado se sirve en el mismo origen y la API va bajo `/api`. En desarrollo, Vite hace de proxy.
5. **PDF al publicar.**
   - Es el último paso del gate. Si `pdf-enlaces` falla, es `fallo de render` y la versión no se publica.
   - Se guarda en el directorio de datos; la API y `download_novel` sirven ese fichero.
6. **Cronología en el linter en vivo: dos avisos ligeros.**
   - Un personaje que reaparece tras su evento excluyente.
   - Una edad escrita que no cuadra con su fecha de nacimiento.
   - Son solo avisos para el editor humano. El gate sigue verificando con Lean, y ningún validador del harness duplica esos invariantes.
7. **Prompts.**
   - Cada prompt es un fichero del repo, en `backend/harness_workspace/`.
   - Un comando lo sube a Langfuse como versión nueva cuando cambia su huella.
   - En ejecución se lee de Langfuse por una etiqueta, que es un ajuste del servidor.
8. **Extensión.** Los objetivos pasan a corta 1.100, media 1.250 y larga 1.400 palabras. `longitud-capitulo` sigue comprobando 1.000–1.500.
9. **Herramientas.**
   - Una **CLI** para reproducir el brief de ejemplo y lanzar las evals.
   - **Alembic desde el principio.**
   - **Dos especificaciones TLA+ extra**: la de regeneraciones concurrentes y la del código de confirmación.
10. **Legibilidad.** Objetivos solo por franja de edad, de longitud de frase y de Fernández-Huerta. El matiz del tono queda para la rúbrica.
11. **Una ejecución `blocked` se reanuda como una `interrupted`.**
    - Parte de su punto de control, con intentos nuevos para el evaluable que bloqueó, dentro de `max_resumes`.
    - Solo `finished` y `cancelled` son terminales.
    - La candidata solo se rechaza al cancelar.
12. **Caducidades.** El token de acceso JWT caduca a las **24 h** y el código de confirmación de un cambio, a los **15 min**.
13. **Revisión visual.** Comprueba estructura y enlaces sobre la instantánea de accesibilidad. Lo puramente estético (CSS sin cargar, solapes) es un riesgo aceptado, escrito en `verification.md` §6.
14. **Coste.**
    - `operation.pricing` da el precio en USD por millón de tokens de cada modelo: entrada, salida, lectura de caché y escritura de caché, copiado de OpenRouter.
    - El coste es el uso exacto de cada sesión multiplicado por ese precio.
    - En la evaluación se contrasta una vez con lo que factura OpenRouter (`/api/v1/generation?id=`).
15. **Deseos de trama.** El brief lleva una lista opcional («que salga un robot»). Llega al planner, y el crítico y el juez no penalizan un tropo pedido.
16. **Catálogo de tropos.**
    - Se construye extrayendo del modelo y podando a mano, con marcadores al nivel de mecanismo narrativo.
    - Se valida con cinco mundos buenos y cinco malos.
    - Los tropos que se repitan en las evals se añaden como aprendidos. No se generan 20–30 mundos.
17. **Carpetas.** `presentation/` se queda con ese nombre y el README explica que es la `/presentacion/` del encargo. `CLAUDE.md` es el fichero que fusionó el usuario.

## 2. Resoluciones por documento

### 2.1 `definitions.md` — primero, porque es la autoridad de nombres

**Personas y brief**
- **`Cliente`:** la «configuración» que el encargo asocia al usuario es su brief. El «editor humano» de la edición manual usa la cuenta del cliente.
- **`Allegado`:** si solo se conoce su edad, su fecha de nacimiento es el 1 de enero de (año presente − edad), la misma regla que el destinatario.
- **`HechoExtraido`:**
  - Atributos: sujeto, atributo, valor, cita, obligatorio y aceptado.
  - Solo se guardan los verificados, así que el atributo «verificado» desaparece.
  - Un sujeto desconocido se descarta.
- **`Brief`:**
  - Gana «deseos de trama», una lista opcional.
  - Las entradas prohibidas pasan a ser obligatorias de preguntar; la lista puede quedar vacía si el cliente responde «ninguna».
  - Datos faltantes, contradicciones y huecos se calculan en cada turno y no se guardan. Se quita el estado de `Contradiccion` y los «hechos resultantes» y el «ámbito» de `Hueco`.
- **`Novela`:**
  - Gana la fecha de creación, que usa la regla C4.
  - Su estado se deriva y no se guarda: `interview`, `ready`, `in_progress` o `published`.
- **`Extension`:** 1.100 / 1.250 / 1.400.
- **`FranjaDeEdad` (`age_band`)** es nueva: infantil 0–12, juvenil 13–17, adulto 18+, con identificadores `children`, `teen`, `adult`.

**Story bible**
- **Versionado:** la story bible es **de cada versión**. Toda fila lleva la versión, y una candidata nueva copia la vigente en una sola transacción.
- **`Mundo` (`world`)** es nuevo: el `Novum`, sus `Consecuencia` y sus `Restriccion`.
- **`Novum`:** su ámbito se alinea con `domain-knowledge.md`: tecnológico, social o cognitivo.
- **`Consecuencia`:**
  - Su orden es la profundidad desde el novum, como mucho 3.
  - Relación nueva: `Consecuencia` → `Restriccion`.
  - Se quita «visible en la narración», que nada usa.
- **`Restriccion`:**
  - Predicados proyectados: `immutable`, `forbidden`, `required`. El tipo es `character`, `place` o `world`.
  - «La puerta dura» pasa a ser «los validadores `delta-declarado` y `delta-real`».
- **`Personaje` y `Lugar`:**
  - Llevan el capítulo desde el que existen.
  - La fecha de nacimiento es opcional; sin ella, el personaje queda fuera de T2 y T5.
  - El nombre de un personaje se escribe desde su hecho de nombre.
- **`Hecho`:**
  - Solo admite inserciones, con capítulo de inicio: un cambio añade la fila sucesora.
  - El sujeto es polimórfico: personaje, lugar o mundo.
  - Son inmutables los de origen brief **y** los de origen texto libre.
  - Los atributos de los hechos del brief forman un vocabulario cerrado en `domain`.
- **`UsoDeHecho`:** solo lo escribe el registrador; se quita el origen «declarado por el writer». Los usos que declara el writer viven en su delta declarado.
- **`Evento`:**
  - Gana «evento que narra», una referencia al evento de trasfondo que narra una analepsis, para no duplicarlo.
  - Los antecedentes que inventa el planner son eventos planificados sin beat.
- **`Cronologia`:**
  - Son los recuerdos, los antecedentes y la trama; los nacimientos no son eventos, y la fecha del novum va aparte.
  - Se verifican **dos** cronologías:
    - la planificada: brief + planificados;
    - la registrada: brief + planificados sin beat + registrados.

**Artefacto**
- **`Version`:**
  - El número se asigna **al publicar**: una candidata o una rechazada no lo tiene.
  - Se quita el origen, que ya da el tipo de su `Ejecucion`.
  - Sus 10 capítulos se copian en cada versión con una huella de título y texto. «Cambiado» significa huella distinta de la última publicada, y la lista se guarda al publicar.
  - Guarda la ruta de su PDF.
- **`Capitulo`:** solo lo producido: texto, título copiado del outline, resumen y tensión medida de 1 a 5. Lo planificado vive en `Outline`.
- **`Beat`:** gana la revelación (tema y contenido). Su evento lleva todos los atributos de `Evento`.
- **`Arco`:** su estado se deriva de los deltas reales de la versión; no se guarda. Tipos: `character`, `plot`, `theme`.
- **`Outline` y `StyleSheet`:**
  - Son de cada versión: se copian en las de cambio y edición. Se quita el atributo «versión» de `Outline`.
  - La tensión va de 1 a 5.
  - En la `StyleSheet`, el registro sale de la franja de edad, el tiempo verbal es `past | present` y el tratamiento entre cada par de personajes, `tu | usted`.
- **`PuntoDeControl`:**
  - Una fila por capítulo aceptado (ejecución, capítulo), solo de inserción.
  - Además, puntos de control de fase:
    - el outline congelado con el canon inicial es el capítulo 0;
    - en el gate se repite el ciclo en curso;
    - en cambios y ediciones se rehacen los capítulos afectados que aún no se registraron.
- **`FichaDePersonajes`:** «Aquí se la llama» pasa a «El encargo la llama».
- **`Parrafo` (`paragraph`)** es nuevo: versión, capítulo, ordinal y texto. El texto es plano, y los párrafos se separan con una línea en blanco.
- **`VistaPrevia` (`preview`)** es nueva: la vista de una candidata. El worker emite su token; se canjea en la primera carga por una cookie limitada a esa candidata y se revoca al terminar la revisión. Lo que MCP devuelve antes de confirmar se llama «propuesta».

**Memoria**
- **`MemoriaDeCortoPlazo`:** los residentes son StyleSheet, elementos obligatorios, proyección del outline, `EstadoDelMundo` compacto, `ResumenRodante` y `CatalogoDeTropos`. Capítulo, defectos, propuesta y rúbrica son entradas de la llamada, no residentes.
- **`CanonCard`:**
  - Lleva `desde_capitulo`. `hasta_capitulo` no se guarda: se deriva del `desde` de la tarjeta sucesora de la misma entidad en esa versión.
  - Se copia por versión, compartiendo los vectores por huella.
- **`VentanaDeContexto`:** se guarda una por sesión de rol.
- **`Trazabilidad`:** filas (versión, capítulo, tipo, referencia).

**Harness**
- **`SesionDeRol` (`role_session`)** es nueva. Se distingue de la `Sesion` de Langfuse y de la autenticación.
- **Componentes de código** como términos: orquestador, guardián de ventana, recuperador, detector de inyección, worker y cola. «Guardián de presupuesto» pasa a ser «guardián de ventana».
- **`Ejecucion`:**
  - Tipos `generation | change_request | manual_edit`.
  - Estados y transiciones de §1.11.
  - Fases por tipo:
    - generación: `planning`, `chapter_production`, `publication`;
    - cambio: `revalidation`, `editing`, `publication`;
    - edición: `recording`, `propagation`, `publication`.
  - Motivo de bloqueo: `retries_exhausted`, `budget_exceeded`, `infeasible_config`, `render_failure`, `banned_content`, `internal_error`.
  - Atributos: candidata; posición en la cola; intentos por evaluable; versión base; PID y hora de arranque; marca de cancelación; copia de la config y de las listas prohibidas; commit.
- **`SolicitudDeCambio`:**
  - Selección `{versión, capítulo, cita}` o `{hecho}`.
  - Propuesta estructurada, código, versión base.
  - Estados `proposed | confirmed | rejected | expired | applied`.
- **`EdicionManual`:**
  - Lleva la versión base; estados `queued | applied | rejected`.
  - Su texto es **contenido no confiable** en cuanto llega al registrador.
- **`Presupuesto`:** en USD. Se aplica a cada ejecución y a cada entrevista.

**Calidad**
- **`Evaluable`:** `chapter`, `fallback_regeneration`, `outline`, `gate_cycle` y `change_interpretation`.
- **`Criterio`:**
  - Tiene id, bloqueante y acción requerida (`correct | regenerate | re_record | block`).
  - Origen `assignment | brief | catalog`.
  - Cada métrica de linter es un criterio determinista con id.
  - El tema prohibido es un criterio fijo que recibe los temas como parámetro.
- **`Rubrica`:** remite a `architecture.md` §10.3 para la lista de criterios.
- **`Validador`:**
  - Se quita el atributo «bloqueante»: lo hereda de sus criterios.
  - Los puntos de ejecución son una lista, y el enumerado crece: `brief_validation`, `extraction`, `tool_output`, `validation_hook`, `policy_hook`, `critic`, `recording`, `outline_freeze`, `world_submission`, `publication_gate`, `pdf_export`, `manual_edit`, `live_lint`, `evaluation`, `ci`.
- **`Defecto`:**
  - Se quita la severidad.
  - El criterio es opcional, para las causas raíz sin criterio.
  - `presupuesto excedido` se reserva al dinero, y la deriva del conteo pasa a ser `count_drift`.
  - `umbral_deriva_conteo` se corrige a `count_drift_threshold`.
- **`Score`:** uno por criterio, `<validador>/<criterio>`, además del agregado. Se copia también en SQLite.
- **`Tropo`:** origen `curated | learned`, alineado con «del género / del modelo».
- **`CatalogoDeTropos`:** lo usan el planner, el crítico y el juez. Un tropo pedido en los deseos de trama no se penaliza.
- **`InformeDeEjecucion`:** se calcula al pedirlo, a partir de los scores, los veredictos y los defectos guardados, e incluye el motivo de bloqueo.

**Política, observabilidad y formal**
- **`MotorDePoliticas`:** lo invocan el hook de policy y el código: sobre la petición, la edición manual y el gate.
- **`Coincidencia`:** tipo de ubicación (`chapter | cover | sheet | request | edit`), capítulo opcional y desplazamiento.
- **`DecisionDePolitica` y `AuditLog`:**
  - Columnas: momento; cliente (obligatorio); novela; ejecución, rol y tool (opcionales); origen; decisión; código de motivo; detalle.
  - El audit log registra también las detecciones de inyección y las escrituras MCP.
- **`Traza`:** una por entrevista, por importación, por interpretación de un cambio, por ejecución y por llamada MCP. Una ejecución reanudada conserva la suya.
- **`Mascara`:** es por novela, con los datos personales del brief y los hechos de origen brief de todas sus versiones.
- **`FicheroDeCronologia`:**
  - Fechas de calendario (año, mes, día, hora, minuto) con el año desplazado un **múltiplo de 400**, que conserva los bisiestos, en vez de minutos relativos.
  - Los identificadores son los de las filas de SQLite, sin nombres, así que no hace falta tabla de seudónimos.
  - Se guarda con su resultado y su testigo.
- **`VerificadorFormal`:** modos `local | github`. Devuelve JSON con el invariante violado y el primer testigo.
- **`EspecificacionDelHarness`:** `Harness.tla`, `Regenerations.tla` y `Confirmation.tla`, cada una con su `.cfg`. Los nombres de módulo van en inglés.

**Plataforma y config**
- **`TokenDeAcceso`:** JWT de 24 h con `exp`, `aud` e `iss`.
- **`Confirmacion`:** caduca a los 15 min y es de un solo uso.
- **`ServidorMCP`:** las tools de lectura no modifican nada; las de escritura solo encolan, y con confirmación. Así se concilia el «servidor de solo lectura» del encargo con su opcional de escritura.
- **§11 config:**
  - Claves nuevas sin valor: `quality.readability_targets` (por franja: longitud de frase y Fernández-Huerta), `operation.pricing` (por modelo: entrada, salida, lectura y escritura de caché, en USD por millón de tokens), `operation.max_verifier_seconds` y `operation.max_tool_output` (cota de salida de una tool, para la reserva de turnos).
  - Claves nuevas con valor: `operation.access_token_hours: 24` y `operation.confirmation_minutes: 15`.
  - `window_ceiling` se valida ≤ 100.000 al arrancar. `budget` va en USD; `count_drift_threshold` es una proporción.
  - Constantes del dominio en `domain`, no en config: 10 capítulos, 1.000–1.500 palabras, 3–6 beats y orden ≤ 3.
- **Ajustes del servidor, con nombre:** directorio de datos, ruta de `config.json`, modo del verificador formal, secreto del JWT, repositorio y workflow de Lean, etiqueta de los prompts y clave de OpenRouter. El backend traduce la clave al entorno del SDK: `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN=<clave>` y `ANTHROPIC_API_KEY=""`.
- **§12:**
  - Proyectar todos los términos y valores nuevos.
  - Completar los enumerados que faltan: estados de `Novela`, `Entrevista`, `SolicitudDeCambio` y `EdicionManual`; fases; ámbitos; orígenes; tipos de `Arco`; campos de `StyleSheet`; `Criterio`; `Tropo`.
  - Unificar `change_request` y `manual_edit`.
  - **Excepción declarada:** los nombres de validador, de span y de prompt son etiquetas en español, ASCII y en kebab-case, porque se ven en Langfuse.

### 2.2 `domain-knowledge.md`

- **§4.3:**
  - C6 cubre los tres niveles de listas prohibidas y también la dedicatoria.
  - Regla nueva **C7**: hay contradicción cuando un allegado está presente en un recuerdo anterior a su nacimiento.
  - C4, C5 y C7 son validación de entrada del brief, anterior a toda cronología: no duplican a Lean.
- **§5.2:**
  - El nacimiento es a las 00:00.
  - Un cumpleaños del 29 de febrero cae el 1 de marzo en un año no bisiesto.
  - Los allegados de edad conocida siguen la regla del 1 de enero.
- **§5.3:** los invariantes pasan a ser **T1–T6**. T1 usa el orden de capítulo y beat.
- **§6:**
  - «Del género / del modelo» equivale a «curado / aprendido».
  - Un tropo pedido en los deseos de trama no es un defecto.
  - §6.2 sigue la decisión 16.
- **§7:** los objetivos van solo por franja de edad; el tono lo juzga la rúbrica.
- **§8 y la lista de la rúbrica:** remiten a `architecture.md` §10.3.

### 2.3 `architecture.md` — sección a sección

**Premisas y entrevista**
- **§1.2:** las constantes del encargo y del dominio frente a la config. El techo es una clave de config validada ≤ 100.000, porque las pruebas doradas usan cuotas menores.
- **§2:** reanudar y cancelar son operaciones, fuera de los «tres momentos» humanos. En el diagrama, el gate termina en el PDF.
- **§3:**
  - El entrevistador pregunta siempre por las prohibidas y anota los deseos de trama.
  - Corre en el proceso de la API, con una sesión del SDK por turno HTTP que recibe el historial guardado:
    - si el proveedor falla o se agota un límite: 503, sin guardar el turno;
    - si un texto libre no cabe: 422;
    - cada entrevista lleva su techo en dinero, `budget`.
  - El extractor entrega sujeto, atributo, valor y cita. Se descarta todo hecho cuya cita se solape con una frase que marque el detector.
  - Reglas C1–C7.
  - Un brief importado queda confirmado al importarse, sus hechos no son obligatorios y tiene su propia traza.
  - Los campos obligatorios incluyen «entradas prohibidas preguntadas».

**Story bible y planificación**
- **§4.1:**
  - El canon del brief lo escribe el código **en el primer paso de la planificación**, dentro de la candidata 1.
  - Tabla de conversión:
    - el destinatario y cada allegado → `Personaje`, más su hecho de nombre;
    - cada rasgo → `Hecho(destinatario, rasgo)`;
    - cada recuerdo → `Hecho(destinatario, recuerdo)`, más su `Evento` de origen brief;
    - la relación → `Hecho(allegado, relación)`;
    - cada hecho extraído aceptado → `Hecho(sujeto, atributo, valor)`.
  - Los hechos de brief y de texto libre solo cambian por una solicitud de cambio o una edición manual del cliente.
- **§4.2:**
  - El planner entrega los antecedentes en `submit_world`.
  - Validador nuevo **`grafo-causal`**: toda consecuencia alcanzable desde el novum, orden ≤ 3 y novum anterior al año presente.
  - La compatibilidad del novum con la ocasión, el tono y el género la juzga el criterio «Tono conforme al brief».
- **§4.3:**
  - Qué cronología entra en cada pasada de Lean (ver `Cronologia`).
  - Solo los beats no analépticos ocurren en el año presente; un beat analéptico remite a su evento de trasfondo.
- **§5.1:** el evento del beat lleva todos los atributos de `Evento`; la revelación tiene tema y contenido; la tensión va de 1 a 5.
- **§5.2:**
  - Lean corre sobre el outline propuesto antes de escribir nada: el generador recibe una lista de eventos y no lee la tabla.
  - Replanificar es abrir una sesión nueva del planner, con los defectos como realimentación.
- **§5.4 y §7.7:** tres excepciones a «ningún rol escribe canon», todas aplicadas por el código:
  - el canon inicial del planner;
  - la propuesta de cambio validada;
  - el delta de una edición manual.

**Memoria**
- **§6.3–§6.4:**
  - `EstadoDelMundo` compacto (decisión 3).
  - Se separan los residentes de las entradas de la llamada.
  - En un cambio, el editor recibe el capítulo afectado entero y la propuesta estructurada.
  - La consulta del editor se construye con los defectos y el texto del capítulo.
- **§6.5:** la config se valida entera al arrancar el servidor, y cada ejecución guarda una copia.
- **§6.6:**
  - `hasta` se deriva; las copias por versión comparten los vectores por huella.
  - Se quita «los capítulos que no cambian se comparten».
  - «El editor busca» pasa a «la recuperación del editor abarca».
- **§6.9:**
  - El desempate es estable por (tipo de entidad, id de entidad, `desde`).
  - FTS5 solo da los candidatos (`MATCH`); BM25 se calcula en código sobre ellos, así que el ranking no depende de otras novelas.
  - Tokenizador `unicode61 remove_diacritics 2`.
- **§6.10:**
  - Techo por ejecución y una sola ejecución activa (decisión 1).
  - La entrada se cuenta con un estimador local antes de lanzar y se reconcilia con la entrada por turno del SDK.
  - Reserva de turnos = (`max_turns` − 1) × (`max_output` + `max_tool_output`).
  - Una sesión que supera su cuota se interrumpe y cuenta como intento fallido.
  - Las sesiones paralelas que no caben con su mínimo van en serie.
  - Causa raíz `count_drift`.
- **§6.11:** las correcciones del gate también escriben el índice, a través del registrador.
- **§6.12:**
  - Los vectores van en una tabla normal (huella, modelo, vector) y se comparan con la distancia coseno de `sqlite-vec` sobre las filas ya filtradas.
  - Las cachés de modelos van al directorio de datos.

**Harness**
- **§7.1:** «sesión de un turno» significa una sola entrega esperada; `max_turns` acota los reintentos por schema.
- **§7.2:**
  - El juez recibe también el `CatalogoDeTropos`.
  - Definir la «story bible compacta» del registrador y del juez.
  - La columna «Fase» usa el enumerado de fases.
  - El planner en modo cambio corre en el proceso de la API.
- **§7.4:** «área de trabajo» pasa a «salidas de la sesión», en la memoria del worker.
- **§7.5:**
  - Spans de tool:
    - las tools en proceso abren y cierran el suyo en su manejador;
    - las de Playwright, entre el hook de policy y un `PostToolUse` de observabilidad;
    - una denegación se registra como evento.
  - La policy solo escanea los campos de texto narrativo: capítulo, corrección, edición, mundo, reparto, outline, título y dedicatoria. Nunca los campos que son listas de prohibidas, como el `update_brief` que las registra o el léxico a evitar de la StyleSheet.
- **§7.6:**
  - `max_retries` cubre también la regeneración de respaldo, que es su propio evaluable, y cada ciclo del gate.
  - Los intentos se guardan por evaluable, dentro de cada tramo de reanudación.
  - Tipos de error:
    - un error de transporte o del proveedor, agotados los reintentos del SDK, lleva a `interrupted`;
    - una salida inválida, los turnos agotados o el tiempo agotado cuentan como intento fallido.
  - `max_agent_seconds` se aplica con `ClaudeSDKClient.interrupt()`.

**Bucle de capítulo**
- **§8.1–§8.3:**
  - El writer que regenera recibe los defectos bloqueantes.
  - `delta-declarado` solo se aplica a `submit_chapter`; las salidas del editor pasan `delta-real` tras el registrador.
  - La prosa solo escribe filas de FTS5, sin vectores.
- **§8.2:** acciones del veredicto `re_record` y `block`, para el enrutado del gate.

**Ejecuciones y versiones**
- **§9.1:**
  - Transiciones nuevas: `blocked → running` (reanudar), `blocked → cancelled` e `interrupted → cancelled`. Terminales: `finished` y `cancelled`.
  - Una ejecución activa en todo el servidor y una cola global de ejecuciones `created`. El worker lanza la siguiente al terminar; si no hay ninguna activa, la lanza la API al encolar.
  - Caídas: la API, al arrancar y al leer una ejecución `running`, comprueba el PID y la hora de arranque del proceso, y si no vive la pasa a `interrupted`.
  - Quién escribe en SQLite:
    - la API: cuentas, entrevista, brief, listas, cola, la marca de cancelación y el paso a `interrupted`;
    - el worker: su ejecución y su candidata.
- **§9.2:** puntos de control de fase; reanudar una `blocked` (decisión 11).
- **§9.3:**
  - El número se asigna al publicar; la candidata se identifica por su id y solo se rechaza al cancelar.
  - Copia por versión de story bible, capítulos, outline, StyleSheet, índice e instantáneas.
  - La generación se puede relanzar mientras no haya ninguna versión publicada.
- **§9.4:**
  - Orden: primero los validadores 1–4, y si alguno falla se enruta sin correr los demás. Después, 5–7 en paralelo, con todos los fallos enrutados juntos. Al final, el PDF y `pdf-enlaces`, que comprueba los enlaces del índice y de la ficha.
  - Toda corrección vuelve a pasar por el registrador y por la transacción de aceptación antes de repetir el gate.
  - Enrutado:
    - un elemento ausente vuelve a los capítulos que le asignó el outline;
    - el juez cita los capítulos en un campo estructurado;
    - una coincidencia prohibida en la portada o la ficha bloquea con `banned_content`.
  - Revisión visual:
    - enlaces esperados de la ficha = capítulos donde aparece la forma canónica, más los usos registrados;
    - un enlace que falta vuelve al registrador, para que vuelva a extraer los usos;
    - un capítulo vacío o sin título en la vista previa, teniendo texto y título en la base, es `fallo de render`.
  - En una ejecución de edición, un fallo que implique el capítulo editado a mano rechaza la edición.
- **§9.5, flujo de un cambio:**
  1. La policy revisa la petición: una prohibida la deniega; una inyección solo se marca y se registra.
  2. El planner interpreta en la API, con su traza y con `max_turns`, `max_output` y `max_retries` para las propuestas inválidas.
  3. El código valida la propuesta: solo puede tocar el hecho seleccionado o hechos cuyo valor aparezca en el fragmento, y el valor nuevo pasa la policy.
  4. El lector ve la propuesta: hechos que cambian, capítulos afectados y código (15 min).
  5. Al confirmar, se encola la ejecución con su versión base.
  6. Al arrancar, revalida: la cita tiene que seguir en la versión vigente y los hechos tener aún su valor antiguo. Si no, la solicitud queda `rejected` y su ejecución, `cancelled` con el motivo.
  7. El código aplica el cambio a la story bible de la candidata.
  8. El editor recibe cada capítulo afectado entero, con los párrafos numerados, y devuelve solo los que edita.
  9. El código comprueba que el valor antiguo ya no aparece.
  10. Pasan los validadores del hook, sin crítico.
  11. Si se agotan los intentos, el writer regenera ese capítulo, como evaluable propio.
  12. El registrador vuelve a registrar, se aplica la transacción y se pasa el gate.
- **§9.6, edición manual:**
  - `PUT` con la versión base: 409 si ya no es la vigente.
  - Validadores deterministas en el acto: 422 con los diagnósticos.
  - La ejecución de edición:
    - pasa el texto al registrador como dato no confiable;
    - propaga el cambio como en §9.5;
    - pasa el gate.
  - Puede cambiar hechos de origen brief, porque la hace el cliente.
- **§9.7:**
  - FastAPI sirve la lectura, con la API bajo `/api`.
  - Vista previa por token y cookie; páginas nuevas `preview` y `print`.
  - El PDF se genera al publicar desde la ruta de impresión de la candidata.

**Calidad**
- **§10.2:**
  - Los puntos de ejecución son listas.
  - Fila nueva para `grafo-causal`.
  - `schema-brief` incluye C7 y la cota de obligatorios.
  - `pdf-enlaces` corre al publicar y bloquea con `fallo de render`.
  - `harness-tla` no envía score: corre en CI.
  - La fila de `revision-visual` describe qué comprueba y qué acepta como riesgo.
- **§10.3:** catálogo de criterios con id, bloqueante y acción:
  - `active_criteria` es una lista de ids de rúbrica; los criterios programáticos no se pueden desactivar;
  - `thresholds` es un mapa de id a número;
  - un score por criterio;
  - los tropos pedidos no se penalizan.
- **§10.4:**
  - El invariante 2 cubre los hechos de brief y de texto libre, y sus cambios por solicitud de cambio o edición manual del cliente.
  - El 5 se queda sin «TLA+».
  - El 8 pasa a «ninguna versión se publica sin pasar el gate».
  - El 1 lo comprueba `grafo-causal`.
  - Se alinea el conjunto de aserciones del orquestador.
  - T1–T6 son los invariantes temporales, en `domain-knowledge.md`.
- **§10.5, Lean:**
  - Fechas de calendario desplazadas un múltiplo de 400 años, con los ids de las filas.
  - Los tipos incluyen capítulo y beat.
  - Cada comprobador devuelve el primer testigo en JSON.
  - Protocolo remoto:
    - `workflow_dispatch` con la entrada comprimida en gzip y base64 (límite de 65.535 caracteres), `return_run_details: true` y la versión de la API fijada;
    - sondeo de la ejecución y artefacto con el resultado;
    - `max_verifier_seconds` agotado → `interrupted`.
  - Seguridad del workflow:
    - compilación con `--wfail` y auditoría de axiomas, porque un `sorry` pasa `lake build`;
    - el job solo tiene `contents: read`;
    - los inputs llegan por variables de entorno.
- **§10.6, TLA+:**
  - Los tres módulos, con el modelo pequeño.
  - Invariantes del código de confirmación: un solo uso, caducidad y propietario.
  - Se modelan las reanudaciones de `blocked`.
  - El diagrama completo de la máquina de estados se añade con la spec 006.
  - La tabla de correspondencia va en el README de la raíz. Corregir la fila de §16, que dice `tla/`.
- **§10.7:** Langfuse admite crear colas de anotación e ítems por API (el plan Hobby permite una cola). Acuerdo por criterio = diferencia absoluta media más tasa de acuerdo exacto.
- **§10.8:**
  - Las evals incluyen cambios reales del lector: miden el coste de una revisión y sirven de demo de la propagación.
  - Coste de una novela = entrevista + ejecución de generación. Una revisión es una solicitud de cambio.

**Guardarraíles**
- **§11.1:** C6 con los tres niveles y la dedicatoria; una sola tabla de prohibidas con el nivel; copia por ejecución; la siembra global sale de una lista propia en `domain`.
- **§11.2:** «sin tools integradas salvo las de su lista»; modo de permisos que deniega lo no preaprobado.
- **§11.3:** descarte de los hechos cuya cita se solape con una frase marcada; el detector no deniega; el texto de una edición manual es no confiable.
- **§11.4:** las columnas del audit log y lo que además registra (ver `DecisionDePolitica`).
- **§11.5:** el coste sale de `operation.pricing` por el uso exacto; el techo se aplica a cada ejecución y a cada entrevista; se contrasta con OpenRouter en la evaluación.
- **§11.6:** el directorio de configuración del CLI del SDK (`CLAUDE_CONFIG_DIR`, sin confirmar), las cachés de modelos y la salida de Playwright MCP del revisor visual van dentro del directorio de datos.

**Observabilidad**
- **§12:** con el SDK de Langfuse v4:
  - `start_as_current_observation` y `propagate_attributes`, cuyos valores deben ser ASCII;
  - `usage_details` y `cost_details` en las generaciones;
  - las trazas de `Traza`; la reanudada conserva la suya;
  - scores por criterio, copiados en SQLite;
  - cada traza lleva el commit y la huella de la config;
  - la máscara por novela;
  - los prompts, según la decisión 7; si Langfuse no responde al abrir una sesión → `interrupted`;
  - la prueba de lectura de vuelta reintenta, porque la ingesta tarda de 15 a 30 s;
  - `harness-tla` no envía score.

**Plataforma**
- **§13.1:** JWT de 24 h con HS256 y `exp`, `aud` e `iss`; tabla de códigos de estado.
- **§13.2:**
  - FastMCP se monta con su lifespan y valida con `JWTVerifier` HS256; la identidad se lee con `get_access_token()`.
  - Las tools de lectura no modifican nada y las de escritura encolan con confirmación (15 min, un solo uso).
  - `request_change` hace la interpretación, con su propia traza.
  - `download_novel` devuelve el PDF como recurso incrustado.
  - Una traza por llamada; con varias novelas, la máscara es la unión de las suyas.
  - El README explica cómo pasa el token cada cliente. Sin confirmar para Claude Desktop, quizá mediante `mcp-remote`.
  - La versión de FastMCP se fija.
- **§13.3:** los umbrales son criterios; objetivos de legibilidad por franja; listas propias.
- **§13.4, linter en vivo:** comprueba prohibidas, nombres no canónicos, personajes desconocidos, valores sustituidos de un hecho, los dos avisos de cronología y los avisos de los linters.
  - Una variante de nombre es la misma forma normalizada con otra forma literal.
  - Retardo entre pulsaciones. No registra en el audit log por pulsación; al guardar, sí.
- **§13.5:** secretos de todo el historial con `detect-secrets` sobre un volcado de `git log -p --all`.
- **§13.6:** páginas nuevas `preview` y `print`.

**Stack y API**
- **§14.1:**
  - Alembic.
  - La traducción de la clave de OpenRouter al entorno del SDK.
  - En Windows, uvicorn sin `--reload`: el bucle `Selector` no puede lanzar subprocesos.
  - Versiones verificadas el 2026-09-23 (en §3); se fijan en el design de la spec 001.
- **§14.2:**
  - Las piezas del bucle que usan varias fases viven en `harness`: la sesión del editor, el registrador y la aceptación. La transacción vive en `store`.
  - Regla nueva: `platform` no importa `domain`.
  - La CLI está en `execution`.
- **§14.3:**
  - La API va bajo `/api`, con `position` y `/brief/extracted-facts/{id}`.
  - Endpoints nuevos:
    - `POST /novels/{id}/change-requests` → propuesta;
    - `POST /change-requests/{id}/confirm {code}` → 202 `{run_id, position}`;
    - `GET /change-requests/{id}`;
    - `GET /novels/{id}`, con la ejecución activa;
    - `GET /novels/{id}/interview/messages`;
    - `GET /novels/{id}/runs`;
    - lectura de la vista previa.
  - Cambios en endpoints existentes:
    - `PUT /novels/{id}/chapters/{n} {text, version}` → 202, 409 o 422;
    - reanudar desde `blocked` o `interrupted`;
    - `DELETE` también sobre esos dos estados;
    - `?version=` en la story bible.
  - Tabla de códigos de estado por endpoint.
- **§14.4:** una sola ejecución activa: la API y un worker. El SSE son instantáneas leídas de SQLite y el cliente las pide con `fetch` y cabecera de autorización.
- **§14.5, sección nueva, «Esquema SQLite»:** diagrama Mermaid `erDiagram` de las tablas, con su ámbito (usuario, novela, versión, ejecución o global) y cuáles solo admiten inserciones. El detalle por columna va a `specs/001-base/design.md`. El encargo pide este diagrama en `/docs`, y `CLAUDE.md` y el README ya apuntan aquí.

**Decisiones**
- **§15.2:** añadir `readability_targets`, `max_verifier_seconds` y `max_tool_output`. `pricing` es un dato de OpenRouter, no una cifra por calibrar, y se rellena con su tabla. Las caducidades ya tienen valor.
- **§15.3, comprobaciones de entorno que quedan:**
  - el CLI empaquetado bajo Smart App Control;
  - el SDK contra OpenRouter con tools en proceso, hooks, la skill, el workspace y `CLAUDE_CONFIG_DIR`;
  - spaCy, `sqlite-vec` y `onnxruntime`;
  - Playwright con Edge sin interfaz, incluidos `page.pdf` y Playwright MCP desde una sesión del SDK;
  - uvicorn con subprocesos;
  - la latencia del workflow de Lean (estimación: 1–3 min);
  - que los ids de mensaje de OpenRouter empiezan por `gen-`.
- **§16:**
  - Una fila por cada decisión de §1, más el versionado por copia, el número al publicar y la seudonimización por desplazamiento.
  - Corregir «Los seis de §5.3» por «de `domain-knowledge.md` §5.3».
  - Actualizar la fila de reanudación.

### 2.4 `verification.md`

- **§3.6:**
  - Invariante 1: el validador acepta el grafo **si y solo si** toda consecuencia es alcanzable.
  - La seudonimización es inyectiva y conserva los órdenes y las edades.
- **§4.2:**
  - Métricas del writer y del editor, sacadas de los datos de ejecución: aceptación al primer intento, y defectos resueltos por corrección.
  - El conjunto dorado del registrador incluye los arcos resueltos y los atributos de evento.
  - «La eval de cada validador semántico es su calibración».
  - Cambios reales, protocolo de coste y resultados al final.
- **§4.3:** pasa a clase T y se quita `disallowed_tools`.
- **§4.4:** los guardarraíles pasan a clase T.
- **§4.9:**
  - La edición manual entra en el modelo de amenaza.
  - Lo esperado en RT2 sigue la regla de la selección.
  - Columnas «Detector esperado» y «Detectado por», que se rellena al probar.
- **§4.10:** invariantes de `Regenerations.tla` y de `Confirmation.tla`.
- **§5, filas que faltan:**
  - el gate, `elementos-obligatorios` y `arcos-cerrados`;
  - los invariantes 2 y 3;
  - `schema-salida`, `delta-real`, `outline`, `grafo-causal` e `inyeccion-detectada`;
  - el planner;
  - los capítulos afectados, el enrutado del gate y la regeneración de respaldo;
  - el informe, la edición manual y el linter en vivo;
  - la validación de la config, el frontend, `Confirmation.tla` y la CLI.
  - Además, clases coherentes con §3–§4.
- **§6, riesgos nuevos:**
  - la estética de la revisión visual;
  - la retención de datos en OpenRouter: activar la retención cero en la cuenta;
  - la visibilidad de los inputs y los logs de GitHub;
  - los límites del plan Hobby de Langfuse;
  - las variantes de nombre, que solo detecta la normalización («Tobi» se escapa);
  - los avisos temporales del linter en vivo, que son solo avisos.
- **§8, filas nuevas:**
  - el coste desde `pricing`, porque el SDK estima con precios de Anthropic;
  - las fechas desplazadas en Lean, porque con minutos no se calculan edades;
  - uvicorn sin `--reload` en Windows.

### 2.5 Otros ficheros

- **ADR 0004** (sin commitear; se puede editar): minutos relativos → fechas desplazadas un múltiplo de 400 años; el protocolo remoto; la seguridad del workflow.
- **`config.json`:** las claves nuevas de §2.1, sin valor salvo las dos caducidades.
- **`.env.example`**, solo con marcadores de posición:
  - `STORY_MAKER_DATA_DIR`, `STORY_MAKER_CONFIG`;
  - `FORMAL_VERIFIER=github`, `GITHUB_REPOSITORY=owner/repo`, `LEAN_WORKFLOW=lean-verify.yml`;
  - `JWT_SECRET` (32 caracteres o más), `LANGFUSE_PROMPT_LABEL=production`;
  - las que ya hay.
  - Una nota: el backend traduce `OPENROUTER_API_KEY` al entorno del SDK.
  - `GITHUB_TOKEN` es de grano fino: Actions de lectura y escritura, y Metadata de lectura.
- **README:** `presentation/` es la `/presentacion/` del encargo; corregir «Planned…».
- **No toques `.claude/skills/README.md`, `.mcp.json` ni `.claude/`.** Los lleva otro chat.

## 3. Hechos verificados

Verificados el 2026-09-23, con fuentes. Entran en los docs como hechos; el detalle de librería va al design de cada spec.

- **Versiones:** `claude-agent-sdk` 0.2.158, `langfuse` 4.15.4, `fastmcp` 4.0.5 (salió hace tres semanas), `playwright` 1.63.0, `leanprover/lean-action` v1.6.0, Lean v4.34.0.
- **Agent SDK:**
  - Empaqueta el CLI de Claude Code y lo ejecuta como subproceso.
  - `tools=[]` desactiva las tools integradas.
  - `CLAUDE.md` y las skills se cargan con `setting_sources=["project"]`, aunque el prompt de sistema sea propio. Con `tools` explícitas, hay que incluir `Skill`.
  - `PreToolUse` deniega con `permissionDecision: "deny"` y un motivo. `PostToolUse` solo puede añadir contexto o reemplazar la salida (`updatedToolOutput`).
  - `AssistantMessage` trae `message_id` y el uso por turno; el `output_tokens` de cada paso es provisional.
  - `ResultMessage` trae el uso exacto y un `total_cost_usd` estimado.
  - `ClaudeSDKClient.interrupt()` existe.
  - `max_turns` existe; no hay tiempo máximo.
- **OpenRouter:**
  - Base `https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN` y `ANTHROPIC_API_KEY=""` explícitamente vacío.
  - Admite tools, streaming y caché.
  - El coste facturado está en `GET /api/v1/generation?id=<id>`, que da 404 hasta que se procesa.
  - Con modelos que no son de Anthropic, OpenRouter avisa de que Claude Code puede fallar.
- **Langfuse v4:**
  - `start_as_current_observation(as_type=...)`; `propagate_attributes(session_id, trace_name…)` con valores ASCII de 200 caracteres como mucho.
  - El coste ingerido tiene prioridad sobre el que Langfuse infiere.
  - `mask` (heredado) o `mask_otel_spans`; `auth_check()` lanza una excepción si falla.
  - `create_score` con `data_type`; `/api/public/v2/observations`.
  - Colas de anotación por API. Plan Hobby: 50k unidades al mes y 30 peticiones por minuto.
- **FastMCP 4:**
  - `mcp.http_app()` con su lifespan obligatorio.
  - `JWTVerifier` admite HS256; la identidad sale de `get_access_token()`.
  - `File(format="pdf")` devuelve el PDF incrustado.
- **GitHub Actions:**
  - `return_run_details: true` devuelve el id de la ejecución.
  - Los inputs admiten 65.535 caracteres en total.
  - Los logs y artefactos se descargan con redirecciones que caducan en 1 minuto.
  - PAT mínimo: Actions de lectura y escritura y Metadata de lectura.
- **Playwright:** `page.pdf(outline=True, tagged=True)` existe desde la 1.42 y funciona con `channel="msedge"`.

## 4. Fase 1: aplicar a los docs

1. **Lee `CLAUDE.md`** y los cuatro docs enteros.
2. **Aplica §2.1 en `definitions.md` tú mismo.** Es la autoridad de nombres: todo lo demás usa sus términos.
3. **Lanza tres subagentes en paralelo**, cada uno con este fichero y su parte:
   - `architecture.md` (§2.3 y las filas de §16);
   - `verification.md` (§2.4);
   - `domain-knowledge.md`, ADR 0004, `config.json`, `.env.example` y el README (§2.2 y §2.5).

   Cada uno usa los nombres de `definitions.md` tal como quedaron. Ninguno toca un fichero de otro.
4. **Escribe tú `architecture.md` §14.5** (esquema) cuando termine el subagente de arquitectura.
5. **Lanza un subagente auditor de solo lectura** sobre los cuatro docs y el ADR. Que busque:
   - contradicciones entre docs;
   - términos sin definir;
   - referencias rotas entre secciones;
   - requisitos del encargo sin cubrir.

   Corrige lo que encuentre.
6. **Añade a `verification.md` §9.4** la fila de los subagentes de este chat.

**Fase 1 terminada** cuando cada punto de §1 y §2 esté aplicado en su sección, §16 tenga su fila por decisión y el auditor no encuentre contradicciones.

## 5. Fase 2: las specs

Proceso: [`workflow/2-specs.md`](../workflow/2-specs.md).

> **Actualización:** la fase 2 ya no la hace este chat. Se reparte en chats paralelos desde [`.scratch/v1/tablero.md`](v1/tablero.md), y la matriz es `docs/relational-matrix.md` (gap plan–arquitectura, [proceso 3](../workflow/3-plan.md)), no `docs/relation-matrix.md`.

- **Una ronda de grill por spec**, hasta cuatro specs por llamada a `AskUserQuestion`. Pregunta solo lo que los docs no decidan todavía: alcance, fronteras, qué se rechaza y qué queda fuera.
- **Todo el encargo cuenta como Obligatorio**, incluidos sus opcionales.
- **Dependencias:** cada requisito vive en una sola spec; las specs se citan entre sí por número.

Orden de implementación, con el código de módulo de cada una:

| # | Carpeta | MÓD | Qué entrega |
|---|---|---|---|
| 001 | `001-base` | BAS | Stack, módulos y regla de dependencia, store con Alembic, config y ajustes, puerto de agente con su doble, workspace, índice, CLI mínima, CI, frontend base con tema corporativo y cliente generado, comprobaciones de entorno (D). `design.md` con el esquema por columna |
| 002 | `002-aut-autenticacion` | AUT | Registro, acceso, JWT de 24 h y propiedad (404) |
| 003 | `003-pol-politica-y-guardarrailes` | POL | Prohibidas en tres niveles, normalización, motor de políticas, lista blanca, audit log, detector de inyección |
| 004 | `004-obs-observabilidad` | OBS | Langfuse: sesiones, trazas, spans, generaciones con coste, scores, prompts sincronizados, máscara, `auth_check`, lectura de vuelta |
| 005 | `005-ent-entrevista-y-brief` | ENT | Entrevistador, extractor, citas, C1–C7, brief importado, página de entrevista |
| 006 | `006-tla-especificacion-del-harness` | TLA | `Harness.tla`, `Regenerations.tla`, `Confirmation.tla`, TLC en CI y diagrama en §10.6 |
| 007 | `007-run-ejecuciones` | RUN | Ciclo de vida, worker, cola global, SSE, caídas, reanudación, límites, presupuesto, informe, aserciones |
| 008 | `008-mem-memoria` | MEM | Índice, recuperador, residentes, cuotas, guardián de ventana, conteo, trazabilidad |
| 009 | `009-lea-validador-formal-de-la-historia` | LEA | Biblioteca Lean con demostraciones y negativos, generador del fichero, verificador local y remoto, traducción del testigo |
| 010 | `010-pln-planificacion` | PLN | Planner, `grafo-causal`, outline, Lean al congelar, StyleSheet, canon inicial, catálogo de tropos |
| 011 | `011-cap-produccion-por-capitulo` | CAP | Writer, hooks, crítico, editor, registrador, veredicto, aceptación, skill `personalizacion-natural` |
| 012 | `012-lin-linters-de-prosa` | LIN | Los cuatro linters con spaCy, como criterios |
| 013 | `013-lec-lectura-web-y-pdf` | LEC | Lectura web, vista previa, ruta de impresión, PDF y `pdf-enlaces` |
| 014 | `014-pub-publicacion-y-versiones` | PUB | Gate, versiones, juez, revisor visual con Playwright MCP |
| 015 | `015-cam-cambios-y-edicion-manual` | CAM | Solicitudes de cambio, edición dirigida, respaldo, edición manual y linter en vivo |
| 016 | `016-mcp-servidor-mcp` | MCP | FastMCP, tools de lectura y de escritura con confirmación, README de conexión |
| 017 | `017-evl-evaluacion-del-sistema` | EVL | Cinco briefs, evals de rol, tabla, ajuste, revisión humana, cambios reales, coste por novela y por revisión, novela de ejemplo |
| 018 | `018-sec-auditoria-de-seguridad` | SEC | Subagente, skill y comando de auditoría; `docs/security-report.md` |

**Durante la fase 2:**
- Borra con `git rm -r` las carpetas antiguas de `specs/` (001–011, del producto anterior) antes de crear las nuevas.
- La cobertura y los huecos van en `docs/relational-matrix.md`, que se queda.
- Cuando la fase 2 termine, borra este fichero.
- Deja sin marcar las casillas de aprobación. Al terminar, pide al usuario que las marque. Ningún `plan.md` se escribe antes de eso.

## 6. Hecho cuando

- Los cuatro docs y el ADR 0004 reflejan §1–§3 sin contradicciones.
- Cada elemento de `project-constraints.md` tiene sección en los docs y RF en una spec.
- Existen las 18 specs, con sus casillas sin marcar, y las antiguas están borradas.
- Este fichero está borrado.
- `verification.md` §9.4 tiene las filas de los subagentes usados.
