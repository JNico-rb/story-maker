// Navegación por el fragmento de la URL (#/…), con la API del navegador.
//
// Es lo mínimo para que cada novela, cada capítulo y cada documento tengan un
// enlace propio que se puede recargar y compartir. No hace falta un router.

export const PESTANAS = ['leer', 'progreso', 'documentos', 'registro'] as const

export type Pestana = (typeof PESTANAS)[number]

export const TITULO_PESTANA: Record<Pestana, string> = {
  leer: 'Leer',
  progreso: 'Progreso',
  documentos: 'Documentos',
  registro: 'Registro',
}

export type Ruta =
  | { vista: 'lista' }
  | { vista: 'estudio'; encargo: string | null }
  | { vista: 'novela'; slug: string; pestana: Pestana; seleccion: string | null }

function esPestana(valor: string | undefined): valor is Pestana {
  return valor !== undefined && (PESTANAS as readonly string[]).includes(valor)
}

export function leerRuta(hash: string): Ruta {
  const partes = hash
    .replace(/^#\/?/, '')
    .split('/')
    .filter((p) => p !== '')
    .map(decodeURIComponent)

  if (partes[0] === 'estudio') return { vista: 'estudio', encargo: partes[1] ?? null }

  if (partes[0] !== 'n' || partes[1] === undefined) return { vista: 'lista' }

  const pestana = esPestana(partes[2]) ? partes[2] : 'leer'
  const resto = partes.slice(3)

  return {
    vista: 'novela',
    slug: partes[1],
    pestana,
    seleccion: resto.length > 0 ? resto.join('/') : null,
  }
}

export function escribirRuta(ruta: Ruta): string {
  if (ruta.vista === 'lista') return '#/'
  if (ruta.vista === 'estudio') {
    return ruta.encargo === null ? '#/estudio' : `#/estudio/${encodeURIComponent(ruta.encargo)}`
  }
  const base = `#/n/${encodeURIComponent(ruta.slug)}/${ruta.pestana}`
  if (ruta.seleccion === null) return base
  const cola = ruta.seleccion.split('/').map(encodeURIComponent).join('/')
  return `${base}/${cola}`
}

export function irA(ruta: Ruta): void {
  window.location.hash = escribirRuta(ruta)
}
