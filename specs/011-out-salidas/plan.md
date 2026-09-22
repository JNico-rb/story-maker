# 011 — OUT · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: guardarraíles y trazas; demostración de extremo a extremo con prompt casi vacío, clases T y D (`docs/verification.md` §5).

### Steps

- [ ] `GET /runs/{id}/manuscript` entrega el manuscrito en Markdown, único formato soportado (RF-OUT-1, R7)
- [ ] El informe de ejecución declara compromisos cumplidos, compromisos no verificables, huecos resueltos y con qué, novum elegido y su puntuación, defectos no resueltos con su localización, presupuesto consumido y causas raíz registradas (RF-OUT-2)
- [ ] `GET /runs/{id}/report` entrega el informe al terminar o al cancelar; mientras la ejecución corre devuelve conflicto, nombrando el estado actual (RF-OUT-3)
- [ ] El informe de una ejecución cancelada tiene la misma estructura, con los campos no evaluados declarados como tales y la fase en que se canceló (RF-OUT-4)
- [ ] El informe recoge las causas raíz que no producen defecto: `contexto ausente` por recorte y `presupuesto excedido` por deriva de conteo (RF-OUT-5)
- [ ] Toda resolución de conflicto entre config y prompt queda registrada en el informe; ninguna se resuelve en silencio (RF-OUT-6)
- [ ] El manuscrito parcial es accesible durante la ejecución, marcado como no definitivo (RF-OUT-7)
- [ ] Demostración de extremo a extremo con un prompt casi vacío: de `POST /runs` a manuscrito e informe (`verification.md` §5 · clase D)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
