// Documentos: la biblia, las escaletas, el libro de estado y demás material de
// referencia. Índice a la izquierda, documento a la derecha.

import { api } from '../lib/api'
import { formatearPalabras } from '../lib/formato'
import { escribirRuta } from '../lib/ruta'
import { useDatos } from '../lib/useDatos'
import type { Documento, DocumentoConTexto, Novela } from '../lib/tipos'
import { Markdown } from './Markdown'
import { Cargando, Fallo, Vacio } from './ui/Estados'

function Indice({
  documentos,
  slug,
  activo,
}: {
  documentos: Documento[]
  slug: string
  activo: string | null
}) {
  return (
    <nav className="space-y-1" aria-label="Documentos de la novela">
      {documentos.map((documento) => {
        const seleccionado = documento.id === activo
        return (
          <a
            key={documento.id}
            href={escribirRuta({
              vista: 'novela',
              slug,
              pestana: 'documentos',
              seleccion: documento.id,
            })}
            aria-current={seleccionado ? 'page' : undefined}
            className={`block rounded-md border px-3 py-2 text-sm transition ${
              seleccionado
                ? 'border-acento bg-acento-suave text-acento'
                : 'border-transparent text-tinta-suave hover:border-borde hover:bg-panel-hoja'
            }`}
          >
            <span className="block font-medium">{documento.titulo}</span>
            <span className="block text-xs text-tinta-tenue">
              {formatearPalabras(documento.palabras)}
            </span>
          </a>
        )
      })}
    </nav>
  )
}

function Contenido({
  slug,
  id,
  refrescando,
}: {
  slug: string
  id: string
  refrescando: boolean
}) {
  const { datos, cargando, error, recargar } = useDatos<DocumentoConTexto>(
    (señal) => api.leerDocumento(slug, id, señal),
    `documento:${slug}:${id}`,
    refrescando,
  )

  if (cargando && datos === null) return <Cargando que="el documento" />
  if (error !== null && datos === null) return <Fallo mensaje={error} alReintentar={recargar} />
  if (datos === null) return null

  return (
    <article className="rounded-lg border border-borde bg-panel-hoja p-6">
      <header className="mb-4 border-b border-borde pb-3">
        <h2 className="text-base font-semibold text-tinta">{datos.titulo}</h2>
        <p className="font-dato text-xs text-tinta-tenue">{datos.ruta}</p>
      </header>
      <Markdown texto={datos.cuerpo} />
    </article>
  )
}

interface Props {
  novela: Novela
  seleccion: string | null
  refrescando: boolean
}

export function PestanaDocumentos({ novela, seleccion, refrescando }: Props) {
  if (novela.documentos.length === 0) {
    return <Vacio titulo="Esta novela todavía no tiene documentos" />
  }

  const activo = novela.documentos.some((d) => d.id === seleccion)
    ? seleccion
    : (novela.documentos[0]?.id ?? null)

  return (
    <div className="mx-auto max-w-6xl gap-6 px-6 py-8 lg:grid lg:grid-cols-[16rem_minmax(0,1fr)]">
      <aside className="mb-6 lg:mb-0">
        <Indice documentos={novela.documentos} slug={novela.slug} activo={activo} />
      </aside>
      {activo !== null && <Contenido slug={novela.slug} id={activo} refrescando={refrescando} />}
    </div>
  )
}
