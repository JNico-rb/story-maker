# frontend — el visor

Aplicación web de **solo lectura** sobre `novelas/`. No forma parte del harness: ver [specs/functional.md](../specs/functional.md) §9.2, que manda sobre este fichero.

## La regla que no se negocia

**El visor solo lee.** No invoca agentes, no decide nada del flujo y no escribe, borra ni mueve un solo byte dentro de `novelas/`. El servidor responde `405` a cualquier método que no sea `GET` o `HEAD`, y su única raíz accesible es la carpeta de novelas.

Si alguna vez hace falta que el visor escriba algo, eso es un cambio de diseño: primero la spec y el [CHANGELOG](../CHANGELOG.md), después el código (regla 5 de [CLAUDE.md](../CLAUDE.md)).

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
├── server/                  # Servidor de lectura (Node, sin dependencias)
│   ├── index.mjs            # HTTP y rutas
│   ├── novelas.mjs          # Interpreta novelas/<slug>/ (spec §3)
│   ├── yaml.mjs             # El subconjunto de YAML de las plantillas
│   └── dev.mjs              # `pnpm dev`: servidor + web de una vez
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

**El vocabulario es el de la spec §0.** Los términos del proyecto se escriben en castellano y exactamente igual que allí: `Capitulo`, `Intento`, `Informe`, `veredicto`, `gravedad`, `libroEstado`. Lo demás va en inglés, como es costumbre en React. Un término nuevo entra antes en el glosario de la spec que en este código.

**El visor no calcula métricas de calidad.** Las de §8.3 las calcula el harness y viven en `informe-cierre.md`. Si no existen, se dice que aún no las hay. Duplicar esa regla aquí permitiría que la web y el harness dieran cifras distintas sin saber cuál miente.

## Estilo de código

- Componentes pequeños y legibles de un vistazo. Uno por fichero por defecto.
- Primero `useState`, `useReducer` y valores derivados; una librería de estado global solo si el problema lo pide de verdad.
- Antes las capacidades del navegador (`FormData`, `Date`, `Intl`, `URL`, métodos de colección) que un paquete.
- Todo el HTTP detrás de `src/lib/api.ts`.
- Las formas de la API viven como tipos en `src/lib`; los componentes consumen tipos de dominio.
- **Lo que puede ir mal se ve**: carga, fallo del servidor, refresco fallido, intento sin informe, novela sin capítulos. Cada vista que pide datos sabe enseñar sus tres estados (`components/ui/Estados.tsx`).

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
