import Chronology

open Chronology

def cronologia : Cronologia where
  novum := ⟨6020, 5, 14⟩
  nacimientos := [
    ⟨63, ⟨6019, 1, 1⟩⟩,
    ⟨64, ⟨6015, 1, 1⟩⟩,
    ⟨65, ⟨6006, 1, 1⟩⟩
  ]
  eventos := [
    { id := 500, momento := ⟨6024, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 67, presentes := [⟨63, some 5⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := true },
    { id := 501, momento := ⟨6026, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 68, presentes := [⟨63, some 7⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := true },
    { id := 539, momento := ⟨6026, 9, 27, 8, 0⟩, capitulo := some 1, beat := some 1, lugar := 69, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 540, momento := ⟨6026, 9, 27, 9, 0⟩, capitulo := some 1, beat := some 2, lugar := 69, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 541, momento := ⟨6026, 9, 27, 9, 30⟩, capitulo := some 1, beat := some 3, lugar := 69, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 542, momento := ⟨6026, 9, 27, 19, 0⟩, capitulo := some 1, beat := some 4, lugar := 69, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 543, momento := ⟨6026, 9, 28, 12, 0⟩, capitulo := some 2, beat := some 1, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 544, momento := ⟨6026, 9, 28, 13, 0⟩, capitulo := some 2, beat := some 2, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 545, momento := ⟨6026, 9, 28, 17, 0⟩, capitulo := some 2, beat := some 3, lugar := 70, presentes := [⟨63, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 546, momento := ⟨6026, 9, 28, 18, 30⟩, capitulo := some 3, beat := some 1, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 547, momento := ⟨6024, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 2, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := true },
    { id := 548, momento := ⟨6026, 9, 28, 19, 0⟩, capitulo := some 3, beat := some 3, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 549, momento := ⟨6026, 9, 29, 10, 0⟩, capitulo := some 4, beat := some 1, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨67, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 550, momento := ⟨6026, 9, 29, 10, 30⟩, capitulo := some 4, beat := some 2, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 551, momento := ⟨6026, 9, 29, 11, 0⟩, capitulo := some 4, beat := some 3, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 552, momento := ⟨6026, 9, 29, 12, 0⟩, capitulo := some 4, beat := some 4, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨66, none⟩], tipo := .ordinario, analepsis := false },
    { id := 553, momento := ⟨6026, 9, 29, 12, 30⟩, capitulo := some 4, beat := some 4, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 554, momento := ⟨6026, 9, 29, 13, 0⟩, capitulo := some 4, beat := some 4, lugar := 70, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 555, momento := ⟨6026, 9, 30, 9, 0⟩, capitulo := some 5, beat := some 1, lugar := 70, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 556, momento := ⟨6026, 9, 30, 9, 30⟩, capitulo := some 5, beat := some 2, lugar := 70, presentes := [⟨63, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 557, momento := ⟨6026, 9, 30, 18, 0⟩, capitulo := some 5, beat := some 3, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 558, momento := ⟨6026, 1, 1, 23, 0⟩, capitulo := some 5, beat := some 4, lugar := 68, presentes := [⟨63, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := true },
    { id := 559, momento := ⟨6026, 10, 1, 9, 0⟩, capitulo := some 6, beat := some 1, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 560, momento := ⟨6026, 10, 1, 9, 45⟩, capitulo := some 6, beat := some 2, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 561, momento := ⟨6026, 10, 1, 10, 0⟩, capitulo := some 6, beat := some 3, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 562, momento := ⟨6026, 10, 1, 10, 30⟩, capitulo := some 6, beat := some 4, lugar := 71, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 563, momento := ⟨6026, 10, 2, 11, 0⟩, capitulo := some 7, beat := some 1, lugar := 70, presentes := [⟨64, none⟩, ⟨66, none⟩], tipo := .ordinario, analepsis := false },
    { id := 564, momento := ⟨6026, 10, 2, 11, 30⟩, capitulo := some 7, beat := some 1, lugar := 70, presentes := [⟨64, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 565, momento := ⟨6026, 10, 2, 11, 0⟩, capitulo := some 7, beat := some 2, lugar := 67, presentes := [⟨63, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 566, momento := ⟨6026, 10, 2, 12, 30⟩, capitulo := some 7, beat := some 2, lugar := 67, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 567, momento := ⟨6026, 10, 2, 12, 0⟩, capitulo := some 7, beat := some 3, lugar := 70, presentes := [⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 568, momento := ⟨6026, 10, 2, 12, 30⟩, capitulo := some 7, beat := some 3, lugar := 70, presentes := [⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 569, momento := ⟨6026, 10, 2, 18, 0⟩, capitulo := some 7, beat := some 4, lugar := 67, presentes := [⟨63, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 570, momento := ⟨6026, 10, 2, 18, 15⟩, capitulo := some 7, beat := some 4, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩], tipo := .ordinario, analepsis := false },
    { id := 571, momento := ⟨6026, 10, 2, 18, 30⟩, capitulo := some 7, beat := some 4, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 572, momento := ⟨6026, 10, 3, 21, 0⟩, capitulo := some 8, beat := some 1, lugar := 70, presentes := [⟨63, some 7⟩, ⟨64, some 11⟩], tipo := .ordinario, analepsis := false },
    { id := 573, momento := ⟨6026, 10, 3, 21, 30⟩, capitulo := some 8, beat := some 2, lugar := 70, presentes := [⟨63, some 7⟩, ⟨64, some 11⟩], tipo := .ordinario, analepsis := false },
    { id := 574, momento := ⟨6026, 10, 3, 22, 0⟩, capitulo := some 8, beat := some 3, lugar := 70, presentes := [⟨63, some 7⟩, ⟨64, some 11⟩, ⟨65, none⟩], tipo := .ordinario, analepsis := false },
    { id := 575, momento := ⟨6026, 10, 4, 8, 0⟩, capitulo := some 9, beat := some 1, lugar := 70, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 576, momento := ⟨6026, 10, 4, 12, 0⟩, capitulo := some 9, beat := some 2, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨67, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 577, momento := ⟨6026, 10, 4, 13, 0⟩, capitulo := some 9, beat := some 3, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 578, momento := ⟨6026, 10, 4, 13, 5⟩, capitulo := some 9, beat := some 4, lugar := 70, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 579, momento := ⟨6026, 10, 4, 14, 0⟩, capitulo := some 10, beat := some 1, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 580, momento := ⟨6026, 10, 4, 16, 0⟩, capitulo := some 10, beat := some 2, lugar := 67, presentes := [⟨63, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 581, momento := ⟨6026, 10, 4, 16, 15⟩, capitulo := some 10, beat := some 2, lugar := 67, presentes := [⟨63, none⟩, ⟨68, none⟩], tipo := .ordinario, analepsis := false },
    { id := 582, momento := ⟨6026, 10, 4, 18, 30⟩, capitulo := some 10, beat := some 3, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 583, momento := ⟨6026, 10, 4, 18, 35⟩, capitulo := some 10, beat := some 3, lugar := 67, presentes := [⟨63, none⟩, ⟨64, none⟩, ⟨65, none⟩, ⟨66, none⟩, ⟨67, none⟩], tipo := .ordinario, analepsis := false },
    { id := 584, momento := ⟨6026, 10, 4, 21, 30⟩, capitulo := some 10, beat := some 4, lugar := 70, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false },
    { id := 585, momento := ⟨6026, 10, 4, 21, 45⟩, capitulo := some 10, beat := some 4, lugar := 70, presentes := [⟨63, none⟩], tipo := .ordinario, analepsis := false }
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
