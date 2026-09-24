# 020 — Evals

> Carril: D (C03, C04 y C15 en el carril X) · Depende de: 012-gate-de-publicacion (y, por él, 004, 008, 011) y 031-arranque (C03, C04, C15) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Medir el sistema sobre cinco briefs fijos y dejar la evidencia en el repo: `story-maker evals run` genera una novela por brief y `story-maker evals table` produce, desde SQLite, la tabla brief × validador y el resumen por brief de `verification.md` §4.2 (a) y (b). Esa evidencia sostiene la iteración de tuning, la comparación juez frente a humano, el caso de Lean y el cambio del lector propagado (§4.2 c–f). Cubre las filas 5e.1–5e.3, 5b.2, 5c.4, R.17 y P.2–P.5 de `verification.md` §5.

## Alcance

- Los cinco briefs ficticios de `ejemplos/briefs/` (`verification.md` §4.2 método 1): ejemplo, infantil, boda, adversarial y temporal, válidos para `schema-brief`.
- `evals run --email <cliente>`: importa cada brief con las mismas reglas que la entrevista (008), acepta sin cliente los hechos extraídos de sus `TextoLibre`, y lanza una ejecución de generación por brief (011) con la config y la etiqueta de prompts vigentes.
- `evals table`: la tabla (a) con la leyenda de celdas de §4.2 y el resumen (b), en Markdown, desde `validator_results`, `attempts`, `runs`, `role_sessions`, `extracted_facts` y `audit_log`, con el commit, la etiqueta de prompts y la traza de cada brief.
- Las demostraciones con modelo real (§4.2 a–f), al final, en un lote.

## Fuera de alcance

- Importar y validar un brief, comprobaciones C1–C6 y extracción de hechos → 008-brief-y-entrevista (esta spec las usa).
- Producir, validar y publicar → 011-produccion-de-capitulos, 012-gate-de-publicacion. Scores en Langfuse y `prompts push` → 004-observabilidad.
- Cambio del lector → 014-cambios-del-lector (aquí solo se usa en la demo §4.2 f). La `VistaDeVersion`, el PDF, `pdf-enlaces` y `export-pdf` → 013-lectura-y-pdf.
- Auditoría de seguridad y red-team D → 021-auditoria-de-seguridad.

## Comportamiento observable

**Convenciones.** Las pruebas usan el doble falso del puerto de agente (003) con guiones que publican o fallan, el doble nulo de observabilidad (001) y una base de fixture. A es un cliente registrado.

### Briefs

#### 020-C01 — Los cinco briefs del repositorio son válidos (T)
- **Entrada:** cada fichero de `ejemplos/briefs/`.
- **Salida:** hay exactamente cinco (ejemplo, infantil, boda, adversarial, temporal) y cada uno pasa `schema-brief` y las comprobaciones C1–C6 de 008. El adversarial lleva en un `TextoLibre` una instrucción dirigida al sistema; el temporal, un recuerdo con una partida definitiva y un deseo de trama que la contradice (`verification.md` §4.2, tabla «Qué debería ejercitar cada brief»).

### `evals run`

#### 020-C02 — Sin un cliente registrado no se crea nada (T)
- **Entrada:** `evals run --email nadie@example.com`, o sin `--email`.
- **Salida:** código de salida distinto de 0, un mensaje que nombra el problema y ninguna novela, brief ni ejecución nueva (`architecture.md` §15.8: el propietario es un cliente ya registrado).

#### 020-C03 — Una novela y una ejecución por brief, del cliente dado (T)
- **Entrada:** `evals run --email <A>` con el doble falso guionizado para publicar.
- **Salida:** cinco novelas nuevas de A, cada una con su brief confirmado importado del fichero y una ejecución de generación encolada; los hechos extraídos de sus `TextoLibre` quedan aceptados sin intervención del cliente. Al terminar la cola, las cinco ejecuciones están `published` y la salida lista cada brief con su novela y su ejecución.

#### 020-C04 — Un brief que no pasa no para a los demás (T)
- **Entrada:** `evals run` con un directorio de fixture donde uno de los cinco briefs no pasa `schema-brief`.
- **Salida:** ese brief no crea novela y la salida lo nombra con su defecto; los otros cuatro se lanzan como en 020-C03; el código de salida es distinto de 0.

#### 020-C17 — Un brief que ya tiene novela del cliente no se repite (T)
- **Entrada:** `evals run --email <A>` cuando A ya tiene la novela de un brief de eval (creada por `example` sobre ese fichero o por un `evals run` anterior), con su ejecución publicada, o en cola o interrumpida.
- **Salida:** ese brief no crea novela ni ejecución; la salida lo nombra con su novela y su ejecución; si estaba en cola, la procesa el mismo worker hasta `published`, sin relanzarla; los demás, como en 020-C03. `evals table` cuenta esa novela como la del brief.

#### 020-C05 — `evals run` no corre en la CI (T)
- **Entrada:** `evals run --email <A>` con la variable de entorno `CI` definida.
- **Salida:** código distinto de 0 y ninguna novela: las evals solo corren en la máquina con sesión de Claude Code (`verification.md` §4.2 método 2).

### `evals table`

#### 020-C06 — Celdas de la tabla brief × validador (T)
Con una base de fixture con las cinco ejecuciones y sus `validator_results` e `attempts`:

| Situación del validador en un brief | Celda |
|---|---|
| Bloqueante por capítulo, pasa al final, 2 intentos rechazados por él | `pasa · 2` |
| Bloqueante por capítulo, la ejecución terminó `failed` por él, 3 rechazos | `falla · 3` |
| Semántico con criterios 4, 3 y 5 | `4.0 (3)` |
| Linter con 7 avisos | `7` |
| No llegó a ejecutarse | `n/a` |
| Detector de inyección con 2 marcas en `audit_log` | `2` |
| Hook de política con 1 denegación en `audit_log` | `1` |

Las filas son los validadores de `verification.md` §4.2 (a), en ese orden; las columnas, los cinco briefs.

#### 020-C07 — Resumen por brief (T)
- **Entrada:** la misma base.
- **Salida:** la tabla (b) con, por brief: estado final (`published`, o `failed` con su motivo), capítulos aceptados al primer intento, ciclos de gate, tokens de entrada y de salida, coste USD (suma de `role_sessions.cost_usd`), latencia total, pico de tokens concurrentes reservados (máximo de la suma de `reserved_tokens` de las sesiones solapadas), etiqueta de prompts y commit, y el identificador de traza.

#### 020-C08 — La tabla sale solo de SQLite (T)
- **Entrada:** `evals table` con el doble nulo de observabilidad y la red saliente bloqueada.
- **Salida:** la misma tabla que con cualquier otro estado de Langfuse: nada de la tabla se lee de un servicio externo (`architecture.md` §11.7).

#### 020-C09 — Sin ejecuciones de evals, la tabla lo dice (T)
- **Entrada:** `evals table` sobre una base sin novelas de evals.
- **Salida:** código distinto de 0 y un mensaje que pide correr `evals run`; no se escribe ninguna tabla.

### `example` (movido desde 013)

#### 020-C15 — `example` produce la novela y su PDF (T)
- **Entrada:** `story-maker example ejemplos/briefs/ejemplo.json --email <cliente registrado>`, con el doble determinista del puerto de agente.
- **Salida:** una novela nueva, propiedad del cliente de `--email`, con una versión publicada y su PDF guardado en la ruta que recibe la orden.

### Demostraciones (con modelo real, al final)

#### 020-C16 — La novela de ejemplo real (D)
- **Entrada:** `story-maker example` sobre el brief del README, con el modelo real.
- **Salida:** `ejemplos/novela-ejemplo.pdf`, con 10 capítulos, pasa `pdf-enlaces`. Es el fichero que se commitea.


#### 020-C10 — Cinco briefs reales llenan (a) y (b) (D)
`evals run` con el login de Claude Code y `evals table` pegada en `verification.md` §4.2 (a) y (b), con números.

#### 020-C11 — Una iteración de tuning con antes y después (D)
§4.2 (c): un prompt vN → vN+1 (o un umbral) sobre los briefs del disparador (mínimo uno): el antes es su resultado de 020-C10, sin regenerar, y el después una ejecución nueva; cada resultado con la versión de prompt de Langfuse que lo produjo.

#### 020-C12 — Juez frente a revisión humana (D)
§4.2 (d) sobre la versión publicada del brief 1: una persona puntúa con la rúbrica del juez, sin ver antes sus puntuaciones, y se calcula la diferencia y el acuerdo.

#### 020-C13 — El caso que solo detecta Lean (D)
§4.2 (e) con el brief 5: `cronologia-lean` detecta la incoherencia y ningún otro validador; o, si no apareció, por qué.

#### 020-C14 — Un cambio del lector propagado y su coste (D)
§4.2 (f) sobre la novela del brief 1, con los afectados, los capítulos reescritos, el gate, la versión base conservada y el coste de la revisión.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 020-I1 | Ninguna prueba de esta spec llama a un modelo ni a Langfuse | T | Las pruebas corren con el doble falso, el doble nulo y la red saliente bloqueada salvo `127.0.0.1` |
| 020-I2 | `evals table` es determinista: la misma base da la misma salida, byte a byte | T | Dos ejecuciones sobre la misma fixture comparan su salida |
| 020-I3 | Las evals usan las mismas reglas de importación y validación que el producto: ningún atajo solo para evals | I | `verificador`: `evals run` llama a los mismos casos de uso que la API |
| 020-I4 | El coste es a precio de lista, no una factura (`verification.md` §6 U23) | U | §6 |

## Decisiones (en `architecture.md` §18)

- Un brief inválido no para a los demás; la orden termina con código distinto de 0 (020-C04).
- `evals run` se niega a correr con `CI` definida (020-C05).
- `evals table` escribe el Markdown en la salida estándar; se pega a mano en `verification.md` §4.2.

## Docs referenciados

- `verification.md` §4.2 (método, leyenda, tablas a–f, protocolo de coste, presupuesto de cuota), §5 (filas 5e.1–5e.3, 5b.2, 5c.4, R.17, P.2–P.5), §6 U23.
- `architecture.md` §11.7 (evals y evidencia en SQLite), §13 (scores y prompts), §15.6 (tablas), §15.8 (órdenes de la CLI), §16.15.
- `definitions.md`: `Brief`, `TextoLibre`, `Ejecucion`, `SesionDeRol`, `Cliente`.
- Specs 001, 003, 004, 008, 011, 012, 013, 014.
