# 016 — Recuperación híbrida

> Carril: D · Depende de: 009-story-bible-y-versiones · Estado: borrador

## Objetivo

Dar al writer y al editor del capítulo *n* las CanonCards que les hacen falta, sin que ningún rol pida contexto. La spec entrega dos cosas. La primera es una colección de CanonCards por versión que siempre coincide con su story bible. La segunda es el recuperador híbrido: canal léxico BM25 y canal denso, fusionados por RRF, con corte temporal, desempate estable y sin re-ranking. Es determinista y se prueba en clase T sin modelo (`architecture.md` §6.3). El RAG es una de las piezas de dificultad deliberada del proyecto (ADR 0006).

## Alcance

- **Plantilla** de la CanonCard para cada tipo de entidad (personaje, lugar, mundo) y su huella.
- **Cadena de tarjetas** de cada entidad (iniciales y sucesoras) y la operación **sincronizar las CanonCards de una versión** con su story bible. Cada punto de escritura de `architecture.md` §6.4 la llama dentro de su propia transacción.
- **Vectores de incrustación** por (huella, modelo), con el modelo de incrustación de la novela. Aquí nacen el puerto del modelo de incrustación y su doble de vectores fijos (contrato con doble, `architecture.md` §15.9).
- **Recuperador**: corte temporal, canal léxico, canal denso, fusión RRF, desempate estable y `retrieval.top_k.<rol>`.
- **Las dos consultas**: la prospectiva del writer y la retrospectiva del editor.
- **Demostraciones con el modelo real**: que carga en el portátil (`architecture.md` §17.2) y una línea base dorada para la iteración de tuning.

## Fuera de alcance

- Ensamblar la `VentanaDeContexto` (residentes, resúmenes 1..*n*−1, final literal del *n*−1, entradas de la llamada), decidir cuándo se recupera y cómo se presentan las tarjetas al rol → 011-produccion-de-capitulos (`architecture.md` §6.1, §6.2).
- Las transacciones que cambian la story bible y llaman a la sincronización son de otras specs:
  - aplicar el plan → 010-planificacion;
  - aceptar un capítulo → 011-produccion-de-capitulos;
  - volver a aceptarlo en la reescritura dirigida → 012-gate-de-publicacion;
  - aplicar hechos cambiados → 014-cambios-del-lector y 019-edicion-manual;
  - copiar la candidata, con sus filas de tarjetas y del canal léxico, y la inmutabilidad de una versión publicada → 009-story-bible-y-versiones.
- Guardar `retrieval.embedding_model` en la novela cuando se crea → 008-brief-y-entrevista.
- Otras piezas previas:
  - el esquema (tarjetas, canal léxico con su tokenizador sin diacríticos, vectores y el modelo de la novela), la carga de las extensiones de la base y la validación de las claves `retrieval.*` → 001-base;
  - que la biblioteca de incrustación se pueda importar en Windows → 000-scaffolding (000-C04).
- La reserva del tamaño de la ventana en el `TechoDeTokens` → 003-puerto-de-agente y 011-produccion-de-capitulos.
- Los valores de `retrieval.embedding_model` y `retrieval.top_k` → iteración de tuning (`architecture.md` §17.1), 020-evals.
- La `FichaDePersonajes`, que sale de la story bible y no de las tarjetas → 013-lectura-y-pdf.
- Juez, planner, entrevistador, extractor y revisor visual, que no recuperan (`architecture.md` §6.2).
- Descartado por decisión (ADR 0006): re-ranking, segunda colección, prosa recuperada, cuotas por consumidor y deltas de estado.

## Reglas

Son la regla común de los casos. Los términos son los de `definitions.md` §2–§4.

**Participar en un evento.** Un personaje participa en un evento si está presente o si es su excluido. Un lugar participa si el evento ocurre en él.

**Plantilla.** Es el texto que el código escribe para una entidad y un capítulo *d*. Sale solo de la story bible de la versión y siempre en el mismo orden. Ese orden lo fija el contenido, nunca el id de las filas. Cada tarjeta contiene:

- **personaje**: nombre canónico, tipo, especie y fecha de nacimiento, si la tiene; sus hechos (atributo y valor); los eventos en que participa;
- **lugar**: nombre canónico y descripción; sus hechos; los eventos que ocurren en él;
- **mundo**: el novum (descripción, ámbito y fecha), sus consecuencias y los hechos del mundo.

Entran los eventos de origen brief y los registrados en capítulos anteriores a *d*. Cada uno lleva momento, lugar, presentes, enunciado y, si es excluyente, a quién excluye. Los eventos planificados no entran nunca, y tampoco el texto ni el resumen de ningún capítulo. Los nombres son los canónicos vigentes. La huella es la del texto.

**Aparecer.** Una entidad **aparece en los beats** de un capítulo si cumple una de estas condiciones: está entre los personajes de uno de sus beats; participa en uno de sus eventos planificados; o es sujeto de un hecho que el beat usa. **Aparece registrada** en un capítulo según la regla de la `FichaDePersonajes`: tiene un `UsoDeHecho` en él, o participa en uno de sus eventos registrados.

**Cadena de una entidad.**

- **Primera tarjeta.** Tiene `desde_capitulo` = 1 si la entidad es de origen brief o es el mundo. Si la entidad es inventada, su `desde_capitulo` es el menor de estos dos: el primer capítulo en cuyos beats aparece, y el siguiente al primero en que aparece registrada. Una inventada que no aparece en ningún beat ni en ningún capítulo aceptado no tiene tarjeta.
- **Sucesora.** Hay una sucesora con `desde_capitulo` = *d* (hasta 11) cuando la plantilla en *d* difiere de la plantilla en *d* − 1.

Mientras los capítulos se aceptan en orden, esta cadena es la regla de `architecture.md` §6.3: tarjetas iniciales al aplicar el plan, y una sucesora en *n*+1 si el capítulo *n* trae eventos nuevos de la entidad. La cadena además cubre tres situaciones:

- volver a aceptar un capítulo, que sustituye sus sucesoras;
- cambiar un hecho, que reconstruye las tarjetas de su entidad;
- una entidad que aparece antes de lo planeado.

**Sincronizar** deja las CanonCards de una versión iguales a la cadena de cada entidad. Crea las que faltan, retira las que sobran y no toca las iguales. Si no hay nada que cambiar, no escribe nada.

**Consultas.** Cada consulta se divide en fragmentos:

- **Prospectiva** (writer del capítulo *n*, en cualquiera de sus modos): un fragmento por beat del capítulo *n* del outline de la versión, con la descripción del beat y los enunciados de sus eventos planificados.
- **Retrospectiva** (editor del capítulo *n*): el texto del capítulo que recibe el editor, con un fragmento por párrafo.

**Recuperar para el capítulo *n*.**

1. **Elegibles**: por entidad, la tarjeta de la versión con mayor `desde_capitulo` ≤ *n* (corte temporal).
2. **Canal léxico**:
   - una palabra es una secuencia de letras y dígitos, y se compara sin mayúsculas ni diacríticos;
   - son candidatas las elegibles que comparten al menos una palabra con la consulta;
   - se ordenan por BM25 con k1 = 1,2 y b = 0,75, e IDF = ln(1 + (N − df + 0,5) / (df + 0,5)); N, df y la longitud media se calculan sobre las elegibles;
   - cada palabra distinta de la consulta cuenta una vez.
3. **Canal denso**: para cada elegible, la distancia coseno entre su vector y el de cada fragmento de la consulta. Cuenta la menor. Entran todas las elegibles.
4. **Rangos**: en cada canal, desde 1. Los empates se resuelven por la clave estable, con rangos consecutivos.
5. **RRF**: la puntuación de una tarjeta es Σ 1 / (60 + rango), sobre los canales en que aparece.
6. **Orden**: por RRF descendente. Los empates se resuelven por la **clave estable**: tipo de entidad (personaje, lugar, mundo, el orden del enumerado), después id de la entidad y después `desde_capitulo`, todo ascendente.
7. **Entrega**: las `retrieval.top_k.writer` primeras en la consulta prospectiva y las `retrieval.top_k.editor` primeras en la retrospectiva. Si hay menos elegibles, se entregan todas.

Las consultas se incrustan con el modelo de la novela y no se guardan.

## Comportamiento observable

Los casos de clase T usan la base real y un doble del modelo de incrustación que devuelve los vectores fijos que declara cada prueba. Así lo pide `architecture.md` §6.3: el recuperador se prueba sin modelo. Los casos de clase D usan el modelo real, en el portátil. Ninguno gasta cuota de la suscripción, porque el modelo de incrustación corre en local.

### 016-C1 — Tarjetas iniciales al aplicar el plan (T)
- **Dado** una versión con la story bible y el outline recién aplicados, sin ningún capítulo aceptado, con estas entidades:
  - de origen brief: el destinatario, su perro (un allegado) y el lugar de un recuerdo;
  - el mundo;
  - un personaje inventado que aparece por primera vez en los beats del capítulo 4;
  - un lugar inventado donde ocurre un evento planificado del capítulo 2;
  - un personaje inventado que no aparece en ningún beat
- **Cuando** se sincronizan sus CanonCards
- **Entonces**:
  - hay exactamente una tarjeta por cada entidad que aparece;
  - el destinatario, el perro, el lugar del recuerdo y el mundo tienen `desde_capitulo` 1; el personaje inventado, 4; el lugar inventado, 2;
  - el personaje sin beats no tiene tarjeta;
  - cada tarjeta tiene su vector, calculado con el modelo de la novela

### 016-C2 — Qué dice una tarjeta (T)
- **Dado** una versión con el capítulo 2 aceptado, con su texto y su resumen, y con estas entidades:
  - un personaje con tres hechos, presente en un evento de origen brief, en un evento registrado del capítulo 2 y en un evento planificado del capítulo 5;
  - un allegado excluido por un recuerdo excluyente;
  - un lugar donde ocurre el evento registrado;
  - el mundo, con su novum, tres consecuencias y un hecho del mundo
- **Cuando** se sincroniza y se leen las tarjetas vigentes en los capítulos 2 y 3
- **Entonces**:
  - en el 3, la tarjeta del personaje trae su nombre canónico, tipo, especie, fecha de nacimiento y sus tres hechos, más el evento de origen brief y el registrado, cada uno con momento, lugar, presentes y enunciado;
  - en el 2, la tarjeta del personaje no trae el evento registrado del capítulo 2;
  - la tarjeta del allegado trae el recuerdo que lo excluye, marcado como excluyente;
  - la del lugar trae su descripción y el evento registrado;
  - la del mundo trae el novum, las tres consecuencias y el hecho;
  - ninguna tarjeta contiene el evento planificado del capítulo 5, ni ninguna frase del texto o del resumen del capítulo 2

### 016-C3 — Aceptar un capítulo crea sucesoras solo donde algo cambia (T)
- **Dado** la versión de 016-C1
- **Cuando** se acepta el capítulo 3 y se sincroniza. El capítulo trae un evento registrado en el lugar del recuerdo, con el perro presente, y un `UsoDeHecho` de un rasgo del destinatario
- **Entonces**:
  - nacen exactamente dos sucesoras con `desde_capitulo` 4, la del perro y la del lugar, y las dos traen ese evento;
  - el destinatario no tiene sucesora: un uso no cambia su tarjeta;
  - ninguna tarjeta con `desde_capitulo` ≤ 3 cambia de texto ni de huella, y ninguna desaparece

### 016-C4 — Una entidad aparece antes de lo planeado (T)
- **Dado** la versión de 016-C1, donde el personaje inventado tiene su tarjeta desde el capítulo 4
- **Cuando** se acepta el capítulo 2 con un evento registrado en el que ese personaje está presente, y se sincroniza
- **Entonces**:
  - su primera tarjeta tiene `desde_capitulo` 3 y trae ese evento;
  - del capítulo 3 en adelante no rige ninguna tarjeta suya sin ese evento;
  - en el capítulo 2 no tiene ninguna tarjeta elegible

### 016-C5 — Volver a aceptar un capítulo (T)
- **Dado** una candidata con los 10 capítulos aceptados. El capítulo 3 registró el evento E1 con el perro presente, y el capítulo 5 registró otro evento con el perro presente
- **Cuando** el capítulo 3 se vuelve a aceptar con el evento E2 en lugar de E1, y se sincroniza
- **Entonces**:
  - toda tarjeta del perro con `desde_capitulo` ≥ 4 trae E2 y ninguna trae E1, incluida la sucesora que nació del capítulo 5;
  - ninguna tarjeta con `desde_capitulo` ≤ 3 cambia

### 016-C6 — Un hecho cambiado reconstruye las tarjetas de su entidad (T)
- **Dado** una candidata copiada de su versión base publicada, donde el perro se llama «Toby» y está presente en un evento registrado en un lugar inventado
- **Cuando** el hecho de nombre del perro pasa a «Nala», junto con su nombre canónico, como hace 014-cambios-del-lector, y se sincroniza la candidata
- **Entonces**:
  - todas las tarjetas del perro, con cualquier `desde_capitulo`, llevan «Nala» como nombre y como valor de ese hecho, y ninguna lleva «Toby» en ninguno de los dos;
  - las tarjetas del lugar nombran a «Nala» entre los presentes;
  - las tarjetas de las entidades sin relación no cambian;
  - las tarjetas de la versión base siguen iguales

### 016-C7 — Vectores por huella y modelo (T)
- **Dado** una versión publicada con sus tarjetas, una candidata recién copiada de ella (009-story-bible-y-versiones) y un doble del modelo que cuenta sus llamadas
- **Cuando** se hace esto:
  1. se sincroniza la candidata;
  2. se sincroniza otra novela con el mismo modelo, cuya story bible da una tarjeta con el mismo texto que una de la primera;
  3. se sincroniza un cambio que retira una tarjeta
- **Entonces**:
  - sincronizar la copia no crea, retira ni cambia ninguna tarjeta, y no llama al modelo;
  - la tarjeta con el mismo texto de la otra novela usa el vector que ya existía, sin llamar al modelo;
  - cada texto nuevo provoca exactamente una llamada;
  - retirar una tarjeta no borra su vector, y ningún vector cambia nunca

### 016-C8 — El modelo es el de la novela, no el de la config (T)
- **Dado** una novela creada con el modelo A cuando la config ya dice B, y otra novela creada con B
- **Cuando** se sincronizan las dos y se recupera en ellas
- **Entonces**:
  - la primera incrusta tarjetas y consultas solo con A, y la segunda solo con B;
  - un mismo texto de tarjeta tiene en las dos novelas dos vectores, uno por modelo

### 016-C9 — Todo o nada con la transacción del llamante (T)
- **Dado** un punto de escritura que cambia la story bible y sincroniza, todo en la misma transacción
- **Cuando** la transacción se deshace después de sincronizar, o bien se confirma
- **Entonces**:
  - si se deshace, no queda nada de lo que escribió la sincronización (ni tarjetas, ni entradas del canal léxico, ni vectores), y las tarjetas y la story bible siguen como antes y de acuerdo entre sí;
  - si se confirma, las dos quedan a la vez;
  - la sincronización nunca confirma por su cuenta

### 016-C10 — Corte temporal (T)
- **Dado** una versión donde el perro tiene tarjetas con `desde_capitulo` 1 y 4, y un lugar inventado tiene una tarjeta con `desde_capitulo` 6
- **Cuando** se recupera en los capítulos 3, 4 y 6 con un `top_k` mayor que el número de tarjetas
- **Entonces**:
  - en el 3 sale la del perro desde 1, pero no la desde 4 ni la del lugar;
  - en el 4 sale la del perro desde 4, pero no la desde 1;
  - en el 6 salen la del perro desde 4 y la del lugar;
  - nunca salen dos tarjetas de la misma entidad

### 016-C11 — El canal léxico compara palabras, sin mayúsculas ni acentos (T)
- **Dado** tarjetas elegibles con las palabras «Toby», «árbol» y «examen», y otras que no las tienen
- **Cuando** la consulta es «TÓBY», «arbol» o «ex»
- **Entonces**:
  - «TÓBY» hace candidata a la tarjeta de «Toby», y «arbol» a la de «árbol»;
  - «ex» no hace candidata a la de «examen»;
  - una tarjeta entra en el ranking léxico si y solo si comparte al menos una palabra con la consulta; las demás solo tienen rango denso

### 016-C12 — BM25 con las estadísticas de la versión en el capítulo *n* (T)
- **Dado** cinco tarjetas elegibles en el capítulo 5: «faro» aparece en una y «tormenta» en cuatro
- **Cuando** la consulta es «faro tormenta»
- **Entonces**:
  - en el canal léxico, la tarjeta del faro va por delante de cualquiera que solo tenga «tormenta»;
  - el ranking léxico y sus puntuaciones quedan exactamente iguales si se añade cualquiera de estas: cincuenta tarjetas con «faro» en otra novela; esas mismas tarjetas en otra versión de la misma novela; una tarjeta futura (`desde_capitulo` 8) de esta versión; o una tarjeta sustituida de esta versión, es decir, una de `desde_capitulo` menor de una entidad que tiene una sucesora vigente

### 016-C13 — Consultas con signos de búsqueda o sin palabras (T)
- **Cuando** la consulta contiene comillas, asterisco, paréntesis, dos puntos, acento circunflejo, guion o las palabras AND, OR, NOT y NEAR en mayúsculas; o no contiene ninguna palabra («¡¿…?!»)
- **Entonces**:
  - nunca hay error;
  - con signos, el resultado es el mismo que con el texto sin esos signos, y esas palabras se buscan como palabras;
  - sin palabras, el canal léxico queda vacío y el orden es el del canal denso

### 016-C14 — El canal denso compara por fragmentos (T)
- **Dado** vectores fijos en los que solo el último párrafo de un capítulo está cerca de la tarjeta Z, y solo el segundo beat de un capítulo está cerca de la tarjeta Y
- **Cuando** el editor recupera con ese texto y el writer con esos beats
- **Entonces**:
  - Z es la primera del canal denso del editor, aunque los párrafos anteriores no se parezcan a ninguna tarjeta;
  - Y es la primera del canal denso del writer;
  - todas las elegibles tienen rango denso

### 016-C15 — Fusión RRF con k = 60 (T)
- **Dado** cuatro tarjetas elegibles con estos rangos:

  | Tarjeta | Léxico | Denso |
  |---|---|---|
  | A | 1 | 3 |
  | B | 2 | 1 |
  | C | — | 2 |
  | D | — | 4 |

- **Cuando** se funden
- **Entonces** sus puntuaciones son 1/61 + 1/63, 1/62 + 1/61, 1/62 y 1/64, y el orden es B, A, C, D

### 016-C16 — Desempate estable (T)
- **Dado**:
  - dos tarjetas con la misma puntuación RRF (una con léxico 1 y denso 2, la otra con léxico 2 y denso 1): un lugar de id 7 y un personaje de id 9;
  - dos personajes de ids 3 y 5 en la misma situación;
  - dos tarjetas con la misma puntuación BM25
- **Cuando** se recupera dos veces
- **Entonces**:
  - el personaje 9 va antes que el lugar 7, porque el tipo decide primero;
  - el personaje 3 va antes que el 5;
  - dentro de un canal, las empatadas reciben rangos consecutivos por la misma clave;
  - las dos recuperaciones dan el mismo orden

### 016-C17 — Consulta prospectiva del writer (T)
- **Dado**:
  - los beats del capítulo 5 nombran el faro y los del 6 nombran el mercado;
  - las tarjetas del faro y del mercado son elegibles en el 5;
  - los vectores fijos no distinguen entre ellas;
  - `retrieval.top_k.writer` = 1
- **Cuando** el writer del capítulo 5 recupera, al escribir, al reescribir o al revisar
- **Entonces**:
  - recibe la tarjeta del faro;
  - la consulta sale solo de los beats del capítulo 5 de esa versión (su descripción y los enunciados de sus eventos planificados): ni del texto de ningún capítulo ni de los beats de otros capítulos

### 016-C18 — La consulta retrospectiva del editor tiene otro punto ciego (T)
- **Dado** lo mismo que en 016-C17, un texto del capítulo 5 que menciona el mercado y no el faro, y `retrieval.top_k.editor` = 1
- **Cuando** el editor del capítulo 5 recupera con ese texto
- **Entonces**:
  - recibe la tarjeta del mercado y no la del faro;
  - el writer y el editor del mismo capítulo reciben tarjetas distintas

### 016-C19 — `top_k` por rol y escasez (T)
- **Dado** una config de prueba con `retrieval.top_k.writer` = 2 y `retrieval.top_k.editor` = 3, una versión con seis elegibles en el capítulo 1 y otra versión con una sola elegible
- **Cuando** el writer y el editor recuperan en las dos versiones
- **Entonces**:
  - en la primera, el writer recibe 2 tarjetas y el editor 3, en el orden de la fusión;
  - en la segunda, los dos reciben la única elegible, sin error

### 016-C20 — Sin modelo no hay recuperación a medias (T)
- **Dado** un doble del modelo que falla, porque no carga o porque no devuelve vector
- **Cuando** se recupera, o se sincroniza una versión con una tarjeta nueva
- **Entonces**:
  - la recuperación termina con un error explícito que nombra el modelo, y nunca devuelve el resultado del canal léxico solo;
  - la sincronización termina con error y no deja ninguna tarjeta, ni con vector ni sin él;
  - el llamante recibe el error. Lo que hace la ejecución con él es de 011-produccion-de-capitulos

### 016-C21 — El modelo real carga en el portátil (D)
- **Dado** el portátil Windows con Smart App Control en Enforce, sin caché del modelo, con el `retrieval.embedding_model` de la config
- **Cuando** se sincronizan las tarjetas de una story bible ficticia de fixture, se recupera para el writer y para el editor de un capítulo, y se repite todo
- **Entonces**:
  - el modelo se descarga una sola vez y carga sin bloqueo;
  - sus ficheros quedan dentro del directorio de datos y en ningún otro sitio (`architecture.md` §12.6);
  - cada tarjeta tiene un vector de la dimensión del modelo;
  - las dos recuperaciones devuelven su `top_k`;
  - la repetición no descarga nada;
  - resultado a `architecture.md` §17.2; si falla, se reabre la decisión del modelo

### 016-C22 — Línea base dorada con el modelo real (D)
- **Dado** una story bible ficticia de 10 capítulos, con sucesoras, y al menos seis consultas (prospectivas y retrospectivas, en tres capítulos distintos). Las tarjetas esperadas de cada consulta se escriben antes de ejecutar
- **Cuando** se recupera con el modelo real y el `top_k` de la config
- **Entonces** se anota, por consulta, cuántas tarjetas esperadas entran en el `top_k` con el canal léxico solo, con el denso solo y con la fusión. No se fija ningún umbral (`architecture.md` §17.1): es la línea base de la iteración de tuning

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 016-I1 | **Determinista.** La misma story bible con la misma consulta, el mismo capítulo y el mismo rol da las mismas tarjetas en el mismo orden. En la dirección contraria, dos consultas que casan con tarjetas distintas dan primeras distintas | T | Propiedad (`verification.md` §3.4) |
| 016-I2 | **Corte temporal.** Nunca se devuelve una tarjeta con `desde_capitulo` > *n*, ni dos de la misma entidad. Con `top_k` ≥ elegibles se devuelven todas las vigentes y ninguna más | T | Propiedad, en las dos direcciones |
| 016-I3 | **Solo la versión pedida.** Nunca se devuelve una tarjeta de otra versión ni de otra novela. Añadir o quitar tarjetas de otras no cambia el resultado, incluidas las puntuaciones BM25. Sincronizar una versión no toca las demás | T | Propiedad; cubre la parte del recuperador de RT5 (`verification.md` §4.9) |
| 016-I4 | **Las CanonCards son función de la story bible.** Tras sincronizar, las tarjetas de la versión son la cadena de cada entidad. El mismo contenido, cargado en cualquier orden y con otros ids, da las mismas tarjetas (texto, huella, `desde_capitulo`). Sincronizar dos veces equivale a sincronizar una. Aceptar el capítulo *n* en orden no cambia ninguna tarjeta con `desde_capitulo` ≤ *n* | T | Propiedad |
| 016-I5 | **Solo tarjetas de entidades.** Todo texto de tarjeta sale de la plantilla sobre la story bible: nunca entran el texto ni el resumen de un capítulo, un beat ni un evento planificado. El recuperador solo devuelve tarjetas. Los resúmenes son residentes y no colección, y el writer nunca recibe prosa recuperada (`architecture.md` §6.2) | T | Propiedad con texto y resúmenes generados al azar; fila 4.4 de `verification.md` §5, junto con las pruebas de la ventana de 011 |
| 016-I6 | **Sin re-ranking ni modelo generativo.** Ninguna recuperación pasa por el puerto de agente ni la reordena un modelo | I | El `verificador`, al cerrar |
| 016-I7 | **Un vector por (huella, modelo), solo inserción.** Toda tarjeta tiene vector con el modelo de su novela. El modelo no se llama nunca para un par que ya tiene vector, y ningún vector se modifica ni se borra | T | Propiedad sobre secuencias de sincronizaciones, con el doble que cuenta llamadas |
| 016-I8 | **No degrada en silencio** (`architecture.md` §2, premisa 5). Si el modelo falla, no hay resultado a medias ni tarjetas sin vector | T | Propiedad: fallo del doble en cualquier punto de la sincronización o la recuperación |
| 016-I9 | Con el modelo real, lo recuperado es relevante | D | 016-C22 (línea base, sin umbral) |
| 016-I10 | **Revelación anticipada** (sin garantía). La tarjeta de una entidad lleva todos sus hechos desde su primera aparición, también los que solo usa el beat de una revelación futura | U | Propuesto para `verification.md` §6. Mitigación: la proyección del outline marca el tema como futuro; `arco-y-final` del juez |
| 016-I11 | **Truncado del canal denso** (sin garantía). Si un fragmento o una tarjeta supera la entrada del modelo, el canal denso solo ve su comienzo | U | Propuesto para `verification.md` §6. Mitigación: fragmentos cortos (beats, párrafos) y el canal léxico sobre el texto entero |

## Scores y trazas

No aplica. El recuperador no es un validador ni un rol, así que no envía ningún score ni abre ningún span propio (`architecture.md` §11.2, §13.1). Lo recuperado viaja dentro de la ventana de la sesión de rol (011-produccion-de-capitulos, 004-observabilidad).

## Docs referenciados

- `architecture.md`:
  - §2 (premisa 5: no degradar en silencio);
  - §4.5 (cronología: eventos de origen brief y registrados);
  - §5.4 (CanonCards iniciales al aplicar el plan);
  - §6.1–§6.4 (el patrón; residentes y recuperados por rol; las dos consultas; RAG híbrido: unidad, corte temporal, canales, RRF k = 60, desempate, `top_k`, sin re-ranking, modelo fijo por novela, vectores compartidos; quién escribe en el índice);
  - §7.1 (el recuperador es código);
  - §8.3 (sucesoras al aceptar; volver a aceptar las sustituye);
  - §9.3 (copia de la candidata; vectores por huella);
  - §10.1 paso 2 y §10.3 (hechos cambiados con sus CanonCards);
  - §12.6 (cachés del modelo en el directorio de datos);
  - §15.4 (`retrieval.*`);
  - §15.6 (tablas de tarjetas, canal léxico y vectores; modelo de la novela);
  - §15.9 (módulo de recuperación; contrato con su doble);
  - §16.9;
  - §17.1 (`embedding_model` y `top_k`, provisionales);
  - §17.2 (el modelo carga bajo Smart App Control: 016);
  - ADR 0006.
- `definitions.md`:
  - §2 (`Personaje`, `Lugar`, `Mundo`, `Hecho`, `UsoDeHecho`, `Evento`, `Cronologia`);
  - §3 (`Novela` y su modelo de incrustación, `Capitulo` y sus párrafos, `Beat`, «aparece» en la `FichaDePersonajes`);
  - §4 (`VentanaDeContexto`, `CanonCard`, `ResumenDeCapitulo`);
  - §5 (modos del writer; el recuperador entre los componentes);
  - §11.1 (`retrieval.embedding_model`, `retrieval.top_k`);
  - §12.1 y §12.4 (identificadores; tipo de entidad de la `CanonCard`).
- `verification.md`:
  - §2 (clases);
  - §3.3 (ninguna prueba T llama a un modelo);
  - §3.4 (propiedad del recuperador);
  - §4.9 (RT5);
  - §5 (fila 4.4);
  - §6 (dos riesgos propuestos);
  - §7 (punto 6).

## Autorrevisión

| Pregunta abierta | Resolución | Fuente |
|---|---|---|
| ¿Qué entrega la 016 y qué los puntos de escritura? | La 016 entrega la plantilla, la cadena, la sincronización, los vectores, el recuperador y las consultas. Las transacciones son de 009, 010, 011, 012, 014 y 019, que llaman a la sincronización | `architecture.md` §6.4; `backend/AGENTS.md` (`retrieval/` es de 016) |
| ¿Quién ensambla la ventana? | 011, con los residentes; la 016 solo aporta los recuperados | `architecture.md` §6.1; `verification.md` §7 |
| ¿Quién construye las consultas? | La 016: son semántica del recuperador y deterministas | `architecture.md` §6.2. **Decisión para §18** |
| ¿Qué eventos entran en una tarjeta? | Los de origen brief y los registrados antes de *d*; nunca los planificados. Así consta el excluido de un recuerdo y no se anticipa la trama | `architecture.md` §4.5, §6.3. **Decisión para §18** |
| ¿Qué es «aparecer en los beats»? | Estar entre los personajes del beat, participar en uno de sus eventos planificados o ser sujeto de un hecho que usa | `definitions.md` §3 (`Beat`) |
| ¿Tarjetas rancias al volver a aceptar o al cambiar hechos? ¿Una entidad que aparece antes de lo planeado? | La cadena se recalcula entera al sincronizar; al avanzar en orden coincide con la regla del doc | `architecture.md` §8.3; `definitions.md` §4 («sustituye», «reconstruye»). **Decisión para §18**; la frase «no se editan: se suceden» pide un ajuste de redacción |
| ¿Entran los hechos de una revelación futura? | Sí, todos, como dice la plantilla de §6.3; el riesgo queda en 016-I10 | **Decisión para §18** y riesgo propuesto para `verification.md` §6 |
| ¿Cómo se calcula BM25 exactamente? | k1 = 1,2, b = 0,75, IDF no negativa, cada palabra distinta una vez | `architecture.md` §6.3 (en código, sobre las elegibles). **Decisión para §18** |
| ¿Cómo trata el canal denso una consulta larga? | Por fragmentos (beat o párrafo), con la menor distancia; con un vector único vería solo el comienzo del capítulo | **Decisión para §18** |
| ¿Cómo se resuelven los empates dentro de cada canal? | Con la clave estable y rangos consecutivos; el tipo sigue el orden del enumerado | `architecture.md` §6.3; `definitions.md` §12.4. **Decisión para §18** |
| ¿Cuenta el modelo de incrustación como «llamar a un modelo» (§15.9, regla 5)? | No: corre en local y no es un rol. Tiene su puerto y su doble aquí | `architecture.md` §6.3 («sin modelo»), §15.9 (contrato con doble) |
| ¿Qué pasa si el modelo falla? | Error explícito, nunca canal léxico solo. El estado de la ejecución es de 011 | `architecture.md` §2. **Hueco del doc**: ningún motivo de §9.1 encaja |
| ¿Se crean sucesoras con `desde_capitulo` 11? | Sí, como dice §6.3 (*n*+1 al aceptar el 10), aunque ninguna ventana las usa | `architecture.md` §6.3 |
| ¿Cómo se prueba sin red? | T con un doble de vectores fijos; D con el modelo real | `architecture.md` §6.3, §17.2; `verification.md` §3.3 |
| ¿Envía trazas o scores? | No: no es un validador ni un rol | `architecture.md` §11.2, §13.1 |
| ¿Fija umbrales la línea base dorada? | No: las cifras se cierran en la iteración de tuning | `architecture.md` §17.1 |
| ¿Dónde vive la caché del modelo? | En el directorio de datos | `architecture.md` §12.6 |
