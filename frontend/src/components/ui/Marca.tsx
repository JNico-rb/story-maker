// La marca Qaracter. Los tres ficheros de public/ se derivan del logotipo original
// (images/qaracter-logo.png): ver frontend/CLAUDE.md › Marca.

/** Logotipo completo (isotipo + «qaracter»). Lleva el nombre, así que es texto. */
export function Logotipo({ className = 'h-6 w-auto' }: { className?: string }) {
  return (
    <img
      src="/qaracter-logo.png"
      alt="Qaracter"
      width={1200}
      height={278}
      className={className}
      decoding="async"
    />
  )
}

/** Solo el símbolo. Es decoración: nunca lleva el nombre, así que no lleva texto alternativo. */
export function Isotipo({ className = 'h-6 w-auto' }: { className?: string }) {
  return (
    <img
      src="/qaracter-isotipo.png"
      alt=""
      aria-hidden
      width={256}
      height={256}
      className={className}
      decoding="async"
    />
  )
}
