// Pantalla inicial: todas las novelas de novelas/, con su estado de un vistazo.

import { Etiqueta } from './ui/Etiqueta'
import { formatearFecha, TITULO_ETAPA } from '../lib/formato'
import { escribirRuta } from '../lib/ruta'
import type { ResumenNovela } from '../lib/tipos'

function Progreso({ novela }: { novela: ResumenNovela }) {
  const total = novela.totalCapitulos
  if (total === null || total === 0) {
    return <p className="text-sm text-tinta-tenue">Sin escaleta aprobada todavía.</p>
  }

  const porcentaje = Math.round((novela.capitulosAprobados / total) * 100)
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-tinta-suave">
          {novela.capitulosAprobados} de {total} capítulos aprobados
        </span>
        <span className="font-dato text-xs text-tinta-tenue">{porcentaje} %</span>
      </div>
      <div
        className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-borde"
        role="progressbar"
        aria-valuenow={novela.capitulosAprobados}
        aria-valuemin={0}
        aria-valuemax={total}
      >
        <div className="h-full rounded-full bg-acento" style={{ width: `${porcentaje}%` }} />
      </div>
    </div>
  )
}

function Tarjeta({ novela }: { novela: ResumenNovela }) {
  return (
    <a
      href={escribirRuta({ vista: 'novela', slug: novela.slug, pestana: 'leer', seleccion: null })}
      className="block rounded-xl border border-borde bg-panel-hoja p-5 transition hover:border-borde-fuerte hover:shadow-sm"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-tinta">{novela.titulo}</h2>
          <p className="font-dato text-xs text-tinta-tenue">{novela.slug}</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {novela.completa ? (
            <Etiqueta tono="aprobado">Completa</Etiqueta>
          ) : (
            <Etiqueta tono="acento">{TITULO_ETAPA[novela.etapa]}</Etiqueta>
          )}
          {novela.modoPrueba && (
            <Etiqueta tono="aviso" titulo="Ejecución en modo de prueba (spec §8.1)">
              Modo de prueba
            </Etiqueta>
          )}
        </div>
      </div>

      <div className="mt-4">
        <Progreso novela={novela} />
      </div>

      <dl className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-xs text-tinta-tenue">
        {novela.perfil !== null && (
          <div className="flex gap-1.5">
            <dt>Perfil</dt>
            <dd className="font-medium text-tinta-suave">{novela.perfil}</dd>
          </div>
        )}
        {!novela.completa && novela.capituloActual !== null && (
          <div className="flex gap-1.5">
            <dt>En curso</dt>
            <dd className="font-medium text-tinta-suave">
              capítulo {novela.capituloActual}
              {novela.intentoActual !== null && `, intento ${novela.intentoActual}`}
            </dd>
          </div>
        )}
        <div className="flex gap-1.5">
          <dt>Última escritura</dt>
          <dd className="font-medium text-tinta-suave">{formatearFecha(novela.actualizado)}</dd>
        </div>
      </dl>

      {novela.avisos.length > 0 && (
        <p className="mt-3 rounded-md bg-aviso-fondo px-3 py-2 text-xs text-aviso">
          {novela.avisos.length} aviso{novela.avisos.length === 1 ? '' : 's'} del harness
        </p>
      )}
    </a>
  )
}

export function ListaNovelas({ novelas }: { novelas: ResumenNovela[] }) {
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-2xl font-semibold text-tinta">Novelas</h1>
        <p className="mt-1 text-sm text-tinta-tenue">
          Todo lo que hay en <code className="font-dato">novelas/</code>. El visor solo lee: nada de
          lo que veas aquí se puede modificar desde el navegador.
        </p>
      </header>

      <div className="grid gap-4">
        {novelas.map((novela) => (
          <Tarjeta key={novela.slug} novela={novela} />
        ))}
      </div>
    </div>
  )
}
