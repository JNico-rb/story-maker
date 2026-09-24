------------------------------- MODULE Harness -------------------------------
(***************************************************************************)
(* La máquina de estados de una Ejecucion (architecture.md §9.1), con los *)
(* límites de §7.6, el punto de control y la reanudación de §9.2, las     *)
(* versiones de §9.3, el gate y la reescritura dirigida de §9.4, y el     *)
(* cambio del lector y la edición manual de §10.1 y §10.3 (spec 006, C4). *)
(*                                                                         *)
(* Dos ejecuciones como mucho: la generation (1) y el único cambio del    *)
(* modelo (2), que es una change_request o una manual_edit.               *)
(*                                                                         *)
(* No determinista: lo que decide un modelo o el entorno (si Validar pasa,*)
(* a qué capítulos atribuye el gate su fallo, qué capítulos afecta el     *)
(* cambio y cuál se edita, el tipo del cambio y cuándo se pide, cuándo    *)
(* cae la ejecución). Guarda determinista: lo que decide el código.       *)
(*                                                                         *)
(* Defecto = 0 en la config que pasa; 1..5 activa el defecto sembrado de  *)
(* la config de control de esa fila (spec 006, C6). Los defectos son      *)
(* internos de la verificación, no propiedades del harness.               *)
(***************************************************************************)
EXTENDS Integers, Sequences

CONSTANTS NumCapitulos,       \* capítulos de la novela del modelo
          MaxRetriesPlan,     \* max_retries.plan
          MaxRetriesChapter,  \* max_retries.chapter
          MaxRetriesGate,     \* max_retries.gate_cycles
          MaxResumes,         \* max_resumes
          Defecto             \* 0: ninguno; 1..5: control de C6

ASSUME NumCapitulos \in Nat \ {0}
ASSUME {MaxRetriesPlan, MaxRetriesChapter, MaxRetriesGate, MaxResumes} \subseteq Nat
ASSUME Defecto \in 0..5

VARIABLES ej,          \* [Ejecuciones -> registro de la ejecución]
          publicadas,  \* secuencia de versiones publicadas; la i es la versión i
          solicitud    \* estado de la SolicitudDeCambio o la EdicionManual

vars == <<ej, publicadas, solicitud>>

Capitulos == 1..NumCapitulos
Gen == 1
Cambio == 2
Ejecuciones == {Gen, Cambio}
Terminales == {"published", "failed"}

(* Contenido de un capítulo en una candidata o una versión: 0 vacío,     *)
(* EDITADO el texto de una persona aún sin juzgar, r el que aceptó        *)
(* Validar en la ejecución r.                                             *)
EDITADO == -1
Vacia == [c \in Capitulos |-> 0]

Min(S) == CHOOSE x \in S : \A y \in S : x <= y
RECURSIVE Ordenada(_)
Ordenada(S) == IF S = {} THEN <<>> ELSE <<Min(S)>> \o Ordenada(S \ {Min(S)})
Rango(s) == {s[i] : i \in DOMAIN s}

(* Registro de una ejecución.                                             *)
(*  secuencia: generation <<0,1..N>> (0 = el plan); change_request, los   *)
(*    afectados en orden; manual_edit, el editado y después los demás.    *)
(*  cursor: posición de la secuencia en planning y writing.              *)
(*  cps: puntos de control, solo inserción.                               *)
(*  intentos: los del evaluable en curso (plan, capítulo de la secuencia *)
(*    o capítulo atribuido en este ciclo); ciclos: los del ciclo del gate,*)
(*    que solo cuenta los fallidos (§9.4).                                *)
(*  superado: gate superado sobre la candidata tras su última aceptación.*)
(*  Los de un evaluable ya aceptado no vuelven a cambiar, así que acotar *)
(*  el evaluable en curso acota todos.                                    *)
EjInicial == [estado |-> "none", tipo |-> "none", fase |-> "none",
              secuencia |-> <<>>, cursor |-> 0, cps |-> <<>>,
              pendiente |-> FALSE, defectos |-> FALSE,
              intentos |-> 0, ciclos |-> 0, superado |-> FALSE,
              atribuidos |-> {}, reanudaciones |-> 0, arrancada |-> FALSE,
              candidata |-> Vacia, base |-> 0]

Init == /\ ej = [r \in Ejecuciones |-> EjInicial]
        /\ publicadas = <<>>
        /\ solicitud = "none"

MaxRet(fase) == CASE fase = "planning" -> MaxRetriesPlan
                  [] fase \in {"writing", "rewriting"} -> MaxRetriesChapter
                  [] OTHER -> 0

EnCurso(r) == ej[r].estado = "running"
NingunaEnCurso == \A r \in Ejecuciones : ~EnCurso(r)

(* El capítulo en curso es el editado a mano: el primero de su secuencia. *)
EsEditado(r) == /\ ej[r].tipo = "manual_edit"
                /\ ej[r].fase = "writing"
                /\ ej[r].cursor = 1
Editado(r) == IF ej[r].tipo = "manual_edit" THEN ej[r].secuencia[1] ELSE 0

(* Aceptar el capítulo c escribe en la candidata; con el defecto 3, un    *)
(* cambio escribe además sobre su versión base, que no copió.            *)
PubTrasAceptar(r, c) ==
  IF Defecto = 3 /\ r = Cambio
  THEN [publicadas EXCEPT ![ej[r].base].caps[c] = r]
  ELSE publicadas

(* Una ejecución terminada ya no cambia: el modelo olvida lo que solo     *)
(* servía para llevarla (contadores, fase, candidata, ya publicada o      *)
(* descartada) y conserva lo que leen las propiedades. Sin esto, cada     *)
(* final de la generation multiplica el espacio del cambio.               *)
Cerrada(e, estado) ==
  [e EXCEPT !.estado = estado, !.fase = "none", !.cursor = 0,
            !.pendiente = FALSE, !.defectos = FALSE, !.intentos = 0,
            !.ciclos = 0, !.superado = FALSE, !.atribuidos = {},
            !.reanudaciones = 0, !.candidata = Vacia]

(* Relanzar una ejecución reanudada: sigue en la fase siguiente al último *)
(* punto de control, o vuelve al gate (§9.2). Con el defecto 2 se salta   *)
(* un elemento de la secuencia.                                          *)
Relanzar(r) ==
  LET e == ej[r]
      k == Len(e.cps)
      cur == k + 1 + (IF Defecto = 2 /\ k > 0 THEN 1 ELSE 0)
      alGate == e.fase \in {"gate", "rewriting"} \/ cur > Len(e.secuencia)
  IN ej' = [ej EXCEPT
              ![r].estado = "running",
              ![r].fase = IF alGate THEN "gate"
                          ELSE IF e.secuencia[cur] = 0 THEN "planning"
                          ELSE "writing",
              ![r].cursor = IF alGate THEN e.cursor ELSE cur,
              ![r].superado = FALSE,
              ![r].atribuidos = {},
              \* el veredicto del gate que falló se conserva; el de un
              \* capítulo de rewriting se abandona con su ciclo
              ![r].defectos = IF alGate THEN e.defectos /\ e.fase = "gate"
                              ELSE e.defectos,
              ![r].intentos = IF alGate THEN 0 ELSE e.intentos]

(***************************************************************************)
(* Acciones (C4)                                                           *)
(***************************************************************************)

Configurar ==
  /\ ej[Gen].estado = "none"
  /\ ej' = [ej EXCEPT ![Gen].estado = "queued",
                      ![Gen].tipo = "generation",
                      ![Gen].secuencia = <<0>> \o Ordenada(Capitulos),
                      ![Gen].candidata = Vacia]
  /\ UNCHANGED <<publicadas, solicitud>>

Planificar(r) ==
  /\ ej[r].tipo = "generation"
  /\ ej[r].estado = "queued"
  /\ NingunaEnCurso
  /\ IF ~ej[r].arrancada
     THEN ej' = [ej EXCEPT ![r].estado = "running", ![r].fase = "planning",
                           ![r].cursor = 1, ![r].arrancada = TRUE]
     ELSE Relanzar(r)
  /\ UNCHANGED <<publicadas, solicitud>>

Regenerar(r) ==
  /\ ej[r].tipo \in {"change_request", "manual_edit"}
  /\ ej[r].estado = "queued"
  /\ NingunaEnCurso
  /\ ej[r].base = Len(publicadas)  \* revalida la base (la obsoleta es de Regenerations.tla)
  /\ IF ~ej[r].arrancada
     THEN ej' = [ej EXCEPT
                   ![r].estado = "running", ![r].fase = "writing",
                   ![r].cursor = 1, ![r].arrancada = TRUE,
                   ![r].candidata =
                     [c \in Capitulos |->
                        IF ej[r].tipo = "manual_edit" /\ c = ej[r].secuencia[1]
                        THEN EDITADO
                        ELSE publicadas[ej[r].base].caps[c]]]
     ELSE Relanzar(r)
  /\ UNCHANGED <<publicadas, solicitud>>

EscribirCapitulo(r) ==
  LET e == ej[r] IN
  /\ EnCurso(r)
  /\ \/ e.fase = "writing" /\ e.cursor <= Len(e.secuencia)
     \/ e.fase = "rewriting" /\ e.atribuidos # {}
  /\ ~e.pendiente
  /\ ~e.defectos
  /\ ~EsEditado(r)
  /\ ej' = [ej EXCEPT ![r].pendiente = TRUE]
  /\ UNCHANGED <<publicadas, solicitud>>

Validar(r) ==
  LET e == ej[r] IN
  /\ EnCurso(r)
  /\ \/ \* plan o capítulo de la secuencia
        /\ e.fase \in {"planning", "writing"}
        /\ e.cursor <= Len(e.secuencia)
        /\ ~e.defectos
        /\ e.pendiente \/ e.fase = "planning" \/ EsEditado(r)
        /\ LET c == e.secuencia[e.cursor] IN
           \/ \* pasa: plan aplicado o capítulo aceptado, con su punto de control
              /\ ej' = [ej EXCEPT
                          ![r].intentos = 0, ![r].pendiente = FALSE,
                          ![r].cps = Append(e.cps, c),
                          ![r].cursor = e.cursor + 1,
                          ![r].fase = "writing",
                          ![r].superado = FALSE,
                          ![r].candidata = IF c = 0 THEN e.candidata
                                           ELSE [e.candidata EXCEPT ![c] = r]]
              /\ publicadas' = IF c = 0 THEN publicadas ELSE PubTrasAceptar(r, c)
           \/ \* falla: la entrega se descarta y quedan defectos
              /\ ej' = [ej EXCEPT ![r].intentos = e.intentos + 1,
                                  ![r].pendiente = FALSE, ![r].defectos = TRUE]
              /\ UNCHANGED publicadas
     \/ \* capítulo atribuido en rewriting: sin punto de control (§8.3)
        /\ e.fase = "rewriting"
        /\ e.pendiente
        /\ LET c == Min(e.atribuidos) IN
           \/ /\ ej' = [ej EXCEPT
                          ![r].intentos = 0, ![r].pendiente = FALSE,
                          ![r].atribuidos = e.atribuidos \ {c},
                          ![r].superado = FALSE,
                          ![r].candidata = [e.candidata EXCEPT ![c] = r]]
              /\ publicadas' = PubTrasAceptar(r, c)
           \/ /\ ej' = [ej EXCEPT ![r].intentos = e.intentos + 1,
                                  ![r].pendiente = FALSE, ![r].defectos = TRUE]
              /\ UNCHANGED publicadas
     \/ \* una pasada del gate
        /\ e.fase = "gate"
        /\ ~e.superado
        /\ ~e.defectos
        \* Solo un ciclo fallido es un intento del ciclo del gate (§9.4):
        \* contar también la pasada que supera el gate deja superar
        \* 1 + max_retries.gate_cycles al volver a pasarlo tras una caída
        \* (contraejemplo de TLC, spec 006 C10).
        /\ \/ ej' = [ej EXCEPT ![r].superado = TRUE]
           \/ \E S \in SUBSET Capitulos :
                IF /\ S # {}
                   /\ e.ciclos + 1 < 1 + MaxRetriesGate
                   /\ Editado(r) \notin S
                THEN ej' = [ej EXCEPT ![r].ciclos = e.ciclos + 1,
                                      ![r].fase = "rewriting",
                                      ![r].atribuidos = S, ![r].intentos = 0]
                ELSE ej' = [ej EXCEPT ![r].ciclos = e.ciclos + 1,
                                      ![r].defectos = TRUE]
        /\ UNCHANGED publicadas
  /\ UNCHANGED solicitud

Reintentar(r) ==
  LET e == ej[r] IN
  /\ EnCurso(r)
  /\ \/ /\ e.defectos
        /\ e.fase \in {"planning", "writing", "rewriting"}
        /\ ~EsEditado(r)
        /\ e.intentos < 1 + MaxRet(e.fase) + (IF Defecto = 4 THEN 1 ELSE 0)
        /\ ej' = [ej EXCEPT ![r].defectos = FALSE]
     \/ \* todos los atribuidos vueltos a aceptar: ciclo nuevo del gate
        /\ e.fase = "rewriting"
        /\ e.atribuidos = {}
        /\ ej' = [ej EXCEPT ![r].fase = "gate"]
  /\ UNCHANGED <<publicadas, solicitud>>

Gate(r) ==
  /\ EnCurso(r)
  /\ ej[r].fase = "writing"
  /\ ej[r].cursor > Len(ej[r].secuencia)
  /\ ej' = [ej EXCEPT ![r].fase = "gate"]
  /\ UNCHANGED <<publicadas, solicitud>>

Publicar(r) ==
  /\ EnCurso(r)
  /\ ej[r].fase = "gate"
  /\ ej[r].superado \/ Defecto = 1
  /\ publicadas' = Append(publicadas, [caps |-> ej[r].candidata,
                                       gate |-> ej[r].superado,
                                       por |-> r])
  /\ ej' = [ej EXCEPT ![r] = Cerrada(ej[r], "published")]
  /\ solicitud' = IF r = Cambio THEN "applied" ELSE solicitud

(* Ramas (a), (b) y (c) de Fallar: las del bucle, que son del sistema.    *)
FallarEnBucle(r) ==
  LET e == ej[r] IN
  /\ EnCurso(r)
  /\ e.defectos
  /\ \/ e.fase \in {"planning", "writing", "rewriting"}
        /\ (e.intentos >= 1 + MaxRet(e.fase) \/ EsEditado(r))
     \/ e.fase = "gate"

(* Rama (d): una caída con max_resumes agotado; es del entorno.           *)
FallarPorCaida(r) ==
  /\ EnCurso(r)
  /\ ej[r].reanudaciones = MaxResumes
  /\ Defecto # 5

Fallar(r) ==
  /\ FallarEnBucle(r) \/ FallarPorCaida(r)
  /\ ej' = [ej EXCEPT ![r] = Cerrada(ej[r], "failed")]  \* la candidata se descarta
  /\ solicitud' = IF r = Cambio THEN "rejected" ELSE solicitud
  /\ UNCHANGED publicadas

Caer(r) ==
  /\ EnCurso(r)
  /\ ej[r].reanudaciones < MaxResumes \/ Defecto = 5
  /\ ej' = [ej EXCEPT ![r].estado = "interrupted", ![r].pendiente = FALSE]
  /\ UNCHANGED <<publicadas, solicitud>>

Reanudar(r) ==
  /\ ej[r].estado = "interrupted"
  /\ ej[r].reanudaciones < MaxResumes  \* como mucho max_resumes veces (§9.2)
  /\ ej' = [ej EXCEPT ![r].estado = "queued",
                      ![r].reanudaciones = ej[r].reanudaciones + 1]
  /\ UNCHANGED <<publicadas, solicitud>>

PedirCambio ==
  /\ Len(publicadas) > 0
  /\ \A r \in Ejecuciones : ej[r].estado \in {"none"} \cup Terminales
  /\ ej[Cambio].estado = "none"
  /\ \E tipo \in {"change_request", "manual_edit"}, e \in Capitulos,
        A \in SUBSET Capitulos :
       LET sec == IF tipo = "change_request" THEN Ordenada(A)
                  ELSE <<e>> \o Ordenada(A \ {e})
       IN /\ tipo = "change_request" => A # {} /\ e = 1  \* e solo cuenta en manual_edit
          /\ ej' = [ej EXCEPT ![Cambio].estado = "queued",
                              ![Cambio].tipo = tipo,
                              ![Cambio].secuencia = sec,
                              ![Cambio].base = Len(publicadas)]
  /\ solicitud' = "confirmed"
  /\ UNCHANGED publicadas

Next ==
  \/ Configurar
  \/ PedirCambio
  \/ \E r \in Ejecuciones :
       \/ Planificar(r) \/ Regenerar(r) \/ EscribirCapitulo(r) \/ Validar(r)
       \/ Reintentar(r) \/ Gate(r) \/ Publicar(r) \/ Fallar(r)
       \/ Caer(r) \/ Reanudar(r)

(* Equidad débil de las acciones del sistema y de Reanudar (§11.5); no de *)
(* Configurar, PedirCambio ni las caídas, que son del entorno.            *)
Equidad ==
  \A r \in Ejecuciones :
    /\ WF_vars(Planificar(r)) /\ WF_vars(Regenerar(r))
    /\ WF_vars(EscribirCapitulo(r)) /\ WF_vars(Validar(r))
    /\ WF_vars(Reintentar(r)) /\ WF_vars(Gate(r)) /\ WF_vars(Publicar(r))
    /\ WF_vars(FallarEnBucle(r) /\ Fallar(r))
    /\ WF_vars(Reanudar(r))

Spec == Init /\ [][Next]_vars /\ Equidad

(***************************************************************************)
(* Propiedades (§11.5; spec 006, I1-I5)                                    *)
(***************************************************************************)

(* I1: cada versión publicada tuvo el gate superado sobre su candidata    *)
(* tras su última aceptación, y cada capítulo lo aceptó Validar: en esa   *)
(* ejecución o, si no era de los afectados, en la versión base.           *)
NuncaPublicaSinValidar ==
  \A i \in 1..Len(publicadas) :
    LET v == publicadas[i]
        e == ej[v.por]
    IN /\ v.gate
       /\ \A c \in Capitulos :
            /\ v.caps[c] \in Ejecuciones
            /\ \/ v.caps[c] = v.por  \* de la secuencia o reescrito en el gate
               \/ /\ c \notin Rango(e.secuencia)
                  /\ e.base \in 1..Len(publicadas)
                  /\ v.caps[c] = publicadas[e.base].caps[c]

(* I2: los puntos de control son el prefijo de la secuencia hasta k, y en *)
(* planning o writing el elemento en curso es el siguiente al último.     *)
ReanudacionSinDuplicarNiPerder ==
  \A r \in Ejecuciones :
    LET e == ej[r] IN
    /\ Len(e.cps) <= Len(e.secuencia)
    /\ e.cps = SubSeq(e.secuencia, 1, Len(e.cps))
    /\ (EnCurso(r) /\ e.fase \in {"planning", "writing"})
         => e.cursor = Len(e.cps) + 1

(* I3: ningún paso cambia ni quita una versión ya publicada.              *)
VersionAnteriorConservada ==
  [][ /\ Len(publicadas') >= Len(publicadas)
      /\ \A i \in 1..Len(publicadas) : publicadas'[i] = publicadas[i] ]_publicadas

(* I4: intentos por evaluable <= 1 + max_retries; reanudaciones <=        *)
(* max_resumes.                                                           *)
ReintentosAcotados ==
  \A r \in Ejecuciones :
    /\ ej[r].intentos <= 1 + MaxRet(ej[r].fase)
    /\ ej[r].ciclos <= 1 + MaxRetriesGate
    /\ ej[r].reanudaciones <= MaxResumes

(* I5: toda ejecución creada acaba en published o failed.                 *)
TerminaSiempre ==
  \A r \in Ejecuciones : (ej[r].estado # "none") ~> (ej[r].estado \in Terminales)

=============================================================================
