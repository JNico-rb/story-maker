"""Modelo del `Brief` y sus comprobaciones deterministas: schema, faltantes, contradicciones
C1-C6 y cota de obligatorios (`definitions.md` §1, `architecture.md` §3.2,
`domain-knowledge.md` §4.3, §5.2). Puro: sin I/O, opera sobre el contenido ya cargado."""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from story_maker.domain.banned_terms import find_term_matches

Ocasion = Literal["birthday", "wedding", "anniversary", "retirement", "other"]
Genero = Literal["adventure", "humor", "romance", "mystery", "drama", "fable"]
Tono = Literal["tender", "funny", "exciting", "nostalgic", "epic", "unsettling"]
Extension = Literal["short", "medium", "long"]
FranjaDeEdad = Literal["children", "teen", "adult"]

_CHILDISH_GENRES: tuple[Genero, ...] = ("romance", "drama")
_UNSETTLING_TONE: Tono = "unsettling"
_AGE_GATED_OCCASIONS: tuple[Ocasion, ...] = ("wedding", "anniversary")


class Trait(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""
    mandatory: bool = False


class CloseOne(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""
    relation: str = ""
    species: Literal["person", "animal"] | None = None
    age: int | None = Field(default=None, ge=0)
    birth_date: dt.date | None = None
    mandatory: bool = False


class Recollection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""
    age: int | None = Field(default=None, ge=0)
    year: int | None = None
    place: str = ""
    present: list[str] = Field(default_factory=list)
    excluded: str | None = None
    mandatory: bool = False


class Recipient(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = ""
    age: int | None = Field(default=None, ge=0)
    birth_date: dt.date | None = None
    traits: list[Trait] = Field(default_factory=list)
    relation: str | None = None


class PlotWish(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = ""


class BriefContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient: Recipient = Field(default_factory=Recipient)
    close_ones: list[CloseOne] = Field(default_factory=list)
    recollections: list[Recollection] = Field(default_factory=list)
    occasion: Ocasion | None = None
    genre: Genero | None = None
    tone: Tono | None = None
    length: Extension | None = None
    dedication: str = ""
    banned_asked: bool = False
    plot_wishes: list[PlotWish] = Field(default_factory=list)


def age_band(age: int) -> FranjaDeEdad:
    """`FranjaDeEdad`: infantil (< 12), juvenil (12-17) o adulto (>= 18) (`definitions.md` §1)."""
    if age < 12:
        return "children"
    if age < 18:
        return "teen"
    return "adult"


# Campos que un turno puede sustituir enteros (008-C04): cada clave del parche reemplaza el
# valor correspondiente del contenido; una clave ausente del parche deja el campo como estaba.
_PATCHABLE_SCALARS = ("occasion", "genre", "tone", "length", "dedication", "banned_asked")
_PATCHABLE_LISTS = ("close_ones", "recollections", "plot_wishes")
_RECIPIENT_SCALARS = ("name", "age", "birth_date", "relation")


def apply_patch(content: BriefContent, patch: dict[str, Any]) -> BriefContent:
    """El borrador tras aplicar `patch` (008-C04): cada clave presente reemplaza su valor entero,
    listas incluidas; una clave ausente no toca nada. `patch` ya viene de
    `UpdateBriefInput.model_dump(exclude_unset=True)`, así que solo trae lo que el rol entregó."""
    data = content.model_dump(mode="json")
    for key in _RECIPIENT_SCALARS:
        if key in patch:
            data["recipient"][key] = patch[key]
    if "traits" in patch:
        data["recipient"]["traits"] = patch["traits"]
    for key in (*_PATCHABLE_SCALARS, *_PATCHABLE_LISTS):
        if key in patch:
            data[key] = patch[key]
    return BriefContent.model_validate(data)


MISSING_FIELDS = (
    "name",
    "age",
    "traits",
    "recollections",
    "occasion",
    "genre",
    "tone",
    "length",
    "dedication",
    "banned_asked",
)


def missing_fields(content: BriefContent) -> list[str]:
    """`DatoFaltante`, uno por campo obligatorio sin valor (`definitions.md` §1, 008-C09)."""
    missing = []
    if not content.recipient.name.strip():
        missing.append("name")
    if content.recipient.age is None:
        missing.append("age")
    if not content.recipient.traits:
        missing.append("traits")
    if not content.recollections:
        missing.append("recollections")
    if content.occasion is None:
        missing.append("occasion")
    if content.genre is None:
        missing.append("genre")
    if content.tone is None:
        missing.append("tone")
    if content.length is None:
        missing.append("length")
    if not content.dedication.strip():
        missing.append("dedication")
    if not content.banned_asked:
        missing.append("banned_asked")
    return missing


class Contradiccion(BaseModel):
    """Par de datos incompatibles del brief (`definitions.md` §1, `domain-knowledge.md` §4.3)."""

    model_config = ConfigDict(extra="forbid")
    rule: Literal["C1", "C2", "C3", "C4", "C5", "C6"]
    fields: list[str]
    detail: dict[str, str] | None = None


def _anniversary(created_at: dt.date, birth_date: dt.date) -> dt.date:
    """El día en que se cumplen años en el año de `created_at`; un 29 de febrero cae el 1 de
    marzo en un año no bisiesto (`domain-knowledge.md` §5.2)."""
    try:
        return birth_date.replace(year=created_at.year)
    except ValueError:
        return dt.date(created_at.year, 3, 1)


def age_at(created_at: dt.date, birth_date: dt.date) -> int:
    """La edad que da `birth_date` en `created_at` (`domain-knowledge.md` §5.2)."""
    years = created_at.year - birth_date.year
    if created_at < _anniversary(created_at, birth_date):
        years -= 1
    return years


def derived_birth_year(
    age: int | None, birth_date: dt.date | None, created_at: dt.date
) -> int | None:
    """El año de nacimiento: el declarado, o el derivado de la edad (año presente menos edad);
    sin ninguno de los dos, ninguno (`domain-knowledge.md` §5.2)."""
    if birth_date is not None:
        return birth_date.year
    if age is not None:
        return created_at.year - age
    return None


def _c1(content: BriefContent) -> Contradiccion | None:
    age = content.recipient.age
    if age is None or content.genre is None:
        return None
    if age_band(age) == "children" and content.genre in _CHILDISH_GENRES:
        return Contradiccion(rule="C1", fields=["recipient.age", "genre"])
    return None


def _c2(content: BriefContent) -> Contradiccion | None:
    age = content.recipient.age
    if age is None or content.tone is None:
        return None
    if age_band(age) == "children" and content.tone == _UNSETTLING_TONE:
        return Contradiccion(rule="C2", fields=["recipient.age", "tone"])
    return None


def _c3(content: BriefContent) -> Contradiccion | None:
    age = content.recipient.age
    if age is None or content.occasion is None:
        return None
    if content.occasion in _AGE_GATED_OCCASIONS and age < 18:
        return Contradiccion(rule="C3", fields=["occasion", "recipient.age"])
    if content.occasion == "retirement" and age < 50:
        return Contradiccion(rule="C3", fields=["occasion", "recipient.age"])
    return None


def _c4_for(
    age: int | None, birth_date: dt.date | None, created_at: dt.date, prefix: str
) -> Contradiccion | None:
    if age is None or birth_date is None:
        return None
    if age_at(created_at, birth_date) != age:
        return Contradiccion(rule="C4", fields=[f"{prefix}.birth_date", f"{prefix}.age"])
    return None


def _c4(content: BriefContent, created_at: dt.date) -> list[Contradiccion]:
    found = []
    recipient = _c4_for(
        content.recipient.age, content.recipient.birth_date, created_at, "recipient"
    )
    if recipient is not None:
        found.append(recipient)
    for i, close_one in enumerate(content.close_ones):
        result = _c4_for(close_one.age, close_one.birth_date, created_at, f"close_ones[{i}]")
        if result is not None:
            found.append(result)
    return found


def _c5(content: BriefContent, created_at: dt.date) -> list[Contradiccion]:
    found = []
    age = content.recipient.age
    birth_year = derived_birth_year(age, content.recipient.birth_date, created_at)
    for i, recollection in enumerate(content.recollections):
        field = f"recollections[{i}]"
        if recollection.age is not None and age is not None and recollection.age > age:
            found.append(Contradiccion(rule="C5", fields=[field, "age"]))
        elif (
            recollection.year is not None
            and birth_year is not None
            and (recollection.year < birth_year or recollection.year > created_at.year)
        ):
            found.append(Contradiccion(rule="C5", fields=[field, "year"]))
    return found


def contradictions(content: BriefContent, created_at: dt.date) -> list[Contradiccion]:
    """C1-C5 (008-C10); C6 (prohibidas) lo añade `contradictions_with_banned` (008-C11). Una
    regla cuyos datos faltan no se evalúa (`architecture.md` §3.2)."""
    found: list[Contradiccion] = []
    for rule in (_c1(content), _c2(content), _c3(content)):
        if rule is not None:
            found.append(rule)
    found += _c4(content, created_at)
    found += _c5(content, created_at)
    return found


class BannedEntry(BaseModel):
    """Una `EntradaProhibida` tal como la necesita C6; `domain` no importa `policy` (regla de
    dependencias, `architecture.md` §15.9), así que quien llama convierte las filas de
    `banned_terms` a esta forma."""

    model_config = ConfigDict(extra="forbid")
    term: str
    type: Literal["word", "topic"]
    level: Literal["global", "user", "novel"]
    keywords: list[str] = Field(default_factory=list)


class AcceptedFact(BaseModel):
    """Un `HechoExtraido` aceptado, lo único que C6 y la cota de obligatorios necesitan de él."""

    model_config = ConfigDict(extra="forbid")
    id: int
    subject: str
    value: str
    mandatory: bool


def _c6_matches(text: str, entries: list[BannedEntry]) -> list[Contradiccion]:
    found = []
    for entry in entries:
        needles = entry.keywords if entry.type == "topic" else [entry.term]
        for needle in needles:
            for variant in find_term_matches(text, needle):
                found.append((entry, variant))
                break
    return [
        Contradiccion(
            rule="C6",
            fields=[""],
            detail={"term": entry.term, "level": entry.level, "variant": variant},
        )
        for entry, variant in found
    ]


def _c6_at(text: str, field: str, checked: bool, entries: list[BannedEntry]) -> list[Contradiccion]:
    if not checked:
        return []
    return [c.model_copy(update={"fields": [field]}) for c in _c6_matches(text, entries)]


def c6_contradictions(
    content: BriefContent, banned_entries: list[BannedEntry], accepted_facts: list[AcceptedFact]
) -> list[Contradiccion]:
    """C6: una entrada prohibida de cualquier nivel en un elemento obligatorio, en la dedicatoria
    o en un deseo de trama (`domain-knowledge.md` §4.3, 008-C11). Un elemento no obligatorio no
    cuenta, salvo la dedicatoria y los deseos de trama, que siempre se comprueban."""
    found: list[Contradiccion] = []
    found += _c6_at(content.recipient.name, "recipient.name", True, banned_entries)
    for i, trait in enumerate(content.recipient.traits):
        found += _c6_at(trait.statement, f"recipient.traits[{i}]", trait.mandatory, banned_entries)
    for i, recollection in enumerate(content.recollections):
        found += _c6_at(
            recollection.statement,
            f"recollections[{i}]",
            recollection.mandatory,
            banned_entries,
        )
    for i, close_one in enumerate(content.close_ones):
        found += _c6_at(close_one.name, f"close_ones[{i}]", close_one.mandatory, banned_entries)
    found += _c6_at(content.dedication, "dedication", True, banned_entries)
    for i, wish in enumerate(content.plot_wishes):
        found += _c6_at(wish.statement, f"plot_wishes[{i}]", True, banned_entries)
    for fact in accepted_facts:
        found += _c6_at(fact.value, f"extracted_facts[{fact.id}]", fact.mandatory, banned_entries)
    return found


def all_contradictions(
    content: BriefContent,
    created_at: dt.date,
    banned_entries: list[BannedEntry],
    accepted_facts: list[AcceptedFact],
) -> list[Contradiccion]:
    """C1-C6 juntas, en un orden estable (008-I2): no depende del orden de `banned_entries`."""
    found = contradictions(content, created_at) + c6_contradictions(
        content, banned_entries, accepted_facts
    )
    return sorted(found, key=lambda c: (c.rule, tuple(c.fields)))


def mandatory_count(content: BriefContent, accepted_facts: list[AcceptedFact]) -> int:
    """Obligatorios contados para la cota (008-C12): el nombre siempre cuenta, más cada rasgo,
    recuerdo, allegado y hecho aceptado marcado obligatorio. Un elemento que no es obligatorio no
    cuenta, y un hecho que no está aceptado no puede ser obligatorio (`accepted_facts` ya viene
    filtrado a los aceptados, 008-C24)."""
    count = 1  # el nombre de la destinataria, obligatorio siempre
    count += sum(1 for trait in content.recipient.traits if trait.mandatory)
    count += sum(1 for recollection in content.recollections if recollection.mandatory)
    count += sum(1 for close_one in content.close_ones if close_one.mandatory)
    count += sum(1 for fact in accepted_facts if fact.mandatory)
    return count


class SchemaError(BaseModel):
    """Un error de schema que cruza datos del brief (008-C13): a diferencia de los de forma
    (tipos, catálogos, textos vacíos, edad negativa, fechas que no existen), que `BriefContent`
    ya rechaza al validar, estos sí llegan al borrador y bloquean la confirmación."""

    model_config = ConfigDict(extra="forbid")
    message: str
    fields: list[str]


def schema_errors(content: BriefContent, accepted_facts: list[AcceptedFact]) -> list[SchemaError]:
    errors: list[SchemaError] = []
    close_one_names = {c.name for c in content.close_ones if c.name}
    all_names = close_one_names | ({content.recipient.name} if content.recipient.name else set())

    for i, recollection in enumerate(content.recollections):
        field = f"recollections[{i}]"
        unknown_present = [p for p in recollection.present if p not in close_one_names]
        if unknown_present:
            errors.append(
                SchemaError(
                    message="Presente desconocido en el recuerdo", fields=[f"{field}.present"]
                )
            )
        if recollection.excluded is not None and recollection.excluded not in close_one_names:
            errors.append(SchemaError(message="Excluido no válido", fields=[f"{field}.excluded"]))
        has_age = recollection.age is not None
        has_year = recollection.year is not None
        if has_age == has_year:
            errors.append(
                SchemaError(message="El recuerdo necesita edad o año, uno solo", fields=[field])
            )
        if not recollection.place.strip():
            errors.append(SchemaError(message="Recuerdo sin lugar", fields=[f"{field}.place"]))

    for i, close_one in enumerate(content.close_ones):
        if not close_one.relation.strip() or close_one.species is None:
            errors.append(SchemaError(message="Allegado incompleto", fields=[f"close_ones[{i}]"]))

    names = [content.recipient.name, *(c.name for c in content.close_ones)]
    names = [n for n in names if n]
    if len(names) != len(set(names)):
        errors.append(SchemaError(message="Nombre repetido", fields=["close_ones"]))

    for fact in accepted_facts:
        if fact.subject not in all_names:
            errors.append(
                SchemaError(
                    message="Sujeto desconocido", fields=[f"extracted_facts[{fact.id}].subject"]
                )
            )

    return errors


class ElementoPersonal(BaseModel):
    """Dato del brief que personaliza la novela (`definitions.md` §1, 008-C15): el nombre de la
    destinataria, un rasgo, un recuerdo, un allegado o un hecho extraído aceptado. El id es único
    dentro del brief; se calcula al confirmar, y el brief confirmado es inmutable (008-C17), así
    que no necesita ser estable frente a ediciones posteriores del borrador."""

    model_config = ConfigDict(extra="forbid")
    id: int
    origin: Literal["brief_field", "extracted_fact"]
    field: str
    mandatory: bool


def personal_elements(
    content: BriefContent, accepted_facts: list[AcceptedFact]
) -> list[ElementoPersonal]:
    elements = [
        ElementoPersonal(id=1, origin="brief_field", field="recipient.name", mandatory=True)
    ]
    next_id = 2
    for i, trait in enumerate(content.recipient.traits):
        elements.append(
            ElementoPersonal(
                id=next_id,
                origin="brief_field",
                field=f"recipient.traits[{i}]",
                mandatory=trait.mandatory,
            )
        )
        next_id += 1
    for i, recollection in enumerate(content.recollections):
        elements.append(
            ElementoPersonal(
                id=next_id,
                origin="brief_field",
                field=f"recollections[{i}]",
                mandatory=recollection.mandatory,
            )
        )
        next_id += 1
    for i, close_one in enumerate(content.close_ones):
        elements.append(
            ElementoPersonal(
                id=next_id,
                origin="brief_field",
                field=f"close_ones[{i}]",
                mandatory=close_one.mandatory,
            )
        )
        next_id += 1
    for fact in accepted_facts:
        elements.append(
            ElementoPersonal(
                id=next_id,
                origin="extracted_fact",
                field=f"extracted_facts[{fact.id}]",
                mandatory=fact.mandatory,
            )
        )
        next_id += 1
    return elements


# --- Problemas que bloquean confirmar o importar (008-C09 a 008-C13, 008-I1) -------------------


def missing_field_problems(content: BriefContent) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", "brief", "missing_fields", name],
            "msg": f"falta: {name}",
            "type": "missing_field",
        }
        for name in missing_fields(content)
    ]


def contradiction_problems(contradictions_found: list[Contradiccion]) -> list[dict[str, Any]]:
    return [
        {
            "loc": ["body", "brief", "contradictions", *item.fields],
            "msg": f"contradicción {item.rule}",
            "type": "contradiction",
        }
        for item in contradictions_found
    ]


def schema_error_problems(errors: list[SchemaError]) -> list[dict[str, Any]]:
    return [
        {"loc": ["body", "brief", *item.fields], "msg": item.message, "type": "schema_error"}
        for item in errors
    ]


def mandatory_cap_problems(count: int, max_mandatory_elements: int) -> list[dict[str, Any]]:
    if count <= max_mandatory_elements:
        return []
    msg = f"{count} de {max_mandatory_elements}"
    return [{"loc": ["body", "brief", "mandatory_count"], "msg": msg, "type": "mandatory_cap"}]


def brief_problems(
    content: BriefContent,
    created_at: dt.date,
    banned_entries: list[BannedEntry],
    accepted_facts: list[AcceptedFact],
    max_mandatory_elements: int,
) -> list[dict[str, Any]]:
    """Todo lo que bloquea la confirmación o la importación (008-C09 a 008-C13); mismo cálculo
    para las dos vías, así que deciden igual (008-I1)."""
    return (
        missing_field_problems(content)
        + contradiction_problems(
            all_contradictions(content, created_at, banned_entries, accepted_facts)
        )
        + schema_error_problems(schema_errors(content, accepted_facts))
        + mandatory_cap_problems(mandatory_count(content, accepted_facts), max_mandatory_elements)
    )


# --- HechoExtraido: citas-verificadas (008-C18, 008-C19, 008-C20) -----------------------------

_WHITESPACE = re.compile(r"\s+")


def _normalize_whitespace(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def valid_subjects(content: BriefContent) -> set[str]:
    """El destinatario y los allegados, tal cual (008-C18): los únicos sujetos válidos."""
    subjects = {c.name for c in content.close_ones if c.name}
    if content.recipient.name:
        subjects.add(content.recipient.name)
    return subjects


def quote_appears_literally(text: str, quote: str) -> bool:
    """La cita aparece tal cual en `text`, con los espacios normalizados (008-C19)."""
    if not quote.strip():
        return False
    return _normalize_whitespace(quote) in _normalize_whitespace(text)


def _all_spans(haystack: str, needle: str) -> list[tuple[int, int]]:
    if not needle:
        return []
    spans = []
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index == -1:
            break
        spans.append((index, index + len(needle)))
        start = index + 1
    return spans


def _overlaps(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def quote_overlaps_a_marked_phrase(text: str, quote: str, marked_phrases: list[str]) -> bool:
    """La cita comparte al menos un carácter con una frase marcada por el detector (008-C19);
    tocar el límite sin compartir carácter no cuenta. Todo se compara en espacios normalizados,
    igual que `quote_appears_literally`, para que las dos reglas midan sobre el mismo texto."""
    normalized_text = _normalize_whitespace(text)
    quote_spans = _all_spans(normalized_text, _normalize_whitespace(quote))
    if not quote_spans:
        return False
    for phrase in marked_phrases:
        for phrase_span in _all_spans(normalized_text, _normalize_whitespace(phrase)):
            if any(_overlaps(span, phrase_span) for span in quote_spans):
                return True
    return False


def is_fact_verified(
    subject: str, quote: str, text: str, content: BriefContent, marked_phrases: list[str]
) -> bool:
    """`citas-verificadas` (`definitions.md` §1 HechoExtraido, 008-C19): la cita aparece literal,
    el sujeto es válido y la cita no se solapa con una frase marcada."""
    return (
        quote_appears_literally(text, quote)
        and subject in valid_subjects(content)
        and not quote_overlaps_a_marked_phrase(text, quote, marked_phrases)
    )
