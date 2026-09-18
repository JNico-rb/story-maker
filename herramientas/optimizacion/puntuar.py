#!/usr/bin/env python3
"""Puntua una vuelta del bucle contra la verdad de campo (spec functional.md 9.5.3).

    python herramientas/optimizacion/puntuar.py --carpeta <c> --vuelta 03 \
        --split control --agente revisor-encargo --metrica recall_revisor \
        --conjunto defectos-v1
    python herramientas/optimizacion/puntuar.py --publicar --carpeta <c> --vuelta 03

El calculo es LOCAL y escribe <carpeta>/vuelta-NN/<split>/score.json. La subida a
Langfuse va aparte y es fail-open: si Langfuse no responde, el bucle sigue y solo
se pierde la curva (spec 9.3 regla 3). Langfuse proyecta; no decide.

El emparejamiento de citas NO se reimplementa aqui: se importa de
herramientas/evaluadores/, para que la logica que puntua en Langfuse y la que
puntua en local sean literalmente la misma funcion.
"""

import argparse
import json
import os
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "herramientas" / "evaluadores"))

from preparar import CONTRATO, leer_conjunto, peticion  # noqa: E402
import recall_revisor as _recall  # noqa: E402
import cita_verificable as _cita  # noqa: E402

MIN_CITA_VERIFICABLE = 0.90
FACTOR_TAMANO = 1.3


def informe_de(carpeta, vuelta, split, id_caso):
    ruta = Path(carpeta) / "vuelta-{}".format(vuelta) / split / "{}.json".format(id_caso)
    if not ruta.exists():
        return None
    return _recall._a_json(ruta.read_text(encoding="utf-8"))


def recall(casos, carpeta, vuelta, split, agente):
    """Micro-media: defectos vistos / defectos esperados, sobre todos los casos.

    Micro y no macro a proposito: con pocos defectos por caso, la macro-media da
    el mismo peso a un caso con un defecto que a uno con seis, y el numero se
    mueve por el reparto en vez de por el prompt.
    """
    gravedades = CONTRATO.get(agente, set())
    vistos = esperados = 0
    por_clase, no_vistos, sin_informe = {}, [], []

    for caso in casos:
        informe = informe_de(carpeta, vuelta, split, caso["id"])
        if informe is None:
            sin_informe.append(caso["id"])
        texto, _ = _recall._texto_problemas(informe or {})
        for d in caso.get("defectos") or []:
            if d.get("gravedad") not in gravedades:
                continue          # no es su pregunta: no cuenta ni a favor ni en contra
            esperados += 1
            clase = str(d.get("clase") or "sin_clase")
            cuenta = por_clase.setdefault(clase, {"esperados": 0, "vistos": 0})
            cuenta["esperados"] += 1
            cita = str(d.get("cita") or "").strip()
            acierto = (bool(texto) and len(cita) >= _recall.MIN_CARACTERES_CITA
                       and _recall._normalizar(cita) in texto)
            if acierto:
                vistos += 1
                cuenta["vistos"] += 1
            else:
                no_vistos.append("{} [{}] {}".format(caso["id"], clase, cita[:60]))

    return {
        "valor": (vistos / esperados) if esperados else None,
        "vistos": vistos,
        "esperados": esperados,
        "por_clase": por_clase,
        "no_vistos": no_vistos[:30],
        "casos_sin_informe": sin_informe,
    }


def cita_verificable(casos, carpeta, vuelta, split):
    """Fraccion de problemas del informe cuya cita aparece en el capitulo.

    Es la restriccion que tapa el camino barato: inventar problemas sube el
    recall, pero hunde esto.
    """
    verificados = total = con_cita = 0
    fallidos = []
    for caso in casos:
        informe = informe_de(carpeta, vuelta, split, caso["id"])
        if not isinstance(informe, dict):
            continue
        ruta_cap = RAIZ / caso["entradas"]["capitulo"]
        if not ruta_cap.exists():
            continue
        capitulo = _cita._normalizar(ruta_cap.read_text(encoding="utf-8"))
        for problema in informe.get("problemas") or []:
            candidatas = _cita._citas(problema)
            total += 1
            if any(campo in ("cita", "cita_literal") for campo, _ in candidatas):
                con_cita += 1
            if not candidatas:
                fallidos.append("{}: problema sin cita".format(caso["id"]))
                continue
            if any(_cita._normalizar(c) in capitulo for _, c in candidatas):
                verificados += 1
            else:
                fallidos.append("{}: {}".format(caso["id"], candidatas[0][1][:60]))
    return {
        "valor": (verificados / total) if total else None,
        "verificados": verificados,
        "problemas": total,
        "fallidos": fallidos[:20],
        # Solo es exigible si el contrato del agente tiene un campo de cita. El de
        # revisor-encargo (spec 5.6) da donde/que/por_que y ninguno es una cita
        # literal obligatoria: exigirle 0,90 seria medirle por algo que su contrato
        # no le deja cumplir. Queda informativa hasta que se decida A4.
        "aplicable": con_cita > 0,
        "problemas_con_cita": con_cita,
    }


def tamano(carpeta, vuelta):
    prod = (Path(carpeta) / "produccion.md").read_text(encoding="utf-8")
    var = Path(carpeta) / "vuelta-{}".format(vuelta) / "variante.md"
    texto = var.read_text(encoding="utf-8") if var.exists() else prod
    pal, tope = len(texto.split()), int(len(prod.split()) * FACTOR_TAMANO)
    return {"palabras_prompt": pal, "tope_palabras": tope, "cumple": pal <= tope}


def puntuar(carpeta, vuelta, split, agente, metrica, conjunto):
    casos, errores = leer_conjunto(conjunto)
    if errores:
        raise SystemExit("conjunto invalido: " + "; ".join(errores[:5]))
    casos = [c for c in casos if c.get("split") == split]

    r = recall(casos, carpeta, vuelta, split, agente)
    cv = cita_verificable(casos, carpeta, vuelta, split)
    tm = tamano(carpeta, vuelta)

    incumplidas = []
    if cv["aplicable"] and cv["valor"] is not None and cv["valor"] < MIN_CITA_VERIFICABLE:
        incumplidas.append("cita_verificable {:.2f} < {:.2f}".format(
            cv["valor"], MIN_CITA_VERIFICABLE))
    if not tm["cumple"]:
        incumplidas.append("palabras_prompt {} > {}".format(
            tm["palabras_prompt"], tm["tope_palabras"]))

    score = {
        "vuelta": vuelta,
        "split": split,
        "agente": agente,
        "metrica": metrica,
        "conjunto": conjunto,
        "casos": len(casos),
        metrica: r["valor"],
        "detalle": r,
        "restricciones": {
            "cita_verificable": cv,
            "tamano": tm,
            "incumplidas": incumplidas,
        },
    }
    destino = Path(carpeta) / "vuelta-{}".format(vuelta) / split / "score.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(score, indent=1, ensure_ascii=False), encoding="utf-8")

    valor = "sin defectos puntuables" if r["valor"] is None else "{:.3f}".format(r["valor"])
    print("{} vuelta {} split {}: {} = {} ({}/{} defectos)".format(
        agente, vuelta, split, metrica, valor, r["vistos"], r["esperados"]))
    if r["casos_sin_informe"]:
        print("  sin informe: {}".format(", ".join(r["casos_sin_informe"])))
    if incumplidas:
        print("  RESTRICCION INCUMPLIDA: {}".format("; ".join(incumplidas)))
    return score


def publicar(carpeta, vuelta):
    """Sube la vuelta a Langfuse como experiment run. Fail-open por contrato:
    la skill la llama con `|| true` y el bucle no depende de esto."""
    carpeta = Path(carpeta)
    ejecucion = json.loads((carpeta / "ejecucion.json").read_text(encoding="utf-8"))
    nombre = "{}-vuelta-{}".format(carpeta.name, vuelta)
    subidos = 0
    for split in ("busqueda", "control"):
        ruta = carpeta / "vuelta-{}".format(vuelta) / split / "score.json"
        if not ruta.exists():
            continue
        score = json.loads(ruta.read_text(encoding="utf-8"))
        if score[score["metrica"]] is None:
            continue
        peticion("POST", "/api/public/scores", {
            "name": "{}_{}".format(score["metrica"], split),
            "value": score[score["metrica"]],
            "dataType": "NUMERIC",
            "traceId": None,
            "comment": "vuelta {} de {}; {}/{} defectos; restricciones: {}".format(
                vuelta, carpeta.name, score["detalle"]["vistos"],
                score["detalle"]["esperados"],
                ", ".join(score["restricciones"]["incumplidas"]) or "cumplidas"),
            "metadata": {"run": nombre, "agente": ejecucion["agente"],
                         "conjunto": ejecucion["conjunto"], "split": split},
        })
        subidos += 1
    print("publicadas {} puntuaciones de la vuelta {}".format(subidos, vuelta))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--carpeta", required=True)
    p.add_argument("--vuelta", required=True)
    p.add_argument("--split", choices=("busqueda", "control"))
    p.add_argument("--agente")
    p.add_argument("--metrica")
    p.add_argument("--conjunto")
    p.add_argument("--publicar", action="store_true")
    args = p.parse_args()

    if args.publicar:
        if not (os.environ.get("LANGFUSE_PUBLIC_KEY")
                and os.environ.get("LANGFUSE_SECRET_KEY")):
            raise SystemExit("sin credenciales de Langfuse; la curva se pierde y "
                             "el bucle sigue")
        publicar(args.carpeta, args.vuelta)
        return

    for obligatorio in ("split", "agente", "metrica", "conjunto"):
        if not getattr(args, obligatorio):
            raise SystemExit("falta --{}".format(obligatorio))
    puntuar(args.carpeta, args.vuelta, args.split, args.agente,
            args.metrica, args.conjunto)


if __name__ == "__main__":
    main()
