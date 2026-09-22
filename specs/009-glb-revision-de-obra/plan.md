# 009 — GLB · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: consultas estructuradas por prueba; juicios por eval, clases T e I (`docs/verification.md` §5).

### Steps

- [ ] El pase global no lee el manuscrito entero: se descompone en cuatro comprobaciones por tipo de defecto (RF-GLB-1 · clase A)
- [ ] Hilos abiertos: consulta estructurada de `Arco` con estado abierto (RF-GLB-2)
- [ ] Consecuencias establecidas y nunca usadas: consulta estructurada de `Consecuencia` sin ningún vínculo de trazabilidad (RF-GLB-3)
- [ ] Ritmo y curva de tensión: juicio sobre la tabla de tensiones de capítulo, construida por código (RF-GLB-4 · clases T e I)
- [ ] Repetición léxica entre escenas distantes: único uso de recuperación de todo el pase global, sobre la colección de prosa (RF-GLB-6 · clases T e I)
- [ ] Deriva de voz: muestreo de tercios contrastado con el `StyleSheet` (RF-GLB-5 · clase I)
- [ ] Los defectos de obra se resuelven por reescritura dirigida de escenas concretas, nunca por regeneración global (RF-GLB-7)
- [ ] Una escena reescrita vuelve a pasar las puertas del bucle por escena (RF-GLB-8)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
