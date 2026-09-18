// Cliente del servidor de lectura. Todo el HTTP del visor pasa por aquí.
// fetch nativo, sin envoltorios: no hay nada que una librería fuera a simplificar.

import { env } from './env'
import type {
  CapituloConTexto,
  DocumentoConTexto,
  Encargo,
  Lectura,
  Novela,
  NuevoEncargo,
  Pregunta,
  ResumenNovela,
} from './tipos'

export class ErrorApi extends Error {
  readonly estado: number

  constructor(mensaje: string, estado: number) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

async function pedir<T>(ruta: string, señal?: AbortSignal, envio?: unknown): Promise<T> {
  let respuesta: Response
  const opciones: RequestInit =
    envio === undefined
      ? { signal: señal ?? null }
      : {
          signal: señal ?? null,
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(envio),
        }
  try {
    respuesta = await fetch(`${env.apiBaseUrl}${ruta}`, opciones)
  } catch (causa) {
    if (señal?.aborted === true) throw causa
    throw new ErrorApi(
      'No hay respuesta del servidor. ¿Está levantado? (`pnpm dev` en frontend/)',
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

  // ── El estudio (spec §9.4) ────────────────────────────────────────────────

  listarEncargos(señal: AbortSignal): Promise<{ preguntas: Pregunta[]; encargos: Encargo[] }> {
    return pedir<{ preguntas: Pregunta[]; encargos: Encargo[] }>('/encargos', señal)
  },

  leerEncargo(slug: string, señal: AbortSignal): Promise<Encargo> {
    return pedir<Encargo>(`/encargos/${encodeURIComponent(slug)}`, señal)
  },

  crearEncargo(encargo: NuevoEncargo): Promise<{ slug: string }> {
    return pedir<{ slug: string }>('/encargos', undefined, encargo)
  },

  /**
   * Manda una INTENCIÓN, nunca un comando: el navegador no decide qué se
   * ejecuta. La traducción vive en server/harness.mjs (spec §9.4).
   */
  actuar(slug: string, intencion: Record<string, unknown>): Promise<{ estado: string }> {
    return pedir<{ estado: string }>(`/encargos/${encodeURIComponent(slug)}/accion`, undefined, intencion)
  },

  decidir(slug: string, decision: 'confirma' | 'cambios', texto?: string): Promise<{ decision: string }> {
    return pedir<{ decision: string }>(`/encargos/${encodeURIComponent(slug)}/decision`, undefined, {
      decision,
      texto,
    })
  },

  detener(slug: string): Promise<{ estado: string }> {
    return pedir<{ estado: string }>(`/encargos/${encodeURIComponent(slug)}/detener`, undefined, {})
  },

  /** Canal de eventos del harness. SSE, no WebSocket: cero dependencias. */
  escucharEventos(slug: string): EventSource {
    return new EventSource(`${env.apiBaseUrl}/encargos/${encodeURIComponent(slug)}/eventos`)
  },
}
