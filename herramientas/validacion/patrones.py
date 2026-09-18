#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clases de error de lengua del validador de manuscrito (spec functional.md 9.6).

Cada entrada es una CLASE de error del castellano, nunca una instancia del
corpus. La diferencia importa: un patron escrito contra la frase concreta
encuentra justo lo que se escribio para encontrar, y el numero deja de medir
nada (mismo lazo que E5c). La regla se comprueba en comprobar_patrones.py:

  1. el patron casa con TODOS sus ejemplos positivos, que estan inventados aqui
     y no aparecen en ningun manuscrito del repositorio;
  2. el patron NO casa con ninguno de sus ejemplos negativos, que son castellano
     correcto y de forma parecida;
  3. el patron no contiene tres palabras seguidas de ninguna cita etiquetada
     (una palabra suelta del lexico si vale: es miembro de la clase, no la instancia).

VERSION Y HASH. El hash de este fichero entra en cada resultado. Cambiarlo
invalida las comparaciones con puntuaciones anteriores: hay que re-puntuar la
linea base (spec 9.6, regla del detector congelado).
"""

import hashlib
import re
from pathlib import Path

VERSION = "v1"

# Sustantivos femeninos que empiezan por /a/ tonica: exigen el/un, no la/una.
_A_TONICA = ("agua|aula|alma|aguila|águila|area|área|hambre|arma|ave|ancla|acta|"
             "alba|ala|aula|hacha|asa|habla|arpa|aura")

# Sustantivos masculinos que un modelo confunde por terminar en -a o por analogia.
_MASCULINOS = ("conocimiento|problema|tema|sistema|programa|idioma|clima|dia|día|"
               "mapa|planeta|momento|cuerpo|trabajo|silencio|ruido|motor|cable|"
               "panel|sonido|metodo|método|esquema|dilema|sintoma|síntoma")

# Verbos que introducen subordinada y cuyo complemento de persona es DATIVO:
# con subordinada detras, un clitico "la/las" solo puede ser laismo.
_DATIVOS = ("dijo|dije|dijeron|dec[ií]a|dec[ií]an|pregunt[oó]|pregunt[eé]|"
            "preguntaron|preguntaba|explic[oó]|expliqu[eé]|explicaba|pidi[oó]|"
            "ped[ií]a|cont[oó]|contaba|contest[oó]|respondi[oó]|prometi[oó]|"
            "advirti[oó]|record[oó]|sugiri[oó]")

# Presente (indicativo o subjuntivo) tras "como si", que exige imperfecto de
# subjuntivo. Las dos formas son incorrectas ahi.
_PRESENTES = ("es|son|est[aá]|est[aá]n|tiene|tienen|contiene|contienen|puede|"
              "pueden|hace|hacen|sabe|saben|va|van|quiere|quieren|sea|sean|"
              "est[eé]|est[eé]n|tenga|tengan|contenga|contengan|pueda|puedan|"
              "haga|hagan|sepa|sepan|vaya|vayan|quiera|quieran")

# Primera persona del singular del presente, detras de clitico, en narracion de
# tercera y pasado: casi siempre una forma verbal mal conjugada.
_PRIMERA_SG = ("peso|miro|dejo|tomo|cambio|paso|llamo|toco|guardo|saco|meto|"
               "abro|cierro|aprieto|suelto|empujo|levanto|bajo|subo")


CLASES = [
    {
        "clase": "articulo-femenino-ante-a-tonica",
        "descripcion": "Articulo femenino ante sustantivo que empieza por /a/ tonica; exige el/un.",
        "patron": r"\b(?:la|una)\s+(?:" + _A_TONICA + r")\b",
        "positivos": ["Nadie tocaba la arpa del salon", "Bebio una agua turbia"],
        "negativos": ["El agua estaba fria", "Aquella agua no servia",
                      "la aguja del reloj", "Esta agua sabe mal"],
    },
    {
        "clase": "concordancia-articulo-sustantivo",
        "descripcion": "Articulo femenino con sustantivo masculino.",
        "patron": r"\b(?:La|Una|la|una)\s+(?:" + _MASCULINOS + r")\b",
        "positivos": ["La problema de fondo seguia ahi", "una sistema mal montada"],
        "negativos": ["El conocimiento no se pierde", "la parte de atras",
                      "una vez al mes", "la mano derecha"],
    },
    {
        "clase": "laismo",
        "descripcion": "Clitico 'la/las' con verbo de complemento indirecto seguido de subordinada.",
        "patron": r"\b(?:La|la|Las|las)\s+(?:" + _DATIVOS + r")\s+(?:que|si|qu[eé]|c[oó]mo|cu[aá]ndo|d[oó]nde|por qu[eé])\b",
        "positivos": ["La dijo que no volviera", "Las pregunto si tenian frio"],
        "negativos": ["Le dijo que no volviera", "La respuesta que buscaba",
                      "Esa la contesto rapido", "La pregunta que hizo"],
    },
    {
        "clase": "preposicion-ausente-traves",
        "descripcion": "'traves' sin la preposicion 'a' delante.",
        "patron": r"(?<!\ba\s)\btrav[eé]s\b",
        "positivos": ["Lo supo traves de un vecino", "miraba través del cristal"],
        "negativos": ["a traves de la ventana", "a través del cable"],
    },
    {
        "clase": "subjuntivo-tras-como-si",
        "descripcion": "'como si' exige imperfecto de subjuntivo, no presente. Lista cerrada de verbos frecuentes: no cubre el resto.",
        "patron": r"\bcomo si\s+(?:\w+\s+){0,2}?(?:" + _PRESENTES + r")\b",
        "positivos": ["Hablaba como si sabe la respuesta",
                      "Andaba como si el suelo esta hueco"],
        "negativos": ["como si supiera la respuesta", "como si el suelo temblara",
                      "como si hubiera estado alli"],
    },
    {
        "clase": "forma-verbal-primera-persona",
        "descripcion": "Clitico seguido de 1a persona del presente en narracion de 3a en pasado.",
        "patron": r"(?<!\bse\s)(?<!\bSe\s)\b(?:L[oa]s?|l[oa]s?)\s+(?:" + _PRIMERA_SG + r")\b(?!\s+(?:de|del|que))",
        "positivos": ["La dejo sobre el banco y salio", "Lo guardo en el bolsillo y se fue"],
        "negativos": ["el peso de la caja", "los paso de baile", "las miro de reojo el gato",
                      "No se la subo a usted"],
    },
    {
        "clase": "concordancia-sujeto-verbo",
        "descripcion": "Sujeto plural con verbo en singular, adyacentes.",
        "patron": r"(?<!\bde\s)(?<!\ben\s)(?<!\bcon\s)(?<!\bpor\s)(?<!\bbajo\s)(?<!\bsobre\s)(?<!\bentre\s)(?<!\bhasta\s)(?<!\bdesde\s)(?<!\bpara\s)\b(?:sus|los|las|mis|tus|unos|unas)\s+\w+s\s+(?:conoc[ií]a|sab[ií]a|ten[ií]a|hacía|dec[ií]a|pod[ií]a|quer[ií]a|deb[ií]a|iba|era|estaba)\b",
        "positivos": ["sus vecinos sabia lo que pasaba", "los tornillos estaba flojos"],
        "negativos": ["sus vecinos sabian lo que pasaba", "los hombres que conocia",
                      "las escaleras hacia la azotea", "el ruido bajo sus zapatos era",
                      "los dedos de la mano"],
    },
]


def compilados():
    return [(c["clase"], re.compile(c["patron"], re.IGNORECASE)) for c in CLASES]


def hash_patrones():
    """Hash del fichero entero: si cambia una coma, cambia la version efectiva."""
    return hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest()[:7]


if __name__ == "__main__":
    print("detector {} hash {}".format(VERSION, hash_patrones()))
    for c in CLASES:
        print("  {:38} {}".format(c["clase"], c["descripcion"]))
