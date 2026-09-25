# Anexo E · Coste y sensibilidad extendida

> **Estimado · se sustituye por lo medido en Langfuse.** Los tokens son la única entrada estimada; al medirlos se reejecuta `uv run presentacion/costes.py` y todas las cifras se recalculan con las mismas fórmulas.

Supuestos: precios de lista de la API de Anthropic (Sonnet 5: 2 $/M de entrada y 10 $/M de salida; Haiku 4.5: 1 $ y 5 $; Opus 5.5: 4 $ y 20 $), 1 USD = 0,90 €, sobrecoste de reintentos × 1,3 y 3 revisiones incluidas. En desarrollo no se paga por token (suscripción de Claude Code); la cifra es lo que costaría en producción.

## E.1 Coste unitario (200 novelas/mes)

| Partida | €/novela |
|---|---|
| Tokens de la novela (entrevista y generación) | 2,48 |
| Tokens de las 3 revisiones incluidas (0,51 cada una) | 1,54 |
| Infraestructura (92 €/mes ÷ 200) | 0,46 |
| Pasarela de pago (1,5 % + 0,25 €) | 0,69 |
| Contingencia del 15 % sobre tokens | 0,60 |
| Soporte y operación (10 h/mes × 45 €/h ÷ 200) | 2,25 |
| **Coste unitario** | **8,02** |

Precio: **29 € IVA incluido** (23,97 € netos), con 3 revisiones; revisión extra, 2,99 €. Margen: **15,95 € por novela (67 %)**.

## E.2 Infraestructura mensual

| Partida | 50/mes | 200/mes | 500/mes |
|---|---|---|---|
| Servidor (4 vCPU, 8 GB) | 40 € | 40 € | 40 € |
| Langfuse (plan Core) | 27 € | 37 € | 64 € |
| GitHub Actions para Lean | 0 € | 0 € | 22 € |
| Dominio, correo y copias | 15 € | 15 € | 15 € |
| **Total** | **82 €** | **92 €** | **141 €** |

## E.3 Escenarios de volumen

| Novelas/mes | Ingresos netos | Coste variable | Coste fijo | Margen | % |
|---|---|---|---|---|---|
| 50 | 1.198 € | 265 € | 262 € | 671 € | 56 % |
| 200 | 4.793 € | 1.061 € | 542 € | 3.190 € | 67 % |
| 500 | 11.983 € | 2.653 € | 1.041 € | 8.289 € | 69 % |

## E.4 Sensibilidad (200 novelas/mes)

| Caso | Coste variable/novela | Margen/mes | % |
|---|---|---|---|
| Base | 5,31 € | 3.190 € | 67 % |
| Tokens +50 % | 7,62 € | 2.728 € | 57 % |
| Tokens −20 % | 4,38 € | 3.375 € | 70 % |
| 6 revisiones, las 3 extra gratis | 7,08 € | 2.836 € | 59 % |
| 6 revisiones, las 3 extra a 2,99 € | 7,08 € | 4.318 € | 69 % |
| Roles de Sonnet pasan a Opus 5.5 | 8,26 € | 2.599 € | 54 % |
| Peor caso: Opus + tokens +50 % + 6 revisiones gratis | 15,77 € | 1.098 € | 23 % |

**Lectura:**
1. **Tokens ±50 %:** el margen se mueve unos 10 puntos, pero el precio los cubre con holgura; los tokens son poco más de la mitad del coste.
2. **Más revisiones:** cada una cuesta ~0,51 € de tokens; el riesgo real es la capacidad. Con 6 revisiones, una instancia pasa de ~500 a ~350 novelas/mes. Las revisiones extra se cobran para regular la carga.
3. **Peor caso:** con los tres supuestos adversos a la vez, el margen sigue en 23 %.

## E.5 Coste del proyecto de desarrollo

| Fase | Junior (45 €/h) | Senior (110 €/h) | Coste |
|---|---|---|---|
| Diseño: docs, specs y planes | 24 h | 24 h | 3.720 € |
| Desarrollo | 32 h | 32 h | 4.960 € |
| Validación: evals, red-team, Lean, TLA+, revisión humana | 16 h | 16 h | 2.480 € |
| Despliegue (estimado, fuera del alcance) | 16 h | 4 h | 1.160 € |
| Herramientas (Claude Code y portátil amortizado) | | | 150 € |
| Subtotal | 88 h | 76 h | 12.470 € |
| Contingencia 15 % | | | 1.870 € |
| **Total** | | | **14.340 €** |

Con el margen del escenario central (3.190 €/mes), el desarrollo se amortiza en unos **4,5 meses**.

---
