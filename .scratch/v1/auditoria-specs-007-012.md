# Auditoría de las specs 007–012 (2026-09-23)

Fichero de trabajo temporal. Una pasada del subagente `auditor` sobre cada `spec.md`, recién escrita, contra `docs/architecture.md`. No hay filas en la matriz todavía. Se borra cuando cada diferencia esté corregida o pase a `docs/relational-matrix.md` §2 en el bucle de gap de su plan.

Las seis casillas se marcaron antes de que terminaran las auditorías. B = bloqueante, M = menor, según la propuesta del auditor.

## Transversal

- Las seis specs citan «001 design.md §12»; `design.md` se reestructuró y las tablas están en §4.3 y §4.4, y las interfaces en §5.
- 001 design §4.1: las claves son `id INTEGER PRIMARY KEY` globales, así que una copia de versión no conserva el id; 014 RF-PUB-2 dice que sí. Contradicción entre 014 y el design, que afecta a 009 RF-LEA-12.
- `chronology_files` ya no tiene `year_offset`.

## 007-run-ejecuciones (10: 7 B, 3 M) — ya tiene `plan.md` en curso

1. B · §7.5, §7.6, §9.4 · RF-RUN-22 cuenta como intento toda entrega de un rol; deben ser solo las de §7.6: entrega de texto de capítulo fuera del gate, regeneración de respaldo, planificación y ciclo del gate. Las demás sesiones cuentan por sus fallos.
2. B · §7.6, §8.2, §11.1 · Con los intentos agotados tras una denegación, un bloqueo del hook o una sesión sin entrega, el veredicto no ve bloqueantes y «acepta». Deben pasar al veredicto los defectos de la última entrega y la falta de entrega; §8.2, «salvo con los intentos agotados».
3. B · §9.1, §14.4 · Quién abre el tramo y pasa a `running` al reanudar: la API (RF-RUN-16) o el worker (RF-RUN-5). O la API solo lanza el worker, o §9.1 añade la reanudación a la API.
4. B · §10.6 · RF-RUN-36 deja sin código las acciones de la API que implementa 007: encolar, lanzar, detectar caída, marca, cancelar fuera de `running`, reanudar.
5. B · §9.2, §12.1 · Nadie abre la traza `ejecucion` al lanzar ni la continúa al reanudar (004 y 007 se lo pasan): nuevo RF con RF-OBS-3 y RF-OBS-4.
6. B · §9.1, §9.2; definitions §5, §12 · «Detalle» y motivo de `interrupted` y de `cancelled` no existen en `Ejecucion`; añadirlos al doc o quitarlos de la spec; alinear RF-RUN-28 y RF-RUN-35.
7. M · §9.1, §14.4 · La instantánea SSE añade el motivo de bloqueo y el cierre tras `finished`/`cancelled`.
8. B · §6.9, §6.10, §8.2, §13.3 · El informe (RF-RUN-33) no lista los avisos del hook ni los `missing_context` y `count_drift`, que no tienen veredicto.
9. M · §15.2 · Cifra sin valor dentro de una ejecución → `blocked` `infeasible_config`. **Decidido por el usuario; ya en `architecture.md` §15.2 y §16, falta el RF.**
10. M · §6.11 · RF-RUN-20: reanudar no reconstruye ni reincrusta el índice.

Fuera de la matriz: RF-RUN-3 cuenta la `running` en la `position` y design §4.4 no; «Docs de referencia» incompleto.

## 008-mem-memoria (15: 4 B, 11 M)

1. B · §6.11, §6.6 · RF-MEM-2 no fija el `desde_capitulo` de las tarjetas sucesoras de un cambio (015 RF-CAM-17 lo delega): el mismo que la tarjeta que sustituye, y con empate rige la última.
2. B · §7.4 · RF-MEM-31 no acota la salida de Playwright MCP ni de `Skill`: extender a toda tool en el `PostToolUse` (RF-BAS-24), o contar el cuerpo de la skill como gasto fijo.
3. B · §3.5, §9.5, §14.3 · Qué responde una sesión fuera de una ejecución que no cabe: delegación circular con 005 y 015. **Es el hueco (a) del chat central: decisión del usuario.**
4. B · §3.4, §14.3 · RF-MEM-33 y RF-MEM-34 guardan ventana y conteos aunque la sesión no se guarde (importación que falla).
5. M · §6.10, §7.6 · RF-MEM-24 y RF-MEM-32: «quien abre la sesión, el orquestador o la API».
6. M · §6.10; definitions §5 · `SesionDeRol` no tiene conteo estimado.
7. M · §6.6, §10.2, §13.4 · Corte de la prosa en el gate y para el linter de repetición al guardar y en vivo.
8. M · §6.4, §14.2 · Consulta del editor en un cambio o propagación: hechos cambiados con su valor antiguo.
9. M · §10.4 inv. 7 · Trazabilidad de un capítulo editado a mano, sin sesión.
10. M · §6.11 · Reanudar no reincrusta (RF-MEM-5).
11. M · §6.3 · Hechos de mundo en la tarjeta del novum y hechos de lugar en la suya: precisión o doc.
12. M · §6.9 · Constante de RRF sin declarar.
13. M · §6.4 · «titulares» frente a «títulos».
14. M · definitions §3 · RF-MEM-3: «cada bloque separado por una línea en blanco».
15. M · §14.5 · Referencia a design.

Fuera de la matriz: orden de recorte dentro de la prosa; `MATCH` como disyunción de las palabras de la consulta.

## 009-lea-validador-formal-de-la-historia (8: 6 B, 2 M)

1. M · §4.2, §4.3 · Los antecedentes vienen de `submit_world`, no del outline.
2. B · §10.5, §9.3, §14.5 · «que una versión conserva al copiarse»: el design ya no lo hace; quitarlo o decidirlo con 014 RF-PUB-2.
3. B · §10.5, §14.5 · El desplazamiento no se guarda (no hay columna ni atributo): no guardarlo, porque el testigo se traduce por ids.
4. B · §10.5, §12.5 · La traducción con fechas reales filtra fechas de nacimiento sin máscara: quitar las fechas.
5. B · §12.3, §12.5 · El comentario del score con nombres canónicos: llevar solo invariante, ids, capítulo y beat.
6. M · §10.2, §10.3 · Declarar método, origen, dimensión y nivel del criterio, familia y puntos.
7. B · §4.3 · Lo cubren 010 y 011: solo registrar en §1.
8. B · §4.3 · «Los que no son analepsis ocurren en el año presente»: ninguna spec lo entrega; 010 (schema o prompt) y 011.

Fuera de la matriz: personajes y lugares de `submit_cast` tampoco tienen fila al congelar (ampliar la aclaración de ids de la propuesta); qué devuelve el verificador si el fichero no compila por otra causa o el workflow no deja artefacto; el JSON debe listar todos los invariantes violados.

## 010-pln-planificacion (15: 4 B, 11 M)

1. B · §4.2 · Un tropo pedido en un deseo no entra en la lista de evitación del planner.
2. B · §4.3 · Eventos de beat no analépticos en el año presente (= 009-8).
3. B · §7.4, §7.6, §5.2 · Dentro de una planificación, ¿un fallo de schema o una denegación es un intento? Declarar, como en el gate, que el intento es la planificación entera, y alinear RF-RUN-24.
4. B · §10.2, §12.3 · `grafo-causal`, `outline` y `cronologia-lean` no dicen que envían sus scores.
5. M · §4.2 · Preferir predicados detectables (prompt).
6. M · §4.3 · El beat analéptico referencia el evento que narra.
7. M · §4.3 · Antecedentes y eventos de beat entran en la cronología como planificados.
8. M · §5.2 · Lean no corre si `outline` falla: doc o aceptada.
9. M · §9.2 · El canon del brief se conserva al reanudar: doc.
10. M · §5.3, §11.1, §10.3 · Nivel de los temas prohibidos del léxico a evitar frente a los «temas del brief» de `tema-prohibido`.
11. M · domain §4.5 · Un deseo inadecuado para la edad se adapta a la franja.
12. M · §7.3 · Falta un RF del prompt del planner.
13. M · §14.5 · Restricción con su enunciado y lo que la define.
14. M · §4.1 · Personajes y lugares inventados con su hecho de nombre.
15. M · §4.2 · La compatibilidad del novum la juzga `tono` (011, 014).

## 011-cap-produccion-por-capitulo (17: 4 B, 13 M)

1. B · §8.2 · RF-CAP-18: «intentos agotados **del evaluable capítulo**»; si no, agotar la regeneración de respaldo nunca escala.
2. B · §7.2, §8.3, §4.3 · El registrador no recibe los beats del capítulo, con su marco y su evento: doc §7.2 y RF-CAP-21.
3. B · §8.3 · El delta real no lleva «cambios de hechos» en §8.3 aunque §6.4, §9.6 y `DeltaDeEstado` sí: doc y RF-CAP-21.
4. B · §8.3 · El reemplazo de un registro repetido no incluye los sucesores de hechos cambiados: doc y RF-CAP-24.
5. M · §8.3, §9.2 · ¿Volver a registrar inserta otro `PuntoDeControl`? En el gate no; en un cambio o una edición sí.
6. M · §8.2, §13.3 · Los avisos del hook sí llegan al editor: precisar que no llegan al veredicto solo los bloqueantes del hook.
7. M · §7.2, §9.4, §9.5 · RF-CAP-20: vuelve al crítico solo en `chapter_production`.
8. M · §7.1 · El crítico, sesión de un turno.
9. M · §10.2, §4.3 · El delta declarado lleva personajes y lugares nuevos.
10. M · §10.3 · Declarar en el catálogo `longitud-capitulo` y `nombres-exactos`.
11. M · §4.2 · `prohibido`: «toma ese valor en ese atributo».
12. M · §10.3 · RF-CAP-17: limitarlo a `no-cliche`.
13. M · §10.2 · «variante cercana» frente a «misma forma normalizada»: doc.
14. M · §11.1 · RF-CAP-10: citar RF-POL-1, sin variantes de número y género.
15. M · §8.2 · Ninguna fila da el veredicto `re_record`: doc.
16. M · §14.5 · Referencia a design.
17. M · README · Citar README y `workflow/4-code.md` en Docs de referencia.

Hueco sin fila: ¿bloquea un defecto tipado del crítico cuando su criterio puntúa por encima del umbral?

## 012-lin-linters-de-prosa (12: 3 B, 9 M)

1. B · §9.6, §10.2 · §10.2 pone los linters en la edición manual, pero §9.6 no los corre al guardar. Quitar «edición manual» de la fila de los linters en §10.2, o añadirlos al guardado en §9.6 y en 015.
2. B · §14.2 · `lint` solo importa `domain`: los linters no envían scores ni recuperan prosa. Funciones puras; recuperar (008) y enviar (004) lo hace quien los invoca (011, 015). Ajustar «Depende de».
3. B · §13.3 · RF-LIN-14 con narrador en primera persona cuenta como defecto cada verbo en tercera: redefinir la métrica.
4. M · §13.3 · Fijar *n* y «distintivo» de los n-gramas como constantes de `domain`.
5. M · §13.3 · Lista de muletillas en `domain`: doc o aceptada.
6. M · §13.3 · Causa raíz `style_drift`: doc o aceptada.
7. M · §13.3, §11.1 · Normalización de 003; añadir 003 a «Depende de».
8. M · §6.6 · Corte de la prosa del linter fuera de la producción.
9. M · §13.3 · Regla determinista de hablante y destinatario; un par sin tratamiento fijado.
10. M · §13.3 · Incisos del narrador: doc o aceptada.
11. M · §15.2 · `readability_targets` sin valor, como los umbrales.
12. M · §10.3 · Nivel, dimensión y origen de los diez criterios.
