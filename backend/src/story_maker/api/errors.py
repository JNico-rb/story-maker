"""Forma única de los 422 de `/api`: `{"detail": [{"loc", "msg", "type"}]}`, sin `input` ni
`ctx` — ninguno de los dos reproduce lo enviado (hallazgo del integrador tras el cierre de 002:
el 422 por defecto de FastAPI para un cuerpo incompleto lleva `input` con el cuerpo entero,
incluida una contraseña que sí llegó en un campo hermano al que falta)."""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def field_error(field: str, msg: str, error_type: str = "value_error") -> list[dict[str, object]]:
    """El `detail` de un 422 alzado a mano, en la misma forma que el que genera FastAPI."""
    return [{"loc": ["body", field], "msg": msg, "type": error_type}]


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Sustituye el 422 por defecto de FastAPI, que lleva `input` (y a veces `ctx`) con el valor
    enviado; aquí solo `loc`, `msg` y `type`."""
    del request
    detail = [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detail})
