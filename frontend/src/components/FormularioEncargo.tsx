// El formulario del estudio: lo que el usuario rellena antes de que exista la
// novela (spec §9.4).
//
// No sustituye a la entrevista. La spec §4.1 la define como rondas sucesivas
// sin límite fijo, y un formulario no repregunta. Esto la PRECARGA: sus
// respuestas entran como punto de partida del grilling, que sigue corriendo y
// solo pregunta lo que falte. Por eso dejar un campo vacío es legítimo y
// significa «decide tú», no «sin contestar».

import { useMemo, useState } from 'react'
import { api } from '../lib/api'
import { irA } from '../lib/ruta'
import type { Pregunta } from '../lib/tipos'

const PERFILES = [
  { valor: '', etiqueta: 'El de config.json (sin tocar)' },
  { valor: 'relato', etiqueta: 'relato · 5 capítulos de 1.500 palabras' },
  { valor: 'novela_corta', etiqueta: 'novela_corta · 12 capítulos de 2.000' },
  { valor: 'novela', etiqueta: 'novela · 30 capítulos de 2.500' },
  { valor: 'saga', etiqueta: 'saga · 100 capítulos de 2.500' },
]

const AYUDA: Record<string, string> = {
  mundo_que_paso: 'Qué ocurrió con la IA y cómo quedó el mundo después.',
  mundo_reglas: 'Lo que ahora es ley, costumbre o imposible.',
  mundo_vida: 'Lo que se nota al salir a la calle.',
  protagonista: 'Quién es, qué persigue y qué le falta para conseguirlo.',
  antagonismo: 'No hace falta un villano: puede ser una duda, un sistema o un vecindario.',
  tono: 'Sobrio, irónico, épico, seco… y cuánto humor.',
  punto_de_vista: 'Tercera limitada, primera, presente o pasado.',
  final: 'Cerrado, abierto, amargo, esperanzado.',
  temas_tocar: 'Lo que quieres que la novela mire de frente.',
  temas_evitar: 'Lo que no quieres leer bajo ningún concepto.',
  capitulos: 'Déjalo vacío para usar el del perfil.',
  palabras: 'Por capítulo. Vacío para usar el del perfil.',
}

const CAMPOS_CORTOS = new Set(['tono', 'punto_de_vista', 'final', 'capitulos', 'palabras'])

export function FormularioEncargo({ preguntas }: { preguntas: Pregunta[] }) {
  const [idea, setIdea] = useState('')
  const [perfil, setPerfil] = useState('')
  const [respuestas, setRespuestas] = useState<Record<string, string>>({})
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const secciones = useMemo(() => {
    const mapa = new Map<string, Pregunta[]>()
    for (const pregunta of preguntas) {
      const lista = mapa.get(pregunta.seccion) ?? []
      lista.push(pregunta)
      mapa.set(pregunta.seccion, lista)
    }
    return [...mapa.entries()]
  }, [preguntas])

  const contestadas = preguntas.filter((p) => (respuestas[p.id] ?? '').trim() !== '').length
  const listo = idea.trim() !== '' && !enviando

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    if (!listo) return

    setEnviando(true)
    setError(null)
    try {
      const { slug } = await api.crearEncargo({
        idea,
        respuestas,
        ajustes: perfil === '' ? {} : { perfil_activo: perfil },
      })
      irA({ vista: 'estudio', encargo: slug })
    } catch (causa) {
      setError(causa instanceof Error ? causa.message : 'No se ha podido crear el encargo.')
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-3xl px-6 py-8">
      <h1 className="text-xl font-semibold tracking-tight text-tinta">Encargar una novela</h1>
      <p className="mt-2 max-w-prose text-sm text-tinta-tenue">
        Rellena lo que tengas claro. Lo que dejes vacío queda en{' '}
        <strong className="font-medium text-tinta-suave">decide tú</strong>, y lo que quede flojo te
        lo preguntará el interrogatorio después: esto no es la entrevista, es su punto de partida.
      </p>

      <label className="mt-8 block">
        <span className="text-sm font-medium text-tinta">La idea</span>
        <span className="ml-2 text-xs text-tinta-tenue">Una o dos frases. Es lo único obligatorio.</span>
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          rows={3}
          required
          placeholder="Una técnica de mantenimiento de ascensores que nunca quiso saber nada de la IA, hasta que una le pide algo."
          className="mt-2 w-full rounded-lg border border-borde-fuerte bg-panel-hoja px-3 py-2 text-sm text-tinta placeholder:text-tinta-tenue focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
        />
      </label>

      <label className="mt-6 block">
        <span className="text-sm font-medium text-tinta">Tamaño</span>
        <select
          value={perfil}
          onChange={(e) => setPerfil(e.target.value)}
          className="mt-2 w-full rounded-lg border border-borde-fuerte bg-panel-hoja px-3 py-2 text-sm text-tinta focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
        >
          {PERFILES.map((p) => (
            <option key={p.valor} value={p.valor}>
              {p.etiqueta}
            </option>
          ))}
        </select>
      </label>

      {secciones.map(([seccion, lista]) => (
        <fieldset key={seccion} className="mt-8">
          <legend className="text-sm font-semibold text-tinta">{seccion}</legend>
          <div className="mt-3 space-y-4">
            {lista.map((pregunta) => (
              <label key={pregunta.id} className="block">
                <span className="text-sm text-tinta-suave">{pregunta.texto}</span>
                {AYUDA[pregunta.id] !== undefined && (
                  <span className="mt-0.5 block text-xs text-tinta-tenue">{AYUDA[pregunta.id]}</span>
                )}
                {CAMPOS_CORTOS.has(pregunta.id) ? (
                  <input
                    type="text"
                    value={respuestas[pregunta.id] ?? ''}
                    onChange={(e) =>
                      setRespuestas((previo) => ({ ...previo, [pregunta.id]: e.target.value }))
                    }
                    className="mt-1.5 w-full rounded-lg border border-borde bg-panel-hoja px-3 py-2 text-sm text-tinta focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
                  />
                ) : (
                  <textarea
                    value={respuestas[pregunta.id] ?? ''}
                    onChange={(e) =>
                      setRespuestas((previo) => ({ ...previo, [pregunta.id]: e.target.value }))
                    }
                    rows={2}
                    className="mt-1.5 w-full rounded-lg border border-borde bg-panel-hoja px-3 py-2 text-sm text-tinta focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
                  />
                )}
              </label>
            ))}
          </div>
        </fieldset>
      ))}

      {error !== null && (
        <p
          role="alert"
          className="mt-6 rounded-lg border border-rechazado/25 bg-rechazado-fondo px-4 py-3 text-sm text-rechazado"
        >
          {error}
        </p>
      )}

      <div className="sticky bottom-0 mt-8 flex flex-wrap items-center gap-4 border-t border-borde bg-panel/95 py-4 backdrop-blur">
        <button
          type="submit"
          disabled={!listo}
          className="rounded-md bg-acento px-4 py-2 text-sm font-medium text-papel-hoja disabled:opacity-40"
        >
          {enviando ? 'Creando el encargo…' : 'Empezar'}
        </button>
        <p className="text-xs text-tinta-tenue">
          {contestadas} de {preguntas.length} contestadas · el resto queda en «decide tú»
        </p>
      </div>
    </form>
  )
}
