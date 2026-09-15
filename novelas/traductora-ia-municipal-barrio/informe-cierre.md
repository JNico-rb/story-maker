---
resultado: ""          # EXITO | PARADA
motivo: ""             # EXITO | FALLO_TECNICO_PERSISTENTE | INCUMPLE_CONTRATO | ESCALETA_FUERA_LIMITES | ERROR_CONFIGURACION | ESTADO_NO_RECONOCIDO | PAUSA_PROGRAMADA
fecha: ""
fase: ""
capitulo: null
intento: null
---

# Informe de cierre — <slug>

**Resultado:** …
**Motivo:** …
**Detalle:** …

## Dónde se detuvo
Fase · capítulo · intento.

## Qué quedó completado
- Escaleta aprobada: sí/no (N capítulos)
- Capítulos cerrados: … de N (por agotamiento: …)
- Informe global: sí/no

## Invocaciones
interrogador · escritor · revisor.

## Volumen
Suma de `pal_entrada` y `pal_salida` de las filas `invocacion` del registro, por subagente y por modelo. Es el dato para estimar cuánto costaría esta misma novela con otro modelo o en el runner (`specs/functional.md` §6.6).

| subagente | modelo | invocaciones | pal_entrada | pal_salida |
|---|---|---|---|---|

## Avisos
-

## Rutas
- manuscrito.md / informe-global.md (si existen)
- último informe de capítulo relevante

**Para continuar:** `/novela continuar novelas/<slug>`
