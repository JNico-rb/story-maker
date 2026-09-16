// Progreso: dónde va el harness, arco a arco y capítulo a capítulo.

import { formatearDesviacion, formatearPalabras, medirLongitud } from '../lib/formato'
import { escribirRuta } from '../lib/ruta'
import type { Arco, Capitulo, Novela } from '../lib/tipos'
import { Markdown } from './Markdown'
import { Etiqueta } from './ui/Etiqueta'
import { Vacio } from './ui/Estados'

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="rounded-lg border border-borde bg-panel-hoja px-3 py-2.5">
      <dt className="text-xs text-tinta-tenue">{etiqueta}</dt>
      <dd className="mt-0.5 text-sm font-medium text-tinta">{valor}</dd>
    </div>
  )
}

function Cifras({ novela }: { novela: Novela }) {
  const invocaciones = novela.invocaciones
  const total =
    invocaciones === null
      ? null
      : invocaciones.interrogador + invocaciones.escritor + invocaciones.resumidor + invocaciones.revisor

  return (
    <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Dato
        etiqueta="Capítulos aprobados"
        valor={`${novela.capitulosAprobados}${novela.totalCapitulos !== null ? ` de ${novela.totalCapitulos}` : ''}`}
      />
      <Dato
        etiqueta="En curso"
        valor={
          novela.capituloActual === null
            ? '—'
            : `Capítulo ${novela.capituloActual}${novela.intentoActual !== null ? `, intento ${novela.intentoActual}` : ''}`
        }
      />
      <Dato
        etiqueta="Aceptados por agotamiento"
        valor={String(novela.aceptadosPorAgotamiento)}
      />
      <Dato etiqueta="Invocaciones a agentes" valor={total === null ? '—' : String(total)} />
    </dl>
  )
}

function FichaArco({ arco }: { arco: Arco }) {
  return (
    <section className="rounded-lg border border-borde bg-panel-hoja p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-semibold text-tinta">
          Arco {arco.n}
          {arco.titulo !== null && <span className="text-tinta-suave"> · {arco.titulo}</span>}
        </h3>
        {arco.desde !== null && arco.hasta !== null && (
          <Etiqueta>
            capítulos {arco.desde}–{arco.hasta}
          </Etiqueta>
        )}
        {arco.escaletaValidada ? (
          <Etiqueta tono="aprobado">escaleta validada</Etiqueta>
        ) : (
          <Etiqueta tono="aviso">escaleta sin validar</Etiqueta>
        )}
        {arco.tieneInforme && <Etiqueta tono="acento">con informe de arco</Etiqueta>}
      </div>

      {arco.objetivo !== null && <p className="mt-2 text-sm text-tinta-suave">{arco.objetivo}</p>}

      {(arco.hilosAbre.length > 0 || arco.hilosCierra.length > 0) && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          {arco.hilosAbre.length > 0 && (
            <div>
              <p className="text-xs font-medium text-tinta-tenue">Hilos que abre</p>
              <ul className="mt-1 space-y-0.5 text-sm text-tinta-suave">
                {arco.hilosAbre.map((hilo) => (
                  <li key={hilo}>· {hilo}</li>
                ))}
              </ul>
            </div>
          )}
          {arco.hilosCierra.length > 0 && (
            <div>
              <p className="text-xs font-medium text-tinta-tenue">Hilos que debe cerrar</p>
              <ul className="mt-1 space-y-0.5 text-sm text-tinta-suave">
                {arco.hilosCierra.map((hilo) => (
                  <li key={hilo}>· {hilo}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

function FilaCapitulo({
  capitulo,
  slug,
  tolerancia,
}: {
  capitulo: Capitulo
  slug: string
  tolerancia: number | null
}) {
  const aprobado = capitulo.aprobado !== null
  const ultimo = capitulo.intentos.at(-1) ?? null
  const medida =
    ultimo === null ? null : medirLongitud(ultimo.palabras, capitulo.palabrasObjetivo, tolerancia)

  return (
    <a
      href={escribirRuta({
        vista: 'novela',
        slug,
        pestana: 'progreso',
        seleccion: String(capitulo.numero),
      })}
      className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-borde px-4 py-3 transition last:border-b-0 hover:bg-panel"
    >
      <span className="w-8 shrink-0 font-dato text-sm text-tinta-tenue">
        {String(capitulo.numero).padStart(2, '0')}
      </span>

      <span className="min-w-40 flex-1 text-sm font-medium text-tinta">
        {capitulo.titulo ?? <span className="text-tinta-tenue">Sin título en la escaleta</span>}
      </span>

      <span className="flex items-center gap-1.5">
        {capitulo.intentos.map((intento) => {
          const veredicto = intento.informe?.veredicto ?? null
          const tono =
            veredicto === 'APROBADO' ? 'aprobado' : veredicto === 'RECHAZADO' ? 'rechazado' : 'neutro'
          return (
            <Etiqueta
              key={intento.numero}
              tono={tono}
              titulo={
                veredicto === null
                  ? `Intento ${intento.numero}: sin informe todavía`
                  : `Intento ${intento.numero}: ${veredicto}`
              }
            >
              {intento.numero}
            </Etiqueta>
          )
        })}
      </span>

      {medida !== null && (
        <span
          className={`w-36 shrink-0 text-right font-dato text-xs ${medida.dentro ? 'text-tinta-tenue' : 'text-rechazado'}`}
          title={`Objetivo ${medida.objetivo} palabras, margen ${medida.minimo}–${medida.maximo}`}
        >
          {formatearPalabras(medida.palabras)} ({formatearDesviacion(medida.desviacion)})
        </span>
      )}

      <span className="w-28 shrink-0 text-right">
        {aprobado ? (
          capitulo.porAgotamiento ? (
            <Etiqueta tono="aviso" titulo="Se agotaron las reescrituras y se aceptó el mejor intento">
              por agotamiento
            </Etiqueta>
          ) : (
            <Etiqueta tono="aprobado">aprobado</Etiqueta>
          )
        ) : (
          <Etiqueta tono="acento">en curso</Etiqueta>
        )}
      </span>
    </a>
  )
}

function Metricas({ novela }: { novela: Novela }) {
  if (!novela.metricas.disponibles || novela.metricas.cuerpo === null) {
    return (
      <section className="rounded-lg border border-dashed border-borde-fuerte bg-panel-hoja p-4">
        <h3 className="text-sm font-semibold text-tinta">Métricas de calidad</h3>
        <p className="mt-1.5 max-w-prose text-sm text-tinta-tenue">
          Todavía no las hay. Las calcula el harness al terminar la novela y las escribe en{' '}
          <code className="font-dato">informe-cierre.md</code>. El visor no las calcula por su
          cuenta, para que no pueda haber dos cifras distintas para la misma novela.
        </p>
      </section>
    )
  }

  return (
    <section className="rounded-lg border border-borde bg-panel-hoja p-5">
      <h3 className="mb-1 text-sm font-semibold text-tinta">
        Informe de cierre <span className="font-normal text-tinta-tenue">— lo escribió el harness</span>
      </h3>
      <Markdown texto={novela.metricas.cuerpo} />
    </section>
  )
}

export function PestanaProgreso({ novela }: { novela: Novela }) {
  const tolerancia = novela.ajustes?.tolerancia ?? null

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-8">
      <Cifras novela={novela} />

      {novela.avisos.length > 0 && (
        <section className="rounded-lg border border-aviso/25 bg-aviso-fondo p-4">
          <h3 className="text-sm font-semibold text-aviso">Avisos del harness</h3>
          <ul className="mt-2 space-y-1 text-sm text-tinta-suave">
            {novela.avisos.map((aviso, i) => (
              <li key={i}>· {aviso}</li>
            ))}
          </ul>
        </section>
      )}

      {novela.ultimaParada !== null && (
        <section className="rounded-lg border border-rechazado/25 bg-rechazado-fondo p-4">
          <h3 className="text-sm font-semibold text-rechazado">Última parada</h3>
          <p className="mt-1 text-sm text-tinta-suave">{novela.ultimaParada}</p>
        </section>
      )}

      {novela.arcos.map((arco) => (
        <FichaArco key={arco.n} arco={arco} />
      ))}

      <section>
        <h3 className="mb-2 text-sm font-semibold text-tinta">Capítulos</h3>
        {novela.capitulos.length === 0 ? (
          <Vacio titulo="Aún no se ha escrito ningún capítulo" />
        ) : (
          <div className="overflow-hidden rounded-lg border border-borde bg-panel-hoja">
            {novela.capitulos.map((capitulo) => (
              <FilaCapitulo
                key={capitulo.numero}
                capitulo={capitulo}
                slug={novela.slug}
                tolerancia={tolerancia}
              />
            ))}
          </div>
        )}
      </section>

      <Metricas novela={novela} />
    </div>
  )
}
