// Intérprete del subconjunto de YAML que usan las plantillas del harness
// (.claude/skills/novela/plantillas/). No es un YAML completo y no pretende serlo:
// cubre escalares, listas de escalares, listas de objetos y anidamiento por indentación,
// que es exactamente lo que el harness escribe. Sin dependencias, a propósito:
// el servidor del visor no lleva ninguna.

const BARRA = String.fromCharCode(92)
const ESCALAR_VACIO = ['', '~', 'null']

/** Separa el frontmatter YAML del cuerpo Markdown de un artefacto. */
export function separarFrontmatter(texto) {
  const limpio = texto.replace(/^\uFEFF/, '').replace(/\r\n/g, '\n')
  if (!limpio.startsWith('---\n')) return { datos: {}, cuerpo: limpio }

  const cierre = limpio.indexOf('\n---', 3)
  if (cierre === -1) return { datos: {}, cuerpo: limpio }

  const bruto = limpio.slice(4, cierre)
  const finLinea = limpio.indexOf('\n', cierre + 1)
  const cuerpo = finLinea === -1 ? '' : limpio.slice(finLinea + 1)

  try {
    return { datos: interpretar(bruto), cuerpo: cuerpo.trimStart() }
  } catch {
    // Un frontmatter que no entendemos no debe tumbar la lectura de la novela.
    return { datos: {}, cuerpo: cuerpo.trimStart() }
  }
}

/** Interpreta un documento YAML del subconjunto soportado. */
export function interpretar(bruto) {
  const lineas = []
  for (const cruda of bruto.split('\n')) {
    const sinTabs = cruda.replace(/\t/g, '  ')
    const contenido = sinTabs.trim()
    if (contenido === '' || contenido.startsWith('#')) continue
    lineas.push({ sangria: sinTabs.length - sinTabs.trimStart().length, contenido })
  }
  if (lineas.length === 0) return {}
  const [valor] = leerBloque(lineas, 0, lineas[0].sangria)
  return valor
}

function leerBloque(lineas, i, sangria) {
  if (i >= lineas.length) return [null, i]
  return lineas[i].contenido.startsWith('- ') || lineas[i].contenido === '-'
    ? leerLista(lineas, i, sangria)
    : leerMapa(lineas, i, sangria)
}

function leerLista(lineas, i, sangria) {
  const lista = []
  while (i < lineas.length && lineas[i].sangria === sangria && lineas[i].contenido.startsWith('-')) {
    const resto = lineas[i].contenido.replace(/^-\s*/, '')
    i += 1

    if (resto === '') {
      const [valor, siguiente] = leerBloque(lineas, i, sangria + 2)
      lista.push(valor)
      i = siguiente
      continue
    }

    if (esClave(resto)) {
      // Objeto en línea: "- n: 1" seguido de más claves indentadas.
      const sangriaObjeto = sangria + 2
      const virtual = [{ sangria: sangriaObjeto, contenido: resto }]
      while (i < lineas.length && lineas[i].sangria >= sangriaObjeto) {
        virtual.push(lineas[i])
        i += 1
      }
      const [valor] = leerMapa(virtual, 0, sangriaObjeto)
      lista.push(valor)
      continue
    }

    lista.push(leerEscalar(resto))
  }
  return [lista, i]
}

function leerMapa(lineas, i, sangria) {
  const mapa = {}
  while (i < lineas.length && lineas[i].sangria === sangria) {
    const { contenido } = lineas[i]
    const corte = posicionDeLosDosPuntos(contenido)
    if (corte === -1) break

    const clave = contenido.slice(0, corte).trim()
    const resto = contenido.slice(corte + 1).trim()
    i += 1

    if (resto !== '') {
      mapa[clave] = leerEscalar(resto)
      continue
    }

    if (i < lineas.length && lineas[i].sangria > sangria) {
      const [valor, siguiente] = leerBloque(lineas, i, lineas[i].sangria)
      mapa[clave] = valor
      i = siguiente
    } else if (i < lineas.length && lineas[i].sangria === sangria && lineas[i].contenido.startsWith('-')) {
      // Lista al mismo nivel que su clave; el harness la escribe así a veces.
      const [valor, siguiente] = leerLista(lineas, i, sangria)
      mapa[clave] = valor
      i = siguiente
    } else {
      mapa[clave] = null
    }
  }
  return [mapa, i]
}

/** Posición de los dos puntos que separan clave y valor, ignorando los que van dentro de comillas. */
function posicionDeLosDosPuntos(texto) {
  let comilla = null
  for (let p = 0; p < texto.length; p += 1) {
    const c = texto[p]
    if (comilla) {
      if (c === BARRA) p += 1
      else if (c === comilla) comilla = null
      continue
    }
    if (c === '"' || c === "'") comilla = c
    else if (c === ':' && (p + 1 === texto.length || texto[p + 1] === ' ')) return p
  }
  return -1
}

function esClave(texto) {
  return posicionDeLosDosPuntos(texto) !== -1
}

function leerEscalar(bruto) {
  const texto = bruto.trim()

  if (texto.startsWith('"') || texto.startsWith("'")) return leerCadena(texto)

  // Comentario al final de un valor sin comillas: "planteamiento   # arco único"
  const sinComentario = texto.replace(/\s+#.*$/, '').trim()

  if (ESCALAR_VACIO.includes(sinComentario)) return null
  if (sinComentario === 'true') return true
  if (sinComentario === 'false') return false
  if (/^-?\d+$/.test(sinComentario)) return Number(sinComentario)
  if (/^-?\d*\.\d+$/.test(sinComentario)) return Number(sinComentario)
  if (sinComentario.startsWith('[')) return leerListaEnLinea(sinComentario)

  return sinComentario
}

function leerCadena(texto) {
  const comilla = texto[0]
  let valor = ''
  for (let p = 1; p < texto.length; p += 1) {
    const c = texto[p]
    if (c === BARRA && comilla === '"') {
      const siguiente = texto[p + 1]
      valor += siguiente === 'n' ? '\n' : siguiente === 't' ? '\t' : (siguiente ?? '')
      p += 1
      continue
    }
    if (c === comilla) {
      if (comilla === "'" && texto[p + 1] === "'") {
        valor += "'"
        p += 1
        continue
      }
      return valor
    }
    valor += c
  }
  return valor
}

function leerListaEnLinea(texto) {
  const cierre = texto.lastIndexOf(']')
  const dentro = texto.slice(1, cierre === -1 ? texto.length : cierre).trim()
  if (dentro === '') return []

  const partes = []
  let actual = ''
  let comilla = null
  for (let p = 0; p < dentro.length; p += 1) {
    const c = dentro[p]
    if (comilla) {
      actual += c
      if (c === BARRA) {
        actual += dentro[p + 1] ?? ''
        p += 1
      } else if (c === comilla) comilla = null
      continue
    }
    if (c === '"' || c === "'") {
      comilla = c
      actual += c
    } else if (c === ',') {
      partes.push(actual)
      actual = ''
    } else actual += c
  }
  partes.push(actual)

  return partes.map((parte) => leerEscalar(parte)).filter((v) => v !== null || partes.length === 1)
}
