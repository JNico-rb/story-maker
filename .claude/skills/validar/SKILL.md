---
name: validar
description: Puntúa el manuscrito de una novela ya terminada y da el delta contra la línea base. Usar cuando el usuario quiera medir la calidad del texto producido, comparar dos configuraciones ("¿el modelo barato escribe peor?"), congelar una línea base o ver el resultado de una validación anterior. Nunca dentro de /novela.
argument-hint: <carpeta> [--congelar-base] [--publicar] | estado
---

# /validar — validador de manuscrito

Mides el **texto producido**, no lo que los revisores declararon. Es toda la diferencia con §8.3: cuatro de sus seis métricas son autoinformadas, y por eso el sistema devolvió `6/6 CUMPLE` sobre un manuscrito con 30 defectos verificados a mano (E5c). Aquí el texto está delante y no opina.

**Fuera del harness** (spec §9.6, mismo estatus que §9.2–§9.5): `/novela` no te llama nunca, no escribes en `novelas/` —solo lees— y Langfuse es fail-open.

**Esto no es un bucle.** Mide una vez y devuelve un número. No hay condiciones de parada ni vectores de mejora, y **está decidido, no olvidado**: forzar un bucle donde no lo hay produce bloques de adorno que luego nadie respeta. Si algún día se itera sobre `config.json` usando esto como juez, ese bucle traerá su propio STOP.

Argumentos recibidos: `$ARGUMENTS`

## 0. Comandos

| Forma | Hace |
|---|---|
| `<carpeta>` | §1 → §3 |
| `<carpeta> --congelar-base` | igual, y además fija esa medición como línea base |
| `<carpeta> --publicar` | igual, y publica en Langfuse (fail-open) |
| `estado` | §4, solo lectura |

## 1. Comprobar que se puede medir

```
Bash: python herramientas/validacion/comprobar_patrones.py
Bash: python herramientas/validacion/validar.py <carpeta> [flags]
```

El primero comprueba el detector antes de usarlo: que cada clase casa con sus ejemplos positivos, que no se lleva sus negativos, y que **ningún patrón lleva dentro tres palabras seguidas de una cita del etiquetado**. Esa última es la que impide que el detector se corrija su propio examen, y es la misma regla que `comprobar_variante.py` impone al optimizador.

El segundo comprueba las tres precondiciones del TRIGGER y para si falta una:

1. La carpeta pasa §8.7 (etapa `completa` y `manuscrito.md` presente).
2. El **detector** está congelado: su hash coincide con el de la línea base.
3. La **escala** está congelada: su versión coincide con la de la línea base.

Si 2 o 3 fallan, no se compara nada: hay que re-puntuar la base primero. Un delta entre dos detectores distintos no mide el manuscrito, mide el detector.

## 2. Qué sale

`validaciones/<slug>/score.json` y `validaciones/<slug>/informe.md`. Dos dimensiones, cada una en tasa por mil palabras y normalizada a 0–1 donde 1 es mejor, más un índice global ponderado:

| Dimensión | Qué cuenta | Peso |
|---|---|---:|
| `lengua` | Aciertos del detector de agramaticalidades | 0,87 |
| `repeticion` | 6-gramas compartidos entre pares de capítulos | 0,13 |

Los pesos salen del recuento de E5 (13 defectos de lengua, 2 de cohesión), no de una intuición. Los topes de las escalas salen de las tasas medidas. Todo está declarado con su porqué en `herramientas/validacion/escala.json`.

## 3. Cómo se lee el número, y cómo no

Tres reservas que el informe escribe siempre y que **tienes que repetir al usuario**, no dejarlas solo en el fichero:

- **n=1 por configuración.** Otra ejecución con la misma config daría otro manuscrito y otro score. No se puede separar el efecto de la configuración del azar de esa generación, así que **ninguna mejora se declara establecida**. Nunca digas «haiku escribe peor»: di «esta novela de haiku puntuó 0,365 menos que esta novela de opus».
- **Recall 0,462.** El detector ve 6 de los 13 defectos etiquetados a mano (`calibracion.md`). «0 hallazgos» significa «ninguno de los que sabe ver», no «ninguno». El nivel absoluto es optimista; los deltas entre manuscritos no, porque el sesgo es el mismo en los dos.
- **Tres clases de E5 fuera.** Coherencia interna, verosimilitud técnica y mundo post-IA no se miden: exigen un juez LLM independiente, y el único modelo juez disponible es `openrouter/free`, que no garantiza cuál contesta (A14).

## 4. estado

Lee `validaciones/_base.json` y los `score.json` que haya, y resume en una tabla. No mides nada, no congelas nada.

## 5. Lo que este validador no hace, nunca

- No se invoca desde `/novela`, ni al revés.
- No escribe en `novelas/`: lee `estado.json` para saber qué intento se aprobó y lee esos capítulos.
- No sustituye a §8.3. Aquellas son métricas de **proceso**, autoinformadas; estas son de **producto**, medidas sobre el texto. Cuando las dos discrepen, el informe dice de dónde sale cada número y decide el usuario.
- No declara mejoras. Da un delta y sus reservas.
