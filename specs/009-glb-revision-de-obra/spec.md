# 009 — GLB · Revisión de obra

- [ ] Spec approved   <- only the user marks this

## Objetivo

Detectar los defectos que solo existen a escala de obra y repararlos por reescritura dirigida.

## Alcance

Pase global sobre la obra terminada y reescritura dirigida.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-GLB-1 | El pase global no lee el manuscrito entero: se descompone en cuatro comprobaciones por tipo de defecto | Obligatorio | A |
| RF-GLB-2 | Hilos abiertos: consulta estructurada de `Arco` con estado abierto | Obligatorio | T |
| RF-GLB-3 | Consecuencias establecidas y nunca usadas: consulta estructurada de `Consecuencia` sin ningún vínculo de trazabilidad | Obligatorio | T |
| RF-GLB-4 | Ritmo y curva de tensión: juicio sobre la tabla de tensiones de capítulo, construida por código | Obligatorio | T, I |
| RF-GLB-5 | Deriva de voz: muestreo de tercios contrastado con el `StyleSheet` | Obligatorio | I |
| RF-GLB-6 | Repetición léxica entre escenas distantes: único uso de recuperación de todo el pase global, sobre la colección de prosa | Obligatorio | T, I |
| RF-GLB-7 | Los defectos de obra se resuelven por reescritura dirigida de escenas concretas, nunca por regeneración global | Obligatorio | T |
| RF-GLB-8 | Una escena reescrita vuelve a pasar las puertas del bucle por escena | Obligatorio | T |

## Docs de referencia

`architecture.md` §8.9; `definitions.md` §2, §5
