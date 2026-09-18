// La sesión de un encargo: donde el usuario contesta lo que el harness pregunta.
//
// Tres momentos, y el componente solo decide cuál enseñar:
//   1. El interrogatorio, en rondas. Lo que aquí se escribe va al grilling.
//   2. La propuesta de biblia y escaleta. El harness ha parado con
//      ESPERA_APROBACION y espera una decisión (spec §9.4).
//   3. El bucle, que corre sin intervención humana. Aquí solo se mira.
//
// Nada de esto decide nada del flujo: el estudio manda intenciones y enseña lo
// que el harness escribe. Si una regla de negocio apareciera aquí, estaría en
// el sitio equivocado (frontend/CLAUDE.md, regla 2).

import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { escribirRuta } from '../lib/ruta'
import { useDatos } from '../lib/useDatos'
import type { Encargo, EstadoSesion, EventoHarness, ResumenNovela } from '../lib/tipos'
import { Cargando, Fallo } from './ui/Estados'

const ETIQUETA_ESTADO: Record<EstadoSesion, string> = {
  inactivo: 'sin empezar',
  arrancando: 'arrancando',
  trabajando: 'trabajando',
  esperando: 'te toca',
  parado: 'parado',
  parando: 'parando',
  fallado: 'ha fallado',
}

/** Eventos que se pintan en el hilo. El resto es ruido para una consola, no para esto. */
function esVisible(evento: EventoHarness): boolean {
  return (
    evento.tipo === 'asistente' ||
    evento.tipo === 'usuario' ||
    evento.tipo === 'error' ||
    evento.tipo === 'aviso'
  )
}

function useEventos(slug: string) {
  const [eventos, setEventos] = useState<EventoHarness[]>([])
  const [estado, setEstado] = useState<EstadoSesion>('inactivo')
  const [conectado, setConectado] = useState(false)

  useEffect(() => {
    setEventos([])
    const fuente = api.escucharEventos(slug)

    fuente.onopen = () => setConectado(true)
    fuente.onerror = () => setConectado(false)
    fuente.onmessage = (mensaje) => {
      let evento: EventoHarness
      try {
        evento = JSON.parse(mensaje.data) as EventoHarness
      } catch {
        return
      }

      if (evento.tipo === 'hola' || evento.tipo === 'estado') {
        if (evento.estado !== undefined) setEstado(evento.estado)
      }
      if (esVisible(evento)) setEventos((previos) => [...previos, evento])
    }

    return () => fuente.close()
  }, [slug])

  return { eventos, estado, conectado }
}

function Burbuja({ evento }: { evento: EventoHarness }) {
  if (evento.tipo === 'usuario') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[80%] whitespace-pre-wrap rounded-lg rounded-br-sm bg-acento-suave px-3 py-2 text-sm text-tinta">
          {evento.texto}
        </p>
      </div>
    )
  }

  if (evento.tipo === 'error' || evento.tipo === 'aviso') {
    const grave = evento.tipo === 'error'
    return (
      <p
        role={grave ? 'alert' : undefined}
        className={`rounded-lg border px-3 py-2 text-xs ${
          grave
            ? 'border-rechazado/25 bg-rechazado-fondo text-rechazado'
            : 'border-aviso/25 bg-aviso-fondo text-aviso'
        }`}
      >
        {evento.mensaje ?? evento.texto}
      </p>
    )
  }

  return (
    <p className="max-w-[90%] whitespace-pre-wrap rounded-lg rounded-bl-sm border border-borde bg-panel-hoja px-3 py-2 text-sm text-tinta-suave">
      {evento.texto}
    </p>
  )
}

/**
 * La decisión sobre la propuesta. Solo aparece cuando el harness ha parado con
 * ESPERA_APROBACION: quien decide que la propuesta está lista es el harness, no
 * esta pantalla.
 */
function PanelPropuesta({ encargo, novela }: { encargo: string; novela: ResumenNovela }) {
  const [cambios, setCambios] = useState('')
  const [pidiendo, setPidiendo] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function decidir(decision: 'confirma' | 'cambios') {
    setEnviando(true)
    setError(null)
    try {
      await api.decidir(encargo, decision, cambios)
      await api.actuar(encargo, { tipo: 'continuar', novela: novela.slug })
      setPidiendo(false)
      setCambios('')
    } catch (causa) {
      setError(causa instanceof Error ? causa.message : 'No se ha podido enviar la decisión.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <section className="rounded-lg border border-marca/40 bg-marca-tinte px-4 py-4">
      <h2 className="text-sm font-semibold text-tinta">La propuesta está lista</h2>
      <p className="mt-1 text-sm text-tinta-suave">
        El harness ha escrito la biblia y la escaleta y espera tu decisión. Nada se aprueba sin que
        lo digas tú.
      </p>

      <div className="mt-3 flex flex-wrap gap-3 text-sm">
        <a
          href={escribirRuta({ vista: 'novela', slug: novela.slug, pestana: 'documentos', seleccion: 'biblia' })}
          className="rounded-md border border-borde-fuerte bg-panel-hoja px-3 py-1.5 font-medium text-tinta hover:bg-acento-suave"
        >
          Leer la biblia
        </a>
        <a
          href={escribirRuta({ vista: 'novela', slug: novela.slug, pestana: 'documentos', seleccion: 'escaleta' })}
          className="rounded-md border border-borde-fuerte bg-panel-hoja px-3 py-1.5 font-medium text-tinta hover:bg-acento-suave"
        >
          Leer la escaleta
        </a>
      </div>

      {pidiendo ? (
        <div className="mt-4">
          <label className="block text-sm font-medium text-tinta">Qué quieres que cambie</label>
          <textarea
            value={cambios}
            onChange={(e) => setCambios(e.target.value)}
            rows={3}
            autoFocus
            placeholder="El capítulo 3 se adelanta demasiado. Y la protagonista debería tener menos de cincuenta años."
            className="mt-1.5 w-full rounded-lg border border-borde-fuerte bg-panel-hoja px-3 py-2 text-sm text-tinta focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
          />
          <div className="mt-2 flex gap-3">
            <button
              type="button"
              disabled={enviando || cambios.trim() === ''}
              onClick={() => decidir('cambios')}
              className="rounded-md bg-acento px-3 py-1.5 text-sm font-medium text-papel-hoja disabled:opacity-40"
            >
              Mandar los cambios
            </button>
            <button
              type="button"
              onClick={() => setPidiendo(false)}
              className="rounded-md border border-borde-fuerte px-3 py-1.5 text-sm text-tinta-suave"
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            type="button"
            disabled={enviando}
            onClick={() => decidir('confirma')}
            className="rounded-md bg-aprobado px-4 py-2 text-sm font-medium text-papel-hoja disabled:opacity-40"
          >
            {enviando ? 'Enviando…' : 'Confirmar y escribir la novela'}
          </button>
          <button
            type="button"
            onClick={() => setPidiendo(true)}
            className="rounded-md border border-borde-fuerte bg-panel-hoja px-4 py-2 text-sm font-medium text-tinta"
          >
            Pedir cambios
          </button>
        </div>
      )}

      {error !== null && <p className="mt-3 text-sm text-rechazado">{error}</p>}
    </section>
  )
}

export function SesionEncargo({ slug, refrescando }: { slug: string; refrescando: boolean }) {
  const { eventos, estado, conectado } = useEventos(slug)
  const [texto, setTexto] = useState('')
  const [error, setError] = useState<string | null>(null)
  const finDelHilo = useRef<HTMLDivElement>(null)

  const encargo = useDatos<Encargo>((señal) => api.leerEncargo(slug, señal), `encargo:${slug}`, false)
  const novelas = useDatos<ResumenNovela[]>(
    (señal) => api.listarNovelas(señal),
    'novelas',
    refrescando,
  )

  // La novela que nació de este encargo, según estado.json del propio harness.
  const novela = novelas.datos?.find((n) => n.encargo === slug) ?? null
  const parada =
    novela?.ultimaParada !== null && novela?.ultimaParada !== undefined
      ? String(novela.ultimaParada)
      : ''
  const esperandoAprobacion = parada.includes('ESPERA_APROBACION')

  useEffect(() => {
    finDelHilo.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [eventos.length])

  async function mandar(intencion: Record<string, unknown>) {
    setError(null)
    try {
      await api.actuar(slug, intencion)
    } catch (causa) {
      setError(causa instanceof Error ? causa.message : 'No se ha podido hablar con el harness.')
    }
  }

  if (encargo.cargando && encargo.datos === null) return <Cargando que="el encargo" />
  if (encargo.error !== null && encargo.datos === null) {
    return <Fallo mensaje={encargo.error} alReintentar={encargo.recargar} />
  }
  if (encargo.datos === null) return null

  const puedeResponder = estado === 'esperando' || estado === 'parado'

  return (
    <div className="mx-auto max-w-3xl px-6 py-8">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-tinta">{encargo.datos.idea}</h1>
          <p className="mt-1 font-dato text-xs text-tinta-tenue">encargos/{slug}</p>
        </div>
        <span className="rounded-full border border-borde-fuerte px-2.5 py-0.5 text-xs text-tinta-suave">
          {ETIQUETA_ESTADO[estado]}
          {!conectado && ' · sin conexión'}
        </span>
      </header>

      {novela !== null && (
        <a
          href={escribirRuta({ vista: 'novela', slug: novela.slug, pestana: 'progreso', seleccion: null })}
          className="mt-4 flex items-center justify-between rounded-lg border border-borde bg-panel-hoja px-4 py-3 text-sm hover:border-borde-fuerte"
        >
          <span className="text-tinta">
            <strong className="font-medium">{novela.titulo}</strong>
            <span className="ml-2 text-tinta-tenue">
              {novela.capitulosAprobados}
              {novela.totalCapitulos !== null && ` de ${novela.totalCapitulos}`} capítulos
            </span>
          </span>
          <span className="text-marca-fuerte">Ver el progreso →</span>
        </a>
      )}

      {esperandoAprobacion && novela !== null && <div className="mt-4"><PanelPropuesta encargo={slug} novela={novela} /></div>}

      {estado === 'inactivo' && eventos.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-borde-fuerte bg-panel-hoja px-6 py-8 text-center">
          <p className="text-sm text-tinta">El encargo está guardado y nadie lo ha lanzado todavía.</p>
          <p className="mx-auto mt-1 max-w-prose text-sm text-tinta-tenue">
            Al empezar, el harness leerá tus respuestas y te preguntará lo que falte.
          </p>
          <button
            type="button"
            onClick={() => mandar({ tipo: 'empezar', idea: encargo.datos?.idea, ajustes: encargo.datos?.ajustes })}
            className="mt-4 rounded-md bg-acento px-4 py-2 text-sm font-medium text-papel-hoja"
          >
            Empezar el interrogatorio
          </button>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {eventos.map((evento, indice) => (
            <Burbuja key={`${evento.fecha}-${indice}`} evento={evento} />
          ))}
          {estado === 'trabajando' && (
            <p className="flex items-center gap-2 text-xs text-tinta-tenue">
              <span
                aria-hidden
                className="size-3 animate-spin rounded-full border-2 border-borde-fuerte border-t-marca"
              />
              El harness está trabajando…
            </p>
          )}
          <div ref={finDelHilo} />
        </div>
      )}

      {error !== null && (
        <p role="alert" className="mt-4 text-sm text-rechazado">
          {error}
        </p>
      )}

      {eventos.length > 0 && !esperandoAprobacion && (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            if (texto.trim() === '') return
            void mandar({ tipo: 'responder', texto })
            setTexto('')
          }}
          className="sticky bottom-0 mt-6 flex gap-2 border-t border-borde bg-panel/95 py-4 backdrop-blur"
        >
          <input
            type="text"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            disabled={!puedeResponder}
            placeholder={puedeResponder ? 'Tu respuesta…' : 'Espera a que termine el turno…'}
            className="flex-1 rounded-lg border border-borde-fuerte bg-panel-hoja px-3 py-2 text-sm text-tinta disabled:opacity-50 focus:border-marca focus:outline-2 focus:outline-offset-1 focus:outline-marca"
          />
          <button
            type="submit"
            disabled={!puedeResponder || texto.trim() === ''}
            className="rounded-md bg-acento px-4 py-2 text-sm font-medium text-papel-hoja disabled:opacity-40"
          >
            Enviar
          </button>
        </form>
      )}
    </div>
  )
}
