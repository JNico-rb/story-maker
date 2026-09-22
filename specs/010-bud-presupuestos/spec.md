# 010 — BUD · Presupuestos y techos

- [ ] Spec approved   <- only the user marks this

## Objetivo

Mantener separados los tres techos —ventana, reintentos y dinero— y hacer consultable el coste durante la ejecución.

## Alcance

Techos de ventana, reintentos y dinero; uso y coste registrados por cada llamada a modelo.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-BUD-1 | Existen tres techos distintos y no se confunden: ventana en tokens de entrada, reintentos por escena, y ejecución en dinero | Obligatorio | A |
| RF-BUD-2 | El techo de ventana cuenta solo entrada y se aplica a la suma de las llamadas en vuelo de una etapa, no a una llamada suelta | Obligatorio | T |
| RF-BUD-3 | La salida no lleva techo en tokens | Obligatorio | A |
| RF-BUD-4 | Agotado el presupuesto en dinero, la ejecución bloquea | Obligatorio | T |
| RF-BUD-5 | El coste consumido se acumula por llamada y es consultable durante la ejecución | Obligatorio | T |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-10 | **Observabilidad.** Toda llamada a modelo registra agente, fase, escena, tokens de entrada declarados y reales, y coste | T |

## Docs de referencia

`architecture.md` §3.13, §8.12
