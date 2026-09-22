# 001 — BASE · Base técnica del backend

- [ ] Spec approved   <- only the user marks this

## Objetivo

Levantar el backend sobre el stack decidido y hacer comprobables sus restricciones técnicas antes de la primera feature.

## Alcance

Proyecto y stack, tipado y análisis estático, estructura de módulos y sus reglas de dependencia, puerto del proveedor de modelo, persistencia SQLite con índice, `fastembed` en Windows y exportación del esquema OpenAPI. Tablas e interfaces con el exterior: [design.md](design.md).

**Dependencias externas:** un proveedor de modelo de lenguaje accesible por red, y la descarga inicial del modelo de incrustación.

**Fuera de alcance:** el frontend, cliente delgado, fuera del backend V1.

## Restricciones

| # | Restricción | Origen (§ de `architecture.md`) |
|---|---|---|
| R4 | Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, dependencias con `uv` | §9.1, §11 |
| R5 | Índice en el mismo fichero SQLite que el canon, con `sqlite-vec` y FTS5 | §3.14 |
| R6 | Vectores producidos por `fastembed`, local y sin servicio | §3.14 |
| R8 | Ninguna fase importa a otra; `domain` no importa nada | §9.2 |
| R9 | Entorno de desarrollo Windows sin privilegios de administrador y sin VC++ Redistributable: el runtime de Visual C++ se resuelve en espacio de usuario y los enlaces simbólicos de la caché de modelos se desactivan | §3.14 |

## Requisitos no funcionales

| # | Requisito | Clase |
|---|---|---|
| RNF-5 | **Tipado estricto.** Anotaciones en todo el backend y comprobador estricto; modelos validados en tiempo de ejecución en los bordes: entrada HTTP y salida de modelo | A |
| RNF-6 | **Análisis estático.** Ruff sobre todo el backend; escaneo de secretos, de construcción dinámica de consultas y de manejo de rutas al escribir el manuscrito | A |
| RNF-7 | **Aislamiento de módulos.** La regla de dependencia de `architecture.md` §9.2 se comprueba en CI, no por convención | A |
| RNF-8 | **Reparto del recuperador.** Las reglas puras en `domain`, los clientes de incrustación, FTS5 y `sqlite-vec` en `platform`, la política de consulta en cada fase. No existen `commons`, `shared` ni `utils`. Se comprueba en CI | A |
| RNF-9 | **Puerto del proveedor de modelo.** La interfaz vive en `platform` y ninguna fase importa un cliente concreto. Existe además un doble determinista que devuelve respuestas fijas con su uso de entrada y salida y su coste | A |
| RNF-11 | **Sin servicios añadidos.** El índice vive en el mismo fichero SQLite que el canon; no se introduce ningún servicio externo de vectores | A |
| RNF-12 | **Un fichero por ejecución.** Cada ejecución vive en su propio fichero SQLite con canon, artefacto narrativo, estado e índice. La biblioteca de canon vive en un fichero compartido aparte. Las dos rutas salen de `config.operacion` | T |
| RNF-13 | **Portabilidad del entorno de desarrollo.** El backend arranca en Windows sin privilegios de administrador, con el runtime de Visual C++ resuelto en espacio de usuario | D |
| RNF-14 | **Pruebas junto al código.** Las pruebas viven dentro de cada slice | I |
| RNF-15 | **Esquema OpenAPI exportable en estático**, sin arrancar servidor, para generar el cliente del frontend | T |

## Docs de referencia

`architecture.md` §3.14, §9.1, §9.2, §11; `verification.md` §3
