// Etiqueta de estado. Un tono por significado, nunca por decoración.

import type { ReactNode } from 'react'

export type TonoEtiqueta = 'neutro' | 'aprobado' | 'rechazado' | 'aviso' | 'acento'

const TONOS: Record<TonoEtiqueta, string> = {
  neutro: 'bg-panel text-tinta-suave border-borde',
  aprobado: 'bg-aprobado-fondo text-aprobado border-aprobado/25',
  rechazado: 'bg-rechazado-fondo text-rechazado border-rechazado/25',
  aviso: 'bg-aviso-fondo text-aviso border-aviso/25',
  acento: 'bg-acento-suave text-acento border-acento/25',
}

interface Props {
  tono?: TonoEtiqueta
  titulo?: string
  children: ReactNode
}

export function Etiqueta({ tono = 'neutro', titulo, children }: Props) {
  return (
    <span
      title={titulo}
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium whitespace-nowrap ${TONOS[tono]}`}
    >
      {children}
    </span>
  )
}
