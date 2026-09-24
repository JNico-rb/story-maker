"""Sesiones concurrentes no comparten estado (003-I8)."""

from __future__ import annotations

import asyncio
import datetime as dt
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from story_maker.agents.fake import Call, FakeAgent, Say, Script
from story_maker.agents.port import AgentPort, Defect, SessionRequest
from story_maker.agents.usage import Usage
from story_maker.policy.types import DecisionDePolitica, PeticionDePolitica
from story_maker.store.models import Novel

USAGE = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)


def other_novel(session_factory: sessionmaker[Session], user_id: int) -> int:
    with session_factory() as session:
        novel = Novel(
            user_id=user_id,
            title=None,
            embedding_model="e5",
            created_at=dt.datetime(2026, 9, 24, 12, 0),
        )
        session.add(novel)
        session.commit()
        return novel.id


async def test_concurrent_sessions_share_no_state(
    port: AgentPort,
    fake: FakeAgent,
    policy: Any,
    session_factory: sessionmaker[Session],
    user_id: int,
    novel_id: int,
    make_request: Callable[..., SessionRequest],
) -> None:
    novels = {"A": novel_id, "B": other_novel(session_factory, user_id)}
    order: list[str] = []

    def rule(request: PeticionDePolitica) -> DecisionDePolitica:
        order.append(next(n for n, i in novels.items() if str(i) == request.novela))
        return DecisionDePolitica(decision="allow")

    policy.rule = rule
    checked: dict[str, list[str]] = {"A": [], "B": []}

    def checks_for(name: str) -> Callable[[BaseModel], list[Defect]]:
        def checks(value: BaseModel) -> list[Defect]:
            checked[name].append(value.model_dump()["text"])
            return []

        return checks

    for name in novels:
        steps = tuple(
            Call("submit_chapter", {"title": name, "text": f"{name}{i}"}) for i in range(3)
        )
        fake.script("writer", "write", Script(steps=(*steps, Say(name)), usage=USAGE))

    results = await asyncio.gather(
        *(
            port.run(
                make_request(
                    "writer", "write", novel_id=novels[name], chapter_checks=checks_for(name)
                )
            )
            for name in novels
        )
    )

    # las dos sesiones se intercalaron
    assert order[:2] == ["A", "B"]
    for name, result in zip(novels, results, strict=True):
        expected = [f"{name}{i}" for i in range(3)]
        assert [c.input["text"] for c in result.calls] == expected
        assert [c.input["text"] for c in result.deliveries] == expected
        assert checked[name] == expected
        assert result.text == name
        requests = [r for r in policy.requests if r.novela == str(novels[name])]
        assert [{c.path: c.texto for c in r.campos}["text"] for r in requests] == expected
