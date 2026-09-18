// Tipos del dominio, con el vocabulario de specs/functional.md §0.
//
// Los términos de la spec se escriben aquí igual que allí (capitulo, intento,
// informe, veredicto, gravedad) para que buscar un tipo del código en la spec
// dé resultado. Lo que no es vocabulario del proyecto va en inglés, como es
// costumbre en React.

export type Etapa = 'interrogatorio' | 'capitulos' | 'final' | 'desconocida'

export type Veredicto = 'APROBADO' | 'RECHAZADO'

/** 1 contradice · 2 incumple escaleta · 3 longitud (harness) · 4 voz · 5 resumen infiel */
export type Gravedad = 1 | 2 | 3 | 4 | 5

export interface ResumenNovela {
  slug: string
  titulo: string
  etapa: Etapa
  modoPrueba: boolean
  /** Slug del encargo que la pidió, si vino del estudio (spec §9.4). */
  encargo: string | null
  perfil: string | null
  totalCapitulos: number | null
  capitulosAprobados: number
  aceptadosPorAgotamiento: number
  arcoActual: number | null
  capituloActual: number | null
  intentoActual: number | null
  completa: boolean
  ultimaParada: string | null
  avisos: string[]
  actualizado: string
}

export interface Problema {
  gravedad: Gravedad | null
  donde: string
  que: string
  porQue: string
}

export interface Informe {
  veredicto: Veredicto | null
  veredictoRevisor: Veredicto | null
  origen: 'revisor' | 'harness' | null
  problemas: Problema[]
  graves: number
  leves: number
  observaciones: string[]
  cuerpo: string
}

export interface Intento {
  numero: number
  capitulo: number
  palabras: number
  tieneResumen: boolean
  tieneLibroEstado: boolean
  informe: Informe | null
}

export interface IntentoConTexto extends Intento {
  texto: string
  resumen: string | null
}

export interface Capitulo {
  numero: number
  carpeta: string
  titulo: string | null
  arco: number | null
  objetivo: string | null
  sucesos: string[]
  personajes: string[]
  gancho: string | null
  palabrasObjetivo: number | null
  aprobado: number | null
  porAgotamiento: boolean
  intentos: Intento[]
}

export interface CapituloConTexto extends Omit<Capitulo, 'intentos'> {
  intentos: IntentoConTexto[]
}

export interface Arco {
  n: number
  desde: number | null
  hasta: number | null
  escaletaValidada: boolean
  tieneInforme: boolean
  titulo: string | null
  acto: string | null
  objetivo: string | null
  sucesosClave: string[]
  hilosAbre: string[]
  hilosCierra: string[]
  capitulosDetallados: number
}

export interface Documento {
  id: string
  titulo: string
  ruta: string
  palabras: number
}

export interface DocumentoConTexto extends Documento {
  cuerpo: string
}

export interface Registro {
  columnas: string[]
  filas: Array<Record<string, string | null>>
}

export interface Ajustes {
  proveedor: string | null
  palabrasPorCapitulo: number | null
  tolerancia: number | null
  reescriturasMax: number | null
  rechazaConGraves: number | null
  rechazaConLeves: number | null
  modelos: {
    interrogador: string | null
    escritor: string | null
    resumidor: string | null
    revisor: string | null
    escaladoActivo: boolean
  } | null
}

export interface Invocaciones {
  interrogador: number
  escritor: number
  resumidor: number
  revisor: number
}

/** Las métricas de §8.3 las calcula el harness; el visor no las recalcula (§9.2). */
export interface Metricas {
  disponibles: boolean
  cuerpo: string | null
}

export interface Novela extends ResumenNovela {
  idea: string | null
  ajustes: Ajustes | null
  invocaciones: Invocaciones | null
  arcos: Arco[]
  capitulos: Capitulo[]
  documentos: Documento[]
  registro: Registro
  metricas: Metricas
  manuscrito: { existe: boolean; palabras: number }
}

export interface CapituloLeido {
  numero: number
  titulo: string | null
  intento: number
  porAgotamiento: boolean
  palabras: number
  cuerpo: string
}

export interface Lectura {
  fuente: 'manuscrito' | 'capitulos'
  cuerpo: string | null
  capitulos: CapituloLeido[]
}

// ── El estudio (spec §9.4) ───────────────────────────────────────────────────
//
// Un encargo es lo que el usuario rellena antes de que exista la novela. Vive
// en encargos/<slug>/ y no en novelas/, que es del harness en exclusiva.

export interface Pregunta {
  id: string
  seccion: string
  texto: string
}

/** Estado del proceso del harness, tal como lo ve el servidor. */
export type EstadoSesion =
  | 'inactivo'
  | 'arrancando'
  | 'trabajando'
  | 'esperando'
  | 'parado'
  | 'parando'
  | 'fallado'

export interface Encargo {
  version: number
  slug: string
  creado: string
  idea: string
  ajustes: Record<string, string>
  novela?: string
  sesion: EstadoSesion
}

/** Lo que llega por el canal de eventos. `tipo` decide cómo se pinta. */
export interface EventoHarness {
  tipo:
    | 'hola'
    | 'estado'
    | 'asistente'
    | 'usuario'
    | 'herramienta'
    | 'turno_terminado'
    | 'fin_proceso'
    | 'aviso'
    | 'error'
    | 'crudo'
  fecha: string
  estado?: EstadoSesion
  texto?: string
  nombre?: string
  mensaje?: string
  motivo?: string
  codigo?: number | null
  novela?: string | null
}

export interface NuevoEncargo {
  idea: string
  respuestas: Record<string, string>
  ajustes: Record<string, string>
}
