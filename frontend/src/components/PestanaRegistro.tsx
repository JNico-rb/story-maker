// Registro: una fila por invocación y por decisión del harness, filtrable por
// tipo de evento. Es la trazabilidad de la spec §6.6 puesta en una tabla.

import { useMemo, useState } from 'react'
import { formatearNumero } from '../lib/formato'
import type { Novela } from '../lib/tipos'
import { Etiqueta } from './ui/Etiqueta'
import { Vacio } from './ui/Estados'

/** Columnas que solo estorban en pantalla: vacías en el hito 1 (spec §6.6). */
const COLUMNAS_OCULTAS = ['tok_entrada', 'tok_salida', 'coste_usd']

const TONO_EVENTO: Record<string, 'aprobado' | 'rechazado' | 'aviso' | 'acento' | 'neutro'> = {
  invocacion: 'acento',
  veredicto: 'neutro',
  decision_harness: 'neutro',
  discrepancia_veredicto: 'aviso',
  longitud: 'neutro',
  commit: 'neutro',
  inicio_ejecucion: 'acento',
  fin_ejecucion: 'acento',
  paso_descartado: 'aviso',
}

function Volumen({ novela }: { novela: Novela }) {
  const porAgente = useMemo(() => {
    const suma = new Map<string, { invocaciones: number; entrada: number; salida: number }>()
    for (const fila of novela.registro.filas) {
      if (fila['evento'] !== 'invocacion') continue
      const detalle = fila['detalle'] ?? ''
      const agente = detalle.split('·')[0]?.trim() ?? 'desconocido'
      const actual = suma.get(agente) ?? { invocaciones: 0, entrada: 0, salida: 0 }
      actual.invocaciones += 1
      actual.entrada += Number(fila['pal_entrada'] ?? 0) || 0
      actual.salida += Number(fila['pal_salida'] ?? 0) || 0
      suma.set(agente, actual)
    }
    return [...suma.entries()].sort((a, b) => b[1].invocaciones - a[1].invocaciones)
  }, [novela.registro.filas])

  if (porAgente.length === 0) return null

  return (
    <section className="rounded-lg border border-borde bg-panel-hoja p-4">
      <h3 className="text-sm font-semibold text-tinta">Volumen por agente</h3>
      <p className="mt-0.5 text-xs text-tinta-tenue">
        Palabras de entrada y salida contadas por el harness (spec §6.6). En el hito 1 no hay tokens
        ni coste: los dará el runner.
      </p>
      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-tinta-tenue">
            <th className="pb-1 font-medium">Agente</th>
            <th className="pb-1 text-right font-medium">Invocaciones</th>
            <th className="pb-1 text-right font-medium">Palabras leídas</th>
            <th className="pb-1 text-right font-medium">Palabras entregadas</th>
          </tr>
        </thead>
        <tbody>
          {porAgente.map(([agente, datos]) => (
            <tr key={agente} className="border-t border-borde">
              <td className="py-1.5 text-tinta">{agente}</td>
              <td className="py-1.5 text-right font-dato text-tinta-suave">{datos.invocaciones}</td>
              <td className="py-1.5 text-right font-dato text-tinta-suave">
                {formatearNumero(datos.entrada)}
              </td>
              <td className="py-1.5 text-right font-dato text-tinta-suave">
                {formatearNumero(datos.salida)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

export function PestanaRegistro({ novela }: { novela: Novela }) {
  const { columnas, filas } = novela.registro
  const [filtro, setFiltro] = useState<string>('todos')

  const eventos = useMemo(
    () => [...new Set(filas.map((f) => f['evento']).filter((e): e is string => e !== null))].sort(),
    [filas],
  )

  const visibles = useMemo(
    () => (filtro === 'todos' ? filas : filas.filter((f) => f['evento'] === filtro)),
    [filas, filtro],
  )

  if (filas.length === 0) {
    return <Vacio titulo="El registro está vacío" />
  }

  const columnasVisibles = columnas.filter((c) => !COLUMNAS_OCULTAS.includes(c))

  return (
    <div className="mx-auto max-w-6xl space-y-5 px-6 py-8">
      <Volumen novela={novela} />

      <div className="flex flex-wrap items-center gap-1.5">
        <span className="mr-1 text-xs text-tinta-tenue">Eventos:</span>
        {['todos', ...eventos].map((evento) => (
          <button
            key={evento}
            type="button"
            onClick={() => setFiltro(evento)}
            aria-pressed={filtro === evento}
            className={`rounded-md border px-2.5 py-1 font-dato text-xs transition ${
              filtro === evento
                ? 'border-acento bg-acento-suave text-acento'
                : 'border-borde bg-panel-hoja text-tinta-suave hover:border-borde-fuerte'
            }`}
          >
            {evento}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-borde bg-panel-hoja">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-borde bg-panel text-left text-xs text-tinta-tenue">
              {columnasVisibles.map((columna) => (
                <th key={columna} className="px-3 py-2 font-medium whitespace-nowrap">
                  {columna}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visibles.map((fila, i) => (
              <tr key={i} className="border-b border-borde last:border-b-0 align-top">
                {columnasVisibles.map((columna) => {
                  const valor = fila[columna] ?? null
                  if (columna === 'evento' && valor !== null) {
                    return (
                      <td key={columna} className="px-3 py-2">
                        <Etiqueta tono={TONO_EVENTO[valor] ?? 'neutro'}>{valor}</Etiqueta>
                      </td>
                    )
                  }
                  return (
                    <td
                      key={columna}
                      className={`px-3 py-2 ${columna === 'detalle' ? 'min-w-80 text-tinta-suave' : 'font-dato text-xs whitespace-nowrap text-tinta-tenue'}`}
                    >
                      {valor ?? '·'}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
