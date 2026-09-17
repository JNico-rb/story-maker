# story-maker

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. Le das una idea; un harness coordina cinco agentes (interrogador, escritor, resumidor, revisor de encargo y revisor de continuidad) que la convierten en una novela completa con continuidad verificada.

## Frontend

Para ejecutar:
```bash
cd frontend
pnpm dev
```
Cuando está arrancado:
```
http://localhost:5173/#/
```

## Dos hitos

1. **Hito 1 — Claude Code.** El harness es la skill `/novela` más cinco subagentes, todo en Markdown. **Estado: validado con una novela completa de 5 capítulos** (ver spec §8.5). Los agentes van por defecto en `haiku`; el orquestador es la sesión y conviene lanzarla con el modelo bueno.
2. **Hito 2 — Runner contra OpenRouter, modelo barato.** El mismo diseño, en código, para novelas de 100–200 capítulos sin sesión interactiva. Pendiente.

## Cómo se usa (hito 1)

Desde una sesión de Claude Code en este repositorio:

```
/novela nueva "<tu idea en una o dos frases>"
/novela continuar novelas/<slug>
/novela estado novelas/<slug>
/novela verificar novelas/<slug>
/novela comparar comparativa/caso-NN-<slug>
```

`nueva` entrevista al usuario, propone biblia y escaleta, y tras la confirmación escribe la novela capítulo a capítulo sin más intervención. `continuar` retoma una novela donde se quedó. Se puede sobreescribir cualquier variable de configuración por comando: `/novela nueva "…" perfil_activo=novela_corta`.

Modo de prueba: toma idea y entrevista del caso de referencia, sin preguntar, y aprueba la escaleta solo si pasa la validación. Para la ejecución de referencia con confirmación manual: `/novela nueva "…" entrevista: pruebas/referencia/entrevista.md`.

```
/novela nueva modo-prueba: pruebas/referencia
```

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Especificación (manda sobre todo lo demás) y glosario | [specs/functional.md](specs/functional.md) |
| Variables editables: tamaño, modelos, límites, memoria, calidad | [config.json](config.json) |
| Reglas que Claude Code aplica siempre | [CLAUDE.md](CLAUDE.md) |
| Permisos del harness y registro del hook | [.claude/settings.json](.claude/settings.json) |
| Hook de inmutabilidad de los artefactos aprobados | [.claude/hooks/inmutables.sh](.claude/hooks/inmutables.sh) |
| Contratos de los cinco agentes | [.claude/agents/](.claude/agents/) |
| Qué salió de la primera ejecución completa | [specs/functional.md §8.5](specs/functional.md) |
| Trazas de una ejecución en Langfuse (fuera del harness) | [herramientas/trazas/](herramientas/trazas/) |
| Orquestador, procedimientos y plantillas | [.claude/skills/novela/](.claude/skills/novela/) |
| Caso de referencia para comparar configuraciones | [pruebas/referencia/](pruebas/referencia/) |
| Novelas generadas | `novelas/<slug>/` |
| Visor web de las novelas (solo lectura, fuera del harness) | [frontend/](frontend/) |
| Historial de decisiones y motivos | [CHANGELOG.md](CHANGELOG.md) |
