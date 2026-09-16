// `pnpm dev`: levanta el servidor de lectura y la web con un solo comando.
//
// Los dos viven en este mismo proceso: Vite se arranca por su API de Node, no
// como proceso hijo. Así no hay que lanzar ejecutables del sistema, que en
// Windows obliga a pasar por el shell y Node lo rechaza desde su versión 20.

import { createServer as crearServidorWeb } from 'vite'
import { arrancar } from './index.mjs'

await arrancar()

const web = await crearServidorWeb()
await web.listen()
web.printUrls()

async function parar() {
  await web.close()
  process.exit(0)
}

for (const senal of ['SIGINT', 'SIGTERM']) {
  process.on(senal, () => {
    void parar()
  })
}
