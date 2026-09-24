import Chronology

open Chronology

def cronologia : Cronologia where
  novum := ⟨3224, 11, 1⟩
  nacimientos := [
    ⟨11, ⟨3190, 5, 14⟩⟩,
    ⟨12, ⟨3136, 2, 29⟩⟩
  ]
  eventos := [
    { id := 31, momento := ⟨3198, 5, 14, 12, 0⟩, capitulo := none, beat := none, lugar := 21, presentes := [⟨11, some 8⟩, ⟨12, none⟩], tipo := .ordinario, analepsis := false },
    { id := 32, momento := ⟨3210, 9, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 22, presentes := [⟨11, none⟩], tipo := .excluyente 12, analepsis := false },
    { id := 41, momento := ⟨3226, 3, 2, 10, 0⟩, capitulo := some 1, beat := some 1, lugar := 21, presentes := [⟨11, none⟩, ⟨13, none⟩], tipo := .ordinario, analepsis := false },
    { id := 42, momento := ⟨3205, 7, 1, 18, 0⟩, capitulo := some 2, beat := some 1, lugar := 22, presentes := [⟨11, none⟩, ⟨12, none⟩], tipo := .ordinario, analepsis := true },
    { id := 61, momento := ⟨3207, 2, 28, 12, 0⟩, capitulo := none, beat := none, lugar := 21, presentes := [⟨12, some 71⟩], tipo := .ordinario, analepsis := false }
  ]

#eval IO.println ("CRONOLOGIA-LEAN " ++ informe cronologia)

theorem cumpleT1 : T1 cronologia := (compruebaT1_decide cronologia).mp (by decide +kernel)
theorem cumpleT2 : T2 cronologia := (compruebaT2_decide cronologia).mp (by decide +kernel)
theorem cumpleT3 : T3 cronologia := (compruebaT3_decide cronologia).mp (by decide +kernel)
theorem cumpleT4 : T4 cronologia := (compruebaT4_decide cronologia).mp (by decide +kernel)
theorem cumpleT5 : T5 cronologia := (compruebaT5_decide cronologia).mp (by decide +kernel)

#print axioms cumpleT1
#print axioms cumpleT2
#print axioms cumpleT3
#print axioms cumpleT4
#print axioms cumpleT5
