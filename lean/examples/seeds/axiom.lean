import Chronology
import Input.Data

/-! A proof resting on an axiom the file declares: the audit must reject it. -/

axiom seededCheat : False

theorem seededAxiom : Chronology.DeclaredOrder Input.chronology :=
  seededCheat.elim

#assert_standard_axioms seededAxiom
