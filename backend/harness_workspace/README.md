# WorkspaceDelHarness

Directorio de trabajo de las sesiones de rol del Agent SDK: `CLAUDE.md` de producto, la skill `personalizacion-natural` y un prompt por rol.
Lo rellenan las specs dueñas según la tabla de propiedad de `backend/AGENTS.md`: la 011 escribe el `CLAUDE.md` de producto, la skill y los prompts de writer y editor; 008, 010, 012, 014 y 017, los prompts de sus roles.

| Fichero | Rol | Spec |
|---|---|---|
| `CLAUDE.md` | todos | 011-I12 |
| `.claude/skills/personalizacion-natural/SKILL.md` | writer, editor | 011-I13 |
| `prompts/interviewer.md`, `prompts/extractor.md` | entrevistador, extractor | 008 |
| `prompts/planner.md` | planner (modo `plan`) | 010-I8 |
| `prompts/writer.md` | writer (`write`, `rewrite`) | 011-I14 |
| `prompts/editor.md` | editor | 011-I14 |
