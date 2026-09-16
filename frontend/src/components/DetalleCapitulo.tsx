// Un capítulo por dentro: su ficha de escaleta, sus intentos, y para cada
// intento el texto con el informe al lado.

import { useState } from 'react'
import { api } from '../lib/api'
import { formatearDesviacion, formatearPalabras, medirLongitud } from '../lib/formato'
import { escribirRuta } from '../lib/ruta'
import { useDatos } from '../lib/useDatos'
import type { CapituloConTexto, IntentoConTexto } from '../lib/tipos'
import { Markdown } from './Markdown'
import { PanelInforme } from './PanelInforme'
import { Etiqueta } from './ui/Etiqueta'
import { Cargando, Fallo } from './ui/Estados'

function FichaEscaleta({ capitulo }: { capitulo: CapituloConTexto }) {
  const tieneAlgo =
    capitulo.objetivo !== null ||
    capitulo.sucesos.length > 0 ||
    capitulo.personajes.length > 0 ||
    capitulo.gancho !== null

  if (!tieneAlgo) return null

  return (
    <section className="rounded-lg border border-borde bg-panel-hoja p-4">
      <h3 className="text-sm font-semibold text-tinta">Lo que la escaleta pedía</h3>

      {capitulo.objetivo !== null && (
        <p className="mt-2 text-sm text-tinta-suave">
          <span className="font-medium text-tinta">Objetivo. </span>
          {capitulo.objetivo}
        </p>
      )}

      {capitulo.sucesos.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-tinta-tenue">Sucesos clave</p>
          <ul className="mt-1 space-y-1 text-sm text-tinta-suave">
            {capitulo.sucesos.map((suceso, i) => (
              <li key={i} className="border-l-2 border-borde pl-3">
                {suceso}
              </li>
            ))}
          </ul>
        </div>
      )}

      {capitulo.gancho !== null && (
        <p className="mt-3 text-sm text-tinta-suave">
          <span className="font-medium text-tinta">Gancho. </span>
          {capitulo.gancho}
        </p>
      )}

      {capitulo.personajes.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {capitulo.personajes.map((personaje) => (
            <Etiqueta key={personaje}>{personaje}</Etiqueta>
          ))}
        </div>
      )}
    </section>
  )
}

function Longitud({
  intento,
  objetivo,
  tolerancia,
}: {
  intento: IntentoConTexto
  objetivo: number | null
  tolerancia: number | null
}) {
  const medida = medirLongitud(intento.palabras, objetivo, tolerancia)
  if (medida === null) return <span>{formatearPalabras(intento.palabras)}</span>

  return (
    <span className={medida.dentro ? 'text-tinta-tenue' : 'text-rechazado'}>
      {formatearPalabras(medida.palabras)} · objetivo {medida.objetivo} (
      {formatearDesviacion(medida.desviacion)}
      {medida.dentro ? '' : `, fuera del margen ${medida.minimo}–${medida.maximo}`})
    </span>
  )
}

function VistaIntento({
  intento,
  capitulo,
  tolerancia,
}: {
  intento: IntentoConTexto
  capitulo: CapituloConTexto
  tolerancia: number | null
}) {
  const [verResumen, setVerResumen] = useState(false)
  const esAprobado = capitulo.aprobado === intento.numero

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] lg:items-start">
      <article className="rounded-lg border border-borde bg-papel p-6">
        <div className="mb-4 flex flex-wrap items-center gap-2 border-b border-borde pb-3">
          <h3 className="text-sm font-semibold text-tinta">
            Intento {intento.numero}
            {esAprobado && (capitulo.porAgotamiento ? ' · aceptado' : ' · aprobado')}
          </h3>
          {intento.resumen !== null && (
            <button
              type="button"
              onClick={() => setVerResumen((v) => !v)}
              className="ml-auto rounded-md border border-borde bg-panel-hoja px-2.5 py-1 text-xs font-medium text-tinta-suave hover:border-borde-fuerte"
            >
              {verResumen ? 'Ver el texto' : 'Ver el resumen'}
            </button>
          )}
        </div>

        {verResumen && intento.resumen !== null ? (
          <Markdown texto={intento.resumen} />
        ) : (
          <Markdown texto={intento.texto} registro="lectura" />
        )}
      </article>

      <div className="space-y-4 lg:sticky lg:top-44">
        <div className="rounded-lg border border-borde bg-panel-hoja px-4 py-3 text-xs">
          <Longitud intento={intento} objetivo={capitulo.palabrasObjetivo} tolerancia={tolerancia} />
        </div>

        {intento.informe !== null ? (
          <PanelInforme informe={intento.informe} />
        ) : (
          <p className="rounded-lg border border-dashed border-borde-fuerte px-4 py-6 text-center text-sm text-tinta-tenue">
            Este intento todavía no tiene informe. El harness está en ello.
          </p>
        )}
      </div>
    </div>
  )
}

interface Props {
  slug: string
  numero: number
  tolerancia: number | null
  refrescando: boolean
}

export function DetalleCapitulo({ slug, numero, tolerancia, refrescando }: Props) {
  const { datos, cargando, error, recargar } = useDatos<CapituloConTexto>(
    (señal) => api.leerCapitulo(slug, numero, señal),
    `capitulo:${slug}:${numero}`,
    refrescando,
  )
  const [intentoVisible, setIntentoVisible] = useState<number | null>(null)

  if (cargando && datos === null) return <Cargando que={`el capítulo ${numero}`} />
  if (error !== null && datos === null) return <Fallo mensaje={error} alReintentar={recargar} />
  if (datos === null) return null

  const porDefecto = datos.aprobado ?? datos.intentos.at(-1)?.numero ?? null
  const elegido = intentoVisible ?? porDefecto
  const intento = datos.intentos.find((i) => i.numero === elegido) ?? null

  return (
    <div className="mx-auto max-w-6xl space-y-5 px-6 py-8">
      <div>
        <a
          href={escribirRuta({ vista: 'novela', slug, pestana: 'progreso', seleccion: null })}
          className="text-xs text-acento hover:underline"
        >
          ← Todos los capítulos
        </a>
        <h2 className="mt-1 text-xl font-semibold text-tinta">
          Capítulo {datos.numero}
          {datos.titulo !== null && <span className="text-tinta-suave"> · {datos.titulo}</span>}
        </h2>
      </div>

      <FichaEscaleta capitulo={datos} />

      {datos.intentos.length > 1 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-tinta-tenue">Intentos:</span>
          {datos.intentos.map((candidato) => {
            const activo = candidato.numero === elegido
            const veredicto = candidato.informe?.veredicto ?? null
            return (
              <button
                key={candidato.numero}
                type="button"
                onClick={() => setIntentoVisible(candidato.numero)}
                aria-pressed={activo}
                className={`rounded-md border px-3 py-1.5 text-xs font-medium transition ${
                  activo
                    ? 'border-acento bg-acento-suave text-acento'
                    : 'border-borde bg-panel-hoja text-tinta-suave hover:border-borde-fuerte'
                }`}
              >
                {candidato.numero}
                {veredicto !== null && (
                  <span
                    className={veredicto === 'APROBADO' ? 'text-aprobado' : 'text-rechazado'}
                    title={veredicto}
                  >
                    {' '}
                    ●
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {intento === null ? (
        <p className="rounded-lg border border-dashed border-borde-fuerte px-4 py-10 text-center text-sm text-tinta-tenue">
          Este capítulo todavía no tiene ningún intento escrito.
        </p>
      ) : (
        <VistaIntento intento={intento} capitulo={datos} tolerancia={tolerancia} />
      )}
    </div>
  )
}
