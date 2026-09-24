"""Un capítulo limpio: los cuatro linters pasan a la vez (018-C16)."""

from __future__ import annotations

from story_maker.lint.ai_style import lint_ai_style
from story_maker.lint.consistency import StyleSheetInput, lint_consistency
from story_maker.lint.readability import ReadabilityTarget, lint_readability
from story_maker.lint.repetition import lint_repetition

_STYLE_SHEET = StyleSheetInput(narrator="third_person", default_treatment="tu")
_TARGET = ReadabilityTarget(age_band="adult", max_sentence_length=30, min_fernandez_huerta=-100)

# Capítulo de fixture (1.000-1.500 palabras): tercera persona, sin diálogo, vocabulario
# variado dentro de cada párrafo, sin muletillas ni clichés y con pocos adverbios en -mente.
_CLEAN_CHAPTER = """\
Elena bajó por el sendero de piedra que llevaba hasta el faro abandonado. \
El viento traía olor a sal y algas, y las gaviotas volaban en círculos sobre \
las rocas cercanas. Llevaba una linterna vieja y un cuaderno de tapas gastadas \
donde apuntaba cada detalle del lugar. La tarde se apagaba despacio sobre el \
horizonte, y las nubes tomaban un color anaranjado que ella no había visto antes.

El faro se alzaba solitario junto al acantilado. Su pintura blanca se había \
descascarillado con los años, dejando manchas grises en la torre. Una puerta \
de madera cerraba la entrada, pero la cerradura estaba rota desde hacía tiempo. \
La joven empujó la puerta con cuidado y esta cedió con un crujido largo. Dentro, \
el aire olía a humedad y a hierro oxidado.

Subió la escalera de caracol contando los peldaños en voz baja. Eran ciento \
veinte, todos desgastados por el paso de los guardianes que vivieron allí \
antes que nadie los recordara. Las paredes curvas guardaban carteles marinos, \
mapas antiguos y una lámpara de aceite colgada de un gancho oxidado. El sonido \
de sus pasos resonaba en el hueco de piedra como un tambor lejano.

Al llegar arriba encontró la sala de la lente, un espacio circular rodeado de \
cristales gruesos. La lente central seguía intacta, aunque cubierta de polvo. \
Elena limpió un tramo del cristal con la manga y miró hacia el mar abierto. \
Las olas rompían contra las rocas con un ritmo constante, y a lo lejos se veía \
un barco pesquero regresando al puerto.

Sacó el cuaderno y comenzó a dibujar el contorno del faro visto desde dentro. \
Anotó la altura de la sala, el grosor de los cristales y el estado de la \
maquinaria oxidada que antes hacía girar la lente. Cada trazo del lápiz sonaba \
suave contra el papel áspero. El viento golpeaba los cristales con fuerza \
creciente, y la joven sintió un escalofrío frío que la hizo cerrar mejor el \
abrigo.

Bajó de nuevo por la escalera cuando el cielo ya estaba casi oscuro. Guardó el \
cuaderno en la mochila y encendió la linterna vieja, que apenas alumbraba el \
camino de piedra. Los grillos empezaban a cantar entre la hierba alta que \
crecía junto al acantilado. Caminó despacio, atenta a cada raíz y cada piedra \
suelta que pudiera hacerla tropezar.

Al salir, cerró la puerta de madera tras de sí, aunque sabía que la cerradura \
rota no serviría de nada contra el viento ni contra el tiempo. Miró una última \
vez la torre, ahora una sombra oscura recortada contra un cielo violeta. \
Pensó en los guardianes que habían subido esa escalera miles de veces, noche \
tras noche, para mantener la luz encendida.

El camino de regreso al pueblo bordeaba el acantilado durante un buen trecho. \
Las luces de las primeras casas empezaban a encenderse en la distancia, \
pequeños puntos amarillos contra el azul profundo del atardecer. Elena \
apretó el paso, consciente de que la marea subía rápido en esa parte de la \
costa y no quería quedarse atrapada entre las rocas.

Cuando llegó a la plaza del pueblo, el aire olía a pan recién horneado que \
salía de la panadería de la esquina. Se sentó en un banco de piedra frente a \
la fuente y sacó el cuaderno otra vez para terminar el dibujo que había \
empezado en la torre. Añadió sombras donde antes solo había líneas sueltas, \
y el faro cobró una forma más real sobre el papel.

Un vecino mayor se acercó y le preguntó si había subido hasta la lente. Ella \
asintió y le contó lo que había encontrado: los mapas, la lámpara oxidada, el \
polvo sobre los cristales gruesos. El hombre sonrió y dijo que su padre había \
sido guardián del faro muchos años atrás, cuando la luz todavía giraba cada \
noche sobre las aguas oscuras.

Elena guardó esa historia en el cuaderno, junto a los dibujos y las medidas. \
Pensó que cada piedra del faro guardaba una parte distinta de la memoria del \
pueblo, y que su tarea era anotar tantas partes como pudiera antes de que el \
tiempo las borrara del todo. La noche cayó por completo mientras caminaba de \
regreso a la posada donde se hospedaba.

Ya en su cuarto, releyó las notas del día bajo la luz de una lámpara pequeña. \
Corrigió algunas palabras, añadió una fecha en la esquina de la página y \
cerró el cuaderno con cuidado. Por la ventana entraba el sonido lejano de las \
olas, constante y tranquilo, como si el mar también quisiera contarle algo \
sobre el faro y sus guardianes.

Antes de dormir pensó en volver al día siguiente con más luz, para fotografiar \
la maquinaria oxidada y los carteles marinos que había visto entre las \
sombras. Quería reconstruir en el cuaderno toda la historia del faro, desde \
la primera piedra hasta la última noche en que su luz había girado sobre el \
agua abierta.

A la mañana siguiente se despertó temprano, cuando el pueblo todavía dormía \
bajo una niebla ligera. Desayunó pan tostado y fruta en la cocina de la \
posada, mientras revisaba otra vez sus notas de la tarde anterior. La \
posadera le contó que pocos turistas subían ya hasta el faro, porque el \
camino era largo y el edificio llevaba cerrado casi treinta años.

Elena guardó una cámara pequeña en la mochila, junto con el cuaderno y una \
botella de agua. Salió del pueblo cuando el sol apenas asomaba sobre las \
colinas cercanas. El aire era fresco y olía a hierba mojada, distinto del \
olor salado de la tarde anterior. Los pájaros cantaban entre los arbustos que \
bordeaban el sendero de piedra.

Al llegar de nuevo junto al faro, se detuvo un momento para observar su \
silueta contra el cielo claro. La torre parecía menos oscura bajo la luz de \
la mañana, casi acogedora. Sacó la cámara y fotografió la fachada desde \
varios ángulos, prestando atención a las grietas del muro y a las marcas que \
dejaban las tormentas de invierno sobre la piedra.

Entró de nuevo por la puerta de madera, ahora más fácil de abrir tras el uso \
del día anterior. Subió despacio la escalera de caracol, fotografiando los \
carteles marinos y los mapas colgados en las paredes curvas. La lámpara de \
aceite seguía en su gancho, cubierta de una fina capa de óxido que brillaba \
apenas bajo la luz que entraba por las pequeñas ventanas.

Arriba, en la sala de la lente, pasó buena parte de la mañana anotando la \
disposición de los cristales y el mecanismo que antes hacía girar la luz. \
Comparó sus dibujos del día anterior con lo que veía ahora, corrigiendo \
detalles que se le habían escapado la primera vez. El mar, calmado esa \
mañana, se extendía azul y liso hasta perderse en el horizonte lejano.

Cuando bajó del faro, el sol ya estaba alto y el pueblo empezaba a despertar \
del todo. Cruzó la plaza camino de la posada, saludando al vecino que le \
había hablado el día anterior de su padre guardián. El hombre le preguntó \
por los avances del cuaderno, y ella le mostró las páginas llenas de dibujos, \
medidas y notas sobre la historia de la torre.
"""


def test_un_capitulo_de_fixture_limpio_pasa_los_cuatro_linters() -> None:
    word_count = len(_CLEAN_CHAPTER.split())
    assert 1000 <= word_count <= 1500

    repetition = lint_repetition(_CLEAN_CHAPTER)
    readability = lint_readability(_CLEAN_CHAPTER, _TARGET)
    ai_style = lint_ai_style(_CLEAN_CHAPTER)
    consistency = lint_consistency(_CLEAN_CHAPTER, _STYLE_SHEET)

    assert repetition.passed is True
    assert repetition.metric == 0
    assert repetition.defects == ()

    assert readability.passed is True
    assert readability.metric is not None  # su índice, sin aviso
    assert readability.defects == ()

    assert ai_style.passed is True
    assert ai_style.metric is not None  # su densidad, sin aviso
    assert ai_style.defects == ()

    assert consistency.passed is True
    assert consistency.metric == 0
    assert consistency.defects == ()
