# frontend — el visor y el estudio

Aplicación web con dos mitades sobre la misma carpeta. El **visor** enseña novelas ya generadas ([specs/technical.md](../specs/technical.md) §9.2); el **estudio** recoge los inputs del usuario y lanza el harness (§9.4). La spec manda sobre este fichero.

## Las reglas que no se negocian

Eran una y ahora son cuatro, porque el estudio sí escribe y sí ejecuta. Ninguna es opinable:

1. **Nada de `frontend/` escribe en `novelas/`.** Ni el visor ni el estudio: ni un byte, ni crear, ni borrar, ni mover. Esa carpeta es del harness en exclusiva (spec §3.1), y es de lo que cuelga toda la inmutabilidad. Lo que el estudio escribe va a `encargos/<slug>/`, y nada más.
2. **El estudio es una fachada, no un camino alternativo.** No decide nada del flujo, no invoca a ningún agente, no calcula métricas, no elige el mejor intento, no recalcula un veredicto y no aprueba nada por su cuenta. Todo lo que hace se reduce a componer texto, ejecutar el mismo comando `/novela` que ejecutaría el usuario y enseñar lo que el harness escribe. **Si una regla de negocio aparece en este código, está en el sitio equivocado**: vive en la skill y en los procedimientos.
3. **El servidor solo escribe donde se le permite.** Las rutas de escritura son exclusivamente las de `encargos/`; todo lo demás sigue respondiendo `405` a cualquier método que no sea `GET` o `HEAD`. Dos raíces accesibles y ninguna más: `novelas/` en solo lectura y `encargos/` en lectura y escritura.
4. **Lanzar el harness no se salta los permisos.** Se ejecuta apoyándose en la lista de `.claude/settings.json`, que se versiona. Nunca con `bypassPermissions`: un botón de una web local no puede tener permiso para cualquier cosa. Lo que no esté permitido se deniega, el harness para limpio y se ve.

Borrar `frontend/` entero tiene que seguir dejando el sistema capaz de generar la misma novela desde una terminal. Esa es la prueba de que las cuatro reglas se cumplen.

Cualquier cambio a esto es un cambio de diseño: primero la spec y el [CHANGELOG](../CHANGELOG.md), después el código (regla 6 de [CLAUDE.md](../CLAUDE.md)).

## Stack

- **Vite** con una aplicación React de una sola página. No es Next.js: nada de SSR, componentes de servidor, rutas por fichero ni servidor de aplicación.
- **TypeScript estricto**. Antes `unknown` y un estrechamiento que `any`.
- **Tailwind CSS** (v4, configurado en `src/index.css` con `@theme`) y la hoja global. Nada de CSS modules, styled-components ni otro sistema de estilos.
- **APIs nativas del navegador** y `fetch`. Nada de Axios ni de otro envoltorio HTTP.
- **pnpm** para las dependencias.

El stack está cerrado salvo que Jaime apruebe un cambio.

## Estructura

```text
frontend/
├── server/                  # Servidor (Node, sin dependencias)
│   ├── index.mjs            # HTTP y rutas
│   ├── novelas.mjs          # Interpreta novelas/<slug>/ (spec §3). SOLO LEE
│   ├── encargos.mjs         # Escribe encargos/<slug>/ (spec §9.4)
│   ├── harness.mjs          # Lanza y habla con el harness. Único sitio que ejecuta nada
│   ├── yaml.mjs             # El subconjunto de YAML de las plantillas
│   └── dev.mjs              # `pnpm dev`: servidor + web de una vez
├── public/                  # Servido tal cual en la raíz: los recursos de marca
├── src/
│   ├── components/          # Un componente por fichero
│   │   └── ui/              # Primitivos visuales reutilizables
│   ├── lib/                 # Cliente de API, entorno, tipos y ayudas puras
│   ├── App.tsx              # Flujo de la aplicación
│   ├── main.tsx             # Punto de entrada
│   └── index.css            # Tailwind y los tokens del tema
└── index.html
```

## Dónde va cada cosa

**El servidor sabe de ficheros; la web no.** `server/novelas.mjs` es el único sitio que conoce rutas, nombres de fichero y la estructura de la spec §3. Devuelve un modelo ya montado y los componentes solo lo pintan. Si la spec cambia, se toca ahí y en ningún otro sitio.

**`server/harness.mjs` es el único fichero que ejecuta algo.** Ahí viven el arranque en segundo plano, el identificador de sesión y el diálogo con el harness. Ningún otro módulo lanza procesos, y el navegador nunca decide qué comando se ejecuta: manda una intención (`empezar`, `responder`, `confirmar`, `pedir cambios`) y el servidor la traduce al comando `/novela` que corresponde. Una web que pudiera mandar comandos sería una web que ejecuta lo que le pidan.

**El diálogo en vivo va por SSE, sin dependencias.** `text/event-stream` hacia el navegador con `node:http` pelado, `POST` hacia el servidor. Nada de WebSocket: obligaría a un paquete y a romper la promesa de que el servidor no lleva ninguno.

**El vocabulario es el de la spec §0.** Los términos del proyecto se escriben en castellano y exactamente igual que allí: `Capitulo`, `Intento`, `Informe`, `veredicto`, `gravedad`, `libroEstado`. Lo demás va en inglés, como es costumbre en React. Un término nuevo entra antes en el glosario de la spec que en este código.

**El visor no calcula métricas de calidad.** Las de §8.3 las calcula el harness y viven en `informe-cierre.md`. Si no existen, se dice que aún no las hay. Duplicar esa regla aquí permitiría que la web y el harness dieran cifras distintas sin saber cuál miente.

## Estilo de código

- Componentes pequeños y legibles de un vistazo. Uno por fichero por defecto.
- Primero `useState`, `useReducer` y valores derivados; una librería de estado global solo si el problema lo pide de verdad.
- Antes las capacidades del navegador (`FormData`, `Date`, `Intl`, `URL`, métodos de colección) que un paquete.
- Todo el HTTP detrás de `src/lib/api.ts`.
- Las formas de la API viven como tipos en `src/lib`; los componentes consumen tipos de dominio.
- **Lo que puede ir mal se ve**: carga, fallo del servidor, refresco fallido, intento sin informe, novela sin capítulos. Cada vista que pide datos sabe enseñar sus tres estados (`components/ui/Estados.tsx`).

## Marca

El visor lleva la identidad de **Qaracter**. El original es [`images/qaracter-logo.png`](../images/qaracter-logo.png), en la raíz del repositorio y fuera del frontend: es el activo de la empresa, no un fichero de esta aplicación.

De él salen los tres ficheros de `public/`, que es lo único que el navegador pide:

| Fichero | Qué es | Dónde se usa |
|---|---|---|
| `qaracter-logo.png` | Logotipo completo, 1200 px, fondo transparente | `BarraMarca` |
| `qaracter-isotipo.png` | Solo el símbolo, 256 px | Apertura y colofón de la pestaña Leer, icono de aplicación |
| `favicon.png` | El símbolo a 64 px | Pestaña del navegador |

Se derivaron una vez recortando el original, pasando el blanco del fondo a transparente y reduciendo; no hay que regenerarlos salvo que cambie el logotipo. Si cambia, se sustituye el original y se vuelven a derivar los tres, **sin repintarlos a mano**: el logotipo no se recolorea, no se deforma y no se le añaden efectos.

Los dos colores de la marca están en los tokens de `src/index.css`:

- **`--color-tinta` (`#233441`)**, el azul del logotipo, es la tinta de todo el visor.
- **`--color-marca` (`#ff7932`)**, el naranja, es **solo cromo**: la regla de la barra de marca, el subrayado de la pestaña activa, la barra de progreso, el pulso del refresco y el foco. **Nunca significa un estado.** Aprobado, rechazado y aviso ya tienen verde, rojo y ámbar; un cuarto color cálido los volvería indistinguibles de un vistazo. Para naranja como texto está `--color-marca-fuerte`, que es el único que llega al contraste AA sobre fondo claro.

La pestaña **Leer** manda sobre la marca: allí solo entra el isotipo, centrado, al principio y al final. Nada de cromo naranja sobre el papel.

## Configuración

- `src/lib/env.ts` es la única frontera de entorno. Ningún otro fichero lee `import.meta.env`.
- `VITE_API_BASE_URL` es la dirección del servidor de lectura y se valida al arrancar. Si no está, se usa `/api`, que Vite redirige al servidor local.
- Solo se exponen al navegador las variables con prefijo `VITE_`. Nunca un secreto en un fichero de entorno del frontend.

## Dependencias

- **pnpm y solo pnpm.** Nada de `package-lock.json` ni `yarn.lock`.
- **Ninguna dependencia nueva sin que Jaime la apruebe**, con el motivo y qué hace. Las aprobadas hasta ahora: `vite`, `react`, `react-dom`, `tailwindcss`, `@tailwindcss/vite`, `@tailwindcss/typography`, `marked`, `typescript` y los `@types` correspondientes.
- **El servidor no lleva ninguna**, y así debe seguir: es lo que mantiene la promesa de que generar novelas no necesita instalar nada.
- Versiones fijadas exactas y `pnpm-lock.yaml` commiteado con cada cambio aprobado.
- Se mantienen `savePrefix: ''`, `minimumReleaseAge: 10080` y `minimumReleaseAgeStrict: true` en `pnpm-workspace.yaml`.
- Antes de añadir un paquete que sustituiría a diez líneas claras, no se añade.

## Verificación

```bash
pnpm install --frozen-lockfile
pnpm exec tsc -b --pretty false
pnpm build
```

Y después, **a mano en el navegador** (`pnpm dev`, http://localhost:5173): la lista, las cuatro pestañas, un capítulo con varios intentos, un documento y el registro. Nada de Vitest, Jest, Playwright, Cypress ni ficheros `*.test.*`: la verificación de este proyecto son los tipos, la compilación y mirarlo.
