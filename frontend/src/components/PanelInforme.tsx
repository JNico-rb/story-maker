// El informe de un intento: veredicto, problemas por gravedad y observaciones.
// Es la respuesta a «¿por qué tumbaron este intento?», que es lo que cuesta
// reconstruir abriendo ficheros a mano.

import { esGrave, TITULO_GRAVEDAD } from '../lib/formato'
import type { Gravedad, Informe, Problema } from '../lib/tipos'
import { Etiqueta } from './ui/Etiqueta'

const BORDE_GRAVEDAD: Record<Gravedad, string> = {
  1: 'border-l-gravedad-1',
  2: 'border-l-gravedad-2',
  3: 'border-l-gravedad-3',
  4: 'border-l-gravedad-4',
  5: 'border-l-gravedad-5',
}

const TEXTO_GRAVEDAD: Record<Gravedad, string> = {
  1: 'text-gravedad-1',
  2: 'text-gravedad-2',
  3: 'text-gravedad-3',
  4: 'text-gravedad-4',
  5: 'text-gravedad-5',
}

function FichaProblema({ problema, indice }: { problema: Problema; indice: number }) {
  const gravedad = problema.gravedad
  const borde = gravedad === null ? 'border-l-borde-fuerte' : BORDE_GRAVEDAD[gravedad]
  const color = gravedad === null ? 'text-tinta-tenue' : TEXTO_GRAVEDAD[gravedad]

  return (
    <li className={`rounded-r-md border-l-3 bg-panel-hoja py-3 pr-3 pl-4 ${borde}`}>
      <div className="flex items-baseline gap-2">
        <span className="font-dato text-xs text-tinta-tenue">{indice}</span>
        <span className={`text-xs font-semibold ${color}`}>
          Gravedad {gravedad ?? '?'}
          {esGrave(gravedad) && ' · grave'}
        </span>
      </div>
      {gravedad !== null && (
        <p className="mt-0.5 text-xs text-tinta-tenue">{TITULO_GRAVEDAD[gravedad]}</p>
      )}

      <dl className="mt-2 space-y-1.5 text-sm">
        <div>
          <dt className="text-xs font-medium text-tinta-tenue">Dónde</dt>
          <dd className="text-tinta-suave">{problema.donde || '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-tinta-tenue">Qué</dt>
          <dd className="text-tinta">{problema.que || '—'}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium text-tinta-tenue">Por qué</dt>
          <dd className="text-tinta-suave">{problema.porQue || '—'}</dd>
        </div>
      </dl>
    </li>
  )
}

export function PanelInforme({ informe }: { informe: Informe }) {
  const aprobado = informe.veredicto === 'APROBADO'
  const discrepancia =
    informe.veredictoRevisor !== null && informe.veredictoRevisor !== informe.veredicto

  return (
    <section className="rounded-lg border border-borde bg-panel p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-tinta">Informe</h3>
        <Etiqueta tono={aprobado ? 'aprobado' : 'rechazado'}>
          {informe.veredicto ?? 'sin veredicto'}
        </Etiqueta>
        {informe.origen === 'harness' && (
          <Etiqueta tono="aviso" titulo="Rechazo por longitud: el harness no llegó a invocar al revisor">
            emitido por el harness
          </Etiqueta>
        )}
        {discrepancia && (
          <Etiqueta tono="aviso" titulo="El veredicto del revisor no coincide con el recalculado por el harness">
            discrepancia: el revisor dijo {informe.veredictoRevisor}
          </Etiqueta>
        )}
      </div>

      <p className="mt-2 text-xs text-tinta-tenue">
        {informe.graves} problema{informe.graves === 1 ? '' : 's'} de gravedad 1–2 ·{' '}
        {informe.leves} de gravedad 3–5
      </p>

      {informe.problemas.length > 0 ? (
        <ol className="mt-3 space-y-2">
          {informe.problemas.map((problema, i) => (
            <FichaProblema key={i} problema={problema} indice={i + 1} />
          ))}
        </ol>
      ) : (
        <p className="mt-3 text-sm text-tinta-suave">Sin problemas registrados.</p>
      )}

      {informe.observaciones.length > 0 && (
        <details className="mt-3 rounded-md border border-borde bg-panel-hoja px-3 py-2">
          <summary className="cursor-pointer text-xs font-medium text-tinta-suave">
            {informe.observaciones.length} observación
            {informe.observaciones.length === 1 ? '' : 'es'} menor
            {informe.observaciones.length === 1 ? '' : 'es'} (no obligan a reescribir)
          </summary>
          <ul className="mt-2 space-y-1.5 text-sm text-tinta-suave">
            {informe.observaciones.map((observacion, i) => (
              <li key={i} className="border-l-2 border-borde pl-3">
                {observacion}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}
