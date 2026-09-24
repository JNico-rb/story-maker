"""MotorDePoliticas: decide allow | deny | flag ante una PeticionDePolitica (definitions.md §7)."""

from story_maker.policy.engine import decide
from story_maker.policy.types import CampoNarrativo, EntradaProhibida, PeticionDePolitica


def _peticion(texto: str, entradas: list[EntradaProhibida] | None = None) -> PeticionDePolitica:
    return PeticionDePolitica(
        origen="policy_hook",
        cliente="cliente-1",
        campos=[CampoNarrativo(path="capitulo.texto", narrativo=True, texto=texto)],
        banned_entries=entradas or [],
    )


def test_entrada_global_deniega() -> None:
    entradas = [EntradaProhibida(term="idiota", type="word", level="global")]
    decision = decide(_peticion("eres un idiota", entradas))

    assert decision.decision == "deny"
    assert decision.rule == "palabras-prohibidas"
    assert decision.detail == [{"term": "idiota", "level": "global", "variant": "idiota"}]


def test_sin_coincidencia_permite() -> None:
    entradas = [
        EntradaProhibida(term="idiota", type="word", level="global"),
        EntradaProhibida(term="marta", type="word", level="user", owner="cliente-1"),
        EntradaProhibida(term="cristina", type="word", level="novel", owner="novela-1"),
    ]
    decision = decide(_peticion("un texto tranquilo sin nada raro", entradas))

    assert decision.decision == "allow"
    assert decision.rule is None
