"""Tests of the chronology generator and of the verdict, runnable without Lean.

    python3 -m unittest discover -s scripts -p "test_*.py"   (from lean/)
"""
from __future__ import annotations

import base64
import copy
import gzip
import json
import unittest
from pathlib import Path

import generate
import verify

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def positive() -> dict:
    return json.loads((EXAMPLES / "positive.json").read_text(encoding="utf-8"))


def event(**changes: object) -> dict:
    base = {
        "id": 1, "moment": "2026-03-01T09:00", "place_id": 7, "characters": [1],
        "type": "ordinary", "excluded_character_id": None, "declared_ages": {},
        "chapter_number": 1, "beat_number": 1, "flashback": False,
    }
    base.update(changes)
    return base


def chronology(events: list[dict], characters: list[dict] | None = None) -> dict:
    if characters is None:
        characters = [{"id": 1, "birth_date": "1990-06-15"}]
    return {"version": 1, "characters": characters, "events": events}


class ParseAccepts(unittest.TestCase):
    def test_the_positive_example(self) -> None:
        parsed = generate.parse(positive())
        self.assertEqual(len(parsed.characters), 4)
        self.assertEqual(len(parsed.events), 11)
        self.assertEqual(parsed.characters[1].birth, generate.Date(1940, 2, 29))
        self.assertIsNone(parsed.characters[2].birth)

    def test_every_example_file(self) -> None:
        for path in sorted(EXAMPLES.glob("*.json")):
            if path.name != "expected.json":
                with self.subTest(path.name):
                    generate.parse(json.loads(path.read_text(encoding="utf-8")))

    def test_years_shifted_past_9999(self) -> None:
        data = chronology([event(moment="10026-03-01T09:00")], [{"id": 1, "birth_date": "9990-06-15"}])
        parsed = generate.parse(data)
        self.assertEqual(parsed.events[0].moment, generate.Moment(10026, 3, 1, 9, 0))

    def test_a_background_event(self) -> None:
        parsed = generate.parse(chronology([event(chapter_number=None, beat_number=None)]))
        self.assertIsNone(parsed.events[0].narration)

    def test_declared_ages_and_exclusion(self) -> None:
        data = chronology([event(type="exclusion", excluded_character_id=1, declared_ages={"1": 35})])
        parsed = generate.parse(data)
        self.assertEqual(parsed.events[0].excluded, 1)
        self.assertEqual(parsed.events[0].ages, ((1, 35),))


class ParseRejects(unittest.TestCase):
    def assertRejected(self, data: object, fragment: str) -> None:
        with self.assertRaises(generate.ChronologyError) as caught:
            generate.parse(data)
        self.assertIn(fragment, str(caught.exception))

    def test_a_document_that_is_not_an_object(self) -> None:
        self.assertRejected([], "object")

    def test_another_version(self) -> None:
        data = positive()
        data["version"] = 2
        self.assertRejected(data, "version")

    def test_text_fields_so_no_statement_leaves_the_backend(self) -> None:
        self.assertRejected(chronology([event(statement="La abuela sopla las velas")]), "statement")

    def test_a_missing_field(self) -> None:
        data = chronology([event()])
        del data["events"][0]["flashback"]
        self.assertRejected(data, "flashback")

    def test_a_boolean_where_an_id_goes(self) -> None:
        self.assertRejected(chronology([event(id=True)]), "events[0].id")

    def test_a_negative_id(self) -> None:
        self.assertRejected(chronology([event(place_id=-3)]), "events[0].place_id")

    def test_repeated_ids(self) -> None:
        self.assertRejected(chronology([event(), event()]), "repeated")
        characters = [{"id": 1, "birth_date": None}, {"id": 1, "birth_date": None}]
        self.assertRejected(chronology([event()], characters), "repeated")

    def test_an_unknown_character_present(self) -> None:
        self.assertRejected(chronology([event(characters=[1, 9])]), "events[0].characters")

    def test_a_character_present_twice(self) -> None:
        self.assertRejected(chronology([event(characters=[1, 1])]), "events[0].characters")

    def test_29_february_of_a_common_year(self) -> None:
        self.assertRejected(chronology([event(moment="2026-02-29T09:00")]), "events[0].moment")

    def test_impossible_dates_and_times(self) -> None:
        for moment in ["2026-13-01T09:00", "2026-04-31T09:00", "2026-03-01T24:00", "2026-03-01T09:60",
                       "2026-03-01 09:00", "26-03-01T09:00", "2026-3-1T09:00"]:
            with self.subTest(moment):
                self.assertRejected(chronology([event(moment=moment)]), "events[0].moment")
        self.assertRejected(chronology([event()], [{"id": 1, "birth_date": "1990-02-30"}]),
                            "characters[0].birth_date")

    def test_an_exclusion_without_its_character(self) -> None:
        self.assertRejected(chronology([event(type="exclusion")]), "excluded_character_id")

    def test_an_ordinary_event_that_excludes(self) -> None:
        self.assertRejected(chronology([event(excluded_character_id=1)]), "excluded_character_id")

    def test_an_unknown_excluded_character(self) -> None:
        self.assertRejected(chronology([event(type="exclusion", excluded_character_id=9)]), "excluded_character_id")

    def test_an_unknown_type(self) -> None:
        self.assertRejected(chronology([event(type="death")]), "events[0].type")

    def test_bad_declared_ages(self) -> None:
        self.assertRejected(chronology([event(declared_ages={"x": 3})]), "declared_ages")
        self.assertRejected(chronology([event(declared_ages={"9": 3})]), "declared_ages")
        self.assertRejected(chronology([event(declared_ages={"1": -1})]), "declared_ages")

    def test_a_chapter_without_its_beat(self) -> None:
        self.assertRejected(chronology([event(beat_number=None)]), "beat_number")
        self.assertRejected(chronology([event(chapter_number=None)]), "beat_number")

    def test_a_flashback_that_is_not_a_boolean(self) -> None:
        self.assertRejected(chronology([event(flashback=0)]), "events[0].flashback")

    def test_too_many_events(self) -> None:
        events = [event(id=i) for i in range(generate.MAX_EVENTS + 1)]
        self.assertRejected(chronology(events), "events")


class Render(unittest.TestCase):
    def test_a_small_chronology(self) -> None:
        data = chronology(
            [event(id=5, declared_ages={"1": 35}),
             event(id=6, moment="2003-09-01T12:00", place_id=None, characters=[], chapter_number=None,
                   beat_number=None, flashback=True, type="exclusion", excluded_character_id=2)],
            [{"id": 1, "birth_date": "1990-06-15"}, {"id": 2, "birth_date": None}],
        )
        expected = "\n".join([
            "import Chronology.Model",
            "",
            "/-! Generated by scripts/generate.py from the chronology JSON of lean/README.md. -/",
            "",
            "namespace Input",
            "",
            "def chronology : Chronology where",
            "  characters := [",
            "    { id := 1, birth := some (Chronology.Date.mk 1990 6 15) },",
            "    { id := 2, birth := none }",
            "  ]",
            "  events := [",
            "    { id := 5, moment := Chronology.Moment.mk 2026 3 1 9 0, place := some 7, present := [1],"
            " narration := some (Chronology.Position.mk 1 1), flashback := false, excluded := none,"
            " ages := [Chronology.DeclaredAge.mk 1 35] },",
            "    { id := 6, moment := Chronology.Moment.mk 2003 9 1 12 0, place := none, present := [],"
            " narration := none, flashback := true, excluded := some 2, ages := [] }",
            "  ]",
            "",
            "end Input",
            "",
        ])
        self.assertEqual(generate.render(generate.parse(data)), expected)

    def test_empty_lists(self) -> None:
        text = generate.render(generate.parse(chronology([], [])))
        self.assertIn("  characters := []\n  events := []\n", text)


class Decode(unittest.TestCase):
    @staticmethod
    def encode(raw: bytes) -> str:
        return base64.b64encode(gzip.compress(raw)).decode("ascii")

    def test_round_trip(self) -> None:
        data = positive()
        self.assertEqual(generate.decode(self.encode(json.dumps(data).encode("utf-8"))), data)

    def test_rejects_what_is_not_base64_gzip_json(self) -> None:
        for encoded in ["%%%", base64.b64encode(b"plain").decode("ascii"), self.encode(b"{not json")]:
            with self.subTest(encoded):
                with self.assertRaises(generate.ChronologyError):
                    generate.decode(encoded)

    def test_rejects_a_bomb(self) -> None:
        with self.assertRaises(generate.ChronologyError):
            generate.decode(self.encode(b" " * (generate.MAX_JSON_BYTES + 1)))


def entries(failing: dict[str, dict] | None = None) -> list[dict]:
    failing = failing or {}
    return [
        {"invariant": name, "holds": name not in failing, "witness": failing.get(name)}
        for name in verify.INVARIANTS
    ]


class Combine(unittest.TestCase):
    def test_pass(self) -> None:
        result = verify.combine(True, entries())
        self.assertEqual(result["status"], "pass")
        self.assertIsNone(result["invariant"])
        self.assertIsNone(result["witness"])
        self.assertEqual(verify.exit_code(result), 0)

    def test_fail_names_the_first_violated_invariant(self) -> None:
        witness3 = {"events": [4, 5], "characters": [1]}
        witness1 = {"events": [2, 3], "characters": []}
        result = verify.combine(False, entries({"t3-dos-lugares": witness3, "t1-orden": witness1}))
        self.assertEqual(result["status"], "fail")
        self.assertEqual(result["invariant"], "t1-orden")
        self.assertEqual(result["witness"], witness1)
        self.assertEqual([e["holds"] for e in result["invariants"]], [False, True, False, True])
        self.assertEqual(verify.exit_code(result), 1)

    def test_theorems_and_report_that_disagree_are_an_error(self) -> None:
        witness = {"events": [4], "characters": [1]}
        self.assertEqual(verify.combine(True, entries({"t2-edad": witness}))["status"], "error")
        self.assertEqual(verify.combine(False, entries())["status"], "error")

    def test_a_malformed_report_is_an_error(self) -> None:
        self.assertEqual(verify.combine(True, [{"invariant": "t1-orden"}])["status"], "error")
        self.assertEqual(verify.combine(True, entries()[:3])["status"], "error")
        self.assertEqual(verify.exit_code(verify.error_result("boom")), 2)


class Examples(unittest.TestCase):
    def test_expected_covers_every_example(self) -> None:
        expected = json.loads((EXAMPLES / "expected.json").read_text(encoding="utf-8"))
        files = {p.name for p in EXAMPLES.glob("*.json")} - {"expected.json"}
        self.assertEqual(set(expected), files)
        self.assertEqual([e["status"] for e in expected.values()].count("pass"), 1)
        self.assertEqual({e.get("invariant") for e in expected.values()} - {None}, set(verify.INVARIANTS))

    def test_each_negative_changes_the_positive_in_one_event(self) -> None:
        base = positive()
        for path in sorted(EXAMPLES.glob("negative-*.json")):
            with self.subTest(path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                changed = [a["id"] for a, b in zip(base["events"], data["events"]) if a != b]
                self.assertEqual(len(changed), 1)
                self.assertEqual(copy.deepcopy(base["characters"]), data["characters"])


if __name__ == "__main__":
    unittest.main()
