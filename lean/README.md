# Validador formal de la cronología (Lean 4)

Proyecto Lake que verifica la cronología de cada versión de la novela antes de publicarla (`cronologia-lean`, [ADR 0004](../docs/adr/0004-lean-en-github-actions.md)). El backend exporta la cronología de SQLite a JSON; `scripts/generate.py` la convierte en `Input/Data.lean`, y `Input/Proofs.lean` demuestra con `decide` un teorema por invariante. **La versión se publica solo si el módulo compila**: el veredicto es el teorema, no un script.

## Invariantes

Son los T1–T4 de [`domain-knowledge.md` §5.3](../docs/domain-knowledge.md), con T5 dentro de T2, como los agrupa la V1. Cada uno es una proposición cuyos cuantificadores recorren listas de la cronología, así que es decidible. Están en [`Chronology/Invariants.lean`](Chronology/Invariants.lean).

| Criterio | Teorema | Enunciado | Fronteras que no lo violan |
|---|---|---|---|
| `t1-orden` | `DeclaredOrder` | Los eventos narrados que no son analepsis avanzan en el orden de capítulo y beat: ninguno es anterior a otro que se narra antes | Una analepsis; un evento de trasfondo, sin capítulo; dos eventos del mismo momento |
| `t2-edad` | `AgeCoherence` | Un personaje con fecha de nacimiento ha nacido en todo evento en que está presente, y toda edad declarada suya es la que dan su nacimiento y el momento del evento | Estar presente a las 00:00 de la fecha de nacimiento; cumplir el 1 de marzo, en año no bisiesto, por nacer un 29 de febrero; un personaje sin fecha de nacimiento |
| `t3-dos-lugares` | `SinglePlace` | Un personaje presente en dos eventos del mismo momento está en el mismo lugar en los dos | Un evento sin lugar |
| `t4-excluyente` | `NoReturnAfterExclusion` | El personaje excluido de un evento excluyente —muerte o partida definitiva— no está presente en ningún evento posterior | Un evento en el mismo momento que el excluyente |

Reglas de calendario de [`domain-knowledge.md` §5.2](../docs/domain-knowledge.md): un nacimiento es a las 00:00 de su fecha, y un cumpleaños del 29 de febrero cae el 1 de marzo en los años no bisiestos. Las comprueba [`Chronology/Tests.lean`](Chronology/Tests.lean) en cada construcción.

## Estructura

| Ruta | Contenido |
|---|---|
| `Chronology/Model.lean` | Tipos de la cronología y calendario: momento ordinal, edad, año bisiesto |
| `Chronology/Invariants.lean` | Los cuatro invariantes y la búsqueda del primer testigo de cada uno |
| `Chronology/Report.lean` | El informe por invariante, en JSON |
| `Chronology/Audit.lean` | `#assert_standard_axioms`: falla si una demostración depende de `sorryAx` o de un axioma que no sea `propext`, `Classical.choice` o `Quot.sound` |
| `Input/Proofs.lean` | Los cuatro teoremas sobre `Input.chronology`, cerrados con `decide +kernel`, y su auditoría de axiomas |
| `Input/Data.lean` | Generado por `scripts/generate.py`; no se versiona |
| `scripts/generate.py` | JSON → `Input/Data.lean`. Valida la forma de cada campo y solo emite números y tokens fijos de Lean: ningún texto de la entrada llega al fichero |
| `scripts/verify.py` | Genera, compila `Input.Proofs`, ejecuta el informe y escribe el JSON de resultado |
| `examples/` | Un positivo, un negativo por invariante —cada uno cambia un solo evento del positivo— y `expected.json` con el resultado esperado de cada uno; `seeds/` siembra un `sorry` y un axioma que la auditoría debe rechazar |

## JSON de la cronología (lo que produce el backend)

Un objeto con tres campos. Refleja las columnas de `events`, `event_characters` y `characters` de SQLite ([`specs/001-base/design.md`](../specs/001-base/design.md) §4.3). Todo campo es obligatorio, aunque su valor sea `null`; un campo desconocido invalida el fichero, así que ningún enunciado ni nombre viaja por accidente.

```json
{
  "version": 1,
  "characters": [
    {"id": 1, "birth_date": "1990-06-15"},
    {"id": 3, "birth_date": null}
  ],
  "events": [
    {
      "id": 202,
      "moment": "2026-03-01T09:00",
      "place_id": 101,
      "characters": [1, 3],
      "type": "ordinary",
      "excluded_character_id": null,
      "declared_ages": {"1": 35},
      "chapter_number": 1,
      "beat_number": 1,
      "flashback": false
    }
  ]
}
```

| Campo | Tipo | Columna de origen | Reglas |
|---|---|---|---|
| `version` | entero | — | `1` |
| `characters[].id` | entero ≥ 0 | `characters.id` | Único |
| `characters[].birth_date` | `"YYYY-MM-DD"` o `null` | `characters.birth_date` | Fecha real; `null` deja al personaje fuera de `t2-edad` |
| `events[].id` | entero ≥ 0 | `events.id` | Único |
| `events[].moment` | `"YYYY-MM-DDTHH:MM"` | `events.moment` | Fecha y hora reales; el año, de 4 a 6 cifras |
| `events[].place_id` | entero ≥ 0 o `null` | `events.place_id` | |
| `events[].characters` | lista de enteros | `event_characters` | Personajes presentes: conocidos y sin repetir |
| `events[].type` | `"ordinary"` o `"exclusion"` | `events.type` | |
| `events[].excluded_character_id` | entero o `null` | `events.excluded_character_id` | Un personaje conocido si y solo si `type` es `"exclusion"` |
| `events[].declared_ages` | objeto: id de personaje → edad | `events.declared_ages` | Claves: ids de personajes conocidos; edades de 0 a 200 |
| `events[].chapter_number`, `events[].beat_number` | enteros o `null` | `events.chapter_number`, `events.beat_number` | Los dos o ninguno: `null` en el trasfondo |
| `events[].flashback` | booleano | `events.flashback` | |

- **Qué eventos van.** Los de la cronología que se verifica ([`architecture.md` §4.3](../docs/architecture.md)): la registrada en el gate. Una analepsis que narra un evento de trasfondo no se envía otra vez: el evento narrado ya está en la lista, y así cuenta una sola vez. Un beat dentro de un marco no aporta evento.
- **Seudonimización** ([ADR 0004](../docs/adr/0004-lean-en-github-actions.md)). Los ids son los de las filas de SQLite. Las fechas van desplazadas un múltiplo de 400 años distinto de cero, que conserva los bisiestos, las edades y los cumpleaños; el backend guarda el desplazamiento para deshacerlo al traducir el testigo.
- **Límites.** Hasta 1.000 eventos, 500 personajes y 2 MB de JSON.

## JSON del resultado

`scripts/verify.py` lo escribe en `result.json`, que el workflow sube como el artefacto `chronology-result`.

```json
{
  "version": 1,
  "status": "fail",
  "invariant": "t2-edad",
  "witness": {"events": [202], "characters": [2]},
  "invariants": [
    {"invariant": "t1-orden", "holds": true, "witness": null},
    {"invariant": "t2-edad", "holds": false, "witness": {"events": [202], "characters": [2]}},
    {"invariant": "t3-dos-lugares", "holds": true, "witness": null},
    {"invariant": "t4-excluyente", "holds": true, "witness": null}
  ],
  "error": null
}
```

- **`status`**: `pass` si `Input.Proofs` compila y el informe no encuentra ninguna violación; `fail` si no compila y el informe encuentra alguna; `error` en cualquier otro caso —entrada inválida, Lean que no arranca, o teoremas e informe que no coinciden—, con el motivo en `error`. Para el backend, `error` es «verificador no disponible», nunca un invariante violado.
- **`invariant`** y **`witness`**: el primer invariante violado, en el orden de la tabla, y su primer testigo en el orden de la lista de eventos. Los ids del testigo, según el invariante: `t1-orden`, el evento narrado antes y el posterior que ocurre antes; `t2-edad`, el evento y el personaje; `t3-dos-lugares`, los dos eventos y el personaje; `t4-excluyente`, el evento excluyente, el posterior y el personaje.
- **`invariants`**: los cuatro, cada uno con su testigo. Da el score de cada criterio.
- **Código de salida** de `verify.py`: 0 `pass`, 1 `fail`, 2 `error`.

## El workflow: `.github/workflows/lean-verify.yml`

| Evento | Job | Qué hace |
|---|---|---|
| `push` que toca `lean/` o el workflow | `library` | Pruebas de `scripts/`; `lake build --wfail`; los ejemplos contra `expected.json`; y las semillas, que la auditoría debe rechazar |
| `workflow_dispatch` | `verify` | `lake build --wfail`, genera `Input/Data.lean` desde el input, compila `Input.Proofs` y sube `chronology-result` |

**Protocolo remoto** (adaptador `github` del `VerificadorFormal`, [`architecture.md` §10.5](../docs/architecture.md)):

1. **Disparo.** `POST /repos/{GITHUB_REPOSITORY}/actions/workflows/lean-verify.yml/dispatches` con `{"ref": "<rama>", "inputs": {"chronology": base64(gzip(json))}, "return_run_details": true}`, las cabeceras `Authorization: Bearer <GITHUB_TOKEN>` y `X-GitHub-Api-Version` fijada, y `Accept: application/vnd.github+json`. La respuesta trae el id de la ejecución del workflow. Los inputs admiten 65.535 caracteres en total: por eso el gzip.
2. **Espera.** `GET /repos/{…}/actions/runs/{id}` hasta `status = completed`.
3. **Resultado.** `GET /repos/{…}/actions/runs/{id}/artifacts`, el artefacto `chronology-result`, y su `archive_download_url`, que redirige a una URL que caduca en un minuto. Es un zip con `result.json`. Si no hay artefacto, el resultado es `error`.
4. **Tiempo.** Sin conclusión en `max_verifier_seconds`, la ejecución del harness pasa a `interrupted`.

**Token.** `GITHUB_TOKEN` es un token de grano fino limitado a este repositorio, con los permisos **Actions: lectura y escritura** —disparar y leer ejecuciones y artefactos— y **Metadata: lectura**. No necesita ninguno más.

**Seguridad del workflow.**

- Los jobs solo tienen el permiso `contents: read`, y el checkout no guarda credenciales.
- El input llega al script por la variable de entorno `CHRONOLOGY`, nunca interpolado en la orden.
- El generador corta la descompresión en 2 MB y solo escribe números: el input no puede inyectar código Lean.
- `--wfail` convierte en fallo el aviso de un `sorry`, y la auditoría de axiomas lo rechaza además en el término de la demostración; las semillas lo prueban en cada push.

## En local

Smart App Control bloquea las DLL de Lean en el portátil de desarrollo, así que `lake` solo corre en GitHub Actions o en Linux ([ADR 0004](../docs/adr/0004-lean-en-github-actions.md)). Lo que sí corre en local:

```bash
cd lean
python -m unittest discover -s scripts -p "test_*.py"   # generador y veredicto
python scripts/generate.py examples/positive.json       # el Input/Data.lean que se compilaría
```

En Linux, con elan: `lake build --wfail` y `python3 scripts/verify.py --examples examples`.

## Frente a la spec 009

La V1 cubre cuatro invariantes con T5 dentro de T2. Quedan para después, como Deseable: T6 —la fecha del novum—, la demostración general de corrección y de completitud de cada comprobador, y el `FicheroDeCronologia` generado por el backend en lugar del JSON.
