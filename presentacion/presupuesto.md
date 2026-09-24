# Presupuesto y coste — borrador de la slide

Fuente de la slide obligatoria de presupuesto (`project-constraints.md`, «Slide de presupuesto y coste»). Es un borrador: **el coste de tokens es una estimación** hasta que se mida sobre ejecuciones reales (uso registrado por la spec 004-observabilidad; ejecuciones de la 020-evals); entonces se sustituyen las filas marcadas con ⚠ y se recalcula el resto con las mismas fórmulas.

Moneda: euros, con 1 USD = 0,90 € (supuesto; se fija el tipo del día al cerrar la slide). Precios de modelo: precio de lista de la API de Anthropic, los de `operation.pricing` en `config.json` (`architecture.md` §13.2 y §15.4). Con el login de Claude Code no se paga por token: la cifra es lo que costaría la novela en producción.

---

## 1. Supuestos

| Supuesto | Valor | Por qué |
|---|---|---|
| Modelo de los roles que escriben y juzgan (entrevistador, planner, writer, editor, juez) | `claude-sonnet-5`: 2 $/M de entrada, 10 $/M de salida, 0,20 $/M de lectura de caché y 2,50 $/M de escritura de caché | El modelo de cada rol aún no está fijado (`architecture.md` §15.2) |
| Modelo de los roles que extraen o navegan (extractor, revisor visual) | `claude-haiku-4-5`: 1 / 5 / 0,10 / 1,25 $/M | Tareas de comprensión, no de escritura |
| Reparto de la entrada | 35 % nueva, 50 % leída de caché y 15 % escrita en caché | Cada turno del Agent SDK reenvía el prompt de sistema y los turnos anteriores |
| Sobrecoste por reintentos y replanificaciones | × 1,3 | Hasta medirlo en los datos de ejecución |
| Revisiones incluidas en el precio | 3 por novela | El encargo pide la sensibilidad a «más de tres» |
| Duración de una generación y de una revisión | ~30 min y ~10 min | Sin medir; sale de la latencia por novela en Langfuse |

**Volumen de tokens estimado** (miles):

| | Entrada Sonnet | Salida Sonnet | Entrada Haiku | Salida Haiku |
|---|---|---|---|---|
| Novela: entrevista, planificación, 10 capítulos y gate | 792 | 82,5 | 360 | 30 |
| Revisión: interpretación, 3 capítulos afectados y gate | 92 | 7,5 | 287 | 17,5 |

El revisor visual es la partida mayor de Haiku (~260k por gate): recorre los 10 capítulos, la ficha y la portada y sigue cada enlace.

---

## 2. Coste unitario por novela

Calculado en el escenario central, de 200 novelas al mes.

| Partida | €/novela |
|---|---|
| ⚠ Tokens de la novela (entrevista y generación) | 2,48 |
| ⚠ Tokens de las 3 revisiones incluidas (0,51 cada una) | 1,53 |
| Infraestructura (92 €/mes ÷ 200) | 0,46 |
| Margen operativo: pasarela de pago (1,5 % + 0,25 €) | 0,69 |
| Margen operativo: contingencia del 15 % sobre tokens | 0,60 |
| Margen operativo: soporte y operación (10 h/mes × 45 €/h ÷ 200) | 2,25 |
| **Coste unitario** | **8,01** |

**Infraestructura mensual**:

| Partida | 50/mes | 200/mes | 500/mes |
|---|---|---|---|
| Servidor (4 vCPU, 8 GB: API, worker, Edge/Playwright, spaCy, incrustaciones) | 40 | 40 | 40 |
| Langfuse (plan Core, ~800 unidades por novela y ~150 por revisión) | 27 | 37 | 64 |
| GitHub Actions para Lean (~4 min por novela, ~2 por revisión) | 0 | 0 | 22 |
| Dominio, correo transaccional y copias de seguridad | 15 | 15 | 15 |
| **Total** | **82** | **92** | **141** |

Unsure: las tarifas de Langfuse, de GitHub Actions y del servidor son las públicas de referencia; se confirman antes de presentar.

---

## 3. Precio de venta y margen

- **Precio de venta al cliente final: 29 € IVA incluido**, que son 23,97 € netos, con 3 revisiones incluidas. Cada revisión extra, 2,99 €.
- **Referencia:** un libro personalizado impreso para regalo se vende entre 30 y 45 €. Este producto es digital (web y PDF), sin impresión ni envío, y se puede corregir después de entregado.
- **Margen:** 23,97 − 8,01 = **15,96 € por novela (67 %)**.

---

## 4. Coste del proyecto de desarrollo

9 días laborables × 8 h = 72 h por persona, y dos personas a jornada completa.

| Perfil | Tarifa | De dónde sale |
|---|---|---|
| Ingeniero de IA junior | 45 €/h | Bruto ~30.000 €/año × 1,32 de coste de empresa ÷ 1.760 h ≈ 22,5 €/h de coste; una consultora factura ~× 2 |
| Experta senior en harness engineering | 110 €/h | Rango de consultoría senior en IA, 90–130 €/h. Equivale a unos 4.400 € por semana de 40 h facturables |

| Fase | Junior | Experta | Coste |
|---|---|---|---|
| Diseño: docs, specs y planes | 24 h | 24 h | 3.720 € |
| Desarrollo | 32 h | 32 h | 4.960 € |
| Validación: evals, red-team, Lean, TLA+ y revisión humana | 16 h | 16 h | 2.480 € |
| Despliegue (fuera del alcance del proyecto; estimado) | 16 h | 4 h | 1.160 € |
| Herramientas: Claude Code Enterprise (~140 €/mes por puesto × 0,43 meses), portátil amortizado (los roles corren con la suscripción: 0 € de API en desarrollo y evals) | | | 150 € |
| **Subtotal** | **88 h** | **76 h** | **12.470 €** |
| Contingencia (15 %) | | | 1.870 € |
| **Total** | | | **14.340 €** |

Con el margen del escenario central, 3.190 € al mes, el desarrollo se amortiza en unos **4,5 meses**.

Unsure: el precio del puesto de Claude Code Enterprise (sale de la factura de la empresa).

---

## 5. Escenarios de volumen

Con 3 revisiones por novela.

| Novelas/mes | Ingresos netos | Coste variable | Coste fijo (infraestructura + soporte) | Margen | % |
|---|---|---|---|---|---|
| 50 | 1.198 € | 265 € | 262 € (82 + 4 h) | 671 € | 56 % |
| 200 | 4.793 € | 1.061 € | 542 € (92 + 10 h) | 3.190 € | 67 % |
| 500 | 11.983 € | 2.653 € | 1.041 € (141 + 20 h) | 8.289 € | 69 % |

**El límite es la capacidad, no el coste.** Solo hay una ejecución activa en todo el servidor (`architecture.md` §9.1). 500 novelas con 3 revisiones cada una son ~500 h de ejecución al mes, que es el uso realista de una instancia. Por encima hace falta una segunda instancia, y es una decisión del cliente.

---

## 6. Análisis de sensibilidad

Margen en el escenario central, 200 novelas al mes:

| Caso | Coste variable/novela | Margen/mes | % |
|---|---|---|---|
| Base | 5,31 € | 3.190 € | 67 % |
| Precio de los tokens +50 % | 7,62 € | 2.728 € | 57 % |
| 6 revisiones por novela, las 3 extra gratis | 7,08 € | 2.836 € | 59 % |
| 6 revisiones, las 3 extra cobradas a 2,99 € | 7,08 € | 4.318 € | 69 % |
| Tokens +50 % y 6 revisiones gratis (peor caso) | 10,28 € | 2.196 € | 46 % |
| Todos los roles de Sonnet pasan a Opus 5.5 (4 $/20 $): 4,53 € por novela y 0,73 € por revisión | 8,41 € | 2.570 € | 54 % |

- **Precio de los tokens +50 %:** el margen baja unos 10 puntos, pero el precio sigue cubriéndolo con holgura. Los tokens son la mitad del coste unitario.
- **Más de tres revisiones:** cada revisión cuesta ~0,51 € de tokens, así que el coste casi no se mueve. El riesgo real es la capacidad: 6 revisiones por novela a 500/mes son ~750 h, y eso no cabe en una instancia; el techo baja a ~350 novelas al mes. Por eso las revisiones extra se cobran, aunque sea poco: más que cubrir su coste, sirven para regular la carga.

---

## 7. Qué se mide antes de cerrar la slide

1. El coste real por novela y por revisión, en Langfuse (specs 004 y 020): uso real × precio de lista; `total_cost_usd` del SDK, solo como contraste (`architecture.md` §13.2).
2. La duración de una generación y de una revisión, que fija la capacidad.
3. Los modelos elegidos para cada rol (`architecture.md` §15.2).
4. Las tarifas de Langfuse, GitHub Actions, servidor y Claude Code Enterprise.
