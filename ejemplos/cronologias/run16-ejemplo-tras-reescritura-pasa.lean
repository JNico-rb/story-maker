import Chronology

open Chronology

def cronologia : Cronologia where
  novum := ⟨3218, 4, 12⟩
  nacimientos := [
    ⟨87, ⟨3190, 1, 1⟩⟩,
    ⟨88, ⟨3220, 1, 1⟩⟩,
    ⟨89, ⟨3142, 1, 1⟩⟩
  ]
  eventos := [
    { id := 835, momento := ⟨3197, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 93, presentes := [⟨87, some 7⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 836, momento := ⟨3220, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 94, presentes := [⟨87, some 30⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := true },
    { id := 837, momento := ⟨3199, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 95, presentes := [⟨87, some 9⟩], tipo := .ordinario, analepsis := true },
    { id := 893, momento := ⟨3226, 9, 29, 9, 0⟩, capitulo := some 2, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 894, momento := ⟨3226, 9, 29, 9, 30⟩, capitulo := some 2, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 895, momento := ⟨3226, 9, 29, 10, 0⟩, capitulo := some 2, beat := some 3, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 896, momento := ⟨3220, 1, 1, 12, 0⟩, capitulo := some 2, beat := some 4, lugar := 94, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := true },
    { id := 897, momento := ⟨3226, 9, 29, 15, 0⟩, capitulo := some 2, beat := some 5, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 898, momento := ⟨3226, 9, 29, 17, 0⟩, capitulo := some 2, beat := some 6, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 912, momento := ⟨3226, 10, 1, 17, 30⟩, capitulo := some 5, beat := some 1, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 913, momento := ⟨3226, 10, 1, 18, 0⟩, capitulo := some 5, beat := some 1, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 914, momento := ⟨3226, 10, 1, 18, 30⟩, capitulo := some 5, beat := some 2, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 915, momento := ⟨3226, 10, 1, 19, 0⟩, capitulo := some 5, beat := some 2, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 916, momento := ⟨3226, 10, 1, 19, 15⟩, capitulo := some 5, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 917, momento := ⟨3226, 10, 1, 19, 30⟩, capitulo := some 5, beat := some 4, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 918, momento := ⟨3226, 10, 1, 19, 45⟩, capitulo := some 5, beat := some 5, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 919, momento := ⟨3226, 10, 1, 20, 0⟩, capitulo := some 5, beat := some 5, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 920, momento := ⟨3226, 10, 2, 0, 0⟩, capitulo := some 6, beat := some 1, lugar := 100, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 921, momento := ⟨3226, 10, 2, 1, 30⟩, capitulo := some 6, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 922, momento := ⟨3226, 10, 2, 1, 35⟩, capitulo := some 6, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 923, momento := ⟨3226, 10, 2, 1, 45⟩, capitulo := some 6, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 924, momento := ⟨3226, 10, 2, 1, 50⟩, capitulo := some 6, beat := some 3, lugar := 96, presentes := [⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 925, momento := ⟨3226, 10, 2, 2, 0⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 926, momento := ⟨3226, 10, 2, 2, 5⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 927, momento := ⟨3226, 10, 2, 2, 10⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 933, momento := ⟨3226, 10, 5, 8, 0⟩, capitulo := some 8, beat := some 1, lugar := 96, presentes := [⟨87, some 36⟩, ⟨88, some 6⟩], tipo := .ordinario, analepsis := false },
    { id := 934, momento := ⟨3226, 10, 5, 9, 30⟩, capitulo := some 8, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 935, momento := ⟨3226, 10, 5, 10, 0⟩, capitulo := some 8, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 936, momento := ⟨3226, 10, 5, 12, 0⟩, capitulo := some 8, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 937, momento := ⟨3226, 10, 5, 12, 0⟩, capitulo := some 8, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 938, momento := ⟨3226, 10, 5, 12, 15⟩, capitulo := some 8, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 939, momento := ⟨3226, 10, 5, 12, 30⟩, capitulo := some 8, beat := some 5, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 940, momento := ⟨3226, 10, 5, 13, 0⟩, capitulo := some 9, beat := some 1, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 941, momento := ⟨3226, 10, 5, 13, 30⟩, capitulo := some 9, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 942, momento := ⟨3196, 6, 28, 18, 0⟩, capitulo := some 9, beat := some 2, lugar := 93, presentes := [⟨87, some 6⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 943, momento := ⟨3226, 10, 5, 14, 0⟩, capitulo := some 9, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 944, momento := ⟨3226, 10, 5, 14, 5⟩, capitulo := some 9, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 945, momento := ⟨3226, 10, 5, 15, 0⟩, capitulo := some 9, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 946, momento := ⟨3226, 10, 5, 19, 30⟩, capitulo := some 9, beat := some 5, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 947, momento := ⟨3226, 10, 5, 20, 30⟩, capitulo := some 10, beat := some 1, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 948, momento := ⟨3226, 10, 5, 21, 15⟩, capitulo := some 10, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 949, momento := ⟨3226, 10, 5, 21, 30⟩, capitulo := some 10, beat := some 3, lugar := 101, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 950, momento := ⟨3226, 10, 5, 22, 0⟩, capitulo := some 10, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 951, momento := ⟨3226, 9, 28, 7, 0⟩, capitulo := some 1, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 952, momento := ⟨3226, 9, 28, 9, 0⟩, capitulo := some 1, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 953, momento := ⟨3226, 9, 28, 10, 30⟩, capitulo := some 1, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 954, momento := ⟨3226, 9, 28, 11, 0⟩, capitulo := some 1, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 955, momento := ⟨3197, 1, 1, 12, 0⟩, capitulo := some 1, beat := some 4, lugar := 93, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 956, momento := ⟨3199, 1, 1, 12, 0⟩, capitulo := some 1, beat := some 4, lugar := 95, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := true },
    { id := 957, momento := ⟨3220, 1, 1, 12, 0⟩, capitulo := some 1, beat := some 3, lugar := 94, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := true },
    { id := 958, momento := ⟨3226, 9, 30, 6, 0⟩, capitulo := some 3, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 959, momento := ⟨3226, 9, 30, 7, 0⟩, capitulo := some 3, beat := some 2, lugar := 93, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 960, momento := ⟨3197, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 2, lugar := 93, presentes := [⟨87, some 7⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 961, momento := ⟨3226, 9, 30, 7, 45⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 962, momento := ⟨3226, 9, 30, 8, 0⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 963, momento := ⟨3226, 9, 30, 8, 0⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 964, momento := ⟨3226, 9, 30, 8, 15⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 965, momento := ⟨3226, 9, 30, 16, 0⟩, capitulo := some 3, beat := some 4, lugar := 98, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 966, momento := ⟨3199, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 4, lugar := 95, presentes := [⟨87, some 9⟩], tipo := .ordinario, analepsis := true },
    { id := 967, momento := ⟨3226, 9, 30, 16, 30⟩, capitulo := some 4, beat := some 1, lugar := 98, presentes := [⟨87, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 968, momento := ⟨3199, 1, 1, 12, 0⟩, capitulo := some 4, beat := some 2, lugar := 95, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := true },
    { id := 969, momento := ⟨3226, 9, 30, 17, 30⟩, capitulo := some 4, beat := some 3, lugar := 98, presentes := [⟨87, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 970, momento := ⟨3226, 9, 30, 18, 0⟩, capitulo := some 4, beat := some 4, lugar := 98, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 971, momento := ⟨3226, 10, 2, 9, 0⟩, capitulo := some 7, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 972, momento := ⟨3226, 10, 2, 13, 0⟩, capitulo := some 7, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 973, momento := ⟨3226, 10, 3, 15, 0⟩, capitulo := some 7, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 974, momento := ⟨3226, 10, 4, 18, 0⟩, capitulo := some 7, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false }
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
