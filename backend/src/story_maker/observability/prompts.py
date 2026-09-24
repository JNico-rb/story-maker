"""`story-maker prompts push`: sube una versión nueva por rol si cambia su huella (§13.4)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from story_maker.observability.langfuse_client import LangfuseClientPort
from story_maker.observability.roles import ROLE_LABELS


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def push_prompts(prompts_dir: Path, client: LangfuseClientPort, label: str) -> list[str]:
    """Sube el prompt de cada rol cuyo fichero cambió de huella; devuelve los roles subidos."""
    pushed: list[str] = []
    for identifier, role_label in ROLE_LABELS.items():
        path = prompts_dir / f"{identifier}.md"
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        current = fingerprint(text)
        if current == _current_fingerprint(client, role_label, label):
            continue
        client.create_prompt(
            name=role_label, prompt=text, labels=[label], config={"fingerprint": current}
        )
        pushed.append(identifier)
    return pushed


def _current_fingerprint(client: LangfuseClientPort, name: str, label: str) -> str | None:
    try:
        handle = client.get_prompt(name, label=label)
    except Exception:
        return None
    config = handle.config
    if isinstance(config, dict) and isinstance(config.get("fingerprint"), str):
        return str(config["fingerprint"])
    return None
