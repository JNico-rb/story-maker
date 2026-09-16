// Presentación de valores. Intl y Date nativos; nada de librerías de fechas.

import type { Etapa, Gravedad } from './tipos'

const numero = new Intl.NumberFormat('es-ES')
const fechaHora = new Intl.DateTimeFormat('es-ES', { dateStyle: 'medium', timeStyle: 'short' })

export const formatearNumero = (valor: number): string => numero.format(valor)

export function formatearFecha(iso: string): string {
  const fecha = new Date(iso)
  return Number.isNaN(fecha.getTime()) ? '—' : fechaHora.format(fecha)
}

export function formatearPalabras(palabras: number): string {
  return `${numero.format(palabras)} palabra${palabras === 1 ? '' : 's'}`
}

export const TITULO_ETAPA: Record<Etapa, string> = {
  interrogatorio: 'Interrogatorio',
  capitulos: 'Escribiendo capítulos',
  final: 'Cierre',
  desconocida: 'Etapa desconocida',
}

/** Los cinco criterios del revisor, tal como los numera specs/functional.md §5.4. */
export const TITULO_GRAVEDAD: Record<Gravedad, string> = {
  1: 'Contradice la biblia o el libro de estado',
  2: 'No cumple la escaleta o adelanta sucesos',
  3: 'Longitud fuera de tolerancia',
  4: 'Ruptura de voz, punto de vista o tono',
  5: 'El resumen no refleja el capítulo',
}

export function esGrave(gravedad: Gravedad | null): boolean {
  return gravedad === 1 || gravedad === 2
}

export interface Desviacion {
  palabras: number
  objetivo: number
  desviacion: number
  dentro: boolean
  minimo: number
  maximo: number
}

/**
 * Compara las palabras de un intento con su longitud objetivo, con la misma
 * regla que aplica el harness antes de invocar al revisor (§4.2).
 * No es una métrica de calidad: es el dato que el harness ya usó para decidir.
 */
export function medirLongitud(
  palabras: number,
  objetivo: number | null,
  tolerancia: number | null,
): Desviacion | null {
  if (objetivo === null || objetivo <= 0) return null
  const margen = tolerancia ?? 0
  const minimo = Math.round(objetivo * (1 - margen))
  const maximo = Math.round(objetivo * (1 + margen))
  return {
    palabras,
    objetivo,
    desviacion: (palabras - objetivo) / objetivo,
    dentro: palabras >= minimo && palabras <= maximo,
    minimo,
    maximo,
  }
}

export function formatearDesviacion(desviacion: number): string {
  const porcentaje = Math.round(desviacion * 100)
  return `${porcentaje > 0 ? '+' : ''}${porcentaje} %`
}
