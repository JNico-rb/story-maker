// Cabecera fija de una novela: identidad, estado, pestañas y control del refresco.

import { Etiqueta } from './ui/Etiqueta'
import { formatearFecha, TITULO_ETAPA } from '../lib/formato'
import { escribirRuta, PESTANAS, TITULO_PESTANA, type Pestana } from '../lib/ruta'
import type { Novela } from '../lib/tipos'

interface Props {
  novela: Novela
  pestana: Pestana
  refrescando: boolean
  alCambiarRefresco: (valor: boolean) => void
}

export function CabeceraNovela({ novela, pestana, refrescando, alCambiarRefresco }: Props) {
  return (
    <header className="sticky top-0 z-10 border-b border-borde bg-panel-hoja/95 backdrop-blur">
      <div className="mx-auto max-w-6xl px-6 pt-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <a href={escribirRuta({ vista: 'lista' })} className="text-xs text-acento hover:underline">
              ← Todas las novelas
            </a>
            <h1 className="mt-1 text-xl font-semibold text-tinta">{novela.titulo}</h1>
            <p className="font-dato text-xs text-tinta-tenue">{novela.slug}</p>
          </div>

          <div className="flex flex-col items-end gap-2">
            <div className="flex flex-wrap justify-end gap-1.5">
              {novela.completa ? (
                <Etiqueta tono="aprobado">Completa</Etiqueta>
              ) : (
                <Etiqueta tono="acento">{TITULO_ETAPA[novela.etapa]}</Etiqueta>
              )}
              {novela.modoPrueba && <Etiqueta tono="aviso">Modo de prueba</Etiqueta>}
              {novela.perfil !== null && <Etiqueta>Perfil: {novela.perfil}</Etiqueta>}
            </div>

            <label className="flex cursor-pointer items-center gap-2 text-xs text-tinta-tenue">
              <input
                type="checkbox"
                checked={refrescando}
                onChange={(evento) => alCambiarRefresco(evento.target.checked)}
                className="size-3.5 accent-acento"
              />
              Refrescar cada 5 s
              {refrescando && (
                <span aria-hidden className="size-1.5 animate-pulse rounded-full bg-acento" />
              )}
            </label>
          </div>
        </div>

        <p className="mt-3 text-xs text-tinta-tenue">
          Última escritura del harness: {formatearFecha(novela.actualizado)}
        </p>

        <nav className="-mb-px mt-3 flex gap-1 overflow-x-auto" aria-label="Secciones de la novela">
          {PESTANAS.map((clave) => {
            const activa = clave === pestana
            return (
              <a
                key={clave}
                href={escribirRuta({
                  vista: 'novela',
                  slug: novela.slug,
                  pestana: clave,
                  seleccion: null,
                })}
                aria-current={activa ? 'page' : undefined}
                className={`border-b-2 px-4 py-2 text-sm font-medium whitespace-nowrap transition ${
                  activa
                    ? 'border-acento text-acento'
                    : 'border-transparent text-tinta-tenue hover:border-borde-fuerte hover:text-tinta-suave'
                }`}
              >
                {TITULO_PESTANA[clave]}
              </a>
            )
          })}
        </nav>
      </div>
    </header>
  )
}
