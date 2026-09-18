#!/usr/bin/env python3
"""Puerta previa a instalar una variante (spec functional.md 9.5.5).

    python herramientas/optimizacion/comprobar_variante.py \
        --variante optimizaciones/revisor-encargo-.../vuelta-03/variante.md \
        --produccion optimizaciones/revisor-encargo-.../produccion.md \
        --conjunto defectos-v1 --metrica recall_revisor

Sale 0 si la variante puede instalarse, 1 si no, imprimiendo cada prohibicion
con OK o RECHAZA. Las cinco prohibiciones son de la spec y estan aqui en codigo
a proposito: una regla escrita solo en prosa se la salta un modelo sin querer
(E3), y esta en concreto protege el resultado del experimento entero.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI))

from preparar import CONTRATO, leer_conjunto  # noqa: E402

FACTOR_TAMANO = 1.3
MIN_CARACTERES_CITA = 8

# Si el agente sabe como lo puntuan, optimiza al que lo puntua y no a su tarea.
PROHIBIDAS = re.compile(
    r"recall_revisor|cita_verificable|redundancia_resumen|lengua_erratas|"
    r"verosimilitud_dominio|coherencia_interna|mundo_presente|"
    r"langfuse|evaluador|\bscore\b|puntuaci[oó]n|conjunto etiquetado",
    re.I)

CLAVES_SALIDA = ("veredicto", "problemas", "observaciones")


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for comilla in ("«", "»", "“", "”", "‘", "’"):
        texto = texto.replace(comilla, " ")
    return re.sub(r"\s+", " ", texto).casefold().strip()


def partir(texto):
    """Devuelve (frontmatter como dict de lineas, cuerpo)."""
    if not texto.startswith("---\n"):
        return None, texto
    fin = texto.find("\n---\n", 4)
    if fin == -1:
        return None, texto
    fm = {}
    for linea in texto[4:fin].splitlines():
        if ":" in linea and not linea.startswith(" "):
            clave, valor = linea.split(":", 1)
            fm[clave.strip()] = valor.strip()
    return fm, texto[fin + 5:]


def primer_parrafo(cuerpo):
    for bloque in cuerpo.split("\n\n"):
        if bloque.strip():
            return bloque.strip()
    return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variante", required=True)
    p.add_argument("--produccion", required=True)
    p.add_argument("--conjunto", required=True)
    p.add_argument("--metrica", required=True)
    args = p.parse_args()

    variante = Path(args.variante).read_text(encoding="utf-8")
    produccion = Path(args.produccion).read_text(encoding="utf-8")
    fm_v, cuerpo_v = partir(variante)
    fm_p, cuerpo_p = partir(produccion)
    agente = (fm_p or {}).get("name", "")

    rechazos = []

    def di(ok, titulo, detalle=""):
        print("{}  {}{}".format("OK      " if ok else "RECHAZA ", titulo,
                                ": " + detalle if detalle else ""))
        if not ok:
            rechazos.append(titulo)

    # 1. citas del conjunto copiadas en el prompt
    casos, errores = leer_conjunto(args.conjunto)
    if errores:
        di(False, "conjunto legible", "; ".join(errores[:3]))
    else:
        plano = normalizar(variante)
        filtradas = set()
        for caso in casos:
            for d in caso.get("defectos") or []:
                cita = str(d.get("cita") or "").strip()
                if len(cita) >= MIN_CARACTERES_CITA and normalizar(cita) in plano:
                    filtradas.add(cita[:60])
        di(not filtradas, "sin citas del conjunto",
           "aparecen {} ({})".format(len(filtradas), " | ".join(sorted(filtradas)[:3]))
           if filtradas else "")

    # 2. nombre de la metrica o del evaluador
    nombra = sorted({m.group(0).lower() for m in PROHIBIDAS.finditer(variante)})
    di(not nombra, "no nombra a quien puntua", ", ".join(nombra[:5]))

    # 3. rol y contrato intactos
    if fm_v is None or fm_p is None:
        di(False, "frontmatter presente", "la variante o la produccion no lo tienen")
    else:
        distintos = [k for k in ("name", "description", "tools", "model", "maxTurns")
                     if fm_v.get(k) != fm_p.get(k)]
        di(not distintos, "frontmatter intacto",
           "cambian: " + ", ".join(distintos) if distintos else "")
        igual = primer_parrafo(cuerpo_v) == primer_parrafo(cuerpo_p)
        di(igual, "rol y pregunta intactos",
           "" if igual else "el primer parrafo del cuerpo, que declara el rol y la "
                            "pregunta del agente, ha cambiado: eso es cambio de "
                            "contrato y lo decide el usuario en la spec")

    # 4. esquema de salida de 5.6
    faltan = [c for c in CLAVES_SALIDA if '"{}"'.format(c) not in variante]
    di(not faltan, "esquema de salida completo",
       "faltan las claves " + ", ".join(faltan) if faltan else "")

    permitidas = CONTRATO.get(agente)
    if permitidas:
        emitidas = {int(g) for g in re.findall(r'"gravedad"\s*:\s*(\d)', variante)}
        intrusas = sorted(emitidas - permitidas)
        di(not intrusas, "gravedades del contrato",
           "emite {} y solo puede emitir {}".format(
               intrusas, sorted(permitidas)) if intrusas else "")

    # 5. tamano
    pal_v, pal_p = len(variante.split()), len(produccion.split())
    tope = int(pal_p * FACTOR_TAMANO)
    di(pal_v <= tope, "tamano dentro del tope",
       "{} palabras sobre un tope de {} ({} x {})".format(
           pal_v, tope, pal_p, FACTOR_TAMANO) if pal_v > tope else
       "{} palabras, tope {}".format(pal_v, tope))

    if rechazos:
        print("\nVariante RECHAZADA sin instalar ({}).".format(", ".join(rechazos)))
        sys.exit(1)
    print("\nVariante apta para instalar.")


if __name__ == "__main__":
    main()
