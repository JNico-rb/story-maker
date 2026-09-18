// Encargos: lo que el usuario rellena antes de que exista la novela.
//
// Es el ÚNICO módulo de este servidor que escribe en disco, y solo dentro de
// encargos/. Nunca en novelas/, que es del harness en exclusiva (spec §3.1 y
// §9.4): si el estudio escribiera ahí, la garantía de inmutabilidad dejaría de
// ser demostrable, porque el hook no puede distinguir quién escribe.
//
// Sin dependencias, como el resto del servidor.

import { mkdir, readdir, readFile, rename, writeFile } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import { ErrorDeEntrada } from './errores.mjs'

/** Las doce preguntas de plantillas/entrevista.md, en su orden y con su sección. */
export const PREGUNTAS = [
  { id: 'mundo_que_paso', seccion: 'Mundo post-IA', texto: '¿Qué pasó?' },
  { id: 'mundo_reglas', seccion: 'Mundo post-IA', texto: '¿Qué reglas rigen ahora?' },
  { id: 'mundo_vida', seccion: 'Mundo post-IA', texto: '¿Qué ha cambiado en la vida diaria?' },
  {
    id: 'protagonista',
    seccion: 'Protagonista y antagonismo',
    texto: '¿Quién es, qué quiere, qué le falta?',
  },
  { id: 'antagonismo', seccion: 'Protagonista y antagonismo', texto: '¿Qué o quién se le opone?' },
  { id: 'tono', seccion: 'Tono y voz', texto: 'Tono y registro' },
  { id: 'punto_de_vista', seccion: 'Tono y voz', texto: 'Punto de vista y persona narrativa' },
  { id: 'final', seccion: 'Historia', texto: 'Tipo de final' },
  { id: 'temas_tocar', seccion: 'Historia', texto: 'Temas a tocar' },
  { id: 'temas_evitar', seccion: 'Historia', texto: 'Temas a evitar' },
  { id: 'capitulos', seccion: 'Extensión', texto: 'Capítulos' },
  { id: 'palabras', seccion: 'Extensión', texto: 'Palabras por capítulo' },
]

const SLUG_VALIDO = /^[a-z0-9][a-z0-9-]{0,99}$/

/** Deriva el slug de la idea igual que crear_novela de SKILL.md §2: minúsculas, sin acentos, guiones, 40. */
export function derivarSlug(idea) {
  const base = idea
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
    .replace(/-+$/g, '')

  return base === '' ? 'encargo' : base
}

/** Resuelve una ruta dentro de la raíz de encargos, o null si el slug intenta salirse. */
function carpetaDe(raiz, slug) {
  if (!SLUG_VALIDO.test(slug)) return null
  const carpeta = resolve(raiz, slug)
  return carpeta.startsWith(resolve(raiz)) ? carpeta : null
}

/**
 * Compone entrevista-previa.md. No es la entrevista: es su precarga (spec §9.4).
 * El grilling la recibe como punto de partida y solo pregunta lo que falta.
 */
function componerEntrevistaPrevia(respuestas, fecha) {
  const lineas = [
    '---',
    'precarga: true',
    'origen: formulario',
    `fecha: "${fecha}"`,
    '---',
    '',
    '# Entrevista precargada',
    '',
    'Respuestas que el usuario dio por adelantado en el estudio (spec §9.4). **No es una entrevista',
    'cerrada**: el grilling sigue corriendo y pregunta lo que falte, lo que quede ambiguo y lo que',
    'estas respuestas abran. Lo marcado **[decide tú]** se deja abierto a propósito.',
    '',
  ]

  let seccionActual = ''
  for (const pregunta of PREGUNTAS) {
    const bruto = respuestas[pregunta.id]
    const respuesta = typeof bruto === 'string' ? bruto.trim() : ''

    if (pregunta.seccion !== seccionActual) {
      seccionActual = pregunta.seccion
      lineas.push(`## ${seccionActual}`, '')
    }

    const valor = respuesta === '' ? '**[decide tú]**' : `${respuesta} **[usuario]**`
    lineas.push(`- ${pregunta.texto} → ${valor}`)

    const siguiente = PREGUNTAS[PREGUNTAS.indexOf(pregunta) + 1]
    if (siguiente === undefined || siguiente.seccion !== seccionActual) lineas.push('')
  }

  return `${lineas.join('\n').trimEnd()}\n`
}

/**
 * Crea encargos/<slug>/ con idea.md y entrevista-previa.md.
 * Si el slug ya existe, le añade un sufijo de fecha, igual que hace crear_novela.
 */
export async function crearEncargo(raiz, { idea, respuestas, ajustes }) {
  const texto = typeof idea === 'string' ? idea.trim() : ''
  if (texto === '') throw new ErrorDeEntrada('La idea no puede estar vacía.')

  const fecha = new Date()
  const marca = fecha.toISOString().slice(0, 16).replace(/[-:T]/g, '').replace(/(\d{8})(\d{4})/, '$1-$2')

  let slug = derivarSlug(texto)
  if (carpetaDe(raiz, slug) === null) slug = 'encargo'
  const existentes = new Set(await listarSlugs(raiz))
  if (existentes.has(slug)) slug = `${slug}-${marca}`.slice(0, 100)

  const carpeta = carpetaDe(raiz, slug)
  if (carpeta === null) throw new ErrorDeEntrada('Slug no válido.')

  await mkdir(carpeta, { recursive: true })
  await writeFile(join(carpeta, 'idea.md'), `${texto}\n`, 'utf8')
  await writeFile(
    join(carpeta, 'entrevista-previa.md'),
    componerEntrevistaPrevia(respuestas ?? {}, fecha.toISOString().slice(0, 10)),
    'utf8',
  )
  await writeFile(
    join(carpeta, 'encargo.json'),
    `${JSON.stringify({ version: 1, slug, creado: fecha.toISOString(), ajustes: ajustes ?? {} }, null, 2)}\n`,
    'utf8',
  )

  return { slug, carpeta }
}

export async function listarSlugs(raiz) {
  try {
    const entradas = await readdir(raiz, { withFileTypes: true })
    return entradas.filter((e) => e.isDirectory()).map((e) => e.name)
  } catch {
    return []
  }
}

export async function leerEncargo(raiz, slug) {
  const carpeta = carpetaDe(raiz, slug)
  if (carpeta === null) return null

  try {
    const bruto = await readFile(join(carpeta, 'encargo.json'), 'utf8')
    const datos = JSON.parse(bruto)
    const idea = await readFile(join(carpeta, 'idea.md'), 'utf8').catch(() => '')
    return { ...datos, slug, carpeta, idea: idea.trim() }
  } catch {
    return null
  }
}

/** Guarda en el encargo qué novela creó el harness, para poder enlazarlos después. */
export async function anotarNovela(raiz, slug, slugNovela) {
  const encargo = await leerEncargo(raiz, slug)
  if (encargo === null) return
  const { carpeta, idea: _idea, ...datos } = encargo
  await writeFile(
    join(carpeta, 'encargo.json'),
    `${JSON.stringify({ ...datos, novela: slugNovela }, null, 2)}\n`,
    'utf8',
  )
}

/**
 * Escribe la decisión del usuario sobre la propuesta de biblia y escaleta.
 *
 * Va aquí y no en novelas/<slug>/ por dos motivos, y el segundo es el que muerde:
 * esa carpeta es del harness (spec §3.1), y `reanudar` descarta todo lo que
 * encuentre sin commitear dentro de ella, así que una decisión dejada ahí se
 * borraría antes de leerse.
 */
export async function escribirDecision(raiz, slug, { decision, texto }) {
  const carpeta = carpetaDe(raiz, slug)
  if (carpeta === null) throw new ErrorDeEntrada('Slug no válido.')

  if (decision !== 'confirma' && decision !== 'cambios') {
    throw new ErrorDeEntrada('La decisión solo puede ser «confirma» o «cambios».')
  }
  const detalle = typeof texto === 'string' ? texto.trim() : ''
  if (decision === 'cambios' && detalle === '') {
    throw new ErrorDeEntrada('Para pedir cambios hay que decir cuáles.')
  }

  const cuerpo =
    decision === 'confirma'
      ? 'confirma\n'
      : `cambios: ${detalle.replace(/\r\n/g, '\n')}\n`

  await writeFile(join(carpeta, 'decision.md'), cuerpo, 'utf8')
  return { decision }
}

/** Aparta una decisión ya aplicada. Lo hace el harness; está aquí para las pruebas a mano. */
export async function apartarDecision(raiz, slug, fecha = new Date()) {
  const carpeta = carpetaDe(raiz, slug)
  if (carpeta === null) return
  const sello = fecha.toISOString().slice(0, 19).replace(/[:T]/g, '-')
  await rename(join(carpeta, 'decision.md'), join(carpeta, `decision-aplicada-${sello}.md`)).catch(
    () => {},
  )
}
