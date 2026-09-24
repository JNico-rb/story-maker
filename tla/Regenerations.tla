---------------------------- MODULE Regenerations ----------------------------
(***************************************************************************)
(* Concurrencia entre dos cambios confirmados sobre la misma novela       *)
(* (architecture.md §10.2; spec 006, C5): cola global FIFO, una ejecución *)
(* en curso como mucho, versión base y revalidación al arrancar y al      *)
(* relanzarse tras Reanudar (§9.2). Solo usa nombres de acción de         *)
(* Harness.tla; el interior de cada ejecución (fases, intentos) es de     *)
(* Harness.tla y aquí se resume en Publicar o Fallar.                     *)
(*                                                                         *)
(* Defecto = 0 en la config que pasa; 6 activa el defecto sembrado de su  *)
(* config de control (C6): Regenerar no revalida la base.                 *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS NumCambios,  \* cambios del modelo
          MaxResumes,  \* reanudaciones por ejecución
          Defecto      \* 0: ninguno; 6: control de C6

ASSUME NumCambios \in Nat \ {0}
ASSUME MaxResumes \in Nat
ASSUME Defecto \in {0, 6}

VARIABLES ej,          \* [Cambios -> ejecución del cambio]
          solicitud,   \* [Cambios -> estado del cambio]
          publicadas,  \* secuencia de versiones: [base, por]
          reloj        \* siguiente fecha de creación

vars == <<ej, solicitud, publicadas, reloj>>

Cambios == 1..NumCambios
Pendientes == {"queued", "running", "interrupted"}
Vigente == Len(publicadas)

Init ==
  /\ ej = [c \in Cambios |-> [estado |-> "none", base |-> 0,
                               creada |-> 0, reanudaciones |-> 0]]
  /\ solicitud = [c \in Cambios |-> "none"]
  /\ publicadas = <<[base |-> 0, por |-> 0]>>  \* la versión 1, ya vigente
  /\ reloj = 1

NingunaEnCurso == \A c \in Cambios : ej[c].estado # "running"

(* La primera de la cola por fecha de creación.                           *)
Primera(c) ==
  /\ ej[c].estado = "queued"
  /\ \A d \in Cambios : ej[d].estado = "queued" => ej[c].creada <= ej[d].creada

PedirCambio(c) ==
  /\ solicitud[c] = "none"
  /\ solicitud' = [solicitud EXCEPT ![c] = "confirmed"]
  /\ ej' = [ej EXCEPT ![c].estado = "queued", ![c].base = Vigente,
                      ![c].creada = reloj]
  /\ reloj' = reloj + 1
  /\ UNCHANGED publicadas

Regenerar(c) ==
  /\ NingunaEnCurso
  /\ Primera(c)
  /\ ej[c].base = Vigente \/ Defecto = 6
  /\ ej' = [ej EXCEPT ![c].estado = "running"]
  /\ UNCHANGED <<solicitud, publicadas, reloj>>

Fallar(c) ==
  /\ \/ \* (a) stale_base, al arrancar o al relanzarse
        /\ NingunaEnCurso /\ Primera(c) /\ ej[c].base # Vigente
     \/ \* (b) cualquier fallo del bucle
        ej[c].estado = "running"
     \/ \* (c) cae en curso con las reanudaciones agotadas
        /\ ej[c].estado = "running" /\ ej[c].reanudaciones = MaxResumes
  /\ ej' = [ej EXCEPT ![c].estado = "failed"]
  /\ solicitud' = [solicitud EXCEPT ![c] = "rejected"]
  /\ UNCHANGED <<publicadas, reloj>>

Publicar(c) ==
  /\ ej[c].estado = "running"
  /\ publicadas' = Append(publicadas, [base |-> ej[c].base, por |-> c])
  /\ ej' = [ej EXCEPT ![c].estado = "published"]
  /\ solicitud' = [solicitud EXCEPT ![c] = "applied"]
  /\ UNCHANGED reloj

Caer(c) ==
  /\ ej[c].estado = "running"
  /\ ej[c].reanudaciones < MaxResumes
  /\ ej' = [ej EXCEPT ![c].estado = "interrupted"]
  /\ UNCHANGED <<solicitud, publicadas, reloj>>

(* Vuelve a la cola en su puesto original: conserva su fecha de creación. *)
Reanudar(c) ==
  /\ ej[c].estado = "interrupted"
  /\ ej' = [ej EXCEPT ![c].estado = "queued",
                      ![c].reanudaciones = ej[c].reanudaciones + 1]
  /\ UNCHANGED <<solicitud, publicadas, reloj>>

Next ==
  \E c \in Cambios :
    \/ PedirCambio(c) \/ Regenerar(c) \/ Fallar(c)
    \/ Publicar(c) \/ Caer(c) \/ Reanudar(c)

Spec == Init /\ [][Next]_vars

(* I6: la historia de versiones es lineal y ningún cambio confirmado se   *)
(* pierde: está pendiente, aplicado (y su ejecución publicó) o rechazado  *)
(* (y su ejecución falló).                                                *)
VersionesLineales ==
  /\ \A n \in 2..Len(publicadas) : publicadas[n].base = n - 1
  /\ \A c \in Cambios :
       \/ solicitud[c] = "none" /\ ej[c].estado = "none"
       \/ solicitud[c] = "confirmed" /\ ej[c].estado \in Pendientes
       \/ /\ solicitud[c] = "applied" /\ ej[c].estado = "published"
          /\ \E n \in 2..Len(publicadas) : publicadas[n].por = c
       \/ solicitud[c] = "rejected" /\ ej[c].estado = "failed"
  /\ \A n \in 2..Len(publicadas) : ej[publicadas[n].por].estado = "published"

=============================================================================
