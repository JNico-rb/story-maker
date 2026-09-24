# 021 — Auditoría de seguridad

> Carril: A · Depende de: 002-autenticacion, 015-servidor-mcp (y el backend completo) · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Auditar el repositorio y la API del harness con el subagente `seguridad` y dejar `docs/security-report.md`: inyección de prompts, exfiltración entre clientes, dependencias con vulnerabilidades conocidas y secretos en todo el historial, cada hallazgo con su severidad, su evidencia y el cambio que lo resolvió. Cubre las filas O.18–O.22, R.8 y la parte de historial de R.10 de `verification.md` §5 (`architecture.md` §14.7, `verification.md` §4.11).

## Alcance

- Una pasada del subagente `seguridad` sobre el checkout de V2 con el backend completo y la API en local.
- Los casos del red-team log (`verification.md` §4.9) de su alcance: inyección RT1–RT4 y RT16; exfiltración RT5–RT7, RT11 y RT13. Su columna «Resultado» queda rellena.
- Dependencias: `pip-audit` sobre el backend y `pnpm audit --prod` sobre el frontend.
- Secretos: `detect-secrets` sobre el árbol y sobre `git log -p --all`.
- El informe `docs/security-report.md`.

## Fuera de alcance

- Las defensas mismas y sus pruebas T: política y detector de inyección → 005-guardarrailes; identidad y propiedad → 002-autenticacion; MCP → 015-servidor-mcp; extracción y citas → 008-brief-y-entrevista; cambio del lector → 014-cambios-del-lector; edición manual → 019-edicion-manual.
- Los arreglos: cada hallazgo lo corrige el carril dueño del módulo, con su propia prueba (`AGENTS.md` proceso 4, un bug con su prueba que falla).
- `detect-secrets` en la CI y `guard-secretos` → 000-scaffolding.

## Comportamiento observable

Todo esta spec se ejecuta al final, con el backend completo (decisión del usuario, 2026-09-24): sus casos son D o I.

#### 021-C01 — Inyección de prompts por cada vía de texto no confiable (D)
- **Entrada:** el subagente `seguridad` recorre texto libre → extractor, petición de cambio (web y MCP) → planner en modo cambio, y texto de edición manual → editor; ejecuta las pruebas de red-team de esas vías y RT1–RT4 y RT16 contra la API en local.
- **Salida:** una fila del informe por vía, con su receptor único, el detector que la marca y la prueba que la cubre; RT1–RT4 y RT16 con su «Resultado» en `verification.md` §4.9.

#### 021-C02 — Exfiltración entre clientes y novelas (D)
- **Entrada:** el subagente recorre cada ruta de `/api`, `/view` y cada tool MCP con dos clientes de prueba; ejecuta las pruebas de propiedad y RT5–RT7, RT11 y RT13.
- **Salida:** lo ajeno responde como inexistente en cada ruta y tool; toda ruta sin prueba de propiedad es un hallazgo; RT5–RT7, RT11 y RT13 con su «Resultado».

#### 021-C03 — Dependencias con vulnerabilidades conocidas (D)
- **Entrada:** `pip-audit` en el backend y `pnpm audit --prod` en el frontend.
- **Salida:** cada vulnerabilidad es una fila del informe con su severidad y el paquete; sin ninguna, una fila «sin hallazgos» con la salida del comando.

#### 021-C04 — Secretos en todo el historial (D)
- **Entrada:** `detect-secrets` sobre el árbol (sin `.env`) y una búsqueda de los patrones de `guard-secretos` en `git log -p --all`.
- **Salida:** cada coincidencia real es un hallazgo crítico con su commit; los marcadores (`TU_CLAVE_AQUI` y similares) no cuentan.

#### 021-C05 — El informe dice qué se hizo con cada hallazgo (I)
- **Entrada:** `docs/security-report.md` tras la pasada y los arreglos.
- **Salida:** fecha, alcance, comandos ejecutados y una tabla `hallazgo · severidad · evidencia · módulo y spec dueños · cambio que lo resolvió o «abierto»`; ningún hallazgo crítico o alto queda «abierto» en la entrega.

## Invariantes

| Id | Invariante | Clase | Cómo se verifica |
|---|---|---|---|
| 021-I1 | El subagente no corrige: registra; cada arreglo lo hace el carril dueño con su prueba | I | Revisión del diff de la pasada: solo `docs/security-report.md` y la columna «Resultado» de §4.9 |
| 021-I2 | La auditoría nunca lee ni muestra `.env` | I | Comandos del informe; denegación de `.claude/settings.json` |
| 021-I3 | Las pruebas de red-team que ejecuta la auditoría no llaman a un modelo real salvo en los casos D de §4.9 que reutilizan las generaciones de 020 | I | Informe |

## Docs referenciados

- `architecture.md` §12 (guardarraíles y política), §14.3 (autenticación), §14.4 (MCP), §14.7 (auditoría de seguridad).
- `verification.md` §4.9 (red-team log), §4.11, §5 (O.18–O.22, R.8, R.10).
- Specs 000, 002, 005, 008, 014, 015, 019, 020.
