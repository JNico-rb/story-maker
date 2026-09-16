// Cliente del servidor de lectura. Todo el HTTP del visor pasa por aquí.
// fetch nativo, sin envoltorios: no hay nada que una librería fuera a simplificar.

import { env } from './env'
import type { CapituloConTexto, DocumentoConTexto, Lectura, Novela, ResumenNovela } from './tipos'

export class ErrorApi extends Error {
  readonly estado: number

  constructor(mensaje: string, estado: number) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

async function pedir<T>(ruta: string, señal: AbortSignal): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`${env.apiBaseUrl}${ruta}`, { signal: señal })
  } catch (causa) {
    if (señal.aborted) throw causa
    throw new ErrorApi(
      'No hay respuesta del servidor de lectura. ¿Está levantado? (`pnpm dev` en frontend/)',
      0,
    )
  }

  if (!respuesta.ok) {
    const cuerpo: unknown = await respuesta.json().catch(() => null)
    const mensaje =
      cuerpo !== null && typeof cuerpo === 'object' && 'error' in cuerpo
        ? String((cuerpo as { error: unknown }).error)
        : `El servidor respondió ${respuesta.status}.`
    throw new ErrorApi(mensaje, respuesta.status)
  }

  return (await respuesta.json()) as T
}

export const api = {
  async listarNovelas(señal: AbortSignal): Promise<ResumenNovela[]> {
    const datos = await pedir<{ novelas: ResumenNovela[] }>('/novelas', señal)
    return datos.novelas
  },

  leerNovela(slug: string, señal: AbortSignal): Promise<Novela> {
    return pedir<Novela>(`/novelas/${encodeURIComponent(slug)}`, señal)
  },

  leerLectura(slug: string, señal: AbortSignal): Promise<Lectura> {
    return pedir<Lectura>(`/novelas/${encodeURIComponent(slug)}/lectura`, señal)
  },

  leerCapitulo(slug: string, numero: number, señal: AbortSignal): Promise<CapituloConTexto> {
    return pedir<CapituloConTexto>(`/novelas/${encodeURIComponent(slug)}/capitulos/${numero}`, señal)
  },

  leerDocumento(slug: string, id: string, señal: AbortSignal): Promise<DocumentoConTexto> {
    const partes = id.split('/').map(encodeURIComponent).join('/')
    return pedir<DocumentoConTexto>(`/novelas/${encodeURIComponent(slug)}/documentos/${partes}`, señal)
  },
}
