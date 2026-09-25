import Chronology

open Chronology

def cronologia : Cronologia where
  novum := ⟨4418, 4, 12⟩
  nacimientos := [
    ⟨87, ⟨4390, 1, 1⟩⟩,
    ⟨88, ⟨4420, 1, 1⟩⟩,
    ⟨89, ⟨4342, 1, 1⟩⟩
  ]
  eventos := [
    { id := 835, momento := ⟨4397, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 93, presentes := [⟨87, some 7⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 836, momento := ⟨4420, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 94, presentes := [⟨87, some 30⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := true },
    { id := 837, momento := ⟨4399, 1, 1, 12, 0⟩, capitulo := none, beat := none, lugar := 95, presentes := [⟨87, some 9⟩], tipo := .ordinario, analepsis := true },
    { id := 884, momento := ⟨4426, 9, 28, 6, 0⟩, capitulo := some 1, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 885, momento := ⟨4426, 9, 28, 6, 30⟩, capitulo := some 1, beat := some 1, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 886, momento := ⟨4426, 9, 28, 8, 45⟩, capitulo := some 1, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 887, momento := ⟨4426, 9, 28, 9, 0⟩, capitulo := some 1, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 888, momento := ⟨4426, 9, 28, 9, 30⟩, capitulo := some 1, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 889, momento := ⟨4426, 9, 28, 10, 30⟩, capitulo := some 1, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 890, momento := ⟨4426, 9, 28, 11, 0⟩, capitulo := some 1, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 891, momento := ⟨4396, 6, 28, 18, 0⟩, capitulo := some 1, beat := some 4, lugar := 93, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 892, momento := ⟨4406, 9, 28, 14, 0⟩, capitulo := some 1, beat := some 4, lugar := 95, presentes := [⟨87, some 10⟩], tipo := .ordinario, analepsis := true },
    { id := 893, momento := ⟨4426, 9, 29, 9, 0⟩, capitulo := some 2, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 894, momento := ⟨4426, 9, 29, 9, 30⟩, capitulo := some 2, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 895, momento := ⟨4426, 9, 29, 10, 0⟩, capitulo := some 2, beat := some 3, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 896, momento := ⟨4420, 1, 1, 12, 0⟩, capitulo := some 2, beat := some 4, lugar := 94, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := true },
    { id := 897, momento := ⟨4426, 9, 29, 15, 0⟩, capitulo := some 2, beat := some 5, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 898, momento := ⟨4426, 9, 29, 17, 0⟩, capitulo := some 2, beat := some 6, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 899, momento := ⟨4426, 9, 30, 6, 0⟩, capitulo := some 3, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 900, momento := ⟨4426, 9, 30, 10, 0⟩, capitulo := some 3, beat := some 2, lugar := 93, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 901, momento := ⟨4397, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 2, lugar := 93, presentes := [⟨87, some 7⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 902, momento := ⟨4426, 9, 30, 12, 0⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 903, momento := ⟨4426, 9, 30, 12, 30⟩, capitulo := some 3, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 904, momento := ⟨4372, 1, 1, 12, 0⟩, capitulo := some 3, beat := some 3, lugar := 95, presentes := [⟨89, some 30⟩], tipo := .ordinario, analepsis := true },
    { id := 905, momento := ⟨4372, 10, 1, 12, 0⟩, capitulo := some 3, beat := some 3, lugar := 95, presentes := [⟨89, some 30⟩], tipo := .ordinario, analepsis := true },
    { id := 906, momento := ⟨4426, 9, 30, 16, 0⟩, capitulo := some 3, beat := some 4, lugar := 95, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 907, momento := ⟨4426, 9, 30, 16, 30⟩, capitulo := some 3, beat := some 4, lugar := 98, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 908, momento := ⟨4426, 9, 30, 16, 30⟩, capitulo := some 4, beat := some 1, lugar := 98, presentes := [⟨87, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 909, momento := ⟨4399, 1, 1, 12, 0⟩, capitulo := some 4, beat := some 2, lugar := 95, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := true },
    { id := 910, momento := ⟨4426, 9, 30, 17, 30⟩, capitulo := some 4, beat := some 3, lugar := 98, presentes := [⟨87, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 911, momento := ⟨4426, 9, 30, 18, 0⟩, capitulo := some 4, beat := some 4, lugar := 98, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 912, momento := ⟨4426, 10, 1, 17, 30⟩, capitulo := some 5, beat := some 1, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 913, momento := ⟨4426, 10, 1, 18, 0⟩, capitulo := some 5, beat := some 1, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 914, momento := ⟨4426, 10, 1, 18, 30⟩, capitulo := some 5, beat := some 2, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 915, momento := ⟨4426, 10, 1, 19, 0⟩, capitulo := some 5, beat := some 2, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 916, momento := ⟨4426, 10, 1, 19, 15⟩, capitulo := some 5, beat := some 3, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 917, momento := ⟨4426, 10, 1, 19, 30⟩, capitulo := some 5, beat := some 4, lugar := 99, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 918, momento := ⟨4426, 10, 1, 19, 45⟩, capitulo := some 5, beat := some 5, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 919, momento := ⟨4426, 10, 1, 20, 0⟩, capitulo := some 5, beat := some 5, lugar := 99, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 920, momento := ⟨4426, 10, 2, 0, 0⟩, capitulo := some 6, beat := some 1, lugar := 100, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 921, momento := ⟨4426, 10, 2, 1, 30⟩, capitulo := some 6, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 922, momento := ⟨4426, 10, 2, 1, 35⟩, capitulo := some 6, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 923, momento := ⟨4426, 10, 2, 1, 45⟩, capitulo := some 6, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 924, momento := ⟨4426, 10, 2, 1, 50⟩, capitulo := some 6, beat := some 3, lugar := 96, presentes := [⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 925, momento := ⟨4426, 10, 2, 2, 0⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 926, momento := ⟨4426, 10, 2, 2, 5⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 927, momento := ⟨4426, 10, 2, 2, 10⟩, capitulo := some 6, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 928, momento := ⟨4426, 10, 2, 6, 0⟩, capitulo := some 7, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨88, none⟩], tipo := .ordinario, analepsis := false },
    { id := 929, momento := ⟨4426, 10, 2, 9, 0⟩, capitulo := some 7, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 930, momento := ⟨4426, 10, 2, 13, 0⟩, capitulo := some 7, beat := some 2, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 931, momento := ⟨4426, 10, 3, 15, 0⟩, capitulo := some 7, beat := some 3, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 932, momento := ⟨4426, 10, 4, 18, 0⟩, capitulo := some 7, beat := some 4, lugar := 96, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 933, momento := ⟨4426, 10, 5, 8, 0⟩, capitulo := some 8, beat := some 1, lugar := 96, presentes := [⟨87, some 36⟩, ⟨88, some 6⟩], tipo := .ordinario, analepsis := false },
    { id := 934, momento := ⟨4426, 10, 5, 9, 30⟩, capitulo := some 8, beat := some 1, lugar := 96, presentes := [⟨87, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 935, momento := ⟨4426, 10, 5, 10, 0⟩, capitulo := some 8, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 936, momento := ⟨4426, 10, 5, 12, 0⟩, capitulo := some 8, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 937, momento := ⟨4426, 10, 5, 12, 0⟩, capitulo := some 8, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 938, momento := ⟨4426, 10, 5, 12, 15⟩, capitulo := some 8, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 939, momento := ⟨4426, 10, 5, 12, 30⟩, capitulo := some 8, beat := some 5, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨90, none⟩], tipo := .ordinario, analepsis := false },
    { id := 940, momento := ⟨4426, 10, 5, 13, 0⟩, capitulo := some 9, beat := some 1, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 941, momento := ⟨4426, 10, 5, 13, 30⟩, capitulo := some 9, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := false },
    { id := 942, momento := ⟨4396, 6, 28, 18, 0⟩, capitulo := some 9, beat := some 2, lugar := 93, presentes := [⟨87, some 6⟩, ⟨89, none⟩], tipo := .ordinario, analepsis := true },
    { id := 943, momento := ⟨4426, 10, 5, 14, 0⟩, capitulo := some 9, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 944, momento := ⟨4426, 10, 5, 14, 5⟩, capitulo := some 9, beat := some 3, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 945, momento := ⟨4426, 10, 5, 15, 0⟩, capitulo := some 9, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 946, momento := ⟨4426, 10, 5, 19, 30⟩, capitulo := some 9, beat := some 5, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 947, momento := ⟨4426, 10, 5, 20, 30⟩, capitulo := some 10, beat := some 1, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 948, momento := ⟨4426, 10, 5, 21, 15⟩, capitulo := some 10, beat := some 2, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false },
    { id := 949, momento := ⟨4426, 10, 5, 21, 30⟩, capitulo := some 10, beat := some 3, lugar := 101, presentes := [⟨87, none⟩], tipo := .ordinario, analepsis := false },
    { id := 950, momento := ⟨4426, 10, 5, 22, 0⟩, capitulo := some 10, beat := some 4, lugar := 101, presentes := [⟨87, none⟩, ⟨88, none⟩, ⟨89, none⟩, ⟨90, none⟩, ⟨91, none⟩], tipo := .ordinario, analepsis := false }
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
