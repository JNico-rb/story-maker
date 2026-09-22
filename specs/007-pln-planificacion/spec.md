# 007 — PLN · Planificación y puerta de factibilidad

- [ ] Spec approved   <- only the user marks this

## Objetivo

Planificar la obra y comprobar que el alcance comprometido cabe en la longitud pedida.

## Alcance

Planificación: `Outline` jerárquico y puerta de factibilidad.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-PLN-1 | El planificador produce un `Outline` jerárquico de capítulos y escenas a partir del canon, el contrato y `config` | Obligatorio | T |
| RF-PLN-2 | El outline declara la cobertura de arcos y el estado de cada `Arco` | Obligatorio | T |
| RF-PLN-3 | La puerta 0 calcula la densidad narrativa como `objetivo_palabras` entre el número de elementos estructurales **comprometidos**, y solo cuenta los derivados del `ContratoDeBrief` | Obligatorio | T, A |
| RF-PLN-4 | Por debajo de `densidad_minima`, la ejecución se bloquea con un mensaje que nombra las tres cifras: elementos comprometidos, palabras por elemento y mínimo exigido | Obligatorio | T |
| RF-PLN-5 | La puerta 0 comprueba que todo compromiso tiene cobertura en el outline; si falta alguno, vuelve a planificación | Obligatorio | T |
| RF-PLN-6 | Con cero compromisos, la puerta 0 pasa por construcción y la ejecución continúa | Obligatorio | T |
| RF-PLN-7 | La puerta 0 corre una sola vez, sobre el outline, antes de congelar la estructura, y no forma parte del bucle por escena | Obligatorio | T |
| RF-PLN-8 | Superada la puerta 0, la estructura se congela | Obligatorio | T |

## Docs de referencia

`architecture.md` §4.1, §6.3, §8.6; `definitions.md` §2
