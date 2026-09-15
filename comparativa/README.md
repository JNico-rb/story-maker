# comparativa/

Comparaciones entre **dos novelas generadas con la misma idea y distinta configuración**. Es la herramienta con la que se deciden los pasos 2 y 3 del plan de escalado (`specs/functional.md` §7.7):

- **Modelo caro frente a barato**, en Claude Code: ¿qué pierde la historia con `haiku`/`sonnet` y lo compensa el escalado a `opus`?
- **Claude Code frente al runner**: ¿produce el runner una carpeta equivalente con el mismo diseño?

Las novelas **no se copian aquí**: viven en `novelas/<slug>/` con su historial de git, que es parte de lo que se mide. Un caso solo las referencia.

## Un caso

```
comparativa/caso-NN-<slug>/
  caso.md           # idea, qué se compara y por qué; ruta y configuración de cada lado
  comparacion.md    # lo rellena /novela comparar; no se escribe a mano
```

`caso.md` tiene dos lados, **A** y **B**. Cada lado es una carpeta `novelas/<slug>/` con `estado.json` en `fase: completa`. La configuración de cada lado se lee de su `config.json`; en `caso.md` solo se anota qué difiere (p. ej. "A: modelos.* = opus · B: modelos.* = haiku, escalado activo").

## Reglas para que la comparación sea justa

1. **Misma idea y misma entrevista.** El lado B se crea con `/novela nueva "<misma idea>" …` y respondiendo igual, o —mejor— copiando `entrevista.md` del lado A a la carpeta del B antes del interrogatorio para que el orquestador la tome como cerrada (`procedimientos/interrogatorio.md`, A.1). Cualquier diferencia de entrevista se anota en `caso.md`.
2. **Mismo perfil.** `perfil_activo` y `formato.*` iguales; si no, no se comparan longitudes.
3. **Ejecuciones completas.** Los dos lados con `fase: completa`. Una parada no se compara: se relanza.
4. **Todo cuenta.** Los intentos rechazados, los aceptados por agotamiento y los reintentos técnicos forman parte del resultado, no se ocultan.
5. **Nada se estima.** Todo dato de `comparacion.md` sale de contar o de leer. Lo que no está disponible se escribe `desconocido`.

## Crear un caso

1. Copia `plantilla/` a `caso-NN-<slug>/` (NN correlativo).
2. Rellena `caso.md`: idea, qué se compara, rutas de A y B, qué difiere.
3. `/novela comparar comparativa/caso-NN-<slug>`.

El resultado más útil que puede dar un caso es una lista de **cambios accionables para el harness** (qué fichero, qué cambiar). Si el lado barato se lee igual de bien, el procedimiento obliga a decirlo: es la respuesta que buscamos.
