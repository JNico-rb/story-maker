"""Tools con schema: el JSON Schema sale del modelo Pydantic de cada tool (arch. §7.4)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError


@dataclass(frozen=True)
class ToolSpec:
    """Una tool propia de un rol; su spec de rol declara el modelo y los campos narrativos."""

    name: str
    model: type[BaseModel]
    description: str = ""
    narrative: tuple[str, ...] = ()

    def schema(self) -> dict[str, Any]:
        return self.model.model_json_schema()

    def schema_text(self) -> str:
        return json.dumps(self.schema(), ensure_ascii=False)

    def validate(self, raw: dict[str, Any]) -> tuple[BaseModel | None, tuple[str, ...]]:
        """La entrada validada, o ninguna y un error por campo que falla."""
        try:
            return self.model.model_validate(raw), ()
        except ValidationError as exc:
            return None, tuple(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
