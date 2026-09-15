# Informe de cierre

Se ejecuta **siempre** al terminar una ejecución de `/novela nueva` o `/novela continuar`, con ÉXITO o PARADA. Nunca terminar sin él.

## Motivos

| Motivo | Cuándo | Acción para el usuario |
|---|---|---|
| `EXITO` | Novela completa | Leer `manuscrito.md` e `informe-global.md` |
| `FALLO_TECNICO_PERSISTENTE` | Un subagente falló `reintentos_tecnicos` veces | `/novela continuar <carpeta>` |
| `INCUMPLE_CONTRATO` | Un subagente volvió sin la salida esperada, con artefactos inválidos o escribiendo fuera de zona, `reintentos_tecnicos` veces | `/novela continuar <carpeta>`; si se repite en varias novelas, revisar la definición del subagente y anotarlo en `CHANGELOG.md` |
| `ESCALETA_FUERA_LIMITES` | El interrogador no logró una escaleta dentro de límites en `escaleta_rechazos_max` vueltas | Relajar límites (`/novela continuar <carpeta> capitulos_max=…`) o ajustar la idea |
| `ERROR_CONFIGURACION` | Falla una comprobación previa (git, ficheros del harness, carpeta) | Corregir lo indicado y relanzar |
| `ESTADO_NO_RECONOCIDO` | `estado.json` no parsea o su fase es desconocida | Revisar el último commit de la carpeta indicado en el informe; no adivinar |
| `PAUSA_PROGRAMADA` | Pausa voluntaria cada `pausa_cada_capitulos` para no agotar el contexto | `/novela continuar <carpeta>` en una sesión nueva |
| `INTERRUMPIDO` | Solo se registra a posteriori, al reanudar y encontrar un paso a medias | Nada; ya se ha descartado lo a medias |

## Pasos

1. Si es PARADA: `estado.fase = parada`, `estado.ultima_parada = { motivo, fecha, detalle, fase_previa }`. Guarda `estado.json`.
2. Escribe `informe-cierre.md` desde la plantilla con: resultado, motivo, fase y capítulo/intento en que se detuvo, capítulos cerrados (y cuáles por agotamiento), invocaciones por subagente, **volumen** (suma de `palabras_entrada` y `palabras_salida` del registro, por subagente y por modelo), avisos acumulados, rutas relevantes, y la línea **Para continuar**.
3. Registra `fin_ejecucion(resultado, motivo)`.
4. Commit `novela <slug>: <EXITO | PARADA motivo>`. Si el fallo es `ERROR_CONFIGURACION` sin carpeta válida, omite los pasos 1-2 y 4 y solo muestra el informe en la sesión.
5. Muestra el informe completo en la sesión. En PARADA, la última línea es la acción exacta para continuar.
