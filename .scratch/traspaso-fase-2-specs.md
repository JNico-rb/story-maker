# Traspaso: fase 2, las 18 specs (2026-09-23)

Fichero de trabajo temporal. Lo aplica un chat nuevo de Claude Code, que escribe las 18 specs **sin volver a hacer grill**: el grill de cada spec ya está hecho y el usuario lo confirmó. Se borra al terminar, junto con `.scratch/acuerdo-cohesion-docs.md` (ver §7).

## 0. Estado de partida

- **La fase 1 está terminada.** Los cuatro docs de referencia, ADR 0003, ADR 0004, `config.json`, `.env.example` y el README reflejan el acuerdo de cohesión y todas las decisiones posteriores del usuario. Los docs son la fuente de verdad: esta nota no repite su contenido, solo dice qué va en cada spec y qué ya se decidió.
- **Tres pases de auditoría de solo lectura** corrieron sobre los docs, y se corrigió todo lo que encontraron. Tras el tercero no hubo un cuarto. Si al escribir una spec aparece una contradicción entre docs, corrige el doc siguiendo `workflow/1-docs.md`, sin grill si es una incoherencia y no una decisión nueva, y anótalo en tu informe.
- **Decisiones del usuario posteriores al acuerdo, ya en los docs:**
  - al reanudar, la ejecución toma la config y las listas vigentes, en un tramo nuevo (`run_segment`);
  - la cuota de una sesión se cumple por construcción, sin corte en vivo, porque por OpenRouter el uso por turno llega a cero; se reconcilia al cerrar la sesión;
  - volver a registrar un capítulo reemplaza en la candidata lo que escribió su registro anterior (`architecture.md` §8.3);
  - los subagentes efímeros creados por un orquestador de modelo se descartan en el producto (§16).
- **Hechos medidos del Agent SDK** que la spec 001 necesita en su `design.md`, en la memoria del proyecto `project-agent-sdk-openrouter-hechos.md`:
  - `claudeMdExcludes` para los `CLAUDE.md` de los padres;
  - `strict_mcp_config=True`;
  - `tools=["Skill"]`, porque `tools=[]` también retira `Skill`;
  - `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` y `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`;
  - `ResultError` después del `ResultMessage` al agotar `max_turns`;
  - `disconnect()` tras `interrupt()`;
  - uso exacto solo en `ResultMessage`.
- **Pendiente de permiso:** el `git rm -r` de las carpetas antiguas de `specs/` (001–011, del producto anterior) lo denegó el clasificador del modo automático. Pide al usuario que lo apruebe o lo ejecute antes de crear `specs/001-base/`, que choca de nombre con la antigua. Las demás carpetas nuevas no chocan.

## 1. Reglas que aplican

- `CLAUDE.md` y [`workflow/2-specs.md`](../workflow/2-specs.md) para el formato de `spec.md`:
  - la casilla de aprobación;
  - Objetivo, Alcance con «fuera de alcance» y su motivo;
  - Requisitos `RF-<MÓD>-<n>`, cada uno condición → resultado observable, con prioridad y clase T/A/I/D/U;
  - RNF y Restricciones, si las hay;
  - Docs de referencia.
- Solo comportamiento en `spec.md`. Nombres de fichero, firmas y librerías van a `design.md`. Excepción: 001 recoge como requisitos comprobables las restricciones técnicas de `architecture.md` §6.12 y §14.
- **Todo el encargo es Obligatorio**, opcionales incluidos. Las cifras de `architecture.md` §15.2 se nombran sin valor.
- Cada requisito vive en una sola spec; las specs se citan por número.
- Usa los términos e identificadores de `definitions.md` tal cual, y consulta su §12 antes de nombrar nada.
- **Deja sin marcar todas las casillas de aprobación.** No escribas ningún `plan.md`. Sin commits. No toques `.claude/` ni `.mcp.json`.
- Idioma: specs en español; identificadores en inglés.

## 2. Decisiones del grill por spec (confirmadas; ya aplicadas a los docs)

| Spec | Decisión |
|---|---|
| 001 | 001 entrega la infraestructura del índice: sqlite-vec cargado, tablas FTS5 con `unicode61 remove_diacritics 2`, la tabla de vectores por (huella, modelo) y fastembed en Windows. 008 entrega todo lo que tiene términos del dominio |
| 002 | El registro devuelve 422 si el email no tiene formato válido o la contraseña tiene menos de 8 caracteres, y 409 si el email ya existe. Sin reglas de complejidad ni límite de intentos |
| 003 | La lista global la forman unos 30–50 términos en español, curados a mano, en `domain` |
| 004 | Una orden de la CLI sube los prompts cambiados como versión nueva sin etiqueta. Otra orden mueve la etiqueta tras pasar las evals |
| 005 | El brief importado solo entra por la API (`POST /api/novels {brief}`) y la CLI; la web no tiene pantalla de subida |
| 006 | TLA+ directo, no PlusCal: cada acción es un operador con nombre, que la tabla del README corresponde con una transición |
| 007 | Cancelar: el worker lee la marca antes de cada sesión y durante la que está en curso. Si aparece, la corta con `interrupt()` y `disconnect()`, rechaza la candidata y termina |
| 008 | Los gastos fijos del rol se estiman en cada sesión con el estimador local sobre los textos fijos; lo que añada el CLI sale como deriva al reconciliar |
| 009 | Cada comprobador de T1–T6 demuestra corrección y completitud: `true` si y solo si el invariante se cumple |
| 010 | Los 5+5 mundos que validan el catálogo de tropos los genera el planner, y una persona los etiqueta; quedan como fixture |
| 011 | Una palabra es lo que queda entre espacios tras quitar los signos sueltos, como las rayas de diálogo |
| 012 | En `linter-consistencia`, el diálogo, entre rayas o comillas, no cuenta para narrador ni tiempo verbal; sí para el tratamiento |
| 013 | La lectura solo se diseña y se prueba para escritorio |
| 014 | El revisor visual recorre portada, índice, ficha y los diez capítulos, siguiendo cada enlace |
| 015 | El valor nuevo de un cambio solo lo filtra la policy; un nombre repetido es el riesgo aceptado 21 |
| 016 | Solo se demuestra MCP Inspector, con el token en la cabecera; el README explica solo ese cliente |
| 017 | Calibración ligera de umbrales: los defectos sembrados más la revisión humana (`architecture.md` §10.3; §15.1 cerrada). **La presentación queda aplazada por el usuario:** deck, anexos, README de `presentation/`, vídeo y slide de coste no tienen RF todavía |
| 018 | Se arreglan todas las críticas y altas. Las medias y bajas se arreglan si es barato; si no, van razonadas a `verification.md` §6 |

## 3. Las 18 specs: qué entrega cada una

Carpeta y código de módulo como en el acuerdo, §5. Para cada spec, las secciones de los docs de las que salen sus requisitos. Es un reparto orientativo: si un requisito encaja mejor en otra spec, muévelo, pero que viva en una sola.

1. **`001-base` · BAS.** Incluye un `design.md` con el esquema por columna de todas las tablas de `architecture.md` §14.5, las versiones fijadas de §14.1 y las interfaces externas. Requisitos:
   - stack y restricciones (§14.1) y módulos con su regla de dependencia (§14.2, en CI con `import-linter`);
   - store con Alembic; conexión con WAL, `busy_timeout` y `foreign_keys`;
   - tablas de solo inserción que rechazan `UPDATE` y `DELETE`, salvo el reemplazo de §8.3;
   - validación entera de la config al arrancar; una cifra `null` falla de forma accionable al leerse;
   - ajustes del servidor (`definitions.md` §11), con `JWT_SECRET` de 32 caracteres o más;
   - traducción de la clave de OpenRouter;
   - puerto de agente con su doble;
   - workspace: `cwd`, solo su `CLAUDE.md` y solo los MCP declarados;
   - la infraestructura del índice (decisión 001);
   - escritura solo en el directorio de datos (§11.6), con la telemetría y la memoria del CLI apagadas;
   - uvicorn sin `--reload` en Windows;
   - FastAPI sirve el frontend y la API bajo `/api`, con el proxy de Vite en desarrollo;
   - esquema OpenAPI estático y cliente generado, con comprobación de deriva;
   - CI por cambio (`verification.md` §4.7, salvo TLC, Lean y la lectura de vuelta, que van en 006, 009 y 004);
   - frontend base FSD con el tema corporativo;
   - CLI mínima con la orden de comprobaciones de entorno;
   - las demostraciones de entorno de §15.3 (clase D).
2. **`002-aut-autenticacion` · AUT.** §13.1, §14.3: registro, acceso, JWT HS256 de 24 h con `exp`, `aud` e `iss`, 401, 404 para lo ajeno, propiedad de cada recurso, pruebas de aislamiento por la API (RT4) y página de acceso. El aislamiento por MCP va en 016.
3. **`003-pol-politica-y-guardarrailes` · POL.** §11.1–§11.4, §7.5 (hook de policy), §11.2 y §11.3:
   - normalización y coincidencias por nivel y variante: pruebas de un caso por nivel más acento y plural;
   - siembra de la lista global y API de la lista de cliente;
   - motor de políticas: `allow`, `deny` y `flag`;
   - hook de policy: lista blanca, campos narrativos sin escanear las listas y `Skill` solo con `personalizacion-natural`;
   - sesiones sin tools integradas y modo de permisos;
   - revisor visual limitado al origen de la vista previa;
   - audit log de solo inserción, con sus columnas y orígenes, y su endpoint;
   - detector de inyección, que marca y no deniega;
   - eventos en la traza.
4. **`004-obs-observabilidad` · OBS.** §12 y §11.5 (coste):
   - `auth_check` al arrancar;
   - sesión por novela y las cinco clases de traza; una ejecución reanudada conserva la suya;
   - commit y huella de la config por tramo;
   - nombres de span, generación con `usage_details`, `cost_details` y la lista de ids `gen-…`;
   - coste: uso exacto por `operation.pricing`;
   - scores agregados y por criterio, copiados en SQLite, con sus excepciones;
   - máscara por novela, y la unión de máscaras en MCP;
   - prompts: fichero por rol y las órdenes de la CLI de subir y promover (decisión 004); se leen por etiqueta;
   - si Langfuse falla: `interrupted` o 503;
   - lectura de vuelta en CI con reintentos.
5. **`005-ent-entrevista-y-brief` · ENT.** §3, `domain-knowledge.md` §4.3 y §5.2:
   - creación de la novela, con su fecha;
   - entrevistador en la API, una sesión por turno, 503 sin guardar;
   - reglas del brief: faltantes con las prohibidas preguntadas, C1–C7 y la cota;
   - confirmación;
   - extractor: citas, sujeto conocido, solape con frases marcadas y 422 por tamaño;
   - aceptar y marcar hechos;
   - brief importado (decisión 005), con su traza;
   - presupuesto de la entrevista;
   - scores `schema-brief` y `citas-verificadas`;
   - 409 sobre un brief ya confirmado;
   - página de entrevista.
6. **`006-tla-especificacion-del-harness` · TLA.** §10.6, `verification.md` §4.10 y §3.12:
   - las tres especificaciones en TLA+ directo;
   - invariantes 8–11, historia lineal, confirmación de un solo uso, caducada y del propietario;
   - vivacidad con equidad débil;
   - el modelo pequeño con su `.cfg`, y una configuración con un invariante roto que debe dar contraejemplo;
   - TLC en CI;
   - la tabla de correspondencia en el README;
   - el diagrama completo en §10.6;
   - los contraejemplos, a `verification.md` §8.
7. **`007-run-ejecuciones` · RUN.** §9.1, §9.2, §7.6, §11.5 (tope), §10.4 (aserciones), §14.3 y §14.4:
   - lanzar una generación, con 409 si el brief no está confirmado, si hay otra sin terminar o si ya hay versión publicada;
   - cola global con una sola activa y su posición;
   - worker y quién lanza cada ejecución;
   - caídas detectadas por PID y hora de arranque;
   - estados y transiciones;
   - cancelar (decisión 007);
   - reanudar: tramo nuevo con config y listas vigentes, intentos nuevos y los 409;
   - puntos de control de capítulo y de fase;
   - límites y tipos de error;
   - presupuesto: `budget_exceeded`;
   - SSE por instantáneas con `fetch`;
   - endpoints de ejecuciones y `GET /novels/{id}`;
   - estado derivado de la novela;
   - informe calculado al pedirlo;
   - aserciones del orquestador que acaban en `internal_error`;
   - página de progreso.
8. **`008-mem-memoria` · MEM.** §6 entero:
   - CanonCards;
   - corte temporal;
   - copia por versión y vectores por huella;
   - quién escribe el índice;
   - dos colecciones, RRF y BM25 en código;
   - arrastre por el grafo y doble consulta;
   - residentes y entradas de la llamada;
   - proyección del outline, `ResumenRodante` y `EstadoDelMundo` compacto (invariante 4);
   - cuotas y escasez;
   - guardián de ventana: techo por ejecución, reparto, sesiones en serie, reserva, gastos fijos estimados (decisión 008) y orden de recorte, con `config infactible`;
   - reconciliación al cierre;
   - trazabilidad y ventana guardada;
   - modelo de incrustación congelado.
9. **`009-lea-validador-formal-de-la-historia` · LEA.** §10.5, ADR 0004, `domain-knowledge.md` §5.3:
   - tipos, T1–T6 y comprobadores con corrección y completitud (decisión 009);
   - `--wfail` y auditoría de axiomas;
   - ficheros positivos y negativos;
   - generador desde una lista de eventos: las dos cronologías, la analepsis contada una vez y el personaje sin fecha fuera de T2 y T5;
   - seudonimización: ids y desplazamiento de 400 años, con su propiedad;
   - JSON con el testigo y su traducción;
   - verificador local y remoto (protocolo y seguridad del workflow), con `max_verifier_seconds`;
   - fichero guardado con su resultado;
   - score `cronologia-lean`.
10. **`010-pln-planificacion` · PLN.** §4, §5, `domain-knowledge.md` §6:
    - canon del brief en el primer paso, con la tabla de §4.1;
    - entradas del planner;
    - `submit_world` y `grafo-causal`;
    - `submit_cast`;
    - `submit_outline` y `outline`;
    - Lean sobre el outline propuesto, con 009;
    - replanificación como intento;
    - StyleSheet;
    - congelación con el canon inicial y su índice como punto de control del capítulo 0;
    - catálogo de tropos, curado y aprendido, con la prueba 5+5 (decisión 010).
11. **`011-cap-produccion-por-capitulo` · CAP.** §7.3–§7.5, §8, §10.2 (validadores del hook) y §10.3 (rúbrica de capítulo):
    - writer;
    - hook de validación con `longitud-capitulo` (decisión 011, fronteras 999, 1.000, 1.500 y 1.501), `nombres-exactos` con las variantes y `delta-declarado`;
    - crítico y rúbrica;
    - veredicto con la tabla de §8.2;
    - editor;
    - registrador y `delta-real`, con enrutado por acción;
    - transacción de aceptación (invariante 5, con fallo inyectado) y reemplazo al volver a registrar (§8.3);
    - skill `personalizacion-natural` y `CLAUDE.md` del workspace.
12. **`012-lin-linters-de-prosa` · LIN.** §13.3: los cuatro linters como criterios, cada uno con sus identificadores (§10.3). Avisos, al informe o al editor si ya lo llama un bloqueante; umbrales sin calibrar; diálogo excluido (decisión 012); dónde corren; scores.
13. **`013-lec-lectura-web-y-pdf` · LEC.** §9.7, §13.6 y §14.3:
    - lectura de una versión: portada, índice, capítulos, ficha con la regla de enlaces, selector y marcas de cambiado;
    - lista de versiones;
    - story bible por versión;
    - «mis novelas»;
    - vista previa con token y cookie, 404 y revocación;
    - ruta `print`;
    - PDF al publicar, `pdf-enlaces` con `pdf-indice` y `pdf-ficha`, y fallo de render;
    - fichero guardado y servido;
    - solo escritorio (decisión 013).
14. **`014-pub-publicacion-y-versiones` · PUB.** §9.3, §9.4, §10.2 y §10.3 (rúbrica de novela):
    - candidata, copia de todas las tablas de ámbito versión, número al publicar, inmutabilidad y capítulos cambiados por huella;
    - rechazo solo al cancelar;
    - gate en tres etapas y su tabla de enrutado; cada ciclo es un intento;
    - `elementos-obligatorios` y `arcos-cerrados`;
    - juez;
    - revisor visual con Playwright MCP: los diez capítulos, cada enlace seguido (decisión 014) y el veredicto por código;
    - publicación.
15. **`015-cam-cambios-y-edicion-manual` · CAM.** §9.5, §9.6, §13.4:
    - selección y petición;
    - interpretación en la API: policy, planner con `propose_change`, `alcance-propuesta`, 201 y 422 `rejected`;
    - capítulos afectados;
    - código de 15 minutos y confirmación: 202, 422, 409 y 404;
    - revalidación al arrancar;
    - edición dirigida en paralelo;
    - `valor-antiguo-ausente`;
    - regeneración de respaldo;
    - nuevo registro, gate y `applied`;
    - edición manual: `PUT` con 409 y 422, la ejecución de edición con su revalidación, `delta-real` sin `hechos-inmutables` para lo que cambió el cliente, propagación y rechazo;
    - linter en vivo, sin audit log ni scores;
    - interfaz de cambio y de edición.
16. **`016-mcp-servidor-mcp` · MCP.** §13.2: FastMCP montado con su lifespan y su versión fijada; `JWTVerifier` HS256; las cinco tools de lectura sin efecto; `download_novel` con el PDF guardado; `request_change` y `confirm_change`; schemas; una traza por llamada con la máscara; audit log de las escrituras; aislamiento por MCP (RT5); README solo para MCP Inspector (decisión 016).
17. **`017-evl-evaluacion-del-sistema` · EVL.** §10.7, §10.8, §10.3 (calibración) y `verification.md` §4.2:
    - cinco briefs ficticios;
    - la CLI reproduce el brief de ejemplo de extremo a extremo y deja `ejemplos/novela-ejemplo.pdf`;
    - la CLI lanza las evals;
    - tabla por brief;
    - evals de rol: extractor, registrador y entrevistador (dorados); crítico y juez (sembrados); observación visual; datos de ejecución;
    - revisión humana en la cola de anotación, con diferencia media y acuerdo exacto;
    - calibración ligera (decisión 017);
    - iteración de ajuste con las versiones de prompt;
    - cambios reales;
    - protocolo de coste por novela y por revisión, contrastado con OpenRouter;
    - el caso de Lean;
    - resultados en `verification.md` §4.2 y §8.
    - **La presentación no entra** (decisión 017).
18. **`018-sec-auditoria-de-seguridad` · SEC.** §13.5, `verification.md` §4.11 y §4.9: subagente, skill y comando de Claude Code, que implementa el chat que lleva `.claude/`; inyección con los casos RT; exfiltración; `pip-audit` y `pnpm audit`; `detect-secrets` sobre `git log -p --all`; `docs/security-report.md` con severidad y cambio; política de arreglo (decisión 018); la fila de §9.4.

**Entregables de Claude Code** (encargo: `CLAUDE.md`, `.claude/` con memoria y comandos, `.mcp.json` con browser MCP, uso del browser MCP, skills y subagentes documentados). Ponlos como Restricciones de clase I en 001, salvo el de seguridad, que va en 018. Su registro vive en `verification.md` §9.

## 4. Matriz temporal de cobertura

Crea `docs/relation-matrix.md`: requisito del encargo → sección de los docs → RF de la spec → hueco. Usa la numeración E1–E92 de abajo. Las filas de la presentación (E6, E79, E89–E92 y la parte de slide de E91) llevan el hueco «aplazado por el usuario (017)». Todas las demás filas deben acabar sin hueco.

E1 personalización natural · E2 calidad narrativa mínima · E3 validadores, editor y juez equilibrados · E4 10 capítulos de 1.000–1.500 · E5 repo: código, README, brief de ejemplo, `.env.example`, /docs · E6 /presentacion/ con deck, anexos y README · E7 entrevista: datos y prohibidas · E8 faltantes y contradicción · E9 texto libre no confiable · E10 brief con schema · E11 índice navegable · E12 ficha con enlaces · E13 portada con dedicatoria · E14 cambio desde la página · E15 regenerar solo los afectados · E16 marcar los cambiados · E17 rama PDF, no elegida (`architecture.md` §16) · E18 versión anterior conservada · E19 ≥3 roles · E20 `CLAUDE.md`, skill y dos hooks · E21 tools con schema · E22 retries con límite · E23 tokens y coste por novela · E24 story bible en SQLite con uso por capítulo · E25 tabla de cronología · E26 resúmenes por capítulo · E27 checkpoint y reanudación · E28 validadores con nombre, punto y score · E29 schema del brief y de cada rol · E30 nombres exactos · E31 longitud · E32 obligatorios contra la tabla de hechos · E33 prohibidas · E34 validación visual por browser MCP · E35 juez con rúbrica · E36 revisión humana · E37 fichero Lean · E38 ≥2 invariantes · E39 Lean automático que bloquea y vuelve al editor · E40 caso que solo detecta Lean · E41 TLA+ del flujo · E42 ≥3 invariantes de seguridad · E43 vivacidad · E44 TLC con modelo pequeño · E45 correspondencia en el README · E46 contraejemplos documentados · E47 cinco briefs · E48 tabla por brief · E49 iteración de ajuste · E50 traza y sesión · E51 spans con nombre · E52 tokens, coste y latencia por llamada, capítulo y novela · E53 scores asociados; TLC en desarrollo · E54 prompts versionados · E55 prohibidas antes de aceptar · E56 tres niveles en SQLite · E57 normalización · E58 reescritura con límite y parada · E59 coincidencia en audit log y Langfuse · E60 tests por nivel y variante · E61 audit log · E62 100.000 tokens · E63 servidor MCP con cinco tools · E64 MCP: schema, solo lectura, Langfuse, README e identidad · E65 escritura MCP con confirmación · E66 linters de prosa · E67 linter de edición manual · E68 demostraciones generales de Lean · E69 TLA+ de regeneraciones concurrentes · E70 login · E71 agente de seguridad e informe · E72 `ejemplos/novela-ejemplo.pdf` · E73 spec inicial · E74 trade-offs · E75 explainers · E76 diagramas · E77 registro de iteraciones · E78 red-team log · E79 vídeo · E80 sin API keys · E81 `CLAUDE.md` cuidado · E82 `.claude/` con memoria y comandos · E83 config MCP con browser · E84 uso del browser MCP documentado · E85 skills referenciadas · E86 subagentes y comandos documentados · E87 evals medibles · E88 imagen corporativa · E89 idioma de la presentación · E90 anexos · E91 slide de presupuesto y coste · E92 evidencias de la presentación.

Los de proceso —E73–E78 y E84–E86— los cubren secciones de los docs y el cierre de cada feature (`workflow/4-code.md`). Dales su RF de clase I en la spec que los produce, o en 001 si no hay otra.

## 5. Registro de proceso

Añade a `docs/verification.md` §9.4 una fila por cada subagente que uses. El grill de las 18 specs ya queda contado en esta nota, así que añade también su fila:

> 2026-09-23 · skill `grill-me`, cinco rondas con `AskUserQuestion` · una ronda por spec antes de escribirla · 18 decisiones de alcance y frontera, aplicadas a los docs

## 6. Hecho cuando

- Existen las 18 carpetas, con `spec.md` y las casillas sin marcar; 001 tiene además `design.md`.
- Las carpetas antiguas están borradas, con el permiso del usuario.
- La matriz no tiene más huecos que los de la presentación aplazada.
- `verification.md` §9.4 tiene sus filas.

## 7. Al terminar

Pide al usuario que marque las casillas de las specs. Pregúntale también si se borran ya la matriz y los dos ficheros de `.scratch/`, o si se conservan hasta que la presentación deje de estar aplazada. El acuerdo pedía borrarlos cuando no quedara ningún hueco.
