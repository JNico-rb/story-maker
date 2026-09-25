"""Error de tool con el código de estado que daría `/api` en el mismo caso (§15.7, 015-C09,
015-C12, 015-C14). El contenido es JSON determinista: `{"status": N, "detail": ...}`."""

from __future__ import annotations

import json
from typing import Any, NoReturn

from fastapi import HTTPException
from fastmcp.exceptions import ToolError


def tool_error(status: int, detail: Any) -> NoReturn:
    raise ToolError(json.dumps({"status": status, "detail": detail}, ensure_ascii=False))


def from_http_exception(exc: HTTPException) -> NoReturn:
    tool_error(exc.status_code, exc.detail)
