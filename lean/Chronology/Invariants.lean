import Chronology.Model

/-!
# The four invariants of the chronology

T1–T4 of domain-knowledge.md §5.3, with T5 inside T2, as the V1 delivery groups them. Each is a
proposition whose quantifiers are all bounded by lists of the chronology, so it is decidable, and
`decide` evaluates it on a generated file (`Input/Proofs.lean`). Next to each, the search for its
first witness in the order of the event list. The witness only feeds the result JSON: the verdict
is the theorem.
-/

namespace Chronology

/-- The events and characters that show an invariant broken. -/
structure Witness where
  events : List Nat
  characters : List Nat
  deriving Repr

/-- `a` is narrated before `b`, by chapter and beat, and neither is a flashback. -/
def Event.narratedBefore (a b : Event) : Bool :=
  match a.narration, b.narration with
  | some p, some q => !a.flashback && !b.flashback && p.before q
  | _, _ => false

/-- **T1 · Declared temporal order.** The narrated events that are not flashbacks advance in the
order of chapters and beats: none is earlier than one narrated before it. -/
abbrev DeclaredOrder (c : Chronology) : Prop :=
  ∀ a ∈ c.events, ∀ b ∈ c.events,
    a.narratedBefore b = true → a.moment.ordinal ≤ b.moment.ordinal

/-- The first `(a, b)` that breaks T1: `a` is narrated before `b` but happens later. -/
def DeclaredOrder.witness? (c : Chronology) : Option Witness :=
  c.events.findSome? fun a => c.events.findSome? fun b =>
    if a.narratedBefore b && decide (b.moment.ordinal < a.moment.ordinal) then
      some (Witness.mk [a.id, b.id] [])
    else
      none

/-- **T2 · Coherent age**, with T5 inside. A character with a birth date is born by every event
they are present at —a birth is at 00:00 of its date— and every age a source declares for them at
an event is the one their birth date gives at its moment. -/
abbrev AgeCoherence (c : Chronology) : Prop :=
  ∀ e ∈ c.events, ∀ ch ∈ c.characters, ∀ d ∈ listOf ch.birth,
    (ch.id ∈ e.present → d.midnight.ordinal ≤ e.moment.ordinal) ∧
    (∀ a ∈ e.ages, a.character = ch.id →
      d.midnight.ordinal ≤ e.moment.ordinal ∧ d.ageAt e.moment = a.age)

/-- The first `(event, character)` that breaks T2: present before being born, or with a declared
age other than the one the birth date gives. -/
def AgeCoherence.witness? (c : Chronology) : Option Witness :=
  c.events.findSome? fun e => c.characters.findSome? fun ch =>
    (listOf ch.birth).findSome? fun d =>
      let born := decide (d.midnight.ordinal ≤ e.moment.ordinal)
      let presentUnborn := e.present.contains ch.id && !born
      let wrongAge := e.ages.any (fun a => a.character == ch.id && (!born || d.ageAt e.moment != a.age))
      if presentUnborn || wrongAge then some (Witness.mk [e.id] [ch.id]) else none

/-- **T3 · No one is in two places at once.** A character present at two events of the same
moment is at the same place in both. An event without a place conflicts with none. -/
abbrev SinglePlace (c : Chronology) : Prop :=
  ∀ a ∈ c.events, ∀ b ∈ c.events, a.moment.ordinal = b.moment.ordinal →
    ∀ p ∈ a.present, p ∈ b.present →
      ∀ x ∈ listOf a.place, ∀ y ∈ listOf b.place, x = y

/-- The first `(a, b, character)` that breaks T3. -/
def SinglePlace.witness? (c : Chronology) : Option Witness :=
  c.events.findSome? fun a => c.events.findSome? fun b =>
    match a.place, b.place with
    | some x, some y =>
      if a.moment.ordinal == b.moment.ordinal && x != y then
        (a.present.find? (fun p => b.present.contains p)).map (fun p => Witness.mk [a.id, b.id] [p])
      else
        none
    | _, _ => none

/-- **T4 · No one comes back from an exclusion.** The character an exclusion event removes —by
death or final departure— is present at no later event. The same moment is not later. -/
abbrev NoReturnAfterExclusion (c : Chronology) : Prop :=
  ∀ x ∈ c.events, ∀ p ∈ listOf x.excluded, ∀ e ∈ c.events,
    p ∈ e.present → e.moment.ordinal ≤ x.moment.ordinal

/-- The first `(exclusion, later event, character)` that breaks T4. -/
def NoReturnAfterExclusion.witness? (c : Chronology) : Option Witness :=
  c.events.findSome? fun x => (listOf x.excluded).findSome? fun p =>
    c.events.findSome? fun e =>
      if e.present.contains p && decide (x.moment.ordinal < e.moment.ordinal) then
        some (Witness.mk [x.id, e.id] [p])
      else
        none

end Chronology
