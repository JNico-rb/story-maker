# Lean se verifica en GitHub Actions porque Smart App Control lo bloquea en el portátil

El portátil de desarrollo tiene Smart App Control en modo Enforce y no hay permisos de administrador, WSL ni Docker. Smart App Control bloquea las DLL sin firma de Lean 4 (`libleanshared*.dll`), así que `lean` y `lake build` no arrancan; se comprobó con las toolchains v4.34.0 y v4.12.0. Pero el encargo exige ejecutar Lean antes de publicar cada versión.

El `VerificadorFormal` tiene dos modos con el mismo resultado, y los elige el ajuste `FORMAL_VERIFIER`:

- **local**, que ejecuta `lake build` en Linux o en CI;
- **github**, que envía el `FicheroDeCronologia` a un workflow de GitHub Actions con `GITHUB_TOKEN` y espera su conclusión.

Es la única salida que no depende de IT ni de cambiar de máquina. Pedir una excepción a Smart App Control no está en nuestra mano, y mover el backend a Linux obligaría a llevar allí también la demo y Playwright.

**Consecuencias.**

- Publicar exige red y GitHub, y cada verificación tarda del orden de minutos.
- **Protocolo.** El backend lanza el workflow con `workflow_dispatch` y la versión de la API de GitHub fijada. El fichero viaja como input, comprimido en gzip y codificado en base64, porque los inputs admiten 65.535 caracteres en total. `return_run_details: true` devuelve el id de la ejecución del workflow; el backend la sondea y lee el resultado de un artefacto. El detalle está en `architecture.md` §10.5.
- Un verificador inalcanzable, o que agota `max_verifier_seconds`, deja la ejecución del harness `interrupted` y reanudable; nunca se publica sin él.
- El fichero sale del portátil **seudonimizado**, para que ningún nombre llegue a los registros de Actions. Los identificadores son los de las filas de SQLite, sin nombres. Las fechas son de calendario, con el año desplazado un múltiplo de 400, que conserva los años bisiestos: con minutos relativos no se podrían calcular edades. Seudonimizado no es anónimo, porque quien conozca la regla deshace el desplazamiento; ese riesgo está aceptado en `verification.md` §6.
- **Seguridad del workflow.** Un `sorry` pasa `lake build`, así que el workflow compila con `--wfail` y audita los axiomas de cada teorema. El job solo tiene `contents: read`, y los inputs llegan a los pasos por variables de entorno.
- El token es de grano fino y está limitado al repositorio: Actions de lectura y escritura, y Metadata de lectura.
