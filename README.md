# story-maker

Generador agéntico de novelas en castellano sobre cómo será el mundo tras la revolución de la IA. Tres agentes —interrogador, escritor, revisor— coordinados por un harness convierten una idea en biblia, escaleta, capítulos revisados y manuscrito, con continuidad verificada.

## El plan, en dos fases

| | Fase 1 (ahora) | Fase 2 (destino) |
|---|---|---|
| Dónde corre | Claude Code: skill `/novela` + tres subagentes. Sin código | Runner propio contra OpenRouter. Código |
| Modelo | El caro (`opus`), para medir el techo del diseño | Barato, con escalado al caro cuando algo va mal |
| Tamaño | 3 capítulos (`relato`) | 100–200 capítulos (`saga`) |
| Para qué | Validar contratos, límites, revisión, reanudación | Generar novelas largas desatendido |

Lo que se valida en la fase 1 —contratos de los agentes, artefactos, configuración, estructura de la carpeta— es exactamente lo que se porta a la fase 2. Qué se porta y qué se reimplementa: [specs/functional.md §10](specs/functional.md#10-fase-2--el-runner-contra-openrouter).

## Cómo se lanza (fase 1)

Desde una sesión de Claude Code en este repositorio:

```
/novela nueva "<idea en una o dos frases>"
/novela continuar novelas/<slug>       # retoma donde se quedó
/novela estado novelas/<slug>          # fase, capítulo, intento, avisos
/novela comparar comparativa/<caso>    # dos novelas de la misma idea, distinta configuración
```

La primera fase hace preguntas (entrevista con `grilling`); tras aprobar la escaleta, el resto corre solo. Para probar el harness sin entrevista: `/novela nueva "…" modo-prueba: pruebas/respuestas-prueba.md`.

Todo lo ajustable —tamaño, modelos, reintentos, reescrituras, memoria— está en [harness.config.json](harness.config.json), explicado en [specs/functional.md §7](specs/functional.md#7-variables-configurables--harnessconfigjson). Cualquier clave se puede sobreescribir en el comando: `/novela nueva "…" modelos.escritor=haiku modelos.escalado.activo=true`.

## Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Especificación (manda sobre todo lo demás) | [specs/functional.md](specs/functional.md) |
| Qué produce una ejecución y cómo comprobar que está completa | [specs/inventario.md](specs/inventario.md) |
| Configuración | [harness.config.json](harness.config.json) |
| Reglas para Claude Code | [CLAUDE.md](CLAUDE.md) |
| Orquestador | [.claude/skills/novela/](.claude/skills/novela/) |
| Contratos de los agentes | [.claude/agents/](.claude/agents/) |
| Novelas generadas (una carpeta por novela, es el único estado) | [novelas/](novelas/) |
| Comparaciones entre ejecuciones | [comparativa/](comparativa/) |
| Historial de decisiones de diseño | [CHANGELOG.md](CHANGELOG.md) |
