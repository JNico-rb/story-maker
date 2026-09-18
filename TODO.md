# Pendiente

Trabajo abierto del harness. **Para qué sirve este fichero:** el [CHANGELOG.md](CHANGELOG.md) cuenta lo que *ya se decidió y por qué*; esto cuenta lo que *falta por hacer*. Un punto sale de aquí cuando está hecho, y solo entra en el CHANGELOG si por el camino se tomó una decisión de diseño que valga la pena proteger.

---

## Implementar la 0.8.0

La spec la recoge entera; la implementación no existe. `config.json` sigue en la forma anterior. Entra todo junto:

- **Hoja de continuidad** que compone el harness antes de invocar al escritor y al revisor de continuidad (spec §4.2, §5.2, §5.5), y los campos nuevos del frontmatter del resumen que necesita: `fecha_ficcion_inicio`, `fecha_ficcion_fin`, `plazos`, `objetos`.
- **`memoria.resumen_max_palabras`** (350) con su reinvocación única al resumidor, y el contrato de §5.3 que separa hechos (resumen) de estado (libro de estado).
- **`veredicto.rechaza_con_graves` se parte** en `rechaza_con_gravedad_1` (1) y `rechaza_con_gravedad_2` (2). Hoy la clave vieja la citan `config.json`, `procedimientos/capitulo.md` y `plantillas/informe.md`, y son coherentes entre sí: **se cambian los tres a la vez o ninguno**. Cambiar solo la plantilla la dejaría nombrando una clave inexistente.
- **`resumenes_completos_ultimos` dentro de cada perfil** (`null` en `relato` y `novela_corta`, 10 en `novela` y `saga`) y **`limites.entrada_max_palabras_invocacion`** (25.000) con el aviso de proyección en `comprobar_entorno`.

## Prueba de punta a punta del estudio

Encargar, entrevistar, aprobar y escribir una novela entera desde el navegador. El servidor está probado por partes; lo que no se ha ejercitado nunca es el recorrido completo, que es lo único que demuestra los tres caminos nuevos del harness: `precarga:`, la parada `ESPERA_APROBACION` y la reanudación leyendo `decision.md`.

## Recalibrar con la segunda ejecución completa

Tres valores elegidos a ojo o sobre una sola ejecución, que solo una segunda puede confirmar:

- `limites.pausa_cada_capitulos` (hoy 3).
- `calidad.min_aprobados_primer_intento_pct` (hoy 40, marcado como suelo provisional).
- Si se corrige el objetivo de longitud por el sesgo medido (+10,5 %, 11 de 13 intentos por encima): `objetivo × (1 − sesgo)`. Calibrar una constante que se realimenta al prompt con un solo punto es ajustar al ruido.

## `--verificar` en el exportador de trazas

No existe. `exportar.py` solo escribe, y por el SDK; leer de vuelta lo exportado exige `/api/public/v2/observations` con `fields=core,io,metadata` (la API legada responde 410 para esta organización). Documentado en `herramientas/trazas/README.md`.
