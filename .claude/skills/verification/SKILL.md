---
name: verification
description: Genera o actualiza `verification.md`, el plan de verificación del proyecto — qué se verifica, con qué técnica y con qué clasificación T/A/I/D/U. Úsala cuando el usuario pida "plan de verificación", "verification.md", "cómo verificamos esto", "cómo sabemos que el código o la salida del agente es correcta", o al cerrar un spec y decidir la estrategia de pruebas.
---

# Plan de verificación

Produces **un documento**: `verification.md` en la raíz del proyecto (o
junto al spec, si el usuario lo pide para una feature concreta). No
implementas las pruebas; decides y documentas **cómo se verifica cada
cosa y quién lo hace**.

La taxonomía completa de técnicas y el marco de clasificación están en
[references/taxonomia.md](references/taxonomia.md). **Léela antes de
escribir nada.**

## Protocolo

1. Lee `docs/architecture.md` y la spec de la feature en curso,
   `specs/NNN-slug/spec.md` (las specs viven en la raiz del repo, no
   dentro de `docs/`). Si no hay nada de eso, pregunta al usuario
   qué se está construyendo antes de inventar.
2. Inventaria **lo que hay que verificar**, en dos bloques separados:
   - **Código** — módulos, interfaces entre servicios, invariantes de
     datos.
   - **Agentes** — cada agente de `.claude/agents/`, sus herramientas,
     su salida y los puntos donde puede hacer daño.
3. Para cada elemento, elige **una técnica** de la taxonomía y
   **exactamente una letra** del marco T/A/I/D/U. Si dos técnicas
   aplican, elige la más barata que dé la garantía necesaria y menciona
   la otra como refuerzo opcional.
4. Todo elemento que **no** se pueda verificar se clasifica `U` y se
   escribe en la tabla igual que los demás. Un riesgo aceptado se
   nombra; no se omite.
5. Escribe `verification.md` con el formato de abajo.
6. Termina con una línea en chat: `verification.md -> <n> elementos, <m> en U`.

## Formato de salida

```markdown
# Plan de verificación — <proyecto o feature>

## Alcance
<Qué cubre este plan y qué queda explícitamente fuera.>

## Verificación de código

| # | Qué se verifica | Técnica | Clase | Herramienta / dónde vive |
|---|---|---|---|---|
| V1 | `parse_outline()` nunca recibe tipos inválidos | Type checking | A | mypy en `./init.sh` |
| V2 | R3: límite por defecto = 20 | Unit test | T | `tests/test_recent.py` |

## Verificación de proceso (agentes)

| # | Qué se verifica | Técnica | Clase | Herramienta / dónde vive |
|---|---|---|---|---|
| P1 | El implementador no escribe fuera de `src/` | Guardrails | A | permisos en `settings.json` |
| P2 | Calidad de la novela generada | Eval LLM-as-judge | I | `evals/coherencia.yaml` |

## Riesgos aceptados (U)

| # | Qué no se verifica | Por qué | Mitigación parcial |
|---|---|---|---|
| U1 | Coste real en producción a 10k usuarios | No hay entorno equivalente | Rollout progresivo al 5% |

## Puertas de calidad
<Qué tiene que estar verde para aprobar un cambio: `./init.sh`,
cobertura de cada `R<n>`, revisión humana en los puntos `I`.>
```

## Reglas duras

- ❌ Nunca dejes un elemento sin clase. Si no sabes, es `U` con una
  razón escrita.
- ❌ Nunca propongas formal verification o symbolic execution "porque
  suena riguroso". Justifica el coste o no lo pongas.
- ❌ Nunca escribas tests ni configures herramientas desde esta skill.
  Solo el plan.
- ✅ Cada fila apunta a un archivo o comando concreto, existente o por
  crear. Nada de "tests unitarios" a secas.
- ✅ Si el proyecto ya tiene `verification.md`, actualízalo preservando
  la numeración `V<n>` / `P<n>` / `U<n>` existente.
