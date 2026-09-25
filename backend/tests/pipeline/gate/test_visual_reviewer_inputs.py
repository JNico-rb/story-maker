"""017-C02 · El revisor recibe la dirección de la vista y la forma de lo que entrega, no los
valores (y 017-I2, sobre las entradas que registra el doble)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from sqlalchemy.orm import Session, sessionmaker
from tests.pipeline.conftest import Seed
from tests.pipeline.gate.visual import (
    BASE_URL,
    DEDICATION,
    EXPECTED,
    SECRET,
    TITLE,
    faithful,
    first_sentence,
    job_of,
    make_settings,
    make_stage,
    reviewer_script,
    reviewer_sessions,
    seed_visual,
)

from story_maker.agents.fake import FakeAgent
from story_maker.api.view_tokens import decode_view_token
from story_maker.observability.port import Trace
from story_maker.pipeline.production import Production
from story_maker.validators.visual_review import PARTS


def test_the_reviewer_receives_the_view_address_with_its_token_and_the_shape_to_deliver(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    fake.script("visual_reviewer", None, reviewer_script(faithful()))

    asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    [session] = reviewer_sessions(fake)
    inputs = json.loads(session.request.message)
    url = urlsplit(inputs["url"])
    assert f"{url.scheme}://{url.netloc}" == BASE_URL
    assert url.path == f"/view/versions/{at_gate.version_id}"
    [token] = parse_qs(url.query)["token"]
    now = production.clock()
    assert decode_view_token(token, SECRET, now=now) == at_gate.version_id
    structure = inputs["structure"]
    assert structure["parts"] == list(PARTS)
    assert set(structure["deliver"]) == set(PARTS)
    assert all(structure["deliver"][part] for part in PARTS)
    assert structure["chapters"] == 10
    assert (structure["characters"], structure["places"]) == (2, 2)


def test_no_reviewer_input_carries_a_value_the_code_compares(
    session_factory: sessionmaker[Session],
    at_gate: Seed,
    fake: FakeAgent,
    production: Production,
    trace: Trace,
    tmp_path: Path,
) -> None:
    seed_visual(session_factory, at_gate)
    fake.script("visual_reviewer", None, reviewer_script(faithful()))

    asyncio.run(make_stage(production, make_settings(tmp_path))(job_of(at_gate), trace))

    [session] = reviewer_sessions(fake)
    received = f"{session.request.prompt}\n{session.request.message}".casefold()
    values = [
        TITLE,
        DEDICATION,
        *(c.title for c in EXPECTED.chapters),
        *(first_sentence(c.number) for c in EXPECTED.chapters),
        "palabra",
        *(e.name for e in EXPECTED.ficha),
    ]
    assert [v for v in values if v.casefold() in received] == []
