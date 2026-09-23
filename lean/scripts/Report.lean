import Chronology.Report
import Input.Data

/-! Prints each invariant of the chronology in `Input/Data.lean` with its first witness. -/

def main : IO Unit :=
  IO.println (Chronology.reportJson Input.chronology)
