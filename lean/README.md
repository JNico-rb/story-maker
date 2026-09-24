# Lean — validador formal de la cronología

Aquí irá (spec 007) la librería `Chronology`: tipos de la cronología, invariantes T1–T5 y sus comprobadores, y el fichero generado desde la story bible de SQLite.
La verificación es `lake build` sobre ese fichero; si falla, la versión no se publica.
No corre en el portátil de desarrollo (Smart App Control bloquea los binarios de Lean): se construye en GitHub Actions (job `lean` de `.github/workflows/ci.yml`).
Toolchain fijado en `lean-toolchain`; paquete sin dependencias externas.
