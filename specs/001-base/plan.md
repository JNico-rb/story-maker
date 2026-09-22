# 001 — BASE · Plan

- [ ] Plan approved   <- only the user marks this

Spec: [spec.md](spec.md). Diseño: [design.md](design.md). Verificación: la clase de cada paso; métodos en `docs/verification.md` §3.

Prerrequisito de todas las demás specs, no casos de aceptación: nada de aquí se enuncia como entrada → salida. Se cierra antes del primer paso de `002-cfg-configuracion`.

### Steps

- [ ] Proyecto `backend/` con `uv`, Python 3.12+, FastAPI, Pydantic v2 y SQLAlchemy 2 (R4 · clase A)
- [ ] Tipado estricto en todo el backend y modelos validados en tiempo de ejecución en los dos bordes: entrada HTTP y salida de modelo (RNF-5 · clase A)
- [ ] Ruff sobre todo el backend, más escaneo de secretos, de construcción dinámica de consultas y de manejo de rutas al escribir el manuscrito (RNF-6 · clase A)
- [ ] Estructura de módulos de `architecture.md` §9.2 creada: `phases/`, `execution/`, `domain/`, `platform/` (R8 · clase A)
- [ ] Las cuatro reglas de dependencia de `architecture.md` §9.2 se comprueban en CI, no por convención (RNF-7 · clase A)
- [ ] El recuperador reparte sus piezas entre `domain`, `platform` y las fases, y no existen `commons`, `shared` ni `utils`; se comprueba en CI (RNF-8 · clase A)
- [ ] El puerto del proveedor de modelo vive en `platform`, ninguna fase importa un cliente concreto, y existe un doble determinista que devuelve respuestas fijas con su uso y su coste (RNF-9 · clase A)
- [ ] Una conexión SQLite carga `sqlite-vec` y FTS5 sobre esa misma conexión, sin servicio externo (R5, RNF-11 · clase A)
- [ ] Cada ejecución vive en su propio fichero SQLite y la biblioteca de canon en el fichero compartido, con las dos rutas leídas de `config.operacion` (RNF-12)
- [ ] `fastembed` arranca en Windows sin privilegios de administrador y sin red tras la descarga inicial, con VC++ en espacio de usuario y symlinks de caché desactivados (R6, R9, RNF-13 · clase D)
- [ ] El esquema OpenAPI se exporta en estático, sin arrancar servidor (RNF-15)
- [ ] Las pruebas viven dentro de cada slice, no en un árbol aparte (RNF-14 · clase I)

### Closing

- [ ] Full suite green, type checks clean
- [ ] Spec updated, or confirmed still true
- [ ] Docs updated, or confirmed still true
