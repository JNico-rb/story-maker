---
caso: "caso-01-opus-vs-haiku"
fecha: "2026-09-18"
tipo: "modelo-caro-vs-barato"
referencia: "pruebas/referencia"
lado_a: "novelas/tecnica-ascensores-peticion-ia"
lado_b: "novelas/tecnica-ascensores-peticion-ia-20260916-1719"
---

# Caso 01 — Los cinco agentes en `opus` frente a los cinco en `haiku`

## Qué se compara y por qué

El paso 2 del plan de escalado (`specs/functional.md` §7.8) pregunta si el modelo barato basta.
Estas son las dos únicas ejecuciones completas del perfil `relato` sobre el caso de referencia:
la línea base con todos los agentes en `opus` y la primera con todos en `haiku`.
Si `haiku` pasara los mismos umbrales de `calidad` y se leyera igual de bien, sería la
configuración del paso 2.

## Lados

| | A | B |
|---|---|---|
| Carpeta | `novelas/tecnica-ascensores-peticion-ia` | `novelas/tecnica-ascensores-peticion-ia-20260916-1719` |
| Generado por | Claude Code | Claude Code |
| Fecha de ejecución | 2026-09-16 10:38 → 2026-09-16 (tarde) | 2026-09-16 17:19 → 2026-09-17 |
| Qué difiere en `config.json` | `modelos.* = opus`, escalado off, `version: 3` | `modelos.* = haiku`, escalado off, `version: 4` |

## Diferencias respecto al caso de referencia

Ninguna. `idea.md` y `entrevista.md` son idénticos byte a byte en las dos carpetas
(md5 `32de1e69…` y `b16a90c9…`). `perfil` y `formato` idénticos.

## Advertencia: el modelo no es la única variable

**Este caso no aísla el modelo.** A se ejecutó con la spec v3 y B con la v4, y entre las dos
cambiaron tres reglas del harness que afectan justo a lo que se mide (§8.5):

1. **Revisión partida.** A tuvo un revisor único con los cinco criterios; B tuvo
   revisor de encargo y revisor de continuidad por separado.
2. **Ajustes de longitud con presupuesto propio.** En A un rechazo por longitud consumía
   reescritura (y es la causa directa del defecto del capítulo 3); en B no.
3. **Umbrales de `calidad` recalibrados.** B los tiene relajados respecto a A
   (`max_graves_por_10`: 1 → 2; `max_agotamiento_pct`: 10 → 20;
   `min_aprobados_primer_intento_pct`: 60 → 40; `max_rechazos_voz_pct`: 10 → 20).

Las reglas 1 y 2 favorecen a B por diseño, y la 3 hace que la columna CUMPLE / NO CUMPLE
no sea comparable tal cual. `comparacion.md` evalúa además a B contra los umbrales de A.
Este caso vale como lo que es —las dos únicas ejecuciones completas que existen— y no como
un experimento controlado. Lo controlado exige relanzar A con la spec v4.
