/-!
# Cronología de una novela y sus invariantes T1–T5 (spec 007)

Tipos de la cronología; los invariantes T1–T5 (`domain-knowledge.md` §5.3) como predicados
decidibles; un comprobador por invariante con su demostración general (corrección y
completitud); y el informe JSON con el primer testigo de cada invariante violado.

Los momentos se comparan por fecha y hora, al minuto: (año, mes, día, hora, minuto) en orden
lexicográfico. El generador del backend solo escribe fechas de calendario válidas, con ids de
fila de SQLite y años desplazados 400·k (lo que no cambia ningún resultado).

Cada predicado se enuncia sobre una relación booleana con nombre (`rompeOrden`, `edadErronea`,
`enDosLugares`, `vuelve`, `antesDeNacer`), que comparten el predicado y la búsqueda del testigo.
El comprobador es la decisión del predicado, que dan los cuantificadores acotados sobre listas;
su demostración general vale para toda cronología. Nada de esto se repite en Python (007-I1).
-/

namespace Chronology

/-! ## Tipos -/

/-- Fecha de calendario. -/
structure Fecha where
  anio : Nat
  mes : Nat
  dia : Nat

/-- Fecha de calendario y hora, al minuto. -/
structure Momento where
  anio : Nat
  mes : Nat
  dia : Nat
  hora : Nat
  minuto : Nat

/-- Personaje presente en un evento, con su edad declarada si la fuente la fija. -/
structure Presente where
  personaje : Nat
  edad : Option Nat

/-- Un evento excluyente (una muerte, una partida definitiva) nombra a su excluido. -/
inductive Tipo where
  | ordinario
  | excluyente (excluido : Nat)

/-- Evento de la cronología; `capitulo` y `beat` van vacíos si no se narra (origen brief). -/
structure Evento where
  id : Nat
  momento : Momento
  capitulo : Option Nat
  beat : Option Nat
  lugar : Nat
  presentes : List Presente
  tipo : Tipo
  analepsis : Bool

/-- Fecha de nacimiento de un personaje. -/
structure Nacimiento where
  personaje : Nat
  fecha : Fecha

/-- Cronología registrada de una versión: eventos, nacimientos y fecha del novum. -/
structure Cronologia where
  eventos : List Evento
  nacimientos : List Nacimiento
  novum : Fecha

/-! ## Orden y edades -/

/-- `xs` es menor que `ys` en orden lexicográfico. -/
def lexMenor : List Nat → List Nat → Bool
  | [], [] => false
  | [], _ :: _ => true
  | _ :: _, [] => false
  | x :: xs, y :: ys => decide (x < y) || (decide (x = y) && lexMenor xs ys)

/-- `xs` e `ys` son iguales. -/
def iguales : List Nat → List Nat → Bool
  | [], [] => true
  | x :: xs, y :: ys => decide (x = y) && iguales xs ys
  | _, _ => false

/-- Componentes de un momento, en el orden en que se comparan. -/
def Momento.componentes (m : Momento) : List Nat := [m.anio, m.mes, m.dia, m.hora, m.minuto]

/-- `x` es anterior a `y`. -/
def Momento.antes (x y : Momento) : Bool := lexMenor x.componentes y.componentes

/-- `x` e `y` son el mismo momento. -/
def Momento.igual (x y : Momento) : Bool := iguales x.componentes y.componentes

/-- Se nace a las 00:00 de la fecha de nacimiento (`domain-knowledge.md` §5.2). -/
def Fecha.inicio (f : Fecha) : Momento := ⟨f.anio, f.mes, f.dia, 0, 0⟩

/-- Edad en años cumplidos en `m` de quien nació en `f`. El cumpleaños llega a las 00:00 de su
día; quien nació un 29 de febrero cumple el 1 de marzo en los años no bisiestos, que no tienen
29 de febrero: el primer día que no es anterior a (2, 29) es el 1 de marzo. -/
def edadEn (f : Fecha) (m : Momento) : Nat :=
  if lexMenor [m.mes, m.dia] [f.mes, f.dia] then m.anio - f.anio - 1 else m.anio - f.anio

/-- `a` se narra antes que `b`, por capítulo y beat. Dentro de un beat no hay orden, y un evento
sin capítulo no se narra. -/
def narradoAntes (a b : Evento) : Bool :=
  match a.capitulo, a.beat, b.capitulo, b.beat with
  | some ca, some ba, some cb, some bb => lexMenor [ca, ba] [cb, bb]
  | _, _, _, _ => false

/-- `p` está presente en `e`. -/
def presente (e : Evento) (p : Nat) : Bool :=
  e.presentes.any fun x => decide (x.personaje = p)

/-- Fecha de nacimiento de `p` en `ns`, si la tiene. -/
def buscarNacimiento (p : Nat) : List Nacimiento → Option Fecha
  | [] => none
  | n :: ns => if n.personaje = p then some n.fecha else buscarNacimiento p ns

/-- Fecha de nacimiento de `p`, si la tiene. -/
def Cronologia.nacimientoDe (c : Cronologia) (p : Nat) : Option Fecha :=
  buscarNacimiento p c.nacimientos

/-! ## Violaciones -/

/-- T1: `b` se narra después de `a` y su momento es anterior; ninguno de los dos es analepsis. -/
def rompeOrden (a b : Evento) : Bool :=
  !a.analepsis && !b.analepsis && narradoAntes a b && b.momento.antes a.momento

/-- T2: la edad declarada de `x` en `e` y la que dan su nacimiento y el momento, si difieren.
Sin edad declarada o sin fecha de nacimiento, T2 no alcanza. -/
def edadErronea (c : Cronologia) (e : Evento) (x : Presente) : Option (Nat × Nat) :=
  match x.edad, c.nacimientoDe x.personaje with
  | some n, some f => if n = edadEn f e.momento then none else some (n, edadEn f e.momento)
  | _, _ => none

/-- T3: `p` está en `a` y en `b`, del mismo momento y en lugares distintos (`a`, el de id
menor). -/
def enDosLugares (a b : Evento) (p : Nat) : Bool :=
  decide (a.id < b.id) && a.momento.igual b.momento && !decide (a.lugar = b.lugar) &&
    presente a p && presente b p

/-- T4: `x` es excluyente y su excluido está presente en `e`, estrictamente posterior. -/
def vuelve (x e : Evento) : Bool :=
  match x.tipo with
  | .excluyente p => x.momento.antes e.momento && presente e p
  | .ordinario => false

/-- T5: `e` es anterior al nacimiento de `x`. Sin fecha de nacimiento, T5 no alcanza. -/
def antesDeNacer (c : Cronologia) (e : Evento) (x : Presente) : Bool :=
  match c.nacimientoDe x.personaje with
  | some f => e.momento.antes f.inicio
  | none => false

/-! ## Invariantes -/

/-- T1 · Orden temporal declarado: los eventos narrados que no son analepsis avanzan en el orden
de capítulo y beat; ninguno es anterior a otro que se narra antes. -/
abbrev T1 (c : Cronologia) : Prop :=
  ∀ a ∈ c.eventos, ∀ b ∈ c.eventos, rompeOrden a b = false

/-- T2 · Edad coherente: la edad declarada de quien tiene fecha de nacimiento es la que dan esa
fecha y el momento del evento. -/
abbrev T2 (c : Cronologia) : Prop :=
  ∀ e ∈ c.eventos, ∀ x ∈ e.presentes, (edadErronea c e x).isNone = true

/-- T3 · Nadie está en dos lugares a la vez: nadie está presente en dos eventos del mismo
momento con lugares distintos. -/
abbrev T3 (c : Cronologia) : Prop :=
  ∀ a ∈ c.eventos, ∀ b ∈ c.eventos, ∀ x ∈ a.presentes, enDosLugares a b x.personaje = false

/-- T4 · Nadie vuelve de un evento excluyente: el excluido no está presente en ningún evento
posterior. -/
abbrev T4 (c : Cronologia) : Prop :=
  ∀ x ∈ c.eventos, ∀ e ∈ c.eventos, vuelve x e = false

/-- T5 · Nadie actúa antes de nacer: nadie con fecha de nacimiento está presente en un evento
anterior a ella. -/
abbrev T5 (c : Cronologia) : Prop :=
  ∀ e ∈ c.eventos, ∀ x ∈ e.presentes, antesDeNacer c e x = false

/-! ## Comprobadores y su demostración general -/

/-- Comprobador de T1. -/
def compruebaT1 (c : Cronologia) : Bool := decide (T1 c)

/-- Comprobador de T2. -/
def compruebaT2 (c : Cronologia) : Bool := decide (T2 c)

/-- Comprobador de T3. -/
def compruebaT3 (c : Cronologia) : Bool := decide (T3 c)

/-- Comprobador de T4. -/
def compruebaT4 (c : Cronologia) : Bool := decide (T4 c)

/-- Comprobador de T5. -/
def compruebaT5 (c : Cronologia) : Bool := decide (T5 c)

/-- Para toda cronología, `compruebaT1` da `true` si y solo si se cumple T1: corrección (→) y
completitud (←), que descarta el comprobador que rechaza siempre. -/
theorem compruebaT1_decide (c : Cronologia) : compruebaT1 c = true ↔ T1 c :=
  show decide (T1 c) = true ↔ T1 c from ⟨of_decide_eq_true, decide_eq_true⟩

/-- Para toda cronología, `compruebaT2` da `true` si y solo si se cumple T2. -/
theorem compruebaT2_decide (c : Cronologia) : compruebaT2 c = true ↔ T2 c :=
  show decide (T2 c) = true ↔ T2 c from ⟨of_decide_eq_true, decide_eq_true⟩

/-- Para toda cronología, `compruebaT3` da `true` si y solo si se cumple T3. -/
theorem compruebaT3_decide (c : Cronologia) : compruebaT3 c = true ↔ T3 c :=
  show decide (T3 c) = true ↔ T3 c from ⟨of_decide_eq_true, decide_eq_true⟩

/-- Para toda cronología, `compruebaT4` da `true` si y solo si se cumple T4. -/
theorem compruebaT4_decide (c : Cronologia) : compruebaT4 c = true ↔ T4 c :=
  show decide (T4 c) = true ↔ T4 c from ⟨of_decide_eq_true, decide_eq_true⟩

/-- Para toda cronología, `compruebaT5` da `true` si y solo si se cumple T5. -/
theorem compruebaT5_decide (c : Cronologia) : compruebaT5 c = true ↔ T5 c :=
  show decide (T5 c) = true ↔ T5 c from ⟨of_decide_eq_true, decide_eq_true⟩

/-! ## Primer testigo -/

/-- Concatena las listas. -/
def aplanar {α : Type} : List (List α) → List α
  | [] => []
  | x :: xs => x ++ aplanar xs

/-- La tupla menor en orden lexicográfico de ids, si hay alguna. -/
def primero (ts : List (List Nat)) : Option (List Nat) :=
  ts.foldl menor none
where
  menor : Option (List Nat) → List Nat → Option (List Nat)
    | none, t => some t
    | some m, t => if lexMenor t m then some t else some m

/-- Testigo de T1: (evento narrado antes, evento narrado después). -/
def testigoT1 (c : Cronologia) : Option (List Nat) :=
  primero <| aplanar <| c.eventos.map fun a =>
    (c.eventos.filter fun b => rompeOrden a b).map fun b => [a.id, b.id]

/-- Testigo de T2: (personaje, evento, edad declarada, edad calculada). -/
def testigoT2 (c : Cronologia) : Option (List Nat) :=
  primero <| aplanar <| c.eventos.map fun e =>
    e.presentes.filterMap fun x =>
      (edadErronea c e x).map fun d => [x.personaje, e.id, d.1, d.2]

/-- Testigo de T3: (personaje, evento, evento), el de id menor primero. -/
def testigoT3 (c : Cronologia) : Option (List Nat) :=
  primero <| aplanar <| c.eventos.map fun a => aplanar <| c.eventos.map fun b =>
    (a.presentes.filter fun x => enDosLugares a b x.personaje).map fun x =>
      [x.personaje, a.id, b.id]

/-- Testigo de T4: (personaje excluido, evento excluyente, evento posterior). -/
def testigoT4 (c : Cronologia) : Option (List Nat) :=
  primero <| aplanar <| c.eventos.map fun x =>
    match x.tipo with
    | .excluyente p => (c.eventos.filter fun e => vuelve x e).map fun e => [p, x.id, e.id]
    | .ordinario => []

/-- Testigo de T5: (personaje, evento). -/
def testigoT5 (c : Cronologia) : Option (List Nat) :=
  primero <| aplanar <| c.eventos.map fun e =>
    (e.presentes.filter fun x => antesDeNacer c e x).map fun x => [x.personaje, e.id]

/-! ## Informe -/

/-- Lista de números en JSON. -/
def jsonLista (t : List Nat) : String :=
  "[" ++ ",".intercalate (t.map toString) ++ "]"

/-- Valor JSON de un invariante: si se cumple y, si no, su primer testigo. -/
def jsonValor : Bool → Option (List Nat) → String
  | true, _ => "{\"cumple\":true}"
  | false, some t => "{\"cumple\":false,\"testigo\":" ++ jsonLista t ++ "}"
  | false, none => "{\"cumple\":false}"

/-- Entrada JSON de un invariante. -/
def jsonInvariante (nombre : String) (cumple : Bool) (testigo : Option (List Nat)) : String :=
  "\"" ++ nombre ++ "\":" ++ jsonValor cumple testigo

/-- Informe JSON de la cronología: por invariante, si se cumple y, si no, su primer testigo. -/
def informe (c : Cronologia) : String :=
  "{" ++ ",".intercalate [
    jsonInvariante "T1" (compruebaT1 c) (testigoT1 c),
    jsonInvariante "T2" (compruebaT2 c) (testigoT2 c),
    jsonInvariante "T3" (compruebaT3 c) (testigoT3 c),
    jsonInvariante "T4" (compruebaT4 c) (testigoT4 c),
    jsonInvariante "T5" (compruebaT5 c) (testigoT5 c)] ++ "}"

end Chronology
