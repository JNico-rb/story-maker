// Servidor del visor y del estudio.
//
// Dos raíces y dos permisos distintos, y la diferencia es la regla 1 y 3 de
// frontend/CLAUDE.md:
//
//   novelas/   SOLO LECTURA. Ni una ruta escribe, borra o mueve nada. Esa
//              carpeta es del harness en exclusiva (spec §3.1).
//   encargos/  Lectura y escritura. Es lo que el usuario rellena antes de que
//              exista la novela (spec §9.4).
//
// Cualquier método que no sea GET o HEAD se rechaza con 405 salvo en las rutas
// de encargos, que están enumeradas una a una más abajo.
//
// Sin dependencias: node:http y node:fs bastan, y así el repositorio sigue
// pudiendo generar novelas con cero paquetes instalados.

import { createServer } from 'node:http'
import { resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { leerCapitulo, leerDocumento, leerLectura, leerNovela, listarNovelas } from './novelas.mjs'
import {
  PREGUNTAS,
  anotarNovela,
  crearEncargo,
  escribirDecision,
  leerEncargo,
  listarSlugs,
} from './encargos.mjs'
import { actuar, detener, resumenSesion, suscribir } from './harness.mjs'
import { ErrorDeEntrada } from './errores.mjs'

const PUERTO = Number(process.env.PUERTO_API ?? 5170)
const RAIZ_REPO = resolve(
  process.env.REPO_DIR ?? fileURLToPath(new URL('../../', import.meta.url)),
)
const RAIZ_NOVELAS = resolve(process.env.NOVELAS_DIR ?? resolve(RAIZ_REPO, 'novelas'))
const RAIZ_ENCARGOS = resolve(process.env.ENCARGOS_DIR ?? resolve(RAIZ_REPO, 'encargos'))

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

/** Lee el cuerpo de una petición como JSON, con un tope para no comerse la memoria. */
function leerCuerpo(req) {
  return new Promise((listo, fallo) => {
    let bruto = ''
    req.setEncoding('utf8')
    req.on('data', (trozo) => {
      bruto += trozo
      if (bruto.length > 512_000) {
        fallo(new ErrorDeEntrada('El cuerpo de la petición es demasiado grande.'))
        req.destroy()
      }
    })
    req.on('end', () => {
      if (bruto.trim() === '') return listo({})
      try {
        listo(JSON.parse(bruto))
      } catch {
        fallo(new ErrorDeEntrada('El cuerpo de la petición no es JSON válido.'))
      }
    })
    req.on('error', fallo)
  })
}

// ── Lectura: novelas/ ────────────────────────────────────────────────────────

async function enrutarNovelas(partes, res) {
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

// ── Estudio: encargos/ ──────────────────────────────────────────────────────

/** Canal de eventos del harness hacia el navegador. SSE, no WebSocket: cero dependencias. */
function abrirEventos(slug, req, res) {
  res.writeHead(200, {
    'content-type': 'text/event-stream; charset=utf-8',
    'cache-control': 'no-store',
    connection: 'keep-alive',
    'access-control-allow-origin': '*',
  })

  const mandar = (evento) => res.write(`data: ${JSON.stringify(evento)}\n\n`)

  // Quien llega tarde o recarga la página ve lo que ya pasó.
  const { estado, historial, novela } = resumenSesion(slug)
  mandar({ tipo: 'hola', estado, novela, fecha: new Date().toISOString() })
  for (const evento of historial) mandar(evento)

  const desuscribir = suscribir(slug, mandar)

  // Un comentario cada 20 s mantiene viva la conexión a través de proxys.
  const latido = setInterval(() => res.write(': latido\n\n'), 20_000)

  const cerrar = () => {
    clearInterval(latido)
    desuscribir()
    res.end()
  }
  req.on('close', cerrar)
  req.on('error', cerrar)
}

async function enrutarEncargos(partes, req, res, metodo) {
  // GET /api/encargos → lo que hace falta para pintar el formulario.
  if (partes.length === 2 && metodo === 'GET') {
    const slugs = await listarSlugs(RAIZ_ENCARGOS)
    const encargos = []
    for (const slug of slugs) {
      const encargo = await leerEncargo(RAIZ_ENCARGOS, slug)
      if (encargo !== null) {
        const { carpeta: _carpeta, ...resto } = encargo
        encargos.push({ ...resto, sesion: resumenSesion(slug).estado })
      }
    }
    return responder(res, 200, { preguntas: PREGUNTAS, encargos })
  }

  // POST /api/encargos → crea encargos/<slug>/ con idea y precarga.
  if (partes.length === 2 && metodo === 'POST') {
    const cuerpo = await leerCuerpo(req)
    const { slug } = await crearEncargo(RAIZ_ENCARGOS, cuerpo)
    return responder(res, 201, { slug })
  }

  const slug = decodeURIComponent(partes[2] ?? '')
  if (!SLUG_VALIDO.test(slug)) return responder(res, 400, { error: 'Slug no válido.' })

  if (partes.length === 3 && metodo === 'GET') {
    const encargo = await leerEncargo(RAIZ_ENCARGOS, slug)
    if (encargo === null) return noEncontrado(res, `el encargo «${slug}»`)
    const { carpeta: _carpeta, ...resto } = encargo
    return responder(res, 200, { ...resto, sesion: resumenSesion(slug) })
  }

  if (partes[3] === 'eventos' && partes.length === 4 && metodo === 'GET') {
    return abrirEventos(slug, req, res)
  }

  // POST /api/encargos/<slug>/accion → una INTENCIÓN, nunca un comando.
  if (partes[3] === 'accion' && partes.length === 4 && metodo === 'POST') {
    const intencion = await leerCuerpo(req)
    const resultado = await actuar(RAIZ_REPO, RAIZ_ENCARGOS, slug, intencion)
    if (typeof intencion.novela === 'string' && intencion.novela !== '') {
      await anotarNovela(RAIZ_ENCARGOS, slug, intencion.novela)
    }
    return responder(res, 202, resultado)
  }

  // POST /api/encargos/<slug>/decision → la respuesta a ESPERA_APROBACION.
  if (partes[3] === 'decision' && partes.length === 4 && metodo === 'POST') {
    const cuerpo = await leerCuerpo(req)
    const resultado = await escribirDecision(RAIZ_ENCARGOS, slug, cuerpo)
    return responder(res, 200, resultado)
  }

  if (partes[3] === 'detener' && partes.length === 4 && metodo === 'POST') {
    return responder(res, 200, detener(slug))
  }

  return noEncontrado(res, 'esa ruta')
}

// ── Enrutado ────────────────────────────────────────────────────────────────

async function enrutar(url, req, res, metodo) {
  const partes = url.pathname.split('/').filter((p) => p !== '')

  if (partes[0] !== 'api') return noEncontrado(res, 'esa ruta')

  if (partes.length === 2 && partes[1] === 'salud') {
    return responder(res, 200, { ok: true, raiz: RAIZ_NOVELAS, encargos: RAIZ_ENCARGOS })
  }

  if (partes[1] === 'novelas') {
    // novelas/ no admite otra cosa que leer, y esto es lo que lo garantiza.
    if (metodo !== 'GET' && metodo !== 'HEAD') {
      res.writeHead(405, { allow: 'GET, HEAD' })
      return res.end()
    }
    return enrutarNovelas(partes, res)
  }

  if (partes[1] === 'encargos') return enrutarEncargos(partes, req, res, metodo)

  return noEncontrado(res, 'esa ruta')
}

export const servidor = createServer((req, res) => {
  const metodo = req.method ?? 'GET'

  // Fuera de /api/encargos, el servidor sigue siendo de solo lectura.
  if (metodo !== 'GET' && metodo !== 'HEAD' && metodo !== 'POST') {
    res.writeHead(405, { allow: 'GET, HEAD, POST' })
    return res.end()
  }

  const url = new URL(req.url ?? '/', 'http://localhost')
  enrutar(url, req, res, metodo).catch((error) => {
    console.error('[estudio] error en', url.pathname, error)
    // Lo que es culpa de la petición se declara como tal; no se adivina por el
    // texto del mensaje. Lo demás es un 500 y no se le cuenta al navegador.
    const esDeEntrada = error instanceof ErrorDeEntrada
    responder(res, esDeEntrada ? 400 : 500, {
      error: esDeEntrada ? error.message : 'Error en el servidor.',
    })
  })
})

export function arrancar() {
  return new Promise((listo) => {
    servidor.listen(PUERTO, '127.0.0.1', () => {
      console.log(`[estudio] servidor en http://127.0.0.1:${PUERTO}`)
      console.log(`[estudio] novelas (solo lectura): ${RAIZ_NOVELAS}`)
      console.log(`[estudio] encargos (lectura y escritura): ${RAIZ_ENCARGOS}`)
      listo(servidor)
    })
  })
}

// Arranca solo si se ejecuta directamente (pnpm dev:api), no al importarlo.
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  arrancar()
}
