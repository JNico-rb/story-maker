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
<head>
<meta charset="utf-8">
<title>{{ data.title }}</title>
<style>
  @page {
    size: A5;
    margin: 20mm 17mm 22mm;
    @bottom-center {
      content: counter(page);
      font-family: Georgia, serif;
      font-size: 9pt;
    }
  }
  @page :first {
    @bottom-center { content: none; }
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    font-family: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #1a1a1a;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  h2 {
    font-weight: normal;
    font-size: 16pt;
    text-align: center;
    margin: 12mm 0 1.4em;
  }

  p {
    margin: 0 0 0.6em;
    text-align: justify;
    hyphens: auto;
    orphans: 2;
    widows: 2;
  }

  #capitulos article p {
    margin: 0;
    text-indent: 1.4em;
  }
  #capitulos article p:first-of-type {
    text-indent: 0;
  }

  #portada {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    min-height: 100vh;
    break-after: page;
  }
  #portada h1 {
    font-size: 22pt;
    font-weight: normal;
    margin: 0 0 1.4em;
  }
  #destinatario {
    font-variant: small-caps;
    letter-spacing: 0.12em;
    font-size: 13pt;
    margin: 0 0 1em;
  }
  #portada hr {
    width: 35%;
    border: none;
    border-top: 1px solid #999;
    margin: 1.2em 0;
  }
  #dedicatoria {
    font-style: italic;
    font-size: 12.5pt;
    max-width: 26em;
    margin: 0;
    text-align: center;
    hyphens: manual;
  }

  #novedades, #indice, #ficha, #capitulos article {
    break-before: page;
  }

  #indice ol {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  #indice li {
    display: flex;
    justify-content: space-between;
    gap: 0.6em;
    align-items: baseline;
    padding: 0.35em 0;
    border-bottom: 1px dotted #bbb;
  }
  #indice .cambiado {
    font-size: 0.8em;
    font-style: italic;
    color: #666;
    white-space: nowrap;
  }

  #capitulos h2 {
    margin: 22mm 0 2em;
  }
  #capitulos .cap-numero {
    display: block;
    font-size: 10pt;
    font-style: italic;
    color: #555;
    margin-bottom: 0.5em;
  }
  #capitulos .cap-titulo {
    display: block;
    font-size: 16pt;
  }

  #ficha .ficha-grupo { margin-bottom: 1.5em; }
  #ficha .ficha-grupo:last-child { margin-bottom: 0; }
  #ficha h3 {
    font-weight: normal;
    font-variant: small-caps;
    font-size: 12pt;
    margin: 0 0 0.6em;
    border-bottom: 1px solid #ccc;
  }
  #ficha ul { margin: 0; padding: 0; list-style: none; }
  #ficha li { margin-bottom: 0.45em; }
  #ficha a { white-space: nowrap; }
  #novedades ul { list-style: none; padding: 0; text-align: center; }
  #novedades li { margin-bottom: 0.4em; }
  #ficha .nombre { font-weight: bold; }

  @media screen {
    body {
      max-width: 40rem;
      margin: 2rem auto;
      padding: 0 1rem;
    }
  }
</style>
</head>
<body>
<section id="portada">
  <h1>{{ data.title }}</h1>
  <p id="destinatario">Para {{ data.recipient }}</p>
  <hr>
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
    <h2>
      <span class="cap-numero">Capítulo {{ chapter.number }}</span>
      <span class="cap-titulo">{{ chapter.title }}</span>
    </h2>
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
        <span class="nombre">{{ entity.name }}</span>:
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
