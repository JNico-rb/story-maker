// Pinta el Markdown que escribió el harness.
//
// El contenido es local y lo ha generado este mismo repositorio, pero aun así se
// quitan las etiquetas ejecutables antes de insertarlo: cuesta diez líneas y
// evita que un capítulo con HTML dentro se ejecute en el navegador.

import { useMemo } from 'react'
import { marked } from 'marked'

marked.setOptions({ gfm: true, breaks: false })

const ETIQUETAS_PROHIBIDAS = /<\/?(script|style|iframe|object|embed|form|link|meta)\b[^>]*>/gi
const ATRIBUTOS_DE_EVENTO = /\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi
const URLS_EJECUTABLES = /(href|src)\s*=\s*("|')\s*javascript:[^"']*\2/gi

function limpiar(html: string): string {
  return html
    .replace(ETIQUETAS_PROHIBIDAS, '')
    .replace(ATRIBUTOS_DE_EVENTO, '')
    .replace(URLS_EJECUTABLES, '')
}

interface Props {
  texto: string
  /** «lectura» para la prosa de la novela; «panel» para documentos de trabajo. */
  registro?: 'lectura' | 'panel'
}

export function Markdown({ texto, registro = 'panel' }: Props) {
  const html = useMemo(() => limpiar(marked.parse(texto, { async: false })), [texto])
  return (
    <div
      className={registro === 'lectura' ? 'prosa-lectura' : 'prosa-panel'}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
