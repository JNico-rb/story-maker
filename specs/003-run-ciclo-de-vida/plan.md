# 003 — RUN · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: integración con dobles, más comprobación de modelos sobre la máquina de estados, clases T y A (`docs/verification.md` §5).

### Steps

- [ ] Los estados del trabajo y sus transiciones legales están declarados y son los únicos posibles (RF-RUN-9 · clase A)
- [ ] `POST /runs` crea la ejecución, devuelve su identificador y no espera a que termine (RF-RUN-1)
- [ ] Los errores aritméticos de bloqueo se devuelven en el `POST`; los de densidad, en el estado del trabajo (RF-RUN-7)
- [ ] La ejecución corre en un worker aparte del proceso que atiende HTTP (RF-RUN-2 · clase D)
- [ ] `GET /runs/{id}` devuelve estado, fase y escena actual en todo momento (RF-RUN-3)
- [ ] `GET /runs/{id}/stream` emite progreso por Server-Sent Events mientras la ejecución avanza (RF-RUN-4 · clases T y D)
- [ ] Existe punto de control por escena: el estado persistido basta para reanudar sin repetir escenas aceptadas (RF-RUN-5)
- [ ] Una caída no pierde más de una escena de trabajo (RNF-4)
- [ ] `DELETE /runs/{id}` cancela conservando el manuscrito parcial y el estado (RF-RUN-6)
- [ ] Cada agente con bucle lleva su propio tiempo máximo, además del presupuesto de reintentos por escena (RF-RUN-8)
- [ ] Ninguna operación de usuario espera a que la ejecución termine (RNF-3 · clase D)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
