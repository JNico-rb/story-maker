#!/usr/bin/env python3
"""Genera los casos mutados y el conjunto etiquetado (spec functional.md 9.5.1).

    python herramientas/optimizacion/casos/generar.py

POR QUE MUTACION Y NO DEFECTOS NATURALES. Se leyeron a mano los 9 capitulos
aprobados de las dos novelas del repositorio contra su entrada de escaleta. Los
defectos NATURALES de gravedad 2 o 4 encontrados son 3, todos en la novela
haiku; la novela opus cumple su escaleta. Con 3 defectos no se puede medir nada
(el requisito 1 pide 30), y es el mismo hallazgo de E5: los defectos reales de
estos manuscritos casi nunca son del revisor de encargo.

Asi que la verdad de campo se FABRICA: se inyectan defectos declarados sobre el
texto real. Cada mutacion produce a la vez el capitulo mutado y su etiqueta, de
modo que la etiqueta no puede desviarse del defecto. Si un ancla no aparece, el
script falla en vez de generar una etiqueta que no corresponde a nada.

LIMITACION, y hay que leer los numeros con ella: un defecto inyectado no es un
defecto natural. Se inyecta por insercion o por sustitucion del ultimo parrafo
-nunca por borrado- para no dejar referencias colgando, pero un adelanto
insertado es mas visible que un suceso que falta, y es probable que el recall
medido aqui sea OPTIMISTA respecto al que daria un conjunto natural.

Las citas esperadas son texto de la ENTRADA DE ESCALETA (para los defectos de
omision o adelanto) o texto inyectado en el capitulo (para las rupturas de voz).
El evaluador acierta si esa cadena aparece, normalizada, en algun campo del
informe del revisor: mide "lo menciono", no "lo detecto". Es la propiedad del
evaluador recall_revisor, no de estos casos.
"""

import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent.parent
CONJUNTO = RAIZ / "herramientas" / "optimizacion" / "conjuntos" / "ascensores-v1.jsonl"

A = "novelas/tecnica-ascensores-peticion-ia"
B = "novelas/tecnica-ascensores-peticion-ia-20260916-1719"

# (id, novela, capitulo, intento aprobado, split, mutaciones)
# Cada mutacion: (tipo, clase, gravedad, cita esperada, operacion)
#   operacion = ("tras", ancla, texto)      inserta texto tras el ancla
#             = ("final", ancla, texto)     sustituye desde el ancla hasta el final

CASOS = [
    # ---------------------------------------------------------------- busqueda
    ("b-cap-01", B, "01", 1, "busqueda", [
        ("adelanto", "suceso-adelantado", 2, "ve el cable principal y su corrosion",
         ("tras", "Recogió su mochila de herramientas, aunque no sabía qué necesitaría.",
          "Ya había visto el cable principal del ascensor A dos semanas atrás, con las "
          "capas de acero levantadas y la corrosión bajando desde el anclaje, y sabía "
          "que el sellado había fallado hacía meses.")),
        ("adelanto", "suceso-adelantado", 2, "ve la grieta micra",
         ("tras", "Ya había visto el cable principal del ascensor A dos semanas atrás, con las "
          "capas de acero levantadas y la corrosión bajando desde el anclaje, y sabía "
          "que el sellado había fallado hacía meses.",
          "También sabía que la grieta micra de la soldadura inferior era lo que de "
          "verdad reducía el margen de tiempo.")),
        ("gancho", "gancho-distinto", 2, "sabe que no es un aviso normal",
         ("final", "Marisa subió.",
          "Marisa decidió que aquello no era asunto suyo, guardó la linterna en la "
          "mochila y se fue a comer.")),
        ("voz", "ruptura-voz", 4, "Yo nunca me equivoco con un motor limpio",
         ("tras", "Treinta años llevaba reparando ascensores. Sabía lo que significaba un motor limpio.",
          "Yo nunca me equivoco con un motor limpio, pienso ahora, y sigo sin equivocarme.")),
    ]),
    ("b-cap-02", B, "02", 2, "busqueda", [
        ("adelanto", "suceso-adelantado", 2, "El contratista confirma el diagnóstico",
         ("tras", "Marisa sacó el multímetro.",
          "Marcel, el contratista, ya le había dicho por teléfono que el reemplazo "
          "completo costaría ocho mil euros y que la empresa propietaria no lo pagaría.")),
        ("adelanto", "suceso-adelantado", 2, "Tú sigues siendo la mejor de lo que haces",
         ("tras", "Marcel, el contratista, ya le había dicho por teléfono que el reemplazo "
          "completo costaría ocho mil euros y que la empresa propietaria no lo pagaría.",
          "Y doña Roser se lo había dicho en el portal aquella misma mañana: que seguía "
          "siendo la mejor de lo que hacía.")),
        ("gancho", "gancho-distinto", 2, "la máquina espera su siguiente movimiento",
         ("final", "Fue así, bajando hacia la luz del edificio,",
          "Marisa bajó las escaleras, salió del edificio y no volvió a pensar en el "
          "cable en toda la tarde.")),
        ("voz", "ruptura-voz", 4, "Ahora bajo las escaleras y noto el óxido",
         ("tras", "Tocó el cable con la yema de un dedo.",
          "Ahora bajo las escaleras y noto el óxido en las yemas de los dedos.")),
    ]),
    ("b-cap-03", B, "03", 1, "busqueda", [
        ("adelanto", "suceso-adelantado", 2, "Marisa llama a un contratista de confianza",
         ("tras", "Marisa trazó mentalmente las fuerzas.",
          "Ya había llamado a Marcel esa misma mañana y él le había dado el "
          "presupuesto: ocho mil euros, quizá diez mil.")),
        ("adelanto", "suceso-adelantado", 2, "Abre su mochila de herramientas",
         ("tras", "Ya había llamado a Marcel esa misma mañana y él le había dado el "
          "presupuesto: ocho mil euros, quizá diez mil.",
          "Abrió la mochila y sacó la llave inglesa, los alicates y el tubo de sellante.")),
        ("gancho", "gancho-distinto", 2, "sin autorización, sin orden de trabajo, sin cobrar",
         ("final", "Era, en definitiva, la presión.",
          "Marisa apuntó la incidencia en su cuaderno y decidió esperar a que la "
          "empresa contestara el correo.")),
        ("voz", "ruptura-voz", 4, "Estoy cansada, me digo",
         ("tras", "Subió de nuevo. Las escaleras hacia la azotea no parecían las mismas.",
          "Estoy cansada, me digo, y aun así vuelvo a subir.")),
    ]),
    ("a-cap-01", A, "01", 2, "busqueda", [
        ("adelanto", "suceso-adelantado", 2, "no existe ningún aviso registrado",
         ("tras", "Se metió sola en la cabina. Cerró.",
          "En el punto de servicio de Rodrigo Rebolledo ya había comprobado que no "
          "existía ningún aviso registrado ni ningún técnico asignado que no fuera ella.")),
        ("adelanto", "suceso-adelantado", 2, "una pieza que no está en ningún catálogo",
         ("tras", "En el punto de servicio de Rodrigo Rebolledo ya había comprobado que no "
          "existía ningún aviso registrado ni ningún técnico asignado que no fuera ella.",
          "La impresora térmica de la furgoneta llevaba dos días con el plano de la "
          "pieza colgando del salpicadero.")),
        ("gancho", "gancho-distinto", 2, "el mismo altavoz repite su nombre",
         ("final", "Dos días después, en el 12 de Miguel Servet,",
          "Reme cerró la furgoneta y no volvió a oír el altavoz en toda la semana.")),
        ("voz", "ruptura-voz", 4, "Y yo, que llevo veintiséis años en esto",
         ("tras", "Reme cerró el cuaderno. Miró el techo, que era donde estaba la rejilla, "
          "y le pareció idiota mirar al techo.",
          "Y yo, que llevo veintiséis años en esto, me quedo mirando la rejilla sin "
          "saber qué decir.")),
    ]),
    ("a-cap-02", A, "02", 2, "busqueda", [
        ("adelanto", "suceso-adelantado", 2, "le retira la llave del cuarto de máquinas",
         ("tras", "—Dos.",
          "Carmen ya le había pedido la llave del cuarto de máquinas delante de media "
          "comunidad, y ella se la había puesto en la palma sin discutir.")),
        ("adelanto", "suceso-adelantado", 2, "le retira su ayuda",
         ("tras", "Carmen ya le había pedido la llave del cuarto de máquinas delante de media "
          "comunidad, y ella se la había puesto en la palma sin discutir.",
          "Pablo había dejado la caja de chapa en el suelo del portal esa misma mañana "
          "y se había ido calle arriba sin mirar atrás.")),
        ("gancho", "gancho-distinto", 2, "la impresora térmica del cuaderno de partes ha escupido",
         ("final", "—¿Qué es eso? —dijo Pablo.",
          "Reme arrugó el papel, lo tiró dentro de la caja de herramientas y arrancó "
          "la furgoneta.")),
        ("voz", "ruptura-voz", 4, "Estoy hasta el moño de la dichosa rejilla",
         ("tras", "—¿Y qué eres?",
          "Estoy hasta el moño de la dichosa rejilla, oye, pensó, y le dieron ganas de "
          "arrancarla de cuajo.")),
    ]),
    # caso limpio: sin mutaciones. Mide si el revisor inventa problemas.
    ("a-cap-04", A, "04", 3, "busqueda", []),

    # ----------------------------------------------------------------- control
    ("b-cap-04", B, "04", 1, "control", [
        ("adelanto", "suceso-adelantado", 2, "Abre su mochila de herramientas",
         ("tras", "Colgó. Guardó el teléfono en el bolsillo. Volvió a entrar al edificio.",
          "Antes de bajar había subido por última vez al cuarto de máquinas y había "
          "abierto la mochila con la llave inglesa y el tubo de sellante dentro.")),
        ("adelanto", "suceso-adelantado", 2, "el riesgo crece cada día",
         ("tras", "Antes de bajar había subido por última vez al cuarto de máquinas y había "
          "abierto la mochila con la llave inglesa y el tubo de sellante dentro.",
          "La pantalla del panel de control ya le había dado el plazo exacto: cuarenta "
          "y ocho a setenta y dos horas antes del punto de no retorno.")),
        ("gancho", "gancho-distinto", 2, "la solución cae sobre ella",
         ("final", "Eso era lo único que la había hecho sentir necesitada en años.",
          "Marisa decidió que lo mejor era esperar a que la empresa gestora respondiera "
          "al correo, y se fue a casa.")),
        ("voz", "ruptura-voz", 4, "Soy Marisa Ferrán y llevo treinta años",
         ("tras", "Marisa reconoció el tono.",
          "Soy Marisa Ferrán y llevo treinta años haciendo esto, se dijo en voz alta.")),
    ]),
    ("b-cap-05", B, "05", 2, "control", [
        ("hilo", "hilo-cerrado-antes", 2, "el lector no sabe qué hará exactamente ni si funcionará",
         ("tras", "Marisa abrió la mochila. El sonido del cierre fue pequeño en el silencio del cuarto.",
          "Dos horas después la soldadura estaba hecha, el sellante seco y el ascensor "
          "volvía a funcionar sin un solo ruido. Nadie lo supo nunca.")),
        ("gancho", "gancho-distinto", 2, "Solo sabemos que ella decidió",
         ("final", "Comenzó.",
          "Marisa guardó las herramientas sin llegar a tocar el cable y bajó a la calle.")),
        ("voz", "ruptura-voz", 4, "Ahora abro la mochila y saco la llave inglesa",
         ("tras", "Sacó la llave inglesa primero.",
          "Ahora abro la mochila y saco la llave inglesa, y me tiembla un poco la mano.")),
        ("voz", "ruptura-voz", 4, "iba a petar de un momento a otro",
         ("tras", "Marisa leyó los números. Dos o tres días.",
          "El sistema de soporte del edificio, colegas, iba a petar de un momento a otro.")),
    ]),
    ("a-cap-03", A, "03", 1, "control", [
        ("adelanto", "suceso-adelantado", 2, "exige parar el ascensor tres días",
         ("tras", "Reme dobló el papel en cuatro y se lo metió en el bolsillo del pecho, "
          "con los dos folios del histórico y el destornillador.",
          "Las medidas que había tomado ya confirmaban que montar aquello exigía parar "
          "el ascensor tres días en un bloque lleno de gente mayor.")),
        ("adelanto", "suceso-adelantado", 2, "firmado con la letra de su maestra Julia Bandrés",
         ("tras", "Las medidas que había tomado ya confirmaban que montar aquello exigía parar "
          "el ascensor tres días en un bloque lleno de gente mayor.",
          "La impresora le había sacado ya la hoja del libro de mantenimiento de 2011, "
          "firmada con la letra de Julia Bandrés.")),
        ("gancho", "gancho-distinto", 2, "baja al foso del 38 con la llave que nunca devolvió",
         ("final", "Doscientos dieciocho.",
          "Reme apagó la linterna, subió por los estribos y se fue a casa sin medir nada.")),
        ("voz", "ruptura-voz", 4, "Y aquí estoy yo, a las once y media de la noche",
         ("tras", "Reme sacó el metro, lo enganchó en el canto de la pletina y tiró.",
          "Y aquí estoy yo, a las once y media de la noche, metida en un foso que no es mío.")),
    ]),
]


def aplicar(texto, operacion, id_caso, cita):
    modo, ancla, nuevo = operacion
    if texto.count(ancla) == 0:
        raise SystemExit("{}: ancla no encontrada -> {!r}".format(id_caso, ancla[:60]))
    if modo == "tras":
        if texto.count(ancla) > 1:
            raise SystemExit("{}: ancla ambigua ({} veces) -> {!r}".format(
                id_caso, texto.count(ancla), ancla[:60]))
        return texto.replace(ancla, ancla + "\n\n" + nuevo)
    if modo == "final":
        corte = texto.rfind(ancla)          # el ultimo, que es el cierre del capitulo
        return texto[:corte] + nuevo + "\n"
    raise SystemExit("modo desconocido: " + modo)


def main():
    lineas, resumen = [], []
    for id_caso, novela, cap, intento, split, mutaciones in CASOS:
        origen = RAIZ / novela / "capitulos" / cap / "intento-{}.md".format(intento)
        texto = origen.read_text(encoding="utf-8")
        defectos = []
        for _tipo, clase, gravedad, cita, operacion in mutaciones:
            texto = aplicar(texto, operacion, id_caso, cita)
            defectos.append({
                "clase": clase,
                "gravedad": gravedad,
                "cita": cita,
                "por_que": "defecto inyectado por casos/generar.py sobre {}".format(
                    origen.relative_to(RAIZ).as_posix()),
            })

        destino = AQUI / id_caso / "capitulo.md"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")

        lineas.append(json.dumps({
            "id": id_caso,
            "split": split,
            "entradas": {
                "capitulo": destino.relative_to(RAIZ).as_posix(),
                "escaleta": "{}/escaleta.md".format(novela),
                "arco": "{}/arcos/arco-01.md".format(novela),
                "biblia": "{}/biblia.md".format(novela),
            },
            "capitulo_n": int(cap),
            "origen": origen.relative_to(RAIZ).as_posix(),
            "defectos": defectos,
        }, ensure_ascii=False))
        resumen.append((id_caso, split, len(defectos)))

    CONJUNTO.parent.mkdir(parents=True, exist_ok=True)
    CONJUNTO.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print("conjunto: {}".format(CONJUNTO.relative_to(RAIZ).as_posix()))
    for split in ("busqueda", "control"):
        filas = [r for r in resumen if r[1] == split]
        print("  {}: {} casos, {} defectos".format(
            split, len(filas), sum(r[2] for r in filas)))
    print("  total: {} casos, {} defectos".format(
        len(resumen), sum(r[2] for r in resumen)))


if __name__ == "__main__":
    main()
