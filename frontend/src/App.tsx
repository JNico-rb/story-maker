// Flujo de la aplicación: qué se está mirando y qué hay que pedir para pintarlo.

import { useCallback, useEffect, useState } from 'react'
import { api } from './lib/api'
import { leerRuta, type Ruta } from './lib/ruta'
import { useDatos } from './lib/useDatos'
import type { Novela, ResumenNovela } from './lib/tipos'
import { BarraMarca } from './components/BarraMarca'
import { CabeceraNovela } from './components/CabeceraNovela'
import { DetalleCapitulo } from './components/DetalleCapitulo'
import { ListaNovelas } from './components/ListaNovelas'
import { PestanaDocumentos } from './components/PestanaDocumentos'
import { PestanaLeer } from './components/PestanaLeer'
import { PestanaProgreso } from './components/PestanaProgreso'
import { PestanaRegistro } from './components/PestanaRegistro'
import { Cargando, Fallo, Vacio } from './components/ui/Estados'

function useRuta(): Ruta {
  const [ruta, setRuta] = useState<Ruta>(() => leerRuta(window.location.hash))

  useEffect(() => {
    const alCambiar = () => setRuta(leerRuta(window.location.hash))
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])

  return ruta
}

function Lista({ refrescando }: { refrescando: boolean }) {
  const { datos, cargando, error, recargar } = useDatos<ResumenNovela[]>(
    (señal) => api.listarNovelas(señal),
    'novelas',
    refrescando,
  )

  if (cargando && datos === null) return <Cargando que="las novelas" />
  if (error !== null && datos === null) return <Fallo mensaje={error} alReintentar={recargar} />
  if (datos === null) return null

  if (datos.length === 0) {
    return (
      <Vacio titulo="No hay ninguna novela todavía">
        Genera una desde Claude Code con <code className="font-dato">/novela nueva</code> y aparecerá
        aquí en cuanto el harness cree su carpeta.
      </Vacio>
    )
  }

  return <ListaNovelas novelas={datos} />
}

function VistaNovela({
  ruta,
  refrescando,
  alCambiarRefresco,
}: {
  ruta: Extract<Ruta, { vista: 'novela' }>
  refrescando: boolean
  alCambiarRefresco: (valor: boolean) => void
}) {
  const { slug, pestana, seleccion } = ruta
  const { datos, cargando, error, recargar } = useDatos<Novela>(
    (señal) => api.leerNovela(slug, señal),
    `novela:${slug}`,
    refrescando,
  )

  if (cargando && datos === null) return <Cargando que="la novela" />
  if (error !== null && datos === null) return <Fallo mensaje={error} alReintentar={recargar} />
  if (datos === null) return null

  const capituloElegido =
    pestana === 'progreso' && seleccion !== null && /^\d+$/.test(seleccion)
      ? Number(seleccion)
      : null

  return (
    <>
      <CabeceraNovela
        novela={datos}
        pestana={pestana}
        refrescando={refrescando}
        alCambiarRefresco={alCambiarRefresco}
      />

      {error !== null && (
        <p className="border-b border-aviso/25 bg-aviso-fondo px-6 py-2 text-center text-xs text-aviso">
          El último refresco falló ({error}). Sigues viendo los datos anteriores.
        </p>
      )}

      {pestana === 'leer' && <PestanaLeer slug={slug} refrescando={refrescando} />}

      {pestana === 'progreso' &&
        (capituloElegido === null ? (
          <PestanaProgreso novela={datos} />
        ) : (
          <DetalleCapitulo
            slug={slug}
            numero={capituloElegido}
            tolerancia={datos.ajustes?.tolerancia ?? null}
            refrescando={refrescando}
          />
        ))}

      {pestana === 'documentos' && (
        <PestanaDocumentos novela={datos} seleccion={seleccion} refrescando={refrescando} />
      )}

      {pestana === 'registro' && <PestanaRegistro novela={datos} />}
    </>
  )
}

export function App() {
  const ruta = useRuta()
  const [refrescando, setRefrescando] = useState(true)
  const alCambiarRefresco = useCallback((valor: boolean) => setRefrescando(valor), [])

  return (
    <div className="min-h-screen bg-panel">
      <BarraMarca />
      {ruta.vista === 'lista' ? (
        <Lista refrescando={refrescando} />
      ) : (
        <VistaNovela ruta={ruta} refrescando={refrescando} alCambiarRefresco={alCambiarRefresco} />
      )}
    </div>
  )
}
