import Chronology

open Chronology

def cronologia : Cronologia where
  novum := ⟨2422, 3, 1⟩
  nacimientos := [
    ⟨69, ⟨2397, 1, 1⟩⟩,
    ⟨70, ⟨2395, 1, 1⟩⟩,
    ⟨71, ⟨2404, 1, 1⟩⟩,
    ⟨72, ⟨2420, 1, 1⟩⟩
  ]
  eventos := [
    { id := 596, momento := ⟨2421, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 72, presentes := [⟨69, some 24⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := true },
    { id := 597, momento := ⟨2424, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 73, presentes := [⟨69, some 27⟩], tipo := .ordinario, analepsis := true },
    { id := 598, momento := ⟨2425, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 74, presentes := [⟨69, some 28⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := true },
    { id := 639, momento := ⟨2426, 9, 26, 6, 30⟩, capitulo := some 1, beat := some 1, lugar := 75, presentes := [⟨69, none⟩], tipo := .ordinario, analepsis := false },
    { id := 640, momento := ⟨2426, 9, 26, 7, 15⟩, capitulo := some 1, beat := some 2, lugar := 72, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 641, momento := ⟨2426, 9, 26, 8, 30⟩, capitulo := some 1, beat := some 3, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 642, momento := ⟨2426, 9, 26, 8, 50⟩, capitulo := some 1, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 643, momento := ⟨2426, 9, 28, 10, 0⟩, capitulo := some 2, beat := some 1, lugar := 75, presentes := [⟨69, none⟩], tipo := .ordinario, analepsis := false },
    { id := 644, momento := ⟨2426, 9, 28, 10, 40⟩, capitulo := some 2, beat := some 2, lugar := 76, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 645, momento := ⟨2426, 9, 28, 11, 15⟩, capitulo := some 2, beat := some 3, lugar := 76, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 646, momento := ⟨2426, 9, 28, 11, 45⟩, capitulo := some 2, beat := some 4, lugar := 76, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 647, momento := ⟨2426, 10, 1, 17, 0⟩, capitulo := some 3, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 648, momento := ⟨2424, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 2, lugar := 73, presentes := [⟨69, none⟩], tipo := .ordinario, analepsis := true },
    { id := 649, momento := ⟨2426, 10, 1, 17, 40⟩, capitulo := some 3, beat := some 3, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 650, momento := ⟨2426, 10, 1, 18, 0⟩, capitulo := some 3, beat := some 4, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 651, momento := ⟨2426, 10, 3, 9, 0⟩, capitulo := some 4, beat := some 1, lugar := 75, presentes := [⟨69, none⟩], tipo := .ordinario, analepsis := false },
    { id := 652, momento := ⟨2426, 10, 3, 9, 15⟩, capitulo := some 4, beat := some 2, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 653, momento := ⟨2426, 10, 3, 15, 0⟩, capitulo := some 4, beat := some 3, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 654, momento := ⟨2426, 10, 3, 15, 20⟩, capitulo := some 4, beat := some 4, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 655, momento := ⟨2426, 10, 5, 7, 0⟩, capitulo := some 5, beat := some 1, lugar := 72, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 656, momento := ⟨2421, 1, 1, 12, 0⟩, capitulo := some 5, beat := some 2, lugar := 72, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := true },
    { id := 657, momento := ⟨2426, 10, 5, 8, 0⟩, capitulo := some 5, beat := some 3, lugar := 79, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 658, momento := ⟨2426, 10, 5, 8, 30⟩, capitulo := some 5, beat := some 4, lugar := 79, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 659, momento := ⟨2426, 10, 8, 21, 0⟩, capitulo := some 6, beat := some 1, lugar := 78, presentes := [⟨69, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .excluyente 70, analepsis := false },
    { id := 660, momento := ⟨2426, 10, 8, 21, 45⟩, capitulo := some 6, beat := some 2, lugar := 78, presentes := [⟨69, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 661, momento := ⟨2426, 10, 8, 22, 15⟩, capitulo := some 6, beat := some 3, lugar := 78, presentes := [⟨69, none⟩, ⟨74, none⟩], tipo := .ordinario, analepsis := false },
    { id := 662, momento := ⟨2426, 10, 8, 23, 30⟩, capitulo := some 6, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 663, momento := ⟨2426, 10, 10, 19, 0⟩, capitulo := some 7, beat := some 1, lugar := 75, presentes := [⟨69, none⟩, ⟨72, none⟩], tipo := .ordinario, analepsis := false },
    { id := 664, momento := ⟨2426, 10, 10, 19, 20⟩, capitulo := some 7, beat := some 2, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨72, none⟩], tipo := .ordinario, analepsis := false },
    { id := 665, momento := ⟨2426, 10, 10, 20, 0⟩, capitulo := some 7, beat := some 3, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 666, momento := ⟨2426, 10, 10, 20, 30⟩, capitulo := some 7, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨72, none⟩], tipo := .ordinario, analepsis := false },
    { id := 667, momento := ⟨2426, 10, 12, 22, 0⟩, capitulo := some 8, beat := some 1, lugar := 75, presentes := [⟨69, some 29⟩, ⟨70, some 31⟩], tipo := .ordinario, analepsis := false },
    { id := 668, momento := ⟨2425, 1, 1, 12, 0⟩, capitulo := some 8, beat := some 2, lugar := 74, presentes := [⟨69, some 27⟩, ⟨70, some 29⟩], tipo := .ordinario, analepsis := true },
    { id := 669, momento := ⟨2426, 10, 12, 22, 40⟩, capitulo := some 8, beat := some 3, lugar := 75, presentes := [⟨69, some 29⟩, ⟨70, some 31⟩], tipo := .ordinario, analepsis := false },
    { id := 670, momento := ⟨2426, 10, 12, 23, 10⟩, capitulo := some 8, beat := some 4, lugar := 75, presentes := [⟨69, some 29⟩, ⟨70, some 31⟩, ⟨71, some 22⟩, ⟨72, some 6⟩], tipo := .ordinario, analepsis := false },
    { id := 671, momento := ⟨2426, 10, 16, 17, 0⟩, capitulo := some 9, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 672, momento := ⟨2426, 10, 16, 17, 0⟩, capitulo := some 9, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨72, none⟩, ⟨73, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 673, momento := ⟨2426, 10, 16, 17, 15⟩, capitulo := some 9, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨73, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 674, momento := ⟨2426, 10, 16, 17, 20⟩, capitulo := some 9, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩], tipo := .ordinario, analepsis := false },
    { id := 675, momento := ⟨2426, 10, 16, 19, 0⟩, capitulo := some 9, beat := some 2, lugar := 78, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 676, momento := ⟨2426, 10, 16, 19, 30⟩, capitulo := some 9, beat := some 2, lugar := 78, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 677, momento := ⟨2426, 10, 16, 19, 30⟩, capitulo := some 9, beat := some 2, lugar := 78, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 678, momento := ⟨2426, 10, 16, 22, 0⟩, capitulo := some 9, beat := some 3, lugar := 79, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 679, momento := ⟨2426, 10, 16, 22, 30⟩, capitulo := some 9, beat := some 3, lugar := 79, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := true },
    { id := 680, momento := ⟨2426, 10, 16, 22, 35⟩, capitulo := some 9, beat := some 3, lugar := 79, presentes := [⟨69, none⟩, ⟨71, none⟩], tipo := .ordinario, analepsis := false },
    { id := 681, momento := ⟨2426, 10, 16, 23, 45⟩, capitulo := some 9, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨72, none⟩], tipo := .ordinario, analepsis := false },
    { id := 682, momento := ⟨2426, 10, 17, 0, 0⟩, capitulo := some 9, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 683, momento := ⟨2426, 10, 17, 0, 0⟩, capitulo := some 9, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 684, momento := ⟨2426, 10, 17, 0, 30⟩, capitulo := some 9, beat := some 4, lugar := 75, presentes := [⟨69, none⟩, ⟨70, none⟩], tipo := .ordinario, analepsis := false },
    { id := 685, momento := ⟨2426, 10, 17, 9, 0⟩, capitulo := some 10, beat := some 1, lugar := 77, presentes := [⟨69, none⟩, ⟨71, none⟩, ⟨72, none⟩], tipo := .ordinario, analepsis := false },
    { id := 686, momento := ⟨2426, 10, 17, 12, 0⟩, capitulo := some 10, beat := some 2, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨72, none⟩, ⟨73, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 687, momento := ⟨2426, 10, 17, 13, 0⟩, capitulo := some 10, beat := some 3, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨73, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false },
    { id := 688, momento := ⟨2426, 10, 17, 20, 0⟩, capitulo := some 10, beat := some 4, lugar := 77, presentes := [⟨69, none⟩, ⟨70, none⟩, ⟨71, none⟩, ⟨72, none⟩, ⟨73, none⟩, ⟨74, none⟩, ⟨75, none⟩], tipo := .ordinario, analepsis := false }
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
