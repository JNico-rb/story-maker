#!/bin/sh
# Hook PreToolUse de Edit y Write. Lo registra .claude/settings.json.
#
# Impone la regla de specs/functional.md §3.1: un artefacto aprobado no se toca. Todos
# estos ficheros se escriben ENTEROS, de una vez, así que `Edit` sobre cualquiera de
# ellos está mal por definición, exista o no. Lo que cambia entre ellos es el `Write`:
#
#   - Casi todos se escriben una sola vez en la vida. El segundo Write es el error que
#     hay que parar; el primero es el harness creando el artefacto y debe pasar. Por eso
#     la condición es si el fichero ya existe, no qué herramienta se usa.
#   - libro-estado.md, el de la raíz de la novela, es la excepción de CLAUDE.md regla 2:
#     el harness lo sustituye entero al cerrar cada capítulo. Su Write siempre pasa.
#     Su versión por intento, libro-estado-K.md, sí se escribe una sola vez.
#
# Fuera a propósito: todo lo que no esté dentro de novelas/. Las plantillas de la skill
# se llaman igual que los artefactos que generan y sí se editan: son el código fuente
# del harness, no su salida.
#
# Falla en abierto: si no logra leer la ruta de la entrada, deja pasar. Un hook que
# bloquea porque no entiende su propia entrada pararía el bucle sin motivo.

entrada=$(cat)

# La entrada es JSON compacto en una línea. Se coge la PRIMERA aparición de la clave:
# un Edit puede llevar la cadena "file_path" dentro del texto que va a escribir.
extraer() {
  printf '%s' "$entrada" |
    grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" |
    head -1 |
    sed 's/.*"\([^"]*\)"$/\1/'
}

ruta=$(extraer file_path)
[ -n "$ruta" ] || exit 0

# En Windows la ruta llega con las barras invertidas escapadas (C:\Users\...).
ruta=$(printf '%s' "$ruta" | sed 's|\\|/|g')

case "$ruta" in
  */novelas/*) ;;
  *) exit 0 ;;
esac

nombre=${ruta##*/}
case "$nombre" in
  libro-estado.md) reescribible=si ;;
  biblia.md|escaleta.md|manuscrito.md) reescribible=no ;;
  arco-[0-9]*.md|informe-arco-[0-9]*.md) reescribible=no ;;
  intento-[0-9]*.md|libro-estado-[0-9]*.md) reescribible=no ;;
  *) exit 0 ;;
esac

if [ "$(extraer tool_name)" = "Write" ]; then
  [ "$reescribible" = si ] && exit 0
  [ -e "$ruta" ] || exit 0
  echo "story-maker: «$nombre» ya existe y es un artefacto aprobado (CLAUDE.md regla 2, specs/functional.md §3.1). El harness lo escribe una sola vez; sobrescribirlo perdería lo aprobado. Si de verdad hay que rehacerlo, es una decisión del usuario: que lo borre él primero." >&2
  exit 2
fi

echo "story-maker: «$nombre» no se edita en sitio (CLAUDE.md regla 2, specs/functional.md §3.1). El harness sustituye estos ficheros con una escritura completa, nunca con Edit." >&2
exit 2
