"""`config.json`: validez y valores de §15.4 (001-C01); validación entera (001-C02)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from story_maker.config import ConfigError, load_config, parse_config
from story_maker.settings import ROOT

VALID = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))


def _errors(data: Any) -> list[str]:
    with pytest.raises(ConfigError) as excinfo:
        parse_config(data)
    return excinfo.value.errors


def test_the_repository_config_json_is_valid_and_carries_the_section_15_4_values() -> None:
    config = parse_config(VALID)

    assert config.token_ceiling == 100000
    assert config.api_wait_seconds == 30
    assert config.max_retries == {"chapter": 3, "plan": 2, "gate_cycles": 2, "change": 2}
    assert config.max_resumes == 3
    assert config.session_timeout_seconds == 600
    assert config.verifier_timeout_seconds == 900
    assert config.max_mandatory_elements == 8
    assert config.access_token_hours == 24
    assert config.confirmation_minutes == 15
    assert config.roles["planner"].model == "claude-haiku-4-5"
    assert config.roles["writer"].model == "claude-haiku-4-5"
    assert config.roles["judge"].model == "claude-haiku-4-5"
    assert config.roles["interviewer"].model == "claude-haiku-4-5"
    assert config.roles["extractor"].model == "claude-haiku-4-5"
    assert config.roles["editor"].model == "claude-haiku-4-5"
    assert config.roles["visual_reviewer"].model == "claude-haiku-4-5"
    assert config.roles["interviewer"].max_turns == 4
    assert config.roles["interviewer"].max_output_tokens == 2000
    assert config.pricing["claude-sonnet-5"].input == 2.00
    assert config.pricing["claude-sonnet-5"].cache_write == 2.50
    assert config.pricing["claude-haiku-4-5"].output == 5.00
    assert set(config.thresholds) == {
        "fidelidad-canon",
        "cumple-beats",
        "personalizacion-natural",
        "prosa",
        "tono",
        "continuidad",
        "coherencia-personajes",
        "arco-y-final",
        "ritmo",
        "no-cliche",
    }
    assert all(threshold == 3 for threshold in config.thresholds.values())
    assert config.readability_targets["children"].sentence_length == 12
    assert config.readability_targets["children"].fernandez_huerta == 80
    assert config.top_k == {"writer": 8, "editor": 8}
    assert config.embedding_model


def _mutated(path: tuple[str, ...], value: Any) -> dict[str, Any]:
    data = copy.deepcopy(VALID)
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return data


def _deleted(path: tuple[str, ...]) -> dict[str, Any]:
    data = copy.deepcopy(VALID)
    target = data
    for key in path[:-1]:
        target = target[key]
    del target[path[-1]]
    return data


def test_unchanged_config_is_valid() -> None:
    parse_config(VALID)


def test_token_ceiling_100000_is_valid() -> None:
    parse_config(_mutated(("operation", "token_ceiling"), 100000))


def test_token_ceiling_100001_is_rejected_naming_the_key_and_the_maximum() -> None:
    errors = _errors(_mutated(("operation", "token_ceiling"), 100001))

    assert any("token_ceiling" in e and "100000" in e for e in errors)


def test_token_ceiling_5000_is_valid() -> None:
    parse_config(_mutated(("operation", "token_ceiling"), 5000))


def test_token_ceiling_0_is_rejected() -> None:
    errors = _errors(_mutated(("operation", "token_ceiling"), 0))

    assert any("token_ceiling" in e for e in errors)


def test_missing_roles_judge_is_rejected_naming_the_missing_key() -> None:
    errors = _errors(_deleted(("operation", "roles", "judge")))

    assert any("operation.roles.judge" in e for e in errors)


def test_an_unknown_role_is_rejected_as_an_unknown_key() -> None:
    data = _mutated(
        ("operation", "roles", "narrator"), {"model": "x", "max_turns": 1, "max_output_tokens": 1}
    )

    errors = _errors(data)

    assert any("operation.roles.narrator" in e and "desconocida" in e for e in errors)


def test_a_role_model_without_a_pricing_entry_is_rejected_naming_the_model() -> None:
    data = _mutated(("operation", "roles", "writer", "model"), "claude-unknown")

    errors = _errors(data)

    assert any("claude-unknown" in e for e in errors)


def test_a_price_for_a_model_no_role_uses_is_valid() -> None:
    data = copy.deepcopy(VALID)
    data["operation"]["pricing"]["claude-unused"] = {
        "input": 1.0,
        "output": 1.0,
        "cache_read": 1.0,
        "cache_write": 1.0,
    }

    parse_config(data)


def test_a_price_without_cache_write_is_rejected() -> None:
    errors = _errors(_deleted(("operation", "pricing", "claude-sonnet-5", "cache_write")))

    assert any("cache_write" in e for e in errors)


def test_a_price_with_a_negative_value_is_rejected() -> None:
    errors = _errors(_mutated(("operation", "pricing", "claude-sonnet-5", "input"), -1))

    assert any("claude-sonnet-5" in e and "input" in e for e in errors)


def test_a_price_input_of_0_is_valid() -> None:
    parse_config(_mutated(("operation", "pricing", "claude-sonnet-5", "input"), 0))


def test_missing_threshold_continuidad_is_rejected() -> None:
    errors = _errors(_deleted(("quality", "thresholds", "continuidad")))

    assert any("continuidad" in e for e in errors)


@pytest.mark.parametrize("value", [1, 5])
def test_threshold_tono_at_the_edges_is_valid(value: int) -> None:
    parse_config(_mutated(("quality", "thresholds", "tono"), value))


@pytest.mark.parametrize("value", [0, 6])
def test_threshold_tono_outside_1_to_5_is_rejected(value: int) -> None:
    errors = _errors(_mutated(("quality", "thresholds", "tono"), value))

    assert any("tono" in e for e in errors)


def test_missing_readability_target_teen_is_rejected() -> None:
    errors = _errors(_deleted(("quality", "readability_targets", "teen")))

    assert any("teen" in e for e in errors)


@pytest.mark.parametrize("key", ["sentence_length", "fernandez_huerta"])
def test_readability_target_children_at_0_is_rejected(key: str) -> None:
    errors = _errors(_mutated(("quality", "readability_targets", "children", key), 0))

    assert any(key in e for e in errors)


def test_max_retries_chapter_0_is_valid() -> None:
    parse_config(_mutated(("operation", "max_retries", "chapter"), 0))


def test_max_retries_chapter_negative_is_rejected() -> None:
    errors = _errors(_mutated(("operation", "max_retries", "chapter"), -1))

    assert any("chapter" in e for e in errors)


def test_max_resumes_0_is_valid() -> None:
    parse_config(_mutated(("operation", "max_resumes"), 0))


def test_max_resumes_negative_is_rejected() -> None:
    errors = _errors(_mutated(("operation", "max_resumes"), -1))

    assert any("max_resumes" in e for e in errors)


@pytest.mark.parametrize("key", ["max_turns", "max_output_tokens"])
def test_role_editor_field_at_0_is_rejected(key: str) -> None:
    errors = _errors(_mutated(("operation", "roles", "editor", key), 0))

    assert any(key in e for e in errors)


@pytest.mark.parametrize(
    "path",
    [
        ("operation", "api_wait_seconds"),
        ("operation", "session_timeout_seconds"),
        ("operation", "verifier_timeout_seconds"),
        ("operation", "access_token_hours"),
        ("operation", "confirmation_minutes"),
        ("operation", "max_mandatory_elements"),
        ("retrieval", "top_k", "writer"),
    ],
)
def test_a_zero_value_of_these_settings_is_rejected(path: tuple[str, ...]) -> None:
    errors = _errors(_mutated(path, 0))

    assert any(path[-1] in e for e in errors)


def test_an_empty_embedding_model_is_rejected() -> None:
    errors = _errors(_mutated(("retrieval", "embedding_model"), ""))

    assert any("embedding_model" in e for e in errors)


def test_an_unknown_key_is_rejected_naming_it() -> None:
    data = _mutated(("operation", "max_retry"), 1)

    errors = _errors(data)

    assert any("max_retry" in e and "desconocida" in e for e in errors)


def test_a_file_that_is_not_json_is_rejected_with_the_path_and_the_error_position(
    tmp_path: Path,
) -> None:
    bad = tmp_path / "config.json"
    bad.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigError) as excinfo:
        load_config(bad)

    (error,) = excinfo.value.errors
    assert str(bad) in error
    assert "línea" in error
    assert "columna" in error


def test_a_config_path_that_does_not_exist_is_rejected_with_the_path(tmp_path: Path) -> None:
    missing = tmp_path / "no-existe.json"

    with pytest.raises(ConfigError) as excinfo:
        load_config(missing)

    (error,) = excinfo.value.errors
    assert str(missing) in error


def test_several_errors_are_reported_together_one_per_key() -> None:
    data = _mutated(("operation", "token_ceiling"), 0)
    data["operation"]["max_resumes"] = -1

    errors = _errors(data)

    assert any("token_ceiling" in e for e in errors)
    assert any("max_resumes" in e for e in errors)
    assert len(errors) >= 2
