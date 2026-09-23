import Chronology
import Input.Data

/-! A proof closed with `sorry`: the audit must reject it even without `--wfail`. -/

theorem seededSorry : Chronology.DeclaredOrder Input.chronology := by
  sorry

#assert_standard_axioms seededSorry
