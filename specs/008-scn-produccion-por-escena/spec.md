# 008 — SCN · Producción por escena

- [ ] Spec approved   <- only the user marks this

## Objetivo

Producir cada escena con el contexto justo, evaluarla en cuatro puertas y aceptarla o corregirla.

## Alcance

Bucle de producción por escena con sus cuatro puertas y su enrutado de defectos.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-SCN-1 | Las escenas se producen en orden; ninguna empieza antes de que la anterior esté aceptada y registrada | Obligatorio | T |
| RF-SCN-2 | El escritor recibe una `VentanaDeContexto` y produce texto de escena más el delta que pretendía | Obligatorio | T |
| RF-SCN-3 | La puerta dura comprueba, sin modelo: violación de `Restriccion`, contradicción temporal, atributo de canon alterado, y los predicados deterministas de los invariantes 3 y 4 | Obligatorio | T |
| RF-SCN-4 | El predicado determinista del invariante 3 se comprueba sobre el delta **declarado** por el escritor, no sobre el real, que todavía no existe | Obligatorio | T |
| RF-SCN-5 | Superada la puerta dura, crítico de canon, crítico de oficio y auditor de tropos corren en paralelo | Obligatorio | T, D |
| RF-SCN-6 | Los críticos devuelven `Defecto` tipados y no reescriben nunca | Obligatorio | T |
| RF-SCN-7 | Los críticos no reciben el razonamiento del escritor ni su ventana | Obligatorio | A |
| RF-SCN-8 | Todo `Defecto` registra severidad, localización y causa raíz | Obligatorio | T |
| RF-SCN-9 | La causa raíz de un `Defecto` pertenece a un conjunto cerrado de seis valores. Una causa raíz fuera de ese conjunto es salida inválida del crítico: se rechaza y consume reintento del presupuesto de la escena | Obligatorio | T, A |
| RF-SCN-10 | El enrutado es uno solo y por naturaleza del defecto: los corregibles al editor, los estructurales al escritor. Nunca por la puerta que lo encontró | Obligatorio | T |
| RF-SCN-11 | La escena corregida por el editor vuelve a entrar por la puerta dura | Obligatorio | T |
| RF-SCN-12 | Agotado el presupuesto de reintentos de una escena, el veredicto es `escalar` y el defecto queda en el informe | Obligatorio | T |
| RF-SCN-13 | El registrador extrae el `DeltaDeEstado` real del texto aceptado; la divergencia con el declarado es un defecto de la puerta dura | Obligatorio | T |
| RF-SCN-14 | Al aceptar una escena se actualizan canon, `EstadoDelMundo`, `ResumenRodante` e índice en una sola transacción, antes de generar la siguiente | Obligatorio | T |
| RF-SCN-15 | Al aceptar una escena se escribe el `EstadoEpistemico` de cada `Personaje` **cuyo conocimiento cambia** en ella, en la misma transacción; el de los demás se arrastra del estado anterior | Obligatorio | T |
| RF-SCN-16 | Ningún agente escribe en canon durante el bucle; solo el registrador, y solo tras veredicto de aceptación | Obligatorio | A |
| RF-SCN-17 | El `EstadoDelMundo` en la escena *n* es la aplicación ordenada de los deltas de las escenas 1..*n*−1 | Obligatorio | T |
| RF-SCN-18 | Todo `Hueco` resuelto pasa a ser canon inviolable | Obligatorio | T |

## Restricciones

| # | Restricción | Origen (§ de `architecture.md`) |
|---|---|---|
| R3 | Generación secuencial por escena; cada una depende del estado que deja la anterior | §8.1 |

## Docs de referencia

`architecture.md` §4.1, §7.1, §8.7, §8.8; `definitions.md` §2, §5
