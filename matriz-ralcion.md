# Matriz de Relación

Parte A — qué parte de [docs/architecture.md](docs/architecture.md) se implementa en [TODO.md](TODO.md), y con qué pasos.
Parte B — qué parte de [specs/spec1.md](specs/spec1.md) se implementa en [TODO.md](TODO.md), requisito a requisito.

Documento derivado: no es fuente de verdad ni layer del workflow de `AGENTS.md`. Se regenera
cuando cambie cualquiera de los ficheros que relaciona. Fecha: 2026-09-22.

**Estados**

| Estado | Significado |
|---|---|
| **Cubierto** | Todo lo que decide la sección tiene paso en el plan |
| **Parcial** | Parte tiene paso y parte no; la columna dice cuál |
| **Sin paso** | Criterio de diseño o riesgo asumido: se aplica al implementar, no se verifica como caso |
| **Fuera de V1** | Declarado fuera de alcance en `specs/spec1.md` §9 |
| **Contradicción** | El documento afirma algo que el repositorio no sostiene |

---

## A1. De `architecture.md` a `TODO.md`

### §1 — Separación en capas

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 1.1 | Tres ontologías: storyworld, artefacto narrativo, sistema de generación; la calidad son predicados sobre A y B | 0. Andamiaje — separación `domain` / `phases` / `platform` | Parcial — informa la estructura; ningún paso lo verifica |
| 1.2 | Tres fuentes de restricción y el test de frontera prompt/config | 1. CFG (RF-CFG-2) · 4. BRF (RF-BRF-7, promoción de poéticos a `Compromiso`) | Cubierto |

### §2 — Extracción del ContratoDeBrief

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 2 | Extracción no fiable al 100 %; verificador de ida y vuelta; compromisos no verificables; huecos de un solo uso | 4. BRF completo (RF-BRF-1 a RF-BRF-8) · 7. SCN (RF-SCN-18, el hueco resuelto pasa a canon) | Cubierto |

### §3 — Gestión de contexto y memoria

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 3.1 | Patrón outline-first + recuperación selectiva + validación de deltas; activos de primera clase | 3. MEM (RF-MEM-9 residentes, RF-MEM-43 trazabilidad) | Cubierto |
| 3.2 | RAG híbrido dinámico **sin re-ranking** | 3. MEM (RF-MEM-20 canal doble, RF-MEM-22 sin re-ranking) | Cubierto |
| 3.3 | Colecciones, no un pozo; RRF confinado dentro de cada colección | 3. MEM (RF-MEM-19) | Cubierto |
| 3.4 | Las tres colecciones: unidad, consumidor y modo de cada una | 3. MEM (RF-MEM-5, RF-MEM-20, RF-MEM-21, RF-MEM-31) | Cubierto |
| 3.5 | Residentes nunca indexados; proyección del outline; catálogo de tropos fuera del índice por calidad | 3. MEM (RF-MEM-9 a RF-MEM-13) | Cubierto — la aritmética de tokens de la tabla es justificación, no requisito |
| 3.6 | Cuota fija por (colección, consumidor); sin préstamo; validación al crear la ejecución | 1. CFG (RF-CFG-3 a RF-CFG-9) · 3. MEM (RF-MEM-28, RF-MEM-29, RF-MEM-30) | Cubierto |
| 3.7 | Corte temporal; `CanonCard` inmutables; índice append-only | 3. MEM (RF-MEM-4, RF-MEM-8, RF-MEM-18) | Cubierto |
| 3.8 | Arrastre por el grafo y arrastre temporal | 3. MEM (RF-MEM-24, RF-MEM-25, RF-MEM-26) | Cubierto |
| 3.9 | Doble consulta: prospectiva del escritor, retrospectiva del crítico de canon | 3. MEM (RF-MEM-15, RF-MEM-16, RF-MEM-17) | Cubierto |
| 3.10 | La escasez no bloquea; causa raíz `contexto ausente` | 3. MEM (RF-MEM-14, RF-MEM-27) · 10. OUT (RF-OUT-5) | Cubierto |
| 3.11 | Vectores congelados, desempate estable, recuperador en clase T | 1. CFG (RF-CFG-13) · 3. MEM (RF-MEM-6, RF-MEM-23, RNF-1, RNF-2) | Cubierto |
| 3.12 | Un escritor de índice por fase, siempre en la transacción del canon | 3. MEM (RF-MEM-2, RF-MEM-3, RF-MEM-7) · 5. WLD (RF-WLD-8) · 7. SCN (RF-SCN-14) | Cubierto |
| 3.13 | Techo de ventana: solo entrada, por etapa; intocables; orden de recorte declarado | 3. MEM (RF-MEM-35, RF-MEM-36, RF-MEM-37, RF-MEM-38) · 9. BUD (RF-BUD-2, RF-BUD-3) | Cubierto |
| 3.14 | `sqlite-vec` + FTS5 en el mismo fichero; `fastembed` con las dos condiciones de Windows | 0. Andamiaje (R5, RNF-11, R9, RNF-13) | Cubierto |
| 3.15 | Cuota por etapa = techo ÷ llamadas en vuelo; guardián invocado por código; conteo y reconciliación | 3. MEM (RF-MEM-33, RF-MEM-34, RF-MEM-39, RF-MEM-40, RF-MEM-41) | Cubierto — RF-MEM-41 marcado *deseable* |

### §4 — Marco de calidad

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 4.1 | Las cuatro puertas y su orden económico; la puerta 0 fuera del bucle | 6. PLN (RF-PLN-3 a RF-PLN-7) · 7. SCN (RF-SCN-3, RF-SCN-5) | Cubierto |
| 4.2 | `Criterio` → `Evaluador` → `Evaluable` → `Defecto` → `Veredicto`; **todo Evaluador declara su fiabilidad conocida**; todo Defecto registra causa raíz | 1. CFG (RF-CFG-15) · 7. SCN (RF-SCN-6, RF-SCN-8, RF-SCN-12) | **Parcial** — la fiabilidad declarada del Evaluador **no tiene paso**; ver A3 de este documento |

### §5 — Configuración

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 5.1 | Cuatro familias y sus ciclos de vida distintos | 1. CFG (RF-CFG-2, RF-CFG-11, RF-CFG-12, RF-CFG-13) | Cubierto |
| 5.2 | Seis reglas: no sobredeterminar, precedencia declarada, inmutabilidad post-outline, criterios desde config, `calidad` y `recuperacion` no editables | 1. CFG (RF-CFG-2, RF-CFG-3-9, 10, 11, 13) · 10. OUT (RF-OUT-6) | Cubierto |

### §6 — Precedencia y conflictos

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 6.1 | config gana en lo estructural, el prompt en lo narrativo; nada en silencio | 10. OUT (RF-OUT-6) | Cubierto |
| 6.2 | Los dos imposibles: aritmético en la entrada, densidad en la puerta 0 | 1. CFG (RF-CFG-1) · 2. RUN (RF-RUN-7) · 6. PLN (RF-PLN-4) | Cubierto |
| 6.3 | Fórmula de densidad; solo elementos comprometidos; techo de invención al arquitecto | 6. PLN (RF-PLN-3, RF-PLN-4, RF-PLN-6) · 5. WLD (RF-WLD-1) | Cubierto |

### §7 — Invariantes

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 7 | Los ocho invariantes y dónde se comprueba cada uno | 1: RF-WLD-6 · 2: RF-SCN-18 · 3 y 4: RF-SCN-3, RF-SCN-4 · 5: RF-SCN-17 · 6: RF-SCN-14 · 7: RF-MEM-8 · 8: RF-MEM-43 | Cubierto |
| 7.1 | Partición de los invariantes 3 y 4 en predicado determinista y semántico | 7. SCN (RF-SCN-3, RF-SCN-4) | Cubierto |
| 7.2 | El arrastre refuerza el invariante 1; el corte temporal refuerza el 5 | 3. MEM (RF-MEM-24, RF-MEM-18) | Cubierto |

### §8 — Sistema de agentes

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 8.1 | Autonomía total, entrada mínima, generación secuencial | 7. SCN (RF-SCN-1) · restricciones R1-R3 del spec | Cubierto — la autonomía es ausencia de pantallas, no un paso |
| 8.2 | Principio de asignación: 9 de código, 9 de modelo en un paso, 4 agentes | — | **Sin paso** — criterio que se aplica al implementar cada sección |
| 8.3 | Los cuatro agentes y el modo «reutilizar canon» | 5. WLD (RF-WLD-1, RF-WLD-2, RF-WLD-9) · 6. PLN (RF-PLN-1) · 7. SCN (RF-SCN-2, RF-SCN-10, RF-SCN-11) | Cubierto |
| 8.4 | Las nueve llamadas de modelo en un paso | 4. BRF (RF-BRF-1, RF-BRF-3) · 5. WLD (RF-WLD-3) · 7. SCN (RF-SCN-5, RF-SCN-6, RF-SCN-13) · 8. GLB (RF-GLB-4, RF-GLB-5, RF-GLB-6) | Cubierto |
| 8.5 | Los nueve componentes de código | 1. CFG · 3. MEM (recuperador) · 5. WLD (RF-WLD-4 selector) · 7. SCN (RF-SCN-3 puerta dura, RF-SCN-17 aplicador) · 8. GLB (RF-GLB-2, RF-GLB-3 comprobador) · 10. OUT (RF-OUT-2 redactor) | Cubierto |
| 8.6 | Flujo por fases, encadenado por artefacto persistido | Orden de las secciones 4 → 5 → 6 → 7 → 8 del plan · 2. RUN (RF-RUN-3) | Cubierto |
| 8.7 | Bucle por escena; correspondencia puerta ↔ crítico; regla única de enrutado | 7. SCN (RF-SCN-1 a RF-SCN-14) | Cubierto |
| 8.8 | Las seis reglas de interacción | 7. SCN (RF-SCN-7, RF-SCN-6, RF-SCN-5, RF-SCN-13, RF-SCN-12, RF-SCN-16) | Cubierto |
| 8.9 | Pase global descompuesto en cuatro comprobaciones por tipo de defecto | 8. GLB completo (RF-GLB-1 a RF-GLB-8) | Cubierto |
| 8.10 | Los cuatro sustitutos de la supervisión humana | 4. BRF (RF-BRF-3, RF-BRF-4, RF-BRF-5) · 5. WLD (RF-WLD-2, RF-WLD-4, RF-WLD-5) · 6. PLN (RF-PLN-3, RF-PLN-5) · 10. OUT (RF-OUT-2) | Cubierto |
| 8.11 | Prompt casi vacío: el caso más frecuente, probado desde el día uno | 4. BRF (RF-BRF-8) · 6. PLN (RF-PLN-6) · 10. OUT (demo de extremo a extremo) | Cubierto |
| 8.12 | Tres techos: ventana recorta, reintentos escalan, dinero bloquea | 9. BUD completo (RF-BUD-1 a RF-BUD-5) | Cubierto |

### §9 — Stack e implicaciones

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 9.1 | Elección de stack: backend, persistencia, frontend, salida | 0. Andamiaje · 10. OUT (RF-OUT-1) | **Parcial** — la fila del frontend queda **fuera de V1** |
| 9.2 | Slice por fase, `domain` y `platform`, regla de dependencia, proyección de nombres, FSD del frontend | 0. Andamiaje (estructura §7 y CI de dependencias) | **Parcial** — FSD del frontend **fuera de V1** |
| 9.3 | Trabajo asíncrono, SSE, punto de control por escena | 2. RUN (RF-RUN-1, RF-RUN-2, RF-RUN-4, RF-RUN-5, RNF-3, RNF-4) | Cubierto |
| 9.4 | Contrato de API mínimo; dónde va cada tipo de error | 2. RUN (RF-RUN-1, RF-RUN-3, RF-RUN-4, RF-RUN-6, RF-RUN-7) · 10. OUT (RF-OUT-1, RF-OUT-2) · 0. Andamiaje (RNF-15) | Cubierto |
| 9.5 | Biblioteca de canon sin vectores; tiempos por agente; el parcial no es verdad cacheable | 5. WLD (RF-WLD-9, RF-WLD-10) · 2. RUN (RF-RUN-8) · 10. OUT (RF-OUT-7) | Cubierto |

### §10 a §12 — Abierto, cerrado y pendiente

| § | Qué decide | Dónde se implementa | Estado |
|---|---|---|---|
| 10.2 | Siete cifras declaradas sin valor y el método para calibrarlas | Nota de cabecera del bloque 001: se leen de config y fallan de forma accionable si faltan | **Parcial** — calibrarlas está **fuera de V1** |
| 10.3 | Fragilidad del verificador de contrato | — | **Sin paso** — riesgo asumido, no tarea |
| 11 | Registro de decisiones cerradas | Transversal: cada fila apunta a la sección que la implementa | Registro, no fuente de pasos |
| 12.1 | Orquestación del trabajo — **sin escribir**: estados, reanudación automática, cancelación que conserva | 2. RUN (RF-RUN-9 estados, RF-RUN-5 punto de control, RF-RUN-6 cancelar) | **Parcial** — reanudación automática, techo de reanudaciones y promoción de canon al cancelar quedan **fuera de V1** |
| 12.2 | Declara escrita `specs/001-memoria-de-la-ejecucion.md` sobre §3 | 3. MEM | **Contradicción** — ese fichero no existe en el repositorio |
| 12.3 | Revisar si la puerta 0 se parte en dos | 6. PLN (RF-PLN-7) implementa la posición actual | **Parcial** — si se parte, arrastra RF-PLN-3 y RF-PLN-7 |
| 12.4 | Dónde se registra la deuda de spec | — | **Sin paso** — sin decidir |

---

## A2. De `TODO.md` a `architecture.md`

Lectura inversa: qué secciones del documento consume cada parte del plan.

| Sección del plan | Pasos | Secciones de `architecture.md` que consume |
|---|---|---|
| 0. Andamiaje | 12 | §3.14, §9.1, §9.2 |
| 1. CFG | 14 | §1.2, §3.6, §3.11, §5.1, §5.2, §6.2 |
| 2. RUN | 11 | §6.2, §9.3, §9.4, §9.5, §12.1 |
| 3. MEM | 45 | §3.1 a §3.13, §3.15, §7.2 |
| 4. BRF | 8 | §1.2, §2, §8.4, §8.10, §8.11 |
| 5. WLD | 11 | §3.12, §6.3, §8.3, §8.4, §8.5, §8.10, §9.5 |
| 6. PLN | 8 | §4.1, §6.2, §6.3, §8.3, §8.10, §8.11, §12.3 |
| 7. SCN | 18 | §2, §3.12, §4.1, §4.2, §7, §7.1, §8.1, §8.3, §8.4, §8.5, §8.7, §8.8 |
| 8. GLB | 8 | §8.4, §8.5, §8.9 |
| 9. BUD | 6 | §3.13, §8.12 |
| 10. OUT | 8 | §3.10, §6.1, §8.5, §8.10, §8.11, §9.1, §9.4, §9.5 |

**§3 es el eje.** Trece de sus quince subsecciones alimentan la sección MEM del plan, que concentra
45 de los 149 pasos. Es coherente con que §12.2 le dedique una spec propia.

---

## A3. Lo que `architecture.md` decide y el plan no implementa

### A3.1 Hueco real — sin paso y sin justificación

| Qué | Origen | Por qué importa |
|---|---|---|
| **Todo `Evaluador` declara su fiabilidad conocida** | §4.2, regla de diseño | Ni `specs/spec1.md` ni `TODO.md` mencionan «Evaluador» ni «fiabilidad». Es la regla que separa un juez calibrado de «ruido con formato de métrica», y hoy ningún paso la entrega. §10.2 da el método de calibración, pero calibrar está fuera de V1 y *declarar* la fiabilidad no lo está |

### A3.2 Fuera de V1, declarado en `specs/spec1.md` §9

| Qué | Origen |
|---|---|
| Frontend completo: stack, FSD v2.1, `app`/`pages`/`shared`, cliente generado | §9.1, §9.2 |
| Reanudación automática desde punto de control y techo de reanudaciones | §9.3, §10.2, §12.1 |
| Promoción del canon a la biblioteca **al cancelar** | §12.1 — promover al terminar bien sí entra, RF-WLD-11 |
| Calibración de las siete cifras sin valor | §10.2 |
| Formatos de salida distintos de Markdown | §11 |
| Re-ranking y expansión de consulta | §3.2, §11 |

### A3.3 Sin paso por naturaleza

| Qué | Origen | Por qué no es un caso |
|---|---|---|
| Tres ontologías | §1.1 | Criterio de modelado; se manifiesta en la estructura de módulos |
| Reparto 9 código / 9 modelo / 4 agentes | §8.2 | Criterio de asignación al implementar cada componente |
| Fragilidad del verificador de contrato | §10.3 | Riesgo asumido con mitigaciones parciales, no tarea |
| Decisiones cerradas | §11 | Registro |
| Deuda de spec | §12.4 | Sin decidir |

---

## A4. Contradicciones detectadas

1. **`architecture.md` §12.2 afirma que `specs/001-memoria-de-la-ejecucion.md` está escrita.**
   El fichero no existe: `specs/` contiene solo `spec1.md`. O se escribe esa spec, o §12.2 se
   corrige. El plan de `TODO.md` no deriva de ella: deriva de `specs/spec1.md`, y cada paso
   cita un identificador `RF-*` que solo existe en ese fichero.

2. **`specs/spec1.md` no cumple el proceso 2 de `AGENTS.md`.** No es `NNN-nombre.md`, cubre diez
   módulos en vez de una feature, y expresa requisitos en vez de casos observables entrada → salida.
   Decidido el 2026-09-22 que se queda así; queda anotado porque §12.2 y §12.4 asumen lo contrario.

3. **`architecture.md` §12.3 deja abierta la posición de la comprobación de densidad.**
   El plan implementa la posición actual (puerta 0 sobre el outline, RF-PLN-7). Si esa revisión
   se resuelve partiendo la puerta 0, cambian RF-PLN-3 y RF-PLN-7, y con ellos dos pasos del plan.

---

## B1. De `specs/spec1.md` a `TODO.md` — cobertura por módulo

**Sin huecos.** Los 147 requisitos de la spec (132 RF en §3, 15 RNF en §4) tienen exactamente
un paso cada uno. Los 149 pasos del plan son esos 147 más dos que no entregan requisito y lo
declaran: el arranque del proyecto, que cita la restricción R4, y la demostración de extremo a
extremo que la spec pide en §8 sin numerarla.

| Bloque de la spec | Requisitos | Sección del plan | Pasos | Estado |
|---|---|---|---|---|
| §3.1 CFG | 15 | 1. CFG | 14 (+1 en Andamiaje) | Cubierto |
| §3.2 RUN | 9 (+ RNF-3, RNF-4) | 2. RUN | 11 | Cubierto |
| §3.3 BRF | 8 | 4. BRF | 8 | Cubierto |
| §3.4 WLD | 11 | 5. WLD | 11 | Cubierto |
| §3.5 PLN | 8 | 6. PLN | 8 | Cubierto |
| §3.6 MEM | 43 (+ RNF-1, RNF-2) | 3. MEM | 45 | Cubierto |
| §3.7 SCN | 18 | 7. SCN | 18 | Cubierto |
| §3.8 GLB | 8 | 8. GLB | 8 | Cubierto |
| §3.9 OUT | 7 (+ demo de §8) | 10. OUT | 8 | Cubierto |
| §3.10 BUD | 5 (+ RNF-10) | 9. BUD | 6 | Cubierto |
| §4 RNF de entorno y estructura | RNF-5 a RNF-9, RNF-11 a RNF-15 | 0. Andamiaje | 12 | Cubierto |
| §2.4 Restricciones | R1 a R9 | repartidas | — | Cubierto — ver B3 |
| §5 Interfaces externas | sostenidas por RF-CFG-10, RF-CFG-14, RF-OUT-3, RNF-9, RNF-12 | repartidas | — | Cubierto |
| §6 Modelo de datos | sostenido por RF-SCN-9, RF-SCN-15, RF-WLD-11 | repartidas | — | Cubierto — ver B2 |
| §7 Estructura de módulos | RNF-7, RNF-8 | 0. Andamiaje | 3 | Cubierto |
| §9 Fuera de alcance | — | — | — | Fuera de V1 por decisión |

- **Clases T/A/I/D alineadas** en los 147 requisitos. RF-CFG-1 declara ya `clases T y A` en su paso.
- **Prioridades alineadas**: quedan dos requisitos *Deseables* —RF-WLD-9 y RF-MEM-41— y son los
  dos únicos pasos marcados `deseable`. RF-OUT-7 subió a Obligatorio y perdió la marca.
- **Un requisito, un paso**: ningún requisito se entrega dos veces. El duplicado de RF-CFG-12 en
  la sección CFG se retiró; la congelación se entrega donde ocurre, en el paso de RF-PLN-8.

---

## B2. Lo que la spec dice fuera de sus tablas y quién lo sostiene

Ningún elemento del modelo de datos ni de las interfaces queda sin requisito que lo respalde,
salvo los dos campos declarados a propósito como estructura sin caso.

| Qué | Dónde | Requisito que lo sostiene |
|---|---|---|
| `GET /runs/{id}/report`, con conflicto mientras la ejecución corre | §5.1 | RF-OUT-3 |
| Informe de una ejecución cancelada | §5.1 | RF-OUT-4 |
| Congelación del modelo de lenguaje, `runs.language_model` | §5.2, §6 | RF-CFG-14 |
| Puerto del proveedor en `platform` y su doble determinista | §5.2 | RNF-9 |
| Un fichero por ejecución más el fichero compartido de biblioteca | §5.4 | RNF-12, rutas por RF-CFG-10 |
| Biblioteca sin índice, consulta estructurada | §5.4 | RF-WLD-10 |
| `library_storyworlds`, `library_entities`, `library_edges`, append-only por versión | §6 | RF-WLD-11 |
| `epistemic_states`: un `EstadoEpistemico` por `Personaje`, solo si cambia su conocimiento | §6 | RF-SCN-15 |
| `defects.root_cause` como conjunto cerrado de seis | §6 | RF-SCN-9 |
| Validación en ejecución en entrada HTTP y salida de modelo | RNF-5 | paso propio de andamiaje |
| Escaneo de secretos, SQL dinámico y rutas | RNF-6 | paso propio de andamiaje |
| Reparto del recuperador y ausencia de `commons`/`shared`/`utils` | §7 | RNF-8 |

**Estructura sin caso, por decisión.** Dos campos de §6 se quedan como forma de tabla y no
generan requisito ni paso: `rolling_summaries.compressed` / `literal_tail`, y
`state_deltas.reversible`. No son comportamiento observable; si alguno lo fuera, entra por
proceso 2 antes que por el plan.

**El catálogo de tropos no está en ninguno de los dos ficheros:** `architecture.md` §9.2 lo sitúa
como dato en `domain`, versionado con el código, y el doc manda sobre la spec.

---

## B3. Restricciones de §2.4 y dónde se citan

Ninguna genera requisito: se citan en el paso que ya entrega su sustancia.

| # | Restricción | Dónde se cita |
|---|---|---|
| R1 | Autonomía total | Sin paso por naturaleza: es ausencia de superficie |
| R2 | Entrada mínima | Sin paso por naturaleza: `POST /runs` la materializa (RF-RUN-1) |
| R3 | Generación secuencial por escena | Paso de RF-SCN-1 |
| R4 | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, `uv` | Paso de arranque del proyecto |
| R5 | Índice en el mismo fichero que el canon | Paso de `sqlite-vec` y FTS5 |
| R6 | `fastembed` local, sin servicio y sin red tras la descarga | Paso de `fastembed` |
| R7 | Markdown, único formato | Paso de RF-OUT-1 |
| R8 | Ninguna fase importa a otra; `domain` no importa nada | Paso de estructura de módulos |
| R9 | Windows sin privilegios de administrador | Paso de `fastembed` |

---

## B4. Lectura inversa — del plan a la spec

Los 149 pasos se reparten así: 147 entregan un requisito cada uno, y dos lo declaran por su
nombre. No hay paso sin origen ni sección del plan sin bloque de requisitos que la funde.

| Paso sin requisito | Qué es |
|---|---|
| Arranque del proyecto con el stack de R4 | Prerrequisito del bloque, no caso de aceptación |
| Demostración de extremo a extremo con prompt casi vacío | Método que la spec exige en §8 para OUT y BUD |

---

## B5. Qué queda abierto entre estos dos ficheros

1. El hueco de **A3.1 sigue abierto**: `architecture.md` §4.2 exige que todo `Evaluador` declare
   su fiabilidad conocida, y eso no es hueco de la spec frente al plan, sino del doc frente a la
   spec. Cerrarlo empieza en `specs/spec1.md`, no aquí.
2. El renumerado de esta ronda cambió identificadores de CFG, SCN, OUT y RNF. `docs/*.md` no cita
   ninguno, así que el cambio no los alcanza. Las citas internas de §6 y §5.2 de la spec y las de
   este documento están actualizadas.
