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
| `PRESUPUESTO_AGOTADO` | Hito 2 solo: coste acumulado > `limites.presupuesto_usd_max`. Con suscripción de Claude Code no hay coste por llamada y este motivo no se da | Subir el presupuesto y relanzar |
| `LIMITE_DE_USO` | El proveedor rechaza la invocación por cuota de suscripción agotada (spec §6.5). No consume reintentos técnicos: el paso en curso se descarta entero | Esperar al reinicio de la cuota (la hora va en el detalle si el error la trae) y `/novela continuar <carpeta>` |
| `PAUSA_PROGRAMADA` | Cada `limites.pausa_cada_capitulos` capítulos cerrados, para no agotar el contexto de la sesión | `/novela continuar <carpeta>` en una sesión nueva |
| `ESPERA_APROBACION` | La propuesta está lista y **no hay usuario en la sesión** a quien preguntar: se lanzó desde el estudio (spec §9.4) o sin interfaz. `biblia.md` y `escaleta.md` quedan escritas **sin** `aprobada: true` | Leer la propuesta y aprobarla o pedir cambios, y después `/novela continuar <carpeta>`. Desde el estudio, con sus botones; a mano, escribiendo la decisión en `decision.md` (ver `interrogatorio.md`) |
| `INTERRUMPIDO` | Solo se registra a posteriori, al reanudar y encontrar un paso a medias | Nada; ya se ha descartado lo a medias |

## Pasos

1. Si es PARADA: `estado.etapa_previa = estado.etapa`; `estado.etapa = parada`; `estado.ultima_parada = { motivo, fecha, detalle, etapa_previa, arco, capitulo, intento }`. Guarda.
2. Escribe `informe-cierre.md` desde la plantilla con: resultado, motivo, detalle; etapa, arco, capítulo e intento en que se detuvo; qué quedó completado (escaleta aprobada, arcos detallados y revisados, capítulos cerrados y cuáles por agotamiento, informe global); invocaciones por agente; **volumen** por agente y por modelo (suma de `pal_entrada`, `pal_salida` y, si las hay, `tok_*` y `coste_usd` de las filas `invocacion` del registro); **métricas de calidad** (tabla de `calcular_metricas`, solo en ÉXITO); avisos acumulados; rutas relevantes; y la línea **Para continuar** con la acción exacta.
3. En ÉXITO, comprueba la carpeta contra `specs/functional.md` §8.7 y anota en el informe cualquier artefacto que falte.
4. Registra `fin_ejecucion(resultado, motivo)`.
5. `commitear(carpeta, "<EXITO | PARADA <motivo>>")`, **con una excepción: aquí `commitear` no para**. Es el único punto donde su comprobación no puede disparar una PARADA, porque `cerrar()` ya es el final del camino y llamarse a sí mismo sería un bucle. Si el commit no se crea o la carpeta no queda limpia, anótalo en el informe como aviso (`"el cierre no pudo commitearse: <salida de git status>"`) y termina igualmente: el informe mostrado en sesión vale más que un cierre que no acaba. Si es `ERROR_CONFIGURACION` sin carpeta válida, omite los pasos 1, 2 y 5 y solo muestra el informe en la sesión.
6. Muestra el informe completo en la sesión. En PARADA, la última línea es la acción exacta para continuar, copiada de la columna «Acción para el usuario» de la tabla de motivos: en `PAUSA_PROGRAMADA` incluye **«en una sesión nueva»**, que es lo que hace que la pausa sirva de algo. Y ahí terminas: no ejecutes tú esa acción.
