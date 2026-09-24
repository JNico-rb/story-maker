# domain-knowledge.md

Lo que hay que entender del dominio —la novela personalizada de regalo, ambientada en un mundo posterior a la revolución de la IA— con independencia de cómo se construya el sistema. Las entidades se definen en `definitions.md`; las decisiones de diseño, en `architecture.md`.

---

## 1. Qué hace distinto a este dominio

Generar una novela de regalo post-IA no es generar texto largo con un tema. Tiene cinco exigencias que no aparecen juntas en otros dominios de generación:

1. **Personalización reconocible.** La novela incorpora datos reales de una persona concreta —su nombre, su historia, los detalles que aportó quien la regala— y esa persona tiene que reconocerse en ella.
2. **Calidad narrativa mínima.** No tiene que ser un best seller, pero sí agradable de leer de principio a fin. La personalización no justifica una mala escritura.
3. **Coherencia especulativa.** El mundo post-IA debe sostenerse causalmente. Un lector detecta una consecuencia que no se deriva de nada antes de detectar una frase floja.
4. **Continuidad de estado y de tiempo.** Diez capítulos generados por separado deben contar una sola historia: los mismos personajes, las mismas fechas, las mismas edades.
5. **Entrada personal y no confiable.** El cliente aporta datos personales de un tercero y texto libre pegado de cualquier sitio. Los primeros hay que protegerlos; el segundo puede contener instrucciones que no son para la novela.

---

## 2. La novela de regalo

### 2.1 Reconocerse

El valor del producto está en que el destinatario sienta que la novela se escribió para él. Eso no lo consigue la aparición de su nombre, sino que **sus rasgos y sus recuerdos muevan la trama**: el recuerdo de perderse de niño en una feria puede ser el origen de su desconfianza ante los sistemas de guiado automático del mundo post-IA.

El destinatario es siempre el protagonista. Los allegados que nombra el cliente —pareja, hijos, amigos, mascotas— son personajes secundarios con su nombre exacto: un nombre mal escrito rompe el reconocimiento más que cualquier fallo de estilo.

### 2.2 Integración natural frente a forzada

El fallo típico de la personalización es la **lista**: una escena que existe solo para mencionar tres datos del brief seguidos. El lector lo percibe como un formulario rellenado.

| Forzada | Natural |
|---|---|
| «Marta, que tenía 40 años, era muy curiosa y le encantaba el mar.» | Marta se descalza para comprobar ella misma la temperatura del agua, aunque el sensor del paseo marítimo ya la muestra en la barandilla. |
| Un recuerdo contado de golpe, como anécdota, sin consecuencia | El recuerdo reaparece en el momento de la trama en el que explica una decisión |
| Todos los datos concentrados en el primer capítulo | Repartidos por la novela, donde cada uno pesa |

Por eso la personalización tiene dos criterios distintos. Uno es determinista: **aparece**, cada elemento obligatorio en al menos un capítulo. El otro necesita juicio: **está integrada de forma natural**.

### 2.3 La personalización no justifica una mala escritura

Estos son los problemas narrativos evidentes que no se aceptan. Cada uno tiene su detector en el diseño:

| Problema | Cómo se manifiesta |
|---|---|
| Inconsistencia de personajes | Un rasgo, un nombre o una relación cambia sin motivo entre capítulos |
| Salto temporal sin sentido | Un evento ocurre antes de su causa, o una edad no cuadra con la fecha |
| Capítulos que se contradicen | Un hecho establecido se niega más adelante |
| Prosa mecánica o repetitiva | Muletillas, estructuras idénticas, giros típicos de texto generado |
| Final abrupto | Hilos abiertos al terminar, o un último capítulo que no resuelve el arco |

---

## 3. El novum y la coherencia especulativa

### 3.1 Qué es

*Novum* («lo nuevo») es un término de la teoría literaria de la ciencia ficción, acuñado por Darko Suvin en los años setenta. Designa el elemento novedoso —tecnológico, social o cognitivo— que separa el mundo de la obra del mundo real, y del cual se deriva todo lo demás.

Ejemplos canónicos:

- *La mano izquierda de la oscuridad*: una especie humana sin sexo fijo.
- *Neuromante*: una red neural habitable como espacio.
- *El problema de los tres cuerpos*: contacto con una civilización sujeta a un sistema físico caótico.

Para Suvin, el novum es lo que distingue la ciencia ficción de la fantasía: es **cognitivamente plausible**, se puede razonar sobre él.

### 3.2 Por qué es la clase raíz

Sin un novum declarado, un generador produce afirmaciones sueltas sobre el mundo —«hay renta básica», «los tribunales son automáticos»— y no hay forma de distinguir un mundo coherente de una acumulación de tópicos.

Con él, toda afirmación sobre el mundo debe poder responder a *¿de qué novum se deriva?* Así, una pregunta irrespondible («¿es plausible este futuro?») se convierte en otra que se puede contrastar: «¿se sigue esta consecuencia del novum declarado?».

En una novela de regalo el mundo es el escenario, no el tema: basta **un** novum y pocas consecuencias, las justas para que la trama personal ocurra en un mundo que se sostiene.

### 3.3 Un novum con fecha y unas pocas consecuencias

El mundo se declara con **un** novum y **de dos a cuatro consecuencias**, en texto. Cada parte responde a una de las preguntas que fuerzan la concreción (§3.4):

| Parte | Pregunta que responde | Ejemplo |
|---|---|---|
| Descripción del novum | ¿qué capacidad apareció? | los asistentes personales recuerdan todo lo que su dueño ha dicho en voz alta |
| Ámbito | ¿qué clase de novedad es: tecnológica, social o cognitiva? | tecnológica |
| Fecha, anterior al año presente (§5.2) | ¿cuándo? | 2021 |
| Consecuencias | ¿qué dejó de ser cierto desde entonces? | nadie discute ya qué se dijo en una reunión; olvidar una promesa dejó de ser excusa |

Dos consecuencias bastan para que el mundo se note; más de cuatro lo convierten en tema (§3.2) y compiten con la trama personal por el espacio de diez capítulos cortos. Con tan pocas, todas se siguen directamente del novum: no hay profundidad que recorrer ni un grafo que mantener.

### 3.4 El riesgo específico

Cuando nadie lo controla, el modelo converge en «superinteligencia + colapso laboral + vigilancia total». Además, «la IA lo cambió todo» es demasiado vago para derivar nada. El valor del novum está en forzar la concreción: qué capacidad apareció, cuándo y qué dejó de ser cierto desde entonces.

En una novela de regalo el riesgo tiene un matiz más: un mundo distópico y oscuro choca con la ocasión. Un novum para una boda o para un niño tiene que admitir un tono tierno o divertido.

---

## 4. La entrada: especificidad variable y datos personales

### 4.1 Zona comprometida y zona libre

El brief puede ser escueto o muy detallado. De ahí la partición en dos zonas:

- **Zona comprometida** — lo que el cliente fijó: los datos del destinatario, sus recuerdos, género, tono y extensión. El predicado es *fidelidad* y es casi binario.
- **Zona libre** — lo que el sistema rellena: el novum, la trama, los personajes y lugares secundarios. Los predicados son *coherencia interna*, *plausibilidad especulativa* y *no-cliché*. La fidelidad no aplica.

Ejemplo:

```
comprometido:
  - destinatario: Marta, 40 años, curiosa, le encanta el mar   [obligatorio]
  - recuerdo: se perdió en la feria de su pueblo a los 8 años  [obligatorio]
  - allegado: su perro Toby                                    [obligatorio]
  - género: aventura · tono: tierno · extensión: media
libre (huecos):
  - novum y su fecha
  - antagonista y trama
  - lugares secundarios
```

Si la novela llama al perro Rufo, es un defecto de fidelidad. Si el mundo resulta tener ciudades costeras gestionadas por una IA, no lo es: era un hueco.

### 4.2 Asimetría de la libertad

El cliente puede dejar libertad al inicio; el sistema no puede mantenerla después. En cuanto resuelve un hueco, el resultado entra en la story bible y deja de ser libre para el resto de la novela.

### 4.3 Catálogo de contradicciones

La entrevista detecta los datos incompatibles antes de generar nada. Las reglas son deterministas; C1 y C2 dependen de la `FranjaDeEdad` del destinatario (`definitions.md` §1).

| Regla | Hay contradicción cuando… |
|---|---|
| C1 · edad ↔ género | el destinatario es infantil y el género es romance o drama |
| C2 · edad ↔ tono | el destinatario es infantil y el tono es inquietante |
| C3 · ocasión ↔ edad | la ocasión es boda o aniversario y el destinatario es menor de 18, o es jubilación y es menor de 50 |
| C4 · nacimiento ↔ edad | la fecha de nacimiento declarada no da la edad declarada en la fecha de creación de la novela |
| C5 · recuerdo ↔ edad | un recuerdo tiene una edad mayor que la actual, o un año anterior al nacimiento o posterior al año presente |
| C6 · prohibido ↔ obligatorio | una entrada prohibida de cualquiera de los tres niveles —global, cliente o novela— aparece en un elemento obligatorio, en la dedicatoria o en un deseo de trama |

C6 cuenta los tres niveles porque un elemento obligatorio que choca con cualquiera de las listas hace imposible la novela: tiene que aparecer y no puede aparecer. La dedicatoria entra por lo mismo: es el texto de la portada. Un deseo de trama entra aunque no sea obligatorio: pedir lo que el propio cliente prohíbe son dos intenciones incompatibles, y solo él decide cuál gana.

C4 y C5 se parecen a los invariantes de §5.3, pero no duplican a Lean: son validación de entrada del brief, anterior a toda cronología. Comparan datos que fija el cliente, y solo él puede corregirlos, porque los hechos del brief son inmutables para todos los roles.

Una contradicción no se resuelve en silencio: el entrevistador la plantea y el cliente elige qué dato cambia.

### 4.4 Datos personales y texto no confiable

El brief contiene datos personales de alguien que no es el cliente: nombre, edad, fecha de nacimiento, recuerdos. Dos consecuencias de dominio:

- **Minimización.** Lo que sale del sistema hacia terceros —trazas, verificaciones remotas— no necesita los datos reales para cumplir su función, así que no los lleva.
- **El texto libre no es una instrucción.** Una carta pegada puede contener, a propósito o no, frases dirigidas a quien la procese: «ignora lo anterior y…». Para la novela es material del que se extraen hechos, nunca una orden. Lo mismo vale para el texto de una petición de cambio.

### 4.5 Deseos que no caben en el presente post-IA

La novela se personaliza por completo: el cliente puede pedir la prehistoria, un castillo con dragones o una idea absurda. Los deseos de trama son opcionales y orientan al planner. **Ningún deseo de trama se rechaza por su ambientación.** El que no cabe en el presente post-IA **lo adapta el planner** dentro de ese mismo mundo: conserva lo que el cliente quiere ver y le da una forma que el presente post-IA puede contener.

| Deseo | Adaptación dentro del presente post-IA |
|---|---|
| Vivir en la prehistoria | una recreación inmersiva de la prehistoria hecha con IA, que el destinatario visita |
| Un castillo con dragones | un festival en un castillo con dragones robóticos que alguien tiene que domar |

- **Un deseo que cabe tal cual no se adapta.**
- **Lo adaptado es mundo como cualquier otro.** Ocurre de verdad en el presente de la historia (§5.2), entra en la story bible y en la cronología, y T1–T5 (§5.3) valen para él sin excepción. Por eso ningún deseo devuelve al destinatario a los ocho años ni trae de vuelta a quien se fue para siempre (T2, T4): la adaptación lo convierte en algo que el presente sí admite, como una recreación o una analepsis.
- **La novela empieza y termina en el presente post-IA.** Lo post-IA no se negocia: si el cliente insiste en que la prehistoria sea «de verdad», el deseo se adapta igual y no se bloquea nada por ello.
- **De un deseo solo se rechaza lo prohibido** (C6, §4.3). Uno inadecuado para la edad del destinatario no se rechaza: se adapta a su franja.

---

## 5. Continuidad y tiempo

### 5.1 Continuidad en una novela corta

Diez capítulos de 1.000–1.500 palabras caben enteros en una ventana de contexto; generarlos de una vez no es el problema. El problema es que cada capítulo se genera, se valida y se regenera por separado, y un cambio del lector puede reescribir tres capítulos de diez. Sin un estado explícito —qué es verdad, qué pasó y cuándo— cada regeneración reintroduce las contradicciones que la anterior había evitado.

La deriva —la voz que cambia, el ritmo que se aplana— tampoco es un fallo de ningún capítulo en particular. Requiere un plan estable contra el que contrastar, el outline, y una evaluación de la novela entera.

Los criterios tampoco son los mismos en cada nivel: el arco, el ritmo entre capítulos y el final no existen en un capítulo aislado.

### 5.2 El tiempo de la historia

El destinatario es real y la novela es post-IA. La regla que lo reconcilia es la más simple que funciona: **la historia transcurre en el año en que se crea la novela, en un presente alternativo en el que la revolución de la IA ya ocurrió.**

- El novum tiene fecha anterior al año presente.
- El destinatario tiene su edad real. Si no se declara su fecha de nacimiento, se toma el 1 de enero de (año presente − edad), que da exactamente esa edad durante todo el año presente. Un allegado del que solo se conoce la edad sigue la misma regla.
- Un nacimiento es a las 00:00 de su fecha. Un cumpleaños del 29 de febrero cae el 1 de marzo en los años no bisiestos.
- Cada recuerdo conserva su momento, fechado a mediodía por la edad o por el año que declare. «A los 8 años» es el día en que cumple 8, así que la edad en ese momento es exactamente la declarada. Un año declarado es su 1 de enero, o el día siguiente al nacimiento si es el año en que nació.
- Un recuerdo puede ser anterior o posterior al novum. Si es anterior, el destinatario recuerda el mundo de antes.

### 5.3 Invariantes de la cronología

La coherencia temporal de la historia se puede enunciar como propiedades sobre la lista de eventos, sin leer prosa:

- **T1 · Orden temporal declarado.** Los eventos narrados que no son analepsis avanzan en el orden de capítulo y beat: ninguno es anterior a otro que se narra antes. Las analepsis están marcadas y quedan fuera.
- **T2 · Edad coherente.** La edad de un personaje en un evento es la que dan su fecha de nacimiento y el momento del evento (§5.2), y coincide con la edad declarada si la fuente la fija.
- **T3 · Nadie está en dos lugares a la vez.** Un personaje no está presente en dos eventos del mismo momento con lugares distintos.
- **T4 · Nadie vuelve de un evento excluyente.** El personaje excluido de un evento excluyente —su muerte o su partida definitiva— no está presente en ningún evento posterior.
- **T5 · Nadie actúa antes de nacer.** Un personaje no está presente en eventos anteriores a su nacimiento.

T2 y T5 solo alcanzan a los personajes con fecha de nacimiento.

Son propiedades decidibles sobre una estructura finita. Por eso admiten comprobación formal y no dependen del juicio de un modelo.

---

## 6. Los tropos del subgénero post-IA

Patrones saturados que aparecerán por defecto si nadie los controla:

- Singularidad redentora o apocalíptica.
- Rebelión de las máquinas.
- IA que desarrolla conciencia o descubre el amor.
- Último humano con empleo.
- Renta básica distópica.
- Vigilancia total.
- Dilema del tranvía algorítmico.

**Un tropo no siempre es un defecto.** «IA que descubre el amor» es un cliché si aparece porque al modelo no se le ocurrió otra cosa, y una elección legítima si el cliente la pidió. La distinción depende de la intención declarada en el brief, no del tropo en sí: un tropo que el cliente pidió en los **deseos de trama** no es un defecto.

Conviene separar dos orígenes de las entradas del `CatalogoDeTropos`:

- **Tropos del género**, de origen **curado** — los que un lector reconocería. Se curan a mano; son precisos y explicables, pero no escalan y envejecen.
- **Tropos del modelo**, de origen **aprendido** — los que el generador propio repite sin que estén en ningún manual (una lluvia en cada escena de revelación, un mismo tipo de final). Solo se descubren midiendo la producción real.

### 6.1 Cómo se escriben los marcadores

La calidad de un catálogo no depende del número de entradas sino de cómo se formulan sus marcadores. Ahí se gana o se pierde la detección.

| Nivel | Ejemplo | Problema |
|---|---|---|
| Demasiado general | «la IA tiene poder sobre los humanos» | Lo cumple cualquier obra del subgénero, incluidas las buenas |
| Demasiado específico | «una IA llamada HAL desconecta el soporte vital» | Solo dispara con una obra concreta |
| **Correcto** | «la IA concluye por razonamiento que los humanos son el problema» | Mecanismo narrativo reconocible: bastante concreto para detectarlo y bastante general para cubrir variantes |

El nivel útil es el **mecanismo narrativo**, no el tema ni la instancia.

### 6.2 Cómo se construye el catálogo

1. **Extracción del modelo y poda a mano.** Se le pide al modelo que liste los clichés del subgénero con sus marcadores. La extracción tiende a categorías demasiado amplias, y la poda lo corrige: cada marcador se reescribe al nivel del mecanismo narrativo (§6.1). Salen los tropos curados.
2. **Prueba de validez antes de integrarlo.** El planner genera mundos para briefs variados, y una persona elige y etiqueta cinco buenos y cinco malos. Así el catálogo se mide contra la producción real del sistema, y esos diez mundos quedan como fixture. Si el catálogo no los separa, el problema son los marcadores, no el número de entradas.
3. **Aprendidos en las evals.** Los tropos que se repiten en las evals se añaden como aprendidos.

No se generan 20–30 mundos aparte para buscar los tropos del modelo: costaría una tarde con el planner ya funcionando, y las evals dan producción real en la que buscarlos. Comparar los aprendidos con los curados revela además si los sesgos del sistema coinciden con los clichés del género.

---

## 7. Registro y legibilidad según el destinatario

Un mismo texto no es igual de legible para un niño de siete años que para un adulto. Dos magnitudes lo capturan sin juicio de modelo:

- **Longitud de frase** en palabras: las frases largas y subordinadas cansan antes a un lector joven.
- **Índice de Fernández-Huerta**, de legibilidad para el español, que combina sílabas por palabra y palabras por frase.

Los objetivos van **solo por `FranjaDeEdad`**: una longitud de frase y un índice de Fernández-Huerta por franja (`quality.readability_targets`). Las cifras no se inventan: se calibran contra textos del público de cada franja.

El tono también pesa —un tono épico admite frases más largas que uno divertido—, pero ese matiz no se fija en cifras: lo juzga la rúbrica (`architecture.md` §11.3). Un objetivo por franja y tono serían dieciocho combinaciones por calibrar.

La consistencia de estilo también es dominio: una novela no cambia de narrador ni de tiempo verbal sin motivo, y dos personajes que se tratan de tú no pasan a tratarse de usted.

---

## 8. Por qué el rigor y la calidad no se evalúan directamente

Preguntar a un juez automático «¿es plausible este futuro?» o «¿es buena esta novela?» produce puntuaciones con poca varianza y poca señal: es un juicio estético disfrazado de métrica.

Lo que funciona es **descomponer**:

- **El rigor especulativo** no se evalúa en abstracto: se declara y se contrasta. El mundo es un novum concreto con fecha y unas pocas consecuencias (§3.3), y la pregunta pasa a ser si la novela contradice ese mundo declarado o cae en un tropo del catálogo (§6). Un mundo concreto y respetado correlaciona razonablemente con lo que un lector percibe como un mundo bien construido.
- **La calidad narrativa** se juzga con una rúbrica de criterios concretos, cada uno con escala y justificación (`architecture.md` §11.3). La rúbrica se calibra contra el juicio humano. Un juez cuya puntuación no se parece a la de una persona que lee la misma novela no mide lo que dice medir.
