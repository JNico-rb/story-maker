"""cita_verificable - evaluador determinista (spec revision 5.4, fila 1).

Sujeto: los informes de revisor-encargo y revisor-continuidad.
Pregunta: de los `problemas` que el revisor afirma, cuantos se pueden verificar
literalmente en el texto que juzgo? Mide alucinacion del revisor, no calidad de
la novela.

CONTRATO CON EL EXPORTADOR (herramientas/trazas/exportar.py):
  observation.input  = el texto del capitulo juzgado (str, o dict con la clave
                       `capitulo` / `texto` / `intento`).
  observation.output = el informe del revisor (JSON, o el str que lo contiene).
Mientras input/output sigan a null, devuelve 0 scores: no puntua nada en falso.

Campo de cita: se prefiere `cita` (propuesto en revision 1.3). Mientras no
exista, cae a `donde` y `que`, que son prosa y fallaran mas: eso es justamente
la senal de que hace falta el campo `cita`.
"""

import json
import re
import unicodedata

CLAVES_TEXTO = ("capitulo", "texto", "contenido", "intento", "manuscrito", "capitulo_texto")
CAMPOS_CITA = ("cita", "cita_literal", "donde", "que")
MIN_CARACTERES_CITA = 12


def _a_texto(valor):
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        for clave in CLAVES_TEXTO:
            if isinstance(valor.get(clave), str):
                return valor[clave]
        return json.dumps(valor, ensure_ascii=False)
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


def _normalizar(texto):
    """Comparacion tolerante: sin tildes, sin comillas tipograficas, sin
    espacios repetidos, sin mayusculas. Una cita real sobrevive; una inventada
    no se salva por un acento."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for comilla in ("\u00ab", "\u00bb", "\u201c", "\u201d", "\u201e", "\u2033"):
        texto = texto.replace(comilla, '"')
    for apostrofo in ("\u2018", "\u2019", "\u2032"):
        texto = texto.replace(apostrofo, "'")
    texto = texto.replace("\u2014", "-").replace("\u2013", "-").replace("\u2026", "...")
    texto = re.sub(r"\s+", " ", texto)
    return texto.casefold().strip()


def _citas(problema):
    if not isinstance(problema, dict):
        return []
    encontradas = []
    for campo in CAMPOS_CITA:
        valor = problema.get(campo)
        if isinstance(valor, str) and len(valor.strip()) >= MIN_CARACTERES_CITA:
            encontradas.append((campo, valor.strip().strip('"\u00ab\u00bb')))
    return encontradas


def evaluate(ctx):
    capitulo = _normalizar(_a_texto(ctx.observation.input))
    informe = _a_json(ctx.observation.output)

    if not capitulo or informe is None:
        return EvaluationResult(scores=[])  # exportador aun sin input/output

    problemas = informe.get("problemas") if isinstance(informe, dict) else None
    if not isinstance(problemas, list) or not problemas:
        return EvaluationResult(scores=[])  # 0 problemas: nada que verificar

    verificados, sin_cita, fallidos = 0, 0, []
    for problema in problemas:
        candidatas = _citas(problema)
        if not candidatas:
            sin_cita += 1
            continue
        campo_ok = next(
            (campo for campo, cita in candidatas if _normalizar(cita) in capitulo), None)
        if campo_ok:
            verificados += 1
        else:
            fallidos.append(candidatas[0][1][:120])

    total = len(problemas)
    fraccion = verificados / total

    detalle = "{}/{} problemas con cita verificable en el capitulo.".format(verificados, total)
    if sin_cita:
        detalle += " {} sin campo de cita utilizable.".format(sin_cita)
    if fallidos:
        detalle += " No aparecen en el texto: " + " | ".join(fallidos[:5])

    return EvaluationResult(scores=[
        Score(
            name="cita_verificable",
            value=fraccion,
            data_type="NUMERIC",
            comment=detalle,
            metadata={
                "problemas_total": total,
                "verificados": verificados,
                "sin_cita": sin_cita,
                "no_verificados": fallidos[:20],
                "agente": (ctx.observation.metadata or {}).get("agente")
                if isinstance(ctx.observation.metadata, dict) else None,
            },
        )
    ])
