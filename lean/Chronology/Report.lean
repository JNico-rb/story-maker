import Chronology.Invariants

/-!
# The report of a verification, as JSON

`scripts/Report.lean` prints it for `Input/Data.lean`, and `scripts/verify.py` joins it with the
verdict of `Input/Proofs.lean` into the result JSON of lean/README.md.
-/

namespace Chronology

/-- The invariants in the order the result lists them, each with its criterion id (spec 009). -/
def checks : List (String × (Chronology → Option Witness)) :=
  [("t1-orden", DeclaredOrder.witness?),
   ("t2-edad", AgeCoherence.witness?),
   ("t3-dos-lugares", SinglePlace.witness?),
   ("t4-excluyente", NoReturnAfterExclusion.witness?)]

/-- A JSON array of numbers. -/
def natsJson (ns : List Nat) : String :=
  "[" ++ ", ".intercalate (ns.map toString) ++ "]"

/-- The witness as a JSON object. -/
def Witness.json (w : Witness) : String :=
  "{\"events\": " ++ natsJson w.events ++ ", \"characters\": " ++ natsJson w.characters ++ "}"

/-- One invariant: whether it holds and, if not, its first witness. -/
def entryJson (id : String) : Option Witness → String
  | none => "{\"invariant\": \"" ++ id ++ "\", \"holds\": true, \"witness\": null}"
  | some w => "{\"invariant\": \"" ++ id ++ "\", \"holds\": false, \"witness\": " ++ w.json ++ "}"

/-- Every invariant of `c`, in order, as a JSON array. -/
def reportJson (c : Chronology) : String :=
  "[" ++ ", ".intercalate (checks.map (fun check => entryJson check.1 (check.2 c))) ++ "]"

end Chronology
