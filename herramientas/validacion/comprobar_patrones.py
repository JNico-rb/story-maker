#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puerta del detector de lengua (spec functional.md 9.6).

    python herramientas/validacion/comprobar_patrones.py

Sale 0 si el detector puede usarse, 1 si no. Tres comprobaciones por clase:

  1. casa con todos sus ejemplos positivos (el patron hace lo que dice);
  2. no casa con ninguno de sus negativos (no se lleva castellano correcto);
  3. no contiene tres palabras seguidas de ninguna cita del etiquetado (el
     patron no esta escrito contra el caso concreto; una palabra suelta del
     lexico si vale, porque es un miembro de la clase y no la instancia).

La 3 es la importante y es la misma regla que comprobar_variante.py impone al
optimizador: quien escribe el examen no puede copiar las respuestas. Sin ella,
el detector encontraria exactamente los 13 defectos que se uso para escribirlo y
el numero no medira nada sobre un manuscrito nuevo.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from patrones import CLASES, VERSION, hash_patrones  # noqa: E402

ETIQUETADO = AQUI / "etiquetado" / "ascensores-lengua-v1.json"
MIN_PALABRAS_SOLAPE = 3


def sin_tildes(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c)).casefold()


def citas_del_etiquetado():
    d = json.loads(ETIQUETADO.read_text(encoding="utf-8"))
    return [x["cita"] for m in d["manuscritos"] for x in m["defectos"]]


def main():
    citas = citas_del_etiquetado()
    fallos = []

    def di(ok, clase, prueba, detalle=""):
        if not ok:
            print("RECHAZA  {:38} {}{}".format(clase, prueba,
                                               ": " + detalle if detalle else ""))
            fallos.append((clase, prueba))

    for c in CLASES:
        rx = re.compile(c["patron"], re.IGNORECASE)

        fallan = [e for e in c["positivos"] if not rx.search(e)]
        di(not fallan, c["clase"], "casa sus positivos",
           "no casa: " + " | ".join(fallan))

        casan = [e for e in c["negativos"] if rx.search(e)]
        di(not casan, c["clase"], "respeta sus negativos",
           "casa mal: " + " | ".join(casan))

        # 3. el patron no lleva dentro un trozo de FRASE de una cita etiquetada.
        #    Se mide en palabras y no en caracteres: una palabra suelta del lexico
        #    ("conocimiento") es un miembro de la clase y vale; tres palabras
        #    seguidas del caso concreto es copiar el examen.
        patron_plano = sin_tildes(c["patron"])
        copiadas = []
        for cita in citas:
            pal = sin_tildes(cita).split()
            for i in range(len(pal) - MIN_PALABRAS_SOLAPE + 1):
                trozo = " ".join(pal[i:i + MIN_PALABRAS_SOLAPE])
                if trozo in patron_plano:
                    copiadas.append(trozo)
                    break
        di(not copiadas, c["clase"], "no copia el examen",
           "trozos de citas etiquetadas: " + " | ".join(copiadas[:3]))

    if fallos:
        print("\nDetector RECHAZADO: {} comprobaciones fallan.".format(len(fallos)))
        sys.exit(1)
    print("Detector {} (hash {}) apto: {} clases, {} positivos, {} negativos.".format(
        VERSION, hash_patrones(), len(CLASES),
        sum(len(c["positivos"]) for c in CLASES),
        sum(len(c["negativos"]) for c in CLASES)))


if __name__ == "__main__":
    main()
