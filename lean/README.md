# Lean — validador formal de la cronología (spec 007)

`Chronology.lean` es la biblioteca: tipos de la cronología, los invariantes T1–T5 (`docs/domain-knowledge.md` §5.3) como predicados decidibles, un comprobador por invariante con su demostración general (`compruebaTn_decide`: para toda cronología, da `true` si y solo si se cumple Tn) y el informe JSON con el primer testigo de cada invariante violado.

El backend genera un `FicheroDeCronologia` por versión (`backend/src/story_maker/formal/generator.py`): la cronología registrada, seudonimizada (ids de fila y años desplazados 400·k), un teorema `cumpleTn` por invariante que se cierra evaluando su comprobador en el núcleo (`decide +kernel`), el informe (`CRONOLOGIA-LEAN {json}`) y `#print axioms` de cada teorema.

**Verificar** un fichero es `lake build --wfail` de la biblioteca y `lake env lean -DwarningAsError=true <fichero>`: un `sorry` o un aviso no pasan, y la auditoría solo admite `propext`, `Classical.choice` y `Quot.sound`. Es `passed` solo si compila, pasa la auditoría y cumple los cinco; `failed` si solo fallan teoremas de invariantes, con su testigo; `error` por cualquier otra causa. La interpretación está en `backend/src/story_maker/formal/lean_output.py` y es la misma en los dos modos del `VerificadorFormal`: `local` (esta máquina, en el directorio de datos) y `github` (el workflow `.github/workflows/verificar-cronologia.yml`, ADR 0004).

**No corre en el portátil de desarrollo** (Smart App Control bloquea los binarios de Lean): se construye y se prueba en GitHub Actions.

**Las demostraciones generales, honestamente.** `compruebaTn_decide` no es una prueba ad hoc por cronología: para cada Tn, `compruebaTn c = true ↔ Tn c` vale para **toda** `c : Cronologia`, vía decidibilidad (`decide (Tn c)` con `of_decide_eq_true` y `decide_eq_true`) — el comprobador ejecutable queda demostrado equivalente al invariante `Prop`, no solo comprobado en casos. Son 3 teoremas más de los que pide el encargo (T1–T5 frente a T1–T2 exigidos), y el generador cierra un teorema `cumpleTn` por invariante evaluando ese comprobador, no repitiendo la prueba.

**Evidencia real.** Las cronologías que generó el gate en las evals se conservan en `ejemplos/cronologias/`: tres fallan algún invariante (ejecución 12: T1; 13: T2 y T4; 16: T2) y la cuarta es la de la ejecución 16 después de que el fallo volviera al editor y se reescribiera: pasa T1–T5. Es el bucle completo: Lean bloquea, el editor corrige y Lean deja pasar.

## Ficheros de la CI — `pruebas/`

Salidas del generador para la cronología de fixture de la spec, con k = 3; `backend/tests/formal/test_lean_files.py` comprueba que son byte a byte lo que el generador escribe hoy. `esperado.json` dice qué debe dar cada uno:

| Ficheros | Caso | Se espera |
|---|---|---|
| `dorado.lean` | 007-C20 | `passed` |
| `negativo-T1.lean` … `negativo-T5.lean` | 007-C21 | `failed`, con ese invariante y su primer testigo |
| `limite-*.lean` | 007-C22 | lo de la tabla de límites |
| `biblioteca.lean` | 007-C23 | los cinco `compruebaTn_decide` solo con axiomas admitidos |
| `control-sorry.lean`, `control-axioma.lean` | 007-C24 | `error`: por `sorry` (no compila y `sorryAx`) y por el axioma `trampa` |

Desde la raíz del repo, con la biblioteca construida:

```
PYTHONPATH=backend/src python3 -m story_maker.formal.lean_ci pruebas lean
```

Sale con 1 si algún fichero no da lo esperado (un negativo que compila, otro testigo, un control que pasa). Solo usa la biblioteca estándar de Python.

Toolchain fijado en `lean-toolchain`; paquete sin dependencias externas.
