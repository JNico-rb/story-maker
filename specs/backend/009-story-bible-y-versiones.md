# 009 — Story bible y versiones

> Carril: B · Depende de: 001-base · Estado: borrador. Usa además dos contratos que la tabla de `TODO.md` no lista: el modelo del brief confirmado de 008-brief-y-entrevista (009-C01 a 009-C10) y la identidad y la propiedad de 002-autenticacion (009-C25 a 009-C27).

## Objetivo

Guardar el canon de cada versión y llevar el ciclo de vida de las versiones de modo que cada una sea autocontenida y una publicada no cambie nunca. El código escribe el canon del brief en la candidata de generación. La candidata de un cambio o de una edición nace como copia íntegra de su base, en una transacción y compartiendo los vectores. Una candidata se publica con el número siguiente y sus capítulos cambiados, o se descarta. La story bible y la cronología registrada de una versión se leen por dentro, de cualquier versión, y por la API, solo de las publicadas del propio cliente.

Del encargo cubre «story bible en SQLite» (el canon del brief escrito por código), «cada hecho registra en qué capítulos se usa» (en la lectura), «tabla de cronología que alimenta el validador formal» y «se conserva la versión anterior» (`verification.md` §5, filas 4.1, 4.2, 4.3 y 2.11).

## Alcance

- **Canon del brief** (`architecture.md` §4.1): lo que el código escribe en la candidata de generación a partir del brief confirmado, con el fechado de `domain-knowledge.md` §5.2 y el vocabulario de atributos de los hechos del brief (`definitions.md` §2 Hecho, §11.2): `nombre` (nominal), `rasgo`, `recuerdo` y `relación`. Los identificadores en inglés se fijan en el plan, según `definitions.md` §12.
- **Copia de versión** (§9.3, §6.4): la candidata de un cambio o de una edición copia en una transacción todas las tablas de ámbito versión de su base (§15.6), con el canal léxico de las CanonCards, y comparte sus vectores.
- **Cambio del valor de un hecho** en una candidata. Si el hecho es un hecho de nombre, cambia también el nombre canónico de su personaje (`definitions.md` §2 Personaje).
- **Estados de la `Version`**: candidata → publicada | descartada. Número al publicar, capítulos cambiados, fecha de publicación y ruta del PDF; la versión vigente; solo una candidata admite escrituras.
- **Lecturas**: la story bible de una versión, con los capítulos que usan cada hecho, y su cronología registrada (§4.5), que lee 007-validador-lean. `GET /api/novels/{id}/story-bible?version={v}` (§15.7).

## Fuera de alcance

- Esquema SQLite (tablas, columnas, `create_all`) → 001-base.
- Cuándo nace cada candidata: la de generación al `Planificar` (§9.1) → 010-planificacion; reutilizarla al reanudar → 011-produccion-de-capitulos; la copia, tras revalidar la base (`stale_base`) → 014-cambios-del-lector y 019-edicion-manual.
- Aplicar el plan (mundo, reparto y lugares inventados, eventos planificados, outline, StyleSheet, título y CanonCards iniciales, §5.4) → 010-planificacion.
- Aceptar un capítulo y volver a aceptarlo: el capítulo y su huella, `UsoDeHecho` = los declarados ∪ la coincidencia literal, eventos registrados, tarjetas sucesoras y punto de control (§8.3) → 011-produccion-de-capitulos.
- Contenido, texto e incrustación de las CanonCards, recuperación y reconstrucción de las tarjetas de una entidad cuyo hecho cambia → 016-recuperacion-hibrida. Esta spec solo las copia.
- Validar una propuesta, añadir un hecho nuevo (y decidir su origen) y calcular los capítulos afectados → 014-cambios-del-lector. Los hechos cambiados de una edición manual → 019-edicion-manual. Las dos usan 009-C15 y 009-C16.
- Cuándo se publica y la transacción que envuelve la publicación (gate superado, PDF generado, solicitud o edición `applied`, scores) → 012-gate-de-publicacion. Cuándo se descarta (la ejecución termina `failed`) → 011-produccion-de-capitulos.
- `FicheroDeCronologia` y su verificación → 007-validador-lean. Ficha, `VistaDeVersion`, lista de versiones y PDF → 013-lectura-y-pdf. `query_story_bible` → 015-servidor-mcp.
- El mecanismo de 401 y de 404 para lo ajeno → 002-autenticacion. Schema, comprobaciones y confirmación del brief, extracción y aceptación de hechos → 008-brief-y-entrevista.
- Lo que no es story bible: la relación del destinatario con el cliente, la ocasión, el género, el tono, la extensión, la dedicatoria, los deseos de trama y las listas prohibidas. El planner los lee del brief (010).

## Datos de las pruebas

Datos ficticios, construidos directamente en el almacén; los briefs, con el modelo del brief confirmado de 008.

- **F1.** Brief confirmado de la novela N1, creada el 2026-09-24 (año presente 2026).
  - Destinatario «Marta», 40 años, sin fecha de nacimiento; rasgos «curiosa» y «le encanta el mar» (obligatorio). Su nombre es obligatorio siempre.
  - Allegados: «Toby», animal, relación «perro», sin edad ni fecha (obligatorio); «Luis», persona, relación «hermano», 37 años; «Rosa», persona, relación «abuela», sin edad ni fecha.
  - Recuerdos: R1 «se perdió en la feria de su pueblo», a los 8 años, en «la feria del pueblo», con Luis (obligatorio); R2 «su primer baño en el mar», año 1990, en «la playa del faro», sin allegados; R3 «la abuela Rosa se marchó para siempre», a los 12 años, en «la estación», con Rosa, excluyente con Rosa como excluida.
  - Hechos extraídos: X1 (Marta, «comida favorita», «la paella»), verificado, aceptado y obligatorio; X2 (Toby, «color», «negro»), verificado y no aceptado.
- **F2.** Brief confirmado de otra novela creada el 2026-09-24. Destinatario «Leo», nacido el 2000-02-29 (26 años), con recuerdos a los 0, a los 4 y a los 5 años, y en los años 2000 y 2010.
- **V1.** Versión publicada v1 de N1: el canon de F1 más:
  - un mundo (novum tecnológico con fecha 2019-05-01, dos consecuencias y un hecho de mundo);
  - un personaje inventado «Iris» (artificial, sin fecha de nacimiento) con su hecho de nombre, y un lugar inventado «el mercado de datos»;
  - un evento planificado P1 (capítulo 1, beat 2) y dos registrados: E4 (capítulo 1, beat 2), el 2026-05-10 a las 18:00 en la feria del pueblo, con Marta y Toby; y E5 (capítulo 3, beat 1), el 2026-05-12 a las 10:00 en el mercado de datos, con Marta e Iris;
  - los 10 capítulos del outline, la StyleSheet y 10 capítulos con su huella;
  - `UsoDeHecho`: el nombre de Marta en 1–10, el de Toby en 3 y 7 y X1 en 5;
  - una CanonCard inicial por entidad y una sucesora de Marta con `desde_capitulo` 4, con su canal léxico y sus vectores.
- **V2.** Versión publicada v2 de N1: la copia de v1 con el hecho de nombre de Toby cambiado a «Nala» (009-C16) y los capítulos 3 y 7 reescritos.

## Comportamiento observable

Todos los casos son **T**: una prueba con estos datos decide sola, sin modelo ni red.

### Canon del brief

#### 009-C01 — La candidata de generación nace con el canon del brief (T)
- **Dado** N1 con F1 confirmado y sin ninguna versión
- **Cuando** se crea su candidata de generación
- **Entonces** existe una versión nueva de N1:
  - en estado candidata, sin versión base, sin número, sin capítulos cambiados ni PDF, y con su fecha de creación;
  - su story bible tiene exactamente 4 personajes, 3 lugares, 13 hechos y 3 eventos, todos de origen brief salvo el hecho de X1, de origen free_text;
  - no tiene mundo, outline, StyleSheet, capítulos, `UsoDeHecho` ni CanonCards: los escriben 010 y 011.

#### 009-C02 — El destinatario y los allegados pasan a personajes con su hecho de nombre (T)
- **Dado** la candidata de 009-C01
- **Cuando** se leen sus personajes y sus hechos
- **Entonces**:
  - Marta es destinataria y persona; Toby, allegado y animal; Luis y Rosa, allegados y personas; todos de origen brief;
  - el nombre canónico de cada uno es exactamente el del brief, y un destinatario «María José» conserva la tilde y el espacio;
  - cada personaje tiene un solo hecho de nombre (atributo `nombre`, valor = su nombre canónico, origen brief), y ese hecho es nominal;
  - ningún otro hecho del canon es nominal.

#### 009-C03 — La fecha de nacimiento es la declarada, la derivada de la edad o ninguna (T)
- **Dado** F1 y F2
- **Cuando** se crean sus candidatas de generación
- **Entonces**:
  - Marta nace el 1986-01-01 a las 00:00 (año presente − 40) y Luis el 1989-01-01;
  - Toby y Rosa no tienen fecha de nacimiento;
  - Leo conserva la declarada, 2000-02-29;
  - F1 en una novela creada el 2027-03-01 da a Marta el 1987-01-01: el año presente sale de la fecha de creación de la novela.

#### 009-C04 — Los rasgos, las relaciones y los hechos extraídos aceptados pasan a hechos (T)
- **Dado** la candidata de 009-C01
- **Cuando** se leen sus hechos
- **Entonces** están:
  - (Marta, `rasgo`, «curiosa») y (Marta, `rasgo`, «le encanta el mar»);
  - (Toby, `relación`, «perro»), (Luis, `relación`, «hermano») y (Rosa, `relación`, «abuela»), todos de origen brief;
  - (Marta, «comida favorita», «la paella»), de origen free_text: el sujeto del hecho extraído pasa a su personaje y conserva su atributo.
- **Y** X2, no aceptado, no está.
- **Y** un brief importado, cuyos hechos verificados llegan aceptados y no obligatorios (008), se escribe igual, con esos hechos de origen free_text y no obligatorios.

#### 009-C05 — Cada recuerdo da su hecho, su evento fechado y su lugar (T)
- **Dado** la candidata de 009-C01
- **Cuando** se leen sus hechos y sus eventos
- **Entonces**:
  - R1 da el hecho (Marta, `recuerdo`, «se perdió en la feria de su pueblo») y un evento con:
    - ese enunciado;
    - momento 1994-01-01 a las 12:00, el día en que Marta cumple 8;
    - lugar «la feria del pueblo»;
    - Marta presente con la edad declarada 8, y Luis presente sin edad;
    - tipo ordinario, sin capítulo ni beat, analepsis y origen brief;
  - R2 da su hecho y un evento el 1990-01-01 a las 12:00 en «la playa del faro», con solo Marta presente y sin edad declarada, porque el recuerdo declara un año.

#### 009-C06 — Un recuerdo excluyente nombra a su excluido (T)
- **Dado** la candidata de 009-C01
- **Cuando** se lee el evento de R3
- **Entonces**:
  - es excluyente, con Rosa como excluida, el 1998-01-01 a las 12:00 en «la estación», con Marta (edad declarada 12) y Rosa presentes;
  - los eventos de R1 y R2 son ordinarios y no tienen excluido.

#### 009-C07 — Hay un lugar del brief por cada nombre de lugar exacto (T)
- **Dado** F1 con dos recuerdos más: R4 «ganó un concurso de dibujo», a los 10 años, en «la feria del pueblo»; y R5 «montó en la noria», a los 9 años, en «La feria del pueblo»
- **Cuando** se crea su candidata de generación
- **Entonces**:
  - hay 4 lugares: «la feria del pueblo», que comparten los eventos de R1 y R4, «La feria del pueblo», «la playa del faro» y «la estación»;
  - todos son de origen brief y no tienen descripción.

#### 009-C08 — El fechado respeta los límites del calendario (T)
- **Dado** F2
- **Cuando** se crea su candidata de generación
- **Entonces** los eventos de sus recuerdos caen, siempre a las 12:00:
  - a los 0 años, el 2000-02-29, después del nacimiento de las 00:00;
  - a los 4, el 2004-02-29 (año bisiesto);
  - a los 5, el 2005-03-01 (el 29 de febrero cae el 1 de marzo en un año no bisiesto);
  - en el año 2000, el de su nacimiento, el 2000-03-01 (el día siguiente al nacimiento);
  - en el año 2010, el 2010-01-01.

#### 009-C09 — Cada elemento personal queda representado y los obligatorios, marcados (T)
- **Dado** la candidata de 009-C01
- **Cuando** se leen sus hechos
- **Entonces** cada hecho que representa un `ElementoPersonal` lleva el identificador del elemento en el brief:
  - el nombre de Marta, en su hecho de nombre;
  - cada rasgo, en su hecho de rasgo;
  - cada recuerdo, en su hecho de recuerdo (el evento no es un hecho);
  - cada allegado, en su hecho de nombre;
  - X1, en su hecho.
- **Y** el hecho es obligatorio si y solo si el elemento lo es. Hay exactamente 5: el nombre de Marta, «le encanta el mar», el nombre de Toby, el recuerdo R1 y X1.
- **Y** los hechos de relación no llevan elemento y no son obligatorios.

#### 009-C10 — Crear la candidata de generación es todo o nada (T)
- **Dado** N1 con F1 y un fallo provocado al escribir el último hecho
- **Cuando** se crea su candidata de generación
- **Entonces**:
  - no queda ninguna versión nueva ni ninguna fila de su canon;
  - repetirla sin el fallo da exactamente 009-C01.

### Copia de versión

#### 009-C11 — La copia reproduce la base entera y conserva la identidad (T)
- **Dado** N1 con V1
- **Cuando** se crea una candidata K copiando v1
- **Entonces**:
  - K es candidata, con v1 como versión base, sin número, sin capítulos cambiados ni PDF;
  - cada tabla de ámbito versión tiene en K las mismas filas que en v1, salvo la versión: mundo, personajes, lugares, hechos, `UsoDeHecho`, eventos de los tres orígenes y sus presentes, capítulos del outline, StyleSheet, capítulos, CanonCards y su canal léxico;
  - cada personaje, lugar, hecho y evento conserva en K el identificador que tenía en v1;
  - cada CanonCard conserva su entidad, su texto, su huella y su `desde_capitulo`;
  - toda referencia de K resuelve dentro de K (009-I2);
  - una búsqueda léxica de «feria» limitada a K devuelve las tarjetas de K que la contienen, las mismas que limitada a v1.

#### 009-C12 — La copia no vuelve a incrustar: comparte los vectores (T)
- **Dado** V1 con los vectores de sus CanonCards
- **Cuando** se crea K copiando v1
- **Entonces**:
  - el número de vectores guardados no cambia;
  - cada tarjeta de K encuentra su vector por su huella y el modelo de incrustación de N1.

#### 009-C13 — La base no cambia al copiarla ni al trabajar la candidata (T)
- **Dado** la huella de v1, calculada sobre su fila de versión y todas sus filas de ámbito versión
- **Cuando** se crea K copiando v1 y en K se cambia un hecho, se reescribe el capítulo 3, se borra un `UsoDeHecho`, se añade un evento registrado y K se publica como v2
- **Entonces** la huella de v1 es la misma antes de copiar, después de copiar y después de cada paso.

#### 009-C14 — Copiar es todo o nada (T)
- **Dado** V1 y un fallo provocado al copiar la última tabla
- **Cuando** se crea K copiando v1
- **Entonces**:
  - no queda ninguna versión nueva ni ninguna fila copiada, y la huella de v1 no cambia;
  - repetirla sin el fallo da exactamente 009-C11.

### Cambio de un hecho en la candidata

#### 009-C15 — Cambiar el valor de un hecho de la candidata (T)
- **Dado** K, copia de v1
- **Cuando** en K se cambia el valor del hecho de X1 a «el cocido»
- **Entonces**:
  - en K el hecho vale «el cocido» y conserva su identificador, su sujeto, su atributo, su origen free_text, su marca de obligatorio, su elemento personal y sus `UsoDeHecho`;
  - en v1 sigue valiendo «la paella».

#### 009-C16 — Cambiar un hecho de nombre cambia a la vez el nombre canónico (T)
- **Dado** K, copia de v1
- **Cuando** en K se cambia el hecho de nombre de Toby a «Nala», primero sin fallos y después con un fallo provocado entre las dos escrituras
- **Entonces**:
  - sin fallo, en K el hecho vale «Nala» y el nombre canónico de Toby es «Nala», en la misma operación;
  - con el fallo, ninguno de los dos cambia;
  - en v1, Toby sigue siendo «Toby».

### Estados de las versiones

#### 009-C17 — Publicar la primera versión (T)
- **Dado** G, candidata de generación de N1 con sus 10 capítulos, sin ninguna versión publicada
- **Cuando** se publica con la ruta de su PDF
- **Entonces**:
  - G queda publicada con el número 1, su fecha de publicación, capítulos cambiados vacíos y esa ruta del PDF;
  - la versión vigente de N1 es v1.

#### 009-C18 — Publicar una copia: número siguiente y capítulos cambiados por huella (T)
- **Dado** v1 vigente y K, copia de v1, en la que:
  - el capítulo 3 tiene otro texto;
  - el capítulo 7 tiene otro título y el mismo texto;
  - el capítulo 5 se reescribió con el mismo título y el mismo texto, y conserva la huella
- **Cuando** se publica K
- **Entonces**:
  - K es v2, con capítulos cambiados [3, 7];
  - v1 sigue publicada y sin cambios;
  - la versión vigente es v2.

#### 009-C19 — Descartar una candidata (T)
- **Dado** v2 vigente y K3, copia de v2
- **Cuando** se descarta K3
- **Entonces**:
  - K3 queda descartada y sin número;
  - la versión vigente sigue siendo v2;
  - la siguiente candidata de N1 que se publique recibe el número 3: una descartada no consume número.

#### 009-C20 — Las transiciones que no salen de una candidata válida se rechazan (T)
- **Dado** N1 con v1, v2 vigente y K3 descartada
- **Cuando** se intenta cada operación de la tabla
- **Entonces** cada una se rechaza con un error que nombra la versión y el motivo.
- **Y** la huella de cada versión no cambia, y una candidata rechazada sigue siendo candidata.

| Operación | Motivo del rechazo |
|---|---|
| Publicar v2 otra vez | ya está publicada |
| Descartar v2 | está publicada |
| Publicar o descartar K3 | está descartada |
| Publicar K2, copia de v1, con v2 vigente | su versión base no es la vigente |
| Publicar una candidata de generación de N1, sin base, con v1 publicada | ya hay una versión publicada |

#### 009-C21 — Solo una candidata admite escrituras (T)
- **Dado** v1 (publicada), K3 (descartada) y una candidata K4
- **Cuando** en cada una se intenta:
  - insertar, modificar o borrar una fila de cada tabla de ámbito versión;
  - cambiar un hecho (009-C15);
  - modificar su fila de versión (número, versión base, capítulos cambiados, ruta del PDF, fechas)
- **Entonces**:
  - en v1 y en K3 cada intento se rechaza con un error que nombra la versión y su estado, y su huella no cambia;
  - en K4, las escrituras en sus tablas de ámbito versión se aceptan.

#### 009-C22 — La versión vigente es la publicada de número más alto (T)
- **Dado** N2 sin versiones publicadas; N1 con v1, v2, una candidata y K3 descartada; y N3 con v1 a v4
- **Cuando** se pide la versión vigente de cada novela
- **Entonces** N2 no tiene ninguna, la de N1 es v2 y la de N3 es v4. Las versiones de N3 no afectan a N1.

### Lecturas

#### 009-C23 — La cronología registrada de una versión (T)
- **Dado** V1 y la candidata G de 009-C01, todavía sin plan
- **Cuando** se pide la cronología registrada de cada una
- **Entonces** la de v1 tiene:
  - los eventos de origen brief y los registrados, en este orden: R2, R1, R3, E4 y E5;
  - cada evento con su enunciado, su momento, su lugar, sus presentes con la edad declarada si la hay, su tipo, su excluido, su analepsis, su origen y su capítulo y beat;
  - las fechas de nacimiento de Marta y Luis, y de nadie más;
  - la fecha del novum, 2019-05-01.
- **Y** el evento planificado P1 no está.
- **Y** la de G tiene los 3 eventos del brief y las dos fechas de nacimiento, sin fecha de novum.
- **Y** el orden es por momento y, a igual momento, por identificador.

#### 009-C24 — La story bible de una versión, por su identificador (T)
- **Dado** V1 y la candidata G
- **Cuando** se pide la story bible de cada una por el identificador de su versión
- **Entonces** la de v1 tiene:
  - el año presente, 2026;
  - el mundo, con su novum y sus consecuencias;
  - los 5 personajes y los 4 lugares, con sus atributos;
  - los 15 hechos, cada uno con los capítulos que lo usan en orden ascendente: el nombre de Marta en 1–10, el de Toby en 3 y 7, X1 en 5 y el resto sin capítulos;
  - la cronología registrada de 009-C23.
- **Y** la de G es el canon de F1, sin mundo y con todos los hechos sin capítulos.
- **Y** esta lectura sirve a una candidata (la usan 010 a 016); la API no llega a las candidatas.

#### 009-C25 — La API devuelve la story bible de la versión vigente (T)
- **Dado** N1 con V1, V2 y una candidata abierta, y el `TokenDeAcceso` de su cliente
- **Cuando** pide `GET /api/novels/{N1}/story-bible` sin `version`
- **Entonces** responde 200 con el número 2 y la story bible de v2, con el contenido de 009-C24. En ella, el personaje y el hecho de nombre de Toby valen «Nala».
- **Y** nada de la candidata aparece.

#### 009-C26 — La API devuelve la story bible de una versión anterior (T)
- **Dado** lo mismo que en 009-C25
- **Cuando** pide `GET /api/novels/{N1}/story-bible?version=1`
- **Entonces** responde 200 con la story bible de v1: el personaje y el hecho de nombre de Toby valen «Toby».
- **Y** ese personaje y ese hecho tienen en v1 los mismos identificadores que en v2.

#### 009-C27 — La API rechaza lo que no existe, lo mal formado, lo anónimo y lo ajeno (T)
- **Dado** N1 como en 009-C25, N2 sin versiones publicadas y el cliente B, que no posee N1
- **Cuando** se pide cada petición de la tabla
- **Entonces** responde lo de la tabla, sin revelar nada de N1 a quien no es su cliente.

| Petición | Respuesta |
|---|---|
| La de N2, sin `version`, por su cliente | 404 |
| La de N1 con `version=3`, por su cliente | 404 |
| La de N1 con `version=0`, `version=-1` o `version=uno` | 422 |
| La de N1 sin token | 401 (002-autenticacion) |
| La de N1 con el token de B, con o sin `version` | 404, idéntica a la de una novela inexistente (002-autenticacion) |

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 009-I1 | Solo una candidata admite escrituras. Una versión publicada o descartada no cambia nunca, ni su fila ni sus tablas de ámbito versión | T | 009-C13, 009-C20 y 009-C21. Refuerzo A: `VersionAnteriorConservada` (006) |
| 009-I2 | Cada versión es autocontenida: toda referencia de una fila de ámbito versión a otra entidad resuelve en su misma versión. Cuenta el sujeto de un hecho, el hecho de un `UsoDeHecho`, el lugar, los presentes y el excluido de un evento, y la entidad de una CanonCard | T | Una prueba recorre todas las referencias tras 009-C01, 009-C11, 009-C15 y 009-C16 |
| 009-I3 | Una lectura de una versión (story bible, cronología registrada o vigente) nunca devuelve filas de otra versión ni de otra novela | T | Dos novelas con los mismos nombres y varias versiones: cada lectura trae solo lo suyo (`verification.md` §4.9, RT5 y RT6) |
| 009-I4 | Crear una candidata, de generación o por copia, es todo o nada | T | 009-C10 y 009-C14 |
| 009-I5 | La historia de versiones es lineal. Los números publicados de una novela son 1..n en orden de publicación. Cada publicada tiene por base la anterior, y la 1 no tiene base. La vigente es la n. Candidatas y descartadas no tienen número | T | Prueba basada en propiedades (`verification.md` §3.4): secuencias al azar de crear la de generación, copiar la vigente, publicar y descartar. Refuerzo A: `VersionesLineales` (006) |
| 009-I6 | El nombre canónico de cada personaje es el valor de su hecho de nombre | T | Tras 009-C01, 009-C11 y 009-C16, y tras el cambio que falla a medias |
| 009-I7 | Todo `ElementoPersonal` del brief tiene al menos un hecho que lo representa, y el de uno obligatorio es obligatorio. Sin esto, `elementos-obligatorios` no podría pasar nunca | T | Prueba basada en propiedades sobre briefs confirmados con números de allegados, recuerdos y hechos extraídos al azar y marcas de obligatorio al azar, además de 009-C09 |
| 009-I8 | El valor de un hecho de origen brief o free_text solo cambia por una `SolicitudDeCambio` o una `EdicionManual`, y solo en su candidata. Ningún rol escribe canon | I | El `verificador`, al cerrar 010, 011, 014 y 019, comprueba que solo 014 y 019 invocan 009-C15 y 009-C16, y que los roles entregan por tool sin persistir (003) |

## Scores y trazas

No aplica. La 009 no ejecuta validadores ni abre sesiones de rol. Sus escrituras ocurren dentro de la traza de la ejecución que las pide.

## Docs referenciados

- `architecture.md`:
  - §4.1 (canon del brief), §4.3 (inmutabilidad), §4.5 (cronología registrada);
  - §6.3 (vectores por huella y modelo), §6.4 (índice en la misma transacción al copiar);
  - §9.1 (quién dispara cada transición), §9.3 (versiones), §9.4 (publicación, como consumidor), §10.1–§10.3 (hechos cambiados y versión base, como consumidores);
  - §14.3 (propiedad), §15.6 (tablas de ámbito versión), §15.7 (`GET /api/novels/{id}/story-bible`, 401/404/422), §15.9 (contratos entre carriles).
- `definitions.md`:
  - §1 (Destinatario, Allegado, Recuerdo, HechoExtraido, Brief, ElementoPersonal);
  - §2 (StoryBible, Personaje y variante de nombre, Lugar, Hecho y hecho nominal, UsoDeHecho, Evento, Cronologia);
  - §3 (Novela y versión vigente, Version y capítulo cambiado, Capitulo y huella), §4 (CanonCard);
  - §11.2 (vocabulario de atributos), §12.4 (enumerados).
- `domain-knowledge.md` §5.2 (fechado de nacimientos y recuerdos), §5.3 (T2–T5, que usan presentes, edades y excluidos).
- `verification.md` §2 (clases), §3.3 (integración con el almacén), §3.4 (propiedades), §4.9 (RT5, RT6), §5 (filas 2.11, 4.1, 4.2 y 4.3).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué posee la 009? | El canon del brief, la copia, el cambio de valor de un hecho, los estados y el número de las versiones, los capítulos cambiados, la vigente, las lecturas y `GET story-bible` | `TODO.md` (Specs), `backend/AGENTS.md` (propiedad), `verification.md` §5 filas 2.11 y 4.1–4.3 |
| ¿Quién decide cuándo? | La ejecución que llama. 010 crea la candidata de generación; 014 y 019 copian tras revalidar; 012 publica tras el gate; 011 descarta al fallar | `architecture.md` §9.1, §9.3 |
| ¿Publicar es de la 009 o de la 012? | De la 009, el cambio de estado de la versión: número, fecha, capítulos cambiados, ruta del PDF y la guarda de base vigente. De la 012, cuándo se publica y la transacción que lo envuelve | `architecture.md` §9.3, §9.4 |
| ¿Cómo se fecha un recuerdo? | A las 12:00. Con edad, el día que la cumple. Con año, el 1 de enero, o el día siguiente al nacimiento si es el año en que nació. El 29 de febrero cae el 1 de marzo | `domain-knowledge.md` §5.2 |
| ¿Quién está presente en un recuerdo? | El destinatario, con la edad que declare el recuerdo, y los allegados presentes. La edad declarada de un presente solo tiene sentido si el destinatario lo está | `definitions.md` §1 Recuerdo, §2 Evento. **Decisión para §18** |
| ¿Qué hecho representa a cada elemento? | El suyo; un allegado, por su hecho de nombre. El identificador del elemento va en todo hecho que representa un elemento, y la marca de obligatorio solo en el de uno obligatorio | `definitions.md` §1 ElementoPersonal, `architecture.md` §4.1. **Decisión para §18** |
| ¿Un lugar por recuerdo o por nombre? | Por nombre exacto, sin descripción | `definitions.md` §2 Lugar. **Decisión para §18** |
| ¿Capítulo y analepsis de un evento del brief? | Sin capítulo ni beat, y analepsis: es pasado de la vida del destinatario. T1 no lo mira | `definitions.md` §2 Evento. **Decisión para §18** |
| ¿Identificadores nuevos o conservados al copiar? | Conservados. Así una selección hecha sobre la base vale en la candidata, la copia no reescribe referencias y la lectura enlaza el mismo hecho entre versiones | **Decisión para §18**; condiciona el esquema de 001 |
| ¿Una descartada se puede escribir? | No: es terminal, como una publicada | `definitions.md` §5 Ejecucion. **Decisión para §18** |
| ¿Capítulos cambiados contra la base o contra la anterior publicada? | Contra la base. Coinciden al publicar, porque la historia es lineal y la publicación exige base vigente | `definitions.md` §3 Version, `architecture.md` §9.3, §10.2 |
| ¿Qué cronología expone la API? | La registrada: lo que dice el texto, como Lean | `architecture.md` §4.5. **Decisión para §18** |
| ¿Y sin `version`, o sin versión publicada? | La vigente; si no hay ninguna publicada, 404 | `architecture.md` §15.7. **Decisión para §18** |
| ¿Quién calcula el `UsoDeHecho`? | 011: los declarados ∪ la coincidencia literal. La 009 lo copia y lo lee | `architecture.md` §8.3 |
| ¿Qué atributos usan los hechos del brief? | `nombre` (nominal), `rasgo`, `recuerdo` y `relación`. Un hecho extraído conserva el suyo | `definitions.md` §2 Hecho, §11.2 |
| ¿De qué depende de verdad? | Del modelo del brief (008) y de la autenticación (002), que la tabla no lista | **Hueco de `TODO.md`** |
| ¿Y dos recuerdos con la misma edad o el mismo año y lugares distintos? | §5.2 les da el mismo momento. T3 falla con un testigo solo del brief, y la ejecución acaba `failed` con `unattributable_defect` | **Hueco del doc**: `domain-knowledge.md` §5.2, o una comprobación del brief en 008 |
| ¿De dónde salen el tipo y el excluido de un recuerdo? | Los pide `architecture.md` §4.1, pero `definitions.md` §1 Recuerdo no los lista | **Hueco del doc** |
