# 001 — BASE · Diseño

Lo que ninguna `spec.md` puede decir porque nombra tecnología: las interfaces con el exterior y el modelo de datos de todo el backend V1. Cada tabla y cada interfaz citan el requisito que las sostiene.

## Proveedor de modelo de lenguaje

Puerto declarado en `platform`, con implementación intercambiable. Toda llamada devuelve, además del texto, el uso de entrada y salida y el coste imputado. El modelo se declara en `config.operacion` y se congela al crear la ejecución (RF-CFG-14). El puerto y su doble determinista son RNF-9.

## Persistencia

Dos ficheros SQLite, con las rutas declaradas en `config.operacion` y sin valor por defecto en el código (RF-CFG-10, RNF-12):

- **Fichero de ejecución**, uno por ejecución: canon, artefacto narrativo, estado e índice. Las extensiones `sqlite-vec` y FTS5 se cargan sobre esa misma conexión.
- **Fichero compartido**: la biblioteca de canon, común a todas las ejecuciones. No lleva índice de ningún tipo —ni vectores (RF-WLD-10) ni FTS5— y se consulta por identificador y por atributos.

El `CatalogoDeTropos` no vive en ninguno de los dos: es dato curado en `domain`, versionado con el código (`architecture.md` §9.2).

## Modelo de datos

Nombres en inglés según la proyección de `architecture.md` §9.2. El esquema es orientativo en tipos y obligatorio en estructura: lo que no puede cambiar es qué es inmutable, qué es append-only y qué se escribe en la misma transacción.

```sql
-- Ejecución y entrada
CREATE TABLE runs (
  id                TEXT PRIMARY KEY,
  created_at        TEXT NOT NULL,
  status            TEXT NOT NULL,     -- máquina de estados de RF-RUN-9
  phase             TEXT NOT NULL,
  current_scene     INTEGER,
  prompt            TEXT NOT NULL,
  config_json       TEXT NOT NULL,     -- config congelada de esta ejecución
  embedding_model   TEXT NOT NULL,     -- congelado, RF-CFG-13
  language_model    TEXT NOT NULL,   -- congelado, RF-CFG-14
  money_spent       REAL NOT NULL DEFAULT 0
);

-- Contrato de brief
CREATE TABLE brief_contracts (run_id TEXT PRIMARY KEY REFERENCES runs(id), freedom_degree REAL NOT NULL);
CREATE TABLE commitments (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  statement TEXT NOT NULL, kind TEXT NOT NULL,
  hardness TEXT NOT NULL CHECK (hardness IN ('inviolable','preference')),
  verifiable INTEGER NOT NULL
);
CREATE TABLE gaps (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  scope TEXT NOT NULL, resolved_by TEXT, resulting_canon TEXT
);

-- Canon: entidades y aristas del grafo causal
CREATE TABLE canon_entities (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  kind TEXT NOT NULL,                  -- novum, consequence, constraint, character, faction, ...
  payload_json TEXT NOT NULL,
  created_at_scene INTEGER NOT NULL
);
CREATE TABLE canon_edges (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  source_id TEXT NOT NULL REFERENCES canon_entities(id),
  target_id TEXT NOT NULL REFERENCES canon_entities(id),
  relation TEXT NOT NULL,              -- implies, derives_from, sustains, defines, ...
  order_n INTEGER CHECK (order_n BETWEEN 1 AND 3)
);

-- Artefacto narrativo
CREATE TABLE outlines (run_id TEXT PRIMARY KEY REFERENCES runs(id), version INTEGER NOT NULL, frozen INTEGER NOT NULL DEFAULT 0);
CREATE TABLE chapters (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  number INTEGER NOT NULL, arc_function TEXT, tension_in REAL, tension_out REAL, target_words INTEGER
);
CREATE TABLE scenes (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  chapter_id TEXT NOT NULL REFERENCES chapters(id),
  number INTEGER NOT NULL, pov TEXT, dramatic_function TEXT, target_words INTEGER,
  status TEXT NOT NULL,                -- planned, drafted, accepted, rewritten
  text TEXT
);
CREATE TABLE arcs (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  name TEXT NOT NULL, kind TEXT NOT NULL,
  setup_scene INTEGER, resolution_scene INTEGER,
  state TEXT NOT NULL CHECK (state IN ('open','resolved'))
);

-- Estado
CREATE TABLE state_deltas (
  id TEXT PRIMARY KEY, scene_id TEXT NOT NULL REFERENCES scenes(id),
  kind TEXT NOT NULL CHECK (kind IN ('declared','real')),
  payload_json TEXT NOT NULL, reversible INTEGER NOT NULL
);
CREATE TABLE world_states (run_id TEXT NOT NULL, scene_number INTEGER NOT NULL, snapshot_json TEXT NOT NULL, PRIMARY KEY (run_id, scene_number));
CREATE TABLE epistemic_states (
  id TEXT PRIMARY KEY, scene_id TEXT NOT NULL REFERENCES scenes(id),
  character_id TEXT NOT NULL, side TEXT NOT NULL CHECK (side IN ('in','out')),
  known_json TEXT NOT NULL, falsely_believed_json TEXT NOT NULL
);
CREATE TABLE rolling_summaries (run_id TEXT NOT NULL, scene_number INTEGER NOT NULL, compressed TEXT NOT NULL, literal_tail TEXT NOT NULL, PRIMARY KEY (run_id, scene_number));
CREATE TABLE style_sheets (run_id TEXT PRIMARY KEY REFERENCES runs(id), payload_json TEXT NOT NULL);

-- Memoria de largo plazo: tres colecciones, append-only
CREATE TABLE canon_cards (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
  entity_id TEXT NOT NULL REFERENCES canon_entities(id),
  content TEXT NOT NULL,
  from_scene INTEGER NOT NULL,
  to_scene INTEGER                      -- NULL = vigente; se cierra, nunca se borra
);
CREATE TABLE scene_summaries (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, scene_number INTEGER NOT NULL, content TEXT NOT NULL);
CREATE TABLE prose_paragraphs (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, scene_number INTEGER NOT NULL, chapter_number INTEGER NOT NULL, content TEXT NOT NULL);

-- Canal léxico y canal denso
CREATE VIRTUAL TABLE memory_fts USING fts5(unit_id, collection, content, tokenize='unicode61');
CREATE VIRTUAL TABLE memory_vec USING vec0(unit_id TEXT PRIMARY KEY, collection TEXT, embedding FLOAT[384]);

-- Calidad y evidencia
CREATE TABLE defects (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL, scene_id TEXT,
  criterion TEXT NOT NULL, severity TEXT NOT NULL, location TEXT,
  root_cause TEXT NOT NULL CHECK (root_cause IN (   -- conjunto cerrado, RF-SCN-9
    'contexto ausente','canon contradictorio','deriva de estilo',
    'fallo de outline','config infactible','presupuesto excedido'))
);
CREATE TABLE verdicts (id TEXT PRIMARY KEY, evaluable_kind TEXT NOT NULL, evaluable_id TEXT NOT NULL, action TEXT NOT NULL);
CREATE TABLE traceability (
  id TEXT PRIMARY KEY, fragment_id TEXT NOT NULL, element_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('justifying','denied')),
  denial_reason TEXT CHECK (denial_reason IN ('quota','trim'))   -- RF-MEM-42
);
CREATE TABLE model_calls (
  id TEXT PRIMARY KEY, run_id TEXT NOT NULL, agent TEXT NOT NULL, phase TEXT NOT NULL,
  scene_number INTEGER, input_tokens_counted INTEGER, input_tokens_reported INTEGER,
  output_tokens INTEGER, cost REAL
);

-- Biblioteca de canon (fichero compartido, sin índice) --------------------------
CREATE TABLE library_storyworlds (
  id TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  parent_id TEXT REFERENCES library_storyworlds(id),  -- versión de la que deriva
  promoted_from_run TEXT NOT NULL,
  promoted_at TEXT NOT NULL
);
CREATE TABLE library_entities (
  id TEXT PRIMARY KEY, storyworld_id TEXT NOT NULL REFERENCES library_storyworlds(id),
  kind TEXT NOT NULL, payload_json TEXT NOT NULL
);
CREATE TABLE library_edges (
  id TEXT PRIMARY KEY, storyworld_id TEXT NOT NULL REFERENCES library_storyworlds(id),
  source_id TEXT NOT NULL, target_id TEXT NOT NULL, relation TEXT NOT NULL,
  order_n INTEGER CHECK (order_n BETWEEN 1 AND 3)
);
```

Cinco reglas del esquema que son requisito y no detalle:

1. `canon_cards` no admite `UPDATE` ni `DELETE`. Un cambio cierra la tarjeta poniendo `to_scene` y añade otra fila (RF-MEM-4).
2. `canon_cards`, `scene_summaries`, `prose_paragraphs`, `memory_fts` y `memory_vec` se escriben en la misma transacción que el canon que las origina (RF-MEM-2).
3. `traceability` guarda lo entregado y lo negado en la misma tabla, distinguidos por `role` (RF-MEM-42).
4. `epistemic_states` solo recibe fila por `Personaje` cuyo conocimiento cambia en la escena; el resto se arrastra (RF-SCN-15). El `EstadoEpistemico` viaja al escritor dentro del `EstadoDelMundo` residente, no como pieza aparte de la ventana.
5. `library_storyworlds` es append-only: promover nunca sobrescribe, añade versión que apunta a la anterior (RF-WLD-11).

Las tablas `library_*` viven en el fichero compartido; todas las demás, en el fichero de la ejecución.

**Estructura sin requisito, por decisión.** `rolling_summaries.compressed` / `literal_tail` y `state_deltas.reversible` se quedan como forma de tabla y no generan requisito ni paso: no son comportamiento observable. Si alguno lo fuera, entra por el proceso 2 antes que por el plan.
