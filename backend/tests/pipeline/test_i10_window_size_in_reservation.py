"""011-I10: el tamaño estimado de la ventana entra en la reserva de su sesión
(`AgentPort.reservation`, `pipeline/test_ceiling_reservation.py` ya lo comprueba de punta a
punta con la producción completa; aquí, aislado, para que una ventana más grande sea la única
variable). El estimador es el de `agents/ceiling.py` (003): chars/4 redondeado hacia arriba."""

from __future__ import annotations

from tests.pipeline.conftest import Seed

from story_maker.agents.ceiling import estimate_tokens
from story_maker.agents.port import AgentPort, SessionRequest
from story_maker.observability.port import Trace
from story_maker.pipeline.submissions import submit_chapter_tool


def _request(seed: Seed, message: str) -> SessionRequest:
    return SessionRequest(
        role="writer",
        mode="write",
        user_id=seed.user_id,
        novel_id=seed.novel_id,
        run_id=seed.run_id,
        chapter=1,
        prompt="Prompt del writer",
        prompt_version="v1",
        message=message,
        tools=(submit_chapter_tool(),),
        trace=Trace(key=f"run:{seed.run_id}"),
    )


def test_a_bigger_window_reserves_more_tokens_by_exactly_its_estimated_size(
    port: AgentPort, seed: Seed
) -> None:
    small_message = "x" * 100
    big_message = "x" * 100_000

    small_reservation = port.reservation(_request(seed, small_message))
    big_reservation = port.reservation(_request(seed, big_message))

    assert big_reservation > small_reservation
    assert big_reservation - small_reservation == estimate_tokens(
        len(big_message)
    ) - estimate_tokens(len(small_message))
