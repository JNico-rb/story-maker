"""Ficheros Lean de la CI (007-C20 a 007-C24): cada uno es la salida del generador para su
cronología, y `lean/pruebas/esperado.json` dice lo que la CI espera de cada uno.

Lo que da Lean al compilarlos solo se ve en la CI (job formal); aquí se comprueba que los ficheros
versionados son los que el generador produce hoy y que sus expectativas son las de la spec.
"""

from __future__ import annotations

import datetime as dt
import json
from collections.abc import Callable
from dataclasses import replace
from typing import Any

import pytest

from story_maker.formal.chronology import Chronology, ChronologyEvent, Presence
from story_maker.formal.generator import generate_chronology_file
from story_maker.settings import ROOT

PRUEBAS = ROOT / "lean" / "pruebas"
K_CI = 3  # k fijo de los ficheros versionados
LIBRARY_THEOREMS = [f"Chronology.compruebaT{n}_decide" for n in range(1, 6)]


def ev(
    id_: int,
    moment: dt.datetime,
    *presences: Presence,
    place: int = 21,
    chapter: int | None = None,
    beat: int | None = None,
    analepsis: bool = False,
    excluded: int | None = None,
) -> ChronologyEvent:
    return ChronologyEvent(
        id=id_,
        moment=moment,
        place_id=place,
        presences=presences,
        type="exclusion" if excluded is not None else "ordinary",
        excluded_character_id=excluded,
        analepsis=analepsis,
        origin="brief" if chapter is None else "recorded",
        chapter=chapter,
        beat=beat if chapter is not None else None,
    )


def at(year: int, month: int, day: int, hour: int = 12, minute: int = 0) -> dt.datetime:
    return dt.datetime(year, month, day, hour, minute)


P = Presence
A, B, C, D = 61, 62, 63, 64

# Fixture + eventos añadidos → nombre del fichero y lo que la CI espera de él.
Extra = Callable[[], tuple[ChronologyEvent, ...]]
CASES: dict[str, tuple[Extra, dict[str, Any]]] = {
    "dorado.lean": (lambda: (), {"resultado": "passed"}),
    # 007-C21: dos violaciones sembradas de un solo invariante; a < b < c < d y p < q.
    "negativo-T1.lean": (
        lambda: (
            ev(A, at(2026, 4, 10, 12), chapter=4, beat=1),
            ev(B, at(2026, 4, 10, 11), chapter=4, beat=2),
            ev(C, at(2026, 6, 10, 12), chapter=6, beat=1),
            ev(D, at(2026, 6, 10, 11), chapter=6, beat=3),
        ),
        {"resultado": "failed", "testigos": {"T1": [A, B]}},
    ),
    "negativo-T2.lean": (
        lambda: (ev(A, at(2000, 5, 14), P(11, 11)), ev(C, at(2010, 1, 1), P(11, 25))),
        {"resultado": "failed", "testigos": {"T2": [11, A, 11, 10]}},
    ),
    "negativo-T3.lean": (
        lambda: (
            ev(A, at(2015, 3, 3), P(11), place=21),
            ev(B, at(2015, 3, 3), P(11), place=22),
            ev(C, at(2016, 4, 4), P(13), place=21),
            ev(D, at(2016, 4, 4), P(13), place=22),
        ),
        {"resultado": "failed", "testigos": {"T3": [11, A, B]}},
    ),
    "negativo-T4.lean": (
        lambda: (
            ev(A, at(2026, 4, 1), excluded=13),
            ev(C, at(2026, 5, 1), P(13)),
            ev(D, at(2026, 6, 1), P(13)),
        ),
        {"resultado": "failed", "testigos": {"T4": [13, A, C]}},
    ),
    "negativo-T5.lean": (
        lambda: (ev(B, at(1985, 1, 1), P(11)), ev(D, at(1989, 1, 1), P(11))),
        {"resultado": "failed", "testigos": {"T5": [11, B]}},
    ),
    # 007-C22: los límites de cada invariante.
    "limite-T1-mismo-momento.lean": (
        lambda: (
            ev(A, at(2026, 4, 1), chapter=3, beat=1),
            ev(B, at(2026, 4, 1), chapter=3, beat=2),
        ),
        {"resultado": "passed"},
    ),
    "limite-T1-minuto-anterior.lean": (
        lambda: (
            ev(A, at(2026, 4, 1, 12, 0), chapter=3, beat=1),
            ev(B, at(2026, 4, 1, 11, 59), chapter=3, beat=2),
        ),
        {"resultado": "failed", "testigos": {"T1": [A, B]}},
    ),
    "limite-T1-analepsis.lean": (
        lambda: (
            ev(A, at(2026, 4, 1), chapter=3, beat=1),
            ev(B, at(2020, 1, 1), chapter=3, beat=2, analepsis=True),
        ),
        {"resultado": "passed"},
    ),
    "limite-T1-mismo-beat.lean": (
        lambda: (
            ev(A, at(2026, 4, 2), chapter=3, beat=1),
            ev(B, at(2026, 4, 1), chapter=3, beat=1),
        ),
        {"resultado": "passed"},
    ),
    "limite-T1-brief-anterior.lean": (lambda: (ev(A, at(1970, 1, 1)),), {"resultado": "passed"}),
    "limite-T2-dia-antes-del-cumpleanos.lean": (
        lambda: (ev(A, at(2000, 5, 13), P(11, 10)),),
        {"resultado": "failed", "testigos": {"T2": [11, A, 10, 9]}},
    ),
    "limite-T2-dia-antes-edad-anterior.lean": (
        lambda: (ev(A, at(2000, 5, 13), P(11, 9)),),
        {"resultado": "passed"},
    ),
    "limite-T2-cumpleanos-a-las-0.lean": (
        lambda: (ev(A, at(2000, 5, 14, 0, 0), P(11, 10)),),
        {"resultado": "passed"},
    ),
    "limite-T2-29-febrero-el-28.lean": (
        lambda: (ev(A, at(2007, 2, 28), P(12, 71)),),
        {"resultado": "failed", "testigos": {"T2": [12, A, 71, 70]}},
    ),
    "limite-T2-29-febrero-el-1-de-marzo.lean": (
        lambda: (ev(A, at(2007, 3, 1), P(12, 71)),),
        {"resultado": "passed"},
    ),
    "limite-T2-sin-nacimiento.lean": (
        lambda: (ev(A, at(2026, 4, 1), P(13, 99)),),
        {"resultado": "passed"},
    ),
    "limite-T3-mismo-lugar.lean": (
        lambda: (ev(A, at(2015, 3, 3), P(11), place=21), ev(B, at(2015, 3, 3), P(11), place=21)),
        {"resultado": "passed"},
    ),
    "limite-T3-lugares-distintos.lean": (
        lambda: (ev(A, at(2015, 3, 3), P(11), place=21), ev(B, at(2015, 3, 3), P(11), place=22)),
        {"resultado": "failed", "testigos": {"T3": [11, A, B]}},
    ),
    "limite-T3-un-minuto-despues.lean": (
        lambda: (
            ev(A, at(2015, 3, 3, 12, 0), P(11), place=21),
            ev(B, at(2015, 3, 3, 12, 1), P(11), place=22),
        ),
        {"resultado": "passed"},
    ),
    "limite-T4-en-su-evento-excluyente.lean": (
        lambda: (ev(A, at(2026, 4, 1), P(13), excluded=13),),
        {"resultado": "passed"},
    ),
    "limite-T4-mismo-momento-y-lugar.lean": (
        lambda: (ev(A, at(2010, 9, 1), P(12), place=22),),
        {"resultado": "passed"},
    ),
    "limite-T4-minuto-posterior.lean": (
        lambda: (ev(A, at(2010, 9, 1, 12, 1), P(12), place=22),),
        {"resultado": "failed", "testigos": {"T4": [12, 32, A]}},
    ),
    "limite-T4-minuto-posterior-analepsis.lean": (
        lambda: (ev(A, at(2010, 9, 1, 12, 1), P(12), place=22, chapter=3, beat=1, analepsis=True),),
        {"resultado": "failed", "testigos": {"T4": [12, 32, A]}},
    ),
    "limite-T4-analepsis-anterior.lean": (
        lambda: (ev(A, at(2009, 1, 1), P(12), chapter=3, beat=1, analepsis=True),),
        {"resultado": "passed"},
    ),
    "limite-T5-nacimiento-a-las-0.lean": (
        lambda: (ev(A, at(1990, 5, 14, 0, 0), P(11)),),
        {"resultado": "passed"},
    ),
    "limite-T5-dia-anterior-23-59.lean": (
        lambda: (ev(A, at(1990, 5, 13, 23, 59), P(11)),),
        {"resultado": "failed", "testigos": {"T5": [11, A]}},
    ),
    "limite-T5-sin-nacimiento.lean": (
        lambda: (ev(A, at(1900, 1, 1), P(13)),),
        {"resultado": "passed"},
    ),
}

THEOREM_T1 = (
    "theorem cumpleT1 : T1 cronologia := (compruebaT1_decide cronologia).mp (by decide +kernel)"
)


def expected_files(chronology: Chronology) -> dict[str, str]:
    """Todo lo que `lean/pruebas/` debe contener, salvo `esperado.json`."""
    files = {
        name: generate_chronology_file(
            replace(chronology, events=chronology.events + extra()), k=K_CI
        )
        for name, (extra, _) in CASES.items()
    }
    golden = files["dorado.lean"]
    # 007-C24: los dos controles de la auditoría de axiomas, sobre el dorado.
    files["control-sorry.lean"] = golden.replace(
        THEOREM_T1, "theorem cumpleT1 : T1 cronologia := sorry"
    )
    files["control-axioma.lean"] = golden.replace(
        THEOREM_T1,
        "axiom trampa : compruebaT1 cronologia = true\n"
        "theorem cumpleT1 : T1 cronologia := (compruebaT1_decide cronologia).mp trampa",
    )
    # 007-C23: la auditoría de los teoremas generales de la biblioteca.
    files["biblioteca.lean"] = "import Chronology\n\n" + "".join(
        f"#print axioms {name}\n" for name in LIBRARY_THEOREMS
    )
    return files


def expectations() -> dict[str, dict[str, Any]]:
    expected = {name: expectation for name, (_, expectation) in CASES.items()}
    expected["control-sorry.lean"] = {"resultado": "error", "compila": False, "motivo": ["sorryAx"]}
    expected["control-axioma.lean"] = {"resultado": "error", "compila": True, "motivo": ["trampa"]}
    expected["biblioteca.lean"] = {"auditoria": LIBRARY_THEOREMS}
    return expected


def test_the_golden_file_is_byte_for_byte_the_generator_output_for_the_fixture(
    chronology: Chronology,
) -> None:
    golden = (PRUEBAS / "dorado.lean").read_bytes()

    assert golden == generate_chronology_file(chronology, k=K_CI).encode("utf-8")


@pytest.mark.parametrize("name", sorted(expectations()))
def test_each_ci_file_is_what_the_generator_writes_today(chronology: Chronology, name: str) -> None:
    assert (PRUEBAS / name).read_bytes() == expected_files(chronology)[name].encode("utf-8")


def test_the_ci_expects_of_each_file_what_the_spec_says() -> None:
    written = json.loads((PRUEBAS / "esperado.json").read_text(encoding="utf-8"))

    assert written == expectations()
    assert sorted(p.name for p in PRUEBAS.glob("*.lean")) == sorted(expectations())


def test_the_control_files_differ_from_the_golden_one_only_in_the_first_theorem(
    chronology: Chronology,
) -> None:
    files = expected_files(chronology)

    assert THEOREM_T1 in files["dorado.lean"]
    for control in ("control-sorry.lean", "control-axioma.lean"):
        assert THEOREM_T1 not in files[control]
        assert files[control] != files["dorado.lean"]
