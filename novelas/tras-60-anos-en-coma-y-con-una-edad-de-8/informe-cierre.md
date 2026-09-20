---
resultado: "PARADA"
motivo: "ESPERA_APROBACION"
fecha: "2026-09-20T17:59Z"
etapa: "interrogatorio"
arco: null
capitulo: null
intento: null
cumple_todas: null
---

# Informe de cierre — tras-60-anos-en-coma-y-con-una-edad-de-8

**Resultado:** PARADA
**Motivo:** ESPERA_APROBACION
**Detalle:** La propuesta (biblia, escaleta de alto nivel y escaleta del arco 1) está escrita y no hay usuario en esta sesión a quien preguntar: la novela se lanzó con `precarga: encargos/tras-60-anos-en-coma-y-con-una-edad-de-8`, que es lo que manda el estudio (spec §9.4), y en esa carpeta no hay `decision.md`. `biblia.md` y `escaleta.md` quedan **sin** `aprobada: true`, y `arcos/arco-01.md` sin `validada: true`, para que la vuelta siguiente pueda reescribirlas.

## Dónde se detuvo

Etapa **interrogatorio**, al pedir la confirmación de la propuesta. Sin arco en curso, sin capítulo, sin intento.

## Qué quedó completado

- Entrevista cerrada: sí (`entrevista.md`, origen `formulario+grilling`; 0 preguntas y 0 rondas de grilling, porque las doce respuestas del formulario venían marcadas **[decide tú]** y eso no se repregunta).
- Escaleta aprobada: **no**. Propuesta lista y pendiente de decisión: «La memoria rota», 3 capítulos en 1 arco.
- Arcos detallados / revisados: 1 escrito (`arcos/arco-01.md`, sin validar) / 0 revisados.
- Capítulos cerrados: 0 de 3 (por agotamiento: 0).
- Informe global: no.

## Canon: 2 problemas de gravedad 1 sin resolver

El revisor de continuidad validó el canon cuatro veces y el interrogador agotó las 3 vueltas de `escaleta_rechazos_max`. Se resolvieron tres tandas (frontmatter de la escaleta desincronizado con su prosa, Tarek ausente de Personajes, edad de Elena) y quedan estos dos, tal como los devolvió el revisor:

1. **`escaleta.md`, frontmatter, campo `acto`** — «`acto: planteamiento` contradice la estructura descrita: la sección Estructura reparte el arco 1 en Planteamiento (cap. 1), Nudo (cap. 2) y Desenlace (cap. 3), y el arco va de 1 a 3, así que el campo solo nombra uno de los tres actos».
2. **`escaleta.md`, tabla «Hilos narrativos»** — «el hilo "La amenaza del Regulador a las anomalías" está en `hilos_abre` y en `hilos_cierra` del arco 1 pero no aparece en la tabla de hilos narrativos».

Se muestran sin filtrar, que es lo que manda `procedimientos/interrogatorio.md`: quien aprueba la biblia es el usuario, y una biblia con una tensión aceptada a conciencia es legítima; lo que no lo es, es que no la vea.

## Invocaciones

interrogador **4** · escritor 0 · resumidor 0 · revisor-encargo 0 · revisor-continuidad **4** (las cuatro en modo `canon`). Reintentos técnicos: 0. Discrepancias de veredicto: 0. Rechazos por longitud: 0.

## Volumen

| agente | modelo | invocaciones | pal_entrada | pal_salida | tok_entrada | tok_salida | coste_usd |
|---|---|---|---|---|---|---|---|
| interrogador | haiku | 4 | 11.825 | 15.350 | – | – | – |
| revisor-continuidad | haiku | 4 | 11.270 | – | – | – | – |
| **total** | haiku | **8** | **23.095** | **15.350** | – | – | – |

El `pal_salida` del interrogador cuenta lo escrito en disco en cada vuelta, incluidos los documentos que volvieron sin cambios. Los revisores no escriben fichero: su salida es el JSON del informe.

## Métricas de calidad

No se calculan: solo se calculan en ÉXITO.

## Avisos

- El canon salió del interrogatorio con 2 problemas de gravedad 1 sin resolver tras 3 vueltas (`specs/functional.md` §4.1).
- Los ítems de las listas `sucesos` de `arcos/arco-01.md` se entrecomillaron al escribirlos para que el frontmatter parsee; el texto del interrogador no se cambió.
- Perfil `relato` con 3 capítulos: `config.json` avisa de que la línea base E1 se midió con 5, así que esta ejecución no será comparable con ella ni con los umbrales de `calidad.*`.

## Rutas

- Propuesta: `novelas/tras-60-anos-en-coma-y-con-una-edad-de-8/biblia.md`, `escaleta.md`, `arcos/arco-01.md`
- Entrevista: `novelas/tras-60-anos-en-coma-y-con-una-edad-de-8/entrevista.md`
- `novelas/tras-60-anos-en-coma-y-con-una-edad-de-8/registro.md`
- Config congelada: `novelas/tras-60-anos-en-coma-y-con-una-edad-de-8/config.json`
- `manuscrito.md` / `informe-global.md`: no existen todavía

**Para continuar:** leer la propuesta y aprobarla o pedir cambios, y después `/novela continuar novelas/tras-60-anos-en-coma-y-con-una-edad-de-8`. Desde el estudio, con sus botones; a mano, escribiendo la decisión en `encargos/tras-60-anos-en-coma-y-con-una-edad-de-8/decision.md` (`confirma`, o `cambios: <texto>`) — nunca dentro de `novelas/`, que la reanudación descarta lo que encuentre ahí sin commitear.
