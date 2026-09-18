#!/usr/bin/env python3
"""Crea en Langfuse los evaluadores y las reglas de la revision 2026-09-17 (5.4).

Fuera del harness: no lo llama /novela nunca (spec 9.3 regla 2). Solo escribe
en Langfuse; no toca novelas/.

    python herramientas/evaluadores/crear.py --dry-run
    python herramientas/evaluadores/crear.py

Variables de entorno: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.

Las reglas se crean DESACTIVADAS a proposito: hoy el exportador manda
input/output a null (revision 5.2) y activarlas puntuaria el vacio. Se activan
cuando el exportador este arreglado.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent

# El modelo del juez NUNCA es el que escribio (revision 5.4). El escritor es
# haiku; esto debe apuntar a opus o sonnet. Se resuelve contra
# GET /api/public/llm-connections.
MODELO_JUEZ = {"provider": "openrouter", "model": "openrouter/free"}

# --- filtros ---------------------------------------------------------------
# El API de reglas no permite filtrar por nombre de observacion; si por
# metadata, que el exportador ya escribe (agente, modo, resultado).


def _f(clave, operador, valor):
    return {"type": "stringObject", "column": "metadata",
            "key": clave, "operator": operador, "value": valor}


SOLO_GENERACIONES = [
    {"type": "stringOptions", "column": "type", "operator": "any of", "value": ["GENERATION"]},
    {"type": "arrayOptions", "column": "tags", "operator": "all of", "value": ["story-maker"]},
]
# `resultado = ok` descarta las filas `pendiente` y las de correccion, que son
# la inflacion del 22 % del analisis de traza.
SOLO_OK = [_f("resultado", "=", "ok")]

FILTRO_ESCRITOR = SOLO_GENERACIONES + SOLO_OK + [
    _f("agente", "=", "escritor"),
    _f("modo", "starts with", "capitulo"),
]
FILTRO_REVISORES = SOLO_GENERACIONES + SOLO_OK + [
    _f("agente", "contains", "revisor"),
]
FILTRO_RESUMIDOR = SOLO_GENERACIONES + SOLO_OK + [
    _f("agente", "=", "resumidor"),
    _f("modo", "starts with", "capitulo"),
]

# --- jueces ----------------------------------------------------------------

COMUN = (
    "Eres un juez independiente de un sistema que genera novelas en castellano. "
    "No escribes ni reescribes: solo cuentas y citas.\n"
    "Reglas que no se negocian:\n"
    "- Toda afirmacion tuya lleva una CITA LITERAL del texto, copiada caracter a "
    "caracter. Si no puedes citar, no lo cuentas.\n"
    "- No juzgas gusto, estilo ni lo que te habria gustado leer.\n"
    "- Si dudas, no cuentas. Un falso positivo envenena la calibracion.\n"
)

JUECES = [
    {
        "name": "lengua_erratas",
        "description": (
            "Agramaticalidades por cada 1.000 palabras, con cita obligatoria. "
            "Clase E de la revision 2026-09-17 (13 de los 30 defectos). "
            "Corre sobre el texto del capitulo (escritor / capitulo)."
        ),
        "prompt": COMUN + (
            "\nTu unica tarea: contar errores de LENGUA en el capitulo.\n"
            "Cuenta como error: concordancia de genero o numero (por ejemplo "
            "\"la agua\", \"La conocimiento\"), laismo y leismo, tiempo o modo "
            "verbal imposible en el contexto (\"habia fallido\" donde el relato "
            "exige \"habia fallado\"), palabra inexistente en castellano, frase sin "
            "sentido sintactico, preposicion o regimen verbal incorrecto.\n"
            "NO cuenta: eleccion de vocabulario, repeticiones, ritmo, longitud de "
            "frase, comas opinables, licencias en dialogo marcadas como habla de "
            "un personaje.\n\n"
            "Capitulo:\n<capitulo>\n{{capitulo}}\n</capitulo>\n\n"
            "Cuenta las palabras del capitulo, cuenta los errores, y devuelve la "
            "tasa por cada 1.000 palabras. En el razonamiento lista cada error con "
            "su cita literal y la correccion, uno por linea."
        ),
        "outputDefinition": {
            "dataType": "NUMERIC", "minValue": 0, "maxValue": 50,
            "scoreValueInstructions": (
                "Numero de errores de lengua por cada 1.000 palabras del capitulo, "
                "con dos decimales. 0 si no hay ninguno. Se calcula "
                "errores * 1000 / palabras_del_capitulo."),
            "scoreReasoningInstructions": (
                "Lista cada error en una linea con este formato: "
                "cita literal -> correccion -> tipo de error. Termina con el "
                "recuento total de errores y el total de palabras del capitulo."),
        },
        "variableMapping": [{"variable": "capitulo", "source": "output"}],
        "filtro": FILTRO_ESCRITOR,
    },
    {
        "name": "verosimilitud_dominio",
        "description": (
            "Afirmaciones tecnicas o factuales que un competente en el dominio "
            "rechazaria. Clase B de la revision 2026-09-17 (4 defectos: el "
            "multimetro que mide integridad estructural, el cable como pieza unica)."
        ),
        "prompt": COMUN + (
            "\nTu unica tarea: encontrar afirmaciones TECNICAS o FACTUALES que un "
            "profesional del dominio rechazaria por falsas, no por poco elegantes.\n"
            "Ejemplo del tipo de fallo que buscas: un instrumento al que se le "
            "atribuye una medida que no puede hacer; una pieza descrita como algo "
            "que no es; un procedimiento que en la realidad no funciona asi.\n"
            "NO cuenta: licencia narrativa declarada como tal, tecnologia del "
            "mundo de ficcion, imprecision que un lego no notaria y un experto "
            "aceptaria como simplificacion razonable.\n\n"
            "Capitulo:\n<capitulo>\n{{capitulo}}\n</capitulo>\n\n"
            "Por cada afirmacion, cita literal + que profesion la rechazaria + por que."
        ),
        "outputDefinition": {
            "dataType": "NUMERIC", "minValue": 0, "maxValue": 20,
            "scoreValueInstructions": (
                "Numero entero de afirmaciones tecnicas o factuales falsas que has "
                "podido citar literalmente. 0 si no hay ninguna."),
            "scoreReasoningInstructions": (
                "Una linea por afirmacion: cita literal -> quien la rechazaria -> "
                "por que es falsa. Si no hay ninguna, escribe exactamente "
                "sin hallazgos."),
        },
        "variableMapping": [{"variable": "capitulo", "source": "output"}],
        "filtro": FILTRO_ESCRITOR,
    },
    {
        "name": "coherencia_interna",
        "description": (
            "Contradicciones del capitulo consigo mismo o con el contexto previo, "
            "con cita. Clase A de la revision 2026-09-17 (7 defectos). Es la unica "
            "clase que el revisor de continuidad ya tenia encargada y no vio."
        ),
        "prompt": COMUN + (
            "\nTu unica tarea: encontrar CONTRADICCIONES.\n"
            "Cuentan tres tipos:\n"
            "1. El capitulo se contradice a si mismo (un personaje esta en el "
            "vestibulo y a la vez fuera del edificio; una edad que no cuadra).\n"
            "2. El capitulo contradice el contexto previo que te doy (un plazo "
            "distinto, un personaje que actua antes de existir, un objeto que "
            "nunca se creo).\n"
            "3. El capitulo da por hecho algo que el contexto dice que no ocurrio.\n"
            "Para cada una necesitas DOS citas: la del capitulo y la del contexto "
            "(o la otra frase del capitulo) con la que choca. Sin las dos, no cuenta.\n"
            "NO cuenta: elipsis, informacion que simplemente falta, o que el "
            "capitulo no repita algo ya sabido.\n\n"
            "Contexto previo (libro de estado y resumenes anteriores):\n"
            "<contexto>\n{{contexto}}\n</contexto>\n\n"
            "Capitulo:\n<capitulo>\n{{capitulo}}\n</capitulo>"
        ),
        "outputDefinition": {
            "dataType": "NUMERIC", "minValue": 0, "maxValue": 20,
            "scoreValueInstructions": (
                "Numero entero de contradicciones para las que tienes las dos citas "
                "literales. 0 si no hay ninguna."),
            "scoreReasoningInstructions": (
                "Una contradiccion por bloque: cita del capitulo, cita contraria, y "
                "una frase diciendo por que son incompatibles. Si no hay ninguna, "
                "escribe exactamente sin hallazgos."),
        },
        "variableMapping": [
            {"variable": "capitulo", "source": "output"},
            {"variable": "contexto", "source": "input"},
        ],
        "filtro": FILTRO_ESCRITOR,
    },
    {
        "name": "mundo_presente",
        "description": (
            "Se nota el mundo post-IA fuera de los parrafos expositivos? "
            "Clase C2 de la revision 2026-09-17: una ciudad gestionada por IA cuyo "
            "conflicto depende de una gestora que tarda meses en contestar correos."
        ),
        "prompt": COMUN + (
            "\nTu unica tarea: decidir si el mundo de la novela se NOTA en la "
            "accion del capitulo, no solo en los parrafos que lo explican.\n"
            "Procedimiento, en este orden:\n"
            "1. Tacha mentalmente todo parrafo cuya funcion sea explicar el mundo.\n"
            "2. En lo que queda (escenas, dialogo, gestos, objetos, obstaculos), "
            "busca si el mundo condiciona lo que los personajes hacen y pueden hacer.\n"
            "3. Pregunta de control: si esta escena ocurriera hoy, sin ese mundo, "
            "habria que cambiar algo? Si la respuesta es no, el mundo no esta "
            "presente.\n"
            "Cita siempre: o el pasaje donde el mundo condiciona la accion, o el "
            "pasaje que podria estar escrito en cualquier epoca.\n\n"
            "El mundo, segun la biblia:\n<mundo>\n{{mundo}}\n</mundo>\n\n"
            "Capitulo:\n<capitulo>\n{{capitulo}}\n</capitulo>"
        ),
        "outputDefinition": {
            "dataType": "NUMERIC", "minValue": 0, "maxValue": 1,
            "scoreValueInstructions": (
                "0 = fuera de los parrafos expositivos la escena podria transcurrir "
                "hoy sin cambiar nada. 0,5 = el mundo asoma en detalles sueltos pero "
                "no condiciona lo que ocurre. 1 = el mundo determina lo que los "
                "personajes pueden y no pueden hacer en la escena. Valores "
                "intermedios permitidos, un decimal."),
            "scoreReasoningInstructions": (
                "Primero la cita donde el mundo condiciona la accion (o la palabra "
                "ninguna). Despues la cita del pasaje mas intercambiable con el "
                "presente. Termina con la respuesta a la pregunta de control en una "
                "frase."),
        },
        "variableMapping": [
            {"variable": "capitulo", "source": "output"},
            {"variable": "mundo", "source": "input"},
        ],
        "filtro": FILTRO_ESCRITOR,
    },
]

CODIGO = [
    {
        "name": "cita_verificable",
        "fichero": "cita_verificable.py",
        "description": (
            "Fraccion de los problemas de un informe cuya cita aparece "
            "literalmente en el capitulo. Mide la alucinacion del revisor, no la "
            "calidad de la novela. Revision 2026-09-17, 1.3 y 5.4 fila 1."),
        "filtro": FILTRO_REVISORES,
    },
    {
        "name": "redundancia_resumen",
        "fichero": "redundancia_resumen.py",
        "description": (
            "Solapamiento de sucesos entre los resumenes de dos capitulos "
            "consecutivos. Caza el defecto D1 sin modelo. Revision 5.4 fila 2."),
        "filtro": FILTRO_RESUMIDOR,
    },
    {
        "name": "recall_revisor",
        "fichero": "recall_revisor.py",
        "description": (
            "Defectos que el conjunto etiquetado tiene y el informe del revisor "
            "tambien, sobre los que el conjunto tiene. Es el numero que decide si "
            "haiku puede revisar. Solo sobre experimentos contra "
            "defectos-ascensores-v1. Revision 5.4 fila 7."),
        "filtro": None,  # sin regla: es de experimento, no de trafico en vivo
    },
]

ETIQUETAS_REGLA = [
    (FILTRO_ESCRITOR, "escritor / capitulo - jueces de texto"),
    (FILTRO_REVISORES, "revisores - cita verificable"),
    (FILTRO_RESUMIDOR, "resumidor - redundancia entre capitulos"),
]


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
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        raise SystemExit("{} {} -> {} {}".format(metodo, ruta, err.code, err.read().decode()))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="imprime los cuerpos y no envia")
    args = p.parse_args()

    if not args.dry_run and not (os.environ.get("LANGFUSE_PUBLIC_KEY")
                                 and os.environ.get("LANGFUSE_SECRET_KEY")):
        raise SystemExit("Faltan LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY.")

    cuerpos = []
    for juez in JUECES:
        cuerpos.append((juez["filtro"], {
            "type": "llm_as_judge",
            "name": juez["name"],
            "description": juez["description"],
            "prompt": juez["prompt"],
            "outputDefinition": juez["outputDefinition"],
            "variableMapping": juez["variableMapping"],
            "modelConfig": MODELO_JUEZ,
        }))
    for ev in CODIGO:
        cuerpos.append((ev["filtro"], {
            "type": "code",
            "name": ev["name"],
            "description": ev["description"],
            "sourceCodeLanguage": "PYTHON",
            "sourceCode": (AQUI / ev["fichero"]).read_text(encoding="utf-8"),
        }))

    if args.dry_run:
        for filtro, cuerpo in cuerpos:
            print("POST /api/public/v2/evaluators", cuerpo["name"],
                  "| regla:", "no" if filtro is None else "si")
        return 0

    creados = []
    for filtro, cuerpo in cuerpos:
        r = peticion("POST", "/api/public/v2/evaluators", cuerpo)
        creados.append((cuerpo["name"], r["id"], filtro))
        print("evaluador {:<24} -> {}".format(cuerpo["name"], r["id"]))

    # Una regla por filtro: los cuatro jueces del escritor comparten regla.
    for filtro, etiqueta in ETIQUETAS_REGLA:
        asignados = [(n, i) for n, i, f in creados if f == filtro]
        if not asignados:
            continue
        r = peticion("POST", "/api/public/v2/evaluation-rules", {
            "name": etiqueta,
            "enabled": False,  # el exportador aun manda input/output a null
            "filter": filtro,
            "evaluatorAssignments": [
                {"evaluatorId": i, "variableMapping": None} for _, i in asignados],
        })
        print("regla     {:<40} -> {} ({})".format(
            etiqueta, r["id"], ", ".join(n for n, _ in asignados)))

    for nombre, _, filtro in creados:
        if filtro is None:
            print("nota      {} queda sin regla: es de experimento".format(nombre))

    return 0


if __name__ == "__main__":
    sys.exit(main())
