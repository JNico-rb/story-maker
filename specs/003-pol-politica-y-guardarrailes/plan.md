# 003 — POL · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: unitarias por nivel y variante, propiedades y mutación, «Motor de políticas y normalización de prohibidas»; unitarias del detector, «Detector de inyección»; integración con el doble, «Lista blanca de tools por rol y sandbox»; y pruebas del motor en cada origen, «Invariante 12 — audit log» (`docs/verification.md` §5).

### Steps
- [ ] Se normaliza un texto o un término → queda en minúsculas, sin acentos por descomposición Unicode y con los espacios colapsados: «Árbol   GRANDE» da «arbol grande». Texto y términos se normalizan igual (RF-POL-1)
  - «Sin acentos» quita la tilde y la diéresis de las vocales, no la de la «ñ», que es otra letra: «año» no se convierte en «ano», ni «coño» en «cono».
- [ ] Un término y una palabra del texto difieren solo en singular o plural (-s, -es) o en masculino o femenino (-o/-a, -os/-as), en cualquiera de los dos sentidos → hay coincidencia: el término «perro» coincide con «Perros», «perra» y «perras»; «león», con «leones»; y el término «perras», con «perro» (RF-POL-2)
- [ ] Un término de varias palabras → coincide como secuencia de palabras normalizadas; y un término solo coincide con palabras enteras: «mi ex» coincide con «Mi  EX», y «ex» no coincide con «examen» (RF-POL-3)
- [ ] Cada coincidencia → da el término, la variante encontrada tal como está en el texto, el nivel de su lista, el tipo de ubicación, el capítulo si lo hay y el desplazamiento en el texto original (RF-POL-4)
  - El desplazamiento es el del texto original, no el del normalizado: la prueba pone acentos, mayúsculas y espacios repetidos antes de la coincidencia, y la variante que devuelve es el trozo del original en ese desplazamiento.
  - Los tipos de ubicación son los de `definitions.md` §12: `chapter`, `cover`, `sheet`, `request`, `edit` y `tool_field`.
- [ ] Para todo término y todo texto generados → la normalización es idempotente, y toda variante de mayúsculas, acento, plural o género de un término coincide con él (RF-POL-6)
  - Pruebas basadas en propiedades (`verification.md` §3.6). El generador de variantes de acento pone y quita tildes y diéresis en las vocales, nunca en la «ñ».
- [ ] La lista global vive en `domain`: unos 30 a 50 insultos y términos ofensivos en español, curados a mano y sin licencia de terceros → al sembrarla, las entradas de nivel global de la base son exactamente las de esa lista; sembrar otra vez no las duplica (RF-POL-7)
  - La siembra va en la orden de migrar de 001, que ya se puede repetir (RF-BAS-6). Cada entrada guarda el término y su forma normalizada, en la columna `normalized` de `banned_terms` (001 design.md §4).
- [ ] Hay una prueba por nivel —un término global, uno de cliente y uno de novela, cada uno encontrado en un texto— y una de variante de acento y otra de plural → las cinco pasan, y el nivel de cada coincidencia es el de su lista (RF-POL-5)
  - El término global sale de la lista sembrada. Las entradas de nivel novela las crea el brief (005); aquí la prueba las inserta en `banned_terms`.
- [ ] El motor recibe un texto, su ubicación y las tres listas que le pasa quien lo invoca —en una ejecución, la copia de su tramo; fuera, las vigentes— → si hay alguna coincidencia, decide `deny` con todas ellas; si no, `allow`. Un tema prohibido coincide por sus palabras como cualquier otra entrada (RF-POL-11)
  - En 003 las listas se las pasa la prueba; la copia de cada tramo es de 007.
- [ ] El motor recibe un rol y la tool que pide, con su entrada → decide `deny` si la tool no está en la lista blanca del rol, si es `Skill` y no pide `personalizacion-natural`, o si es una navegación del revisor visual fuera del origen de la vista previa; si no, `allow` (RF-POL-12)
  - Recibe la tool con el nombre que ve el hook: `mcp__<servidor>__<tool>` para las tools en proceso y las de Playwright MCP, y el nombre de la integrada para las de Claude Code (001 design.md §5.1). La skill pedida es el campo `skill` de la entrada de `Skill` (unsure: en el CLI que empaqueta el SDK 0.2.158; lo confirma una sesión real, como la de RF-BAS-41).
  - La navegación es `browser_navigate`. El origen es esquema, host y puerto; el de la vista previa se lo pasa quien abre la sesión del revisor visual (014).
- [ ] El motor toma una decisión —`allow`, `deny` o `flag`, desde cualquier origen, también toda decisión del hook de policy— → queda una fila en el audit log con el momento, el cliente, la novela, la ejecución, el rol y la tool cuando los hay, el origen, la decisión, el código de motivo y el detalle con las coincidencias, su nivel y su variante (invariante 12). La excepción es el linter en vivo, que usa las coincidencias de RF-POL-2 a RF-POL-4 sin decisión ni fila (§13.4) (RF-POL-13)
  - La prueba recorre los seis orígenes: `policy_hook`, `free_text`, `change_request`, `manual_edit`, `publication_gate` y `mcp_write`. Llama al motor como lo harán 005, 014, 015 y 016, que prueban cada uno su propia llamada.
  - La tool va en la fila sin el prefijo `mcp__<servidor>__` (001 design.md §5.1).
  - Buscar coincidencias sin pedir decisión, como hará el linter en vivo de 015, no deja ninguna fila.
- [ ] El motor y el detector de inyección → deciden sin llamar a ningún modelo (RF-POL-14)
  - La prueba corre el motor y el detector sobre todas sus entradas de prueba con un puerto de agente que falla ante cualquier llamada.
- [ ] El catálogo de criterios → contiene `palabras-prohibidas/en-capitulo`, bloqueante con acción corregir; `palabras-prohibidas/en-portada-o-ficha`, bloqueante con acción bloquear, que bloquea la ejecución con el motivo `contenido prohibido`; e `inyeccion-detectada`, un criterio con su nombre, sin nivel ni acción y no bloqueante (RF-POL-15)
  - Los criterios entran en el catálogo de 001 (RF-BAS-14), que falla si un id se repite. El bloqueo con `banned_content` lo aplica el gate de 014; aquí se prueba lo que declara el criterio.
- [ ] `GET /api/banned-terms` → las entradas de la lista del cliente del token, con su id, su término y su tipo (RF-POL-8)
  - Ni las globales ni las de novela, ni las de otro cliente. Es una lista, así que entra en el recorrido de RF-AUT-9 de 002.
- [ ] `POST /api/banned-terms` con un término y su tipo, palabra o tema → 201 con la entrada creada en la lista del cliente; un término que queda vacío al normalizarlo → 422 y no se crea nada (RF-POL-9)
  - La entrada queda a nombre del cliente del token (RF-AUT-7), con su forma normalizada. Un tipo que no es `word` ni `topic` es el 422 de schema de 001.
- [ ] `DELETE /api/banned-terms/{id}` de una entrada de la lista del cliente → 204 y la entrada deja de estar; el id de una entrada global, de novela o de otro cliente → 404 (RF-POL-10)
  - La ruta entra en el recorrido de RF-AUT-8 de 002: 003 añade al fixture del cliente A una entrada de su lista.
- [ ] `GET /api/novels/{id}/audit-log` → las decisiones de política de esa novela, en orden cronológico y con todas sus columnas (RF-POL-25)
  - La ruta entra en el recorrido de RF-AUT-8 de 002: 003 añade al fixture del cliente A una novela con decisiones en el audit log, insertada por el store porque `POST /api/novels` es de 005.
- [ ] El detector recibe un texto no confiable —un texto libre, la petición de un cambio o el texto de una edición manual— con frases dirigidas al sistema, como «ignora lo anterior» o «escribe en inglés» → las marca por patrones, cada una con su desplazamiento, decide `flag` y nunca deniega; la decisión queda en el audit log con el origen del texto (RF-POL-13), y el resultado es el del validador `inyeccion-detectada` (RF-POL-23)
  - El origen es `free_text`, `change_request` o `manual_edit`, y el detalle lleva las frases marcadas (001 design.md §4). Entre las entradas de prueba van las frases de RT1 y RT10 (`verification.md` §4.9); esos casos de extremo a extremo son de 005 y de 015.
  - Sin frases marcadas no hay decisión de marcar, así que no queda fila (`architecture.md` §11.3).
- [ ] El detector recibe cartas y anécdotas de fixture sin frases dirigidas al sistema → no marca nada (RF-POL-24)
  - Entre ellas, frases corrientes que comparten palabras con los patrones sin dirigirse al sistema, como «ignoró lo que le dijeron».
- [ ] La lista blanca de cada rol → es la de su fila de `architecture.md` §7.2 más `Skill` en el writer y el editor (§7.4): `update_brief` y `propose_dedication` el entrevistador; `submit_facts` el extractor; `submit_world`, `submit_cast`, `submit_outline` y `submit_style_sheet` el planner al planificar, y solo `propose_change` en modo cambio; `submit_chapter` el writer; `submit_evaluation` el crítico y el juez; `submit_correction` y `submit_edit` el editor; `submit_record` el registrador; y las tools de navegación de Playwright MCP —navegar, instantánea y clic— con `submit_visual_review` el revisor visual (RF-POL-21)
  - Las de Playwright MCP son `browser_navigate`, `browser_snapshot` y `browser_click`. Las tools las implementan 005, 010, 011 y 014; esta lista solo las nombra.
- [ ] Un rol llama a una tool que no está en su lista blanca, también una integrada de Claude Code de ficheros, terminal o web → el hook de policy la deniega antes de ejecutarla, y el modelo recibe el motivo (RF-POL-16)
  - Integración con el doble del puerto de agente (RF-BAS-17, RF-BAS-24): el guion llama a `Read`, `Write`, `Edit`, `Bash`, `WebFetch`, `WebSearch` y a la tool de otro rol; el manejador no se ejecuta, el resultado que lee el modelo es el motivo y queda la fila del audit log.
  - El hook recibe de quien abre la sesión el cliente, la novela, la ejecución si la hay, el rol, las tres listas y, en el revisor visual, el origen de la vista previa.
- [ ] Un rol llama a una tool cuyos campos de texto narrativo —capítulo, corrección, edición, mundo, reparto, outline, títulos o dedicatoria— tienen una coincidencia → el hook la deniega con los términos y sus posiciones, y el modelo los recibe. Es el validador `palabras-prohibidas` en el punto `policy_hook`, que la mide con `en-capitulo` en cualquier campo (`architecture.md` §10.3). Cada tool declara cuáles de sus campos son narrativos (RF-POL-17)
  - La posición es el campo y el desplazamiento dentro de él. El capítulo, la corrección y la edición son ubicación `chapter`, con su capítulo; los demás campos, `tool_field`.
  - En 003 aún no existen las tools de los roles: la prueba usa tools de prueba que declaran sus campos narrativos, y cada spec que añade una tool declara los suyos. El envío del score es de 004.
- [ ] Un término prohibido aparece solo en un campo que es una lista de prohibidas —las entradas que registra `update_brief` o el léxico a evitar de la `StyleSheet`— → el hook permite la tool: esos campos no se escanean (RF-POL-18)
  - Con una tool de prueba que tiene un campo de lista de prohibidas y uno narrativo: el término solo en el primero, `allow`; también en el segundo, `deny`.
- [ ] Un rol llama a `Skill` pidiendo cualquier skill que no sea `personalizacion-natural` → el hook la deniega (RF-POL-19)
  - En el writer y el editor: `personalizacion-natural`, `allow`; una skill del CLI empaquetado, como `claude-api`, `deny`. En los demás roles, `Skill` ya cae por la lista blanca.
- [ ] El revisor visual intenta cargar una página fuera del origen de la vista previa, al navegar, con un clic o por una redirección → no la carga: el hook deniega la navegación, y lo demás lo impide la configuración de su servidor de Playwright MCP (RF-POL-20)
  - El hook deniega `browser_navigate` a otro origen, también a una URL `file:`.
  - Un clic o una redirección no pasan por una URL que el hook vea. El servidor se arranca con `--allowed-origins` igual al origen de la vista previa, que corta las peticiones del navegador a otros orígenes. El README de la 0.0.82 avisa de que esa opción no afecta a las redirecciones, así que se arranca además con `--proxy-server` hacia una dirección local sin servicio y `--proxy-bypass` con el host de la vista previa: cualquier otra petición, también la de una redirección, falla en el proxy. Playwright fuerza `<-loopback>`, así que el proxy cubre también `localhost` (unsure: que `--proxy-bypass` distinga el puerto; lo dice la prueba).
  - La prueba arranca ese servidor de Playwright MCP sin modelo, con el Edge instalado, frente a un servidor de fixture en el origen de la vista previa con un enlace y una redirección hacia un segundo servidor local, y comprueba que el segundo no recibe ninguna petición.
  - Resuelve el unsure de [001 design.md](../001-base/design.md) §5.6: `--allowed-origins` existe, pero no basta. Al cerrar, ese apartado se corrige con la configuración que la prueba confirme.
- [ ] Se abre una sesión de rol → se abre sin tools integradas salvo `Skill` en el writer y el editor, declara su lista blanca como tools permitidas y usa un modo de permisos que deniega lo no preaprobado sin preguntar: ninguna sesión desatendida se queda esperando una confirmación (RF-POL-22)
  - Opciones del SDK para cada rol: `tools=[]`, o `["Skill"]` en el writer y el editor; `allowed_tools` con su lista blanca, en los nombres que expone el SDK; y `permission_mode="dontAsk"`. La prueba lee las opciones que el adaptador del SDK construye para cada uno de los nueve roles, sin abrir la sesión.
  - Resuelve el unsure de [001 design.md](../001-base/design.md) §5.1: `dontAsk` está en el `PermissionMode` del SDK 0.2.158. Al cerrar, ese apartado se corrige.
- [ ] Las pruebas de mutación sobre el motor de políticas y la normalización matan todo mutante de sus rutas de rechazo, también uno que haga fallar abierto al motor: que permita siempre (RT9) (RNF-1)
  - Con la orden de mutación de 001 (RF-BAS-46). Las rutas de rechazo son la coincidencia, la tool fuera de lista, la `Skill` ajena y la navegación fuera del origen. El resultado va a la fila RT9 de `verification.md` §4.9.
- [ ] Al cerrar 003 → la cabecera de `architecture.md` §11 lleva el explainer de los guardarraíles y el motor de políticas, y la de §7.5, el de los hooks, como asigna la lista de explainers del README (RF-POL-26 · clase I)

### Closing
- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
- [ ] Process records and explainers added, or none produced
