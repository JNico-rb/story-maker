# TODO

Lo pendiente. Lo ya decidido vive en [CHANGELOG.md](CHANGELOG.md); lo vigente, en [specs/functional.md](specs/functional.md) y [specs/technical.md](specs/technical.md).

## Configuración (revisión del 2026-09-19)

- [ ] **A2 — `veredicto` con un solo umbral para gravedad 1 y 2.** `config.json` tiene `rechaza_con_graves: 1` sobre {1,2}; la spec quiere poder separar contradicción (1) de incumplimiento (2). Hoy el harness lee `rechaza_con_graves` y funciona; separarlo exige tocar `procedimientos/capitulo.md` y §7.5.
- [ ] **A2 — `resumenes_completos_ultimos` está en `memoria`, no en el perfil.** Debería ir por perfil (`null` en `relato` y `novela_corta`, 10 en `novela` y `saga`). Al pasar a `novela` esto se nota.
- [ ] **Claves inertes en el hito 1.** `modelos.temperatura.*` (la herramienta `Agent` no la expone) y `limites.presupuesto_usd_max` (con suscripción no hay coste por llamada). Están documentadas como tales; no borrarlas, son el contrato del runner del hito 2.
- [ ] **A22 — recalibrar `calidad.*`.** Los umbrales vienen de E1 (5 capítulos) y con el `relato` de 3 un solo fallo suspende. Recalibrar con la segunda ejecución controlada, no antes.
- [ ] **A20 — `paginas_objetivo` nunca se ha usado.** Sigue en los cuatro perfiles como `null`. O se usa o se quita en la versión 5.

## Harness

- [ ] **`LIMITE_DE_USO` sin probar.** El motivo de parada por cuota de suscripción agotada está escrito (spec §6.3/§6.5, `invocar.md`, `cierre.md`) pero no se ha disparado nunca de verdad; falta comprobar que el error del proveedor se distingue de un fallo técnico y que la reanudación deja el capítulo limpio.
- [ ] **A19 — decidir el abaratamiento.** El paso 2 de §7.8 está ejecutado pero no decidido: con haiku de revisor las métricas no discriminan (E4). Falta la combinación escritor barato + revisor caro, en una comparación controlada (misma versión de spec en las dos ramas).
- [ ] **A10 — recontar el volumen desde `registro.md`** en el informe de cierre, en vez de fiarse del contador vivo.
- [ ] **A21 — conservar en `.descartado/`** lo que `descartar()` tira hoy.
