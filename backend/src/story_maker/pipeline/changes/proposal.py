"""La tool `propose_change` del planner en modo cambio: hechos a cambiar (hecho, valor nuevo) o
un hecho nuevo (sujeto, atributo, valor) (`architecture.md` §10.1 paso 2, §7.4).

Sin campos narrativos: el hook de policy no escanea los valores nuevos; los juzga el código al
validar la propuesta, con origen `change_request` (014-C06)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from story_maker.agents.tools import ToolSpec

PROPOSE_CHANGE = "propose_change"
MAX_VALUE_CHARS = 500


class FactChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fact_id: int
    new_value: str = Field(max_length=MAX_VALUE_CHARS)


class NewFact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject_type: Literal["character", "place"]
    subject_id: int
    attribute: str = Field(max_length=MAX_VALUE_CHARS)
    value: str = Field(max_length=MAX_VALUE_CHARS)


class ProposeChangeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    changes: list[FactChange] = Field(default_factory=list)
    new_fact: NewFact | None = None

    @model_validator(mode="after")
    def _one_kind_each_fact_once(self) -> ProposeChangeInput:
        """Hechos a cambiar o un hecho nuevo, nunca las dos cosas ni ninguna (014-C06)."""
        if bool(self.changes) == (self.new_fact is not None):
            raise ValueError("entrega hechos a cambiar o un hecho nuevo, exactamente una cosa")
        ids = [change.fact_id for change in self.changes]
        if len(ids) != len(set(ids)):
            raise ValueError("cada hecho a cambiar va una sola vez")
        return self


def propose_change_tool() -> ToolSpec:
    return ToolSpec(
        name=PROPOSE_CHANGE,
        model=ProposeChangeInput,
        description="Entrega la interpretación estructurada de la petición del cliente.",
    )
