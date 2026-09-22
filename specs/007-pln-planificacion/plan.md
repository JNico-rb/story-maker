# 007 — PLN · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: propiedades sobre densidad y cobertura, clases T y A (`docs/verification.md` §5).

### Steps

- [ ] El planificador produce un `Outline` jerárquico de capítulos y escenas a partir del canon, el contrato y `config` (RF-PLN-1)
- [ ] El outline declara la cobertura de arcos y el estado de cada `Arco` (RF-PLN-2)
- [ ] La puerta 0 calcula la densidad narrativa como `objetivo_palabras` entre los elementos estructurales **comprometidos**, contando solo los derivados del `ContratoDeBrief` (RF-PLN-3 · clases T y A)
- [ ] Por debajo de `densidad_minima`, la ejecución se bloquea con un mensaje que nombra las tres cifras: elementos comprometidos, palabras por elemento y mínimo exigido (RF-PLN-4)
- [ ] La puerta 0 comprueba que todo compromiso tiene cobertura en el outline; si falta alguno, vuelve a planificación (RF-PLN-5)
- [ ] Con cero compromisos, la puerta 0 pasa por construcción y la ejecución continúa (RF-PLN-6)
- [ ] La puerta 0 corre una sola vez, sobre el outline, antes de congelar la estructura, y no forma parte del bucle por escena (RF-PLN-7)
- [ ] Superada la puerta 0, la estructura se congela (RF-PLN-8, cierra RF-CFG-12)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
