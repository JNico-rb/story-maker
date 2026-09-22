# 002 — CFG · Configuración y creación de la ejecución

- [ ] Spec approved   <- only the user marks this

## Objetivo

Validar la entrada y rechazar lo imposible antes de gastar nada.

## Alcance

Validación de la configuración y creación de la ejecución.

**Fuera de alcance:** la calibración de umbrales, cuotas y techos. `architecture.md` §10.2: fijarlos hoy sería inventarlos.

## Requisitos

| # | Requisito | Prioridad | Clase |
|---|---|---|---|
| RF-CFG-1 | El sistema valida la aritmética de `config.estructura` antes de ejecutar nada, y rechaza las combinaciones imposibles nombrando los parámetros incompatibles | Obligatorio | T, A |
| RF-CFG-2 | La sobredeterminación es inexpresable: `config.estructura` declara `objetivo_palabras`, `capitulos` y `forma_distribucion`, y el resto se deriva. No existe campo para escribir un estado inconsistente | Obligatorio | A |
| RF-CFG-3 | El sistema valida `config.recuperacion` al crear la ejecución: tabla de cuotas completa, una entrada por par (colección, consumidor), enteros ≥ 0, y `modelo_incrustacion` con valor | Obligatorio | T |
| RF-CFG-4 | Una entrada ausente de la tabla de cuotas impide crear la ejecución, con error que nombra el par que falta | Obligatorio | T |
| RF-CFG-5 | Una cuota negativa o no entera impide crear la ejecución | Obligatorio | T |
| RF-CFG-6 | Una colección o un consumidor desconocidos impiden crear la ejecución | Obligatorio | T |
| RF-CFG-7 | Prosa con cuota mayor que 0 para el escritor o para el crítico de canon impide crear la ejecución. La prosa es del crítico de oficio y de nadie más | Obligatorio | T |
| RF-CFG-8 | Una cuota de 0 es válida y significa que esa colección no entra en la ventana de ese consumidor | Obligatorio | T |
| RF-CFG-9 | No existen cuotas por defecto en el código: sin tabla, no se arranca | Obligatorio | T |
| RF-CFG-10 | El sistema valida que `config.operacion` declara directorio de ejecuciones y ruta de la biblioteca de canon. Sin ellas no se crea la ejecución, con error que nombra la que falta. No existen rutas por defecto en el código | Obligatorio | T |
| RF-CFG-11 | `config.calidad` y `config.recuperacion` no son editables por el usuario final | Obligatorio | A |
| RF-CFG-12 | Los campos estructurales se congelan al aprobar el outline; los poéticos admiten ajuste en caliente | Obligatorio | T |
| RF-CFG-13 | El identificador del modelo de incrustación se congela al crear la ejecución y viaja con el índice. Cambiarlo después en configuración no afecta a una ejecución ya creada | Obligatorio | T |
| RF-CFG-14 | El identificador del modelo de lenguaje declarado en `config.operacion` se congela al crear la ejecución. Cambiarlo después no afecta a una ejecución ya creada: el cambio se ignora y queda anotado en el informe como resolución de conflicto | Obligatorio | T |
| RF-CFG-15 | Cada parámetro estructural genera un `Criterio` de la puerta dura | Obligatorio | T |

## Docs de referencia

`architecture.md` §3.6, §5, §6.2; `definitions.md` §6
