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


def test_una_tool_fuera_de_la_lista_blanca_del_rol_deniega() -> None:
    d1 = decide(PeticionDePolitica(origen="policy_hook", cliente="c1", rol="writer", tool="Bash"))
    d2 = decide(
        PeticionDePolitica(origen="policy_hook", cliente="c1", rol="editor", tool="submit_chapter")
    )

    assert d1.decision == "deny"
    assert d1.rule == "lista-blanca"
    assert d1.detail == [{"role": "writer", "tool": "Bash"}]
    assert d2.decision == "deny"
    assert d2.rule == "lista-blanca"


def test_una_tool_de_la_lista_blanca_del_rol_sin_mas_causa_permite() -> None:
    peticion = PeticionDePolitica(
        origen="policy_hook", cliente="c1", rol="writer", tool="submit_chapter"
    )

    assert decide(peticion).decision == "allow"


def test_solo_personalizacion_natural_se_admite_como_skill() -> None:
    admitida = PeticionDePolitica(
        origen="policy_hook",
        cliente="c1",
        rol="writer",
        tool="Skill",
        skill="personalizacion-natural",
    )
    otra = admitida.model_copy(update={"skill": "otra-skill"})

    assert decide(admitida).decision == "allow"
    d = decide(otra)
    assert d.decision == "deny"
    assert d.rule == "skill-no-admitida"
    assert d.detail == [{"skill": "otra-skill"}]


def test_nunca_escanea_un_campo_no_marcado_como_narrativo() -> None:
    entradas = [EntradaProhibida(term="marta", type="word", level="global")]
    peticion = PeticionDePolitica(
        origen="policy_hook",
        cliente="cliente-1",
        campos=[
            CampoNarrativo(path="capitulo.texto", narrativo=True, texto="un texto tranquilo"),
            CampoNarrativo(
                path="brief.prohibidas", narrativo=False, texto="marta es un termino prohibido"
            ),
        ],
        banned_entries=entradas,
    )

    assert decide(peticion).decision == "allow"


def test_sin_coincidencia_permite() -> None:
    entradas = [
        EntradaProhibida(term="idiota", type="word", level="global"),
        EntradaProhibida(term="marta", type="word", level="user", owner="cliente-1"),
        EntradaProhibida(term="cristina", type="word", level="novel", owner="novela-1"),
    ]
    decision = decide(_peticion("un texto tranquilo sin nada raro", entradas))

    assert decision.decision == "allow"
    assert decision.rule is None
