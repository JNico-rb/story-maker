# 002 — CFG · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: unitarias sobre el validador, más ejecución simbólica en la aritmética de factibilidad, clases T y A (`docs/verification.md` §5).

### Steps

- [ ] `config.estructura` declara `objetivo_palabras`, `capitulos` y `forma_distribucion`, y el resto se deriva: no existe campo donde escribir un estado inconsistente (RF-CFG-2 · clase A)
- [ ] `config.calidad` y `config.recuperacion` no son editables por el usuario final (RF-CFG-11 · clase A)
- [ ] Una combinación aritmética imposible de `config.estructura` se rechaza antes de ejecutar nada, nombrando los parámetros incompatibles (RF-CFG-1 · clases T y A)
- [ ] Sin tabla de cuotas no se arranca: no existen cuotas por defecto en el código (RF-CFG-9)
- [ ] Sin directorio de ejecuciones ni ruta de biblioteca declarados en `config.operacion` no se crea la ejecución, con error que nombra la que falta (RF-CFG-10)
- [ ] Una tabla de cuotas completa, con una entrada por par (colección, consumidor) y `modelo_incrustacion` con valor, deja crear la ejecución (RF-CFG-3)
- [ ] Un par (colección, consumidor) ausente impide crear la ejecución, con error que nombra el par que falta (RF-CFG-4)
- [ ] Una cuota negativa o no entera impide crear la ejecución (RF-CFG-5)
- [ ] Una colección o un consumidor desconocidos impiden crear la ejecución (RF-CFG-6)
- [ ] Prosa con cuota mayor que 0 para el escritor o para el crítico de canon impide crear la ejecución (RF-CFG-7)
- [ ] Una cuota de 0 es válida y significa que esa colección no entra en la ventana de ese consumidor (RF-CFG-8)
- [ ] El identificador del modelo de incrustación se congela al crear la ejecución; cambiarlo después en configuración no afecta a una ejecución ya creada (RF-CFG-13)
- [ ] El identificador del modelo de lenguaje se congela al crear la ejecución; cambiarlo después se ignora y queda anotado en el informe como resolución de conflicto (RF-CFG-14)
- [ ] Cada parámetro estructural genera un `Criterio` de la puerta dura (RF-CFG-15)

RF-CFG-12 no tiene paso aquí: la congelación se entrega donde ocurre, en el paso de RF-PLN-8 (`007-pln-planificacion`).

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
