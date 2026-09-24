"""`VistaDeVersion`: HTML de servidor (Jinja2) de una versión, candidata o publicada — portada,
novedades, índice, capítulos y ficha de personajes y lugares (`definitions.md` §3 Portada,
FichaDePersonajes; `architecture.md` §14.2).

La entrada es un dataclass plano, no los modelos SQLAlchemy: el repositorio de 009 la alimenta
sin traducción rara (013-C01 a 013-C05 la ejercen contra datos reales; aquí solo el render puro).
"""

from __future__ import annotations

from dataclasses import dataclass

from jinja2 import Environment

_ENV = Environment(autoescape=True)

_TEMPLATE = _ENV.from_string(
    """<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>{{ data.title }}</title></head>
<body>
<section id="portada">
  <h1>{{ data.title }}</h1>
  <p id="destinatario">Para {{ data.recipient }}</p>
  <p id="dedicatoria">{{ data.dedication }}</p>
</section>

{% if data.changed_chapters %}
<section id="novedades">
  <h2>Novedades</h2>
  <ul>
    {% for n in data.changed_chapters %}
    <li><a href="#cap-{{ n }}">Capítulo {{ n }}</a></li>
    {% endfor %}
  </ul>
</section>
{% endif %}

<nav id="indice">
  <h2>Índice</h2>
  <ol>
    {% for chapter in chapters %}
    <li>
      <a href="#cap-{{ chapter.number }}">{{ chapter.number }}. {{ chapter.title }}</a>
      {% if chapter.number in data.changed_chapters %}
      <span class="cambiado">{{ changed_label }}</span>
      {% endif %}
    </li>
    {% endfor %}
  </ol>
</nav>

<section id="capitulos">
  {% for chapter in chapters %}
  <article id="cap-{{ chapter.number }}">
    <h2>{{ chapter.number }}. {{ chapter.title }}</h2>
    {% for paragraph in chapter.paragraphs %}
    <p>{{ paragraph }}</p>
    {% endfor %}
  </article>
  {% endfor %}
</section>

<section id="ficha">
  <h2>Ficha de personajes y lugares</h2>
  {% for group_name, entities in ficha_groups %}
  <div class="ficha-grupo">
    <h3>{{ group_name }}</h3>
    <ul>
      {% for entity in entities %}
      <li>
        {{ entity.name }}:
        {% if entity.chapters %}
        {% for n in entity.chapters %}
        <a href="#cap-{{ n }}">Cap. {{ n }}</a>{% if not loop.last %}, {% endif %}
        {% endfor %}
        {% endif %}
      </li>
      {% endfor %}
    </ul>
  </div>
  {% endfor %}
</section>
</body>
</html>
"""
)

_KIND_LABELS = {"personaje": "Personajes", "lugar": "Lugares"}


@dataclass(frozen=True, slots=True)
class CapituloVista:
    """Un capítulo tal como lo guarda 009 (`definitions.md` §3 Capitulo): número, título y texto
    plano con párrafos separados por una línea en blanco."""

    number: int
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class EntidadFicha:
    """Una fila de la `FichaDePersonajes`: nombre canónico, tipo y los capítulos donde aparece
    (por `UsoDeHecho` o evento registrado, `definitions.md` §3). Vacía si no aparece en ninguno
    (013-C03)."""

    name: str
    kind: str  # "personaje" | "lugar"
    chapters: list[int]


@dataclass(frozen=True, slots=True)
class VersionViewData:
    """Entrada del render: lo que 009 expone de una `Version` para pintar su `VistaDeVersion`.

    `version_number` es `None` en una candidata (009-I1: solo las publicadas tienen número); la
    marca «cambiado en vN» cae entonces a «cambiado», sin número."""

    title: str
    recipient: str
    dedication: str
    version_number: int | None
    chapters: list[CapituloVista]
    changed_chapters: list[int]
    ficha: list[EntidadFicha]


def _paragraphs(text: str) -> list[str]:
    return [paragraph for paragraph in text.split("\n\n") if paragraph.strip()]


def render_version_view(data: VersionViewData) -> str:
    """HTML completo de la `VistaDeVersion`: mismo resultado para la misma entrada (013-I5)."""
    chapters = [
        {"number": chapter.number, "title": chapter.title, "paragraphs": _paragraphs(chapter.text)}
        for chapter in data.chapters
    ]
    ficha_groups = [
        (label, [entity for entity in data.ficha if entity.kind == kind])
        for kind, label in _KIND_LABELS.items()
        if any(entity.kind == kind for entity in data.ficha)
    ]
    changed_label = f"cambiado en v{data.version_number}" if data.version_number else "cambiado"
    return _TEMPLATE.render(
        data=data, chapters=chapters, ficha_groups=ficha_groups, changed_label=changed_label
    )
