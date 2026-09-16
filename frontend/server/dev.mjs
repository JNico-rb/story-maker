// `pnpm dev`: levanta el servidor de lectura y la web con un solo comando.
//
// El servidor va dentro de este mismo proceso y Vite como proceso hijo, para no
// depender de ningún paquete que ejecute cosas en paralelo.

import { spawn } from 'node:child_process'
import { arrancar } from './index.mjs'

await arrancar()

// pnpm.cmd en Windows: así no hace falta shell, que Node desaconseja con argumentos.
const pnpm = process.platform === 'win32' ? 'pnpm.cmd' : 'pnpm'
const vite = spawn(pnpm, ['exec', 'vite'], { stdio: 'inherit' })

vite.on('exit', (codigo) => process.exit(codigo ?? 0))

for (const senal of ['SIGINT', 'SIGTERM']) {
  process.on(senal, () => {
    vite.kill()
    process.exit(0)
  })
}
