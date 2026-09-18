// El único módulo de este servidor que ejecuta algo.
//
// Lanza el harness y habla con él. Lo que el navegador manda son INTENCIONES
// (empezar, responder, confirmar, cambios), nunca comandos: una web que pudiera
// mandar comandos sería una web que ejecuta lo que le pidan. La traducción de
// intención a comando `/novela` vive aquí y en ningún otro sitio.
//
// Spec §9.4. Esta capa es la única parte del estudio que NO se porta al hito 2:
// traduce «lanzar el harness» a la herramienta del hito 1. El resto del estudio
// solo depende de la estructura de novelas/<slug>/ y de los motivos de parada.

import { spawn } from 'node:child_process'
import { readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { ErrorDeEntrada } from './errores.mjs'

/**
 * Una sesión viva por encargo. La guarda el SERVIDOR, no el navegador: por eso
 * cerrar la pestaña no para la novela. Lo que sí la para es parar `pnpm dev`,
 * y para eso se persiste el identificador y se puede retomar con --resume.
 */
const sesiones = new Map()

/** Texto plano de un mensaje del asistente, ignorando bloques que no sean texto. */
function textoDe(mensaje) {
  const contenido = mensaje?.message?.content
  if (!Array.isArray(contenido)) return ''
  return contenido
    .filter((bloque) => bloque?.type === 'text' && typeof bloque.text === 'string')
    .map((bloque) => bloque.text)
    .join('\n')
    .trim()
}

/** Nombre de la herramienta de un bloque de uso, para el progreso. */
function herramientasDe(mensaje) {
  const contenido = mensaje?.message?.content
  if (!Array.isArray(contenido)) return []
  return contenido
    .filter((bloque) => bloque?.type === 'tool_use' && typeof bloque.name === 'string')
    .map((bloque) => bloque.name)
}

function crearSesion(slug) {
  const sesion = {
    slug,
    proceso: null,
    idSesion: null,
    estado: 'inactivo',
    novela: null,
    historial: [],
    oyentes: new Set(),
    resto: '',
    /** Cómo guardarse en disco. Lo fija actuar(), que es quien sabe la raíz. */
    persistir: null,
  }
  sesiones.set(slug, sesion)
  return sesion
}

export function obtenerSesion(slug) {
  return sesiones.get(slug) ?? crearSesion(slug)
}

function emitir(sesion, evento) {
  const conFecha = { ...evento, fecha: new Date().toISOString() }

  // El historial es lo que ve quien llega tarde o recarga la página. Acotado:
  // una novela larga produce miles de eventos y esto vive en memoria.
  sesion.historial.push(conFecha)
  if (sesion.historial.length > 500) sesion.historial.splice(0, sesion.historial.length - 500)

  for (const oyente of sesion.oyentes) {
    try {
      oyente(conFecha)
    } catch {
      // Un oyente roto (pestaña que se fue) no puede tumbar la sesión.
    }
  }
}

export function suscribir(slug, oyente) {
  const sesion = obtenerSesion(slug)
  sesion.oyentes.add(oyente)
  return () => sesion.oyentes.delete(oyente)
}

function cambiarEstado(sesion, estado) {
  sesion.estado = estado
  emitir(sesion, { tipo: 'estado', estado })
}

/** Procesa una línea NDJSON de la salida de Claude Code. */
function procesarEvento(sesion, evento) {
  if (evento.type === 'system' && evento.subtype === 'init') {
    if (typeof evento.session_id === 'string') {
      sesion.idSesion = evento.session_id
      // Se persiste AQUÍ y no al lanzar: el identificador no existe hasta que
      // llega este evento, así que guardarlo antes escribía siempre null y
      // --resume no podía funcionar nunca.
      if (sesion.persistir !== null) void sesion.persistir()
    }
    return
  }

  if (evento.type === 'assistant') {
    const texto = textoDe(evento)
    if (texto !== '') emitir(sesion, { tipo: 'asistente', texto })

    for (const herramienta of herramientasDe(evento)) {
      emitir(sesion, { tipo: 'herramienta', nombre: herramienta })
    }
    return
  }

  if (evento.type === 'result') {
    // El harness ha terminado su turno. Si estaba entrevistando, ahora toca al
    // usuario; si estaba generando, ha parado o ha acabado. Cuál de las dos lo
    // dice estado.json, que lee el visor: aquí no se interpreta la novela.
    cambiarEstado(sesion, 'esperando')
    emitir(sesion, { tipo: 'turno_terminado', motivo: evento.subtype ?? 'ok' })
  }
}

function conectarSalida(sesion) {
  const { proceso } = sesion

  proceso.stdout.setEncoding('utf8')
  proceso.stdout.on('data', (trozo) => {
    sesion.resto += trozo
    const lineas = sesion.resto.split('\n')
    sesion.resto = lineas.pop() ?? ''

    for (const linea of lineas) {
      const limpia = linea.trim()
      if (limpia === '') continue
      try {
        procesarEvento(sesion, JSON.parse(limpia))
      } catch {
        // Una línea que no es JSON no es motivo para tirar la sesión.
        emitir(sesion, { tipo: 'crudo', texto: limpia.slice(0, 2000) })
      }
    }
  })

  proceso.stderr.setEncoding('utf8')
  proceso.stderr.on('data', (trozo) => {
    const texto = String(trozo).trim()
    if (texto !== '') emitir(sesion, { tipo: 'aviso', texto: texto.slice(0, 2000) })
  })

  proceso.on('error', (error) => {
    emitir(sesion, {
      tipo: 'error',
      mensaje: `No se ha podido ejecutar «claude». ¿Está en el PATH? (${error.message})`,
    })
    sesion.proceso = null
    cambiarEstado(sesion, 'fallado')
  })

  proceso.on('close', (codigo) => {
    sesion.proceso = null
    emitir(sesion, { tipo: 'fin_proceso', codigo })
    cambiarEstado(sesion, codigo === 0 ? 'parado' : 'fallado')
  })
}

/**
 * Argumentos fijos de toda invocación.
 *
 * Los permisos son los de .claude/settings.json, que ya existe para que el
 * bucle corra sin confirmaciones y se versiona. NUNCA bypassPermissions: un
 * botón de una web local no puede tener permiso para cualquier cosa, y el hook
 * de inmutabilidad no cubre Bash (spec §3.1). Lo que no esté permitido se
 * deniega, el harness para limpio y se ve.
 *
 * AskUserQuestion se deniega a propósito: sus preguntas no caben en este canal.
 * Denegada, el modelo pregunta en texto, que es lo que el estudio sabe enseñar.
 */
function argumentosBase(idSesion) {
  const args = [
    '--print',
    '--input-format',
    'stream-json',
    '--output-format',
    'stream-json',
    '--verbose',
    '--permission-prompts',
    'none',
    '--disallowed-tools',
    'AskUserQuestion',
  ]
  if (idSesion !== null && idSesion !== undefined) args.push('--resume', idSesion)
  return args
}

function mandarMensaje(sesion, texto) {
  if (sesion.proceso === null || sesion.proceso.stdin.destroyed) return false
  const sobre = {
    type: 'user',
    message: { role: 'user', content: [{ type: 'text', text: texto }] },
  }
  sesion.proceso.stdin.write(`${JSON.stringify(sobre)}\n`)
  return true
}

async function arrancarProceso(sesion, raizRepo, prompt) {
  if (sesion.proceso !== null) {
    // Ya hay un turno en marcha: el mensaje entra por la sesión viva.
    return mandarMensaje(sesion, prompt)
  }

  cambiarEstado(sesion, 'trabajando')

  sesion.proceso = spawn('claude', argumentosBase(sesion.idSesion), {
    cwd: raizRepo,
    stdio: ['pipe', 'pipe', 'pipe'],
    shell: process.platform === 'win32',
  })

  conectarSalida(sesion)
  return mandarMensaje(sesion, prompt)
}

/** Guarda el identificador de sesión para poder retomar si se reinicia el servidor. */
async function persistirSesion(raizEncargos, slug, sesion) {
  await writeFile(
    join(raizEncargos, slug, 'sesion.json'),
    `${JSON.stringify({ version: 1, idSesion: sesion.idSesion, novela: sesion.novela }, null, 2)}\n`,
    'utf8',
  ).catch(() => {})
}

export async function cargarSesionPersistida(raizEncargos, slug) {
  const sesion = obtenerSesion(slug)
  if (sesion.idSesion !== null) return sesion

  try {
    const bruto = await readFile(join(raizEncargos, slug, 'sesion.json'), 'utf8')
    const datos = JSON.parse(bruto)
    if (typeof datos.idSesion === 'string') sesion.idSesion = datos.idSesion
    if (typeof datos.novela === 'string') sesion.novela = datos.novela
  } catch {
    // Todavía no hay sesión: es lo normal antes de empezar.
  }
  return sesion
}

/**
 * Traduce una intención del navegador al comando `/novela` que le corresponde.
 * Es la frontera: fuera de esta función nadie decide qué se ejecuta.
 */
export async function actuar(raizRepo, raizEncargos, slug, intencion) {
  const sesion = await cargarSesionPersistida(raizEncargos, slug)
  sesion.persistir = () => persistirSesion(raizEncargos, slug, sesion)

  if (intencion.tipo === 'empezar') {
    if (sesion.proceso !== null) throw new ErrorDeEntrada('Esta novela ya está en marcha.')
    const idea = String(intencion.idea ?? '').replace(/"/g, "'").trim()
    const ajustes = Object.entries(intencion.ajustes ?? {})
      .filter(([, valor]) => valor !== null && valor !== '')
      .map(([clave, valor]) => `${clave}=${valor}`)
      .join(' ')

    const prompt =
      `/novela nueva "${idea}" precarga: encargos/${slug}${ajustes === '' ? '' : ` ${ajustes}`}`
    await arrancarProceso(sesion, raizRepo, prompt)
    return { estado: sesion.estado }
  }

  if (intencion.tipo === 'responder') {
    const texto = String(intencion.texto ?? '').trim()
    if (texto === '') throw new ErrorDeEntrada('No hay nada que responder.')
    cambiarEstado(sesion, 'trabajando')
    emitir(sesion, { tipo: 'usuario', texto })
    if (!(await arrancarProceso(sesion, raizRepo, texto))) {
      throw new ErrorDeEntrada('La sesión no está viva; vuelve a lanzar la novela.')
    }
    return { estado: sesion.estado }
  }

  if (intencion.tipo === 'continuar') {
    const novela = String(intencion.novela ?? '').trim()
    if (novela === '') throw new ErrorDeEntrada('No se sabe qué novela continuar.')
    sesion.novela = novela
    const prompt = `/novela continuar novelas/${novela} precarga: encargos/${slug}`
    await arrancarProceso(sesion, raizRepo, prompt)
    await sesion.persistir()
    return { estado: sesion.estado }
  }

  throw new ErrorDeEntrada(`Intención desconocida: ${String(intencion.tipo)}`)
}

/** Corta el turno en curso. No borra nada: el estado vive en disco. */
export function detener(slug) {
  const sesion = sesiones.get(slug)
  if (sesion?.proceso == null) return { estado: sesion?.estado ?? 'inactivo' }
  sesion.proceso.kill()
  return { estado: 'parando' }
}

export function resumenSesion(slug) {
  const sesion = sesiones.get(slug)
  if (sesion === undefined) return { estado: 'inactivo', historial: [], novela: null }
  return { estado: sesion.estado, historial: sesion.historial, novela: sesion.novela }
}
