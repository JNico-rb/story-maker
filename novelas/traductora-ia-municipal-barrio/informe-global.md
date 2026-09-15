---
capitulo: global
intento: 1
veredicto: RECHAZADO
problemas:
  - gravedad: 1
    donde: "capítulo 2, párrafos 'Lo buscó en los demás...' / 'No estaba en ninguno de los que se habían quedado' (manuscrito.md líneas 65-67), contrastado con los capítulos 1 y 3"
    que: "El expediente de Tomás Aguiló queda fuera del patrón. Las 411 resoluciones son las de la calle Olmos, luego la de Tomás (Olmos 9) está entre ellas. El capítulo 2 afirma que la fórmula 'equilibrado de carga asistencial' está en 134 expedientes de gente que ya no vive en Olmos y en ninguno de los que se quedaron; Tomás aún vive allí, así que su expediente no llevaría la fórmula. Pero en el capítulo 3 se muda a Vallongo por esa misma resolución, y el escrito cita solo los 134: deja fuera el caso que originó todo."
    por_que: "Contradice la biblia ('La decisión oculta': el programa recalificó realojos para desplazar a los de mayor coste) y la regla inviolable 4 (el expediente de Tomás es del mismo tipo). Contradice resumen-1 (hechos 3-6) frente a resumen-2 (hechos 4-5)."
observaciones:
  - "Hilos de la escaleta: los cuatro que debían cerrarse se cierran y quedan abiertos exactamente los dos previstos. Sin hilos huérfanos."
  - "Promesa menor sin pagar: 'Déjeme el número de expediente' (cap. 1) no tiene respuesta narrativa; el lector no sabe si Amalia intentó alegar. Cierra por elipsis en el cap. 3."
  - "Semilla sin recoger: 'Me llegó otro parecido hace nada' (Tomás, cap. 1) no vuelve a mencionarse."
  - "Voz de ONA: 'Son públicas' en el cap. 1 es información no solicitada; desajuste aislado, no cambio de regla."
  - "Continuidad material coherente: portales 9/11, ascensor del 9, mesa camilla, bolígrafo rojo, Vallongo a 31 km, los Cebrián. Reglas 1, 2, 3, 5, 6 y 7 respetadas en toda la novela."
  - "Personajes: nadie desaparece sin explicación."
  - "Veredicto informativo: el capítulo 2 está cerrado y aprobado; no procede reescritura."
---

# Informe global — Lo que dice el expediente

**Veredicto (informativo): RECHAZADO** — 1 problema de gravedad 1, 0 de gravedad 2–5. Nada se reescribe: queda para el usuario.

## Problemas
1. **[gravedad 1]** Capítulo 2, recuento de los 134 expedientes — el expediente de Tomás queda excluido del patrón por construcción ("en ninguno de los que se habían quedado"), pero en el capítulo 3 Tomás se muda por esa misma resolución y el escrito de Amalia no lo cita — contradice biblia regla 4 y la "decisión oculta"; resumen-1 frente a resumen-2. Es una deuda de continuidad entre capítulos que ningún revisor por capítulo podía ver.

## Observaciones
- Dos promesas menores del capítulo 1 sin pagar: el número de expediente que Amalia pide y el "otro papel parecido" de Tomás.
- Voz de ONA en el capítulo 1 ("Son públicas") ligeramente fuera de regla; el gancho lo fijaba la escaleta.
- Hilos, continuidad material y reglas del mundo correctos.

## Lección para el harness
El problema es detectable si el revisor de capítulo recibe también los resúmenes previos con atención al estado de los personajes detonantes: el resumen-1 decía que Tomás seguía en Olmos 9 con un expediente de realojo, y el capítulo 2 afirmó un absoluto ("en ninguno de los que se quedaron") incompatible con ello. Candidato a anotar en `CHANGELOG.md`.
