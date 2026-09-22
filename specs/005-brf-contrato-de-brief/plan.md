# 005 — BRF · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: eval de conjunto dorado para el extractor; eval adversaria para el verificador, clases T e I (`docs/verification.md` §5).

### Steps

- [ ] El sistema deriva del prompt un `ContratoDeBrief` con sus `Compromiso`s, sus `Hueco`s y un grado de libertad entre 0 y 1 (RF-BRF-1)
- [ ] Cada `Compromiso` declara dureza —inviolable o preferencia— y si es verificable (RF-BRF-2)
- [ ] Ante ambigüedad irresoluble, se clasifica como `Hueco` y nunca como `Compromiso` (RF-BRF-5)
- [ ] Los parámetros poéticos de `config` se promocionan a `Compromiso` del contrato (RF-BRF-7)
- [ ] Un verificador independiente redacta una paráfrasis del contrato y la contrasta con el prompt original (RF-BRF-3 · clases T e I)
- [ ] Lo que aparece en el prompt y no en la paráfrasis se trata como compromiso perdido y vuelve a extracción (RF-BRF-4)
- [ ] Un compromiso no verificable, o se convierte en criterio con rúbrica, o se declara como no verificado en el informe (RF-BRF-6)
- [ ] Un prompt casi vacío produce un contrato con cero compromisos y grado de libertad 1.0, y la ejecución continúa (RF-BRF-8)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
