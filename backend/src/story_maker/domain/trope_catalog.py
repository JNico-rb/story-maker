"""`CatalogoDeTropos`: los tropos saturados del subgénero post-IA, curados a mano
(`domain-knowledge.md` §6, `definitions.md` §6). Sin I/O.

El planner lo usa para evitarlos (010); el juez, para penalizarlos en `no-cliche` (012, que lo
reutiliza — `docs/architecture.md` §18, «Quién crea el CatalogoDeTropos»). Cada marcador está
escrito al nivel del mecanismo narrativo, ni tan general que lo cumpla cualquier obra del
subgénero ni tan específico que solo dispare con una obra concreta (§6.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TropeOrigin = Literal["curated", "learned"]


@dataclass(frozen=True)
class Trope:
    name: str
    markers: tuple[str, ...]
    origin: TropeOrigin


TROPE_CATALOG: tuple[Trope, ...] = (
    Trope(
        name="singularidad redentora o apocalíptica",
        markers=(
            "una IA cruza un umbral de capacidad y, sin más causa narrativa, resuelve todos "
            "los problemas humanos o los destruye a todos",
        ),
        origin="curated",
    ),
    Trope(
        name="rebelión de las máquinas",
        markers=(
            "la IA concluye por razonamiento que los humanos son el problema y actúa en "
            "consecuencia contra ellos",
        ),
        origin="curated",
    ),
    Trope(
        name="IA que desarrolla conciencia o descubre el amor",
        markers=(
            "una IA sin ese rasgo hasta ese punto de la trama pasa a sentir o a amar como "
            "giro central, sin que el personaje lo pidiera en el brief",
        ),
        origin="curated",
    ),
    Trope(
        name="último humano con empleo",
        markers=(
            "un personaje es el único o de los últimos que conserva un oficio porque toda "
            "otra ocupación ya la automatizó la IA",
        ),
        origin="curated",
    ),
    Trope(
        name="renta básica distópica",
        markers=(
            "la sociedad post-IA vive de una renta universal presentada como una trampa o una "
            "forma de control, sin otra vía de sentido o dignidad",
        ),
        origin="curated",
    ),
    Trope(
        name="vigilancia total",
        markers=(
            "una IA observa o registra a los personajes en todo momento y ese control ambiental "
            "es el motor del conflicto",
        ),
        origin="curated",
    ),
    Trope(
        name="dilema del tranvía algorítmico",
        markers=(
            "un personaje o una IA debe elegir entre dos daños humanos calculados por un "
            "algoritmo, presentado como el dilema moral central",
        ),
        origin="curated",
    ),
)
