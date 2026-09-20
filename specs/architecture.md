---
spec_version: 1.0.0
fecha: 2026-09-19
deriva_de: "functional.md 1.0.0, technical.md 1.0.0"
caracter: descriptivo
---

# story-maker — Arquitectura en diagramas

Vista visual de lo que [functional.md](functional.md) (§0–§8, §10) y [technical.md](technical.md) (§9) fijan en prosa. **Este documento es descriptivo, no normativo**: si un diagrama y la spec funcional discrepan, gana la spec y el diagrama se corrige. Cada sección enlaza el punto de la spec que la sostiene.

Índice:

1. [Flujo completo de una novela](#1-flujo-completo-de-una-novela) — las tres etapas
2. [Estados de un intento de capítulo](#2-estados-de-un-intento-de-capítulo) — longitud, veredicto, agotamiento
3. [Reanudación](#3-reanudación) — cómo se retoma una carpeta a medias
4. [Paradas y fallos](#4-paradas-y-fallos)
5. [Herramientas fuera del harness](#5-herramientas-fuera-del-harness) — `/optimizar`, `/validar`, observabilidad

---

## 1. Flujo completo de una novela

Spec: §4. Es el mismo diagrama que la spec funcional trae en §4, reproducido aquí para que este documento se lea solo. **Si los dos difieren, el de §4 manda.**

```mermaid
flowchart TD
    idea([Usuario: idea])
    subgraph E1["Etapa 1 — Interrogatorio"]
        preg[Harness entrevista y cierra la Entrevista]
        prop[Interrogador propone biblia + escaleta]
        can{Revisor de continuidad: ¿canon coherente?}
        conf{¿Usuario confirma?}
        preg --> prop --> can
        can -- "no" --> prop
        can -- "sí" --> conf
        conf -- "cambios" --> prop
    end
    subgraph E2["Etapa 2 — Bucle por arco y capítulo, sin intervención humana"]
        arco[Interrogador detalla arco A; harness valida]
        esc[Escritor escribe capítulo N]
        lon{Harness: ¿longitud OK?}
        ajus{¿Quedan ajustes?}
        res[Resumidor: resumen + libro de estado propuesto]
        rev[Dos revisores en paralelo; harness une]
        vered{Veredicto recalculado}
        quedan{¿Quedan reescrituras?}
        agot[Mejor intento + aviso]
        cierra[Cierra capítulo: libro de estado, estado, commit]
        finarco{¿Fin de arco?}
        revarco[Informe de arco]
        mas{¿Quedan capítulos?}
        arco --> esc --> lon
        lon -- "no" --> ajus
        ajus -- "sí" --> esc
        ajus -- "no" --> quedan
        lon -- "sí" --> res --> rev --> vered
        vered -- "RECHAZADO" --> quedan
        quedan -- "sí" --> esc
        quedan -- "no" --> agot --> cierra
        vered -- "APROBADO" --> cierra
        cierra --> finarco
        finarco -- "sí" --> revarco --> mas
        finarco -- "no" --> mas
        mas -- "mismo arco" --> esc
        mas -- "arco nuevo" --> arco
    end
    subgraph E3["Etapa 3 — Final"]
        ens[Ensamblar manuscrito] --> glob[Informe global] --> err[erratas.md]
    end
    idea --> preg
    conf -- "confirma" --> arco
    mas -- "no" --> ens
    err --> fin([Usuario])
```

La etapa 2 **no tiene intervención humana** (§4.2, §9.4): no hay botón de reescribir, aprobar intento ni cambiar la biblia. El usuario solo puede interrumpir; se reanuda desde disco.

---

## 2. Estados de un intento de capítulo

Spec: §4.2 (decisión, mejor intento), §6.3 (límites). Los dos presupuestos —reescrituras y ajustes de longitud— son **independientes**, y ese es el detalle que el diagrama de flujo general no deja ver.

```mermaid
stateDiagram-v2
    [*] --> Escrito: escritor entrega el intento K
    Escrito --> RechazadoLongitud: wc -w fuera de tolerancia
    Escrito --> Resumido: longitud en tolerancia

    RechazadoLongitud --> Escrito: quedan ajustes_longitud,<br/>K+1, no gasta reescritura
    RechazadoLongitud --> SinPresupuesto: ajustes agotados,<br/>la longitud vuelve a gastar reescritura

    Resumido --> Revisado: dos revisores en paralelo
    Revisado --> Aprobado: veredicto recalculado APROBADO
    Revisado --> Rechazado: veredicto recalculado RECHAZADO

    Rechazado --> Escrito: quedan reescrituras,<br/>máx. 2, tres intentos en total
    Rechazado --> SinPresupuesto: reescrituras agotadas

    SinPresupuesto --> MejorIntento: mejor_intento
    MejorIntento --> Cerrado: por_agotamiento true + aviso
    Aprobado --> Cerrado: libro de estado, estado.json, commit

    Cerrado --> [*]

    note right of MejorIntento
        Orden: 1 descartar los rechazados por longitud ·
        2 cumple los hilos_cierra de la escaleta ·
        3 menos problemas de gravedad 1-2 ·
        4 menos problemas en total · 5 el más reciente.
        Resuelto en 4 o 5: aviso "sin criterio fuerte".
        Nunca se pregunta al usuario.
    end note
```

---

## 3. Reanudación

Spec: §6.2. Siempre `/novela continuar <carpeta>`; el punto de retorno sale de `estado.json`, no de la sesión.

```mermaid
stateDiagram-v2
    [*] --> Lee: /novela continuar carpeta
    Lee --> Sucio: git status sucio
    Sucio --> Lee: descartar() copia a .descartado/<br/>y registra paso_descartado

    Lee --> Etapa1: escaleta sin aprobar
    Lee --> Etapa2: en el bucle
    Lee --> Global: bucle terminado, sin informe global
    Lee --> Nada: etapa completa
    Lee --> NoReconocido: estado.json ilegible o versión desconocida

    Etapa1 --> AplicaDecision: tras ESPERA_APROBACION la propuesta<br/>NO se rehace, solo se aplica decision.md
    Etapa2 --> Arco: arco sin escaleta validada, se detalla de nuevo
    Etapa2 --> Intento: intento a medias, se repite con el MISMO número
    NoReconocido --> [*]: PARADA señalando<br/>el último commit consistente
    Nada --> [*]: no hace nada

    note left of Lee
        Tras PAUSA_PROGRAMADA la reanudación
        va en una sesión NUEVA: el harness
        no la encadena.
    end note
```

---

## 4. Paradas y fallos

Spec: §6.5. El principio es que **nunca muere en silencio ni deja el estado a medias**: toda ejecución acaba con informe de cierre.

```mermaid
flowchart TD
    fallo(["Algo va mal"]) --> tipo{"¿Qué ha pasado?"}

    tipo -->|"agente falla, vacío o cortado"| trans["Reintenta hasta reintentos_tecnicos.<br/>En revisión, SOLO el revisor que falló"]
    trans -->|"agotados"| parada
    tipo -->|"forma inesperada o turnos agotados"| incump["Incumplimiento de contrato:<br/>repite indicando qué faltó"]
    incump -->|"se repite entre novelas"| prompt["Es del prompt: va al CHANGELOG"]
    tipo -->|"escaleta fuera de límites"| esc["Devuelve hasta escaleta_rechazos_max"]
    esc -->|"agotados"| parada
    tipo -->|"propuesta lista, sin usuario en la sesión"| espera["ESPERA_APROBACION"]
    tipo -->|"N capítulos cerrados"| pausa["PAUSA_PROGRAMADA"]
    tipo -->|"coste sobre presupuesto_usd_max, hito 2"| parada
    tipo -->|"sin git, falta un fichero, maxTurns distinto de config"| conf["ERROR_CONFIGURACION:<br/>para ANTES de invocar a nadie"]
    tipo -->|"estado.json ilegible"| nore["ESTADO_NO_RECONOCIDO"]
    tipo -->|"commit no creado o carpeta sucia"| cnl["COMMIT_NO_LIMPIO:<br/>para sin avanzar, nada se pierde"]
    tipo -->|"no se pudo copiar a .descartado/"| dns["DESCARTE_NO_SEGURO:<br/>no destruye sin copia"]

    parada["Parada limpia"] --> informe
    espera --> informe
    pausa --> informe
    conf --> informe
    nore --> informe
    cnl --> informe
    dns --> informe

    informe["informe-cierre.md: resultado EXITO o PARADA,<br/>motivo clasificado, etapa/arco/capítulo,<br/>qué quedó hecho, avisos, métricas, volumen<br/>y la acción exacta para continuar"]
    informe --> user(["Usuario: nunca hace falta borrar<br/>nada a mano ni editar el Estado"])
```

---

## 5. Herramientas fuera del harness

Spec: technical.md §9.2–§9.6. Todas comparten estatus: **manuales, borrables, nunca dentro de `/novela`**.

### 5.1 El bucle `/optimizar` (§9.5)

Decide qué prompt usará un agente **la próxima vez**, no si un capítulo se aprueba. Los tres papeles no se mezclan.

```mermaid
flowchart TD
    trig["/optimizar agente --metrica score --vueltas N"] --> req{"Los 5 requisitos de §9.5.1"}
    req -->|"falta uno"| no["No arranca y dice cuál,<br/>antes de gastar una invocación"]
    req -->|"todos"| base["Vuelta 0 obligatoria: mide producción<br/>sobre búsqueda y control,<br/>y guarda produccion.md con su hash"]

    base --> prop["El optimizador propone UNA variante con UNA<br/>operación de la taxonomía cerrada. Lee lecciones.md;<br/>tiene prohibido repetir una variante descartada"]
    prop --> comp{"comprobar_variante.py"}
    comp -->|"copia citas · nombra la métrica · cambia el rol ·<br/>rompe el JSON · toca otro fichero"| abort["ABORTA"]
    comp -->|"limpia"| inst["Instala: cp sobre .claude/agents/agente.md"]
    inst --> corre["Ejecuta el agente sobre búsqueda y control"]
    corre --> punt["puntuar.py en local; publicar<br/>en Langfuse es posterior y fail-open"]
    punt --> dec{"¿Control mejora 0,10 o más<br/>sobre la mejor aceptada?"}
    dec -->|"sí"| acep["Aceptada, línea en vueltas.jsonl"]
    dec -->|"no"| rech["Rechazada, línea en vueltas.jsonl"]
    acep --> stop
    rech --> stop
    stop{"¿Parar?"}
    stop -->|"recall 0,80 o más en control"| cand["Marca candidato"]
    stop -->|"N vueltas hechas"| mejor["Devuelve la mejor probada"]
    stop -->|"tope de invocaciones · 3 vueltas sin mejora ·<br/>restricción dura rota"| abort
    stop -->|"seguir"| prop

    cand --> restaura
    mejor --> restaura
    abort --> restaura
    restaura["<b>Invariante de restauración</b>: siempre devuelve<br/>.claude/agents/agente.md al hash original,<br/>también al abortar y también si falla.<br/>Si no coincide, es PARADA y lo dice"]
    restaura --> usu(["Promover a producción es un commit<br/>que hace el USUARIO. Nada se promueve solo"])
```

Los tres papeles, que **nunca se mezclan**:

```mermaid
flowchart LR
    o1["<b>Optimizado</b><br/>el agente cuyo prompt cambia<br/>No hace nada: se le ejecuta"]
    o2["<b>Juez</b><br/>evaluador + conjunto etiquetado<br/>Puntúa contra verdad de campo, no opina.<br/>Congelado toda la ejecución"]
    o3["<b>Optimizador</b><br/>propone variantes<br/>NUNCA puntúa y NUNCA ve el conjunto:<br/>lo corta permissions.deny sobre Read,<br/>y con él cat, head y las redirecciones de Bash"]
    o3 -->|"variante"| o1
    o1 -->|"salidas"| o2
    o2 -->|"solo el score de búsqueda"| o3
```

**La decisión de aceptar se toma siempre en control**; búsqueda solo alimenta al optimizador. El `split` se fija por caso y no por defecto: si dos defectos del mismo capítulo cayeran en lados distintos, el optimizador habría visto en búsqueda el mismo texto con el que se decide en control.

### 5.2 El validador `/validar` (§9.6)

No es un bucle: mide una vez y devuelve un número reproducible **sobre el texto**, no sobre lo que los revisores declararon.

```mermaid
flowchart LR
    v["/validar carpeta"] --> pre{"3 precondiciones"}
    pre -->|"la carpeta pasa §8.7 ·<br/>detector congelado ·<br/>escala congelada"| mide
    pre -->|"falta una"| nomide["No mide y dice cuál"]
    mide["patrones.py sobre manuscrito.md"] --> dims
    subgraph dims["Dos dimensiones, por mil palabras"]
        l["lengua · tope 2,0/mil · peso 0,87"]
        r["repeticion · 6-gramas compartidos entre<br/>pares de capítulos · tope 16,0/mil · peso 0,13"]
    end
    dims --> glob["Índice global 0 a 1, 1 = mejor"]
    glob --> delta["Delta contra validaciones/_base.json"]
    delta --> out["validaciones/slug/score.json e informe.md"]
    out -.->|"posterior y fail-open"| lf["Langfuse"]
```

Con `n=1` por configuración no se puede separar el efecto de la config del azar de esa generación: el informe lo escribe siempre y **ninguna mejora se declara establecida**.

### 5.3 Proceso frente a producto

§8.3 y §9.6 conviven con nombres distintos, y esa distinción es la razón de ser de `/validar`.

```mermaid
flowchart TB
    e5["E5(c): el sistema se corrige a sí mismo los exámenes.<br/>erratas.md decía total: 0 sobre un manuscrito<br/>con 13 agramaticalidades contadas a mano"]
    proc["<b>§8.3 — métricas de PROCESO</b>, autoinformadas<br/>Las calcula el harness a partir de lo que los revisores<br/>dijeron. Ven agotamientos, reintentos, intentos por capítulo"]
    prod["<b>§9.6 — métricas de PRODUCTO</b>, medidas<br/>Las mide un detector sobre el texto.<br/>Ven lo que ningún revisor declaró"]
    e5 --> prod
    proc -.->|"cuando discrepen, decide el usuario.<br/>Ninguna se retira"| prod
```

### 5.4 Observabilidad: por qué nunca bloquea

Spec: technical.md §9.3. Las seis reglas en una imagen.

```mermaid
flowchart LR
    inv["invocar() del harness"] -->|"NUNCA un curl aquí"| x(("regla 2:<br/>nunca puerta<br/>del flujo"))
    inv --> reg["registro.md<br><b>regla 1: la fuente de verdad</b>"]
    reg -->|"a mano, después"| exp["herramientas/trazas/exportar.py"]
    exp -->|"regla 3: fail-open"| lfz["Langfuse"]
    lfz -.->|"regla 4: no escribe en novelas/"| nov[("novelas/")]
    cred[".env y settings.local.json<br/>reglas 5 y 6: fuera de git<br/>y con deny de Read"] --> exp

    classDef prohibido stroke:#c00,stroke-dasharray: 4 3
    class x,nov prohibido
```

---

## Cómo mantener este documento

- Cada diagrama lleva el `§` de la spec que lo sostiene. Si cambias la spec, busca aquí ese `§`.
- El diagrama de la sección 1 es **copia** del de functional.md §4: se actualizan a la vez, o se borra de aquí.
- Este fichero no introduce reglas nuevas. Si al dibujar aparece una decisión que la spec no tiene, va a la spec primero (§10.4: «si algo no funciona en ella, se cambia aquí primero»).
