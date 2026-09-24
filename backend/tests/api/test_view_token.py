"""El token de vista se emite firmado y con sus reclamaciones (013-C06, parte de 013-I2)."""

from __future__ import annotations

import datetime as dt

import jwt
import pytest

from story_maker.api.view_tokens import (
    AUDIENCE,
    ViewTokenError,
    create_view_token,
    decode_view_token,
)

JWT_SECRET = "x" * 32
NOW = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.UTC)
SESSION_TIMEOUT_SECONDS = 600


def test_the_view_token_is_signed_hs256_with_its_claims() -> None:
    token = create_view_token(41, JWT_SECRET, SESSION_TIMEOUT_SECONDS, NOW)

    payload = jwt.decode(
        token, JWT_SECRET, algorithms=["HS256"], audience=AUDIENCE, options={"verify_exp": False}
    )
    t0 = int(NOW.timestamp())
    assert payload == {
        "sub": "41",
        "iat": t0,
        "exp": t0 + SESSION_TIMEOUT_SECONDS,
        "aud": AUDIENCE,
    }


def test_a_freshly_issued_token_decodes_to_its_version_id() -> None:
    token = create_view_token(41, JWT_SECRET, SESSION_TIMEOUT_SECONDS, NOW)

    assert decode_view_token(token, JWT_SECRET, now=NOW) == 41


def test_a_token_signed_with_another_secret_is_rejected() -> None:
    token = create_view_token(41, JWT_SECRET, SESSION_TIMEOUT_SECONDS, NOW)

    with pytest.raises(ViewTokenError):
        decode_view_token(token, "y" * 32, now=NOW)
