# Calibración de `recall_revisor`

Requisito 2 del TRIGGER (spec §9.5.1): antes de usar una métrica para decidir, hay que saber **cuánto se equivoca**. Si no, una variante puede "mejorar" 0,10 y ser ruido del emparejador.

- **Conjunto**: `ascensores-v1` (9 casos, 32 defectos puntuables para `revisor-encargo`).
- **Material**: los 9 informes de la vuelta 0 de `optimizaciones/revisor-encargo-20260918-1600/`, con el prompt de producción.
- **Método**: para cada uno de los 32 defectos etiquetados se comparó lo que dice el emparejador (¿aparece la cita esperada, normalizada, en algún campo del informe?) con la lectura a mano del informe (¿detectó el revisor ese defecto, lo diga como lo diga?).

## Resultado

| | El revisor **sí** lo detectó | El revisor **no** lo detectó |
|---|---:|---:|
| El emparejador dice **visto** | 14 | 0 |
| El emparejador dice **no visto** | 1 | 17 |

- **Exactitud: 31/32 = 0,969.**
- **Falsos positivos: 0.** El emparejador nunca dio por visto un defecto que el revisor no hubiera detectado.
- **Falsos negativos: 1** (3,1 %).

## El único fallo, y por qué importa

`b-cap-05`, defecto `hilo-cerrado-antes`, cita esperada *«el lector no sabe qué hará exactamente ni si funcionará»*. El revisor **sí** lo detectó, y bien —«Adelanta el resultado de la acción […] La entrada 5 manda que el lector no sepa si logrará reparar»—, pero lo dijo con sus palabras en vez de citar la escaleta. El emparejador, que busca la cadena literal, no lo vio.

De ahí la propiedad que hay que tener presente al leer cualquier número de este evaluador:

> **`recall_revisor` mide «lo mencionó citando la escaleta», no «lo detectó».** Es un límite inferior del recall real.

Consecuencias prácticas:

1. El sesgo es **conservador y en una sola dirección**: el valor real nunca es peor que el medido. Una mejora medida es una mejora real; una no-mejora medida puede ser una mejora invisible.
2. Es **optimizable por la vía equivocada**: un prompt que obligue al revisor a citar literalmente la entrada de escaleta subiría la métrica sin mejorar la detección. Es un riesgo real de este bucle y hay que mirarlo en los informes, no solo en la curva.
3. Con 32 defectos, un falso negativo vale 0,031. El umbral de aceptación de 0,10 está por encima de ese ruido, pero solo por tres veces.

## Cuándo hay que rehacer esta calibración

Cuando cambie el conjunto, cuando cambie `_normalizar` o el emparejamiento de `recall_revisor.py`, o cuando el contrato de §5.6 gane el campo `cita` obligatorio (A4): eso último cambiaría el material de entrada del emparejador y, con él, estos números.
