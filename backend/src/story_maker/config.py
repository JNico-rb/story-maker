"""`config.json`: política del servidor, validada entera al arrancar (`definitions.md` §11.1)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROLES = ("interviewer", "extractor", "planner", "writer", "editor", "judge", "visual_reviewer")
CRITERIA = (
    "fidelidad-canon",
    "cumple-beats",
    "personalizacion-natural",
    "prosa",
    "tono",
    "continuidad",
    "coherencia-personajes",
    "arco-y-final",
    "ritmo",
    "no-cliche",
)
AGE_BANDS = ("children", "teen", "adult")


class ConfigError(ValueError):
    """Config inválida; `errors` nombra cada clave que falta, sobra o no vale."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class RoleConfig:
    model: str
    max_turns: int
    max_output_tokens: int


@dataclass(frozen=True)
class PriceConfig:
    input: float
    output: float
    cache_read: float
    cache_write: float


@dataclass(frozen=True)
class ReadabilityTarget:
    sentence_length: int
    fernandez_huerta: int


@dataclass(frozen=True)
class Config:
    token_ceiling: int
    api_wait_seconds: int
    max_retries: dict[str, int]
    max_resumes: int
    session_timeout_seconds: int
    verifier_timeout_seconds: int
    max_mandatory_elements: int
    access_token_hours: int
    confirmation_minutes: int
    roles: dict[str, RoleConfig]
    pricing: dict[str, PriceConfig]
    thresholds: dict[str, int]
    readability_targets: dict[str, ReadabilityTarget]
    embedding_model: str
    top_k: dict[str, int]


def _obj(data: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        errors.append(f"{path}: debe ser un objeto")
        return {}
    return data


def _unknown_keys(
    obj: dict[str, Any], path: str, allowed: tuple[str, ...], errors: list[str]
) -> None:
    for key in obj:
        if key not in allowed:
            errors.append(f"{path}.{key}: clave desconocida")


def _missing_keys(
    obj: dict[str, Any], path: str, required: tuple[str, ...], errors: list[str]
) -> None:
    for key in required:
        if key not in obj:
            errors.append(f"{path}.{key}: falta")


def _positive_int(obj: dict[str, Any], path: str, key: str, errors: list[str]) -> int:
    value = obj.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        errors.append(f"{path}.{key}: debe ser un entero mayor que 0")
        return 0
    return value


def _nonnegative_int(obj: dict[str, Any], path: str, key: str, errors: list[str]) -> int:
    value = obj.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{path}.{key}: debe ser un entero mayor o igual que 0")
        return 0
    return value


def _nonnegative_number(obj: dict[str, Any], path: str, key: str, errors: list[str]) -> float:
    value = obj.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        errors.append(f"{path}.{key}: debe ser un número mayor o igual que 0")
        return 0.0
    return float(value)


def _parse_max_retries(operation: dict[str, Any], errors: list[str]) -> dict[str, int]:
    keys = ("chapter", "plan", "gate_cycles", "change")
    path = "operation.max_retries"
    obj = _obj(operation.get("max_retries"), path, errors)
    _unknown_keys(obj, path, keys, errors)
    _missing_keys(obj, path, keys, errors)
    return {key: _nonnegative_int(obj, path, key, errors) for key in keys if key in obj}


def _parse_roles(operation: dict[str, Any], errors: list[str]) -> dict[str, RoleConfig]:
    path = "operation.roles"
    obj = _obj(operation.get("roles"), path, errors)
    _unknown_keys(obj, path, ROLES, errors)
    _missing_keys(obj, path, ROLES, errors)
    roles: dict[str, RoleConfig] = {}
    for role in ROLES:
        if role not in obj:
            continue
        role_path = f"{path}.{role}"
        role_obj = _obj(obj[role], role_path, errors)
        _unknown_keys(role_obj, role_path, ("model", "max_turns", "max_output_tokens"), errors)
        model = role_obj.get("model")
        if not isinstance(model, str) or not model:
            errors.append(f"{role_path}.model: falta o no vale")
            model = ""
        max_turns = _positive_int(role_obj, role_path, "max_turns", errors)
        max_output_tokens = _positive_int(role_obj, role_path, "max_output_tokens", errors)
        roles[role] = RoleConfig(
            model=model, max_turns=max_turns, max_output_tokens=max_output_tokens
        )
    return roles


def _parse_pricing(
    operation: dict[str, Any], roles: dict[str, RoleConfig], errors: list[str]
) -> dict[str, PriceConfig]:
    path = "operation.pricing"
    obj = _obj(operation.get("pricing"), path, errors)
    pricing: dict[str, PriceConfig] = {}
    for model, entry in obj.items():
        entry_path = f"{path}.{model}"
        entry_obj = _obj(entry, entry_path, errors)
        keys = ("input", "output", "cache_read", "cache_write")
        _unknown_keys(entry_obj, entry_path, keys, errors)
        _missing_keys(entry_obj, entry_path, keys, errors)
        pricing[model] = PriceConfig(
            input=_nonnegative_number(entry_obj, entry_path, "input", errors),
            output=_nonnegative_number(entry_obj, entry_path, "output", errors),
            cache_read=_nonnegative_number(entry_obj, entry_path, "cache_read", errors),
            cache_write=_nonnegative_number(entry_obj, entry_path, "cache_write", errors),
        )
    for role, role_config in roles.items():
        if role_config.model and role_config.model not in pricing:
            errors.append(
                f"operation.roles.{role}.model: el modelo '{role_config.model}' no tiene precio"
            )
    return pricing


def _parse_thresholds(quality: dict[str, Any], errors: list[str]) -> dict[str, int]:
    path = "quality.thresholds"
    obj = _obj(quality.get("thresholds"), path, errors)
    _unknown_keys(obj, path, CRITERIA, errors)
    _missing_keys(obj, path, CRITERIA, errors)
    thresholds: dict[str, int] = {}
    for criterion in CRITERIA:
        if criterion not in obj:
            continue
        value = obj[criterion]
        if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 5):
            errors.append(f"{path}.{criterion}: el umbral va de 1 a 5")
            continue
        thresholds[criterion] = value
    return thresholds


def _parse_readability_targets(
    quality: dict[str, Any], errors: list[str]
) -> dict[str, ReadabilityTarget]:
    path = "quality.readability_targets"
    obj = _obj(quality.get("readability_targets"), path, errors)
    _unknown_keys(obj, path, AGE_BANDS, errors)
    _missing_keys(obj, path, AGE_BANDS, errors)
    targets: dict[str, ReadabilityTarget] = {}
    for band in AGE_BANDS:
        if band not in obj:
            continue
        band_path = f"{path}.{band}"
        band_obj = _obj(obj[band], band_path, errors)
        _unknown_keys(band_obj, band_path, ("sentence_length", "fernandez_huerta"), errors)
        targets[band] = ReadabilityTarget(
            sentence_length=_positive_int(band_obj, band_path, "sentence_length", errors),
            fernandez_huerta=_positive_int(band_obj, band_path, "fernandez_huerta", errors),
        )
    return targets


def _parse_retrieval(data: dict[str, Any], errors: list[str]) -> tuple[str, dict[str, int]]:
    path = "retrieval"
    obj = _obj(data.get("retrieval"), path, errors)
    _unknown_keys(obj, path, ("embedding_model", "top_k"), errors)
    _missing_keys(obj, path, ("embedding_model", "top_k"), errors)

    embedding_model = obj.get("embedding_model")
    if not isinstance(embedding_model, str) or not embedding_model:
        if "embedding_model" in obj:
            errors.append(f"{path}.embedding_model: no puede estar vacío")
        embedding_model = ""

    top_k_path = f"{path}.top_k"
    top_k_obj = _obj(obj.get("top_k"), top_k_path, errors)
    _unknown_keys(top_k_obj, top_k_path, ("writer", "editor"), errors)
    _missing_keys(top_k_obj, top_k_path, ("writer", "editor"), errors)
    top_k: dict[str, int] = {
        key: _positive_int(top_k_obj, top_k_path, key, errors)
        for key in ("writer", "editor")
        if key in top_k_obj
    }
    return embedding_model, top_k


def parse_config(data: Any) -> Config:
    """Valida `data` entero contra §15.4; `ConfigError.errors` nombra cada clave que falla."""
    errors: list[str] = []
    root = _obj(data, "", errors)
    _unknown_keys(root, "", ("operation", "quality", "retrieval"), errors)
    _missing_keys(root, "", ("operation", "quality", "retrieval"), errors)

    operation = _obj(root.get("operation"), "operation", errors)
    _unknown_keys(
        operation,
        "operation",
        (
            "token_ceiling",
            "api_wait_seconds",
            "max_retries",
            "max_resumes",
            "session_timeout_seconds",
            "verifier_timeout_seconds",
            "max_mandatory_elements",
            "access_token_hours",
            "confirmation_minutes",
            "roles",
            "pricing",
        ),
        errors,
    )

    token_ceiling = operation.get("token_ceiling")
    if not isinstance(token_ceiling, int) or isinstance(token_ceiling, bool) or token_ceiling <= 0:
        errors.append("operation.token_ceiling: debe ser un entero mayor que 0")
        token_ceiling = 0
    elif token_ceiling > 100000:
        errors.append("operation.token_ceiling: no puede superar el máximo de 100000")

    api_wait_seconds = _positive_int(operation, "operation", "api_wait_seconds", errors)
    max_retries = _parse_max_retries(operation, errors)
    max_resumes = _nonnegative_int(operation, "operation", "max_resumes", errors)
    session_timeout_seconds = _positive_int(
        operation, "operation", "session_timeout_seconds", errors
    )
    verifier_timeout_seconds = _positive_int(
        operation, "operation", "verifier_timeout_seconds", errors
    )
    max_mandatory_elements = _positive_int(operation, "operation", "max_mandatory_elements", errors)
    access_token_hours = _positive_int(operation, "operation", "access_token_hours", errors)
    confirmation_minutes = _positive_int(operation, "operation", "confirmation_minutes", errors)
    roles = _parse_roles(operation, errors)
    pricing = _parse_pricing(operation, roles, errors)

    quality = _obj(root.get("quality"), "quality", errors)
    _unknown_keys(quality, "quality", ("thresholds", "readability_targets"), errors)
    thresholds = _parse_thresholds(quality, errors)
    readability_targets = _parse_readability_targets(quality, errors)

    embedding_model, top_k = _parse_retrieval(root, errors)

    if errors:
        raise ConfigError(errors)

    return Config(
        token_ceiling=token_ceiling,
        api_wait_seconds=api_wait_seconds,
        max_retries=max_retries,
        max_resumes=max_resumes,
        session_timeout_seconds=session_timeout_seconds,
        verifier_timeout_seconds=verifier_timeout_seconds,
        max_mandatory_elements=max_mandatory_elements,
        access_token_hours=access_token_hours,
        confirmation_minutes=confirmation_minutes,
        roles=roles,
        pricing=pricing,
        thresholds=thresholds,
        readability_targets=readability_targets,
        embedding_model=embedding_model,
        top_k=top_k,
    )


def load_config(path: Path) -> Config:
    """Lee y valida `config.json`; rechaza con la ruta si no existe o no es JSON válido."""
    if not path.is_file():
        raise ConfigError([f"{path}: el fichero de config no existe"])
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(
            [f"{path}: JSON inválido en la línea {exc.lineno}, columna {exc.colno}"]
        ) from exc
    return parse_config(data)
