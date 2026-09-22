# 005 — BRF · Extracción del contrato de brief

- [ ] Spec approved   <- only the user marks this

## Objetivo

Convertir prosa libre en un contrato de compromisos y huecos declarados.

## Alcance

Extracción del `ContratoDeBrief` desde el prompt, con verificación de ida y vuelta.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BRF-1 | El sistema deriva del prompt un `ContratoDeBrief` con sus `Compromiso`s, sus `Hueco`s y un grado de libertad entre 0 y 1 | Obligatorio | T |
| RF-BRF-2 | Cada `Compromiso` declara dureza —inviolable o preferencia— y si es verificable | Obligatorio | T |
| RF-BRF-3 | Un verificador independiente redacta una paráfrasis del contrato y la contrasta con el prompt original | Obligatorio | T, I |
| RF-BRF-4 | Lo que aparece en el prompt y no en la paráfrasis se trata como compromiso perdido y vuelve a extracción | Obligatorio | T |
| RF-BRF-5 | Ante ambigüedad irresoluble, se clasifica como `Hueco` y nunca como `Compromiso` | Obligatorio | T |
| RF-BRF-6 | Un compromiso no verificable, o se convierte en criterio con rúbrica, o se declara como no verificado en el informe. Nunca se deja dentro sin método | Obligatorio | T |
| RF-BRF-7 | Los parámetros poéticos de `config` se promocionan a `Compromiso` del contrato | Obligatorio | T |
| RF-BRF-8 | Un prompt casi vacío produce un contrato con cero compromisos y grado de libertad 1.0, y la ejecución continúa | Obligatorio | T |

## Docs de referencia

`architecture.md` §2, §8.10, §8.11; `definitions.md` §3
