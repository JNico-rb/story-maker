# Pendiente

Trabajo abierto del harness. **Para qué sirve este fichero:** el [CHANGELOG.md](CHANGELOG.md) cuenta lo que *ya se decidió y por qué*; esto cuenta lo que *falta por hacer*. Un punto sale de aquí cuando está hecho, y solo entra en el CHANGELOG si por el camino se tomó una decisión de diseño que valga la pena proteger.

Orden de trabajo propuesto: primero lo que desbloquea el harness (bloque 1), después el arrastre de la 0.8.0 (bloque 2), y al final la ejecución que mide si algo de esto sirvió (bloque 3).

---

## 1. Desbloquear el harness

Ninguna novela nueva puede aprobar su escaleta hasta que esto esté. Diagnóstico completo en el CHANGELOG 0.8.1.

- [ ] **Reescribir spec §3.1** con la regla nueva del hook (decidir por frontmatter aprobado, no por existencia). Va antes que el código, por la regla 6 de CLAUDE.md.
- [ ] **`.claude/hooks/inmutables.sh`**: para `biblia.md`, `escaleta.md` y `arco-AA.md`, mirar `aprobada: true` / `validada: true` en el frontmatter del fichero existente. El resto sigue con la regla de existencia.
- [ ] **Reescribir spec §9.3** con las dos reglas `deny` de credenciales.
- [ ] **`.claude/settings.json`**: quitar `Write(/novelas/**)` y `Write(/comparativa/**)`, que Claude Code acepta y nunca consulta.

## 2. Arrastre de la 0.8.0

La 0.8.0 es solo spec y CHANGELOG. Falta toda la implementación.

- [ ] **`config.json`**: claves nuevas (`memoria.resumen_max_palabras`, `limites.entrada_max_palabras_invocacion`, `veredicto.rechaza_con_gravedad_1` / `_2`, `resumenes_completos_ultimos` por perfil) y subir a `version: 5`.
- [ ] **`SKILL.md` y `procedimientos/capitulo.md`**: composición de la hoja de continuidad, recuento del resumen con reinvocación única, regla de veredicto nueva.
- [ ] **`.claude/agents/resumidor.md` y `escritor.md`**: contratos nuevos.
- [ ] **`plantillas/resumen.md` y `plantillas/estado.json`**: campos `fecha_ficcion_inicio`, `fecha_ficcion_fin`, `plazos`, `objetos`.
- [ ] **`comprobar_entorno`**: proyección de entrada del último capítulo del perfil, con aviso (no parada).

### Desincronizaciones sueltas

Cuatro sitios donde un fichero contradice a otro, encontrados en la revisión del 17/09/2026 y aún sin arreglar:

- [ ] `procedimientos/cierre.md`, tabla de motivos: `ESTADO_NO_RECONOCIDO` dice «no es `version: 3`»; `SKILL.md` §1 dice 4. Quedó de la 0.5.x.
- [ ] `SKILL.md` §9, lista de inmutables: faltan `informe-arco-*.md` y `libro-estado-*.md`, que sí están en spec §3.1 y en el hook.
- [ ] `plantillas/informe.md`: cita `veredicto.rechaza_con_graves`, la clave que la 0.8.0 parte en dos.
- [ ] `.gitignore`: falta `herramientas/trazas/__pycache__/` (ya hay un `.pyc` sin ignorar). Y `exportar.py` importa `langfuse` sin fichero de dependencias: falta `herramientas/trazas/requirements.txt` con la versión fijada.

## 3. Medir

- [ ] **Ejecución completa con perfil `relato`** sobre el caso de referencia. Hasta que exista, el 58,4 % de la 0.8.0 es un diagnóstico, no un resultado, y no se sabe si la hoja de continuidad baja de verdad los reintentos.
- [ ] Con esa segunda ejecución se deciden dos cosas que la 0.8.0 dejó abiertas a propósito: recalibrar `pausa_cada_capitulos` (hoy 3, elegido a ojo) y si se corrige el objetivo de longitud por el sesgo medido de +10,5 %.

---

## Sin decidir

**`herramientas/comprobar.sh`.** Un guion que haga lo que la revisión del 17/09/2026 hizo a mano: que las claves `config.*` que citan la skill y los procedimientos existan en `config.json` y al revés las que declara §7; que el frontmatter de los cinco agentes coincida con `config.json` (el paso 3 de `comprobar_entorno`, pero **antes** de lanzar una novela y no después); casos de ejemplo de `inmutables.sh` con su código de salida esperado; `exportar.py --dry-run` sobre la novela de referencia; y `pnpm typecheck`. Encima, quince líneas de GitHub Actions que lo ejecuten en cada push a `JNico-rb/story-maker`.

Es lo que habría detectado el desfase entre la spec 0.8.0 y `config.json` el mismo día que apareció, en vez de en una revisión manual.

Descartado dentro de esa propuesta: framework de tests (vitest, pytest) para seis comprobaciones, cobertura de código, más linters que el `typecheck` que ya existe, matriz de versiones de Node, hook de pre-commit que bloquee commits locales, y cualquier forma de CD —no hay nada que desplegar, el producto es Markdown en una carpeta—.
