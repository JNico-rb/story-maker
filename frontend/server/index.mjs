// Servidor de lectura del visor.
//
// Sirve el contenido de novelas/ como JSON. SOLO LEE: no hay una sola ruta que
// escriba, borre o mueva nada, y el único directorio al que puede llegar es la
// carpeta de novelas. Ver specs/functional.md §9.2.
//
// Sin dependencias: node:http y node:fs bastan, y así el repositorio sigue
// pudiendo generar novelas con cero paquetes instalados.

import { createServer } from 'node:http'
import { resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { leerCapitulo, leerDocumento, leerLectura, leerNovela, listarNovelas } from './novelas.mjs'

const PUERTO = Number(process.env.PUERTO_API ?? 5170)
const RAIZ_NOVELAS = resolve(
  process.env.NOVELAS_DIR ?? fileURLToPath(new URL('../../novelas', import.meta.url)),
)

/** Un slug es un nombre de carpeta del harness: minúsculas, dígitos y guiones. */
const SLUG_VALIDO = /^[a-z0-9][a-z0-9-]{0,99}$/

function responder(res, estado, cuerpo) {
  const json = JSON.stringify(cuerpo)
  res.writeHead(estado, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'access-control-allow-origin': '*',
  })
  res.end(json)
}

const noEncontrado = (res, que) => responder(res, 404, { error: `No se encuentra ${que}.` })

async function enrutar(url, res) {
  const partes = url.pathname.split('/').filter((p) => p !== '')

  if (partes[0] !== 'api') return noEncontrado(res, 'esa ruta')

  if (partes.length === 2 && partes[1] === 'salud') {
    return responder(res, 200, { ok: true, raiz: RAIZ_NOVELAS })
  }

  if (partes[1] !== 'novelas') return noEncontrado(res, 'esa ruta')

  if (partes.length === 2) {
    return responder(res, 200, { novelas: await listarNovelas(RAIZ_NOVELAS) })
  }

  const slug = decodeURIComponent(partes[2] ?? '')
  if (!SLUG_VALIDO.test(slug)) return responder(res, 400, { error: 'Slug no válido.' })

  if (partes.length === 3) {
    const novela = await leerNovela(RAIZ_NOVELAS, slug)
    return novela ? responder(res, 200, novela) : noEncontrado(res, `la novela «${slug}»`)
  }

  if (partes[3] === 'lectura' && partes.length === 4) {
    const lectura = await leerLectura(RAIZ_NOVELAS, slug)
    return lectura ? responder(res, 200, lectura) : noEncontrado(res, `la novela «${slug}»`)
  }

  if (partes[3] === 'capitulos' && partes.length === 5) {
    const numero = Number(partes[4])
    if (!Number.isInteger(numero) || numero < 1) {
      return responder(res, 400, { error: 'Número de capítulo no válido.' })
    }
    const capitulo = await leerCapitulo(RAIZ_NOVELAS, slug, numero)
    return capitulo ? responder(res, 200, capitulo) : noEncontrado(res, `el capítulo ${numero}`)
  }

  if (partes[3] === 'documentos' && partes.length >= 5) {
    const id = partes.slice(4).map(decodeURIComponent).join('/')
    const documento = await leerDocumento(RAIZ_NOVELAS, slug, id)
    return documento ? responder(res, 200, documento) : noEncontrado(res, `el documento «${id}»`)
  }

  return noEncontrado(res, 'esa ruta')
}

export const servidor = createServer((req, res) => {
  // Solo lectura, también a nivel de protocolo.
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { allow: 'GET, HEAD' })
    return res.end()
  }

  const url = new URL(req.url ?? '/', 'http://localhost')
  enrutar(url, res).catch((error) => {
    console.error('[visor] error al leer', url.pathname, error)
    responder(res, 500, { error: 'Error leyendo la carpeta de novelas.' })
  })
})

export function arrancar() {
  return new Promise((listo) => {
    servidor.listen(PUERTO, '127.0.0.1', () => {
      console.log(`[visor] servidor de lectura en http://127.0.0.1:${PUERTO}`)
      console.log(`[visor] leyendo ${RAIZ_NOVELAS}`)
      listo(servidor)
    })
  })
}

// Arranca solo si se ejecuta directamente (pnpm dev:api), no al importarlo.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  arrancar()
}
