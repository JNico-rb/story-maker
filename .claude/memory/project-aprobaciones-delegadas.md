---
name: project-aprobaciones-delegadas
description: "Desde 2026-09-24 las casillas de aprobación de spec y plan las marcan agentes (auditor a gap cero, verificador al cierre), no el usuario; solo escalados y tareas humanas le llegan a él."
metadata:
  node_type: memory
  type: project
  modified: 2026-09-24T09:31:40.882Z
---

El 2026-09-24 el usuario confirmó (AskUserQuestion) que las casillas de aprobación de spec y plan de `TODO.md` las marcan agentes: `auditor` aprueba spec y plan con gap cero y deja acta; `verificador` marca el cierre. El usuario solo interviene en escalados (≤3 rondas de auditoría sin gap cero) y en tareas solo humanas.

**Why:** quiere que la implementación la lleve otro chat de forma lo más autónoma posible; el `AGENTS.md` que él recortó esa mañana ya no tenía la regla «solo el usuario marca». Los carriles y sesiones de V2-test (8e, 9b, 019-*) quedaron obsoletos: solo existe la rama V2.

**Relajado el mismo día (11:35):** prioridad empezar y acabar el backend. El auditor aprueba sin huecos **bloqueantes** (requisito del encargo sin cubrir, contradicción con docs, caso no testeable, dependencia rota); los menores quedan anotados para después. Máximo 2 rondas.

**How to apply:** nunca pedirle que marque casillas; pasar spec y plan por `auditor`. Sí avisarle de lo que no puede delegarse: la revisión humana de una novela (el encargo la exige humana), el vídeo de demo, cuentas y tokens. Ver [[project-v2-reinicio-lean]] y [[feedback-maxima-simplicidad]].
