// Los tres estados que toda vista que pide datos tiene que saber enseñar:
// está cargando, ha fallado, o no hay nada que enseñar todavía.

import type { ReactNode } from 'react'

export function Cargando({ que }: { que: string }) {
  return (
    <div className="flex items-center gap-3 px-6 py-10 text-sm text-tinta-tenue">
      <span
        aria-hidden
        className="size-3.5 animate-spin rounded-full border-2 border-borde-fuerte border-t-acento"
      />
      Cargando {que}…
    </div>
  )
}

export function Fallo({ mensaje, alReintentar }: { mensaje: string; alReintentar?: () => void }) {
  return (
    <div
      role="alert"
      className="m-6 rounded-lg border border-rechazado/25 bg-rechazado-fondo px-4 py-3 text-sm text-rechazado"
    >
      <p className="font-medium">No se han podido leer los datos.</p>
      <p className="mt-1 text-tinta-suave">{mensaje}</p>
      {alReintentar && (
        <button
          type="button"
          onClick={alReintentar}
          className="mt-3 rounded-md border border-rechazado/30 bg-panel-hoja px-3 py-1.5 text-xs font-medium text-rechazado hover:bg-rechazado-fondo"
        >
          Reintentar
        </button>
      )}
    </div>
  )
}

export function Vacio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="m-6 rounded-lg border border-dashed border-borde-fuerte bg-panel-hoja px-6 py-10 text-center">
      <p className="text-sm font-medium text-tinta">{titulo}</p>
      {children && <div className="mx-auto mt-2 max-w-prose text-sm text-tinta-tenue">{children}</div>}
    </div>
  )
}
