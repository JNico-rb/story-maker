# Examen final · Harness Engineering

## Contexto

Una empresa quiere vender novelas personalizadas para regalar: a un hijo, a la pareja, para celebrar una boda, un aniversario o una jubilación. Tu tarea es diseñar y construir el sistema agéntico que las genera, y presentarlo como solución técnico-comercial.

El objetivo del cliente tiene dos dimensiones igual de importantes:

- **Personalización.** La novela debe incorporar de forma natural los datos del destinatario: su nombre, su historia, los detalles que el comprador ha aportado. El destinatario debe reconocerse en la novela y sentir que fue escrita para él.
- **Calidad narrativa mínima.** La novela no tiene que ser un best seller, pero debe ser agradable de leer. No se aceptan novelas con problemas narrativos evidentes: inconsistencias de personajes, saltos temporales sin sentido, capítulos que se contradicen, prosa mecánica o repetitiva, o finales abruptos. El lector debe poder leerla de principio a fin sin tropezar. La personalización no justifica una mala escritura.

El sistema no puede optimizar solo para que los datos aparezcan: debe también producir una historia que funcione como historia. Los validadores, el rol de editor y el LLM-as-judge deben reflejar este equilibrio.

**Proyecto individual.** Novelas de 10 capítulos de unas 1.000–1.500 palabras cada uno. La complejidad está en el harness, no en la extensión.

## Entregables

- **Repositorio storyMaker** — el proyecto de novelas personalizadas: código, README, brief de ejemplo reproducible, `.env.example` y carpeta `/docs` con toda la documentación de proceso.
- **Repositorio MyFactory** — herramientas y utilidades del curso, ya iniciado durante las prácticas.
- La presentación formal y sus anexos en la carpeta `/presentacion/`, commiteados antes del plazo de entrega del repo storyMaker.

Formato de los archivos en `/presentacion/`:

- el deck principal en PDF y en el formato original editable (PowerPoint, Keynote o similar);
- los anexos como ficheros individuales nombrados de forma descriptiva (por ejemplo, `anexo-tla-spec.pdf`, `anexo-evals-tabla.pdf`);
- un `README.md` en la misma carpeta que liste el contenido y el idioma elegido.

## Entrega final

La entrega se hace enviando un email a xesca.alabart@easyspecs.ai con el asunto:

```text
[Harness Engineering] Entrega final — <nombre del estudiante>
```

El email debe incluir:

- el link al commit final del repositorio storyMaker;
- el link al commit final del repositorio MyFactory;
- una frase de no más de tres líneas resumiendo la decisión de diseño más importante que tomaste.

No se aceptan entregas fuera de plazo. El commit final es el que cuenta, no la hora del email.

## Alcance del proyecto

### 1. Configuración

- Un agente entrevistador recoge los datos del destinatario: nombre, edad, rasgos, recuerdos, género, tono y extensión. También recoge las palabras o temas que el cliente no quiere que aparezcan.
- Detecta los datos que faltan y al menos un tipo de contradicción (por ejemplo, edad frente a género o tono).
- El usuario puede pegar texto libre (una anécdota, una carta) del que se extraen hechos. Ese texto se trata como contenido no confiable.
- El resultado de la entrevista es un brief estructurado y validado con schema.

### 2. Lectura interactiva (web o PDF)

La novela se entrega como web o como PDF interactivo. En ambos casos debe incluir:

- un índice de capítulos navegable;
- una ficha de personajes y lugares generada desde la story bible, con enlaces al capítulo donde aparece cada uno;
- una portada con dedicatoria personalizada.

Si es web, el lector puede seleccionar un fragmento o un hecho y pedir un cambio desde la propia página ("el perro se llama Nala"). El sistema identifica los capítulos que usan ese hecho, regenera solo esos sin romper la continuidad y marca en la lectura qué capítulos han cambiado respecto a la versión anterior.

Si es PDF, el cambio se pide desde fuera del documento (formulario o CLI) y se genera una nueva versión del PDF. Esa versión incluye una página inicial de "novedades" con los capítulos modificados y enlaces internos a cada uno.

En ambas opciones se conserva la versión anterior de la novela.

### 3. Harness

- Tres roles como mínimo: planner, writer y editor/critic.
- Un archivo de instrucciones `CLAUDE.md`, una skill reutilizable y dos hooks: uno de validación del capítulo y otro de policy.
- Tools con schema validado.
- Retries con límite.
- Registro de tokens y coste por novela a través de Langfuse (ver sección de observabilidad).

### 4. Memoria

- Una story bible en SQLite (obligatorio) en la que cada hecho registra en qué capítulos se usa. Incluye una tabla de cronología (eventos, momento, personajes, lugar) que alimenta el validador formal.
- Resúmenes por capítulo para construir el contexto de los siguientes.
- Checkpoint por capítulo: si la generación falla, se reanuda desde el último capítulo completado.

### 5. Validación y evaluación

El sistema debe incluir validadores de cuatro tipos. Cada validador tiene un nombre, se ejecuta en un punto concreto del harness (hook, rol editor o gate antes de publicar una versión) y envía su resultado a Langfuse como score.

#### a) Validadores programáticos (deterministas)

Mínimo tres, por ejemplo:

- el brief y la salida de cada rol cumplen su schema;
- el nombre del destinatario y los personajes aparecen escritos exactamente como en la story bible;
- la longitud de cada capítulo está dentro del rango;
- cada elemento personalizado obligatorio del brief aparece en al menos un capítulo, comprobado contra la tabla de hechos de SQLite;
- el guardrail de palabras prohibidas (ver sección 7);
- validación visual via browser MCP: el agente abre la novela en el browser, navega por los capítulos y verifica que el índice, la ficha de personajes y la portada renderizan correctamente; si detecta un error visual, lo registra como fallo y lo devuelve al writer o al rol correspondiente.

#### b) Validadores no programáticos (semánticos)

Mínimo dos:

- un LLM-as-judge con rúbrica que evalúe continuidad, tono, calidad narrativa (arco de la historia, coherencia de personajes, ritmo entre capítulos) y que la personalización esté integrada de forma natural y no forzada, con una puntuación por criterio y una justificación;
- una revisión humana de al menos una novela completa, con la misma rúbrica, para comparar el juicio humano con el del LLM.

#### c) Validador formal de la historia (Lean 4)

La cronología de la historia se modela formalmente y se verifica:

- a partir de la story bible en SQLite se genera un fichero Lean con los hechos temporales: eventos, momento, personajes presentes, lugar, fechas de nacimiento;
- se definen en Lean al menos dos invariantes, por ejemplo:
  - los eventos respetan el orden temporal declarado;
  - la edad de un personaje en cada evento es coherente con su fecha de nacimiento;
  - un personaje no está en dos lugares en el mismo momento;
  - un personaje no aparece después de un evento que lo excluye (muerte, partida definitiva);
- la verificación se ejecuta de forma automática (`lake build` o `lean`) y, si falla, la versión de la novela no se publica y el fallo vuelve al editor como feedback;
- debe mostrarse al menos un caso real en el que el validador formal detecta una incoherencia que los otros validadores no detectaron, o justificar por qué no se encontró ninguno.

#### d) Validador formal del sistema (TLA+)

Mientras Lean verifica la coherencia de la historia, TLA+ verifica el comportamiento del harness. Referencia: [learntla.com](https://learntla.com).

- Una especificación en TLA+ o PlusCal del flujo de generación como máquina de estados: configuración → planificación → escritura de capítulo → validación → publicación de versión, incluyendo retries, reanudación desde checkpoint y regeneración por cambio del lector.
- Al menos tres invariantes de seguridad, por ejemplo:
  - nunca se publica una versión con un capítulo que no ha pasado todos los validadores;
  - la reanudación desde checkpoint no duplica ni pierde capítulos;
  - la versión anterior de la novela se conserva siempre tras una regeneración;
  - el número de reintentos nunca supera el límite.
- Al menos una propiedad de liveness: toda generación termina publicando una versión o deteniéndose con error; nunca queda en un bucle infinito.
- Verificación con el model checker TLC sobre un modelo pequeño (por ejemplo, 5 capítulos y 2 reintentos), con la configuración incluida en el repo.
- La especificación debe corresponder al código: el README explica qué estado o transición del código implementa cada acción de la especificación.
- Si TLC encontró algún contraejemplo durante el desarrollo, se documenta junto con el cambio que hizo en el código.

#### Evaluación del sistema

- Cinco briefs de prueba, incluido al menos uno adversarial (injection en el texto libre) y uno diseñado para provocar una incoherencia temporal.
- Una tabla que muestre, por brief, qué validadores pasaron y cuáles fallaron.
- Una iteración de tuning documentada, con los resultados antes y después.

### 6. Observabilidad

- Cada generación de novela es una traza en Langfuse, agrupada por sesión (una sesión por novela, incluyendo la entrevista y las regeneraciones posteriores).
- Cada rol (entrevistador, planner, writer, editor) y cada llamada a tool aparece como span con nombre identificable.
- Tokens, coste y latencia visibles por llamada, por capítulo y por novela.
- Los resultados de todos los validadores (programáticos, semánticos y Lean) se envían a Langfuse como scores asociados a la traza correspondiente. TLC se ejecuta en desarrollo, no en cada generación.
- Los prompts versionados en Langfuse, de forma que la iteración de tuning muestre qué versión de prompt produjo cada resultado.

### 7. Guardrails

- Un guardrail de palabras prohibidas, aplicado en código sobre cada capítulo antes de aceptarlo:
  - listas guardadas en SQLite, en tres niveles: globales (insultos, términos ofensivos) y por novela, definidas por el cliente en la configuración (por ejemplo, el nombre de una expareja o un tema que no quiere que aparezca);
  - la detección normaliza el texto antes de comparar: mayúsculas, acentos, plurales y variantes simples;
  - si hay coincidencia, el capítulo se devuelve al writer para reescribirlo, con un límite de intentos; si se agota el límite, la generación se detiene y se informa;
  - cada coincidencia queda registrada en el audit log y en Langfuse;
  - tests que cubran al menos un caso de cada nivel y un caso de variante (acento o plural).
- Un audit log de las decisiones del policy engine.
- Uso de un maximo de 100.000 Tokens Concurrentes.

### Opcional (suma nota)

- **Servidor MCP para consultar y descargar novelas.** Expone la plataforma como servidor MCP al que conectar cualquier cliente (Claude Desktop, Claude Code o MCP Inspector). Se recomienda implementarlo con FastMCP como plugin del FastAPI que ya tienen, para no añadir infraestructura nueva. Tools sugeridas:
  - `list_novels`: lista las novelas con su estado y versión actual.
  - `get_chapter`: devuelve un capítulo concreto de una versión concreta.
  - `list_versions`: historial de versiones de una novela y qué capítulos cambiaron en cada una.
  - `query_story_bible`: consulta personajes, lugares, hechos y cronología.
  - `download_novel`: devuelve la novela completa en PDF.

  Requisitos si se implementa: cada tool con schema validado; servidor de solo lectura; cada llamada registrada en Langfuse; el README explica cómo conectarlo a un cliente MCP. Si además tienen login, el servidor respeta la identidad del usuario autenticado.
- **Tools de escritura sobre el servidor MCP** (pedir un cambio del lector desde un cliente MCP), con permisos y confirmación. Requiere el servidor MCP implementado.
- **Nuevos tipos de linters de prosa** además de los validadores obligatorios, por ejemplo:
  - repeticiones de palabras o muletillas en un mismo párrafo;
  - frases demasiado largas o legibilidad inadecuada para el tono del destinatario;
  - abuso de adverbios, clichés o expresiones típicas de texto generado por IA;
  - consistencia de estilo: tiempo verbal, narrador (primera o tercera persona), tratamiento entre personajes.

  Pueden basarse en herramientas existentes (como Vale o LanguageTool) con reglas propias, o escribirse desde cero.
- **Linter propio para edición manual de la novela:** el cliente o un editor humano modifica el texto a mano, y el linter señala los problemas mientras se edita:
  - integrado en el editor web, en una extensión de VS Code o como servidor LSP;
  - comprueba el texto editado contra la story bible (nombres, hechos, cronología) y contra las palabras prohibidas;
  - una edición manual que cambia un hecho actualiza la story bible y vuelve a pasar por los validadores (incluido Lean) antes de publicar la versión.
- **Invariantes adicionales en Lean**, o demostraciones generales (para cualquier cronología) en lugar de comprobaciones sobre una cronología concreta.
- **Especificación TLA+** del servidor MCP o de la concurrencia entre regeneraciones simultáneas.
- **Login de usuarios con SQLite.** Un sistema de autenticación básico que permita a cada cliente acceder solo a sus propias novelas:
  - registro e inicio de sesión con email y contraseña hasheada (bcrypt o similar), almacenados en SQLite;
  - sesión gestionada con token (JWT o similar);
  - cada novela, configuración y entrada del audit log queda asociada al usuario propietario;
  - si se ha implementado el servidor MCP, respeta la identidad del usuario autenticado: `list_novels` y `download_novel` solo devuelven las novelas del usuario en sesión;
  - tests que verifiquen que un usuario no puede acceder a las novelas de otro.
- **con agentes o skills.** Un agente o skill dedicado que analiza el sistema en busca de vulnerabilidades, ejecutado sobre el propio repo o sobre la API del harness. Ejemplos de lo que puede cubrir:
  - prompt injection: intentos de modificar el comportamiento del sistema a través del texto libre aportado por el usuario en la configuración;
  - exfiltración de datos: comprueba que un brief no puede extraer información de otra novela o de otro cliente;
  - dependencias: análisis de las dependencias del proyecto en busca de paquetes con vulnerabilidades conocidas (por ejemplo, con `pip audit` o `npm audit`, orquestado por el agente);
  - secrets leak: el agente escanea el historial de commits en busca de API keys o credenciales expuestas accidentalmente;
  - los resultados del análisis se guardan en un informe en `/docs/security-report.md` y las vulnerabilidades encontradas se registran con su severidad y el cambio que se hizo para resolverlas.

### Fuera de alcance

Pagos, cuentas de usuario, impresión física, ilustraciones, audio y despliegue en producción.

## Los repositorios deben incluir también

- **Novela de ejemplo generada:** el PDF de una novela completa de 10 capítulos, generada con el brief de ejemplo del README, commiteada en `/ejemplos/novela-ejemplo.pdf`. Es la evidencia de que el sistema funciona de principio a fin. Si el formato de lectura elegido es web, se incluye igualmente el PDF exportado.
- **`/docs` en storyMaker con la documentación de proceso.** No se corrige el resultado, se corrige el razonamiento que llevó a él:
  - **Spec inicial:** qué se decidió construir y por qué, antes de escribir código.
  - **Trade-offs:** cada decisión de diseño relevante explicada como decisión: opciones, criterios y elección. Por ejemplo: single-agent vs multi-agent, formato de la story bible, elección del modelo de lectura, integración de TLA+ con el flujo real, invariantes de Lean priorizados.
  - **Explainers:** uno por cada concepto del curso aplicado en el proyecto. Breves. Para demostrar que se entiende lo que se aplica, no para copiar la teoría.
  - **Diagramas:** arquitectura del harness, máquina de estados de TLA+, esquema SQLite, tabla de validadores con su punto de ejecución.
  - **Registro de iteraciones:** qué cambió tras cada eval o contraejemplo de TLC o Lean, y por qué. No un diario, sino un log de decisiones con causa y efecto.
  - **Red-team log:** casos adversariales probados, qué validador los detectó (o no) y cómo se resolvió.
- **Vídeo de demo** en cualquier formato (Loom, MP4 u otro), de la duración que se considere necesaria para mostrar el sistema con claridad. Debe estar subido al repositorio storyMaker dentro de `/presentacion/`, o enlazado desde su `README.md` si el fichero supera el límite de tamaño de GitHub.
- **Sin API keys en ningún repo.** Usar `.env.example`.
- **Claude Code.** Los estudiantes trabajan con Claude Code. El repo debe reflejar ese uso:
  - el fichero `CLAUDE.md` en la raíz del repo (ya obligatorio como archivo de instrucciones del harness) debe estar cuidado y ser legible: es parte del examen;
  - la carpeta `.claude/` con los ficheros de memoria y comandos personalizados debe estar commiteada;
  - el fichero de configuración MCP (`.claude/mcp.json` o equivalente) debe incluir un servidor MCP de inspección de browser (Chrome MCP, Playwright MCP o similar), de forma que Claude Code pueda abrir la lectura web de la novela y verificar el resultado visualmente;
  - el uso real del browser MCP debe estar documentado en `/docs`: qué inspeccionó el agente, qué detectó y qué cambio provocó en el código o en los prompts;
  - los ficheros de skills usados o creados durante el desarrollo deben estar en el repo y referenciados desde `/docs`;
  - si se han usado subagentes o comandos `/` propios, deben estar documentados en `/docs` con su propósito y resultado.

**Un proyecto sin evals con resultados medibles, o sin documentación de proceso en `/docs`, no aprueba.**

## Presentación (10 minutos)

La presentación es una propuesta formal a cliente. Debe tener imagen corporativa propia: nombre de empresa, logotipo, paleta de colores y tipografía aplicados de forma consistente en todas las slides. No se acepta una plantilla genérica de PowerPoint ni un deck sin identidad visual.

**Idioma.** La presentación puede estar en inglés o en castellano. Se recomienda usar los términos técnicos en inglés independientemente del idioma elegido para el resto del contenido.

**Anexos.** La presentación puede incluir todos los anexos que se consideren necesarios, al final del deck. Los anexos se revisan y se valoran dentro de la nota final. Ejemplos de material que encaja bien como anexo: diagramas de arquitectura detallados, especificación TLA+ comentada, tabla completa de resultados de evals, esquema de la base de datos SQLite, análisis de sensibilidad extendido, red-team log, comparación de modelos de LLM considerados, capturas de Langfuse.

**Slide obligatoria de portada:** nombre de la empresa presentadora, nombre del cliente ficticio al que se presenta, fecha y nombre del estudiante.

| Bloque | Tiempo | Contenido mínimo |
|---|---|---|
| Portada y contexto | 0,5 min | Empresa presentadora, cliente, ocasión |
| Problema y cliente | 1 min | Quién compra, para qué ocasiones y por qué las alternativas actuales no funcionan |
| Configuración y lectura | 1 min | Cómo se configura una novela y cómo se lee y se corrige (web o PDF) |
| Arquitectura del harness | 2 min | Diagrama de roles y bucle, gestión del contexto, story bible, tools, hooks y justificación del diseño |
| Validación, evaluación y observabilidad | 2 min | Los cuatro tipos de validadores y dónde actúan; tabla de resultados por brief; un fallo detectado por Lean; las propiedades verificadas con TLC; la mejora tras el tuning; una traza real en Langfuse |
| Guardrails | 0,5 min | Palabras prohibidas (con un ejemplo de detección y reescritura), tratamiento de datos personales, injection y audit log |
| Presupuesto y coste | 1 min | Ver detalle abajo |
| Demo y cierre | 1 min | Un cambio del lector que se propaga a los capítulos afectados, visto en la web o en el PDF regenerado; riesgos y siguientes pasos |
| Contraportada | — | Datos de contacto de la empresa presentadora |

Después de la presentación, 5 minutos de preguntas técnicas.

### Slide de presupuesto y coste (obligatoria)

La slide se presenta como si fuera una propuesta económica real al cliente. Debe incluir:

- **Coste unitario por novela:** desglosado en coste de tokens (medido en Langfuse sobre ejecuciones reales), coste de infraestructura y margen operativo.
- **Precio de venta** al cliente final y margen resultante.
- **Coste del proyecto de desarrollo:** estimación en horas de las fases principales (diseño, desarrollo, validación, despliegue) con una tarifa hora y un total.
- **Escenarios de volumen:** tabla o gráfico con el margen para tres volúmenes distintos de novelas vendidas al mes.
- **Análisis de sensibilidad:** qué ocurre si el precio de los tokens sube un 50% o si el cliente pide más de tres revisiones por novela.

Los números deben ser reales o razonados, no inventados: el coste de tokens sale de Langfuse, el resto se estima y se justifica.

### Evidencias obligatorias en la presentación

- La tabla de resultados de las evals, con números.
- El coste real por novela, obtenido de Langfuse, y el margen resultante.
- La demo de un cambio del lector propagado a los capítulos afectados.
