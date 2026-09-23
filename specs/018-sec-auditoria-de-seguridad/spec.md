# 018 — SEC · Auditoría de seguridad

- [x] Spec approved   <- only the user marks this

## Objetivo

Que un subagente de Claude Code audite el repositorio y la API —inyección, exfiltración, dependencias y secretos— y deje en `docs/security-report.md` cada hallazgo con su severidad y el cambio que lo resolvió.

## Alcance

Cubre el subagente de auditoría con su skill y su comando de Claude Code, sus cuatro comprobaciones, el informe, la política de arreglo, el cierre del red-team log y su registro en `verification.md` §9.

Depende de 002, 003, 005, 015 y 016: la auditoría ataca el sistema entero.

**Fuera de alcance:**

- Correr la auditoría en cada cambio: va bajo demanda (`verification.md` §4.7). `detect-secrets` sobre cada cambio y Ruff con las reglas de seguridad son de 001.
- Las pruebas de aislamiento por la API y por MCP, que son de 002 y 016, y las de cada detector, que son de su spec: la auditoría las repite desde fuera, contra la API.
- La mutación de los guardarraíles (RT9): 003 y 014.
- Un servicio desplegado: el despliegue está fuera del encargo, así que la auditoría ataca una API local.

## Requisitos

Todos son **Obligatorio**.

### Auditoría

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-SEC-1 | El comando de Claude Code de la auditoría → lanza el subagente de seguridad, que carga su skill y ejecuta las cuatro comprobaciones sobre el repositorio y sobre una API local con datos ficticios | Obligatorio | D |
| RF-SEC-2 | Inyección → el subagente lanza contra la API los briefs y las peticiones adversariales de `verification.md` §4.9 —texto libre (RT1), petición de cambio y MCP (RT2, RT3), edición manual (RT10)— y comprueba que ninguna instrucción llega al brief, a una propuesta fuera de la selección ni a un delta, y que cada detección queda en el audit log | Obligatorio | D |
| RF-SEC-3 | Exfiltración → con dos clientes, el subagente pide con el token de B, por la API y por MCP, cada recurso de A —novela, versiones, capítulos, story bible, PDF, solicitudes de cambio y audit log—, e importa un brief de B cuyo texto libre pide datos de «la otra novela» (RT6). Todo responde como inexistente, y ninguna ventana guardada de las sesiones de B contiene datos de A | Obligatorio | D |
| RF-SEC-4 | Dependencias → `pip-audit` sobre el backend y `pnpm audit` sobre el frontend; cada vulnerabilidad conocida es un hallazgo, con la severidad que le da su fuente | Obligatorio | D |
| RF-SEC-5 | Secretos → `detect-secrets` sobre un volcado de `git log -p --all`, que abarca todo el historial de todas las ramas; cada secreto encontrado es un hallazgo | Obligatorio | D |

### Informe y arreglo

| ID | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-SEC-6 | El informe `docs/security-report.md` → lleva la fecha, el commit auditado y las comprobaciones hechas, y por cada hallazgo su comprobación, su severidad —crítica, alta, media o baja—, su estado y el cambio que lo resolvió o el riesgo aceptado de `verification.md` §6 que lo cubre | Obligatorio | I |
| RF-SEC-7 | Antes de entregar → todo hallazgo crítico o alto está resuelto, con su cambio. Uno medio o bajo se resuelve si es barato; si no, queda como riesgo aceptado en `verification.md` §6, con su motivo | Obligatorio | I |
| RF-SEC-8 | Al cerrar 018 → cada caso de `verification.md` §4.9 tiene rellenas «Detectado por», «Resultado» y «Resolución», con lo que de verdad lo cazó o «ninguno» | Obligatorio | I |
| RF-SEC-9 | Al cerrar 018 → la fila del subagente de auditoría de `verification.md` §9.4 recoge su resultado y la del comando, su propósito; la skill figura en §9.1 y en `.claude/skills/README.md`; y §9.5 ya no da los comandos por pendientes | Obligatorio | I |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-1 | El informe nunca reproduce el valor de un secreto: da el commit, el fichero, la línea y el tipo | I |

## Restricciones

| # | Restricción | Origen | Clase |
|---|---|---|---|
| R1 | El subagente, su skill y su comando se commitean en `.claude/`, como entregables de Claude Code del encargo, y se escriben con la skill `writing-for-agents` cargada | `project-constraints.md` («con agentes o skills», «Claude Code»); `CLAUDE.md` | I |

## Docs de referencia

- `architecture.md` §11.3, §13.1, §13.5 y §14.1 (seguridad).
- `verification.md` §3.2, §4.7, §4.9, §4.11, §5 («Seguridad del repositorio y la API»), §6 y §9.
