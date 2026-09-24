# 018 — Linters de prosa

> Carril: C · Depende de: 011-produccion-de-capitulos · Estado: borrador

## Objetivo

Señalar, sin bloquear y sin modelo, los cuatro problemas de prosa que el encargo propone como linters opcionales: palabras o muletillas repetidas en un mismo párrafo; legibilidad inadecuada para la franja de edad del destinatario; abuso de adverbios en -mente, clichés y giros típicos de texto generado; y persona del narrador y tratamiento tú/usted distintos de los de la StyleSheet. Son los cuatro `Linter` de `definitions.md` §6: `linter-repeticion`, `linter-legibilidad`, `linter-estilo-ia` y `linter-consistencia`. Corren en el bucle del capítulo, tras el hook de validación y antes del editor, que recibe sus avisos. Con el veredicto, los avisos llegan como no bloqueantes al writer, al `InformeDeEjecucion`, a SQLite y a Langfuse. Cubre `verification.md` §5 O.8 y la parte de «prosa mecánica o repetitiva» de C.2.

Un **aviso** es un `Defecto` de un linter, que es siempre no bloqueante. Así lo llaman `architecture.md` §10.3 y `verification.md` §4.2.

## Alcance

- Los cuatro linters: comprobaciones deterministas escritas desde cero, sin analizador morfológico (`architecture.md` §14.5, §15.3). Analizan solo el **texto** de un capítulo, nunca su título.
- Sus entradas:
  - el texto;
  - la `StyleSheet` de la versión: el narrador y el tratamiento por defecto con sus excepciones por par de personajes, para `linter-consistencia`;
  - los objetivos de legibilidad de la `FranjaDeEdad` del destinatario del brief, `quality.readability_targets.<franja>`, para `linter-legibilidad`;
  - las listas y los umbrales propios, que son constantes del dominio (`definitions.md` §11.2).
- Su salida: los avisos, cada uno con su validador, su capítulo y un mensaje que dice qué se detectó, cuántas veces y en qué párrafo; y la métrica de cada linter.
- Su punto de ejecución `editor` en el bucle del capítulo (`architecture.md` §8.1, §11.2), que abarca:
  - el orden: después de los hooks y antes de la sesión del editor;
  - los avisos como entrada de la llamada del editor y del veredicto, siempre como no bloqueantes;
  - un span `validador:<linter>` por ejecución;
  - con la aceptación del capítulo, un `ResultadoDeValidador` y un `Score` por linter.
- Que los linters den el mismo resultado en el lint en vivo (`live_lint`). Solo dependen de sus entradas.

## Fuera de alcance

- **Lint en vivo** (`architecture.md` §10.3, §14.6) → 019-edicion-manual. Esa spec cubre la petición de lint, que junta los avisos de estos linters con los nombres, los hechos, las prohibidas y los dos avisos ligeros de cronología, sin traza, sin score y sin audit log (`verification.md` §5 O.9, O.10). También cubre el guardado y la ejecución `manual_edit`. El editor web con lint en vivo → 028-edicion-manual (frontend).
- **El bucle del capítulo** → 011-produccion-de-capitulos. Esa spec cubre los hooks, el recuento de palabras de `longitud-capitulo`, la ventana del editor, el veredicto, los intentos, la transacción de aceptación y el `InformeDeEjecucion`. Aquí solo se añade el paso de los linters y lo que dejan.
- **Otros flujos que reutilizan el bucle** y heredan el paso de los linters (018-I4): la reescritura dirigida del gate → 012-gate-de-publicacion; el writer en modo revisión → 014-cambios-del-lector; el re-registro del editor sin writer → 017-revision-visual; la edición manual → 019-edicion-manual.
- **Emisión de spans y scores, y máscara** → 004-observabilidad. El puerto de observabilidad y su doble nulo → 001-base.
- **Clave `quality.readability_targets` y su validación al arrancar** → 001-base. Calibrar los objetivos de las franjas `teen` y `adult` corresponde a la iteración de tuning (`architecture.md` §17.1) → 020-evals.
- **El recuento de avisos en la tabla de evals** → 020-evals.
- **Tiempo verbal**: no lo comprueba ningún linter. Lo revisa el editor contra la StyleSheet (`architecture.md` §14.5; `verification.md` §6 U18).
- **Léxico a evitar y palabras prohibidas**: no los comprueba ningún linter. Las prohibidas las caza la policy → 005-guardarrailes. El **registro** y la adecuación al tono los juzgan los criterios `tono` y `prosa` (011, 012).
- **Tropos**, que son mecanismos narrativos: criterio `no-cliche` del juez → 012. Los clichés de aquí son frases hechas de una lista.
- **Repetición entre capítulos**: los linters miran un capítulo, y dentro de él cada párrafo. Entre capítulos la mitiga que el writer nunca reciba prosa recuperada (`architecture.md` §6.2), y la juzga el juez.

## Comportamiento observable

### Reglas comunes

- **Párrafo:** bloque del texto separado del siguiente por una línea en blanco (`definitions.md` §3, `Capitulo`). Se numera desde 1.
- **Palabra:** la unidad que cuenta `longitud-capitulo` (011). De cada palabra solo cuentan sus letras, con tilde, ñ y ü. Una palabra sin letras no se compara y no tiene sílabas.
- **Comparación:**
  - no distingue mayúsculas, pero sí tildes: «Ventana» es «ventana»; «té» no es «te»;
  - va por palabras completas: «ex» no aparece en «examen»;
  - una expresión de varias palabras se busca como una secuencia de palabras consecutivas.
- **Frase:**
  - termina en un signo final (`.` `!` `?` `…`) o en una serie de ellos si después viene el fin del párrafo o un espacio y un texto que no empieza por minúscula (se salta una raya de inciso);
  - `¡` y `¿` no cortan;
  - un párrafo sin signo final cierra su última frase.
- **Diálogo y narración:**
  - en una línea que empieza por raya (`—`), el texto de detrás de la raya es diálogo; cada raya siguiente de esa línea alterna entre inciso del narrador y diálogo;
  - también es diálogo el texto entre comillas (`« »`, `“ ”`, `" "`);
  - **narración** es todo lo demás, incisos incluidos;
  - una **intervención** es el diálogo de una línea con raya, o un texto entre comillas.
- **Sílabas:**
  - una sílaba es cada núcleo vocálico;
  - las vocales son a, e, i, o, u, con tilde o sin ella, y ü; la y es vocal débil solo al final de una palabra;
  - las fuertes son a, e, o; las débiles, i, u, ü;
  - una serie de vocales seguidas es un solo núcleo, salvo que se separe en dos puntos: entre dos fuertes seguidas, y entre una débil con tilde (í, ú) y una fuerte que tenga al lado.
- **Medidas:** se redondean a dos decimales y se comparan ya redondeadas.
  - Longitud media de frase = palabras ÷ frases.
  - Índice de Fernández-Huerta = 206,84 − 60 × (sílabas ÷ palabras) − 1,02 × (palabras ÷ frases).
- **Orden de los avisos:** por linter, en el orden de la tabla siguiente; dentro de cada linter, por párrafo y después por primera aparición.
- **Métrica y resultado** de cada linter. Un linter **pasa** si no da ningún aviso.

| Linter | Métrica (valor del score) | Umbral (comentario del score) |
|---|---|---|
| `linter-repeticion` | número de avisos | una palabra 3 veces o una muletilla 2 veces en un párrafo |
| `linter-legibilidad` | índice de Fernández-Huerta | la franja; la longitud media de frase y su máximo; el índice y su mínimo |
| `linter-estilo-ia` | adverbios en -mente por 1.000 palabras | umbral 6 por 1.000; número de clichés encontrados |
| `linter-consistencia` | número de avisos | el narrador y los tratamientos que admite la StyleSheet |

### Casos

**C1 — `linter-repeticion`: una palabra repetida en un párrafo (T)**

- Entrada: el párrafo 1 contiene «ventana» tres veces, una de ellas como «Ventana».
- Salida: un aviso: «"ventana" 3 veces en el párrafo 1». La métrica es 1.

Límites:

| Texto | Resultado |
|---|---|
| «ventana» 2 veces en el párrafo 1 y 2 veces en el párrafo 2 | Sin aviso: los párrafos no se suman |
| «ventana» 4 veces en un párrafo | Un solo aviso, con 4 |
| «ventana» 2 veces y «ventanas» 1 vez en un párrafo | Sin aviso: el plural es otra palabra |
| una palabra gramatical («la», «de», «que») 5 veces en un párrafo | Sin aviso |
| un nombre canónico («Marta») 3 veces en un párrafo | Un aviso: los nombres cuentan como cualquier palabra |

Las palabras gramaticales forman una lista cerrada del dominio: artículos, preposiciones, conjunciones, pronombres y las formas de ser, estar y haber. No cuentan para esta regla.

**C2 — `linter-repeticion`: una muletilla repetida en un párrafo (T)**

- Entrada: el párrafo 3 contiene «de repente» dos veces.
- Salida: un aviso: «muletilla "de repente" 2 veces en el párrafo 3».

Límites:

| Texto | Resultado |
|---|---|
| «entonces» 2 veces en un párrafo | Un aviso: una muletilla dispara con 2, no con 3 |
| «de repente» 1 vez en el párrafo 1 y 1 vez en el párrafo 2 | Sin aviso |
| «de repente» 3 veces en un párrafo | Un solo aviso, el de la muletilla, con 3. Las palabras de una muletilla encontrada no cuentan como palabras sueltas, así que no hay aviso aparte por «repente» |

La lista de muletillas es una constante del dominio. Incluye al menos «de repente», «entonces», «en ese momento» y «de alguna manera».

**C3 — `linter-legibilidad`: medidas e índice (T)**

- Entrada: un texto de 20 palabras, 36 sílabas y 2 frases, con la franja `children` (objetivos de fixture: 12 y 80).
- Salida: la longitud media de frase es 10,00 y el índice, 206,84 − 108 − 10,20 = 88,64. No hay aviso, y la métrica es 88,64.

**C4 — `linter-legibilidad`: la longitud media de frase en su límite (T)**

- Entrada: franja `children` con un máximo de 12. Las sílabas por palabra dejan el índice en su objetivo o por encima.
- Salida:

| Palabras ÷ frases | Resultado |
|---|---|
| 120 ÷ 10 = 12,00 | Sin aviso |
| 121 ÷ 10 = 12,10 | Un aviso: «longitud media de frase 12,10 palabras; máximo de la franja children: 12» |

**C5 — `linter-legibilidad`: el índice en su límite (T)**

- Entrada: franja `children` con un mínimo de 80, y 250 palabras en 25 frases (longitud 10,00).
- Salida:

| Sílabas | Índice | Resultado |
|---|---|---|
| 486 | 80,00 | Sin aviso |
| 487 | 79,76 | Un aviso: «índice de Fernández-Huerta 79,76; mínimo de la franja children: 80» |

**C6 — `linter-legibilidad`: la franja del destinatario elige el objetivo (T)**

- Entrada: el mismo texto, con una longitud media de frase de 15,00, en dos novelas. El destinatario de una tiene 7 años (`children`, máximo 12). El de la otra tiene 30 (`adult`, máximo de fixture 20).
- Salida: solo la novela infantil recibe el aviso de longitud. En la adulta no hay aviso. La franja sale de la edad del destinatario en el brief (`definitions.md` §1, `FranjaDeEdad`).

**C7 — Recuento de sílabas (T)**

- Entrada: cada palabra de la tabla, sola.
- Salida: su número de sílabas.

| Palabra | Sílabas | Regla |
|---|---|---|
| casa | 2 | un núcleo por vocal separada |
| cielo | 2 | débil y fuerte: un solo núcleo |
| ciudad | 2 | dos débiles: un solo núcleo |
| poeta | 3 | dos fuertes se separan |
| aéreo | 4 | fuertes seguidas, todas separadas |
| río | 2 | una débil con tilde se separa de la fuerte |
| caída | 3 | la débil con tilde se separa de las dos fuertes |
| buey | 1 | serie sin punto de separación; y final como vocal |
| pingüino | 3 | ü es vocal débil |
| y | 1 | y final como vocal |
| ya | 1 | y inicial, consonante |

**C8 — Recuento de frases (T)**

- Entrada: cada texto de la tabla como un párrafo, salvo que la tabla diga otra cosa.
- Salida: su número de frases.

| Texto | Frases | Regla |
|---|---|---|
| «Hola. Adiós.» | 2 | punto, espacio y mayúscula |
| «—¿Vienes? —preguntó Marta.» | 1 | se salta la raya de inciso y sigue una minúscula |
| «¡Ya! ¿Qué?» | 2 | tras el signo final viene «¿», que no es minúscula |
| «Esperó… y siguió.» | 1 | sigue una minúscula |
| «Llegó a las 8 p. m. y se fue.» | 1 | la abreviatura va seguida de minúscula |
| párrafo 1: «Esperó...»; párrafo 2: «Nadie vino» | 2 | una serie de signos corta una vez; el párrafo sin signo final cierra su frase |

**C9 — `linter-estilo-ia`: la densidad de adverbios en -mente en su límite (T)**

- Entrada: textos con adverbios en -mente, dentro o fuera del diálogo.
- Salida:

| Palabras | Adverbios en -mente | Densidad | Resultado |
|---|---|---|---|
| 1.000 | 6 | 6,00 | Sin aviso |
| 1.000 | 7 | 7,00 | Un aviso: «7,00 adverbios en -mente por 1.000 palabras; umbral: 6» |
| 1.250 | 8 | 6,40 | Un aviso |

La métrica es la densidad, haya aviso o no.

**C10 — `linter-estilo-ia`: palabras en -mente que no son adverbios (T)**

- Entrada: un texto con «mente», «demente», «clemente», «vehemente», «comente», «aumente» y «lamente», y otro con «rápidamente», «suavemente» y «fácilmente».
- Salida: el primero suma 0 adverbios; el segundo, 3.

Cuenta toda palabra terminada en «mente» salvo las de una lista cerrada del dominio con las que no son adverbios. Esa lista recoge sustantivos y adjetivos, y formas de los verbos en -mentar.

**C11 — `linter-estilo-ia`: clichés y giros de texto generado (T)**

- Entrada: la lista de clichés, que es una constante del dominio e incluye al menos «un escalofrío le recorrió la espalda», «el tiempo pareció detenerse» y «sin lugar a dudas». El texto tiene «Un escalofrío le recorrió la espalda» en los párrafos 2 y 5 y «el tiempo pareció detenerse» en el 4.
- Salida: un aviso por cada cliché distinto, con cuántas veces aparece y en qué párrafos:
  - «cliché "un escalofrío le recorrió la espalda" 2 veces (párrafos 2 y 5)»;
  - «cliché "el tiempo pareció detenerse" 1 vez (párrafo 4)».

  Un cliché basta para un aviso: no hay umbral.
- Límites:
  - «un escalofrío frío le recorrió la espalda» no dispara, porque las palabras deben ir seguidas;
  - «UN ESCALOFRÍO LE RECORRIÓ LA ESPALDA» dispara.

**C12 — `linter-consistencia`: narrador en tercera persona (T)**

- Entrada: la StyleSheet dice `third_person`. Las marcas de primera persona son yo, me, mí, mi, mis, conmigo, nosotros, nosotras, nos, nuestro, nuestra, nuestros y nuestras.
- Salida:

| Texto | Resultado |
|---|---|
| narración del párrafo 1: «Aquella tarde me pareció eterna.» | Un aviso: «párrafo 1: primera persona en la narración ("me"); la StyleSheet pide tercera persona» |
| «—Me voy a casa —dijo Marta.» | Sin aviso: «me» está en el diálogo |
| «Marta escribió: «Te echo de menos, mi amor».» | Sin aviso: el texto entre comillas es diálogo |
| «—Vete —me dijo Marta—.» | Un aviso: el inciso del narrador es narración |
| dos marcas en la narración del mismo párrafo | Un solo aviso para ese párrafo, con las dos marcas |

**C13 — `linter-consistencia`: narrador en primera persona (T)**

- Entrada: la StyleSheet dice `first_person`.
- Salida:

| Capítulo | Resultado |
|---|---|
| al menos una marca de primera persona en la narración | Sin aviso |
| marcas de primera persona solo dentro del diálogo | Un aviso: «el capítulo no tiene marcas de primera persona en la narración; la StyleSheet pide primera persona» |

**C14 — `linter-consistencia`: tratamiento sin excepciones (T)**

- Entrada: una StyleSheet sin excepciones por par. Las marcas de tú son tú, tu, tus, te, ti y contigo; la de usted, usted. Solo cuentan dentro del diálogo.
- Salida:

| Tratamiento por defecto | Texto | Resultado |
|---|---|---|
| `tu` | párrafo 4: «—¿Usted viene? —preguntó Marta.» | Un aviso: «párrafo 4: tratamiento "usted" no admitido por la StyleSheet (tú)» |
| `tu` | narración: «Marta nunca trataba de usted a nadie.» | Sin aviso: fuera del diálogo no se mira |
| `tu` | «—¿Quieres un té?» | Sin aviso: «té» no es «te» |
| `usted` | «—Te espero aquí.» | Un aviso por «te» |

**C15 — `linter-consistencia`: tratamiento con excepciones y mezcla (T)**

- Entrada: la StyleSheet tiene `tu` por defecto y un par de personajes con `usted`. Los tratamientos admitidos son el de por defecto más los de las excepciones.
- Salida:

| Texto | Resultado |
|---|---|
| «—¿Usted viene?» | Sin aviso: usted está admitido |
| «—Usted sabe que te quiero.» | Un aviso: «párrafo n: mezcla tú y usted en la misma intervención» |
| sin excepciones y con `tu`: «—Usted sabe que te quiero.» | Un solo aviso, el de «usted» no admitido (C14): cada intervención da un aviso como mucho, y el tratamiento no admitido va antes que la mezcla |

**C16 — Capítulo limpio (T)**

- Entrada: un capítulo de fixture de 1.000 a 1.500 palabras que cumple todo esto:
  - ningún párrafo repite una palabra 3 veces ni una muletilla 2 veces;
  - la longitud de frase y el índice están dentro del objetivo de su franja;
  - tiene 6 adverbios en -mente o menos por 1.000 palabras, y ningún cliché;
  - el narrador y el tratamiento son los de su StyleSheet.
- Salida: ninguno de los cuatro da aviso y los cuatro pasan. Las métricas son 0, su índice, su densidad y 0.

**C17 — Texto sin palabras (T)**

- Entrada: un texto vacío o solo con signos. En el punto `editor` no puede llegar, pero sí en el lint en vivo de 019.
- Salida: ningún linter da aviso, tampoco el de narrador en primera persona. `linter-legibilidad` y `linter-estilo-ia` no tienen métrica; `linter-repeticion` y `linter-consistencia` tienen 0.

**C18 — Corren tras los hooks y antes del editor, que recibe sus avisos (T)**

- Entrada: una ejecución `generation` en la fase `writing`, con el doble falso del puerto de agente y el doble nulo de observabilidad. El writer entrega un capítulo que pasa el hook de policy y el de validación, y que dispara al menos un aviso de cada linter.
- Salida:
  - en el span `capitulo-<n>` hay un span `validador:<linter>` por linter, en el orden `linter-repeticion`, `linter-legibilidad`, `linter-estilo-ia` y `linter-consistencia`;
  - los cuatro van después de los validadores del hook de validación y antes del span `rol:editor`;
  - las entradas de la llamada de la sesión del editor (`VentanaDeContexto`) contienen los avisos de los cuatro, en ese orden, marcados como no bloqueantes.

**C19 — Una entrega que no pasa los hooks no llega a los linters (T)**

- Entrada: en la misma sesión del writer, una primera entrega de 999 palabras que el hook de validación rechaza, y después una de 1.000 palabras que pasa. En una variante, la policy deniega la primera entrega por una prohibida.
- Salida: los linters corren una sola vez, sobre la entrega que pasó. La entrega rechazada no produce ningún span `validador:linter-*`.

**C20 — Con solo avisos, el capítulo se acepta (T)**

- Entrada: el editor entrega sin defectos bloqueantes, y los linters dan avisos.
- Salida: el veredicto es `accept` y el capítulo queda aceptado en ese intento. Los avisos no abren una reescritura ni cuentan como intento.

**C21 — En una reescritura por otra causa, el writer recibe los avisos (T)**

- Entrada: el editor entrega un defecto bloqueante (por ejemplo, `fidelidad-canon` bajo su umbral), los linters dan avisos y quedan intentos.
- Salida:
  - el veredicto es `rewrite`;
  - la nueva sesión del writer recibe entre sus defectos el bloqueante del editor y los avisos de los linters sobre la entrega rechazada, como no bloqueantes;
  - la nueva entrega vuelve a pasar por los cuatro linters antes del editor, y el editor recibe los avisos nuevos, no los de la entrega anterior.

**C22 — Con la aceptación: un resultado por linter en SQLite y en el informe (T)**

- Entrada: se acepta el capítulo n de la candidata, y su entrega tenía avisos de `linter-repeticion` y ninguno de los demás.
- Salida:
  - en la misma transacción de aceptación del capítulo (011, `architecture.md` §8.3), `validator_results` recibe cuatro filas, una por linter;
  - cada fila lleva el validador, la versión candidata, el capítulo n, si pasa (el de repetición no; los otros tres sí), el score (su métrica) y el detalle con sus avisos;
  - el `InformeDeEjecucion` (011) muestra los avisos de repetición como defectos no bloqueantes del capítulo n.

**C23 — Tras el commit: un score por linter en Langfuse (T)**

- Entrada: la misma aceptación de C22 y, en otra prueba, una transacción de aceptación que falla.
- Salida: si la transacción se confirma, el doble nulo recibe después del commit cuatro scores asociados a la traza de la ejecución y al span `capitulo-<n>`:
  - cada score se llama como su linter;
  - su valor es la métrica;
  - su comentario, el umbral de la tabla de las reglas comunes, con la franja y sus objetivos en el de `linter-legibilidad`.

  Si la transacción falla, no se envía ningún score de linter. Como toda exportación, los comentarios pasan por la máscara (004).

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 018-I1 | Todo aviso es un `Defecto` no bloqueante, sin criterio de rúbrica, con su capítulo y un mensaje que nombra lo detectado y su párrafo (o el capítulo entero, en C13). Ningún aviso, solo o con otros, cambia el `Veredicto` ni cuenta como `Intento` | T | Los cuatro linters sobre textos que los disparan dan solo defectos no bloqueantes; C20 |
| 018-I2 | Los linters son deterministas: el mismo texto, la misma StyleSheet y los mismos objetivos dan los mismos avisos, en el mismo orden, y la misma métrica | T | Prueba basada en propiedades: dos pasadas sobre textos generados coinciden |
| 018-I3 | Los linters son puros y no usan modelo. Solo leen sus entradas: no consultan SQLite, la config ni ningún rol, ni emiten nada. Registrar y emitir le toca a quien los llama en el punto `editor`, y en `live_lint` nadie registra (019). Son heurísticas propias, sin analizador morfológico ni binarios nativos | I | Revisión del `verificador` (`architecture.md` §15.3, §18) |
| 018-I4 | Los linters corren antes de toda sesión del editor sobre un capítulo, en cualquier flujo que reutilice el bucle del capítulo: la reescritura dirigida (012), la revisión de un cambio (014), el re-registro sin writer (017) y la edición manual (019). Ningún flujo llega al editor sin pasar por ellos | I | El `verificador`, al cerrar 012, 014, 017 y 019 |
| 018-I5 | Las listas son constantes del dominio: palabras gramaticales, muletillas, clichés, palabras en -mente que no son adverbios, y marcas de primera persona, de tú y de usted. Los umbrales también: 3, 2 y 6 por 1.000. De la config solo salen los objetivos de legibilidad | I | Revisión del `verificador` (`definitions.md` §11.2) |
| 018-I6 | Ningún linter comprueba el tiempo verbal | U | `verification.md` §6 U18 |
| 018-I7 | Las heurísticas son aproximadas y sus errores solo dan avisos de más o de menos, sin bloquear. Fallan en: las sílabas con h intercalada o con prefijos; las abreviaturas ante mayúscula («Sr. García»), que cortan la frase; el diálogo sin raya ni comillas; las palabras en -mente que no son adverbios y faltan en la lista; las marcas de primera persona en estilo indirecto libre; y el tratamiento de un par de personajes cuando el otro tratamiento también está admitido | U | Hace falta una fila nueva en `verification.md` §6 (propuesta al integrador) |

## Docs referenciados

- `architecture.md`:
  - §5.3: la StyleSheet y su uso por `linter-consistencia`;
  - §6.2: las entradas de la llamada del editor, con los defectos de los linters; el writer nunca recibe prosa recuperada;
  - §7.1: código, no rol;
  - §8.1: el bucle y su orden económico;
  - §8.2: el veredicto; los no bloqueantes llegan al writer y al informe;
  - §8.3: la aceptación en una transacción y los scores tras el commit;
  - §10.3 y §14.6: el lint en vivo, fuera de alcance;
  - §11.1 y §11.2: la familia programática, el punto de ejecución y el score como métrica con el umbral en el comentario;
  - §11.3: los criterios `prosa` y `tono`;
  - §13.1 y §13.3: los spans `validador:` y los scores;
  - §14.5: los cuatro linters;
  - §15.3 y §15.4: sin spaCy; `quality.readability_targets`;
  - §17.1: la calibración de los objetivos;
  - §18: linters heurísticos en Python puro.
- `definitions.md`:
  - §1: `FranjaDeEdad`;
  - §3: `Capitulo` (sus párrafos) y `StyleSheet`;
  - §4: `VentanaDeContexto` (las entradas de la llamada);
  - §6: `Linter`, `Defecto`, `Veredicto`, `ResultadoDeValidador`, `Score` e `InformeDeEjecucion`;
  - §8: `Span`;
  - §11.1 y §11.2: la config y las constantes del dominio;
  - §12.3: los nombres de los validadores;
  - §12.4: `Narrador`, `Tratamiento`, `FranjaDeEdad` y el punto de ejecución (`editor`, `live_lint`).
- `domain-knowledge.md`:
  - §2.3: la prosa mecánica o repetitiva;
  - §7: la legibilidad por franja y la consistencia de estilo.
- `verification.md`:
  - §2: las clases;
  - §3.3 y §3.4: las unitarias de los validadores programáticos y las pruebas basadas en propiedades;
  - §4.2: en la tabla de evals, los linters cuentan sus avisos (020);
  - §5: filas O.8 y C.2;
  - §6: U18.
- `project-constraints.md`, «Nuevos tipos de linters de prosa»: repeticiones y muletillas (C1, C2); frases largas y legibilidad (C3 a C6); adverbios, clichés y giros de IA (C9 a C11); narrador y tratamiento (C12 a C15). El tiempo verbal es 018-I6.
- Specs: 011-produccion-de-capitulos, 019-edicion-manual, 004-observabilidad, 001-base, 005-guardarrailes, 012-gate-de-publicacion, 014-cambios-del-lector, 017-revision-visual, 020-evals y 028-edicion-manual (frontend).

## Autorrevisión

| Pregunta | Respuesta | Fuente |
|---|---|---|
| ¿Qué se pide? | Los cuatro linters y su punto `editor` en el bucle del capítulo | `architecture.md` §11.2, §14.5; `definitions.md` §6, `Linter` |
| ¿Es de esta spec el lint en vivo? | No, es de 019. Aquí solo se exige que los linters sirvan igual allí | `architecture.md` §14.6; `verification.md` §5 O.9, O.10; el encargo separa «linters de prosa» y «linter para edición manual» |
| ¿Qué es un párrafo y qué es una palabra? | Un bloque separado por una línea en blanco; y la unidad de `longitud-capitulo` | `definitions.md` §3; 011 |
| ¿Qué umbrales se usan para la repetición y el -mente? | Los docs no los fijan: 3 y 2 por párrafo, y 6 por 1.000, como constantes provisionales del dominio | **Decisión para §18** |
| ¿Qué forma del índice de Fernández-Huerta? | La corregida, con palabras por frase. Con ella los textos infantiles rondan 80, que es el objetivo de la config | **Decisión para §18** |
| ¿En qué sentido se aplica cada objetivo? | La longitud de frase es un máximo y el índice, un mínimo: lo que cansa al lector joven es lo difícil | `domain-knowledge.md` §7; **decisión para §18** |
| ¿De dónde sale la franja? | De la edad del destinatario en el brief | `definitions.md` §1 |
| ¿Cómo se distinguen el diálogo, el narrador y el tratamiento? | Raya y comillas; marcas pronominales; los tratamientos admitidos más la mezcla en una intervención, porque sin análisis sintáctico no se puede atribuir el interlocutor | `architecture.md` §14.5; **decisión para §18** |
| ¿Qué se envía como score y cuándo pasa un linter? | La métrica de cada linter, con el umbral en el comentario; pasa si no da avisos | `architecture.md` §11.2 («métrica medida»); **decisión para §18** |
| ¿Se comprueba el tiempo verbal? | No | `architecture.md` §14.5; U18 |
| ¿Hay alguna pregunta para el usuario? | Ninguna: no hay dinero, cuentas ni alcance en juego | — |
