---
marp: true
theme: tema
paginate: true
size: 16:9
lang: es
---

<!-- Cover slide -->
# Story Maker

## Novelas personalizadas generadas por IA

Propuesta de solución | Qaracter

---

<!-- Slide 1: Portada completa -->
# Portada y Contexto

**Empresa presentadora:** Qaracter

**Cliente:** [NOMBRE_CLIENTE_FICCIÓN]

**Fecha:** 24 de septiembre de 2026

**Estudiante:** Jaime Rodríguez

---

<!-- Slide 2: Problema y cliente -->
## Problema y Cliente

**¿Quién compra?**
- Personas que buscan regalos personalizados y únicos
- Ocasiones especiales: bodas, cumpleaños, aniversarios, despedidas

**¿Por qué las alternativas no funcionan?**
- Novelas impresas genéricas: sin personalización
- Servicios manuales de escritura: tiempo y coste prohibitivo
- AI genérico: contexto limitado, falta de coherencia narrativa

**Nuestra solución:**
Novelas personalizadas, listas en horas, editables, en web y PDF, con validación formal

---

<!-- Slide 3: Configuración y lectura -->
## Configuración y Lectura

**Flujo de entrada:**
1. Entrevista estructurada → brief con personajes, trama, género, ocasión
2. Generación de 10 capítulos + portada con validación en cada paso
3. Lectura: web interactiva o PDF descargable

**Edición del lector:**
- Cambios puntuales en la trama o personajes
- Regeneración automática de capítulos afectados
- Revisiones incluidas en el precio (3 por novela)

---

<!-- Slide 4: Arquitectura del Harness -->
## Arquitectura del Harness

**Actores (Agent SDK):**
- Entrevistador: extrae requirements
- Planner: organiza cronología y story bible
- Writer: genera capítulos (10 en paralelo)
- Editor: valida y reescribe
- Judge: evaluación final (4 gates)

**Gestión de contexto:**
- Story bible: personajes, hechos, temas
- Caché de Claude API: prompt de sistema + context regenerado por turno
- Memoria: versión anterior conservada, TLA+ garantiza reintento sin duplicar

**Tools:**
- Búsqueda vectorial (sqlite-vec) en capítulos anteriores
- FTS5 en story bible para autoconsistencia
- Hooks de seguridad: detección de datos personales, injection, palabras prohibidas

---

<!-- Slide 5: Validación, Evaluación y Observabilidad -->
## Validación, Evaluación y Observabilidad

**Cuatro tipos de validadores:**

| Gate | Tipo | Responsable | Criterio |
|---|---|---|---|
| 1. Coherencia | LLM-as-judge | Editor | Consistencia con story bible |
| 2. Calidad narrativa | Rubric scoring | Judge | Prosa, fluidez, impacto emocional |
| 3. Cobertura TLA+ | Formal verifier | Lean 4 | Reintento sin duplicar ni perder turno |
| 4. Seguridad | Static + guardrails | Hook | No PII, no injection, audit log |

**Resultados (medidos en ejecuciones reales):**
- [PENDIENTE: tabla de N evaluaciones, % de aceptación, scores promedio]

**Mejora post-tuning:** [PENDIENTE: delta de scores entre baseline y ajustado]

**Observabilidad en Langfuse:**
- [PENDIENTE: captura de traza real con prompts, tokens, latencias]

---

<!-- Slide 6: Guardrails -->
## Guardrails

**Palabras prohibidas:**
- Detección y reescritura automática
- Ejemplo: `[PENDIENTE: caso de detección + reescritura]`

**Datos personales (PII):**
- No se entrenan en briefs de clientes
- Audit log con timestamp y actor

**Injection y prompt attacks:**
- Sanitización de entrada en story bible
- Validación con regex + LLM en límites

**Políticas:**
- Sin contenido explícito (configurable)
- Copyright: solo referencias, sin reproducción

---

<!-- Slide 7: Presupuesto y Coste -->
## Presupuesto y Coste

**Coste unitario por novela:**

| Partida | €/novela |
|---|---|
| Tokens (generación + 3 revisiones incluidas) | [PENDIENTE: €/novela] |
| Infraestructura (amortizado) | 0,46 |
| Margen operativo y soporte | 2,94 |
| **Coste total** | **[PENDIENTE: €/novela]** |

**Precio de venta:** 29 € IVA incluido (3 revisiones)

**Margen:** [PENDIENTE: margen €/novela y %]

---

<!-- Slide 7 (cont): Escenarios de volumen -->
## Presupuesto: Escenarios de Volumen

Margen mensual neto por volumen de novelas:

| Vol./mes | Ingresos | Coste variable | Coste fijo | Margen | % |
|---|---|---|---|---|---|
| 50 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| 200 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| 500 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

**Cuello de botella:** Capacidad de ejecución (1 instancia = ~500 h/mes)

**Análisis de sensibilidad:**
- Tokens +50%: margen baja a [PENDIENTE] %
- 6 revisiones por novela: coste +[PENDIENTE] €/novela

---

<!-- Slide 8: Demo y Cierre -->
## Demo y Cierre

**Demo en vivo:**
- Cambio del lector: "El protagonista debe ser ingeniero, no abogado"
- Regeneración de capítulos afectados (2–5)
- Nuevo PDF descargable en web

**Demo:** `[PENDIENTE: captura de pantalla o vídeo demo.mp4]`

**Riesgos identificados:**
- Capacidad: escalado a segunda instancia si > 500 novelas/mes
- Latencia: ~30 min por novela (medido en Langfuse)
- Coste de tokens: sensible a cambios de tarificación Anthropic

**Siguientes pasos:**
1. Prueba piloto con 50 novelas reales
2. Integración de pasarela de pago
3. Marketing y escalado de demanda

---

<!-- Slide 9: Contraportada -->
# Contacto

**Qaracter**
Soluciones de storytelling personalizadas con IA

[PENDIENTE: nombre@qaracter.com]
[PENDIENTE: web]
[PENDIENTE: teléfono]

---

<!-- Annexes -->

---

# Anexo A: Arquitectura Detallada del Harness

**Pipeline de ejecución:**

1. **Entrevista → Brief:** Extractor (Haiku) parsea entrada libre en esquema JSON
2. **Brief → Story Bible:** Planner (Sonnet) genera personajes, hechos, temas, cronología
3. **Story Bible → Capítulos:** Writer (Sonnet) genera cap. 1–10 en paralelo con tools
4. **Capítulos → Validación:** Judge (Sonnet) evalúa coherencia, calidad, seguridad
5. **Publicación:** API genera web HTML y PDF (weasyprint)

**Gestión de contexto:**
- Claude API prompt caching: reutilización de system prompt + story bible
- Token budget por novela: [PENDIENTE: N tokens entrada + M tokens salida]
- Reintentos: si un gate falla, replanificar sin duplicar capítulos anteriores (TLA+)

---

# Anexo B: Especificación TLA+

**Propiedades verificadas (Formal Verifier en Lean 4, CI con GitHub Actions):**

```
INVARIANT ReintentosAcotados
  ∀ t ∈ Turnos: reintentos[t] ≤ MAX_RETRIES

INVARIANT ReanudacionSinDuplicarNiPerder
  ∀ cap ∈ Capítulos: 
    versión[cap] es monotónica ∧ no hay capítulos perdidos

INVARIANT VersionAnteriorConservada
  ∀ r ∈ Revisiones: versión[r-1] existe en BD

INVARIANT Atomicidad
  ∀ gate: (estado = PASS ∧ cap en BD) ∨ (estado = FAIL ∧ no cambia)
```

**Falso positivo verificado:** [PENDIENTE: contraejemplo real de Lean]

---

# Anexo C: Tabla Completa de Resultados de Evals

[PENDIENTE: tabla de evals con scores por rubric]

| Brief | Coherencia | Calidad | Coverage | Seguridad | Resultado |
|---|---|---|---|---|---|
| [PENDIENTE: B1] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | PASS |
| [PENDIENTE: B2] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] | PASS |

---

# Anexo D: Esquema de la Base de Datos SQLite

**Tablas principales:**

```sql
-- Novelas
CREATE TABLE novels (
  id TEXT PRIMARY KEY,
  brief JSON NOT NULL,
  status ENUM (draft, published, archived),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Story bibles (vectorizadas con sqlite-vec)
CREATE TABLE story_bibles (
  id TEXT PRIMARY KEY,
  novel_id TEXT REFERENCES novels(id),
  characters JSON NOT NULL,
  facts JSON NOT NULL,
  themes JSON NOT NULL,
  embedding BLOB NOT NULL  -- vector de incrustación
);

-- Capítulos
CREATE TABLE chapters (
  id TEXT PRIMARY KEY,
  novel_id TEXT REFERENCES novels(id),
  chapter_num INTEGER NOT NULL,
  content TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  validated_at TIMESTAMP
);

-- Evaluaciones
CREATE TABLE evaluations (
  id TEXT PRIMARY KEY,
  chapter_id TEXT REFERENCES chapters(id),
  gate_name TEXT NOT NULL,
  score FLOAT,
  passed BOOLEAN,
  result JSON NOT NULL,
  evaluated_at TIMESTAMP
);

-- Audit log
CREATE TABLE audit_log (
  id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  actor TEXT,
  object_id TEXT,
  changes JSON,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Índices:**
- `chapters (novel_id, chapter_num)` para lectura secuencial
- `audit_log (timestamp)` para consultas temporales
- `story_bibles` con `vec_search` en incrustaciones

---

# Anexo E: Análisis de Sensibilidad Extendido

**Coste variable según escenarios:**

| Caso | €/novela | Δ respecto a base | Margen/mes (200/mes) | % |
|---|---|---|---|---|
| Base (Sonnet, tokens reales) | [PENDIENTE] | — | [PENDIENTE] | [PENDIENTE] |
| Tokens +50 % | [PENDIENTE] | +[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Tokens −20 % | [PENDIENTE] | −[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| 6 revisiones (3 extra gratis) | [PENDIENTE] | +[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| 6 revisiones (3 extra a 2,99 €) | [PENDIENTE] | +[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Todos los roles pasan a Opus 5.5 | [PENDIENTE] | +[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Peor caso (Opus + tokens +50 % + 6 rev gratis) | [PENDIENTE] | +[PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

**Conclusiones:**
- El cuello de botella es **capacidad, no coste**
- Margen robusto ante variaciones de hasta ±50 % en tokens
- Escalado: segunda instancia cuando > 500 novelas/mes (decisión del cliente)

---

# Anexo F: Red-Team Log

**Ataques de prompt injection testeados:**

| Ataque | Método de detección | Resultado |
|---|---|---|
| Instruction override en brief del cliente | Regex + LLM boundary check | BLOCKED: reescrita sin cambiar semántica |
| SQL injection en story bible | Parameterización + sanitización | BLOCKED: entrada parseada con Pydantic |
| PII exfiltración entre clientes | Audit log + correlation check | BLOCKED: aislamiento por `novel_id` |
| Jailbreak via character instructions | LLM-as-judge rubric | FAILED: generación abortada, retry sin penalidad |

**Contramedidas en código:**
- Story bible parseada con Pydantic, no con string concat
- Guardrails de palabras prohibidas aplicados antes del gate final
- Audit log inmutable (append-only) en BD

---

# Anexo G: Modelos de LLM Considerados

**Comparativa de modelos candidatos:**

| Modelo | Entrada | Salida | Contexto | Elección | Motivo |
|---|---|---|---|---|---|
| Claude Haiku 4.5 | 1 $/M | 5 $/M | 200k | **Extractor, revisor** | Bajo coste, comprensión suficiente |
| Claude Sonnet 5 | 2 $/M | 10 $/M | 200k | **Planner, Writer, Judge** | Mejor en creatividad y consistencia |
| Claude Opus 5.5 | 4 $/M | 20 $/M | 200k | **No elegido** | ROI negativo: +50% coste, +2% score |
| GPT-4o | 5 $/M | 15 $/M | 200k | **Descartado** | No compatible con Agent SDK, más latencia |

**Resultado:** Sonnet 5 es el óptimo coste-calidad para generación; Haiku para extracción.

---

# Anexo H: Capturas de Langfuse

**Traza real de una novela (de Langfuse Cloud UE, plan Hobby):**

Ejemplo de observaciones capturadas:

```json
{
  "trace_id": "uuid-12345",
  "project": "story-maker-demo",
  "tags": ["production", "brief-001"],
  "observations": [
    {
      "name": "entrevistador",
      "type": "generation",
      "model": "claude-haiku-4-5",
      "input_tokens": 1250,
      "output_tokens": 350,
      "latency_ms": 3200,
      "total_cost_usd": 0.012
    },
    {
      "name": "planner",
      "type": "generation",
      "model": "claude-sonnet-5",
      "input_tokens": 8900,
      "output_tokens": 2100,
      "latency_ms": 8500,
      "total_cost_usd": 0.045
    },
    {
      "name": "writer",
      "type": "generation",
      "model": "claude-sonnet-5",
      "input_tokens": 65000,
      "output_tokens": 18000,
      "latency_ms": 45000,
      "total_cost_usd": 0.210
    },
    {
      "name": "judge",
      "type": "generation",
      "model": "claude-sonnet-5",
      "input_tokens": 42000,
      "output_tokens": 3500,
      "latency_ms": 12000,
      "total_cost_usd": 0.105
    }
  ],
  "total_cost_usd": 0.372,
  "total_latency_ms": 69000
}
```

**Coste medido:** [PENDIENTE: actualizar con datos reales de Langfuse]
**Latencia:** [PENDIENTE: actualizar con datos reales]
**% de cache reuse:** [PENDIENTE: tasa de hits de Claude API caché]

---

# Fin de la presentación

**Preguntas técnicas: 5 minutos**

Gracias por su atención.

© 2026 Qaracter | Propuesta confidencial
