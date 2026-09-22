# 008 — SCN · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Verificación: propiedades y mutación en la puerta dura; eval de juez calibrada en los críticos, clases T e I (`docs/verification.md` §5).

### Steps

- [ ] Los críticos no reciben el razonamiento del escritor ni su ventana (RF-SCN-7 · clase A)
- [ ] Ningún agente escribe en canon durante el bucle; solo el registrador, y solo tras veredicto de aceptación (RF-SCN-16 · clase A)
- [ ] Las escenas se producen en orden: ninguna empieza antes de que la anterior esté aceptada y registrada (RF-SCN-1, R3)
- [ ] El escritor recibe una `VentanaDeContexto` y produce texto de escena más el delta que pretendía (RF-SCN-2)
- [ ] La puerta dura comprueba, sin modelo: violación de `Restriccion`, contradicción temporal, atributo de canon alterado y los predicados deterministas de los invariantes 3 y 4 (RF-SCN-3)
- [ ] El predicado determinista del invariante 3 se comprueba sobre el delta **declarado** por el escritor, no sobre el real (RF-SCN-4)
- [ ] Superada la puerta dura, crítico de canon, crítico de oficio y auditor de tropos corren en paralelo (RF-SCN-5 · clases T y D)
- [ ] Los críticos devuelven `Defecto` tipados y no reescriben nunca (RF-SCN-6)
- [ ] Todo `Defecto` registra severidad, localización y causa raíz (RF-SCN-8)
- [ ] La causa raíz pertenece a un conjunto cerrado de seis valores; una causa fuera de ese conjunto es salida inválida del crítico, se rechaza y consume reintento (RF-SCN-9 · clases T y A)
- [ ] El enrutado es uno solo y por naturaleza del defecto: los corregibles al editor, los estructurales al escritor, nunca por la puerta que lo encontró (RF-SCN-10)
- [ ] La escena corregida por el editor vuelve a entrar por la puerta dura (RF-SCN-11)
- [ ] Agotado el presupuesto de reintentos de una escena, el veredicto es `escalar` y el defecto queda en el informe (RF-SCN-12)
- [ ] El registrador extrae el `DeltaDeEstado` real del texto aceptado; la divergencia con el declarado es un defecto de la puerta dura (RF-SCN-13)
- [ ] Al aceptar una escena se actualizan canon, `EstadoDelMundo`, `ResumenRodante` e índice en una sola transacción, antes de generar la siguiente (RF-SCN-14)
- [ ] Al aceptar una escena se escribe el `EstadoEpistemico` de cada `Personaje` cuyo conocimiento cambia en ella, en esa misma transacción; el de los demás se arrastra (RF-SCN-15)
- [ ] El `EstadoDelMundo` en la escena *n* es la aplicación ordenada de los deltas de las escenas 1..*n*−1 (RF-SCN-17)
- [ ] Todo `Hueco` resuelto pasa a ser canon inviolable (RF-SCN-18)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
