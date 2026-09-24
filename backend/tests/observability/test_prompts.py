"""`prompts push`: sube una versión nueva por rol si y solo si cambia su huella (004-C07/C08/I4)."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import FakeLangfuseClient

from story_maker.observability.prompts import push_prompts

LABEL = "produccion"


def _write_prompt(prompts_dir: Path, role: str, text: str) -> None:
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / f"{role}.md").write_text(text, encoding="utf-8")


# --- C07: sube una versión nueva si cambia la huella del fichero ------------------------------


def test_push_uploads_a_new_version_named_as_the_role_label_with_its_label(
    tmp_path: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    _write_prompt(tmp_path, "writer", "Escribe el capítulo con fidelidad al canon.")

    pushed = push_prompts(tmp_path, fake_langfuse_client, LABEL)

    assert pushed == ["writer"]
    handle = fake_langfuse_client.get_prompt("writer", label=LABEL)
    assert handle.version == 1
    assert handle.text == "Escribe el capítulo con fidelidad al canon."


def test_push_uploads_a_new_version_when_the_role_already_had_one_with_a_different_fingerprint(
    tmp_path: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    fake_langfuse_client.register_prompt(
        "writer", LABEL, version=1, config={"fingerprint": "vieja"}
    )
    _write_prompt(tmp_path, "writer", "Texto nuevo del prompt del writer.")

    pushed = push_prompts(tmp_path, fake_langfuse_client, LABEL)

    assert pushed == ["writer"]
    assert fake_langfuse_client.get_prompt("writer", label=LABEL).version == 2


# --- C08: no sube si la huella no cambió -------------------------------------------------------


def test_push_uploads_nothing_when_the_fingerprint_is_unchanged(
    tmp_path: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    _write_prompt(tmp_path, "editor", "Revisa el capítulo con la rúbrica del rol.")
    push_prompts(tmp_path, fake_langfuse_client, LABEL)

    pushed_again = push_prompts(tmp_path, fake_langfuse_client, LABEL)

    assert pushed_again == []
    assert fake_langfuse_client.get_prompt("editor", label=LABEL).version == 1


# --- I4: sube si y solo si cambia la huella ------------------------------------------------


def test_push_uploads_exactly_on_the_pushes_where_the_fingerprint_actually_changed(
    tmp_path: Path, fake_langfuse_client: FakeLangfuseClient
) -> None:
    _write_prompt(tmp_path, "planner", "v1 del prompt del planner.")

    first = push_prompts(tmp_path, fake_langfuse_client, LABEL)
    second_unchanged = push_prompts(tmp_path, fake_langfuse_client, LABEL)
    _write_prompt(tmp_path, "planner", "v2 del prompt del planner.")
    third_changed = push_prompts(tmp_path, fake_langfuse_client, LABEL)
    fourth_unchanged = push_prompts(tmp_path, fake_langfuse_client, LABEL)

    assert (first, second_unchanged, third_changed, fourth_unchanged) == (
        ["planner"],
        [],
        ["planner"],
        [],
    )
    assert fake_langfuse_client.get_prompt("planner", label=LABEL).version == 2
