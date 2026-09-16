# comparativa/

Comparaciones entre **dos novelas generadas con el mismo caso de referencia y distinta configuración**. Es la herramienta con la que se deciden los pasos 2 y 3 del plan de escalado (`specs/functional.md` §7.8):

- **Modelo caro frente a barato**, en Claude Code: ¿pasa la novela barata los mismos umbrales de `calidad` que la cara, y lo compensa el escalado?
- **Claude Code frente al runner**: ¿produce el runner una carpeta equivalente con el mismo diseño?

Las novelas **no se copian aquí**: viven en `novelas/<slug>/` con su historial de git, que es parte de lo que se mide. Un caso solo las referencia.

## Un caso

```
comparativa/caso-NN-<slug>/
  caso.md           # qué se compara y por qué; ruta y configuración de cada lado
  comparacion.md    # lo rellena /novela comparar; no se escribe a mano
```

`caso.md` tiene dos lados, **A** y **B**. Cada lado es una carpeta `novelas/<slug>/` que pasa `/novela verificar`. La configuración de cada lado se lee de su `config.json`; en `caso.md` solo se anota qué difiere.

## Reglas para que la comparación sea justa

1. **Mismo caso de referencia.** Los dos lados se generan con `entrevista: pruebas/referencia/entrevista.md` (o `modo-prueba: pruebas/referencia`), así `idea.md` y `entrevista.md` son idénticos. `/novela comparar` lo comprueba byte a byte y para si no lo son.
2. **Mismo perfil.** `perfil` y `formato` iguales; si no, no se comparan longitudes.
3. **Ejecuciones completas.** Los dos lados con `etapa: completa`. Una parada no se compara: se relanza.
4. **Todo cuenta.** Los intentos rechazados, los aceptados por agotamiento, los rechazos por longitud y los reintentos técnicos forman parte del resultado, no se ocultan.
5. **Nada se estima.** Todo dato de `comparacion.md` sale de contar o de leer. Lo que no está disponible se escribe `desconocido`.

## Crear un caso

1. Copia `plantilla/` a `caso-NN-<slug>/` (NN correlativo).
2. Rellena `caso.md`: qué se compara, rutas de A y B, qué difiere.
3. `/novela comparar comparativa/caso-NN-<slug>`.

El resultado más útil que puede dar un caso es una lista de **cambios accionables para el harness** (qué fichero, qué cambiar). Si el lado barato pasa los mismos umbrales y se lee igual de bien, el procedimiento obliga a decirlo: es la respuesta que buscamos.
