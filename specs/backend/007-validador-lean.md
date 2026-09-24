# 007 — Validador Lean

> Carril: D · Depende de: 000; 009 *parcial*, solo para leer la `Cronologia` y la story bible de una versión desde SQLite (casos 007-C06 y 007-C07 a 007-C12) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Entregar el validador formal de la historia, `cronologia-lean`. Una biblioteca Lean 4 define la cronología y los invariantes T1–T5 como predicados decidibles, cada uno con un comprobador y su demostración general. Desde la `Cronologia` de una versión en SQLite se genera un `FicheroDeCronologia` seudonimizado. El `VerificadorFormal` (modo `local` o `github`) lo compila contra la biblioteca y devuelve `passed`, `failed` o `error`, o bien ningún veredicto, con el motivo `verifier_unreachable` o `verifier_timeout`. Si es `failed`, el testigo de cada invariante violado se traduce de vuelta a capítulos y nombres, como defectos listos para el gate. Con esto se cumple §5c del encargo: el fichero se genera desde SQLite, hay al menos dos invariantes (aquí cinco, con demostraciones generales) y la verificación es automática y devuelve el fallo como feedback.

## Alcance

- **Biblioteca de la cronología (Lean 4).** Contiene los tipos de la cronología: eventos con id, momento como fecha de calendario y hora, capítulo y beat, presentes con su edad declarada, lugar, tipo y personaje excluido, y analepsis. Contiene también las fechas de nacimiento y la fecha del novum. Define T1–T5 como predicados decidibles y un comprobador por invariante, con la demostración general de que decide su invariante para cualquier cronología (corrección y completitud). La salida es un documento JSON que da, por invariante, si se cumple y, para cada invariante violado, su primer testigo.
- **Generador del `FicheroDeCronologia`.** Parte de la `Cronologia` registrada de una versión (eventos de origen brief y registrados, fechas de nacimiento y fecha del novum) y produce los datos más un teorema por invariante, que se cierra evaluando el comprobador. El fichero va seudonimizado: los ids son los de las filas y las fechas se desplazan 400·*k* años.
- **Verificación de la candidata de una ejecución.** El fichero se guarda en el directorio de datos y deja una fila en `chronology_files` con la ejecución, la huella, el resultado y el detalle. El testigo se traduce a `Defecto` de `cronologia-lean`.
- **`VerificadorFormal`** con sus dos modos, que elige `FORMAL_VERIFIER`, y un doble determinista para las pruebas de las specs que lo consumen.
- **Workflow de verificación en GitHub Actions**, disparado por `workflow_dispatch`, con su seguridad: `--wfail`, auditoría de axiomas, permiso de solo lectura e inputs por variables de entorno.
- **En la CI:** el fichero dorado, un fichero negativo por invariante, los límites de cada invariante y los controles de la auditoría de axiomas.

## Fuera de alcance

- Cuándo corre la verificación dentro del gate (en paralelo con `juez-novela`) y qué hace el gate con cada salida → 012-gate-de-publicacion (`architecture.md` §9.4). Allí se decide la reescritura dirigida de los capítulos atribuidos, `failed` con `unattributable_defect` si el defecto no tiene capítulo y `interrupted` con el motivo que devuelve 007. También se decide ahí qué hacer con `error` (propuesta en la autorrevisión), cómo recibe el defecto el writer y el editor, y que prevalece sobre `cumple-beats`.
- Enviar los scores `cronologia-lean` y `cronologia-lean/T1` a `/T5`, abrir el span `validador:cronologia-lean` y copiar el resultado a `validator_results` → 012-gate-de-publicacion, por el puerto de 004-observabilidad (`architecture.md` §11.2, §13.3; `verification.md` §5, filas 5.0 y 6.4). Para ello, 007 entrega el resultado por invariante.
- La verificación en el gate de una edición manual → 019-edicion-manual, que usa el gate de 012.
- Escribir la cronología → 009-story-bible-y-versiones (esquema de story bible y copia de versión), el canon del brief con el fechado de los recuerdos según `domain-knowledge.md` §5.2 y los eventos planificados → 010-planificacion, y los eventos registrados al aceptar un capítulo → 011-produccion-de-capitulos.
- El caso real que solo detecta Lean (brief 5, incoherencia temporal) → 020-evals (`architecture.md` §11.7; `verification.md` §4.2 e).
- Los dos avisos ligeros de cronología del lint en vivo, que no son Lean → 019-edicion-manual.
- La lectura de los ajustes del servidor y la validación de `config.json`, incluidos el valor de `FORMAL_VERIFIER` y `operation.verifier_timeout_seconds` → 001-base. El esquema de `chronology_files` → 001-base.
- La reanudación tras `interrupted` → 011-produccion-de-capitulos. TLA+ → 006-especificacion-tla.

## Comportamiento observable

Datos de los casos. Una **cronología de fixture** tiene estos elementos (ids de fila entre paréntesis):

- el destinatario (11), nacido el 1990-05-14;
- la abuela (12), nacida el 1936-02-29;
- el perro (13), sin fecha de nacimiento;
- dos lugares (21 y 22);
- el novum, del 2024-11-01;
- el evento de origen brief 31, un recuerdo del 1998-05-14 a las 12:00 en el lugar 21, con el destinatario (edad declarada 8) y la abuela;
- el evento de origen brief 32, excluyente, del 2010-09-01 a las 12:00 en el lugar 22, con la abuela como excluida;
- el evento registrado 41, del capítulo 1, beat 1, del 2026-03-02 a las 10:00 en el lugar 21, con el destinatario y el perro;
- el evento registrado 42, del capítulo 2, beat 1, analepsis, del 2005-07-01 a las 18:00 en el lugar 22, con el destinatario y la abuela;
- el evento planificado 51, del capítulo 3, beat 2.

En los mensajes, «nombre» es la forma canónica de la story bible.

**Resultado de una verificación:**

- `passed`, `failed` o `error` (resultado del `FicheroDeCronologia`), con cumple sí/no para cada uno de T1–T5 en `passed` y en `failed`, el primer testigo de cada invariante violado y el motivo en `error`;
- o ningún veredicto, con el motivo de interrupción `verifier_unreachable` o `verifier_timeout`.

**Testigo** de cada invariante, como tupla de ids de fila:

| Invariante | Tupla |
|---|---|
| T1 | evento narrado antes, evento narrado después |
| T2 | personaje, evento, edad declarada, edad calculada |
| T3 | personaje, evento, evento (el de id menor primero) |
| T4 | personaje excluido, evento excluyente, evento posterior |
| T5 | personaje, evento |

El **primer testigo** es la tupla menor en orden lexicográfico de ids.

### Generador del `FicheroDeCronologia`

#### 007-C01 — El fichero lleva la cronología registrada de la versión y nada más (T)
- **Dado** la cronología de fixture
- **Cuando** se genera su `FicheroDeCronologia`
- **Entonces**:
  - contiene los eventos 31, 32, 41 y 42, cada uno con su id, su momento, su capítulo y beat (vacíos en 31 y 32), el id de su lugar, los ids de sus presentes con la edad declarada si la hay, su tipo, el id del excluido en 32 y su analepsis;
  - no contiene el evento planificado 51;
  - contiene las fechas de nacimiento de 11 y 12, y ninguna de 13;
  - contiene la fecha del novum;
  - no contiene ningún nombre, enunciado, descripción, hecho, título ni texto de la story bible: solo ids, fechas, números y valores sí/no

#### 007-C02 — Los ids son los de las filas y las fechas se desplazan 400·k años (T)
- **Dado** la cronología de fixture y un *k* dado
- **Cuando** se genera
- **Entonces**:
  - cada evento, personaje y lugar aparece con el id de su fila;
  - cada fecha (momento, nacimiento, novum) conserva el mes, el día, la hora y el minuto, y su año es el real + 400·*k*;
  - el fichero no contiene *k* ni ninguno de los años reales de la cronología (1936, 1990, 1998, 2005, 2010, 2024, 2026)

#### 007-C03 — k se elige al azar en cada fichero, entre 1 y 10 (T)
- **Dado** la cronología de fixture
- **Cuando** se genera muchas veces sin fijar *k*
- **Entonces**:
  - cada *k* es un entero entre 1 y 10, y nunca 0, que no desplazaría nada;
  - dos ficheros de la misma cronología con *k* distinto solo difieren en los años

#### 007-C04 — La misma cronología y el mismo k dan el mismo fichero (T)
- **Dado** la cronología de fixture, escrita en SQLite en dos órdenes de inserción distintos
- **Cuando** se genera con el mismo *k*
- **Entonces** los dos ficheros son idénticos byte a byte y listan los eventos por id ascendente

#### 007-C05 — El 29 de febrero y las edades se conservan al desplazar (T)
- **Dado** la abuela, nacida el 1936-02-29, presente en tres eventos:
  - uno del 2026-02-28 a las 12:00, con edad declarada 89;
  - uno del 2026-03-01 a las 00:00, con edad declarada 90;
  - uno del 2028-02-29 a las 00:00, con edad declarada 92
- **Cuando** se genera con cada *k* de 1 a 10
- **Entonces**:
  - su nacimiento sigue siendo un 29 de febrero de un año bisiesto;
  - 2026 sigue siendo no bisiesto y 2028 bisiesto;
  - la edad en años cumplidos en cada evento (`domain-knowledge.md` §5.2) es la misma que con las fechas reales: 89, 90 y 92

#### 007-C06 — Solo entra la versión que se verifica (T)
- **Dado** una novela con su versión publicada, una candidata copiada de ella con un evento registrado más, y otra novela con su propia cronología
- **Cuando** se genera el fichero de la candidata
- **Entonces** solo contiene filas de la candidata: el evento añadido está, y ningún id de la versión publicada ni de la otra novela que no sea también de la candidata

### Traducción del testigo

#### 007-C07 — Un testigo con eventos narrados da un defecto por capítulo (T)
- **Dado** una candidata cuya verificación da `failed` con:
  - T4, con el testigo (12, 32, 71), donde 71 es un evento registrado del capítulo 7, beat 2, con la abuela presente, posterior a 32;
  - T1, con el testigo (43, 44): 43 es del capítulo 3 y 44 del capítulo 5, con un momento anterior al de 43
- **Cuando** se traduce el testigo
- **Entonces** hay tres `Defecto` de `cronologia-lean`, bloqueantes y sin criterio:
  - uno de T4 con capítulo 7;
  - dos de T1, uno con capítulo 3 y otro con capítulo 5, con el mismo mensaje;
  - cada mensaje, en español, nombra el invariante, los personajes y lugares del testigo por su nombre y, de cada evento, su origen, su capítulo y beat si los tiene y su momento real, sin desplazar

#### 007-C08 — Un testigo solo con eventos del brief da un defecto sin capítulo (T)
- **Dado** `failed` con T3 y el testigo (11, 31, 33), donde 33 es otro recuerdo del brief a la misma hora que 31 en el lugar 22
- **Cuando** se traduce
- **Entonces** hay un único `Defecto` de `cronologia-lean`: bloqueante, sin capítulo (no atribuible) y con el mensaje de 007-C07

### Verificación de la candidata de una ejecución (con el doble del `VerificadorFormal`)

#### 007-C09 — Una verificación que pasa deja su fichero y su fila (T)
- **Dado** una ejecución con su candidata y el doble programado con `passed`
- **Cuando** se verifica la candidata
- **Entonces**:
  - el fichero queda en el directorio de datos;
  - `chronology_files` tiene una fila de esa ejecución con la huella del fichero guardado (coincide al recalcularla), resultado `passed` y sin testigo;
  - la salida es `passed`, con T1–T5 cumplidos y sin defectos

#### 007-C10 — Un invariante violado deja la fila `failed` y devuelve los defectos (T)
- **Dado** el doble programado con T4 y T1 violados, con los testigos de 007-C07, y T2, T3 y T5 cumplidos
- **Cuando** se verifica
- **Entonces**:
  - la fila tiene resultado `failed` y, en su detalle, T1 y T4 con sus testigos;
  - la salida es `failed`, con T1 y T4 no cumplidos y los otros tres cumplidos, y con los defectos de 007-C07

#### 007-C11 — Un fichero que no compila por otra causa es `error` y nunca `passed` (T)
- **Dado** el doble programado con `error` y un motivo
- **Cuando** se verifica
- **Entonces**:
  - la fila tiene resultado `error` y el motivo;
  - la salida es `error`, sin resultado por invariante ni defectos

#### 007-C12 — Sin veredicto no hay fila (T)
- **Dado** el doble programado primero como inalcanzable y después como agotado
- **Cuando** se verifica cada vez
- **Entonces**:
  - las salidas son «sin veredicto», con `verifier_unreachable` y con `verifier_timeout`;
  - `chronology_files` no gana ninguna fila

### Modo `local`

#### 007-C13 — El modo local compila en el directorio de datos e interpreta la salida (T)
- **Dado** `FORMAL_VERIFIER=local` y un sustituto de la compilación Lean que produce la salida de cada fila
- **Cuando** se verifica un fichero
- **Entonces**:
  - la compilación corre con el fichero dentro del directorio de datos;
  - el resultado es el de la tabla

| Salida de la compilación | Resultado |
|---|---|
| Compila; el JSON da T1–T5 cumplidos; la auditoría solo ve axiomas admitidos | `passed` |
| No compila; el JSON da T4 no cumplido con su testigo y los demás cumplidos | `failed`, con T4 y su testigo |
| No compila y el JSON da los cinco cumplidos, o no hay JSON | `error`, con el primer diagnóstico |
| Compila, pero el JSON da algún invariante no cumplido | `error`: son incoherentes |
| La auditoría ve `sorryAx` o un axioma no admitido | `error`, con el teorema y el axioma |
| La orden de compilación no existe o no arranca (como en el portátil con Smart App Control) | Sin veredicto, `verifier_unreachable` |
| No termina dentro de `verifier_timeout_seconds` | Sin veredicto, `verifier_timeout`, y ningún proceso de la compilación sigue vivo |

### Modo `github`

#### 007-C14 — El modo github envía el fichero comprimido por `workflow_dispatch` (T)
- **Dado** `FORMAL_VERIFIER=github`; `GITHUB_REPOSITORY`, `LEAN_WORKFLOW` y `GITHUB_TOKEN` con el marcador `TU_CLAVE_AQUI`; y un doble HTTP de la API de GitHub
- **Cuando** se verifica un fichero
- **Entonces**:
  - hay una sola petición de lanzamiento del workflow `LEAN_WORKFLOW` de `GITHUB_REPOSITORY`, que pide los detalles de la ejecución creada (`return_run_details: true`);
  - su input es el fichero comprimido en gzip y codificado en base64, y al decodificarlo sale el fichero byte a byte;
  - toda petición lleva la versión fijada de la API de GitHub y el token como autorización

#### 007-C15 — El modo github sondea la ejecución y lee el resultado del artefacto (T)
- **Dado** el doble HTTP, que responde con el id de la ejecución, la da en curso durante varios sondeos y después terminada con su artefacto
- **Cuando** termina
- **Entonces**:
  - con cada JSON del artefacto de las filas de 007-C13, el resultado es el mismo que en 007-C13;
  - una ejecución terminada sin artefacto de resultado, o con un artefacto que no cumple el schema del resultado, da «sin veredicto» con `verifier_unreachable`

#### 007-C16 — El input cabe en el límite de 65.535 caracteres o no se envía (T)
- **Dado** el doble HTTP y ficheros cuyos inputs codificados suman 65.535 y 65.536 caracteres
- **Cuando** se verifica cada uno
- **Entonces**:
  - el de 65.535 se envía;
  - el de 65.536 no se envía (ninguna petición) y da `error` con el motivo «el fichero no cabe en los inputs del workflow»

#### 007-C17 — Un GitHub inalcanzable o lento interrumpe sin reintentar (T)
- **Dado** el doble HTTP con cada fallo de la tabla
- **Cuando** se verifica
- **Entonces**:
  - el resultado es el de la tabla, sin reintentos dentro del verificador;
  - ningún mensaje ni detalle contiene el token

| Fallo | Resultado |
|---|---|
| Error de red, 5xx, 401, 403 o 404 en el lanzamiento | `verifier_unreachable`, tras una sola petición |
| Error de red o 5xx en un sondeo o en la descarga del artefacto | `verifier_unreachable` |
| La ejecución sigue sin terminar cuando pasan `verifier_timeout_seconds` desde el lanzamiento | `verifier_timeout` |

#### 007-C18 — El modo github sin sus ajustes no se construye (T)
- **Dado** `FORMAL_VERIFIER=github` y, por turnos, sin `GITHUB_REPOSITORY`, sin `LEAN_WORKFLOW` o sin `GITHUB_TOKEN`
- **Cuando** se construye el `VerificadorFormal`
- **Entonces** no se construye, y el error nombra el ajuste que falta sin mostrar el valor de ningún otro

### Doble para las specs que consumen el verificador

#### 007-C19 — El doble del `VerificadorFormal` devuelve lo programado sin red ni Lean (T)
- **Dado** el doble programado con una secuencia de resultados: `passed`; `failed` con sus testigos; `error`; `verifier_unreachable`; `verifier_timeout`
- **Cuando** se le piden verificaciones seguidas
- **Entonces**:
  - devuelve esos resultados en orden;
  - conserva los ficheros que recibió;
  - no abre conexiones de red, no lanza procesos y no evalúa ningún invariante

### Biblioteca Lean (en la CI)

#### 007-C20 — El fichero dorado compila y cumple T1–T5 (T)
- **Dado** el fichero que genera el generador desde la cronología de fixture con un *k* fijo, versionado como fichero dorado
- **Cuando** la CI lo compila contra la biblioteca con `--wfail` y audita sus axiomas
- **Entonces**:
  - la salida del generador para la fixture es idéntica, byte a byte, al fichero dorado;
  - el fichero compila y cierra sus cinco teoremas;
  - el JSON da T1–T5 cumplidos;
  - la auditoría solo ve axiomas admitidos (007-I11)

#### 007-C21 — Un fichero negativo por invariante falla con ese invariante y su primer testigo (A)
- **Dado** la cronología de fixture más dos violaciones sembradas de un solo invariante, con ids a < b < c < d y personajes p < q
- **Cuando** la CI compila cada negativo
- **Entonces**:
  - no compila;
  - el JSON da ese invariante no cumplido, con el testigo de la tabla, y los otros cuatro cumplidos;
  - la CI espera ese fallo y ese testigo, y se pone en rojo si compila o si el testigo es otro

| Invariante | Violaciones sembradas | Primer testigo esperado |
|---|---|---|
| T1 | a (cap. 4, beat 1) posterior en momento a b (cap. 4, beat 2); c (cap. 6, beat 1) posterior a d (cap. 6, beat 3); ninguno es analepsis | (a, b) |
| T2 | p, con fecha de nacimiento, con una edad declarada que no cuadra en a y en c | (p, a, declarada, calculada) |
| T3 | p en a y b a la misma hora en lugares distintos; q en c y d igual | (p, a, b) |
| T4 | p, excluido en a, presente en c y d, posteriores | (p, a, c) |
| T5 | p presente en b y d, anteriores a su nacimiento | (p, b) |

#### 007-C22 — Los límites de cada invariante (A)
- **Dado** un fichero por cada fila de la tabla, sobre la cronología de fixture
- **Cuando** la CI lo compila
- **Entonces** el invariante da lo de la tabla, y los demás se cumplen

| Invariante | Situación | Resultado |
|---|---|---|
| T1 | El evento narrado después tiene el mismo momento que el narrado antes | Cumple |
| T1 | El evento narrado después es un minuto anterior | No cumple |
| T1 | El evento narrado después es anterior, pero es analepsis | Cumple |
| T1 | Dos eventos del mismo capítulo y beat, en cualquier orden de momento | Cumple: no hay orden dentro de un beat |
| T1 | Eventos de origen brief anteriores a todo lo narrado | Cumple: sin capítulo no entran en T1 |
| T2 | Evento el día anterior al cumpleaños n, con edad declarada n | No cumple (la calculada es n − 1) |
| T2 | El mismo evento con edad declarada n − 1 | Cumple |
| T2 | Evento a las 00:00 del cumpleaños n, con edad declarada n | Cumple |
| T2 | Nacido un 29 de febrero, año no bisiesto: el 28 de febrero con edad declarada n | No cumple |
| T2 | Nacido un 29 de febrero, año no bisiesto: el 1 de marzo con edad declarada n | Cumple |
| T2 | Personaje sin fecha de nacimiento, con cualquier edad declarada | Cumple: T2 no lo alcanza |
| T3 | Mismo personaje, mismo momento, mismo lugar | Cumple |
| T3 | Mismo personaje, mismo momento, lugares distintos | No cumple |
| T3 | Mismo personaje, lugares distintos, con un minuto de diferencia | Cumple |
| T4 | El excluido está presente en su propio evento excluyente | Cumple |
| T4 | El excluido, en otro evento del mismo momento y del mismo lugar | Cumple: no es posterior |
| T4 | El excluido, en un evento un minuto posterior (también si es analepsis) | No cumple |
| T4 | El excluido, en un evento anterior a su exclusión narrado después (analepsis) | Cumple |
| T5 | Evento a las 00:00 de la fecha de nacimiento | Cumple |
| T5 | Evento a las 23:59 del día anterior | No cumple |
| T5 | Personaje sin fecha de nacimiento | Cumple: T5 no lo alcanza |

#### 007-C23 — Cada comprobador decide su invariante para cualquier cronología (A)
- **Dado** la biblioteca
- **Cuando** la CI la compila con `--wfail` y audita los axiomas de sus teoremas
- **Entonces**:
  - para cada uno de T1–T5 hay un teorema que dice que, para toda cronología, el comprobador devuelve `true` si y solo si el predicado se cumple (corrección y completitud);
  - todos cierran sin avisos;
  - la auditoría solo ve axiomas admitidos

#### 007-C24 — La auditoría de axiomas no pasa en vacío (A)
- **Dado** dos ficheros de control:
  - uno con un teorema cerrado con `sorry`;
  - otro que declara un axioma propio y cierra con él un teorema
- **Cuando** la CI compila cada uno
- **Entonces**:
  - los dos dan `error`: el primero por `--wfail` y por `sorryAx`, y el segundo con el nombre de su axioma;
  - la CI espera los dos fallos y se pone en rojo si alguno pasa

### Workflow real

#### 007-C25 — Una verificación real por GitHub Actions responde a tiempo (D)
- **Dado**:
  - el workflow de verificación en el repositorio de GitHub (GitHub Free);
  - un `GITHUB_TOKEN` de grano fino limitado al repositorio (Actions de lectura y escritura, Metadata de lectura), que crea el usuario;
  - los ajustes del modo github en el `.env`
- **Cuando**:
  - el backend verifica el fichero dorado y el negativo de T4;
  - se lanza a mano el workflow con un input que no es gzip ni base64
- **Entonces**:
  - el dorado da `passed` y el negativo `failed`, con T4 y el mismo testigo que en la CI;
  - el input inválido da `error` sin compilar nada;
  - cada verificación responde dentro de `verifier_timeout_seconds`, y la duración medida se anota para `architecture.md` §17.2;
  - el registro de la ejecución no muestra nombres ni fechas reales, y el job solo tiene permiso de lectura del contenido

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 007-I1 | Lean no se duplica en Python: ningún código del producto comprueba T1–T5 fuera de la biblioteca Lean; el doble del verificador y la traducción del testigo no evalúan invariantes | I | Revisión del `verificador` al cerrar (`architecture.md` §11.4, §18 «Lean frente a Python») |
| 007-I2 | Solo es `passed` lo que compila, pasa la auditoría y cumple los cinco invariantes. Cualquier otra salida es `failed`, `error` o «sin veredicto», y ninguna se confunde con `passed` | T | 007-C09 a 007-C13 y 007-C15 |
| 007-I3 | El `FicheroDeCronologia` no lleva datos personales: solo ids de fila, fechas desplazadas, números y valores sí/no. Ningún nombre, enunciado ni texto de la story bible aparece en él | T | Propiedad: con story bibles generadas con nombres y enunciados al azar, ninguno aparece en el fichero; y 007-C01 |
| 007-I4 | La seudonimización no cambia el resultado de ningún comprobador. Es inyectiva y conserva el orden y la igualdad de cualquier par de instantes del fichero, el día y el mes de cada fecha, si cada año es bisiesto y, con ello, la edad en años cumplidos de cada personaje en cada evento, que es lo único que leen T1–T5. Cada id de un testigo se traduce a su fila de la versión | T | Propiedad sobre cronologías generadas y *k* de 1 a 10 (`verification.md` §3.4); 007-C05 |
| 007-I5 | El mismo fichero da siempre el mismo resultado y el mismo primer testigo; la misma cronología con el mismo *k* da el mismo fichero | T (generador), A (biblioteca) | 007-C04; 007-C21 |
| 007-I6 | El fichero solo contiene filas de la versión que se verifica | T | 007-C06 |
| 007-I7 | El verificador solo escribe en `STORY_MAKER_DATA_DIR`: allí guarda el fichero y allí corre la compilación local | T | 007-C09 y 007-C13, con el directorio de datos de la prueba; nada se crea fuera de él |
| 007-I8 | `GITHUB_TOKEN` nunca aparece en el fichero, el input, el resultado, la fila, un mensaje de error ni un registro | T | 007-C14, 007-C17 y 007-C18, buscando el marcador en todo lo producido |
| 007-I9 | Los dos modos dan el mismo resultado para la misma salida de la verificación (estado de la compilación, diagnósticos, JSON y auditoría), porque ejecutan la misma verificación: la misma biblioteca, `--wfail` y la misma auditoría | T (interpretación), I (misma verificación) | La tabla de 007-C13 pasada por los dos modos; revisión del workflow frente al modo local |
| 007-I10 | El workflow solo se dispara por `workflow_dispatch`, su job solo tiene `contents: read` y sus inputs llegan a los pasos por variables de entorno, nunca interpolados en una orden. Comprueba que la carga es base64 y gzip antes de descomprimirla | I | Revisión del `verificador`; demostrada en 007-C25 |
| 007-I11 | La auditoría solo admite los tres axiomas estándar de Lean: `propext`, `Classical.choice` y `Quot.sound`. Rechaza `sorryAx`, cualquier axioma declarado en el proyecto o en el fichero y la confianza en el compilador para evaluar | A | 007-C20, 007-C23 y 007-C24 |
| 007-I12 | La fila de `chronology_files` solo existe con un resultado (`passed`, `failed` o `error`), y su huella es la del fichero guardado | T | 007-C09 a 007-C12 |
| 007-I13 | Ninguna prueba de la suite del backend llama a GitHub ni ejecuta Lean: usan el doble del verificador, el doble HTTP o el sustituto de la compilación. Lean solo corre en el job formal de la CI y en 007-C25 | I | Revisión del `verificador`; la CI no usa secretos (`verification.md` §4.6) |

## Scores y trazas

La 007 no envía scores ni abre spans. Entrega al gate el resultado con cumple sí/no para cada uno de T1–T5, y con él 012-gate-de-publicacion envía `cronologia-lean` (0/1) y `cronologia-lean/T1` a `cronologia-lean/T5` a la traza de la ejecución y copia el resultado a `validator_results` (`architecture.md` §11.2, §13.3; `definitions.md` §12.3).

## Docs referenciados

- `architecture.md`:
  - §4.4, tiempo de la historia;
  - §4.5, `Cronologia`: qué verifica Lean;
  - §7.6, `verifier_timeout_seconds`;
  - §9.1, `Caer` y los motivos `verifier_unreachable` y `verifier_timeout`;
  - §9.4, orden del gate y atribución del testigo Lean;
  - §11.2, fila `cronologia-lean`;
  - §11.4, entera: biblioteca, generador, seudonimización, cuándo, dónde, seguridad del workflow y Lean no duplicado;
  - §12.6, solo el directorio de datos;
  - §15.5, ajustes del verificador formal;
  - §15.6, tabla `chronology_files`;
  - §15.9, módulo `formal`, y el contrato que nace con su doble;
  - §17.2, el tiempo de respuesta del workflow;
  - §18, filas «Dónde corre Lean», «Seudonimización del fichero Lean», «Invariantes de Lean priorizados» y «Lean frente a Python».
- ADR 0004: protocolo `workflow_dispatch`, gzip y base64, 65.535 caracteres, `return_run_details`, versión fijada de la API, seguridad del workflow y token.
- `definitions.md`:
  - §2, `Personaje`, `Evento` y `Cronologia`;
  - §5, `Ejecucion` y sus motivos;
  - §6, `Validador`, `ResultadoDeValidador` y `Defecto`;
  - §9, `FicheroDeCronologia`, los invariantes de la cronología y `VerificadorFormal`;
  - §11.1, `operation.verifier_timeout_seconds`;
  - §11.3, `STORY_MAKER_DATA_DIR`, `FORMAL_VERIFIER`, `GITHUB_REPOSITORY`, `LEAN_WORKFLOW` y `GITHUB_TOKEN`;
  - §12.3, scores por invariante;
  - §12.4, resultado de `FicheroDeCronologia`, modo del `VerificadorFormal` y motivo de interrupción.
- `domain-knowledge.md`:
  - §5.2, nacimiento a las 00:00 y 29 de febrero;
  - §5.3, enunciados de T1–T5; T2 y T5 solo con fecha de nacimiento.
- `verification.md`:
  - §2, clases;
  - §3.4, propiedad del generador;
  - §3.5, contrato del fichero Lean;
  - §3.6, Lean: `--wfail`, axiomas y negativos;
  - §4.6, job formal de la CI;
  - §4.9, RT18;
  - §5, filas C.2, 4.3, 5c.1, 5c.2, 5c.3 y O.12;
  - §6, U4 y U14.
- `project-constraints.md`, §5c: el fichero Lean generado desde SQLite; al menos dos invariantes; `lake build` automático, sin publicar si falla y con feedback al editor; opcional, invariantes adicionales y demostraciones generales.

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué entrega la 007 y qué el gate? | La 007 entrega la biblioteca, el generador, el verificador (dos modos y un doble), la fila de `chronology_files` y los defectos traducidos. La 012 decide la acción, los scores y `validator_results` | `TODO.md` (Specs); `verification.md` §5, filas 5.0, 5c.3 y 6.4 |
| ¿Qué eventos entran? | Los de origen brief y los registrados; nunca los planificados. Los nacimientos de todo personaje que tiene fecha, y el novum | `architecture.md` §4.5; `definitions.md` §2 `Cronologia` |
| ¿Qué es «narrado antes» en T1? | El orden de capítulo y beat. Los eventos sin capítulo no entran en T1, y dentro de un beat no hay orden | `domain-knowledge.md` §5.3; **hueco del doc** (dentro de un beat) → §18 |
| ¿Posterior, anterior y mismo momento? | Por momento, con fecha y hora. T3 exige el mismo momento exacto; T4, estrictamente posterior; T5 cuenta el instante de nacimiento como ya nacido | `domain-knowledge.md` §5.2 y §5.3; **hueco** (límites) → §18 |
| ¿Cuál es el «primer testigo»? | La tupla menor en orden lexicográfico de ids. Un testigo por invariante violado | `architecture.md` §11.4; **hueco** (orden) → §18 |
| ¿Cómo se prueba la propiedad de §3.4 sin Lean en la suite? | Comprobando lo único que leen T1–T5: el orden y la igualdad de instantes, las edades, los bisiestos y la traducción de ids | `verification.md` §3.4; `architecture.md` §11.4 (no duplicar Lean) |
| ¿Qué k? | Un entero al azar entre 1 y 10, hacia el futuro. Nunca 0, que dejaría las fechas reales, ni negativo, que llevaría años antes de la era | `architecture.md` §11.4; **hueco** → §18 |
| ¿Qué axiomas admite la auditoría? | `propext`, `Classical.choice` y `Quot.sound`. Los teoremas se cierran evaluando en el núcleo, sin confiar en el compilador | `architecture.md` §11.4; **hueco** → §18 |
| ¿`error`, `failed` o sin veredicto? | `failed`: solo fallan teoremas de invariantes, con testigo. `error`: cualquier otra causa (no compila, auditoría, JSON incoherente, input que no cabe). Sin artefacto legible o sin respuesta: `verifier_unreachable` | `definitions.md` §9; ADR 0004; **hueco** → §18 |
| ¿Reintenta el modo github? | No. Cualquier fallo de una petición da `verifier_unreachable`, que ya es reanudable y está acotado por `max_resumes` | Máxima de simplicidad; `architecture.md` §7.6 |
| ¿Un defecto o varios? | Uno por invariante violado y por capítulo de los eventos de su testigo; si no hay capítulo, uno sin capítulo | `architecture.md` §9.4; `definitions.md` §6 `Defecto` (un capítulo) |
| ¿Fila sin veredicto? | No: la fila solo existe con un resultado; lo que no llegó a verificarse no se registra | `definitions.md` §12.4 (tres resultados) |
| ¿Qué hace el gate con `error`? | Es de la 012. Propuesta: `failed` con `internal_error` (fallo del código, no de la historia) | `architecture.md` §9.1; **hueco del doc** |
| ¿Sobre qué rama se lanza el workflow? | La rama por defecto del repositorio. Unsure: GitHub solo dispara `workflow_dispatch` si el workflow está en ella, así que es una decisión del usuario sobre su cuenta | ADR 0004; pregunta para el usuario |
| ¿Quién crea el token? | El usuario (cuentas y tokens). Solo lo necesita 007-C25 | `verification.md` §9.7 |
