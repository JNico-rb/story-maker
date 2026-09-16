// Hook de carga con refresco automático.
//
// El harness escribe en novelas/ mientras corre, así que el visor vuelve a
// preguntar cada pocos segundos. El refresco no vacía lo que ya está en pantalla:
// si falla, se conservan los últimos datos buenos y se muestra el aviso encima.

import { useCallback, useEffect, useRef, useState } from 'react'
import { env } from './env'

export interface Datos<T> {
  datos: T | null
  cargando: boolean
  error: string | null
  recargar: () => void
}

export function useDatos<T>(
  pedir: (señal: AbortSignal) => Promise<T>,
  clave: string,
  refrescar: boolean,
): Datos<T> {
  const [datos, setDatos] = useState<T | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)

  // La función de petición cambia en cada render; la clave es lo que identifica
  // qué se está pidiendo, y es lo que decide cuándo hay que volver a empezar.
  const pedirRef = useRef(pedir)
  pedirRef.current = pedir

  const recargar = useCallback(() => setTick((n) => n + 1), [])

  useEffect(() => {
    setCargando(true)
    setDatos(null)
    setError(null)
  }, [clave])

  useEffect(() => {
    const control = new AbortController()
    let vigente = true

    pedirRef
      .current(control.signal)
      .then((resultado) => {
        if (!vigente) return
        setDatos(resultado)
        setError(null)
      })
      .catch((causa: unknown) => {
        if (!vigente || control.signal.aborted) return
        setError(causa instanceof Error ? causa.message : 'Error desconocido.')
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })

    return () => {
      vigente = false
      control.abort()
    }
  }, [clave, tick])

  useEffect(() => {
    if (!refrescar) return undefined
    const temporizador = window.setInterval(recargar, env.intervaloRefresco)
    return () => window.clearInterval(temporizador)
  }, [refrescar, recargar])

  return { datos, cargando, error, recargar }
}
