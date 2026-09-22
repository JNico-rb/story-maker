# 011 — OUT · Salidas

- [ ] Spec approved   <- only the user marks this

## Objetivo

Entregar el manuscrito y la evidencia de lo que se hizo.

## Alcance

Manuscrito en Markdown e `InformeDeEjecucion`.

**Fuera de alcance:** los formatos de salida distintos de Markdown. Decisión cerrada en `architecture.md` §11.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-OUT-1 | El manuscrito se entrega en Markdown | Obligatorio | T |
| RF-OUT-2 | El informe de ejecución declara: compromisos cumplidos, compromisos no verificables, huecos resueltos y con qué, novum elegido y su puntuación, defectos no resueltos con su localización, presupuesto consumido y causas raíz registradas | Obligatorio | T |
| RF-OUT-3 | `GET /runs/{id}/report` entrega el `InformeDeEjecucion` al terminar o al cancelar. Mientras la ejecución sigue corriendo devuelve conflicto, nombrando el estado actual | Obligatorio | T |
| RF-OUT-4 | El informe de una ejecución cancelada tiene la misma estructura, con los campos que no llegaron a evaluarse declarados como no evaluados y la fase en que se canceló | Obligatorio | T |
| RF-OUT-5 | El informe recoge las causas raíz que no producen defecto: `contexto ausente` por recorte y `presupuesto excedido` por deriva de conteo | Obligatorio | T |
| RF-OUT-6 | Toda resolución de conflicto entre config y prompt queda registrada en el informe; ninguna se resuelve en silencio | Obligatorio | T |
| RF-OUT-7 | El manuscrito parcial es accesible durante la ejecución, marcado como no definitivo | Obligatorio | T |

## Restricciones

| # | Restricción | Origen (§ de `architecture.md`) |
|---|---|---|
| R7 | Salida en Markdown, único formato soportado | §11 |

## Docs de referencia

`architecture.md` §6.1, §8.10; `definitions.md` §5
