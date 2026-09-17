# cerrar — informe de cierre

Implementa `cerrar(carpeta, resultado, motivo, detalle | metricas)` de SKILL.md §3. Se ejecuta **siempre** al terminar una ejecución de `/novela nueva` o `/novela continuar`, con ÉXITO o PARADA. Nunca termines sin él.

## Motivos

| Motivo | Cuándo | Acción para el usuario |
|---|---|---|
| `EXITO` | Novela completa, revisión global hecha, métricas calculadas | Leer `manuscrito.md` e `informe-global.md` |
| `FALLO_TECNICO_PERSISTENTE` | Un agente falló `reintentos_tecnicos` veces | `/novela continuar <carpeta>` |
| `INCUMPLE_CONTRATO` | Un agente devolvió `reintentos_tecnicos` veces una salida sin la forma esperada, fuera de límites, o agotó sus turnos | `/novela continuar <carpeta>`; si se repite en varias novelas, revisar la definición del agente y anotarlo en `CHANGELOG.md` |
| `ESCALETA_FUERA_LIMITES` | `resolver_perfil` calculó desde `paginas_objetivo` un número de capítulos fuera de rango | Ajustar el perfil o los límites y relanzar |
| `ERROR_CONFIGURACION` | Falla una comprobación de `comprobar_entorno` (git, `config.json`, agentes, `maxTurns`, carpeta) | Corregir lo indicado y relanzar |
| `ESTADO_NO_RECONOCIDO` | `estado.json` no parsea, no es `version: 4` (ni `3` en `estado` y `verificar`, los dos modos de solo lectura) o su etapa es desconocida | Revisar el último commit de la carpeta indicado en el informe; no adivinar |
| `PRESUPUESTO_AGOTADO` | Hito 2 solo: coste acumulado > `limites.presupuesto_usd_max` | Subir el presupuesto y relanzar |
| `PAUSA_PROGRAMADA` | Cada `limites.pausa_cada_capitulos` capítulos cerrados, para no agotar el contexto de la sesión | `/novela continuar <carpeta>` en una sesión nueva |
| `INTERRUMPIDO` | Solo se registra a posteriori, al reanudar y encontrar un paso a medias | Nada; ya se ha descartado lo a medias |

## Pasos

1. Si es PARADA: `estado.etapa_previa = estado.etapa`; `estado.etapa = parada`; `estado.ultima_parada = { motivo, fecha, detalle, etapa_previa, arco, capitulo, intento }`. Guarda.
2. Escribe `informe-cierre.md` desde la plantilla con: resultado, motivo, detalle; etapa, arco, capítulo e intento en que se detuvo; qué quedó completado (escaleta aprobada, arcos detallados y revisados, capítulos cerrados y cuáles por agotamiento, informe global); invocaciones por agente; **volumen** por agente y por modelo (suma de `pal_entrada`, `pal_salida` y, si las hay, `tok_*` y `coste_usd` de las filas `invocacion` del registro); **métricas de calidad** (tabla de `calcular_metricas`, solo en ÉXITO); avisos acumulados; rutas relevantes; y la línea **Para continuar** con la acción exacta.
3. En ÉXITO, comprueba la carpeta contra `specs/inventario.md` §4 y anota en el informe cualquier artefacto que falte.
4. Registra `fin_ejecucion(resultado, motivo)`.
5. Commit `novela <slug>: <EXITO | PARADA <motivo>>`. Si es `ERROR_CONFIGURACION` sin carpeta válida, omite los pasos 1, 2 y 5 y solo muestra el informe en la sesión.
6. Muestra el informe completo en la sesión. En PARADA, la última línea es la acción exacta para continuar, copiada de la columna «Acción para el usuario» de la tabla de motivos: en `PAUSA_PROGRAMADA` incluye **«en una sesión nueva»**, que es lo que hace que la pausa sirva de algo. Y ahí terminas: no ejecutes tú esa acción.
