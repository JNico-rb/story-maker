# Anexo D · Esquema SQLite

Un único fichero SQLite con FTS5 y `sqlite-vec`. Las tablas de ámbito versión se copian enteras al crear una versión nueva, en una sola transacción; así cada versión publicada es autocontenida e inmutable.

## D.1 Cuentas, entrada y peticiones

```mermaid
erDiagram
    users ||--o{ novels : posee
    users ||--o{ banned_terms : "nivel user"
    novels ||--o{ banned_terms : "nivel novel"
    users ||--o{ audit_log : propietario
    novels ||--o| interviews : "se entrevista en"
    interviews ||--o{ interview_messages : registra
    novels ||--|| briefs : tiene
    novels ||--o{ free_texts : adjunta
    free_texts ||--o{ extracted_facts : produce
    novels ||--o{ change_requests : recibe
    novels ||--o{ manual_edits : recibe
```

## D.2 Una versión: story bible, artefacto e índice

```mermaid
erDiagram
    novels ||--o{ versions : tiene
    versions |o--o{ versions : "version base"
    versions ||--|| worlds : ambienta
    versions ||--|{ characters : agrupa
    versions ||--o{ places : agrupa
    versions ||--|{ facts : agrupa
    facts ||--o{ fact_usages : "se usa en"
    versions ||--o{ events : ordena
    events ||--o{ event_characters : presentes
    characters ||--o{ event_characters : "esta en"
    versions ||--|{ outline_chapters : "10 capitulos"
    versions ||--|| style_sheets : sigue
    versions ||--o{ chapters : "hasta 10"
    versions ||--o{ canon_cards : indexa
    canon_cards ||--|| canon_cards_fts : "canal lexico"
    canon_cards }o--|| embeddings : "vector por huella"
```

## D.3 Ejecuciones y calidad

```mermaid
erDiagram
    novels ||--o{ runs : "se ejecuta en"
    runs ||--o| versions : candidata
    runs ||--o{ attempts : cuenta
    runs ||--o{ checkpoints : deja
    runs |o--o{ role_sessions : abre
    runs ||--o{ validator_results : produce
    runs ||--o{ chronology_files : verifica
    runs |o--o{ audit_log : "decide en"
```

## D.4 Tablas clave

| Tabla | Guarda |
|---|---|
| `facts` | Sujeto, atributo, valor, origen (brief, texto libre o planificado), si es obligatorio |
| `fact_usages` | En qué capítulo se usa cada hecho: calcula los capítulos afectados por un cambio |
| `events`, `event_characters` | La cronología que alimenta Lean: momento, lugar, presentes, tipo, excluido, analepsis |
| `canon_cards`, `canon_cards_fts`, `embeddings` | El índice del RAG; los vectores se comparten entre versiones por huella |
| `checkpoints` | Un capítulo aceptado por fila (0 = plan aplicado). Solo inserción |
| `role_sessions` | Rol, modelo, versión de prompt, tokens, coste, latencia: la fuente del coste por novela |
| `validator_results` | Validador, capítulo, pasa, score, detalle: la fuente de la tabla de evals |
| `audit_log` | Cada decisión del policy engine (allow, deny, flag). Solo inserción |

---
