import Chronology
import Input.Data

/-!
# The verification of `Input/Data.lean`

`scripts/generate.py` writes `Input/Data.lean` from the chronology JSON of lean/README.md. Each
theorem evaluates one invariant with `decide`, and the kernel checks that evaluation, so this
module compiles if and only if the four invariants hold. The audit then rejects any proof resting
on `sorry` or on an axiom beyond Lean's standard ones.
-/

namespace Input

set_option maxHeartbeats 4000000

theorem declaredOrder : Chronology.DeclaredOrder chronology := by
  decide +kernel

theorem ageCoherence : Chronology.AgeCoherence chronology := by
  decide +kernel

theorem singlePlace : Chronology.SinglePlace chronology := by
  decide +kernel

theorem noReturnAfterExclusion : Chronology.NoReturnAfterExclusion chronology := by
  decide +kernel

end Input

#assert_standard_axioms Input.declaredOrder
#assert_standard_axioms Input.ageCoherence
#assert_standard_axioms Input.singlePlace
#assert_standard_axioms Input.noReturnAfterExclusion
