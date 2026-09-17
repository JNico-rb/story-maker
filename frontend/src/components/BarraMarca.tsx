// Barra de marca: lo primero que se ve en cualquier pantalla del visor.
// No es navegación de la novela (de eso va CabeceraNovela): es la identidad y la
// vuelta al principio. Por eso no es pegajosa y deja el sitio de arriba a la
// cabecera de la novela cuando se hace scroll.

import { escribirRuta } from '../lib/ruta'
import { Logotipo } from './ui/Marca'

export function BarraMarca() {
  return (
    <div className="bg-panel-hoja">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-3 gap-y-1 px-6 py-3">
        <a
          href={escribirRuta({ vista: 'lista' })}
          className="shrink-0 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-marca"
          title="Todas las novelas"
        >
          <Logotipo className="h-6 w-auto sm:h-7" />
        </a>
        <span aria-hidden className="h-5 w-px bg-borde-fuerte" />
        <p className="text-sm font-semibold tracking-tight text-tinta">story-maker</p>
        <p className="text-xs text-tinta-tenue">visor de novelas · solo lectura</p>
      </div>
      <div aria-hidden className="h-[3px] bg-marca" />
    </div>
  )
}
