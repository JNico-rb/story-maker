# TLA+ — validador formal del sistema

Aquí irán (spec 006) `Harness.tla` y `Regenerations.tla`, cada una con su `.cfg` (modelo pequeño), y la tabla de correspondencia acción ↔ transición del código.
Se comprueban con TLC: JDK Temurin 21 portable y `tla2tools.jar` de la release oficial (`github.com/tlaplus/tlaplus/releases`), sin instalar nada.
Ejecución: `java -XX:+UseParallelGC -jar tla2tools.jar -config Harness.cfg -workers auto Harness.tla` desde `tla/`.
CI (job `tla` de `.github/workflows/ci.yml`) ejecuta TLC sobre cada `tla/*.tla` que tenga `.cfg`; TLC no envía scores a Langfuse.
