// Leer: el manuscrito si ya está ensamblado, y si no los capítulos aprobados.
// Aquí manda la lectura: columna estrecha, serifa y nada de interfaz alrededor.

import { api } from '../lib/api'
import { formatearPalabras } from '../lib/formato'
import { useDatos } from '../lib/useDatos'
import type { Lectura } from '../lib/tipos'
import { Markdown } from './Markdown'
import { Cargando, Fallo, Vacio } from './ui/Estados'

interface Props {
  slug: string
  refrescando: boolean
}

export function PestanaLeer({ slug, refrescando }: Props) {
  const { datos, cargando, error, recargar } = useDatos<Lectura>(
    (señal) => api.leerLectura(slug, señal),
    `lectura:${slug}`,
    refrescando,
  )

  if (cargando && datos === null) return <Cargando que="el texto" />
  if (error !== null && datos === null) return <Fallo mensaje={error} alReintentar={recargar} />
  if (datos === null) return null

  if (datos.fuente === 'manuscrito' && datos.cuerpo !== null) {
    return (
      <article className="mx-auto max-w-2xl bg-papel px-6 py-14 sm:px-10">
        <Markdown texto={datos.cuerpo} registro="lectura" />
      </article>
    )
  }

  if (datos.capitulos.length === 0) {
    return (
      <Vacio titulo="Todavía no hay nada que leer">
        Ningún capítulo ha sido aprobado. En cuanto el harness cierre el primero aparecerá aquí.
      </Vacio>
    )
  }

  return (
    <div className="mx-auto max-w-2xl bg-papel px-6 py-14 sm:px-10">
      <p className="mb-10 rounded-md border border-borde bg-panel-hoja px-4 py-2.5 text-center text-xs text-tinta-tenue">
        El manuscrito aún no está ensamblado. Se muestran los {datos.capitulos.length} capítulos
        aprobados, en orden.
      </p>

      {datos.capitulos.map((capitulo) => (
        <article key={capitulo.numero} className="mb-16 last:mb-0">
          <p className="mb-2 text-center font-dato text-xs tracking-wide text-tinta-tenue uppercase">
            Capítulo {capitulo.numero} · intento {capitulo.intento} ·{' '}
            {formatearPalabras(capitulo.palabras)}
            {capitulo.porAgotamiento && ' · aceptado por agotamiento'}
          </p>
          <Markdown texto={capitulo.cuerpo} registro="lectura" />
        </article>
      ))}
    </div>
  )
}
