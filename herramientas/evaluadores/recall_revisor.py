"""recall_revisor - evaluador derivado (spec revision 5.4, fila 7).

Sujeto: el informe de un revisor frente a la verdad de campo.
Pregunta: de los defectos que un juez independiente encuentra, cuantos vio
tambien el revisor? Es el numero que decide si `haiku` puede revisar.

Solo tiene sentido sobre EXPERIMENTOS contra el conjunto etiquetado
`defectos-ascensores-v1` (spec revision 5.3). Sobre trafico en vivo no hay
verdad de campo y devuelve 0 scores.

CONTRATO CON EL DATASET:
  expectedOutput del item = {"defectos": [{"clase": "E", "cita": "la agua",
                             "capitulo": "03", "por_que": "..."}, ...]}
                            Tambien se acepta la lista pelada.
  output de la observacion = el informe del revisor (JSON con `problemas`).

Emparejamiento: un defecto esperado se considera visto si su cita aparece,
normalizada, dentro de algun campo de texto de algun problema del informe.
Es deliberadamente generoso: el falso negativo que interesa medir es "no lo
menciono en absoluto", no "lo redacto distinto".
"""

import json
import re
import unicodedata

CAMPOS_PROBLEMA = ("cita", "cita_literal", "donde", "que", "por_que", "descripcion")
MIN_CARACTERES_CITA = 8


def _a_json(valor):
    if isinstance(valor, (dict, list)):
        return valor
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    valla = re.search(r"```(?:json)?\s*(.*?)```", texto, re.S)
    if valla:
        texto = valla.group(1).strip()
    for abre, cierra in (("{", "}"), ("[", "]")):
        ini, fin = texto.find(abre), texto.rfind(cierra)
        if ini != -1 and fin > ini:
            try:
                return json.loads(texto[ini:fin + 1])
            except ValueError:
                continue
    return None


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    for comilla in ("\u00ab", "\u00bb", "\u201c", "\u201d", "\u2018", "\u2019"):
        texto = texto.replace(comilla, " ")
    texto = re.sub(r"\s+", " ", texto)
    return texto.casefold().strip()


def _esperados(ctx):
    if ctx.experiment is None:
        return []
    dato = _a_json(ctx.experiment.item_expected_output)
    if isinstance(dato, dict):
        dato = dato.get("defectos") or dato.get("problemas") or []
    if not isinstance(dato, list):
        return []
    return [d for d in dato if isinstance(d, dict)]


def _texto_problemas(informe):
    problemas = informe.get("problemas") if isinstance(informe, dict) else None
    if not isinstance(problemas, list):
        return "", 0
    trozos = []
    for problema in problemas:
        if isinstance(problema, dict):
            trozos += [str(problema[c]) for c in CAMPOS_PROBLEMA if problema.get(c)]
        elif isinstance(problema, str):
            trozos.append(problema)
    return _normalizar(" || ".join(trozos)), len(problemas)


def evaluate(ctx):
    esperados = _esperados(ctx)
    if not esperados:
        return EvaluationResult(scores=[])  # sin verdad de campo no hay recall

    informe = _a_json(ctx.observation.output)
    if informe is None:
        return EvaluationResult(scores=[])

    texto_informe, n_problemas = _texto_problemas(informe)

    vistos, perdidos, por_clase = 0, [], {}
    for defecto in esperados:
        clase = str(defecto.get("clase") or "sin_clase")
        cita = str(defecto.get("cita") or "").strip()
        acierto = bool(cita) and len(cita) >= MIN_CARACTERES_CITA \
            and _normalizar(cita) in texto_informe
        cuenta = por_clase.setdefault(clase, {"esperados": 0, "vistos": 0})
        cuenta["esperados"] += 1
        if acierto:
            vistos += 1
            cuenta["vistos"] += 1
        else:
            perdidos.append("[{}] {}".format(clase, cita[:80]))

    recall = vistos / len(esperados)
    return EvaluationResult(scores=[
        Score(
            name="recall_revisor",
            value=recall,
            data_type="NUMERIC",
            comment="El revisor vio {}/{} defectos etiquetados ({} problemas en su informe). "
                    "No vistos: {}".format(vistos, len(esperados), n_problemas,
                                           " | ".join(perdidos[:8]) or "ninguno"),
            metadata={
                "defectos_esperados": len(esperados),
                "defectos_vistos": vistos,
                "problemas_en_informe": n_problemas,
                "por_clase": por_clase,
                "no_vistos": perdidos[:30],
            },
        )
    ])
