# Pendiente

Trabajo abierto del harness. **Para qué sirve este fichero:** el [CHANGELOG.md](CHANGELOG.md) cuenta lo que *ya se decidió y por qué*; esto cuenta lo que *falta por hacer*. Un punto sale de aquí cuando está hecho, y solo entra en el CHANGELOG si por el camino se tomó una decisión de diseño que valga la pena proteger.

Orden de trabajo propuesto: primero lo que desbloquea el harness (bloque 1), después el arrastre de la 0.8.0 (bloque 2), y al final la ejecución que mide si algo de esto sirvió (bloque 3).

---

## 1. Desbloquear el harness — **hecho el 17/09/2026**

Estaba en que ninguna novela nueva podía aprobar su escaleta. Ya no. Los cuatro puntos, implementados y verificados; el detalle y las pruebas, en el CHANGELOG 0.8.1.

- [x] **Spec §3.1** reescrita: `Write` decide **por aprobación** en `biblia.md`, `escaleta.md` y `arco-*.md`, y **por existencia** en los demás. La limitación conocida de Bash queda escrita ahí.
- [x] **`.claude/hooks/inmutables.sh`** implementa esas dos reglas leyendo el frontmatter del fichero existente. Probado a mano contra 28 casos con su código de salida.
- [x] **Spec §9.3** gana la regla 6 con las dos `deny` de credenciales.
- [x] **`.claude/settings.json`**: entran `Read(.env)` y `Read(.claude/settings.local.json)`; salen `Write(/novelas/**)` y `Write(/comparativa/**)`. El aviso de arranque ya no sale, comprobado con un control.

## 2. Arrastre de la 0.8.0

La 0.8.0 es solo spec y CHANGELOG. Falta toda la implementación.

- [ ] **`config.json`**: claves nuevas (`memoria.resumen_max_palabras`, `limites.entrada_max_palabras_invocacion`, `veredicto.rechaza_con_gravedad_1` / `_2`, `resumenes_completos_ultimos` por perfil) y subir a `version: 5`.
- [ ] **`SKILL.md` y `procedimientos/capitulo.md`**: composición de la hoja de continuidad, recuento del resumen con reinvocación única, regla de veredicto nueva.
- [ ] **`.claude/agents/resumidor.md` y `escritor.md`**: contratos nuevos.
- [ ] **`plantillas/resumen.md` y `plantillas/estado.json`**: campos `fecha_ficcion_inicio`, `fecha_ficcion_fin`, `plazos`, `objetos`.
- [ ] **`comprobar_entorno`**: proyección de entrada del último capítulo del perfil, con aviso (no parada).

### Desincronizaciones sueltas

Cuatro sitios donde un fichero contradice a otro, encontrados en la revisión del 17/09/2026. Tres arreglados; el que queda depende de esta misma versión:

- [x] `procedimientos/cierre.md`, tabla de motivos: `ESTADO_NO_RECONOCIDO` decía «no es `version: 3`». Ahora dice 4, y que 3 solo se acepta en `estado` y `verificar`.
- [x] `SKILL.md` §9, lista de inmutables: entran `informe-arco-*.md` y `libro-estado-*.md`, y la línea distingue lo que admite una escritura por versión de lo que admite una sola.
- [ ] `plantillas/informe.md`: cita `veredicto.rechaza_con_graves`. **No se toca suelto.** `config.json` y `procedimientos/capitulo.md` citan esa misma clave y los tres son coherentes; quien va por delante es la spec §7.5. Cambiar solo la plantilla dejaría tres ficheros contradiciéndose en vez de uno. Sale con el resto de este bloque, de una vez.
- [x] `.gitignore` ignora `herramientas/trazas/__pycache__/`, y `herramientas/trazas/requirements.txt` fija `langfuse==4.15.3` (la versión instalada; `exportar.py` usa `propagate_attributes`, que no existe en el SDK v2).

## 3. Medir

- [ ] **Ejecución completa con perfil `relato`** sobre el caso de referencia. Hasta que exista, el 58,4 % de la 0.8.0 es un diagnóstico, no un resultado, y no se sabe si la hoja de continuidad baja de verdad los reintentos.
- [ ] Con esa segunda ejecución se deciden dos cosas que la 0.8.0 dejó abiertas a propósito: recalibrar `pausa_cada_capitulos` (hoy 3, elegido a ojo) y si se corrige el objetivo de longitud por el sesgo medido de +10,5 %.

---

## Sin decidir

**`herramientas/comprobar.sh`.** Un guion que haga lo que la revisión del 17/09/2026 hizo a mano: que las claves `config.*` que citan la skill y los procedimientos existan en `config.json` y al revés las que declara §7; que el frontmatter de los cinco agentes coincida con `config.json` (el paso 3 de `comprobar_entorno`, pero **antes** de lanzar una novela y no después); casos de ejemplo de `inmutables.sh` con su código de salida esperado; `exportar.py --dry-run` sobre la novela de referencia; y `pnpm typecheck`. Encima, quince líneas de GitHub Actions que lo ejecuten en cada push a `JNico-rb/story-maker`.

Es lo que habría detectado el desfase entre la spec 0.8.0 y `config.json` el mismo día que apareció, en vez de en una revisión manual.

Descartado dentro de esa propuesta: framework de tests (vitest, pytest) para seis comprobaciones, cobertura de código, más linters que el `typecheck` que ya existe, matriz de versiones de Node, hook de pre-commit que bloquee commits locales, y cualquier forma de CD —no hay nada que desplegar, el producto es Markdown en una carpeta—.
