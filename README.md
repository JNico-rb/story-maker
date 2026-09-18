# story-maker

Generador agéntico de novelas en castellano sobre **cómo será el mundo tras la revolución de la IA**. Le das una idea; un harness coordina cinco agentes (interrogador, escritor, resumidor, revisor de encargo y revisor de continuidad) que la convierten en una novela completa con continuidad verificada.

## Ejecución del frontend

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

1. **Hito 1 — Claude Code.** Montar un harness que ejecuta modelos "más caros": el agente orquestador es Opus, ejecutado desde Claude Code, y los agentes del harness son Haiku.
2. **Hito 2 — Runner contra OpenRouter, modelo barato.** El mismo diseño, pero con el agente orquestador ejecutado a través de OpenRouter, y los agentes del harness con Haiku u otros modelos más baratos.

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
