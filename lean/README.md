# Lean — validador formal de la cronología (spec 007)

`Chronology.lean` es la biblioteca: tipos de la cronología, los invariantes T1–T5 (`docs/domain-knowledge.md` §5.3) como predicados decidibles, un comprobador por invariante con su demostración general (`compruebaTn_decide`: para toda cronología, da `true` si y solo si se cumple Tn) y el informe JSON con el primer testigo de cada invariante violado.

El backend genera un `FicheroDeCronologia` por versión (`backend/src/story_maker/formal/generator.py`): la cronología registrada, seudonimizada (ids de fila y años desplazados 400·k), un teorema `cumpleTn` por invariante que se cierra evaluando su comprobador en el núcleo (`decide +kernel`), el informe (`CRONOLOGIA-LEAN {json}`) y `#print axioms` de cada teorema.

**Verificar** un fichero es `lake build --wfail` de la biblioteca y `lake env lean -DwarningAsError=true <fichero>`: un `sorry` o un aviso no pasan, y la auditoría solo admite `propext`, `Classical.choice` y `Quot.sound`. Es `passed` solo si compila, pasa la auditoría y cumple los cinco; `failed` si solo fallan teoremas de invariantes, con su testigo; `error` por cualquier otra causa. La interpretación está en `backend/src/story_maker/formal/lean_output.py` y es la misma en los dos modos del `VerificadorFormal`: `local` (esta máquina, en el directorio de datos) y `github` (el workflow `.github/workflows/verificar-cronologia.yml`, ADR 0004).

**No corre en el portátil de desarrollo** (Smart App Control bloquea los binarios de Lean): se construye y se prueba en GitHub Actions.

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
