# story-maker

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. Le das una idea; un harness coordina cuatro agentes (interrogador, escritor, resumidor y revisor) que la convierten en una novela completa con continuidad verificada.

## Dos hitos

1. **Hito 1 — Claude Code, modelo caro.** El harness es la skill `/novela` más cuatro subagentes, todo en Markdown. Se valida con historias de 5 capítulos. **Estado: en reconstrucción sobre la spec 0.5.0.**
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
| Permisos y hook de inmutabilidad | [.claude/settings.json](.claude/settings.json) |
| Contratos de los cuatro agentes | [.claude/agents/](.claude/agents/) |
| Orquestador, procedimientos y plantillas | [.claude/skills/novela/](.claude/skills/novela/) |
| Caso de referencia para comparar configuraciones | [pruebas/referencia/](pruebas/referencia/) |
| Novelas generadas | `novelas/<slug>/` |
| Visor web de las novelas (solo lectura, fuera del harness) | [frontend/](frontend/) |
| Historial de decisiones y motivos | [CHANGELOG.md](CHANGELOG.md) |
