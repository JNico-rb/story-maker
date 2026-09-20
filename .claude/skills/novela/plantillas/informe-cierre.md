---
resultado: ""          # EXITO | PARADA
motivo: ""             # EXITO | FALLO_TECNICO_PERSISTENTE | INCUMPLE_CONTRATO | ESCALETA_FUERA_LIMITES | ERROR_CONFIGURACION | ESTADO_NO_RECONOCIDO | PRESUPUESTO_AGOTADO | PAUSA_PROGRAMADA
fecha: ""
etapa: ""
arco: null
capitulo: null
intento: null
cumple_todas: null     # solo en EXITO: true si todas las métricas cumplen su umbral
---

# Informe de cierre — <slug>

**Resultado:** …
**Motivo:** …
**Detalle:** …

## Dónde se detuvo
Etapa · arco · capítulo · intento.

## Qué quedó completado
- Escaleta aprobada: sí/no (N capítulos en A arcos)
- Arcos detallados / revisados: … / …
- Capítulos cerrados: … de N (por agotamiento: …)
- Informe global: sí/no (base: manuscrito | resúmenes)

## Invocaciones
interrogador · escritor · resumidor · revisor-encargo · revisor-continuidad. Reintentos técnicos: … Discrepancias de veredicto: … Rechazos por longitud: …

## Volumen
Suma de las filas `invocacion` del registro, por agente y por modelo (`specs/functional.md` §6.6).

| agente | modelo | invocaciones | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd |
|---|---|---|---|---|---|---|---|

## Métricas de calidad
Solo en ÉXITO (`procedimientos/final.md` › calcular_metricas; umbrales en `config.calidad`).

| métrica | valor | umbral | resultado |
|---|---|---|---|
| graves_por_10 | | | CUMPLE / NO CUMPLE |
| agotamiento_pct | | | |
| hilos_sin_cerrar | | | |
| primer_intento_pct | | | |
| rechazos_voz_pct | | | |
| desviacion_longitud | | informativa | – |

## Avisos
-

## Inventario
Solo en ÉXITO: artefactos de `specs/functional.md` §8.7 que faltan, o "completo".

## Rutas
- `manuscrito.md` / `informe-global.md` (si existen)
- `registro.md`
- último informe de capítulo relevante

**Para continuar:** la acción de la tabla de motivos de `procedimientos/cierre.md` — normalmente `/novela continuar novelas/<slug>`, en `PAUSA_PROGRAMADA` **en una sesión nueva**, o "nada que continuar"
