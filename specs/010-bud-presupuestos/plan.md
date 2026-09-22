# 010 — BUD · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: guardarraíles y trazas, clases T y D (`docs/verification.md` §5).

### Steps

- [ ] Existen tres techos distintos y no se confunden: ventana en tokens de entrada, reintentos por escena y ejecución en dinero (RF-BUD-1 · clase A)
- [ ] La salida no lleva techo en tokens (RF-BUD-3 · clase A)
- [ ] El techo de ventana cuenta solo entrada y se aplica a la suma de las llamadas en vuelo de una etapa, no a una llamada suelta (RF-BUD-2)
- [ ] Toda llamada a modelo registra agente, fase, escena, tokens de entrada declarados y reales, y coste (RNF-10)
- [ ] El coste consumido se acumula por llamada y es consultable durante la ejecución (RF-BUD-5)
- [ ] Agotado el presupuesto en dinero, la ejecución bloquea (RF-BUD-4)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
