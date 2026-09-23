import Lean

/-!
# The axiom audit

`sorry` only warns, so a proof closed with it would pass a plain `lake build`. `--wfail` turns the
warning into a failure, and this audit rejects it again at the level of the proof term, together
with any axiom a file could declare.
-/

open Lean Elab Command

namespace Chronology

/-- The axioms of Lean's own library. -/
def standardAxioms : List Name := [``propext, ``Classical.choice, ``Quot.sound]

/-- `#assert_standard_axioms thm` fails unless the proof of `thm` rests only on
`standardAxioms`: `sorryAx`, or an axiom declared outside Lean's library, fails it. -/
elab "#assert_standard_axioms " thm:ident : command => do
  let name := thm.getId
  unless (← getEnv).contains name do
    throwErrorAt thm m!"unknown declaration '{name}'"
  let axioms ← liftCoreM (collectAxioms name)
  for ax in axioms do
    unless standardAxioms.contains ax do
      throwErrorAt thm m!"'{name}' depends on '{ax}', which is not a standard axiom"
  logInfoAt thm m!"'{name}' depends only on standard axioms: {axioms.toList}"

end Chronology
