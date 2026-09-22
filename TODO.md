# TODO — implementation plans

One block per feature, newest last. Format and rules: AGENTS.md, process 3.

Only the user marks an approval box `[x]`. Agents mark step boxes as each case goes green.

---

## 001 — Backend V1

Spec: [specs/spec1.md](specs/spec1.md).

Decidido el 2026-09-22: el SRS es la **única** spec del proyecto. No se trocea por módulo,
no se renombra a `NNN-nombre.md`, y este es su único bloque. Las once partes de abajo son
secciones del plan, no specs separadas.

Cada paso cita el requisito que entrega. Solo la **clase T** se convierte en prueba; los
pasos marcados `clase A` se cierran con tipado estricto y análisis estático, `clase I` con
revisión y `clase D` con ejecución demostrativa (AGENTS.md, proceso 4).

Las cifras sin calibrar (`densidad_minima`, umbrales de juicio, techos, cuotas,
`umbral_deriva_conteo`) se leen de configuración y fallan de forma accionable si faltan.
Ningún paso de este plan inventa un número (spec §2.5).

- [ ] Spec `specs/spec1.md` approved   <- only the user marks this
- [ ] Plan below approved              <- only the user marks this

### Steps

#### 0. Andamiaje

Prerrequisito del bloque, no casos de aceptación: nada de aquí se enuncia como
entrada → salida. Se cierra antes del primer paso de CFG.

- [ ] Proyecto `backend/` con `uv`, Python 3.12+, FastAPI, Pydantic v2 y SQLAlchemy 2 (R4 · clase A)
- [ ] Tipado estricto en todo el backend y modelos validados en tiempo de ejecución en los dos bordes: entrada HTTP y salida de modelo (RNF-5 · clase A)
- [ ] Ruff sobre todo el backend, más escaneo de secretos, de construcción dinámica de consultas y de manejo de rutas al escribir el manuscrito (RNF-6 · clase A)
- [ ] Estructura de módulos de spec §7 creada: `phases/`, `execution/`, `domain/`, `platform/` (R8 · clase A)
- [ ] Las cuatro reglas de dependencia de spec §7 se comprueban en CI, no por convención (RNF-7 · clase A)
- [ ] El recuperador reparte sus piezas entre `domain`, `platform` y las fases, y no existen `commons`, `shared` ni `utils`; se comprueba en CI (RNF-8 · clase A)
- [ ] El puerto del proveedor de modelo vive en `platform`, ninguna fase importa un cliente concreto, y existe un doble determinista que devuelve respuestas fijas con su uso y su coste (RNF-9 · clase A)
- [ ] Una conexión SQLite carga `sqlite-vec` y FTS5 sobre esa misma conexión, sin servicio externo (R5, RNF-11 · clase A)
- [ ] Cada ejecución vive en su propio fichero SQLite y la biblioteca de canon en el fichero compartido, con las dos rutas leídas de `config.operacion` (RNF-12)
- [ ] `fastembed` arranca en Windows sin privilegios de administrador y sin red tras la descarga inicial, con VC++ en espacio de usuario y symlinks de caché desactivados (R6, R9, RNF-13 · clase D)
- [ ] El esquema OpenAPI se exporta en estático, sin arrancar servidor (RNF-15)
- [ ] Las pruebas viven dentro de cada slice, no en un árbol aparte (RNF-14 · clase I)

#### 1. CFG — Configuración y creación de la ejecución

- [ ] `config.estructura` declara `objetivo_palabras`, `capitulos` y `forma_distribucion`, y el resto se deriva: no existe campo donde escribir un estado inconsistente (RF-CFG-2 · clase A)
- [ ] `config.calidad` y `config.recuperacion` no son editables por el usuario final (RF-CFG-11 · clase A)
- [ ] Una combinación aritmética imposible de `config.estructura` se rechaza antes de ejecutar nada, nombrando los parámetros incompatibles (RF-CFG-1 · clases T y A)
- [ ] Sin tabla de cuotas no se arranca: no existen cuotas por defecto en el código (RF-CFG-9)
- [ ] Sin directorio de ejecuciones ni ruta de biblioteca declarados en `config.operacion` no se crea la ejecución, con error que nombra la que falta (RF-CFG-10)
- [ ] Una tabla de cuotas completa, con una entrada por par (colección, consumidor) y `modelo_incrustacion` con valor, deja crear la ejecución (RF-CFG-3)
- [ ] Un par (colección, consumidor) ausente impide crear la ejecución, con error que nombra el par que falta (RF-CFG-4)
- [ ] Una cuota negativa o no entera impide crear la ejecución (RF-CFG-5)
- [ ] Una colección o un consumidor desconocidos impiden crear la ejecución (RF-CFG-6)
- [ ] Prosa con cuota mayor que 0 para el escritor o para el crítico de canon impide crear la ejecución (RF-CFG-7)
- [ ] Una cuota de 0 es válida y significa que esa colección no entra en la ventana de ese consumidor (RF-CFG-8)
- [ ] El identificador del modelo de incrustación se congela al crear la ejecución; cambiarlo después en configuración no afecta a una ejecución ya creada (RF-CFG-13)
- [ ] El identificador del modelo de lenguaje se congela al crear la ejecución; cambiarlo después se ignora y queda anotado en el informe como resolución de conflicto (RF-CFG-14)
- [ ] Cada parámetro estructural genera un `Criterio` de la puerta dura (RF-CFG-15)

#### 2. RUN — Ciclo de vida de la ejecución

- [ ] Los estados del trabajo y sus transiciones legales están declarados y son los únicos posibles (RF-RUN-9 · clase A)
- [ ] `POST /runs` crea la ejecución, devuelve su identificador y no espera a que termine (RF-RUN-1)
- [ ] Los errores aritméticos de bloqueo se devuelven en el `POST`; los de densidad, en el estado del trabajo (RF-RUN-7)
- [ ] La ejecución corre en un worker aparte del proceso que atiende HTTP (RF-RUN-2 · clase D)
- [ ] `GET /runs/{id}` devuelve estado, fase y escena actual en todo momento (RF-RUN-3)
- [ ] `GET /runs/{id}/stream` emite progreso por Server-Sent Events mientras la ejecución avanza (RF-RUN-4 · clases T y D)
- [ ] Existe punto de control por escena: el estado persistido basta para reanudar sin repetir escenas aceptadas (RF-RUN-5)
- [ ] Una caída no pierde más de una escena de trabajo (RNF-4)
- [ ] `DELETE /runs/{id}` cancela conservando el manuscrito parcial y el estado (RF-RUN-6)
- [ ] Cada agente con bucle lleva su propio tiempo máximo, además del presupuesto de reintentos por escena (RF-RUN-8)
- [ ] Ninguna operación de usuario espera a que la ejecución termine (RNF-3 · clase D)

#### 3. MEM — Memoria de la ejecución

Determinista de principio a fin: ningún paso de esta sección llama a un modelo de lenguaje.
Sus pruebas corren sobre un índice de fixture con vectores almacenados, y la cuota entra
como dato del caso (spec §8).

**Escritura**

- [ ] Solo el arquitecto de mundo en la fase 1 y el registrador de estado en la fase 3 escriben en el índice (RF-MEM-7 · clase A)
- [ ] Cada entidad del canon inicial produce una `CanonCard` con `desde_escena` = 1 y `hasta_escena` abierto, consultable de inmediato (RF-MEM-1)
- [ ] Un cambio en una entidad cierra la tarjeta vigente y añade otra: el índice es append-only, sin `UPDATE` ni `DELETE` (RF-MEM-4)
- [ ] Al aceptar una escena, su delta se indexa en la misma transacción que el canon: no hay instante observable en que canon e índice discrepen (RF-MEM-2)
- [ ] Una escena rechazada no deja rastro: el índice queda idéntico al anterior a generarla (RF-MEM-3)
- [ ] Aceptar una escena escribe su resumen y una fila por párrafo, cada una con su escena y su capítulo (RF-MEM-5)
- [ ] Un vector almacenado nunca se recalcula (RF-MEM-6)
- [ ] El índice es función pura del canon aceptado: reconstruirlo desde el canon produce el mismo contenido (RF-MEM-8)

**Residentes y proyección**

- [ ] Los residentes no se indexan nunca (RF-MEM-10 · clase A)
- [ ] La ventana lleva siempre los residentes que existan: proyección del outline, `EstadoDelMundo`, `ResumenRodante`, `StyleSheet`, compromisos inviolables y `CatalogoDeTropos` (RF-MEM-9)
- [ ] La proyección del outline contiene los capitulares de toda la obra, las escenas del capítulo actual y la lista explícita de lo que aún no puede revelarse (RF-MEM-11)
- [ ] La proyección no contiene las escenas de otros capítulos, ni siquiera resumidas (RF-MEM-12)
- [ ] La lista de lo no revelable nombra los hechos de outline posteriores a la escena actual, sin exponer su contenido (RF-MEM-13)
- [ ] Una escena que no existe en el outline produce ventana sin proyección de capítulo, con causa raíz `contexto ausente`, sin bloquear (RF-MEM-14)

**Consultas y recuperación**

- [ ] No existe re-ranking por modelo en ninguna colección (RF-MEM-22 · clase A)
- [ ] El corte temporal filtra antes de puntuar: para la escena *n* solo son candidatas las unidades con `desde_escena` ≤ *n* < `hasta_escena` (RF-MEM-18)
- [ ] Cada colección se puntúa por separado: ningún ranking mezcla unidades de dos colecciones (RF-MEM-19)
- [ ] `CanonCards` y resúmenes se recuperan por canal léxico y canal denso, fundidos por rango recíproco dentro de la colección (RF-MEM-20)
- [ ] La prosa se recupera solo por canal léxico, sin incrustaciones, y su unidad es el párrafo (RF-MEM-21)
- [ ] Los empates se desempatan por identificador, de forma estable entre ejecuciones (RF-MEM-23)
- [ ] El escritor consulta de forma prospectiva, desde la entrada de outline de la escena que va a escribir (RF-MEM-15)
- [ ] El crítico de canon consulta de forma retrospectiva, desde el texto que el escritor acaba de producir (RF-MEM-16)
- [ ] Las dos consultas sobre la misma escena son distintas; ninguna reutiliza la otra (RF-MEM-17)
- [ ] Una `Consecuencia` recuperada arrastra sus ancestros hasta el `Novum` como enunciado de una línea, sin consumir cuota y sin entrar como tarjeta completa (RF-MEM-24)
- [ ] Un resumen recuperado arrastra el anterior y el siguiente, y consume tres plazas (RF-MEM-25)
- [ ] El arrastre temporal respeta el corte: no arrastra resúmenes de escenas posteriores a la actual (RF-MEM-26)
- [ ] Recuperación vacía o escasa no bloquea: se genera con lo que haya y se registra causa raíz `contexto ausente` (RF-MEM-27)

**Cuotas, ensamblado y tope**

- [ ] El guardián de presupuesto lo invoca el código, nunca el modelo: el agente no ve su presupuesto ni decide qué pedir (RF-MEM-34 · clase A)
- [ ] Cada par (colección, consumidor) entrega como mucho sus plazas; el sobrante se registra como negado (RF-MEM-28)
- [ ] Las plazas sobrantes no se prestan entre colecciones (RF-MEM-29)
- [ ] Con cuota 0, esa colección no se consulta ni aparece en la ventana de ese consumidor (RF-MEM-30)
- [ ] El escritor nunca recibe prosa recuperada; el crítico de oficio sí (RF-MEM-31)
- [ ] El orden de las piezas en la ventana es declarado y estable: mismas entradas, misma ventana, pieza por pieza (RF-MEM-32)
- [ ] El conteo de entrada usa el tokenizador del modelo congelado al crear la ejecución (RF-MEM-40)
- [ ] La cuota de entrada de la etapa la calcula el orquestador dividiendo el techo entre las llamadas realmente en vuelo (RF-MEM-33)
- [ ] Lo ensamblado nunca supera la cuota de entrada de la etapa (RF-MEM-35)
- [ ] Si no cabe, se recorta en el orden declarado —prosa, resúmenes de escena, `CanonCards`, `ResumenRodante`— y dentro de cada colección por rango inverso (RF-MEM-36)
- [ ] Residentes y arrastres no se recortan, salvo el `ResumenRodante`, que es la última válvula (RF-MEM-37)
- [ ] Si lo intocable ya supera la cuota, se recorta el `ResumenRodante` y se entrega igual, con causa raíz `contexto ausente`, sin bloquear (RF-MEM-38)
- [ ] Lo negado se descuenta antes de cerrar la ventana y no llega al consumidor de ninguna forma (RF-MEM-39)
- [ ] Deriva de conteo por encima de `umbral_deriva_conteo` anota causa raíz `presupuesto excedido`, que no bloquea ni reintenta (RF-MEM-41 · deseable)

**Trazabilidad y determinismo**

- [ ] La ventana registra qué entró y qué quedó fuera: identificador de cada residente y de cada unidad recuperada, más los negados con su motivo —cuota o recorte— (RF-MEM-42)
- [ ] Todo fragmento generado registra las `CanonCard` que lo justificaron, derivadas de la ventana con la que se generó (RF-MEM-43)
- [ ] Con el mismo índice, la misma configuración y la misma escena, la ventana es idéntica pieza por pieza, sin ninguna llamada a modelo (RNF-1)
- [ ] Una ejecución cuyo modelo de incrustación ya no exista no se reanuda sin reconstruir el índice (RNF-2)

#### 4. BRF — Extracción del contrato de brief

- [ ] El sistema deriva del prompt un `ContratoDeBrief` con sus `Compromiso`s, sus `Hueco`s y un grado de libertad entre 0 y 1 (RF-BRF-1)
- [ ] Cada `Compromiso` declara dureza —inviolable o preferencia— y si es verificable (RF-BRF-2)
- [ ] Ante ambigüedad irresoluble, se clasifica como `Hueco` y nunca como `Compromiso` (RF-BRF-5)
- [ ] Los parámetros poéticos de `config` se promocionan a `Compromiso` del contrato (RF-BRF-7)
- [ ] Un verificador independiente redacta una paráfrasis del contrato y la contrasta con el prompt original (RF-BRF-3 · clases T e I)
- [ ] Lo que aparece en el prompt y no en la paráfrasis se trata como compromiso perdido y vuelve a extracción (RF-BRF-4)
- [ ] Un compromiso no verificable, o se convierte en criterio con rúbrica, o se declara como no verificado en el informe (RF-BRF-6)
- [ ] Un prompt casi vacío produce un contrato con cero compromisos y grado de libertad 1.0, y la ejecución continúa (RF-BRF-8)

#### 5. WLD — Arquitectura de mundo

- [ ] El orden de una `Consecuencia` se limita a 1.º, 2.º o 3.º (RF-WLD-7 · clase A)
- [ ] El catálogo de tropos existe curado desde la primera ejecución; sin él no se puede puntuar originalidad (RF-WLD-5)
- [ ] La biblioteca de canon guarda entidades, aristas y vigencias, nunca vectores (RF-WLD-10)
- [ ] El arquitecto recibe como restricción de entrada un techo de elementos estructurales inventables (RF-WLD-1)
- [ ] El arquitecto produce N candidatos de `Novum`, nunca uno solo (RF-WLD-2)
- [ ] El auditor de tropos puntúa el solapamiento de cada candidato con el `CatalogoDeTropos` (RF-WLD-3 · clases T e I)
- [ ] El selector puntúa cada candidato en derivabilidad, ajuste a los compromisos y distancia al catálogo, y elige por puntuación (RF-WLD-4)
- [ ] Las consecuencias se derivan hasta que no queda ninguna huérfana: toda `Consecuencia` es alcanzable desde al menos un `Novum` (RF-WLD-6)
- [ ] Al cerrar la fase, el arquitecto escribe el canon inicial y su índice en la misma transacción (RF-WLD-8)
- [ ] Una ejecución que entrega manuscrito promueve su canon a la biblioteca como versión nueva que apunta a la anterior; ninguna versión se sobrescribe (RF-WLD-11)
- [ ] El arquitecto admite el modo «reutilizar canon», que parte de un storyworld de la biblioteca en vez de inventarlo (RF-WLD-9 · deseable)

#### 6. PLN — Planificación y puerta de factibilidad

- [ ] El planificador produce un `Outline` jerárquico de capítulos y escenas a partir del canon, el contrato y `config` (RF-PLN-1)
- [ ] El outline declara la cobertura de arcos y el estado de cada `Arco` (RF-PLN-2)
- [ ] La puerta 0 calcula la densidad narrativa como `objetivo_palabras` entre los elementos estructurales **comprometidos**, contando solo los derivados del `ContratoDeBrief` (RF-PLN-3 · clases T y A)
- [ ] Por debajo de `densidad_minima`, la ejecución se bloquea con un mensaje que nombra las tres cifras: elementos comprometidos, palabras por elemento y mínimo exigido (RF-PLN-4)
- [ ] La puerta 0 comprueba que todo compromiso tiene cobertura en el outline; si falta alguno, vuelve a planificación (RF-PLN-5)
- [ ] Con cero compromisos, la puerta 0 pasa por construcción y la ejecución continúa (RF-PLN-6)
- [ ] La puerta 0 corre una sola vez, sobre el outline, antes de congelar la estructura, y no forma parte del bucle por escena (RF-PLN-7)
- [ ] Superada la puerta 0, la estructura se congela (RF-PLN-8, cierra RF-CFG-12)

#### 7. SCN — Producción por escena

- [ ] Los críticos no reciben el razonamiento del escritor ni su ventana (RF-SCN-7 · clase A)
- [ ] Ningún agente escribe en canon durante el bucle; solo el registrador, y solo tras veredicto de aceptación (RF-SCN-16 · clase A)
- [ ] Las escenas se producen en orden: ninguna empieza antes de que la anterior esté aceptada y registrada (RF-SCN-1, R3)
- [ ] El escritor recibe una `VentanaDeContexto` y produce texto de escena más el delta que pretendía (RF-SCN-2)
- [ ] La puerta dura comprueba, sin modelo: violación de `Restriccion`, contradicción temporal, atributo de canon alterado y los predicados deterministas de los invariantes 3 y 4 (RF-SCN-3)
- [ ] El predicado determinista del invariante 3 se comprueba sobre el delta **declarado** por el escritor, no sobre el real (RF-SCN-4)
- [ ] Superada la puerta dura, crítico de canon, crítico de oficio y auditor de tropos corren en paralelo (RF-SCN-5 · clases T y D)
- [ ] Los críticos devuelven `Defecto` tipados y no reescriben nunca (RF-SCN-6)
- [ ] Todo `Defecto` registra severidad, localización y causa raíz (RF-SCN-8)
- [ ] La causa raíz pertenece a un conjunto cerrado de seis valores; una causa fuera de ese conjunto es salida inválida del crítico, se rechaza y consume reintento (RF-SCN-9 · clases T y A)
- [ ] El enrutado es uno solo y por naturaleza del defecto: los corregibles al editor, los estructurales al escritor, nunca por la puerta que lo encontró (RF-SCN-10)
- [ ] La escena corregida por el editor vuelve a entrar por la puerta dura (RF-SCN-11)
- [ ] Agotado el presupuesto de reintentos de una escena, el veredicto es `escalar` y el defecto queda en el informe (RF-SCN-12)
- [ ] El registrador extrae el `DeltaDeEstado` real del texto aceptado; la divergencia con el declarado es un defecto de la puerta dura (RF-SCN-13)
- [ ] Al aceptar una escena se actualizan canon, `EstadoDelMundo`, `ResumenRodante` e índice en una sola transacción, antes de generar la siguiente (RF-SCN-14)
- [ ] Al aceptar una escena se escribe el `EstadoEpistemico` de cada `Personaje` cuyo conocimiento cambia en ella, en esa misma transacción; el de los demás se arrastra (RF-SCN-15)
- [ ] El `EstadoDelMundo` en la escena *n* es la aplicación ordenada de los deltas de las escenas 1..*n*−1 (RF-SCN-17)
- [ ] Todo `Hueco` resuelto pasa a ser canon inviolable (RF-SCN-18)

#### 8. GLB — Revisión de obra

- [ ] El pase global no lee el manuscrito entero: se descompone en cuatro comprobaciones por tipo de defecto (RF-GLB-1 · clase A)
- [ ] Hilos abiertos: consulta estructurada de `Arco` con estado abierto (RF-GLB-2)
- [ ] Consecuencias establecidas y nunca usadas: consulta estructurada de `Consecuencia` sin ningún vínculo de trazabilidad (RF-GLB-3)
- [ ] Ritmo y curva de tensión: juicio sobre la tabla de tensiones de capítulo, construida por código (RF-GLB-4 · clases T e I)
- [ ] Repetición léxica entre escenas distantes: único uso de recuperación de todo el pase global, sobre la colección de prosa (RF-GLB-6 · clases T e I)
- [ ] Deriva de voz: muestreo de tercios contrastado con el `StyleSheet` (RF-GLB-5 · clase I)
- [ ] Los defectos de obra se resuelven por reescritura dirigida de escenas concretas, nunca por regeneración global (RF-GLB-7)
- [ ] Una escena reescrita vuelve a pasar las puertas del bucle por escena (RF-GLB-8)

#### 9. BUD — Presupuestos y techos

- [ ] Existen tres techos distintos y no se confunden: ventana en tokens de entrada, reintentos por escena y ejecución en dinero (RF-BUD-1 · clase A)
- [ ] La salida no lleva techo en tokens (RF-BUD-3 · clase A)
- [ ] El techo de ventana cuenta solo entrada y se aplica a la suma de las llamadas en vuelo de una etapa, no a una llamada suelta (RF-BUD-2)
- [ ] Toda llamada a modelo registra agente, fase, escena, tokens de entrada declarados y reales, y coste (RNF-10)
- [ ] El coste consumido se acumula por llamada y es consultable durante la ejecución (RF-BUD-5)
- [ ] Agotado el presupuesto en dinero, la ejecución bloquea (RF-BUD-4)

#### 10. OUT — Salidas

- [ ] `GET /runs/{id}/manuscript` entrega el manuscrito en Markdown, único formato soportado (RF-OUT-1, R7)
- [ ] El informe de ejecución declara compromisos cumplidos, compromisos no verificables, huecos resueltos y con qué, novum elegido y su puntuación, defectos no resueltos con su localización, presupuesto consumido y causas raíz registradas (RF-OUT-2)
- [ ] `GET /runs/{id}/report` entrega el informe al terminar o al cancelar; mientras la ejecución corre devuelve conflicto, nombrando el estado actual (RF-OUT-3)
- [ ] El informe de una ejecución cancelada tiene la misma estructura, con los campos no evaluados declarados como tales y la fase en que se canceló (RF-OUT-4)
- [ ] El informe recoge las causas raíz que no producen defecto: `contexto ausente` por recorte y `presupuesto excedido` por deriva de conteo (RF-OUT-5)
- [ ] Toda resolución de conflicto entre config y prompt queda registrada en el informe; ninguna se resuelve en silencio (RF-OUT-6)
- [ ] El manuscrito parcial es accesible durante la ejecución, marcado como no definitivo (RF-OUT-7)
- [ ] Demostración de extremo a extremo con un prompt casi vacío: de `POST /runs` a manuscrito e informe (spec §8 · clase D)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
