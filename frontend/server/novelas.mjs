// Lectura e interpretación de novelas/<slug>/.
//
// Este módulo es el único sitio del visor que conoce la estructura de carpeta
// descrita en specs/functional.md §3: nombres de fichero, dónde vive cada cosa y
// cómo se relacionan capítulos, intentos e informes. La web solo pinta lo que
// aquí se devuelve. Nada de este fichero escribe en disco.

import { readdir, readFile, stat } from 'node:fs/promises'
import { join } from 'node:path'
import { separarFrontmatter } from './yaml.mjs'

/** Documentos de referencia de una novela, en el orden en que se leen. */
const DOCUMENTOS = [
  { id: 'idea', titulo: 'Idea', ruta: 'idea.md' },
  { id: 'entrevista', titulo: 'Entrevista', ruta: 'entrevista.md' },
  { id: 'biblia', titulo: 'Biblia', ruta: 'biblia.md' },
  { id: 'escaleta', titulo: 'Escaleta de alto nivel', ruta: 'escaleta.md' },
  { id: 'libro-estado', titulo: 'Libro de estado', ruta: 'libro-estado.md' },
  { id: 'informe-global', titulo: 'Informe global', ruta: 'informe-global.md' },
  { id: 'informe-cierre', titulo: 'Informe de cierre', ruta: 'informe-cierre.md' },
  { id: 'config', titulo: 'Configuración congelada', ruta: 'config.json' },
]

export function contarPalabras(texto) {
  const limpio = texto.trim()
  return limpio === '' ? 0 : limpio.split(/\s+/).length
}

async function existe(ruta) {
  try {
    await stat(ruta)
    return true
  } catch {
    return false
  }
}

async function leerSiExiste(ruta) {
  try {
    return await readFile(ruta, 'utf8')
  } catch {
    return null
  }
}

async function leerJson(ruta) {
  const texto = await leerSiExiste(ruta)
  if (texto === null) return null
  try {
    return JSON.parse(texto)
  } catch {
    return null
  }
}

async function leerFrontmatterDe(ruta) {
  const texto = await leerSiExiste(ruta)
  return texto === null ? null : separarFrontmatter(texto).datos
}

/** Todas las novelas de la carpeta raíz, de la más reciente a la más antigua. */
export async function listarNovelas(raiz) {
  let entradas = []
  try {
    entradas = await readdir(raiz, { withFileTypes: true })
  } catch {
    return []
  }

  const novelas = []
  for (const entrada of entradas) {
    if (!entrada.isDirectory()) continue
    const resumen = await leerResumen(raiz, entrada.name)
    if (resumen) novelas.push(resumen)
  }
  novelas.sort((a, b) => (a.actualizado < b.actualizado ? 1 : -1))
  return novelas
}

async function leerResumen(raiz, slug) {
  const carpeta = join(raiz, slug)
  const estado = await leerJson(join(carpeta, 'estado.json'))
  if (!estado) return null

  const config = await leerJson(join(carpeta, 'config.json'))
  const escaleta = await leerFrontmatterDe(join(carpeta, 'escaleta.md'))
  const info = await stat(carpeta).catch(() => null)

  const capitulos = estado.capitulos ?? {}
  const aprobados = Object.values(capitulos).filter((c) => c && c.aprobado != null)

  return {
    slug,
    titulo: typeof escaleta?.titulo === 'string' ? escaleta.titulo : slug,
    etapa: estado.etapa ?? 'desconocida',
    modoPrueba: estado.modo_prueba === true,
    perfil: config?.perfil?.nombre ?? config?.origen?.perfil_activo ?? null,
    totalCapitulos: estado.total_capitulos ?? null,
    capitulosAprobados: aprobados.length,
    aceptadosPorAgotamiento: aprobados.filter((c) => c.por_agotamiento === true).length,
    arcoActual: estado.arco_actual ?? null,
    capituloActual: estado.capitulo_actual ?? null,
    intentoActual: estado.intento_actual ?? null,
    completa: await existe(join(carpeta, 'informe-cierre.md')),
    ultimaParada: estado.ultima_parada ?? null,
    avisos: Array.isArray(estado.avisos) ? estado.avisos : [],
    actualizado: info ? info.mtime.toISOString() : new Date(0).toISOString(),
  }
}

/** Una novela entera, sin el texto de los capítulos (eso se pide aparte). */
export async function leerNovela(raiz, slug) {
  const carpeta = join(raiz, slug)
  const resumen = await leerResumen(raiz, slug)
  if (!resumen) return null

  const estado = await leerJson(join(carpeta, 'estado.json'))
  const config = await leerJson(join(carpeta, 'config.json'))
  const arcos = await leerArcos(carpeta, estado, await leerFrontmatterDe(join(carpeta, 'escaleta.md')))

  return {
    ...resumen,
    idea: (await leerSiExiste(join(carpeta, 'idea.md')))?.trim() ?? null,
    ajustes: resumirAjustes(config),
    invocaciones: estado?.invocaciones ?? null,
    arcos: arcos.map(({ entradas, ...resto }) => ({ ...resto, capitulosDetallados: entradas.length })),
    capitulos: await leerCapitulos(carpeta, estado, indexarEntradas(arcos)),
    documentos: await listarDocumentos(carpeta, arcos),
    registro: await leerRegistro(carpeta),
    metricas: await leerMetricas(carpeta),
    manuscrito: await leerManuscrito(carpeta),
  }
}

/** Los ajustes de la configuración congelada que explican lo que se ve en el panel. */
function resumirAjustes(config) {
  if (!config) return null
  return {
    proveedor: config.proveedor ?? null,
    palabrasPorCapitulo: config.perfil?.palabras_por_capitulo ?? null,
    tolerancia: config.formato?.tolerancia_longitud ?? null,
    reescriturasMax: config.limites?.reescrituras_max ?? null,
    rechazaConGraves: config.veredicto?.rechaza_con_graves ?? null,
    rechazaConLeves: config.veredicto?.rechaza_con_leves ?? null,
    modelos: config.modelos
      ? {
          interrogador: config.modelos.interrogador ?? null,
          escritor: config.modelos.escritor ?? null,
          resumidor: config.modelos.resumidor ?? null,
          revisor: config.modelos.revisor ?? null,
          escaladoActivo: config.modelos.escalado?.activo === true,
        }
      : null,
  }
}

function indexarEntradas(arcos) {
  const entradas = new Map()
  for (const arco of arcos) {
    for (const entrada of arco.entradas) entradas.set(entrada.n, { ...entrada, arco: arco.n })
  }
  return entradas
}

async function leerArcos(carpeta, estado, escaleta) {
  const declarados = Array.isArray(escaleta?.arcos) ? escaleta.arcos : []
  const desdeEstado = Object.entries(estado?.arcos ?? {}).map(([n, a]) => ({
    n: Number(n),
    desde: a.desde ?? null,
    hasta: a.hasta ?? null,
    escaletaValidada: a.escaleta_validada === true,
    tieneInforme: a.informe === true,
  }))

  const arcos = []
  for (const base of desdeEstado) {
    const alto = declarados.find((a) => a.n === base.n) ?? null
    const detalle = await leerFrontmatterDe(join(carpeta, ficheroArco(base.n)))
    arcos.push({
      ...base,
      titulo: alto?.titulo ?? null,
      acto: alto?.acto ?? null,
      objetivo: alto?.objetivo ?? null,
      sucesosClave: Array.isArray(alto?.sucesos_clave) ? alto.sucesos_clave : [],
      hilosAbre: Array.isArray(alto?.hilos_abre) ? alto.hilos_abre : [],
      hilosCierra: Array.isArray(alto?.hilos_cierra) ? alto.hilos_cierra : [],
      entradas: Array.isArray(detalle?.entradas) ? detalle.entradas : [],
    })
  }
  arcos.sort((a, b) => a.n - b.n)
  return arcos
}

function ficheroArco(n) {
  return `arcos/arco-${String(n).padStart(2, '0')}.md`
}

async function leerCapitulos(carpeta, estado, entradas) {
  const raizCapitulos = join(carpeta, 'capitulos')
  let carpetas = []
  try {
    carpetas = (await readdir(raizCapitulos, { withFileTypes: true }))
      .filter((e) => e.isDirectory() && /^\d+$/.test(e.name))
      .map((e) => e.name)
      .sort()
  } catch {
    return []
  }

  const capitulos = []
  for (const nombre of carpetas) {
    const numero = Number(nombre)
    const enEstado = estado?.capitulos?.[String(numero)] ?? null
    const entrada = entradas.get(numero) ?? null

    capitulos.push({
      numero,
      carpeta: nombre,
      titulo: entrada?.titulo ?? null,
      arco: entrada?.arco ?? null,
      objetivo: entrada?.objetivo ?? null,
      sucesos: Array.isArray(entrada?.sucesos) ? entrada.sucesos : [],
      personajes: Array.isArray(entrada?.personajes) ? entrada.personajes : [],
      gancho: entrada?.gancho ?? null,
      palabrasObjetivo: entrada?.palabras_objetivo ?? null,
      aprobado: enEstado?.aprobado ?? null,
      porAgotamiento: enEstado?.por_agotamiento === true,
      intentos: await leerIntentos(join(raizCapitulos, nombre), numero),
    })
  }
  return capitulos
}

async function leerIntentos(carpetaCapitulo, numeroCapitulo) {
  let ficheros = []
  try {
    ficheros = await readdir(carpetaCapitulo)
  } catch {
    return []
  }

  const numeros = ficheros
    .map((f) => /^intento-(\d+)\.md$/.exec(f))
    .filter((m) => m !== null)
    .map((m) => Number(m[1]))
    .sort((a, b) => a - b)

  const intentos = []
  for (const k of numeros) {
    const texto = (await leerSiExiste(join(carpetaCapitulo, `intento-${k}.md`))) ?? ''
    intentos.push({
      numero: k,
      capitulo: numeroCapitulo,
      palabras: contarPalabras(texto),
      tieneResumen: await existe(join(carpetaCapitulo, `resumen-${k}.md`)),
      tieneLibroEstado: await existe(join(carpetaCapitulo, `libro-estado-${k}.md`)),
      informe: await leerInforme(join(carpetaCapitulo, `informe-${k}.md`)),
    })
  }
  return intentos
}

async function leerInforme(ruta) {
  const texto = await leerSiExiste(ruta)
  if (texto === null) return null
  const { datos, cuerpo } = separarFrontmatter(texto)

  const problemas = (Array.isArray(datos.problemas) ? datos.problemas : [])
    .filter((p) => p && typeof p === 'object')
    .map((p) => ({
      gravedad: typeof p.gravedad === 'number' ? p.gravedad : null,
      donde: String(p.donde ?? ''),
      que: String(p.que ?? ''),
      porQue: String(p.por_que ?? ''),
    }))

  return {
    veredicto: datos.veredicto ?? null,
    veredictoRevisor: datos.veredicto_revisor ?? null,
    origen: datos.origen ?? null,
    problemas,
    graves: problemas.filter((p) => p.gravedad === 1 || p.gravedad === 2).length,
    leves: problemas.filter((p) => p.gravedad !== null && p.gravedad >= 3).length,
    observaciones: (Array.isArray(datos.observaciones) ? datos.observaciones : []).map(String),
    cuerpo,
  }
}

async function listarDocumentos(carpeta, arcos) {
  const lista = []
  for (const doc of DOCUMENTOS) {
    const texto = await leerSiExiste(join(carpeta, doc.ruta))
    if (texto === null) continue
    lista.push({ ...doc, palabras: contarPalabras(texto) })
  }

  for (const arco of arcos) {
    const dosDigitos = String(arco.n).padStart(2, '0')
    const candidatos = [
      [ficheroArco(arco.n), `Escaleta del arco ${arco.n}`],
      [`arcos/informe-arco-${dosDigitos}.md`, `Informe del arco ${arco.n}`],
    ]
    for (const [ruta, titulo] of candidatos) {
      const texto = await leerSiExiste(join(carpeta, ruta))
      if (texto === null) continue
      lista.push({ id: ruta, titulo, ruta, palabras: contarPalabras(texto) })
    }
  }
  return lista
}

/** El registro es una tabla Markdown de ancho fijo; aquí se convierte en filas. */
async function leerRegistro(carpeta) {
  const texto = await leerSiExiste(join(carpeta, 'registro.md'))
  if (texto === null) return { columnas: [], filas: [] }

  const lineas = texto.split(/\r?\n/).filter((l) => l.trim().startsWith('|'))
  if (lineas.length === 0) return { columnas: [], filas: [] }

  const celdas = (linea) =>
    linea
      .trim()
      .replace(/^\|/, '')
      .replace(/\|$/, '')
      .split('|')
      .map((c) => c.trim())

  const columnas = celdas(lineas[0])
  const esSeparador = (linea) => /^[\s|:-]+$/.test(linea.trim())
  const vacio = (valor) => valor === '' || valor === '–' || valor === '-'

  const filas = lineas
    .slice(1)
    .filter((l) => !esSeparador(l))
    .map(celdas)
    .filter((f) => f.length === columnas.length)
    .map((valores) => {
      const fila = {}
      for (const [i, columna] of columnas.entries()) {
        const valor = valores[i] ?? ''
        fila[columna] = vacio(valor) ? null : valor
      }
      return fila
    })

  return { columnas, filas }
}

/**
 * Las métricas de calidad (§8.3) las calcula el harness y viven en informe-cierre.md.
 * El visor no las recalcula nunca: o están, o se dice que aún no están (§9.2).
 */
async function leerMetricas(carpeta) {
  const texto = await leerSiExiste(join(carpeta, 'informe-cierre.md'))
  if (texto === null) return { disponibles: false, cuerpo: null }
  return { disponibles: true, cuerpo: separarFrontmatter(texto).cuerpo }
}

async function leerManuscrito(carpeta) {
  const texto = await leerSiExiste(join(carpeta, 'manuscrito.md'))
  if (texto === null) return { existe: false, palabras: 0 }
  return { existe: true, palabras: contarPalabras(texto) }
}

/** El detalle de un capítulo: el texto de cada intento y su resumen. */
export async function leerCapitulo(raiz, slug, numero) {
  const carpeta = join(raiz, slug)
  const estado = await leerJson(join(carpeta, 'estado.json'))
  if (!estado) return null

  const arcos = await leerArcos(carpeta, estado, await leerFrontmatterDe(join(carpeta, 'escaleta.md')))
  const capitulos = await leerCapitulos(carpeta, estado, indexarEntradas(arcos))
  const capitulo = capitulos.find((c) => c.numero === numero)
  if (!capitulo) return null

  const carpetaCapitulo = join(carpeta, 'capitulos', capitulo.carpeta)
  const intentos = []
  for (const intento of capitulo.intentos) {
    const texto = (await leerSiExiste(join(carpetaCapitulo, `intento-${intento.numero}.md`))) ?? ''
    const resumen = await leerSiExiste(join(carpetaCapitulo, `resumen-${intento.numero}.md`))
    intentos.push({
      ...intento,
      texto,
      resumen: resumen === null ? null : separarFrontmatter(resumen).cuerpo,
    })
  }
  return { ...capitulo, intentos }
}

/** El Markdown de un documento de referencia. */
export async function leerDocumento(raiz, slug, id) {
  const carpeta = join(raiz, slug)
  const estado = await leerJson(join(carpeta, 'estado.json'))
  if (!estado) return null

  const arcos = await leerArcos(carpeta, estado, await leerFrontmatterDe(join(carpeta, 'escaleta.md')))
  const documento = (await listarDocumentos(carpeta, arcos)).find((d) => d.id === id)
  if (!documento) return null

  const texto = (await leerSiExiste(join(carpeta, documento.ruta))) ?? ''
  const esJson = documento.ruta.endsWith('.json')
  return {
    ...documento,
    cuerpo: esJson ? ['```json', texto.trim(), '```'].join('\n') : separarFrontmatter(texto).cuerpo,
  }
}

/** El manuscrito ensamblado; si aún no existe, los capítulos aprobados en orden. */
export async function leerLectura(raiz, slug) {
  const carpeta = join(raiz, slug)
  const manuscrito = await leerSiExiste(join(carpeta, 'manuscrito.md'))
  if (manuscrito !== null) {
    return { fuente: 'manuscrito', cuerpo: separarFrontmatter(manuscrito).cuerpo, capitulos: [] }
  }

  const estado = await leerJson(join(carpeta, 'estado.json'))
  if (!estado) return null

  const arcos = await leerArcos(carpeta, estado, await leerFrontmatterDe(join(carpeta, 'escaleta.md')))
  const capitulos = await leerCapitulos(carpeta, estado, indexarEntradas(arcos))

  const leidos = []
  for (const capitulo of capitulos) {
    if (capitulo.aprobado === null) continue
    const ruta = join(carpeta, 'capitulos', capitulo.carpeta, `intento-${capitulo.aprobado}.md`)
    const texto = await leerSiExiste(ruta)
    if (texto === null) continue
    leidos.push({
      numero: capitulo.numero,
      titulo: capitulo.titulo,
      intento: capitulo.aprobado,
      porAgotamiento: capitulo.porAgotamiento,
      palabras: contarPalabras(texto),
      cuerpo: texto,
    })
  }
  return { fuente: 'capitulos', cuerpo: null, capitulos: leidos }
}
