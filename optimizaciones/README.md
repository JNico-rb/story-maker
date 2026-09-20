# optimizaciones/

Registro local del bucle de [specs/technical.md](../specs/technical.md) §9.5. Lo escribe la skill [`/optimizar`](../.claude/skills/optimizar/SKILL.md); nada de aquí entra en el harness de la novela.

**Se versiona en git**, entero. `lecciones.md` es la única memoria del bucle entre ejecuciones: si se pierde, el optimizador vuelve a proponer variantes ya descartadas, que es justo lo que tiene prohibido.

```
optimizaciones/
├── <agente>/
│   └── lecciones.md              una linea por variante probada, entre ejecuciones
└── <agente>-<AAAAMMDD-HHMM>/     una ejecucion
    ├── ejecucion.json            agente, metrica, conjunto y su hash, topes, objetivo
    ├── produccion.md             copia del prompt vigente al arrancar
    ├── produccion.hash           su hash; §7 de la skill comprueba la restauracion
    ├── mejor.md                  la mejor variante aceptada hasta ahora
    ├── vueltas.jsonl             una linea por vuelta, tambien las rechazadas
    ├── informe.md                cierre: motivo, curva, invocaciones, reservas
    └── vuelta-NN/
        ├── diagnostico.md        perfil de fallos AGREGADO que ve el optimizador
        ├── propuesta.json        operacion, hipotesis, cambio, leccion
        ├── variante.md           el fichero del agente que se instalo
        ├── busqueda/<id>.json    informe del agente por caso, + score.json
        └── control/<id>.json     idem
```

## Las dos cosas que se leen primero

- **`informe.md`**: dice si la ejecución paró o abortó, cuál fue la mejor variante, y **cuántas veces se consultó el split de control**. Esa última cifra es la reserva con la que hay que leer el resultado: con 10 casos de control y 10 consultas, la ganadora puede estar ajustada a esos 10 casos.
- **`vueltas.jsonl`**: la curva. Una vuelta con `aceptada: false` y `invocaciones: 0` es una variante que `comprobar_variante.py` paró antes de instalar; el `motivo` dice cuál de las cinco prohibiciones tocó.

## Lo que no hay aquí

Ningún prompt promovido. El bucle deja un **candidato** en `mejor.md` y, si hubo red, en Langfuse con esa etiqueta. Moverlo a producción es copiarlo sobre `.claude/agents/<agente>.md` y hacer commit, y eso lo hace el usuario (§9.5.4).
