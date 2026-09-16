// Única frontera de configuración del visor.
//
// Ningún otro fichero lee import.meta.env. Si la configuración es inválida se
// detecta aquí, al arrancar, y no a mitad de una petición.

function validarBaseUrl(bruto: unknown): string {
  if (bruto === undefined || bruto === null || bruto === '') return '/api'

  if (typeof bruto !== 'string') {
    throw new Error('VITE_API_BASE_URL debe ser una cadena de texto.')
  }

  const valor = bruto.trim().replace(/\/+$/, '')
  if (valor.startsWith('/')) return valor

  try {
    const url = new URL(valor)
    if (url.protocol !== 'http:' && url.protocol !== 'https:') {
      throw new Error('protocolo no admitido')
    }
    return valor
  } catch {
    throw new Error(
      `VITE_API_BASE_URL no es válida: «${bruto}». Se espera una ruta como «/api» o una URL http(s) completa.`,
    )
  }
}

export const env = {
  /** Dirección del servidor de lectura (frontend/server). */
  apiBaseUrl: validarBaseUrl(import.meta.env.VITE_API_BASE_URL),
  /** Cada cuánto se vuelve a preguntar por los datos, en milisegundos. */
  intervaloRefresco: 5000,
} as const
