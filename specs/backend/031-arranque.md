# 031 — Arranque

> Carril: X (C05 en el carril Y) · Depende de: 002, 008, 011, 012, 013, 016 · Estado: aprobada sin revisión (decisión del usuario, 2026-09-24)

## Objetivo

Que el servidor real haga lo que las pruebas de cada spec ya hacen por separado. Cada spec entregó sus piezas con dependencias inyectadas, pero nadie las monta: hoy `serve` levanta la aplicación sin base, sin rutas de API y sin worker, así que ninguna ejecución sale de la cola y el canal denso no tiene modelo de incrustación. Esta spec es el montaje único que comparten `serve`, `example` y `evals run` (Arq. §1.4: un proceso).

## Alcance

- `serve` monta la aplicación completa a partir de los ajustes (§15.5) y de `config.json`: base, secreto JWT, puerto de agente de `LLM_PROVIDER` (§15.2), observabilidad, workspace, policy, verificador formal (`FORMAL_VERIFIER`), render del PDF e incrustaciones.
- El worker del mismo proceso: arranca con el servidor, toma la cola y se apaga con él (sustituye a los antiguos 011-C33 y 011-C34).
- Los prompts de los roles salen de su fichero del workspace, con su versión de Langfuse (§13.4).
- El adaptador de incrustaciones con `fastembed` (§6.3), el único que no existía.
- Cortar una sesión de rol abierta al parar, sin tareas colgadas.

## Fuera de alcance

- La lógica de cada pieza: la cola, el worker y la producción → 011; el gate → 012; el PDF → 013; la recuperación → 016; `example` y `evals run` → 020 (usan este montaje).
- El revisor visual (017) y el servidor MCP (015): fuera de alcance del proyecto; el montaje no los arranca.

## Comportamiento observable

**Convenciones.** Las pruebas usan el doble falso del puerto de agente (003), el doble nulo de observabilidad (001), el doble del verificador formal y una base de fixture en un directorio de datos temporal. Ninguna prueba llama a un modelo, a Langfuse ni a GitHub.

### 031-C01 — `serve` monta la API completa (T)
- **Sostiene:** Arq. §1.4, §15 (API), §15.5.
- **Dado** ajustes válidos, una base inicializada y el compilado del frontend
- **Cuando** se construye el servidor como lo hace `serve`
- **Entonces** responden, sobre esa base, el registro y el acceso (002), las novelas, la entrevista, los textos libres y el brief (008), las ejecuciones (011), las versiones, la lectura y el PDF (013), la story bible y la SPA. Sin compilado del frontend arranca igual, sin la SPA (001).

### 031-C02 — Arrancar el servidor pone el worker a tomar la cola (T)
- **Sostiene:** Arq. §9.1 (cola y worker), §13.4, §15.2.
- **Dado** una generación `queued` y el servidor parado
- **Cuando** el servidor arranca (tras 011-C25)
- **Entonces**:
  - el worker del mismo proceso toma la ejecución sin ninguna otra orden y la lleva hasta `published` (con el doble guionizado para publicar);
  - el puerto de agente que recibe es el de `LLM_PROVIDER` con los perfiles de rol de `config.json`;
  - planner, writer, editor y juez reciben el prompt de su fichero del workspace, y cada `SesionDeRol` guarda su versión (la de Langfuse con `LANGFUSE_PROMPT_LABEL`; sin las variables de Langfuse, el fichero sin versión: doble nulo de §13.6).

### 031-C03 — Parar el servidor apaga el worker sin perder nada (T)
- **Sostiene:** Arq. §9.1, §9.2.
- **Dado** el servidor con una ejecución `running` y otra `queued`
- **Cuando** el servidor se detiene
- **Entonces**:
  - el worker deja de tomar ejecuciones y el proceso termina sin tareas colgadas, aunque hubiera una sesión de rol abierta;
  - la `queued` sigue `queued`; la `running` no cambia hasta el siguiente arranque, que aplica 011-C25;
  - no queda ningún capítulo aceptado a medias.

### 031-C04 — Una novela nueva usa el modelo de incrustación real (T)
- **Sostiene:** Arq. §6.3, §15.4 (`retrieval.embedding_model`).
- **Dado** el montaje de `serve`
- **Cuando** se sincronizan las tarjetas de una versión
- **Entonces** los vectores los calcula el adaptador de incrustaciones local con el `embedding_model` de la novela, no el doble.

### 031-C05 — El adaptador de incrustaciones (T)
- **Sostiene:** Arq. §6.3; `definitions.md` (tarjetas y `embeddings`).
- **Entrada:** textos y un nombre de modelo, con la librería de incrustaciones sustituida por un doble en la prueba.
- **Salida:** un vector por texto, en el orden de entrada. Un modelo que no carga, o que no devuelve un vector por texto, da el fallo de incrustación que ya tratan 016 y 011.

### 031-C06 — `example` y `evals run` sirven la vista mientras procesan la cola (T)
- **Sostiene:** Arq. §14.2 (la `VistaDeVersion` en `STORY_MAKER_BASE_URL` con token de vista), 017-C02 (el revisor visual recibe esa dirección); añadido 2026-09-25: sin servidor, la etapa 3 del gate no puede navegar la vista y ninguna novela de `example` o `evals run` publica.
- **Dado** el montaje de `example` o de `evals run`, con el puerto de `STORY_MAKER_BASE_URL` libre
- **Cuando** el worker del montaje procesa la cola
- **Entonces** mientras dura, `GET /view/versions/{id}?token=…` en `STORY_MAKER_BASE_URL` responde la vista de esa versión, como con `serve`; ese servidor no arranca un segundo worker (solo toma la cola el del montaje), y al terminar la orden el puerto queda libre.
- **Rechazo:** con el puerto ocupado (p. ej. un `serve` en marcha), la orden termina con código distinto de 0 y un mensaje que lo nombra, sin crear novela ni ejecución.

## Invariantes

| ID | Invariante | Clase | Cómo se comprueba |
|---|---|---|---|
| 031-I1 | El montaje es uno: `serve`, `example` y `evals run` lo comparten; ninguna orden monta sus piezas por su cuenta | I | `verificador` al cerrar |
| 031-I2 | Ninguna prueba de esta spec llama a un modelo, a Langfuse ni a GitHub | T | la suite corre sin red (los dobles de 003, 001 y del verificador) |

## Docs referenciados

- `architecture.md` §1.4, §6.3, §9.1, §9.2, §13.4, §13.6, §15.2, §15.4, §15.5, §15.9.
- `definitions.md` §5 (`Ejecucion`, `SesionDeRol`).
- Specs: 001, 002, 008, 011 (C25), 012, 013, 016, 020.
