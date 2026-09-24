# TLA+ — validador formal del sistema

Aquí van (spec 006) `Harness.tla` y `Regenerations.tla`, sus `.cfg` y la tabla de correspondencia acción ↔ transición del código.

Versiones fijadas, las mismas en el portátil y en la CI (`.github/workflows/ci.yml`, job `formal`): **Temurin 21.0.12+8** y **`tla2tools.jar` v1.7.4** (TLC 2.19).

En el portátil, sin administrador ni instalador:

1. Temurin portable: descomprime el zip de `jdk-21.0.12+8` (Windows x64, de Adoptium) fuera del repositorio, p. ej. en `~/tools/`.
2. `curl -fsSL -o tla/tla2tools.jar https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar` (git lo ignora).
3. Desde `tla/`: `~/tools/jdk-21.0.12+8/bin/java -XX:+UseParallelGC -jar tla2tools.jar -config Harness.cfg -workers auto Harness.tla`.

La CI ejecuta TLC sobre cada `tla/*.cfg`; TLC no envía scores a Langfuse.
