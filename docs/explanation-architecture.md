# explanation-architecture.md

**Documento derivado, no autoridad.** Es una explicación simplificada de `architecture.md` para entender el proyecto de un vistazo, escrita para alguien que abre el repositorio por primera vez. No introduce términos ni decisiones nuevas: si algo de aquí contradice a `architecture.md`, `definitions.md` o `verification.md`, mandan ellos.

Cada término del dominio se explica en una frase la primera vez que aparece. La definición formal está siempre en `definitions.md`.

---

## 1. Qué hace el sistema

Le das **un prompt en texto libre y un fichero de configuración**. Te devuelve **una novela completa en español** sobre el mundo posterior a la revolución de la IA, más un **informe de ejecución**: qué decidió, qué cumplió y qué no pudo resolver.

No hay preguntas por el camino. La ejecución es autónoma de principio a fin: nadie revisa nada a mitad.

```mermaid
graph LR
    P[Prompt en texto libre] --> SYS
    C[config.json<br/>capitulos, tono, modelo, presupuesto] --> SYS
    SYS[Story Maker<br/>ejecucion autonoma] --> M[Manuscrito en markdown]
    SYS --> I[Informe de ejecucion]
```

Tres apuestas sostienen todo lo demás:

| Apuesta | En una frase |
|---|---|
| **Outline primero** | Se planifica la obra entera antes de escribir una línea y ese plan se congela. Es lo que evita que la novela se vaya desviando. |
| **Memoria selectiva** | Ninguna llamada al modelo recibe «todo el contexto»: recibe una ventana armada a propósito para ella. |
| **Puertas de calidad** | Ninguna escena entra en el canon sin pasar filtros, ordenados de más barato a más caro. |

> **Canon:** el conjunto de lo que ya es verdad dentro de la ficción. Una vez algo entra en el canon, el resto de la novela no puede contradecirlo.

---

## 2. Las cuatro fases de una ejecución

Toda ejecución recorre siempre el mismo camino.

```mermaid
graph TD
    F0[Fase 0 - Entender<br/>el prompt libre se convierte<br/>en un contrato explicito]
    F1[Fase 1 - Inventar el mundo<br/>novum, restricciones<br/>y sus consecuencias]
    F2[Fase 2 - Planificar<br/>outline de toda la obra,<br/>luego se congela]
    F3[Fase 3 - Escribir<br/>escena a escena, en orden]
    F4[Fase 4 - Pase global<br/>defectos que ninguna<br/>escena ve por si sola]
    OUT[Manuscrito + informe]

    F0 --> F1 --> F2 --> F3 --> F4 --> OUT
```

**Fase 0 — Entender.** Tu prosa se convierte en un **ContratoDeBrief**: la lista de lo que has pedido de verdad. Se parte en dos:

- **Compromisos** — lo que el sistema está obligado a cumplir.
- **Huecos** — lo que dejas libre y el sistema decidirá por su cuenta.

Ante la duda, Hueco. Un compromiso inventado restringe la obra entera; un hueco solo la deja abierta.

**Fase 1 — Inventar el mundo.** El arquitecto propone varios **novum** candidatos —el postulado especulativo raíz, lo que separa este mundo del real— y un selector elige uno puntuando tres ejes: cuántas consecuencias admite, cuánto encaja con el contrato y cuánto se aleja del catálogo de tópicos del género. Del novum elegido se derivan consecuencias encadenadas: eso es el canon inicial.

**Fase 2 — Planificar.** Se escribe el **outline**, el plan jerárquico de capítulos y escenas. Se comprueba que los elementos comprometidos aparecen lo suficiente y que ningún compromiso se ha quedado fuera; entonces la estructura se congela.

**Fase 3 — Escribir.** El bucle por escena (sección 5). Es secuencial, porque cada escena depende del estado que deja la anterior.

**Fase 4 — Pase global.** Cuatro comprobaciones sobre la obra entera (sección 6). Lo que encuentran se arregla reescribiendo escenas concretas, nunca regenerando la novela.

---

## 3. Quién hace cada cosa

No todo paso es un agente. Solo lo es lo que necesita explorar, consultar y decidir en varios pasos. El resto es código normal o una llamada de modelo de un solo paso, que es más barato y más predecible.

```mermaid
graph TD
    subgraph AG[4 agentes - exploran y deciden en varios pasos]
        A1[Arquitecto de mundo - fase 1]
        A2[Planificador - fase 2]
        A3[Escritor - fase 3]
        A4[Editor - fase 3]
    end
    subgraph MO[9 llamadas de modelo de un solo paso]
        M1[Extractor y verificador de brief - fase 0]
        M2[Auditor de topicos - fases 1 y 3]
        M3[Critico de canon y critico de oficio - fase 3]
        M4[Registrador de estado - fase 3]
        M5[Tres jueces del pase global - fase 4]
    end
    subgraph CO[9 componentes de codigo - sin modelo]
        C1[Orquestador y validador de config]
        C2[Ensamblador de contexto y recuperador]
        C3[Puerta dura y selector de novum]
        C4[Comprobador estructurado de obra]
        C5[Redactor del informe]
    end
```

Dos reglas de reparto que explican el resto del diseño:

- **Quien escribe no se evalúa a sí mismo.** Un agente que critica su propio texto ya tiene el contexto que justificó sus decisiones, así que se da la razón.
- **Quien critica no corrige.** Los críticos devuelven defectos tipados; corregir es trabajo del editor. Separarlos permite medir por separado si la detección funciona.

---

## 4. Memoria y contexto

El problema de fondo: una novela entera no cabe en la ventana de un modelo. La solución no es una ventana mayor, es **decidir qué entra en cada llamada**.

Hay dos memorias, y se distinguen por **cómo llegan a una llamada**.

```mermaid
graph LR
    subgraph CP[MemoriaDeCortoPlazo - entra siempre, sin consulta]
        R1[Proyeccion del outline]
        R2[EstadoDelMundo]
        R3[ResumenRodante]
        R4[StyleSheet]
        R5[Compromisos inviolables]
        R6[Catalogo de topicos]
    end

    subgraph LP[MemoriaDeLargoPlazo - solo por consulta]
        L1[CanonCards]
        L2[Resumenes de escena]
        L3[Prosa por parrafo]
    end

    CP -->|entra entera| V
    LP -->|plazas fijas por<br/>coleccion y consumidor| V
    V[VentanaDeContexto<br/>de UNA llamada concreta] --> LL[Agente o critico]
    LL --> T[Trazabilidad:<br/>que justifico cada frase]
```

Qué es cada pieza residente:

- **Proyección del outline** — no el outline entero, sino los títulos de toda la obra, las escenas del capítulo actual y la lista de lo que aún no puede revelarse. Así el tamaño de la ventana deja de depender del tamaño de la novela.
- **EstadoDelMundo** — foto mutable de la situación, versionada escena a escena.
- **ResumenRodante** — comprimido de lo ya narrado más las últimas escenas en literal.
- **StyleSheet** — voz, registro, léxico prohibido, disciplina de punto de vista.

### 4.1 Cómo se recupera de la memoria de largo plazo

La memoria de largo plazo es un índice que **nace vacío y crece con el canon aceptado de la propia ejecución**. No es un almacén único: son tres colecciones separadas, cada una con su unidad y su cliente.

```mermaid
graph TD
    Q[Consulta de UN consumidor] --> F{Filtro temporal<br/>desde escena / hasta escena}
    F --> CC[CanonCards<br/>unidad: tarjeta de entidad]
    F --> RS[Resumenes<br/>unidad: una escena]
    F --> PR[Prosa<br/>unidad: el parrafo]

    CC -->|lexico + denso<br/>+ arrastre por el grafo causal| N1[Plazas fijas]
    RS -->|lexico + denso<br/>+ escena anterior y siguiente| N2[Plazas fijas]
    PR -->|solo lexico| N3[Plazas fijas]

    N1 --> W[VentanaDeContexto]
    N2 --> W
    N3 --> W
```

Las reglas que importan, y por qué:

- **Corte temporal.** Las `CanonCard` son inmutables y llevan desde qué escena y hasta qué escena son válidas. Al evaluar la escena 12 nadie ve la verdad de la escena 60; si no, el crítico inventa contradicciones que aún no existían.
- **Plazas fijas por par (colección, consumidor), sin préstamos.** La ventana deja de ser un montón y pasa a ser una tabla legible, y cada celda se puede probar por separado.
- **La prosa solo la ve el crítico de oficio.** Si el escritor leyera prosa lejana la imitaría, y eso empeoraría justo el defecto que la fase 4 existe para detectar.
- **Consultas distintas para escritor y crítico.** El escritor consulta mirando hacia delante, desde el outline de la escena que va a escribir; el crítico de canon consulta hacia atrás, desde el texto ya escrito. Con una consulta compartida ambos tendrían el mismo punto ciego.
- **Nada de reordenar con un modelo.** Renunciar a eso es lo que permite probar la recuperación entera sin llamar a ningún modelo: la misma escena siempre produce la misma ventana.
- **Si no cabe, se recorta y se sigue.** El orden es declarado, no calculado: `prosa → resúmenes → CanonCards → ResumenRodante`. Queda anotado en el informe; nunca bloquea.

### 4.2 Quién decide cuánto cabe

El presupuesto de ventana lo hace cumplir **el orquestador, que es código, nunca el modelo**.

```mermaid
graph LR
    E[Se abre una etapa:<br/>3 criticos en paralelo] --> D[Techo de 100k tokens<br/>de ENTRADA por etapa]
    D --> Q[33k de cuota<br/>para cada uno]
    Q --> A[Ensamblador:<br/>residentes + recuperado]
    A --> R{Cabe?}
    R -->|si| LL[Llamada con la<br/>ventana ya cerrada]
    R -->|no| RE[Recortar por el<br/>orden declarado]
    RE --> LL
```

Tres matices que se confunden con facilidad:

- El techo es **por etapa de llamadas simultáneas, no por llamada**. Tres críticos a la vez se reparten los 100k.
- **Cuenta solo la entrada.** La salida no tiene techo en tokens: no se puede acotar antes de generarla. Lo único que la controla es el presupuesto en dinero.
- Lo que no cabe **se niega antes de construir el prompt**. El agente nunca razona sobre contexto que luego no va a ver.

---

## 5. Las puertas de calidad y el bucle por escena

Cuatro puertas, ordenadas de más barato a más caro. Una escena que falla lo barato no gasta presupuesto en lo caro.

```mermaid
graph LR
    G0[Puerta 0 - Factibilidad<br/>una sola vez, sobre el outline] --> G1
    G1[Puerta 1 - Dura<br/>codigo] --> G2[Puerta 2 - Canon<br/>recuperacion + modelo]
    G2 --> G3[Puerta 3 - Juicio<br/>modelo con rubrica]

    G0 -.detecta.-> D0[config incoherente,<br/>compromiso sin cobertura]
    G1 -.detecta.-> D1[restriccion violada,<br/>contradiccion temporal]
    G2 -.detecta.-> D2[incoherencia con<br/>el grafo causal]
    G3 -.detecta.-> D3[prosa, ritmo, punto de vista,<br/>cliche, infodump]
```

Las puertas 2 y 3 no son pasos aparte del bucle: **son los críticos**. Así se ve:

```mermaid
graph TD
    ENS[Ensamblador de contexto] --> ESC[Escritor]
    ESC --> P1{Puerta 1 - Dura}
    P1 -->|falla| ED[Editor]
    P1 -->|pasa| CRI[Tres criticos en paralelo]

    CRI --> C1[Critico de canon<br/>= puerta 2]
    CRI --> C2[Critico de oficio<br/>= puerta 3]
    CRI --> C3[Auditor de topicos<br/>= puerta 3]

    C1 --> AGR{Defectos?}
    C2 --> AGR
    C3 --> AGR

    AGR -->|ninguno| REG[Registrador de estado]
    AGR -->|corregible| ED
    AGR -->|estructural| ESC
    ED --> P1

    REG --> UPD[Canon, estado, resumen e indice<br/>se actualizan en UNA transaccion]
    UPD --> SIG[Siguiente escena]
```

Cuatro ideas dentro de este diagrama:

1. **El enrutado va por naturaleza del defecto**, no por la puerta que lo encontró: lo corregible al editor, lo estructural de vuelta al escritor.
2. **Solo el registrador escribe en canon**, y solo después de aceptar la escena. Así una escena rechazada no contamina el estado.
3. **El estado se extrae, no se asume.** El escritor declara el cambio que pretendía; el registrador lee el texto aceptado y extrae el cambio real. Si difieren, es un defecto.
4. **Canon e índice se escriben juntos**, en la misma transacción. Nunca existe un instante en el que discrepen, y por eso se puede reanudar desde un punto de control sin reconstruir nada.

### Los tres techos

| Techo | Se mide en | Al agotarse |
|---|---|---|
| **Ventana** | tokens de **entrada** de las llamadas simultáneas de una etapa | recorta y sigue |
| **Reintentos por escena** | intentos | escala y lo deja anotado en el informe |
| **Ejecución** | **dinero** | bloquea |

El presupuesto de la obra se mide en dinero y no en tokens porque un token de indexación y uno de generación se diferencian en órdenes de magnitud de coste; el dinero es la única unidad en la que ambos son comparables.

---

## 6. El pase global

Hay defectos que no existen a escala de escena: el ritmo de la obra, un hilo que se abre y nunca se cierra, la misma imagen repetida en las escenas 8 y 74, la voz que se desvía del principio al final.

El manuscrito completo no cabe en la ventana, así que el pase global **no es un agente que lea la novela entera**. Se descompone por tipo de defecto, y de los cinco solo uno necesita recuperación.

```mermaid
graph TD
    OBRA[Obra completa] --> CE[Comprobador estructurado<br/>consultas, sin modelo]
    OBRA --> J1[Juez de curva de tension]
    OBRA --> J2[Detector de deriva de voz]
    OBRA --> J3[Detector de repeticion lexica]

    CE --> D1[Hilos abiertos sin cerrar]
    CE --> D2[Consecuencias establecidas<br/>y nunca usadas]
    J1 --> D3[Ritmo de la obra]
    J2 --> D4[La voz del ultimo tercio<br/>no es la del primero]
    J3 --> D5[Imagenes repetidas<br/>entre escenas lejanas]

    D1 --> RW[Reescritura dirigida<br/>de escenas concretas]
    D2 --> RW
    D3 --> RW
    D4 --> RW
    D5 --> RW
```

Los dos primeros son consultas exactas a la base de datos, no problemas de similitud: un hilo abierto es un arco cuyo estado sigue abierto, y una consecuencia sin usar es una fila sin ninguna referencia de trazabilidad.

---

## 7. Cómo se ejecuta por fuera

Una novela son decenas o cientos de escenas; el tiempo total se mide en minutos u horas. No cabe en una petición HTTP.

```mermaid
graph LR
    FE[Frontend] -->|POST /runs| API[FastAPI]
    API -->|run_id| FE
    API --> W[Worker aparte]
    W --> DB[(SQLite: canon + indice<br/>+ punto de control por escena)]
    W -->|eventos de progreso SSE| FE
    FE -->|GET manuscrito / informe| API
```

- El progreso **se transmite, no se espera**: eventos en vivo desde el servidor.
- Hay **punto de control por escena**. Si el proceso cae en la escena 80, se reanuda desde ahí.
- El frontend **no debe dar por buena una escena mostrada durante el progreso**: el pase global puede reescribirla. Solo el manuscrito final es definitivo.

---

## 8. Dónde está el proyecto ahora

El trabajo recorre siempre cinco capas en este orden, y nunca se salta hacia arriba.

```mermaid
graph LR
    D["docs/*.md<br/>HECHO"] --> S["spec.md<br/>11 sin aprobar"]
    S --> P["plan.md<br/>11 sin aprobar"]
    P --> T[tests<br/>no existen]
    T --> C["backend/ y frontend/<br/>vacios"]
```

Qué dice cada capa:

- **`docs/`** — qué es verdad del dominio y por qué el diseño es así. Es la autoridad.
- **`spec.md`** — qué comportamiento observable tiene una feature: requisitos comprobables, cada uno con su clase de verificación. Una carpeta por feature en `specs/`, con su `plan.md` al lado.
- **`plan.md`** — el plan de esa spec: un paso por requisito, en orden de implementación.
- **tests y código** — se escriben test primero, caso a caso.

Ahora mismo **solo la primera capa está hecha**; las specs del backend V1 y sus planes (`001-base` a `011-out-salidas`) están escritos y sin aprobar. Lo siguiente, en orden:

1. **Aprobar cada spec y su plan**, empezando por `001-base`.
2. **Orquestación del trabajo** — estados, reanudación desde punto de control, cancelación y reparto del presupuesto en dinero. Es la pieza de diseño que falta (`architecture.md` §12.1).
3. **Código por TDD** desde esas specs. Ninguna carpeta se crea hasta que una spec la exija.
