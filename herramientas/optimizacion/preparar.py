#!/usr/bin/env python3
"""Prerrequisitos del bucle de optimizacion (spec functional.md 9.5.1).

Fuera del harness: no lo llama /novela nunca. No escribe en novelas/.

    python herramientas/optimizacion/preparar.py --comprobar \
        --agente revisor-encargo --metrica recall_revisor --conjunto defectos-v1
    python herramientas/optimizacion/preparar.py --subir-conjunto --conjunto defectos-v1
    python herramientas/optimizacion/preparar.py --publicar-candidato --carpeta optimizaciones/...

--comprobar sale con 0 si los cinco requisitos estan, 1 si falta alguno, e
imprime uno por linea. Es la unica puerta del bucle: mientras devuelva 1, no se
gasta ni una invocacion del agente optimizado.

Variables de entorno (solo --subir-conjunto y --publicar-candidato):
LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
CONJUNTOS = AQUI / "conjuntos"
EVALUADORES = RAIZ / "herramientas" / "evaluadores"

# Que gravedades emite cada agente (spec 5.6). Un defecto de gravedad 1 no puede
# contar contra el revisor de encargo: no es que falle, es que no es su pregunta.
CONTRATO = {
    "revisor-encargo": {2, 4},
    "revisor-continuidad": {1, 5},
}

MIN_DEFECTOS = 30
SPLITS = ("busqueda", "control")


# --- conjunto --------------------------------------------------------------

def ruta_conjunto(nombre):
    return CONJUNTOS / "{}.jsonl".format(nombre)


def leer_conjunto(nombre):
    """Lee el .jsonl y valida su forma. Devuelve (casos, errores)."""
    ruta = ruta_conjunto(nombre)
    if not ruta.exists():
        return [], ["no existe {}".format(ruta.relative_to(RAIZ))]

    casos, errores, vistos = [], [], set()
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        try:
            caso = json.loads(linea)
        except ValueError as err:
            errores.append("linea {}: no parsea ({})".format(n, err))
            continue
        for clave in ("id", "split", "entradas", "defectos"):
            if clave not in caso:
                errores.append("linea {}: falta '{}'".format(n, clave))
        if caso.get("split") not in SPLITS:
            errores.append("linea {}: split '{}' no es busqueda|control".format(
                n, caso.get("split")))
        if caso.get("id") in vistos:
            errores.append("linea {}: id '{}' repetido".format(n, caso.get("id")))
        vistos.add(caso.get("id"))
        for d in caso.get("defectos") or []:
            if not str(d.get("cita") or "").strip():
                errores.append("linea {}: un defecto sin 'cita'".format(n))
            if "gravedad" not in d:
                errores.append("linea {}: un defecto sin 'gravedad' (null si no "
                               "es de ningun contrato)".format(n))
        casos.append(caso)
    return casos, errores


def puntuables(casos, agente):
    """Defectos del conjunto que caen dentro del contrato del agente."""
    gravedades = CONTRATO.get(agente, set())
    total = 0
    for caso in casos:
        for d in caso.get("defectos") or []:
            if d.get("gravedad") in gravedades:
                total += 1
    return total


def reparto(casos, agente):
    """(defectos puntuables, casos) por split."""
    gravedades = CONTRATO.get(agente, set())
    out = {s: {"defectos": 0, "casos": 0} for s in SPLITS}
    for caso in casos:
        s = caso.get("split")
        if s not in out:
            continue
        out[s]["casos"] += 1
        out[s]["defectos"] += sum(
            1 for d in (caso.get("defectos") or []) if d.get("gravedad") in gravedades)
    return out


# --- los cinco requisitos --------------------------------------------------

def comprobar(agente, metrica, conjunto):
    fallos = []

    def di(ok, n, texto):
        print("{}  {}. {}".format("OK   " if ok else "FALTA", n, texto))
        if not ok:
            fallos.append(n)

    if agente not in CONTRATO:
        di(False, 0, "agente '{}' sin contrato de gravedades conocido; "
                     "anade su fila a CONTRATO en preparar.py".format(agente))
        return fallos

    # 1. conjunto etiquetado
    casos, errores = leer_conjunto(conjunto)
    if errores:
        di(False, 1, "conjunto '{}': {}".format(conjunto, "; ".join(errores[:5])))
    else:
        n_punt = puntuables(casos, agente)
        rep = reparto(casos, agente)
        detalle = ("{} defectos puntuables para {} en {} casos "
                   "(busqueda {}d/{}c, control {}d/{}c)".format(
                       n_punt, agente, len(casos),
                       rep["busqueda"]["defectos"], rep["busqueda"]["casos"],
                       rep["control"]["defectos"], rep["control"]["casos"]))
        if n_punt < MIN_DEFECTOS:
            di(False, 1, detalle + "; hacen falta {}. Los defectos fuera del "
                                   "contrato de {} no cuentan: no puede verlos "
                                   "(spec 5.6)".format(MIN_DEFECTOS, agente))
        elif rep["control"]["defectos"] == 0 or rep["busqueda"]["defectos"] == 0:
            di(False, 1, detalle + "; un split se queda sin defectos puntuables")
        else:
            di(True, 1, detalle)

    # 2. metrica existente y calibrada
    mod = EVALUADORES / "{}.py".format(metrica)
    cal = EVALUADORES / "calibracion-{}.md".format(metrica)
    if not mod.exists():
        di(False, 2, "no existe {}".format(mod.relative_to(RAIZ)))
    elif not cal.exists():
        di(False, 2, "{} existe pero no esta calibrada: falta {} con su exactitud "
                     "contra el conjunto".format(metrica, cal.relative_to(RAIZ)))
    else:
        di(True, 2, "{} existe y esta calibrada ({})".format(
            metrica, cal.relative_to(RAIZ)))

    # 3. prompt en el repositorio y arbol limpio
    prompt = RAIZ / ".claude" / "agents" / "{}.md".format(agente)
    if not prompt.exists():
        di(False, 3, "no existe {}".format(prompt.relative_to(RAIZ)))
    else:
        sucio = subprocess.run(
            ["git", "status", "--porcelain", "--", str(prompt)],
            cwd=str(RAIZ), capture_output=True, text=True).stdout.strip()
        if sucio:
            di(False, 3, "{} tiene cambios sin commitear; el bucle lo sobrescribe "
                         "y los perderias".format(prompt.relative_to(RAIZ)))
        else:
            di(True, 3, "{} en git y limpio".format(prompt.relative_to(RAIZ)))

    # 4. juez distinto del optimizado (N/A si la metrica es de codigo)
    if mod.exists() and "llm" not in mod.read_text(encoding="utf-8")[:2000].lower():
        di(True, 4, "N/A: {} es un evaluador de codigo, no hay juez LLM que "
                    "contaminar".format(metrica))
    else:
        di(False, 4, "{} usa un juez LLM; comprueba a mano que su modelo no es el "
                     "del agente optimizado (hoy la unica conexion es "
                     "openrouter/free, que no lo garantiza: A14)".format(metrica))

    # 5. presupuesto: lo pasa la skill, aqui solo se deja constancia
    di(True, 5, "presupuesto declarado por la skill (--vueltas y "
                "--tope-invocaciones); en el hito 1 se cuenta en invocaciones "
                "porque Agent no devuelve tokens de subagente")

    return fallos


# --- transporte ------------------------------------------------------------

def peticion(metodo, ruta, cuerpo=None):
    base = os.environ.get("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
    credencial = base64.b64encode(
        "{}:{}".format(os.environ["LANGFUSE_PUBLIC_KEY"],
                       os.environ["LANGFUSE_SECRET_KEY"]).encode()).decode()
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(base.rstrip("/") + ruta, data=datos, method=metodo)
    req.add_header("Authorization", "Basic " + credencial)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def subir_conjunto(nombre):
    """Espejo del conjunto en Langfuse. La fuente de verdad es el .jsonl en git."""
    casos, errores = leer_conjunto(nombre)
    if errores:
        raise SystemExit("conjunto invalido: " + "; ".join(errores[:5]))
    peticion("POST", "/api/public/v2/datasets",
             {"name": nombre, "description": "Espejo de herramientas/optimizacion/"
                                             "conjuntos/{}.jsonl. La fuente de "
                                             "verdad es el fichero en git.".format(nombre)})
    for caso in casos:
        peticion("POST", "/api/public/dataset-items", {
            "datasetName": nombre,
            "id": caso["id"],
            "input": caso["entradas"],
            "expectedOutput": {"defectos": caso["defectos"]},
            "metadata": {"split": caso["split"]},
        })
    print("subidos {} casos a '{}'".format(len(casos), nombre))


def publicar_candidato(carpeta):
    """Publica mejor.md como version con etiqueta 'candidato'. Nunca 'produccion':
    quien promueve es el usuario, con un commit (spec 9.5.4)."""
    carpeta = Path(carpeta)
    ejecucion = json.loads((carpeta / "ejecucion.json").read_text(encoding="utf-8"))
    texto = (carpeta / "mejor.md").read_text(encoding="utf-8")
    peticion("POST", "/api/public/v2/prompts", {
        "name": "agente/{}".format(ejecucion["agente"]),
        "type": "text",
        "prompt": texto,
        "labels": ["candidato"],
        "config": {
            "origen": str(carpeta),
            "metrica": ejecucion["metrica"],
            "conjunto": ejecucion["conjunto"],
            "mejor_control": ejecucion.get("mejor_control"),
        },
    })
    print("publicado como candidato: agente/{}".format(ejecucion["agente"]))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--comprobar", action="store_true")
    p.add_argument("--subir-conjunto", action="store_true")
    p.add_argument("--publicar-candidato", action="store_true")
    p.add_argument("--agente")
    p.add_argument("--metrica")
    p.add_argument("--conjunto")
    p.add_argument("--carpeta")
    args = p.parse_args()

    if args.comprobar:
        for obligatorio in ("agente", "metrica", "conjunto"):
            if not getattr(args, obligatorio):
                raise SystemExit("--comprobar necesita --{}".format(obligatorio))
        fallos = comprobar(args.agente, args.metrica, args.conjunto)
        if fallos:
            print("\nEl bucle NO arranca: faltan los requisitos {}.".format(
                ", ".join(str(f) for f in fallos)))
            sys.exit(1)
        print("\nLos cinco requisitos estan. El bucle puede arrancar.")
        return

    if args.subir_conjunto:
        if not args.conjunto:
            raise SystemExit("--subir-conjunto necesita --conjunto")
        subir_conjunto(args.conjunto)
        return

    if args.publicar_candidato:
        if not args.carpeta:
            raise SystemExit("--publicar-candidato necesita --carpeta")
        publicar_candidato(args.carpeta)
        return

    raise SystemExit("elige --comprobar, --subir-conjunto o --publicar-candidato")


if __name__ == "__main__":
    main()
