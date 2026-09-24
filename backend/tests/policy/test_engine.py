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


def test_entrada_user_deniega_solo_para_su_cliente() -> None:
    entradas = [EntradaProhibida(term="marta", type="word", level="user", owner="cliente-a")]
    peticion_a = PeticionDePolitica(
        origen="policy_hook",
        cliente="cliente-a",
        campos=[CampoNarrativo(path="c", narrativo=True, texto="la protagonista se llama Marta")],
        banned_entries=entradas,
    )
    peticion_b = peticion_a.model_copy(update={"cliente": "cliente-b"})

    assert decide(peticion_a).decision == "deny"
    assert decide(peticion_a).detail == [{"term": "marta", "level": "user", "variant": "Marta"}]
    assert decide(peticion_b).decision == "allow"


def test_entrada_novel_deniega_solo_para_su_novela() -> None:
    entradas = [EntradaProhibida(term="cristina", type="word", level="novel", owner="n1")]
    peticion_n1 = PeticionDePolitica(
        origen="policy_hook",
        cliente="cliente-a",
        novela="n1",
        campos=[CampoNarrativo(path="c", narrativo=True, texto="la ex se llamaba Cristina")],
        banned_entries=entradas,
    )
    peticion_n2 = peticion_n1.model_copy(update={"novela": "n2"})

    assert decide(peticion_n1).decision == "deny"
    assert decide(peticion_n1).detail[0]["level"] == "novel"
    assert decide(peticion_n2).decision == "allow"


def test_un_tema_coincide_por_cualquiera_de_sus_palabras_clave() -> None:
    entradas = [
        EntradaProhibida(
            term="divorcio", type="topic", level="global", keywords=["separación", "custodia"]
        )
    ]
    d1 = decide(_peticion("hablaron de la separación", entradas))
    d2 = decide(_peticion("pidió la custodia", entradas))
    d3 = decide(_peticion("se fueron de viaje", entradas))

    assert d1.decision == "deny"
    assert d1.detail == [{"term": "divorcio", "level": "global", "variant": "separación"}]
    assert d2.decision == "deny"
    assert d2.detail == [{"term": "divorcio", "level": "global", "variant": "custodia"}]
    assert d3.decision == "allow"


def test_sin_coincidencia_permite() -> None:
    entradas = [
        EntradaProhibida(term="idiota", type="word", level="global"),
        EntradaProhibida(term="marta", type="word", level="user", owner="cliente-1"),
        EntradaProhibida(term="cristina", type="word", level="novel", owner="novela-1"),
    ]
    decision = decide(_peticion("un texto tranquilo sin nada raro", entradas))

    assert decision.decision == "allow"
    assert decision.rule is None
