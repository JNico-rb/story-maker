# Calibración del detector de lengua

Detector `v1`, hash `59ca75b`. Medido contra [etiquetado/ascensores-lengua-v1.json](etiquetado/ascensores-lengua-v1.json), que es verdad de campo etiquetada a mano sobre los manuscritos completos de las dos novelas del repositorio.

| | Palabras | Marcados por el detector | Etiquetados a mano |
|---|---:|---:|---:|
| A | 8271 | 0 | 0 |
| B | 6426 | 6 | 13 |

| Medida | Valor | Qué significa |
|---|---:|---|
| Precisión | **1.000** | de lo que marca, cuánto es de verdad un error |
| Recall | **0.462** | de los 13 defectos etiquetados, cuántos ve |
| Recall sobre el techo | **1.000** | de los 6 que alguna clase del v1 puede cazar |

**No vistos**: b01, b03, b06, b07, b08, b11, b13.

## El techo, que es lo importante

De los 13 defectos etiquetados, solo **6** caen en una clase que el detector v1 puede expresar. Los otros 7 exigen cosas que una lista de patrones no da: un léxico para las palabras inexistentes, y análisis morfosintáctico para el tiempo verbal. Están declarados uno a uno en el etiquetado con `detectable_v1: false`.

Leído de otra forma: **el recall de 0.46 no es un fallo del detector, es el alcance de la v1**. Para subirlo hace falta una dependencia nueva (spaCy o language-tool), y eso ata la línea base a una versión externa.

## Cuándo hay que rehacer esto

Cuando cambie `patrones.py` (el hash lo delata), cuando se añada un manuscrito al etiquetado, o cuando entre una dependencia de análisis lingüístico. Mientras tanto, estos dos números son los que hay que citar al lado de cualquier puntuación de lengua.
