---
name: project-agent-sdk-openrouter-hechos
description: "Comportamientos del Claude Agent SDK 0.2.158 (CLI 2.1.280) sobre OpenRouter que contradicen o precisan architecture.md §7.3, §7.4, §11.2 y §12.1; medidos el 2026-09-23; pasados a los docs el mismo día"
metadata:
  node_type: memory
  type: project
  modified: 2026-09-23T13:13:50.334Z
---

Medido el 2026-09-23 en la comprobación de `architecture.md` §15.3 (modelo `inclusionai/ling-3.0-flash`, el más barato que hizo tool calls; `mistralai/mistral-nemo` responde pero no llama tools). Aplicados el 2026-09-23 en `architecture.md` §6.10 (cuota por construcción, decisión del usuario), §7.3, §7.4, §7.6, §11.2, §11.6, §12.1 y §16, y en `verification.md` §8, filas 11–14. Lo que queda aquí y no en los docs es detalle de librería para el `design.md` de la spec 001: `claudeMdExcludes`, `strict_mcp_config=True`, los nombres de las variables de entorno y el `ResultError` tras `max_turns`.

- `tools=[]` retira también la tool integrada `Skill` aunque esté en `allowed_tools`. Funciona `tools=["Skill"]`. Con `Skill` a secas, un rol puede cargar las skills que trae el CLI (probado con `claude-api`); `skills=["<nombre>"]` las rechaza ("not in this session's skills allowlist").
- Con `setting_sources=["project"]`, el CLI carga el `CLAUDE.md` (y `.claude/CLAUDE.md`) de **todos los directorios padre** del `cwd`: desde `backend/harness_workspace/` entraría el `CLAUDE.md` de desarrollo de la raíz y el `~/.claude/CLAUDE.md` personal. `CLAUDE_CONFIG_DIR` no lo evita. Arregla: `settings='{"claudeMdExcludes": [rutas de los padres]}'`. También arranca los servidores del `.mcp.json` de la raíz del repo; arregla `strict_mcp_config=True`. Los `.claude/settings.json` de los padres no se aplican.
- Por OpenRouter, `AssistantMessage.usage` llega a cero en todos los turnos; `ResultMessage.usage` (por consulta) coincide al token con OpenRouter; `model_usage` y `total_cost_usd` se acumulan por sesión, y el coste es una estimación unas 250 veces por encima del real (`costBasis: unknown`). `message_id` = id de generación `gen-…`, que `GET /api/v1/generation?id=` resuelve con el coste real. No hay llamadas ocultas: el gasto de la clave cuadra con las generaciones visibles.
- `interrupt()` corta el turno en ~0,02 s (`error_during_execution`, `terminal_reason=aborted_streaming`), pero el subproceso sigue vivo hasta `disconnect()` (~0,5 s, sin huérfanos). Agotar `max_turns` hace que `query()` lance `ResultError` después del `ResultMessage`.
- Por defecto: telemetría activa (`analytics_disabled: False`) y memoria automática activa; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` y `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` las apagan.

**Why:** son la base de las filas de §8 propuestas y de la spec 001; volver a descubrirlos cuesta una tarde de pruebas.

**How to apply:** al escribir la spec o el plan de las sesiones de rol, o al tocar §7.3, §7.4, §11.2 o §12.1, partir de estos hechos. Ver también [[entorno-windows-sin-admin]].
