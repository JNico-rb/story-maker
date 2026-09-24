# TLA+ — validador formal del sistema

Especificaciones de la spec 006, en TLA+ directo (sin PlusCal), y sus configs para TLC. La tabla de correspondencia acción ↔ transición ↔ código está en el README de la raíz.

| Fichero | Qué es |
|---|---|
| `Harness.tla` | La `Ejecucion` de `docs/architecture.md` §9.1 con sus doce acciones; propiedades `NuncaPublicaSinValidar`, `ReanudacionSinDuplicarNiPerder`, `VersionAnteriorConservada`, `ReintentosAcotados` y `TerminaSiempre` (§11.5) |
| `Regenerations.tla` | Dos cambios confirmados sobre la misma novela, cola FIFO global, versión base y revalidación (§10.2); invariante `VersionesLineales` |
| `Harness.cfg`, `Regenerations.cfg` | Las configs que pasan: el modelo pequeño (5 capítulos, 2 reintentos, 2 reanudaciones, 1 cambio; 2 cambios y 1 reanudación) |
| `Harness.control1..5.cfg`, `Regenerations.control6.cfg` | Control del comprobador: el mismo modelo con un único defecto sembrado (constante `Defecto`); cada una comprueba solo la propiedad que nombra su línea `\* espera:` |
| `verificar.sh` | Decide el veredicto de cada config, igual en el portátil y en la CI |

## Veredictos (`verificar.sh`)

- **Config que pasa:** TLC termina sin error y cada acción del modelo se toma al menos una vez en el informe de cobertura; si no, nombra las acciones sin disparar.
- **Config de control:** TLC da el contraejemplo de la propiedad de su línea `\* espera:`. Falla si TLC termina sin error, si informa de otra propiedad o si se detiene por otra causa (sintaxis, semántica, memoria). TLC 2.19 no nombra la propiedad temporal violada: el control 5 solo comprueba `TerminaSiempre`, así que el contraejemplo es suyo.
- Sale con 0 solo si todas las configs dan su veredicto; cada fallo se imprime como `FALLO <config>: <motivo>`.
- La vivacidad se comprueba al final (`-lncheck final`): comprobarla a intervalos multiplica el tiempo.

## Versiones y portátil

Versiones fijadas, las mismas en el portátil y en la CI (`.github/workflows/ci.yml`, job `formal`): **Temurin 21.0.12+8** y **`tla2tools.jar` v1.7.4** (TLC 2.19).

En el portátil, sin administrador ni instalador:

1. Temurin portable: descomprime el zip de `jdk-21.0.12+8` (Windows x64, de Adoptium) fuera del repositorio, p. ej. en `~/tools/`.
2. `curl -fsSL -o tla/tla2tools.jar https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar` (git lo ignora).
3. Todas las configs: `JAVA=~/tools/jdk-21.0.12+8/bin/java bash tla/verificar.sh`; solo algunas, con sus nombres: `bash tla/verificar.sh Harness.cfg`.

TLC no corre en ninguna generación ni envía scores a Langfuse.
