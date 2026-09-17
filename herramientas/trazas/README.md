# Trazas de dominio en Langfuse

Proyecta una novela ya generada a Langfuse con la forma del problema: **novela › capítulo › intento › invocación**. Es la mitad «de dominio» de la observabilidad de [`specs/functional.md` §9.3](../../specs/functional.md); la otra mitad, la traza de sesión, la pone el hook `Stop` de Claude Code y vive fuera del repositorio.

## Qué es y qué no es

Tiene el mismo estatus que el visor (§9.2): **fuera del harness, solo lectura, borrable sin consecuencias**. Si borras esta carpeta entera, el harness genera novelas exactamente igual.

1. **No es fuente de verdad.** `registro.md` manda; esto es una proyección suya. Si Langfuse y el registro discrepan, miente Langfuse.
2. **No es puerta del flujo.** No se ejecuta desde `/novela`, nunca. La skill lo tiene prohibido por escrito (SKILL.md §9): meter una llamada de red dentro del bucle añadiría turnos y un modo de fallo nuevo a un bucle cuyo mérito medido es tener cero fallos técnicos en 37 invocaciones.
3. **Fail-open.** Cualquier error se traga y sale con código 0.
4. **No escribe** un byte en `novelas/`.
5. **No recalcula nada.** Las métricas de calidad que sube son las que el harness escribió en `informe-cierre.md`, literales. Si no existen, no las inventa. Misma razón que en §9.2: dos cifras distintas para la misma novela y no sabrías cuál miente.

## Uso

```bash
# ver el árbol sin enviar nada y sin necesitar credenciales
python herramientas/trazas/exportar.py novelas/<slug> --dry-run

# exportar una novela
python herramientas/trazas/exportar.py novelas/<slug>

# exportar todas
python herramientas/trazas/exportar.py --todas
```

Credenciales desde el entorno: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`. Están en `.env` y en `.claude/settings.local.json`, los dos ignorados por git. **Nunca** en `.claude/settings.json`, que sí se versiona porque lleva los permisos del harness y el hook de inmutabilidad.

Si faltan las credenciales, avisa y sale sin error: regla 3.

## Qué sube

| Nivel | Observación | Contenido |
|---|---|---|
| Novela | traza (`agent`) | La idea como entrada; las métricas de `informe-cierre.md` como salida; perfil, modelos, límites, avisos y recuento de invocaciones como metadatos. `session_id` = slug |
| Etapa | span | `interrogatorio`, `capitulo NN`, `final` |
| Intento | span | Veredicto, longitud, decisiones del harness y totales de palabras de ese intento |
| Invocación | `generation` | Agente, modo, modelo, resultado, `pal_entrada`, `pal_salida` y, si algún día los hay, tokens y coste |
| Lo demás | evento | `longitud`, `veredicto`, `decision_harness`, `commit`, `paso_descartado`… con su fila del registro entera |

## Limitación conocida

`tok_entrada`, `tok_salida` y `coste_usd` vienen vacíos en el hito 1: la herramienta `Agent` de Claude Code no los devuelve (§6.6). Lo que sube es el volumen **en palabras**, que es lo que el harness sí mide. El coste real por agente llega en el hito 2, cuando la respuesta de OpenRouter lo traiga.

## Leer de vuelta: la API legada devuelve 410

`exportar.py` solo **escribe**, y lo hace por el SDK, así que esto no le afecta; pero cualquier lectura de vuelta (verificar lo subido, analizar una traza) se topa con ello. Comprobado el 2026-09-17 contra `cloud.langfuse.com`:

| Petición | Respuesta |
|---|---|
| `GET /api/public/traces` | **410** `LEGACY_API_UNAVAILABLE_FOR_NEW_ORGANIZATION` |
| `GET /api/public/observations` | **410**, mismo error |
| `GET /api/public/v2/observations` | 200 |

Langfuse retira esa API legada para las organizaciones creadas a partir del 16-09-2026, que es el caso de esta. El sustituto:

```bash
GET /api/public/v2/observations?traceId=<id>&fromStartTime=<ISO>&toStartTime=<ISO>&fields=core,io,metadata
```

**`fields=core,io,metadata` no es opcional.** Sin ese parámetro la respuesta trae la ficha (`name`, `level`, `latency`, `sessionId`…) pero **omite las claves `input`, `output` y `metadata`** — no vienen a `null`: no vienen. Como todo lo que esta herramienta sube de interés va justamente ahí, la traza parece vacía y el error se lee como «no se exportó nada» en vez de como «faltó un parámetro».

Autenticación: `Basic` con `LANGFUSE_PUBLIC_KEY:LANGFUSE_SECRET_KEY` en base64, las mismas credenciales de más arriba.

El MCP de Langfuse (`https://cloud.langfuse.com/api/public/mcp`) es la vía cómoda y está configurado en este proyecto; si en una sesión no responde, esto es el plan B.

## Dependencias

`langfuse>=4.0,<5`. Nada más; solo biblioteca estándar. El harness sigue sin dependencias de ningún tipo.
