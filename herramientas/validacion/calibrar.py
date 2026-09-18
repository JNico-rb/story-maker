#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Calibracion del detector de lengua (spec functional.md 9.6, requisito 3).

    python herramientas/validacion/calibrar.py
    python herramientas/validacion/calibrar.py --escribir

Mide el detector contra el etiquetado a mano y escribe calibracion.md. Sin este
numero, el validador seria otro erratas.md: dijo 0 y nadie sabia que faltaban 13.

Un acierto del detector cuenta como defecto etiquetado si el trozo que casa cae
dentro de la cita etiquetada, o al reves. Todo lo que no cae en ninguna cita es
un falso positivo y se imprime entero, para revisarlo a mano: un detector con
precision baja no mide calidad, mide ruido.

Se reportan DOS recalls: sobre los 13 defectos etiquetados (el que importa) y
sobre los que alguna clase del v1 puede cazar (el techo declarado). La distancia
entre los dos es lo que falta por construir, no lo que el detector falla.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))

from patrones import CLASES, VERSION, compilados, hash_patrones  # noqa: E402

ETIQUETADO = AQUI / "etiquetado" / "ascensores-lengua-v1.json"


def normalizar(t):
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).casefold().strip()


def hallazgos(texto):
    """Cada acierto del detector, con su clase y el trozo exacto que casa."""
    out = []
    for clase, rx in compilados():
        for m in rx.finditer(texto):
            ini = max(0, m.start() - 40)
            fin = min(len(texto), m.end() + 30)
            out.append({"clase": clase, "trozo": m.group(0),
                        "contexto": re.sub(r"\s+", " ", texto[ini:fin])})
    return out


def calibrar():
    etq = json.loads(ETIQUETADO.read_text(encoding="utf-8"))
    filas, tp, fp, etiquetas_vistas = [], 0, 0, set()
    falsos = []
    esperados, techo = [], []

    for m in etq["manuscritos"]:
        texto = (RAIZ / m["ruta"]).read_text(encoding="utf-8")
        hs = hallazgos(texto)
        citas = [(d["id"], normalizar(d["cita"]), d) for d in m["defectos"]]
        esperados += [d["id"] for d in m["defectos"]]
        techo += [d["id"] for d in m["defectos"] if d["detectable_v1"]]

        for h in hs:
            trozo = normalizar(h["trozo"])
            casa = next((i for i, c, _ in citas if trozo in c or c in trozo), None)
            if casa:
                tp += 1
                etiquetas_vistas.add(casa)
            else:
                fp += 1
                falsos.append((m["lado"], h["clase"], h["trozo"], h["contexto"]))
        filas.append((m["lado"], len(texto.split()), len(hs), len(m["defectos"])))

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = len(etiquetas_vistas) / len(esperados) if esperados else None
    recall_techo = (len([i for i in etiquetas_vistas if i in techo]) / len(techo)
                    if techo else None)
    no_vistos = [i for i in esperados if i not in etiquetas_vistas]

    return {
        "version": VERSION, "hash": hash_patrones(),
        "filas": filas, "tp": tp, "fp": fp,
        "precision": precision, "recall": recall, "recall_techo": recall_techo,
        "esperados": len(esperados), "techo": len(techo),
        "vistos": sorted(etiquetas_vistas), "no_vistos": no_vistos,
        "falsos": falsos,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--escribir", action="store_true", help="escribe calibracion.md")
    args = p.parse_args()
    r = calibrar()

    print("detector {} hash {}".format(r["version"], r["hash"]))
    for lado, pal, hs, defs in r["filas"]:
        print("  {}: {} palabras, {} aciertos del detector, {} defectos etiquetados".format(
            lado, pal, hs, defs))
    print("  precision  {:.3f}  ({} aciertos buenos de {} marcados)".format(
        r["precision"], r["tp"], r["tp"] + r["fp"]) if r["precision"] is not None else "  precision: sin datos")
    print("  recall     {:.3f}  ({} de {} defectos etiquetados)".format(
        r["recall"], len(r["vistos"]), r["esperados"]))
    print("  recall/techo {:.3f}  ({} clases del v1 cubren {} de {})".format(
        r["recall_techo"], len(CLASES), r["techo"], r["esperados"]))
    print("  no vistos: {}".format(", ".join(r["no_vistos"]) or "ninguno"))
    if r["falsos"]:
        print("  FALSOS POSITIVOS ({}):".format(len(r["falsos"])))
        for lado, clase, trozo, ctx in r["falsos"]:
            print("    [{}] {:34} {!r}".format(lado, clase, trozo))
            print("         ...{}...".format(ctx))

    if args.escribir:
        destino = AQUI / "calibracion.md"
        destino.write_text(informe(r), encoding="utf-8")
        print("\nescrito {}".format(destino.relative_to(RAIZ).as_posix()))


def informe(r):
    lineas = [
        "# Calibración del detector de lengua",
        "",
        "Detector `{}`, hash `{}`. Medido contra "
        "[etiquetado/ascensores-lengua-v1.json](etiquetado/ascensores-lengua-v1.json), "
        "que es verdad de campo etiquetada a mano sobre los manuscritos completos "
        "de las dos novelas del repositorio.".format(r["version"], r["hash"]),
        "",
        "| | Palabras | Marcados por el detector | Etiquetados a mano |",
        "|---|---:|---:|---:|",
    ]
    for lado, pal, hs, defs in r["filas"]:
        lineas.append("| {} | {} | {} | {} |".format(lado, pal, hs, defs))
    lineas += [
        "",
        "| Medida | Valor | Qué significa |",
        "|---|---:|---|",
        "| Precisión | **{:.3f}** | de lo que marca, cuánto es de verdad un error |".format(r["precision"]),
        "| Recall | **{:.3f}** | de los {} defectos etiquetados, cuántos ve |".format(r["recall"], r["esperados"]),
        "| Recall sobre el techo | **{:.3f}** | de los {} que alguna clase del v1 puede cazar |".format(r["recall_techo"], r["techo"]),
        "",
        "**No vistos**: {}.".format(", ".join(r["no_vistos"]) or "ninguno"),
        "",
        "## El techo, que es lo importante",
        "",
        "De los {} defectos etiquetados, solo **{}** caen en una clase que el "
        "detector v1 puede expresar. Los otros {} exigen cosas que una lista de "
        "patrones no da: un léxico para las palabras inexistentes, y análisis "
        "morfosintáctico para el tiempo verbal. Están declarados uno a uno en el "
        "etiquetado con `detectable_v1: false`.".format(
            r["esperados"], r["techo"], r["esperados"] - r["techo"]),
        "",
        "Leído de otra forma: **el recall de {:.2f} no es un fallo del detector, "
        "es el alcance de la v1**. Para subirlo hace falta una dependencia nueva "
        "(spaCy o language-tool), y eso ata la línea base a una versión externa.".format(r["recall"]),
        "",
        "## Cuándo hay que rehacer esto",
        "",
        "Cuando cambie `patrones.py` (el hash lo delata), cuando se añada un "
        "manuscrito al etiquetado, o cuando entre una dependencia de análisis "
        "lingüístico. Mientras tanto, estos dos números son los que hay que citar "
        "al lado de cualquier puntuación de lengua.",
    ]
    return "\n".join(lineas) + "\n"


if __name__ == "__main__":
    main()
