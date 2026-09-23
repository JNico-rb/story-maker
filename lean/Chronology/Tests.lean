import Chronology.Model

/-!
# Calendar checks

The rules of domain-knowledge.md §5.2 that the invariants rely on, checked with every build.
-/

namespace Chronology.Tests

open Chronology

-- A 29 February birthday falls on 1 March in common years, and on 29 February in leap years.
example : (Date.mk 2000 2 29).ageAt ⟨2001, 2, 28, 23, 59⟩ = 0 := by decide
example : (Date.mk 2000 2 29).ageAt ⟨2001, 3, 1, 0, 0⟩ = 1 := by decide
example : (Date.mk 2000 2 29).ageAt ⟨2004, 2, 28, 12, 0⟩ = 3 := by decide
example : (Date.mk 2000 2 29).ageAt ⟨2004, 2, 29, 0, 0⟩ = 4 := by decide

-- An age changes at 00:00 of the birthday.
example : (Date.mk 1990 6 15).ageAt ⟨2026, 6, 14, 23, 59⟩ = 35 := by decide
example : (Date.mk 1990 6 15).ageAt ⟨2026, 6, 15, 0, 0⟩ = 36 := by decide

-- Gregorian leap years.
example : isLeapYear 2000 = true := by decide
example : isLeapYear 1900 = false := by decide
example : isLeapYear 2024 = true := by decide
example : isLeapYear 2026 = false := by decide

-- Shifting the years by a multiple of 400, as the pseudonymisation does (ADR 0004), keeps ages.
example : (Date.mk 2400 2 29).ageAt ⟨2401, 3, 1, 0, 0⟩ = 1 := by decide
example : (Date.mk 2400 2 29).ageAt ⟨2401, 2, 28, 12, 0⟩ = 0 := by decide

-- The ordinal keeps the order of moments, and a birth is at 00:00.
example : (Moment.mk 2026 3 31 23 59).ordinal < (Moment.mk 2026 4 1 0 0).ordinal := by decide
example : (Moment.mk 2025 12 31 23 59).ordinal < (Moment.mk 2026 1 1 0 0).ordinal := by decide
example : (Date.mk 2026 3 10).midnight.ordinal = (Moment.mk 2026 3 10 0 0).ordinal := by decide

end Chronology.Tests
