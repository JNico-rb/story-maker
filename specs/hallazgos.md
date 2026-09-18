# story-maker — Hallazgos (evidencia de la spec)

Cada regla de [functional.md](functional.md) que nació de un dato apunta aquí con `E-n`. Este fichero no manda sobre nada: es el **porqué**, con la cifra que lo sostiene y de dónde salió. Si una cifra no está, es que no se tiene (`desconocido`); ninguna se estima.

Fuentes: `novelas/tecnica-ascensores-peticion-ia/` (A, opus, spec v3), `novelas/tecnica-ascensores-peticion-ia-20260916-1719/` (B, haiku, spec v4), sus `registro.md`, los análisis de traza del 09-16 y del 09-17, `comparativa/caso-01-opus-vs-haiku/`, la revisión de ingeniería del 09-17 y el CHANGELOG 0.8.1 (en `git show HEAD:CHANGELOG.md`).

| E | Qué | Fecha | Reglas que motivó |
|---|---|---|---|
| E1 | La ejecución de referencia (opus) | 2026-09-16 | §2, §4.1 canon, §4.2 ajustes de longitud, mejor intento, revisión partida, §7.7 |
| E2 | Diagnóstico de volumen | 2026-09-17 | §4.2 hoja de continuidad y tope del resumen, §7.5, §7.6 |
| E3 | La ejecución con haiku | 2026-09-17 | §1.2 limitación, §5 tolerancia de formato, §6.1, §6.6, §8.3 signo |
| E4 | Comparativa caso-01 (A frente a B) | 2026-09-18 | §7.3, §7.7 limitación, §8.3 regla vacía, §5.4–5.5 fallos |
| E5 | La matriz de criterios no cubre los defectos reales | 2026-09-17 | §5 modos de fallo, §9.3.1 evaluadores |
| E6 | Estado de la observabilidad | 2026-09-17 | §9.3 |
| E7 | Revisión del repositorio: hook, deriva, duplicación | 2026-09-17 | §3.1, marcas `pendiente` |

---

<a id="e1"></a>
## E1 — La ejecución de referencia (A, opus)

`novelas/tecnica-ascensores-peticion-ia/`, 2026-09-16 10:38 → 14:21, perfil `relato`, 5 capítulos, un arco, los agentes en `opus`, spec v3 (revisor único, sin ajustes de longitud, umbrales viejos).

**Qué funcionó.** 37 invocaciones (38 en la traza: una fila `en curso` duplicada), **cero** fallos técnicos, **cero** incumplimientos de contrato, **cero** discrepancias de veredicto. Novela completa, 8.271 palabras, revisión global sobre el texto entero.

**Qué falló: las reglas de flujo, no los agentes.**

| Qué pasó | Por qué | Regla que salió |
|---|---|---|
| Cap. 3 cerrado con una contradicción de cronología («dos semanas» cuando habían pasado seis días) que el revisor había señalado | Sus dos reescrituras se gastaron en rechazos por longitud (1.940 y 1.879 palabras: 140 y 79 sobre el techo). Cada reescritura añade texto y el margen no da de sí | §4.2 ajustes de longitud con presupuesto propio; suelo y techo en palabras absolutas en el prompt |
| Cap. 5 cerrado con el intento 2, que dejaba abierto «Reme y el vecindario» (la escaleta mandaba cerrarlo), descartando el intento 3 que lo cerraba, tenía los cinco sucesos y acertaba una fecha que el 2 erraba | Empatados a un grave, desempató «menos problemas en total» (1 frente a 2). Esa regla premia al texto que hace menos | §4.2 mejor intento por cierres de escaleta antes que por recuento. Produjo solo `hilos_sin_cerrar: 1` y uno de los graves del global |
| La revisión global encontró 4 problemas de gravedad 1 (5 según la traza) que ninguna revisión de capítulo vio; tres, contradicciones a distancia | El revisor único recibía ~19.000 palabras para un capítulo de 1.700 con cinco criterios | §2, §5.4–5.5 revisión partida en dos agentes |
| Dos incoherencias venían de la biblia: una llave entregada en 2011 a quien lleva 26 años de oficio con 52 años en 2049; un ascensor con menos paradas que plantas | El interrogador no las fijó; ningún revisor de capítulo puede verlas porque la biblia es su vara de medir | §4.1 canon explícito y validación en modo `canon` |
| Dos fechas atadas a un día de la semana equivocado | Un modelo no calcula días de la semana con fiabilidad | §4.1 regla derivada |

**Capítulo a capítulo.** Intentos 2 · 2 · 3 · 3 · 3 = 13. Los cinco intentos nº 1 recibieron **exactamente 3 problemas**; los aprobados, 0–1 leves. Caps. 3 y 5 por agotamiento. Minutos: 17 · 20 · 17 · 33 · 44, creciendo con el contexto, no con la longitud.

**Longitud.** 13 mediciones, objetivo 1.500: media 1.657, **+10,5 %**, 11 de 13 por encima, dos sobre el techo. La métrica absoluta (9,3 %) lo escondía → §8.3 con signo.

**Métricas: 0 de 5** con los umbrales viejos (`graves_por_10` 8,0 ≤ 1; agotamiento 40 % ≤ 10; hilos 1 ≤ 0; primer intento 0 % ≥ 60; voz 15,4 % ≤ 10). Tres umbrales eran inalcanzables por construcción a 5 capítulos (un grave = 2,0 puntos; un agotamiento = 20 puntos) → §7.7 recalibrado a 2 · 20 · 0 · 40 · 20.

**Volumen.** 403.727 palabras de entrada, 77.066 de salida (traza: 412.877; el registro manda). **49,6 palabras leídas por palabra publicada.** Revisor 38 % de la entrada, escritor 45 %. Ni un token: `Agent` no los devuelve.

**Fugas de integridad.** `estado.json` se desincronizó y hubo que recontar desde `registro.md` al cerrar; un `paso_descartado` al reanudar se llevó un `intento-1.md` de 1.333 palabras (→ A21).

---

<a id="e2"></a>
## E2 — Diagnóstico de volumen (A releída con la traza)

Pregunta: de las 403.727 palabras de entrada, cuáles sobraban.

**1. El 58,4 % se gastó en reintentos.** Primeros intentos 143.664; reintentos **235.763**; interrogatorio y global 24.300.

**2. El umbral de veredicto no es la causa.** Reprocesados los 13 informes con tres reglas (`rechaza_con_graves: 1`, `graves ≥ 2`, y gravedad 1 separada de la 2): aprobados al primer intento **0 de 5 con las tres**. Los cinco primeros intentos traían al menos una gravedad 1. Donde sí ahorra separar 1 de 2: el tercer intento del cap. 5, rechazado por una sola gravedad 2, costó **43.625 palabras (10,8 %)**. `graves ≥ 2` ahorraría además el tercero del cap. 4 (38.190) dando por bueno un intento que contradecía el libro de estado → descartado (§7.5).

**3. La causa real es mecánica.** De 9 problemas de gravedad 1, **7** son aritmética temporal o estado de un objeto:

| Clase | Casos | Ejemplo |
|---|---:|---|
| Fechas, edades, plazos | 5 | «desde el noventa y ocho» contra 52 años en 2049; «dos semanas» por seis días; resina atornillada antes de sus 36 horas |
| Estado de un objeto | 2 | Altavoz sonando con el fusible sin reponer; cuadro operado sin la llave, que tenía otra persona |
| Regla del mundo | 1 | Registro de trabajo dentro de una red que la biblia dice que no lo tiene |
| Trama | 1 | |

Todos estaban en el contexto (libro de estado, resúmenes), diluidos en 17.000 palabras → §4.2 hoja de continuidad. Descartado decírselo al escritor en el prompt (ya lo hace implícitamente y no bastó con opus) y un agente «continuista» (una invocación más para algo que no requiere juicio).

**4. El resumen no resume.** Media **1.785 palabras para capítulos de 1.629 (110 %)**, porque el contrato viejo pedía al resumidor lo mismo que al libro de estado. En el cap. 5 el escritor leyó 16.875 palabras: resúmenes 7.373 (**crece sin tope**), libro de estado 3.138, biblia+escaletas 4.378, capítulo anterior 1.612.

**5. Proyección** (solo el término que crece), entrada del escritor por invocación:

| Capítulo | Resumen como estaba | Resumen a 350 |
|---|---:|---:|
| 5 | 16.306 | 10.366 (−36 %) |
| 12 | 28.801 | 12.466 (−57 %) |
| 30 | 60.931 | 17.866 (−71 %) |
| 200 | 364.381 | 68.866 (−81 %) |

`saga` era inviable por el contrato del resumidor, no por el modelo → §7.6 `resumen_max_palabras`, `resumenes_completos_ultimos` por perfil, aviso de proyección. Descartado recortar la ventana (tira capítulos enteros para un problema de redundancia) y digestos por arco (una pieza de memoria más; con 350 palabras, 200 capítulos caben en 70.000).

**6. La entrada por invocación se multiplicó por 3,7** en cinco capítulos (4.594 → 16.875) con `resumenes_completos_ultimos: null`. La nota de `config.json` que lo avisaba no impidió nada → mecanismo, no nota.

---

<a id="e3"></a>
## E3 — La ejecución con haiku (B)

`novelas/tecnica-ascensores-peticion-ia-20260916-1719/`, 2026-09-16 17:19 → 2026-09-17 11:58, **dos sesiones** (reanudación en el cap. 4), `relato`, los cinco agentes en `haiku`, spec v4. Traza Langfuse `a64d7a26…`, 125 observaciones.

**Cambiaron dos variables a la vez**: las correcciones de flujo (E1) y el modelo. Casi todo lo que mejoró se explica por la segunda.

**Capítulo a capítulo.** Intentos 3 · 2 · 1 · 1 · 2 = 9. Ningún agotamiento. **Un solo intento rechazado por contenido** en toda la novela (cap. 1, int. 2, una gravedad 1 de continuidad que encargo no vio: la única `discrepancia_veredicto`). Los otros tres rechazos, por longitud, los tres **por defecto** (1.012, 980, 821). Interrogatorio: 39 minutos y 6 de 41 invocaciones (2 rechazos de canon buenos, 3 reintentos de contrato); a un rechazo de abortar.

**1. La puerta de veredicto no se abrió: se desactivó.** 6 revisiones de contenido → 1 problema. Global sobre 6.426 palabras → 0 problemas, 4 observaciones. Con opus, cinco intentos nº 1 con 3 problemas cada uno y 5 graves en la global. `graves_por_10 = 0,0` mide al revisor, no al manuscrito. El propio informe global de B describe un hueco real (fotos que nadie tomó) y lo clasifica como observación «porque no contradice el canon». **Invalida** recalibrar umbrales con estos datos y hace que el plan del análisis anterior (reprocesar informes de A) no se pueda comparar con B.

**2. El sesgo de longitud se invirtió con el modelo.** haiku: media 1.159, **−22,7 %**, **9 de 9 por debajo**, 3 bajo el suelo; aprobados 1.223–1.398, media 1.278 (−14,8 %). opus: +10,5 %, 11 de 13 por encima. Mismo prompt. La corrección `objetivo × (1 − sesgo)` habría pedido 1.350 a un escritor que entrega 1.159: tres rechazos se habrían convertido en cinco. Retirada (→ A11). El sesgo es del modelo.

**3. Modo de fallo nuevo: 7 reintentos técnicos en 41 invocaciones (17 %)**, 0 en 37 con opus. Interrogador 3 (2 sin bloques, 1 arcos duplicados), escritor 3 (2 sin bloques, 1 sin `=== FIN ===`), resumidor 1. Cinco de siete: el agente **describe el fichero en vez de emitirlo**. Además, absorbidos sin reintento: JSON en valla de código (2), comilla tras el delimitador, `**` sobrantes. Tolerancia improvisada, no contrato → A8.

**4. Correcciones de E1 ejercitadas.** Ajustes de longitud: 3 de 3, reescrituras intactas. Split de revisores: 6 veces, funciona, produjo la única discrepancia y el harness impuso su recálculo. Mejor intento por cierres: **nunca** (sin agotamiento). «Primero cuentas, después registras»: **falló otra vez**, en el resumidor del cap. 5 (`pal_salida` 3.492 registrado antes de contar; real 2.774).

**5. Contabilidad.** `estado.json` e informe de cierre: 40 invocaciones, revisor-continuidad 9; `registro.md`: **41 y 10**. Falta la revisión global (14.455 palabras de entrada, la invocación más cara, 8,8 % del total). Entrada publicada 149.971; real **164.426**. Salida publicada 34.460; real **33.742** (corrección no propagada). Coste de contexto publicado un 9 % bajo. **25,6 palabras leídas por palabra publicada** (la mitad que A, porque todo es más corto, no por la política de memoria).

**6. Filas `pendiente`.** La herramienta `Agent` devolvió todas las salidas en segundo plano y no expone `run_in_background`; cada invocación ocupó **dos** filas (13 `pendiente` sobre 50). Cualquier consumidor que cuente filas se infla un 22 %. Es un defecto de Claude Code, no del diseño → A9.

**Volumen por agente (recontado):** interrogador 6 / 8.346 / 11.672 · escritor 12 / 56.551 / 10.433 · resumidor 7 / 17.306 / 11.637 · revisor-encargo 6 / 26.837 / — · revisor-continuidad 10 / 55.386 / — · **total 41 / 164.426 / 33.742**.

---

<a id="e4"></a>
## E4 — Comparativa caso-01: A (opus, v3) frente a B (haiku, v4)

`comparativa/caso-01-opus-vs-haiku/`, 2026-09-18. `idea.md` y `entrevista.md` idénticos byte a byte. **No aísla el modelo**: entre A y B cambiaron revisión partida, ajustes de longitud y umbrales; las dos primeras favorecen a B por diseño.

**Métricas (recalculadas).** A: 0 de 5 con sus umbrales. B: **5 de 5** con los suyos, 4 de 5 con los de A (falla primer intento: 40 % frente a 60 %). `b_aguanta: true` **por vacío**: A no cumple ninguna, así que la regla de §8.3 no discrimina → A6.

| | A | B |
|---|---|---|
| Palabras del manuscrito | 8.271 | 6.426 |
| Intentos | 13 | 9 |
| Rechazos por longitud | 2, por exceso | 3, por defecto |
| Incumplimientos de contrato / reintentos técnicos | 0 / 0 | 7 / 7 |
| Rechazos de canon | 0 | 2 |
| Problemas del global | 4 de gravedad 1 + 1 de 2 | **0** |
| Invocaciones (registro) | 37 | 41 |
| Entrada / salida (palabras) | 403.727 / 77.066 | 164.426 / 33.742 |
| Tokens, coste | desconocido | desconocido |

**Lectura.** «A se lee como una novela; B como el resumen de una.» B: tres contradicciones verificables que el revisor de haiku **vio y degradó a observación** (título «La 4ª planta» sin referente; tres días que aparecen de la nada entre el cap. 4 y el 5; fotos que nadie tomó); un suceso de escaleta incumplido aprobado por encargo; el motivo «treinta años» repetido cinco veces; castellano roto no marcado por nadie («la agua», «había fallido», «La conocimiento», «hubiese trovado», «La peso», «sospecha través de datos»); un error de hecho copiado al libro de estado («vecina de cincuenta años» / «cincuenta años en el barrio»). A: canon de la biblia con la tensión de la llave de 2011 (previo al canon explícito); voz de la IA sostenida sin fisura; escenas con dos personas dentro.

**Conclusiones.** (1) Las métricas miden el harness, no la novela: cuatro de seis dependen de lo que el revisor declare. (2) haiku sale barato en volumen (41 % de la entrada de A) y caro en fricción (7 reintentos, 2 rechazos de canon, 4 pasos descartados). (3) La comparación limpia exige relanzar A con la spec v4. **El paso 2 de §7.8 no queda decidido y lo que hay apunta a que no** → A19.

**Cambios propuestos por el caso** (a decidir, consolidación §3): precondición de misma `config.version` y `calidad` + commit del harness en el registro (A7); `b_aguanta` no informativo si A cumple cero (A6); prohibir al revisor de continuidad degradar saltos temporales y objetos no sembrados (A12); título con referente para encargo (A12); aviso asimétrico de longitud según modelo (A11); tolerancia de formato en `invocar.md` (A8); recuento obligatorio desde `registro.md` al cerrar (A10); métrica informativa de lengua (A5).

---

<a id="e5"></a>
## E5 — La matriz de criterios no cubre los defectos reales

Revisión de ingeniería del 2026-09-17 sobre **30 defectos encontrados a mano** en el manuscrito de B. **La lista itemizada no está en el repositorio**; solo esta clasificación (→ A24).

| Clase | n | ¿Qué criterio lo cubre? | ¿Quién lo vio? |
|---|---:|---|---|
| A. Coherencia interna (plazo contradictorio, personaje antes de existir, fotos inexistentes) | 7 | Gravedad 1: **tiene dueño** | Nadie |
| B. Verosimilitud técnica (multímetro que mide «integridad estructural») | 4 | **Ninguno** | — |
| C. Mundo post-IA ausente, anacronismo social | 2 | **Ninguno** | — |
| D. Cohesión estructural (caps. 2 y 3 son la misma escena; motivo repetido) | 2 | **Ninguno** | — |
| E. Erratas y agramaticalidades («la agua», laísmo, «La conocimiento») | 13 | **Ninguno** | — |
| E′. Incoherencias locales | 2 | Gravedad 1 | Nadie |
| A7. Título huérfano | 1 | Gravedad 2 | Nadie |

**Unos 21 de 30 no tienen dueño en ningún contrato.** La palabra «gramática» no aparece en los cinco. `0 problemas` no es solo un fallo de haiku: es la respuesta correcta a las preguntas que se hicieron; opus también habría devuelto 0 en la clase E.

**Corolarios.** (a) La frontera problema/observación no está definida y un modelo pequeño la rellena hacia el lado barato. (b) Nada obliga a que un problema cite texto que existe. (c) **El sistema se corrige a sí mismo los exámenes**: `calcular_metricas` cuenta lo que los revisores declaran y nadie mide a los revisores; 6/6 CUMPLE sobre un manuscrito con 13 agramaticalidades. La pregunta del proyecto no se puede contestar con la instrumentación actual. (d) El ajuste de longitud **fabrica** defectos: cap. 5, 821 → 1.288 palabras, «treinta años» 1 → 3 veces. (e) Con criterios que cubrieran las clases B–E, casi todos los capítulos de B habrían sido rechazados y `reescrituras_max: 2` no habría bastado; es el dato que hoy no se tiene.

Propuestas derivadas, todas abiertas (A4, A5, A28): agente `corrector` (gravedades 6 lengua, 7 verosimilitud), gravedad 8 repetición para encargo, presencia del mundo dentro del criterio 4, `cita` obligatoria verificada con `grep`, reglas inviolables como lista de comprobación por capítulo, y evaluadores en Langfuse (§9.3.1) como fuente de verdad externa cuyo prompt calibrado **asciende** a criterio.

---

<a id="e6"></a>
## E6 — Estado de la observabilidad (2026-09-17 / 18)

**Langfuse**: 59 trazas, 4 de dominio (dos novelas: A por triplicado por `trace_id` no determinista, B una vez) y 55 de sesión (hook `Stop`). Las de sesión no aportan coste ni tokens (`inputPrice`, `outputPrice`, `modelId` a `null` en 1.540 observaciones); sí latencias reales.

**Exportador `herramientas/trazas/exportar.py`**, defectos verificados:

| Defecto | Consecuencia |
|---|---|
| `resultado_invocacion()` busca `"resultado ok"` y el registro escribe `resultado: ok` | `metadata.resultado = "desconocido"` en el 100 % de las generaciones; los filtros de los evaluadores no casan con ninguna |
| `input`/`output` nunca se rellenan | `null` en las 50 generaciones: nada que puntuar |
| Filas `pendiente` emitidas como generaciones | 50 generaciones para 41 invocaciones (+22 %) |
| Fila de corrección exportada como agente | `metadata.agente` = «correccion de la fila anterior…» |
| Todas las observaciones con el instante de la exportación | Latencias 0–0,015 s; Langfuse no ordena ni mide |
| `trace_id` no determinista | Reexportar duplica |
| Sin `encoding="utf-8"` explícito | Mojibake en cuanto un aviso lleve tilde |

**Lectura de vuelta**: `/api/public/traces` y `/observations` responden **410** para organizaciones creadas desde el 16-09-2026; `GET /api/public/v2/observations?…&fields=core,io,metadata` responde 200 (sin `fields`, `input`/`output`/`metadata` **no vienen**); la v2 no devuelve `name` (el agente se lee de `metadata.agente`); retardo de ingesta de ~45 s; límite de 30 peticiones/minuto (una descarga sin backoff se corta a las 600 observaciones en silencio).

**Evaluadores** (`herramientas/evaluadores/`): siete creados, tres reglas `enabled: false`, juez `openrouter/free`. Detalle en functional.md §9.3.1. Ninguno de los arreglos toca el harness (→ A13, A14).

---

<a id="e7"></a>
## E7 — Revisión del repositorio (2026-09-17): hook, deriva, duplicación

**El hook bloqueaba tres pasos que el flujo exige.** `inmutables.sh` decidía por existencia del fichero, y `aprobar()`, el bucle de `proponer_escaleta` y `detallar_arco` reescriben `biblia.md`, `escaleta.md` y `arco-AA.md` a propósito: **ninguna novela nueva podía aprobar su escaleta**. No se vio antes porque el hook es posterior a A. Arreglo (0.8.1): decidir **por aprobación** (frontmatter `aprobada`/`validada`) en esos tres y por existencia en el resto. Verificado a mano contra **28 casos** con código de salida. Descartados: que el interrogador devuelva ya `aprobada: true` (quien aprueba es el usuario, después), borrar antes de reescribir (ventana sin artefacto), extender el hook a Bash (parser nuevo dentro del bucle; queda como limitación conocida).

**Permisos**: `Write(/novelas/**)` y `Write(/comparativa/**)` no se consultan nunca en Claude Code (solo las reglas `Edit(ruta)` y `Read(ruta)` cubren rutas) y provocaban un aviso al arrancar; fuera. `Edit(/novelas/**)` es la que autoriza `Write`: **quitarla rompería el bucle** (consolidación §4). Entran `deny` de `Read(.env)` y `Read(.claude/settings.local.json)`; los cinco subagentes tienen `Read`.

**Deriva spec ↔ implementación.** La spec 0.8.0 declara hoja de continuidad, `resumen_max_palabras`, `hoja_continuidad_max_palabras`, `rechaza_con_gravedad_1/_2`, `resumenes_completos_ultimos` por perfil y `entrada_max_palabras_invocacion`; `config.json` (`version: 4`) no tiene ninguna, `capitulo.md` aplica `rechaza_con_graves` y `plantillas/informe.md` la cita. Los tres son coherentes entre sí; cambiar solo uno dejaría tres ficheros contradiciéndose. Nada lo detectó salvo una lectura manual → marcas `pendiente` en functional.md y A2, A3 (`comprobar.sh`).

**Duplicación.** La regla de inmutabilidad está escrita en cuatro sitios (spec §3.1, CLAUDE.md, SKILL.md §9, cabecera del hook) → A27.

**Lo que aguantó** y conviene no tocar: solo el harness escribe; la carpeta como único estado con git como registro de transacciones (`descartar()` reanudó sin perder nada aprobado); contratos con forma verificable (cero fallos de herramienta en 78 invocaciones entre A y B); ajustes de longitud (3 de 3); revisión partida.
