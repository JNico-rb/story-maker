# Matriz de Relación

Parte A — qué parte de [docs/architecture.md](docs/architecture.md) se implementa en qué spec de [specs/](specs/), y con qué requisitos.
Parte B — cómo se comprueba la cobertura requisito → paso.

Documento derivado: no es fuente de verdad ni layer del workflow de `AGENTS.md`. Se regenera
cuando cambie cualquiera de los ficheros que relaciona. Regenerada el 2026-09-23, al migrar a
`specs/NNN-slug/`.

**Estados**

| Estado | Significado |
|---|---|
| **Cubierto** | Todo lo que decide la sección tiene paso en algún plan |
| **Parcial** | Parte tiene paso y parte no; la columna dice cuál |
| **Sin paso** | Criterio de diseño o riesgo asumido: se aplica al implementar, no se verifica como caso |
| **Fuera de V1** | Declarado en el «Fuera de alcance» de su spec |
| **Contradicción** | El documento afirma algo que el repositorio no sostiene |

**Specs**: 001 BASE · 002 CFG · 003 RUN · 004 MEM · 005 BRF · 006 WLD · 007 PLN · 008 SCN · 009 GLB · 010 BUD · 011 OUT.

---

## A1. De `architecture.md` a las specs

### §1 — Separación en capas

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 1.1 | Tres ontologías: storyworld, artefacto narrativo, sistema de generación; la calidad son predicados sobre A y B | 001 — separación `domain` / `phases` / `platform` | Parcial — informa la estructura; ningún paso lo verifica |
| 1.2 | Tres fuentes de restricción y el test de frontera prompt/config | 002 (RF-CFG-2) · 005 (RF-BRF-7, promoción de poéticos a `Compromiso`) | Cubierto |

### §2 — Extracción del ContratoDeBrief

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 2 | Extracción no fiable al 100 %; verificador de ida y vuelta; compromisos no verificables; huecos de un solo uso | 005 completa (RF-BRF-1 a RF-BRF-8) · 008 (RF-SCN-18, el hueco resuelto pasa a canon) | Cubierto |

### §3 — Gestión de contexto y memoria

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 3.1 | Patrón outline-first + recuperación selectiva + validación de deltas; activos de primera clase | 004 (RF-MEM-9 residentes, RF-MEM-43 trazabilidad) | Cubierto |
| 3.2 | RAG híbrido dinámico **sin re-ranking** | 004 (RF-MEM-20 canal doble, RF-MEM-22 sin re-ranking) | Cubierto |
| 3.3 | Colecciones, no un pozo; RRF confinado dentro de cada colección | 004 (RF-MEM-19) | Cubierto |
| 3.4 | Las tres colecciones: unidad, consumidor y modo de cada una | 004 (RF-MEM-5, RF-MEM-20, RF-MEM-21, RF-MEM-31) | Cubierto |
| 3.5 | Residentes nunca indexados; proyección del outline; catálogo de tropos fuera del índice por calidad | 004 (RF-MEM-9 a RF-MEM-13) | Cubierto — la aritmética de tokens de la tabla es justificación, no requisito |
| 3.6 | Cuota fija por (colección, consumidor); sin préstamo; validación al crear la ejecución | 002 (RF-CFG-3 a RF-CFG-9) · 004 (RF-MEM-28, RF-MEM-29, RF-MEM-30) | Cubierto |
| 3.7 | Corte temporal; `CanonCard` inmutables; índice append-only | 004 (RF-MEM-4, RF-MEM-8, RF-MEM-18) | Cubierto |
| 3.8 | Arrastre por el grafo y arrastre temporal | 004 (RF-MEM-24, RF-MEM-25, RF-MEM-26) | Cubierto |
| 3.9 | Doble consulta: prospectiva del escritor, retrospectiva del crítico de canon | 004 (RF-MEM-15, RF-MEM-16, RF-MEM-17) | Cubierto |
| 3.10 | La escasez no bloquea; causa raíz `contexto ausente` | 004 (RF-MEM-14, RF-MEM-27) · 011 (RF-OUT-5) | Cubierto |
| 3.11 | Vectores congelados, desempate estable, recuperador en clase T | 002 (RF-CFG-13) · 004 (RF-MEM-6, RF-MEM-23, RNF-1, RNF-2) | Cubierto |
| 3.12 | Un escritor de índice por fase, siempre en la transacción del canon | 004 (RF-MEM-2, RF-MEM-3, RF-MEM-7) · 006 (RF-WLD-8) · 008 (RF-SCN-14) | Cubierto |
| 3.13 | Techo de ventana: solo entrada, por etapa; intocables; orden de recorte declarado | 004 (RF-MEM-35, RF-MEM-36, RF-MEM-37, RF-MEM-38) · 010 (RF-BUD-2, RF-BUD-3) | Cubierto |
| 3.14 | `sqlite-vec` + FTS5 en el mismo fichero; `fastembed` con las dos condiciones de Windows | 001 (R5, RNF-11, R9, RNF-13) | Cubierto |
| 3.15 | Cuota por etapa = techo ÷ llamadas en vuelo; guardián invocado por código; conteo y reconciliación | 004 (RF-MEM-33, RF-MEM-34, RF-MEM-39, RF-MEM-40, RF-MEM-41) | Cubierto — RF-MEM-41 marcado *deseable* |

### §4 — Marco de calidad

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 4.1 | Las cuatro puertas y su orden económico; la puerta 0 fuera del bucle | 007 (RF-PLN-3 a RF-PLN-7) · 008 (RF-SCN-3, RF-SCN-5) | Cubierto |
| 4.2 | `Criterio` → `Evaluador` → `Evaluable` → `Defecto` → `Veredicto`; **todo Evaluador declara su fiabilidad conocida**; todo Defecto registra causa raíz | 002 (RF-CFG-15) · 008 (RF-SCN-6, RF-SCN-8, RF-SCN-12) | **Parcial** — la fiabilidad declarada del Evaluador **no tiene paso**; ver A3.1 |

### §5 — Configuración

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 5.1 | Cuatro familias y sus ciclos de vida distintos | 002 (RF-CFG-2, RF-CFG-11, RF-CFG-12, RF-CFG-13) | Cubierto |
| 5.2 | Seis reglas: no sobredeterminar, precedencia declarada, inmutabilidad post-outline, criterios desde config, `calidad` y `recuperacion` no editables | 002 (RF-CFG-2, RF-CFG-3-9, 10, 11, 13) · 011 (RF-OUT-6) | Cubierto |

### §6 — Precedencia y conflictos

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 6.1 | config gana en lo estructural, el prompt en lo narrativo; nada en silencio | 011 (RF-OUT-6) | Cubierto |
| 6.2 | Los dos imposibles: aritmético en la entrada, densidad en la puerta 0 | 002 (RF-CFG-1) · 003 (RF-RUN-7) · 007 (RF-PLN-4) | Cubierto |
| 6.3 | Fórmula de densidad; solo elementos comprometidos; techo de invención al arquitecto | 007 (RF-PLN-3, RF-PLN-4, RF-PLN-6) · 006 (RF-WLD-1) | Cubierto |

### §7 — Invariantes

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 7 | Los ocho invariantes y dónde se comprueba cada uno | 1: RF-WLD-6 · 2: RF-SCN-18 · 3 y 4: RF-SCN-3, RF-SCN-4 · 5: RF-SCN-17 · 6: RF-SCN-14 · 7: RF-MEM-8 · 8: RF-MEM-43 | Cubierto |
| 7.1 | Partición de los invariantes 3 y 4 en predicado determinista y semántico | 008 (RF-SCN-3, RF-SCN-4) | Cubierto |
| 7.2 | El arrastre refuerza el invariante 1; el corte temporal refuerza el 5 | 004 (RF-MEM-24, RF-MEM-18) | Cubierto |

### §8 — Sistema de agentes

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 8.1 | Autonomía total, entrada mínima, generación secuencial | 008 (RF-SCN-1, R3) · 003 (R1, R2) | Cubierto — la autonomía es ausencia de pantallas, no un paso |
| 8.2 | Principio de asignación: 9 de código, 9 de modelo en un paso, 4 agentes | — | **Sin paso** — criterio que se aplica al implementar cada spec |
| 8.3 | Los cuatro agentes y el modo «reutilizar canon» | 006 (RF-WLD-1, RF-WLD-2, RF-WLD-9) · 007 (RF-PLN-1) · 008 (RF-SCN-2, RF-SCN-10, RF-SCN-11) | Cubierto |
| 8.4 | Las nueve llamadas de modelo en un paso | 005 (RF-BRF-1, RF-BRF-3) · 006 (RF-WLD-3) · 008 (RF-SCN-5, RF-SCN-6, RF-SCN-13) · 009 (RF-GLB-4, RF-GLB-5, RF-GLB-6) | Cubierto |
| 8.5 | Los nueve componentes de código | 002 · 004 (recuperador) · 006 (RF-WLD-4 selector) · 008 (RF-SCN-3 puerta dura, RF-SCN-17 aplicador) · 009 (RF-GLB-2, RF-GLB-3 comprobador) · 011 (RF-OUT-2 redactor) | Cubierto |
| 8.6 | Flujo por fases, encadenado por artefacto persistido | Orden 005 → 006 → 007 → 008 → 009 · 003 (RF-RUN-3) | Cubierto |
| 8.7 | Bucle por escena; correspondencia puerta ↔ crítico; regla única de enrutado | 008 (RF-SCN-1 a RF-SCN-14) | Cubierto |
| 8.8 | Las seis reglas de interacción | 008 (RF-SCN-7, RF-SCN-6, RF-SCN-5, RF-SCN-13, RF-SCN-12, RF-SCN-16) | Cubierto |
| 8.9 | Pase global descompuesto en cuatro comprobaciones por tipo de defecto | 009 completa (RF-GLB-1 a RF-GLB-8) | Cubierto |
| 8.10 | Los cuatro sustitutos de la supervisión humana | 005 (RF-BRF-3, RF-BRF-4, RF-BRF-5) · 006 (RF-WLD-2, RF-WLD-4, RF-WLD-5) · 007 (RF-PLN-3, RF-PLN-5) · 011 (RF-OUT-2) | Cubierto |
| 8.11 | Prompt casi vacío: el caso más frecuente, probado desde el día uno | 005 (RF-BRF-8) · 007 (RF-PLN-6) · 011 (demo de extremo a extremo) | Cubierto |
| 8.12 | Tres techos: ventana recorta, reintentos escalan, dinero bloquea | 010 completa (RF-BUD-1 a RF-BUD-5) | Cubierto |

### §9 — Stack e implicaciones

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 9.1 | Elección de stack: backend, persistencia, frontend, salida | 001 · 011 (RF-OUT-1) | **Parcial** — la fila del frontend queda **fuera de V1** |
| 9.2 | Slice por fase, `domain` y `platform`, regla de dependencia, proyección de nombres, FSD del frontend | 001 (estructura de §9.2 y CI de dependencias) | **Parcial** — FSD del frontend **fuera de V1** |
| 9.3 | Trabajo asíncrono, SSE, punto de control por escena | 003 (RF-RUN-1, RF-RUN-2, RF-RUN-4, RF-RUN-5, RNF-3, RNF-4) | Cubierto |
| 9.4 | Contrato de API mínimo; dónde va cada tipo de error | 003 (RF-RUN-1, RF-RUN-3, RF-RUN-4, RF-RUN-6, RF-RUN-7) · 011 (RF-OUT-1, RF-OUT-2) · 001 (RNF-15) | Cubierto |
| 9.5 | Biblioteca de canon sin vectores; tiempos por agente; el parcial no es verdad cacheable | 006 (RF-WLD-9, RF-WLD-10) · 003 (RF-RUN-8) · 011 (RF-OUT-7) | Cubierto |

### §10 a §12 — Abierto, cerrado y pendiente

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 10.2 | Siete cifras declaradas sin valor, el método para calibrarlas y la regla de leerlas de config | Regla de lectura en §10.2 y en `workflow/3-plan.md`; cada cifra la consume su spec | **Parcial** — calibrarlas está **fuera de V1** (002) |
| 10.3 | Fragilidad del verificador de contrato | — | **Sin paso** — riesgo asumido, no tarea |
| 11 | Registro de decisiones cerradas | Transversal: cada fila apunta a la sección que la implementa | Registro, no fuente de pasos |
| 12.1 | Orquestación del trabajo — **sin escribir**: estados, reanudación automática, cancelación que conserva | 003 (RF-RUN-9 estados, RF-RUN-5 punto de control, RF-RUN-6 cancelar) | **Parcial** — reanudación automática, techo de reanudaciones y promoción de canon al cancelar quedan **fuera de V1** (003, 006) |
| 12.3 | Revisar si la puerta 0 se parte en dos | 007 (RF-PLN-7) implementa la posición actual | **Parcial** — si se parte, arrastra RF-PLN-3 y RF-PLN-7 |
| 12.4 | Dónde se registra la deuda de spec | — | **Sin paso** — sin decidir |

---

## A2. De las specs a `architecture.md`

Lectura inversa: qué secciones del documento consume cada spec.

| Spec | Pasos | Secciones de `architecture.md` que consume |
|---|---|---|
| 001 BASE | 12 | §3.14, §9.1, §9.2 |
| 002 CFG | 14 | §1.2, §3.6, §3.11, §5.1, §5.2, §6.2 |
| 003 RUN | 11 | §6.2, §8.1, §9.3, §9.4, §9.5, §12.1 |
| 004 MEM | 45 | §3.1 a §3.13, §3.15, §7.2 |
| 005 BRF | 8 | §1.2, §2, §8.4, §8.10, §8.11 |
| 006 WLD | 11 | §3.12, §6.3, §8.3, §8.4, §8.5, §8.10, §9.5 |
| 007 PLN | 8 | §4.1, §6.2, §6.3, §8.3, §8.10, §8.11, §12.3 |
| 008 SCN | 18 | §2, §3.12, §4.1, §4.2, §7, §7.1, §8.1, §8.3, §8.4, §8.5, §8.7, §8.8 |
| 009 GLB | 8 | §8.4, §8.5, §8.9 |
| 010 BUD | 6 | §3.13, §8.12 |
| 011 OUT | 8 | §3.10, §6.1, §8.5, §8.10, §8.11, §9.1, §9.4, §9.5 |

**§3 es el eje.** Trece de sus quince subsecciones alimentan 004 MEM, que concentra 45 de los 149 pasos.

---

## A3. Lo que `architecture.md` decide y ningún plan implementa

### A3.1 Hueco real — sin paso y sin justificación

| Qué | Origen | Por qué importa |
|---|---|---|
| **Todo `Evaluador` declara su fiabilidad conocida** | §4.2, regla de diseño | Ninguna `spec.md` ni ningún `plan.md` menciona «Evaluador» ni «fiabilidad». Es la regla que separa un juez calibrado de «ruido con formato de métrica», y hoy ningún paso la entrega. §10.2 da el método de calibración, pero calibrar está fuera de V1 y *declarar* la fiabilidad no lo está. Cerrarlo es un cambio de spec (proceso 2), no de esta matriz |

### A3.2 Fuera de V1

| Qué | Origen | Declarado en |
|---|---|---|
| Frontend completo: stack, FSD v2.1, `app`/`pages`/`shared`, cliente generado | §9.1, §9.2 | 001 |
| Reanudación automática desde punto de control y techo de reanudaciones | §9.3, §10.2, §12.1 | 003 |
| Promoción del canon a la biblioteca **al cancelar** | §12.1 — promover al terminar bien sí entra, RF-WLD-11 | 006 |
| Calibración de las siete cifras sin valor | §10.2 | 002 |
| Formatos de salida distintos de Markdown | §11 | 011 |
| Re-ranking y expansión de consulta | §3.2, §11 | 004 |

### A3.3 Sin paso por naturaleza

| Qué | Origen | Por qué no es un caso |
|---|---|---|
| Tres ontologías | §1.1 | Criterio de modelado; se manifiesta en la estructura de módulos |
| Reparto 9 código / 9 modelo / 4 agentes | §8.2 | Criterio de asignación al implementar cada componente |
| Fragilidad del verificador de contrato | §10.3 | Riesgo asumido con mitigaciones parciales, no tarea |
| Decisiones cerradas | §11 | Registro |
| Deuda de spec | §12.4 | Sin decidir |
| Autonomía total y entrada mínima (R1, R2) | §8.1 | Ausencia de superficie; `POST /runs` materializa la entrada mínima (RF-RUN-1) |

### A3.4 A revisar — lo que la antigua §12.2 dejaba sin spec

§12.2 se retiró al dar a la memoria su spec propia (004). Listaba como «todavía sin spec» cuatro cosas; así quedan:

| Qué | Estado |
|---|---|
| Reconciliación del conteo con el uso del proveedor (§3.15) | Cubierto — RF-MEM-41 (004, *deseable*) |
| Reanudación desde punto de control | Fuera de V1 (003) |
| Fabricación del `EstadoDelMundo` | Cubierto — RF-SCN-17 (008) |
| Fabricación del `ResumenRodante` | **A revisar** — RF-SCN-14 lo actualiza; ningún requisito dice cómo se construye |
| Cálculo de los vectores | **A revisar** — 004 los recibe dados y RF-MEM-6 prohíbe recalcularlos; ningún requisito pide calcularlos al indexar |

---

## A4. Contradicciones detectadas

1. **`architecture.md` §12.3 deja abierta la posición de la comprobación de densidad.**
   El plan de 007 implementa la posición actual (puerta 0 sobre el outline, RF-PLN-7). Si esa
   revisión se resuelve partiendo la puerta 0, cambian RF-PLN-3 y RF-PLN-7, y con ellos dos pasos.

Las dos contradicciones anteriores —§12.2 afirmando una spec inexistente, y `specs/spec1.md` fuera
del proceso 2— se resolvieron en la migración a `specs/NNN-slug/`.

---

## B. Cobertura requisito → paso

Ya no se mantiene aquí: cada `specs/NNN-slug/plan.md` cita en cada paso el ID que entrega, en la
misma carpeta que su `spec.md`, y la cobertura se comprueba con grep.

Comprobado al migrar (2026-09-23), contra el commit `7fb15ed`:

- **156 identificadores** —132 RF, 15 RNF, 9 R—, cada uno definido en una sola `spec.md`.
- **149 pasos**, sin duplicados. Cada identificador lo entrega un solo paso, con tres salvedades
  declaradas: RF-CFG-12 lo entrega el paso de RF-PLN-8, donde ocurre la congelación; R1 y R2 no
  tienen paso por naturaleza (A3.3); y la demostración de extremo a extremo de 011 es el único
  paso sin identificador, porque lo exige `verification.md` §5.
- **Prioridades**: dos requisitos *Deseables* —RF-WLD-9 y RF-MEM-41— y son los dos únicos pasos
  marcados `deseable`.
