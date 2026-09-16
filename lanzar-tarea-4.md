# Tarea 4 (lanzar el paso 1)

Cuando exista la skill, el procedimiento exacto es:

1. **Commitea el estado actual del repo**, para que los commits automáticos de `novelas/` partan de una base limpia y el criterio de inmutabilidad se pueda comprobar con git.
   - El harness exige repositorio git y no arranca si no lo hay.

2. **Abre una sesión nueva de Claude Code en el repo.**
   - El orquestador tiene que arrancar con el contexto vacío salvo la skill; esta conversación no debe arrastrarse.
   - Elige como modelo de sesión el caro: el orquestador es el harness, y su fiabilidad importa tanto como la de los agentes.

3. **En esa sesión, escribe `/hooks` una vez** o simplemente confía en el reinicio: es lo que carga `settings.json`, que no existía cuando se abrió esta sesión.

4. **Primera ejecución, de humo, en modo de prueba**, para comprobar la fontanería sin gastar tu atención en la entrevista:

   ```
   /novela nueva "prueba" modo-prueba: pruebas/referencia/respuestas.md limites.pausa_cada_capitulos=null
   ```

   - La pausa va a `null` porque con 5 capítulos y pausa cada 5 pararía justo al terminar, que es ruido.
   - Al acabar, `/novela estado novelas/<slug>` y lee `informe-cierre.md`. Si el inventario está completo y las métricas se calcularon, el harness funciona.

5. **Segunda ejecución, la de referencia**, con la idea fija y la entrevista real:

   ```
   /novela nueva "<la idea de pruebas/referencia/idea.md>" limites.pausa_cada_capitulos=null
   ```

   - Respondes a la entrevista, confirmas la escaleta, y a partir de ahí solo miras el progreso.
   - Con 5 capítulos y Opus en los cuatro agentes son unas 15 a 25 invocaciones, del orden de una hora.

6. **Guarda el resultado**: `informe-cierre.md` de esa novela es tu línea base.
   - Sus métricas de §8.3 y su volumen de §6.6 son contra lo que se comparará la ejecución barata del paso 2.