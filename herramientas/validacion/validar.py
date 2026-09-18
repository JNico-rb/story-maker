#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador de manuscrito (spec functional.md 9.6).

    python herramientas/validacion/validar.py <carpeta> [--congelar-base]
    python herramientas/validacion/validar.py <carpeta> --publicar

Punta el TEXTO producido, no lo que los revisores declararon. Es la diferencia
con 8.3: cuatro de sus seis metricas son autoinformadas, y por eso el sistema
devolvio 6/6 CUMPLE sobre un manuscrito con 30 defectos verificados (E5c).

Fuera del harness: /novela no lo llama nunca, no escribe en novelas/ y la
publicacion en Langfuse es fail-open (9.3 reglas 2, 3 y 4).

NO es un bucle: mide una vez y devuelve un numero. No tiene condiciones de
parada ni vectores de mejora, y eso esta decidido, no olvidado (9.6).
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))

from patrones import VERSION, compilados, hash_patrones  # noqa: E402

ESCALA = json.loads((AQUI / "escala.json").read_text(encoding="utf-8"))
BASE = RAIZ / "validaciones" / "_base.json"


# --- precondiciones (TRIGGER, 9.6) -----------------------------------------

def precondiciones(carpeta, base):
    """Las tres del TRIGGER. Devuelve (lista de lineas, ok)."""
    out, ok = [], True

    def di(bien, texto):
        nonlocal ok
        out.append("  {}  {}".format("OK  " if bien else "FALTA", texto))
        ok = ok and bien

    estado_p = carpeta / "estado.json"
    manuscrito_p = carpeta / "manuscrito.md"
    if not estado_p.exists():
        di(False, "no hay estado.json en {}".format(carpeta))
        return out, False
    estado = json.loads(estado_p.read_text(encoding="utf-8"))
    di(estado.get("etapa") == "completa" and manuscrito_p.exists(),
       "ejecucion completa (8.7): etapa={}, manuscrito.md={}".format(
           estado.get("etapa"), "si" if manuscrito_p.exists() else "no"))

    if base:
        mismo = base.get("detector", {}).get("hash") == hash_patrones()
        di(mismo, "detector congelado: base {} / ahora {}".format(
            base.get("detector", {}).get("hash"), hash_patrones()))
        misma_escala = base.get("escala_version") == ESCALA["version_escala"]
        di(misma_escala, "escala congelada: base v{} / ahora v{}".format(
            base.get("escala_version"), ESCALA["version_escala"]))
    else:
        di(True, "sin linea base: nada que cotejar (usa --congelar-base)")
    return out, ok


# --- lectura ----------------------------------------------------------------

def capitulos_aprobados(carpeta):
    """El intento aprobado de cada capitulo, segun estado.json. Es la misma
    fuente que usa 8.7: no se adivina cual es el bueno."""
    estado = json.loads((carpeta / "estado.json").read_text(encoding="utf-8"))
    out = {}
    for n, d in sorted((estado.get("capitulos") or {}).items(), key=lambda x: int(x[0])):
        k = d.get("aprobado")
        if k is None:
            continue
        p = carpeta / "capitulos" / "{:02d}".format(int(n)) / "intento-{}.md".format(k)
        if p.exists():
            out["{:02d}".format(int(n))] = p.read_text(encoding="utf-8")
    return out


# --- dimensiones ------------------------------------------------------------

def lengua(texto):
    hallazgos = []
    for clase, rx in compilados():
        for m in rx.finditer(texto):
            ini, fin = max(0, m.start() - 45), min(len(texto), m.end() + 30)
            hallazgos.append({"clase": clase, "cita": m.group(0),
                              "contexto": re.sub(r"\s+", " ", texto[ini:fin])})
    return hallazgos


def _ngramas(texto, n):
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    pal = re.findall(r"\w+", t)
    return {" ".join(pal[i:i + n]) for i in range(len(pal) - n + 1)}


def repeticion(caps, n):
    g = {c: _ngramas(t, n) for c, t in caps.items()}
    claves = sorted(g)
    total, pares = 0, []
    for i, a in enumerate(claves):
        for b in claves[i + 1:]:
            comun = g[a] & g[b]
            if comun:
                total += len(comun)
                pares.append({"capitulos": [a, b], "comunes": len(comun),
                              "ejemplo": sorted(comun)[0]})
    return total, sorted(pares, key=lambda x: -x["comunes"])


def normalizar(tasa, tope):
    """tasa 0 -> 1,0 ; tasa >= tope -> 0,0 ; lineal en medio."""
    return max(0.0, min(1.0, 1.0 - tasa / tope))


# --- puntuacion -------------------------------------------------------------

def puntuar(carpeta):
    caps = capitulos_aprobados(carpeta)
    if not caps:
        raise SystemExit("no hay capitulos aprobados legibles en {}".format(carpeta))
    texto = "\n\n".join(caps[c] for c in sorted(caps))
    palabras = len(texto.split())

    hl = lengua(texto)
    nrep, pares = repeticion(caps, ESCALA["n_gramas"])

    dims = {}
    for nombre, bruto in (("lengua", len(hl)), ("repeticion", nrep)):
        cfg = ESCALA["dimensiones"][nombre]
        tasa = 1000.0 * bruto / palabras
        dims[nombre] = {
            "bruto": bruto, "tasa_mil": round(tasa, 3),
            "tope_cero": cfg["tope_cero"], "peso": cfg["peso"],
            "normalizado": round(normalizar(tasa, cfg["tope_cero"]), 3),
        }
    global_ = sum(d["normalizado"] * d["peso"] for d in dims.values())

    return {
        "manuscrito": carpeta.resolve().relative_to(RAIZ).as_posix(),
        "detector": {"version": VERSION, "hash": hash_patrones()},
        "escala_version": ESCALA["version_escala"],
        "palabras": palabras, "capitulos": len(caps),
        "dimensiones": dims,
        "global": round(global_, 3),
        "hallazgos_lengua": hl,
        "pares_repetidos": pares[:5],
        "reservas": [
            "n=1 por configuracion: no se puede separar el efecto de la config del "
            "azar de esta generacion; ninguna mejora se declara establecida",
            "detector v1: precision 1,000 y recall 0,462 (calibracion.md); el nivel "
            "absoluto de lengua es optimista, los deltas entre manuscritos no",
            "clases A, B y C de E5 (coherencia, verosimilitud, mundo post-IA) fuera "
            "de la v1: exigen un juez LLM independiente que hoy no existe (A14)",
        ],
    }


# --- salida -----------------------------------------------------------------

def informe(r, base):
    L = ["# Validación — {}".format(Path(r["manuscrito"]).name), "",
         "Detector `{}` (hash `{}`), escala v{}. "
         "{} palabras en {} capítulos aprobados.".format(
             r["detector"]["version"], r["detector"]["hash"], r["escala_version"],
             r["palabras"], r["capitulos"]), "",
         "| Dimensión | Tasa /mil | Normalizado | Peso |" +
         (" Base | Delta |" if base else ""),
         "|---|---:|---:|---:|" + ("---:|---:|" if base else "")]
    for nombre, d in r["dimensiones"].items():
        fila = "| {} | {:.2f} | {:.3f} | {:.2f} |".format(
            nombre, d["tasa_mil"], d["normalizado"], d["peso"])
        if base:
            bd = base["dimensiones"][nombre]["normalizado"]
            fila += " {:.3f} | {:+.3f} |".format(bd, d["normalizado"] - bd)
        L.append(fila)
    L.append("")
    if base:
        L.append("**Índice global: {:.3f}** · base {:.3f} · **delta {:+.3f}**".format(
            r["global"], base["global"], r["global"] - base["global"]))
    else:
        L.append("**Índice global: {:.3f}** (línea base)".format(r["global"]))
    L += ["", "## Hallazgos de lengua", ""]
    if r["hallazgos_lengua"]:
        for h in r["hallazgos_lengua"]:
            L.append("- **{}** — «{}»  \n  `…{}…`".format(
                h["clase"], h["cita"], h["contexto"]))
    else:
        L.append("Ninguno. Con recall 0,462, esto significa «ninguno de los que el "
                 "detector v1 sabe ver», no «ninguno».")
    L += ["", "## Capítulos que más se parecen", ""]
    if r["pares_repetidos"]:
        for p in r["pares_repetidos"]:
            L.append("- capítulos {} y {}: {} secuencias de {} palabras comunes "
                     "(p. ej. «{}»)".format(p["capitulos"][0], p["capitulos"][1],
                                            p["comunes"], ESCALA["n_gramas"],
                                            p["ejemplo"]))
    else:
        L.append("Ninguno.")
    L += ["", "## Reservas", ""] + ["- {}".format(x) for x in r["reservas"]]
    return "\n".join(L) + "\n"


def publicar(r):
    """Fail-open por contrato: la skill lo llama con `|| true`."""
    import base64
    import urllib.request
    if not (os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY")):
        raise SystemExit("sin credenciales de Langfuse; el resultado ya esta en disco")
    host = (os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com").rstrip("/")
    cred = base64.b64encode("{}:{}".format(
        os.environ["LANGFUSE_PUBLIC_KEY"], os.environ["LANGFUSE_SECRET_KEY"]).encode()).decode()
    for nombre, d in list(r["dimensiones"].items()) + [("global", {"normalizado": r["global"]})]:
        cuerpo = {"name": "manuscrito_" + nombre, "value": d["normalizado"],
                  "dataType": "NUMERIC", "traceId": None,
                  "comment": "{} · detector {} · escala v{}".format(
                      r["manuscrito"], r["detector"]["hash"], r["escala_version"]),
                  "metadata": {"manuscrito": r["manuscrito"],
                               "detector": r["detector"]["hash"]}}
        req = urllib.request.Request(host + "/api/public/scores",
                                     data=json.dumps(cuerpo).encode(), method="POST")
        req.add_header("Authorization", "Basic " + cred)
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req).read()
    print("publicadas {} puntuaciones".format(len(r["dimensiones"]) + 1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("carpeta")
    p.add_argument("--congelar-base", action="store_true")
    p.add_argument("--publicar", action="store_true")
    args = p.parse_args()

    carpeta = Path(args.carpeta).resolve()
    base = json.loads(BASE.read_text(encoding="utf-8")) if BASE.exists() else None

    lineas, ok = precondiciones(carpeta, None if args.congelar_base else base)
    print("precondiciones")
    print("\n".join(lineas))
    if not ok:
        raise SystemExit("\nNo se valida: falta una precondicion.")

    r = puntuar(carpeta)
    destino = RAIZ / "validaciones" / carpeta.name
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "score.json").write_text(
        json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
    (destino / "informe.md").write_text(
        informe(r, None if args.congelar_base else base), encoding="utf-8")

    print("\n{}  ·  {} palabras en {} capitulos".format(
        carpeta.name, r["palabras"], r["capitulos"]))
    for nombre, d in r["dimensiones"].items():
        linea = "  {:12} {:6.2f} /mil  ->  {:.3f}".format(
            nombre, d["tasa_mil"], d["normalizado"])
        if base and not args.congelar_base:
            bd = base["dimensiones"][nombre]["normalizado"]
            linea += "     base {:.3f}   {:+.3f}".format(bd, d["normalizado"] - bd)
        print(linea)
    linea = "  {:12} {:>14}      {:.3f}".format("GLOBAL", "", r["global"])
    if base and not args.congelar_base:
        linea += "     base {:.3f}   {:+.3f}".format(base["global"], r["global"] - base["global"])
    print(linea)

    if args.congelar_base:
        BASE.parent.mkdir(parents=True, exist_ok=True)
        BASE.write_text(json.dumps(r, indent=1, ensure_ascii=False), encoding="utf-8")
        print("\n  LINEA BASE CONGELADA en {}".format(BASE.relative_to(RAIZ).as_posix()))
    print("  n=1 por configuracion: no se declara mejora ni regresion establecida")

    if args.publicar:
        publicar(r)


if __name__ == "__main__":
    main()
