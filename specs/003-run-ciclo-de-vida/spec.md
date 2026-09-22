# 003 — RUN · Ciclo de vida de la ejecución

- [ ] Spec approved   <- only the user marks this

## Objetivo

Correr la ejecución como trabajo asíncrono: crearla sin esperar, exponer su estado y su progreso, y conservar lo producido ante caída o cancelación.

## Alcance

Superficie HTTP con progreso en vivo y cancelación.

**Fuera de alcance:**

- Reanudación automática desde punto de control, con techo de reanudaciones: el diseño de orquestación está declarado sin escribir (`architecture.md` §12.1). V1 implementa el punto de control (RF-RUN-5) y deja la política de reanudación para cuando ese diseño exista.
- Roles y multiusuario: un único perfil, quien lanza la ejecución. No hay rol de revisor, ni de editor, ni de administrador, ni autenticación ni cuotas por usuario.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-RUN-1 | `POST /runs` crea la ejecución, devuelve su identificador y no espera a que termine | Obligatorio | T |
| RF-RUN-2 | La ejecución corre en un worker aparte del proceso que atiende HTTP | Obligatorio | D |
| RF-RUN-3 | El estado de la ejecución es consultable en todo momento: estado, fase y escena actual | Obligatorio | T |
| RF-RUN-4 | El progreso se emite por Server-Sent Events mientras la ejecución avanza | Obligatorio | T, D |
| RF-RUN-5 | Existe punto de control por escena: el estado persistido basta para reanudar sin repetir escenas aceptadas | Obligatorio | T |
| RF-RUN-6 | Cancelar conserva el manuscrito parcial y el estado; no destruye lo producido | Obligatorio | T |
| RF-RUN-7 | Los errores aritméticos de bloqueo se devuelven en el `POST`; los de densidad, en el estado del trabajo, porque exigen haber construido el outline | Obligatorio | T |
| RF-RUN-8 | Cada agente con bucle lleva su propio tiempo máximo, además del presupuesto de reintentos por escena | Obligatorio | T |
| RF-RUN-9 | Los estados del trabajo y sus transiciones legales están declarados y son los únicos posibles | Obligatorio | A |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-3 | **Ejecución larga.** El tiempo total se mide en minutos u horas; ninguna operación de usuario espera a que termine | D |
| RNF-4 | **Punto de control.** Una caída no pierde más de una escena de trabajo | T |

## Restricciones

| # | Restricción | Origen (§ de `architecture.md`) |
|---|---|---|
| R1 | Autonomía total: ninguna pausa, pregunta de aclaración ni pantalla de aprobación | §8.1 |
| R2 | Entrada mínima: `config` más un único prompt. No hay más interacción | §8.1, `definitions.md` §6 |

## Docs de referencia

`architecture.md` §9.3, §9.4, §9.5, §12.1
