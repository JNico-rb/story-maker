/-!
# The chronology of a novel

What the backend sends for one version of a novel (lean/README.md): the events, each with its
moment, its place, the characters present, where it is narrated and whom it excludes; and the
characters, with their birth dates. Identifiers are SQLite row ids, so no name reaches Lean.
-/

namespace Chronology

/-- A calendar date. -/
structure Date where
  year : Nat
  month : Nat
  day : Nat
  deriving Repr

/-- A calendar moment, to the minute. -/
structure Moment where
  year : Nat
  month : Nat
  day : Nat
  hour : Nat
  minute : Nat
  deriving Repr

/-- The moment as a point of the time line, in mixed radix. Two well-formed moments —month
1–12, day 1–31, hour 0–23, minute 0–59, which `scripts/generate.py` checks— compare as their
ordinals, so the order of events and "the same moment" are those of `Nat`. -/
def Moment.ordinal (m : Moment) : Nat :=
  (((m.year * 13 + m.month) * 32 + m.day) * 24 + m.hour) * 60 + m.minute

/-- 00:00 of the date: the moment of a birth (domain-knowledge.md §5.2). -/
def Date.midnight (d : Date) : Moment :=
  { year := d.year, month := d.month, day := d.day, hour := 0, minute := 0 }

/-- Leap years of the Gregorian calendar. -/
def isLeapYear (y : Nat) : Bool :=
  y % 4 == 0 && (y % 100 != 0 || y % 400 == 0)

/-- Month and day of the birthday in year `y`: a 29 February birthday falls on 1 March in
common years (domain-knowledge.md §5.2). -/
def Date.birthdayIn (d : Date) (y : Nat) : Nat × Nat :=
  if d.month = 2 ∧ d.day = 29 ∧ isLeapYear y = false then (3, 1) else (d.month, d.day)

/-- Whole years lived at `m` by someone born on `d`. Meaningful only when `m` is not before
the birth, which the invariants check first. -/
def Date.ageAt (d : Date) (m : Moment) : Nat :=
  let birthday := d.birthdayIn m.year
  if m.month < birthday.1 ∨ (m.month = birthday.1 ∧ m.day < birthday.2) then
    m.year - d.year - 1
  else
    m.year - d.year

/-- Where an event is narrated. -/
structure Position where
  chapter : Nat
  beat : Nat
  deriving Repr

/-- Narrative order: by chapter, then by beat. -/
def Position.before (p q : Position) : Bool :=
  decide (p.chapter < q.chapter) || (p.chapter == q.chapter && decide (p.beat < q.beat))

/-- The age a source fixes for a character at an event. -/
structure DeclaredAge where
  character : Nat
  age : Nat
  deriving Repr

/-- An event of the chronology. -/
structure Event where
  id : Nat
  moment : Moment
  /-- `none` when the event has no place. -/
  place : Option Nat
  /-- The characters present. -/
  present : List Nat
  /-- The chapter and beat that narrate it; `none` for the background. -/
  narration : Option Position
  /-- A flashback is narrated out of the order of time, so T1 leaves it out. -/
  flashback : Bool
  /-- The character an exclusion event removes from the story: their death or final departure. -/
  excluded : Option Nat
  /-- The ages the source fixes. -/
  ages : List DeclaredAge
  deriving Repr

/-- A character of the story bible. -/
structure Character where
  id : Nat
  /-- `none` when the story bible has no birth date: T2 then leaves the character out. -/
  birth : Option Date
  deriving Repr

/-- The elements of an optional value, to quantify over it as over a list. -/
def listOf {α : Type} : Option α → List α
  | none => []
  | some a => [a]

end Chronology

/-- The chronology of one version of a novel. -/
structure Chronology where
  characters : List Chronology.Character
  events : List Chronology.Event
  deriving Repr
