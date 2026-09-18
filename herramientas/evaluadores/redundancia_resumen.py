"""redundancia_resumen - evaluador determinista (spec revision 5.4, fila 2).

Sujeto: el resumen del capitulo N frente al del N-1.
Pregunta: cuanto se solapan los sucesos de dos capitulos consecutivos? Es el
defecto D1 (capitulos 2 y 3 son la misma escena) medido sin modelo.

CONTRATO CON EL EXPORTADOR:
  observation.output = resumen del capitulo N (texto o dict con `resumen`).
  observation.input  = dict que incluye `resumen_previo` (el del capitulo N-1).
                       Tambien vale `resumenes_previos` (lista): se toma el
                       ultimo. El capitulo 1 no tiene previo -> 0 scores.

El valor es un Jaccard sobre bigramas de palabras de contenido. 0 = ningun
solapamiento, 1 = el mismo resumen. No hay umbral aqui: el umbral se calibra
con datos, que es lo que hoy no existe.
"""

import json
import re
import unicodedata

CLAVES_RESUMEN = ("resumen", "resumen_capitulo", "texto", "contenido")
CLAVES_PREVIO = ("resumen_previo", "resumen_anterior", "resumen_n_menos_1")
CLAVES_LISTA_PREVIOS = ("resumenes_previos", "resumenes", "resumenes_anteriores")

# Palabras vacias del castellano: no distinguen un suceso de otro.
VACIAS = set("""
a al algo alguna algunas alguno algunos ante antes aquel aquella aquellas aquello aquellos
aqui asi aun aunque cada como con contra cual cuales cuando de del desde donde dos e el ella
ellas ello ellos en entre era eran es esa esas ese eso esos esta estaba estaban estan estar
estas este esto estos fue fueron ha habia han hasta hay la las le les lo los mas me mi mientras
mis mucho muy nada ni no nos nuestra nuestro o os otra otras otro otros para pero poco por
porque que quien quienes se sea segun ser si sin sobre solo son su sus tambien tan tanto te
tiene tienen toda todas todo todos tras tu tus un una unas uno unos y ya
""".split())

MIN_TOKENS = 10


def _a_texto(valor, claves):
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        for clave in claves:
            sub = valor.get(clave)
            if isinstance(sub, str):
                return sub
            if isinstance(sub, dict):
                return _a_texto(sub, claves)
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, list) and valor:
        return _a_texto(valor[-1], claves)
    return str(valor)


def _a_json(valor):
    if isinstance(valor, (dict, list)):
        return valor
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    valla = re.search(r"```(?:json)?\s*(.*?)```", texto, re.S)
    if valla:
        texto = valla.group(1).strip()
    ini, fin = texto.find("{"), texto.rfind("}")
    if ini == -1 or fin <= ini:
        return None
    try:
        return json.loads(texto[ini:fin + 1])
    except ValueError:
        return None


def _tokens(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    palabras = re.findall(r"[a-z0-9]+", texto.casefold())
    return [p for p in palabras if p not in VACIAS and len(p) > 2]


def _bigramas(tokens):
    return set(zip(tokens, tokens[1:]))


def _previo(entrada):
    """Saca el resumen N-1 de la entrada, sea dict, JSON en un str, o nada."""
    dato = _a_json(entrada) if isinstance(entrada, str) else entrada
    if not isinstance(dato, dict):
        return ""
    for clave in CLAVES_PREVIO:
        if clave in dato and dato[clave]:
            return _a_texto(dato[clave], CLAVES_RESUMEN)
    for clave in CLAVES_LISTA_PREVIOS:
        lista = dato.get(clave)
        if isinstance(lista, list) and lista:
            return _a_texto(lista[-1], CLAVES_RESUMEN)
    return ""


def evaluate(ctx):
    actual = _tokens(_a_texto(_a_json(ctx.observation.output) or ctx.observation.output,
                              CLAVES_RESUMEN))
    previo = _tokens(_previo(ctx.observation.input))

    if len(actual) < MIN_TOKENS or len(previo) < MIN_TOKENS:
        return EvaluationResult(scores=[])  # capitulo 1, o exportador sin datos

    bi_actual, bi_previo = _bigramas(actual), _bigramas(previo)
    union = bi_actual | bi_previo
    if not union:
        return EvaluationResult(scores=[])
    comunes = bi_actual & bi_previo
    solapamiento = len(comunes) / len(union)

    muestra = [" ".join(b) for b in sorted(comunes)[:12]]
    return EvaluationResult(scores=[
        Score(
            name="redundancia_resumen",
            value=solapamiento,
            data_type="NUMERIC",
            comment="Solapamiento de bigramas de contenido con el resumen anterior: "
                    "{:.3f} ({} comunes de {}). Comunes: {}".format(
                        solapamiento, len(comunes), len(union), ", ".join(muestra) or "-"),
            metadata={
                "bigramas_comunes": len(comunes),
                "bigramas_union": len(union),
                "tokens_actual": len(actual),
                "tokens_previo": len(previo),
                "muestra_comunes": muestra,
            },
        )
    ])
