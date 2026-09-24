"""Construcción del `VerificadorFormal` desde los ajustes (007-C18, 007-I8)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from story_maker.formal.github import GithubFormalVerifier
from story_maker.formal.local import LocalFormalVerifier
from story_maker.formal.verifier import FormalVerifierConfigError, make_formal_verifier
from story_maker.settings import Settings, load_settings

GITHUB = {
    "github_repository": "cliente/story-maker",
    "lean_workflow": "verificar-cronologia.yml",
    "github_token": "TU_CLAVE_AQUI",
}
NAMES = {
    "github_repository": "GITHUB_REPOSITORY",
    "lean_workflow": "LEAN_WORKFLOW",
    "github_token": "GITHUB_TOKEN",
}


@pytest.fixture
def local_settings(tmp_path: Path) -> Settings:
    env = {
        "JWT_SECRET": "x" * 32,
        "FORMAL_VERIFIER": "local",
        "STORY_MAKER_DATA_DIR": str(tmp_path / "data"),
    }
    return load_settings(env=env, env_file=tmp_path / "no-existe.env")


def test_the_local_mode_is_built_on_the_data_dir(local_settings: Settings) -> None:
    verifier = make_formal_verifier(local_settings, timeout_seconds=900)

    assert isinstance(verifier, LocalFormalVerifier)
    assert verifier.data_dir == local_settings.data_dir
    assert verifier.timeout_seconds == 900


def test_the_github_mode_is_built_with_its_three_settings(local_settings: Settings) -> None:
    settings = replace(local_settings, formal_verifier="github", **GITHUB)

    verifier = make_formal_verifier(settings, timeout_seconds=900)

    assert isinstance(verifier, GithubFormalVerifier)
    assert verifier.repository == GITHUB["github_repository"]
    assert verifier.workflow == GITHUB["lean_workflow"]
    assert "TU_CLAVE_AQUI" not in repr(verifier)


@pytest.mark.parametrize("missing", sorted(GITHUB))
def test_the_github_mode_without_one_of_its_settings_is_not_built(
    local_settings: Settings, missing: str
) -> None:
    settings = replace(local_settings, formal_verifier="github", **{**GITHUB, missing: None})

    with pytest.raises(FormalVerifierConfigError) as excinfo:
        make_formal_verifier(settings, timeout_seconds=900)

    message = str(excinfo.value)
    assert NAMES[missing] in message
    for value in GITHUB.values():
        assert value not in message
