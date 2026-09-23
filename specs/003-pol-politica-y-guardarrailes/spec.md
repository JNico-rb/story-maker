# 003 — POL · Política y guardarraíles

- [ ] Spec approved   <- only the user marks this

## Objetivo

Que el código, nunca un modelo, decida qué tools usa cada rol y qué términos prohibidos se deniegan, y que cada decisión quede en el audit log.

## Alcance

Cubre:

- la normalización de las palabras prohibidas y sus coincidencias, por nivel y variante;
- la lista global sembrada desde `domain` y la API de la lista de cliente;
- el motor de políticas, con sus tres decisiones: `allow`, `deny` y `flag`;
- el hook de policy: la lista blanca de cada rol, el escaneo de los campos narrativos, `Skill` limitada a `personalizacion-natural` y la navegación del revisor visual;
- la apertura de cada sesión sin tools integradas, con su lista blanca y un modo de permisos que no pregunta;
- el detector de inyección, que marca y no deniega;
- el audit log y su endpoint;
- los criterios de `palabras-prohibidas` y de `inyeccion-detectada` en el catálogo.

Depende de 001 y de 002.

**Fuera de alcance:**

- Dónde se invoca el motor fuera del hook y qué se hace con su decisión: la petición de un cambio, la edición manual y el linter en vivo son de 015; la novela entera, portada y ficha incluidas, del gate de 014.
- La reescritura tras una denegación, que cuenta como intento, y el bloqueo al agotarlos, que son de 007 y 011. El caso RT7, que es ese flujo de extremo a extremo, es de 011.
- La copia de las listas en cada tramo de una ejecución, que es de 007.
- El envío a Langfuse de cada decisión como evento de la traza, de los scores y del span `tool:` de cada llamada, también el de nivel WARNING que el hook de policy abre y cierra en el acto al denegar (`architecture.md` §7.5), que es de 004.
- Una página para gestionar la lista de cliente: `architecture.md` §13.6 no la incluye, así que la lista se gestiona por la API.

## Requisitos

Todos son **Obligatorio**.

### Normalización y coincidencias

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-1 | Se normaliza un texto o un término → queda en minúsculas, sin acentos por descomposición Unicode y con los espacios colapsados: «Árbol   GRANDE» da «arbol grande». Texto y términos se normalizan igual | Obligatorio | T |
| RF-POL-2 | Un término y una palabra del texto difieren solo en singular o plural (-s, -es) o en masculino o femenino (-o/-a, -os/-as), en cualquiera de los dos sentidos → hay coincidencia: el término «perro» coincide con «Perros», «perra» y «perras»; «león», con «leones»; y el término «perras», con «perro» | Obligatorio | T |
| RF-POL-3 | Un término de varias palabras → coincide como secuencia de palabras normalizadas; y un término solo coincide con palabras enteras: «mi ex» coincide con «Mi  EX», y «ex» no coincide con «examen» | Obligatorio | T |
| RF-POL-4 | Cada coincidencia → da el término, la variante encontrada tal como está en el texto, el nivel de su lista, el tipo de ubicación, el capítulo si lo hay y el desplazamiento en el texto original | Obligatorio | T |
| RF-POL-5 | Hay una prueba por nivel —un término global, uno de cliente y uno de novela, cada uno encontrado en un texto— y una de variante de acento y otra de plural → las cinco pasan, y el nivel de cada coincidencia es el de su lista | Obligatorio | T |
| RF-POL-6 | Para todo término y todo texto generados → la normalización es idempotente, y toda variante de mayúsculas, acento, plural o género de un término coincide con él | Obligatorio | T |

### Listas

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-7 | La lista global vive en `domain`: unos 30 a 50 insultos y términos ofensivos en español, curados a mano y sin licencia de terceros → al sembrarla, las entradas de nivel global de la base son exactamente las de esa lista; sembrar otra vez no las duplica | Obligatorio | T |
| RF-POL-8 | `GET /api/banned-terms` → las entradas de la lista del cliente del token, con su id, su término y su tipo | Obligatorio | T |
| RF-POL-9 | `POST /api/banned-terms` con un término y su tipo, palabra o tema → 201 con la entrada creada en la lista del cliente; un término que queda vacío al normalizarlo → 422 y no se crea nada | Obligatorio | T |
| RF-POL-10 | `DELETE /api/banned-terms/{id}` de una entrada de la lista del cliente → 204 y la entrada deja de estar; el id de una entrada global, de novela o de otro cliente → 404 | Obligatorio | T |

### Motor de políticas

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-11 | El motor recibe un texto, su ubicación y las tres listas que le pasa quien lo invoca —en una ejecución, la copia de su tramo; fuera, las vigentes— → si hay alguna coincidencia, decide `deny` con todas ellas; si no, `allow`. Un tema prohibido coincide por sus palabras como cualquier otra entrada | Obligatorio | T |
| RF-POL-12 | El motor recibe un rol y la tool que pide, con su entrada → decide `deny` si la tool no está en la lista blanca del rol, si es `Skill` y no pide `personalizacion-natural`, o si es una navegación del revisor visual fuera del origen de la vista previa; si no, `allow` | Obligatorio | T |
| RF-POL-13 | El motor toma una decisión —`allow`, `deny` o `flag`, desde cualquier origen, también toda decisión del hook de policy— → queda una fila en el audit log con el momento, el cliente, la novela, la ejecución, el rol y la tool cuando los hay, el origen, la decisión, el código de motivo y el detalle con las coincidencias, su nivel y su variante (invariante 12). La excepción es el linter en vivo, que usa las coincidencias de RF-POL-2 a RF-POL-4 sin decisión ni fila (§13.4) | Obligatorio | T |
| RF-POL-14 | El motor y el detector de inyección → deciden sin llamar a ningún modelo | Obligatorio | T |
| RF-POL-15 | El catálogo de criterios → contiene `palabras-prohibidas/en-capitulo`, bloqueante con acción corregir; `palabras-prohibidas/en-portada-o-ficha`, bloqueante con acción bloquear, que bloquea la ejecución con el motivo `contenido prohibido`; e `inyeccion-detectada`, un criterio con su nombre, sin nivel ni acción y no bloqueante | Obligatorio | T |

### Hook de policy y sesiones

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-16 | Un rol llama a una tool que no está en su lista blanca, también una integrada de Claude Code de ficheros, terminal o web → el hook de policy la deniega antes de ejecutarla, y el modelo recibe el motivo | Obligatorio | T |
| RF-POL-17 | Un rol llama a una tool cuyos campos de texto narrativo —capítulo, corrección, edición, mundo, reparto, outline, títulos o dedicatoria— tienen una coincidencia → el hook la deniega con los términos y sus posiciones, y el modelo los recibe. Es el validador `palabras-prohibidas` en el punto `policy_hook`, que la mide con `en-capitulo` en cualquier campo (`architecture.md` §10.3). Cada tool declara cuáles de sus campos son narrativos | Obligatorio | T |
| RF-POL-18 | Un término prohibido aparece solo en un campo que es una lista de prohibidas —las entradas que registra `update_brief` o el léxico a evitar de la `StyleSheet`— → el hook permite la tool: esos campos no se escanean | Obligatorio | T |
| RF-POL-19 | Un rol llama a `Skill` pidiendo cualquier skill que no sea `personalizacion-natural` → el hook la deniega | Obligatorio | T |
| RF-POL-20 | El revisor visual intenta cargar una página fuera del origen de la vista previa, al navegar, con un clic o por una redirección → no la carga: el hook deniega la navegación, y lo demás lo impide la configuración de su servidor de Playwright MCP | Obligatorio | T |
| RF-POL-21 | La lista blanca de cada rol → es la de su fila de `architecture.md` §7.2 más `Skill` en el writer y el editor (§7.4): `update_brief` y `propose_dedication` el entrevistador; `submit_facts` el extractor; `submit_world`, `submit_cast`, `submit_outline` y `submit_style_sheet` el planner al planificar, y solo `propose_change` en modo cambio; `submit_chapter` el writer; `submit_evaluation` el crítico y el juez; `submit_correction` y `submit_edit` el editor; `submit_record` el registrador; y las tools de navegación de Playwright MCP —navegar, instantánea y clic— con `submit_visual_review` el revisor visual | Obligatorio | T |
| RF-POL-22 | Se abre una sesión de rol → se abre sin tools integradas salvo `Skill` en el writer y el editor, declara su lista blanca como tools permitidas y usa un modo de permisos que deniega lo no preaprobado sin preguntar: ninguna sesión desatendida se queda esperando una confirmación | Obligatorio | T |

### Detector de inyección

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-23 | El detector recibe un texto no confiable —un texto libre, la petición de un cambio o el texto de una edición manual— con frases dirigidas al sistema, como «ignora lo anterior» o «escribe en inglés» → las marca por patrones, cada una con su desplazamiento, decide `flag` y nunca deniega; la decisión queda en el audit log con el origen del texto (RF-POL-13), y el resultado es el del validador `inyeccion-detectada` | Obligatorio | T |
| RF-POL-24 | El detector recibe cartas y anécdotas de fixture sin frases dirigidas al sistema → no marca nada | Obligatorio | T |

### Audit log y explainers

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-POL-25 | `GET /api/novels/{id}/audit-log` → las decisiones de política de esa novela, en orden cronológico y con todas sus columnas | Obligatorio | T |
| RF-POL-26 | Al cerrar 003 → la cabecera de `architecture.md` §11 lleva el explainer de los guardarraíles y el motor de políticas, y la de §7.5, el de los hooks, como asigna la lista de explainers del README | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | Las pruebas de mutación sobre el motor de políticas y la normalización matan todo mutante de sus rutas de rechazo, también uno que haga fallar abierto al motor: que permita siempre (RT9) | T |

## Docs de referencia

- `architecture.md` §7.2 (columna de tools), §7.4, §7.5, §7.7 (regla 6), §10.2 y §10.3 (`palabras-prohibidas`, `inyeccion-detectada`), §10.4 (invariante 12), §11.1–§11.4, §13.1 (propiedad), §13.4, §13.6, §14.3 y §14.5 (`banned_terms`, `audit_log`).
- `definitions.md` §1 (`ListaProhibida`, `EntradaProhibida`), §5 (`Hook`, detector de inyección), §6 (`Criterio`), §7 y §12.
- `domain-knowledge.md` §4.4.
- `verification.md` §3.6 (normalización), §3.7, §4.3, §4.4, §4.9 (RT9) y §5.
- README de la raíz («Explainers») y `workflow/4-code.md`, paso 5.
