#!/bin/sh
# Hook PreToolUse de Edit y Write. Lo registra .claude/settings.json.
#
# Impone la regla de specs/functional.md §3.1: una aprobación no se toca. Todos estos
# ficheros se escriben ENTEROS, de una vez, así que `Edit` sobre cualquiera de ellos
# está mal por definición, exista o no. Lo que cambia entre ellos es el `Write`:
#
#   - POR APROBACIÓN — biblia.md, escaleta.md, arco-AA.md. Se reescriben a propósito
#     mientras son una propuesta: el bucle de proponer_escaleta los rehace en cada
#     vuelta, y aprobarlos consiste justamente en reescribirlos con la marca puesta.
#     Así que la condición no es que el fichero exista, es que el que ya está en disco
#     traiga `aprobada: true` (biblia, escaleta) o `validada: true` (arco) en su
#     frontmatter. Lo que se protege es la aprobación, no el fichero.
#   - POR EXISTENCIA — intento-K.md, libro-estado-K.md, informe-arco-AA.md,
#     manuscrito.md. Se escriben una sola vez en la vida: el primer Write es el harness
#     creando el artefacto y debe pasar; el segundo es el error que hay que parar.
#   - EXCEPCIÓN — libro-estado.md, el de la raíz de la novela (CLAUDE.md regla 2): el
#     harness lo sustituye entero al cerrar cada capítulo. Su Write siempre pasa. Su
#     versión por intento, libro-estado-K.md, sí se escribe una sola vez.
#
# Fuera a propósito: todo lo que no esté dentro de novelas/. Las plantillas de la skill
# se llaman igual que los artefactos que generan y sí se editan: son el código fuente
# del harness, no su salida.
#
# Falla en abierto: si no logra leer de su entrada la herramienta o la ruta, o no logra
# leer el frontmatter del fichero existente, deja pasar. Un hook que bloquea porque no
# entiende su propia entrada pararía el bucle sin motivo. La garantía cubre Edit y
# Write, NO Bash: el criterio 6 de §8.2 sigue demostrándola a posteriori con git.

entrada=$(cat)

# La entrada es JSON compacto en una línea. Se coge la PRIMERA aparición de la clave:
# un Edit puede llevar la cadena "file_path" dentro del texto que va a escribir.
extraer() {
  printf '%s' "$entrada" |
    grep -o "\"$1\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" |
    head -1 |
    sed 's/.*"\([^"]*\)"$/\1/'
}

herramienta=$(extraer tool_name)
ruta=$(extraer file_path)
[ -n "$ruta" ] || exit 0

# En Windows la ruta llega con las barras invertidas escapadas (C:\Users\...).
ruta=$(printf '%s' "$ruta" | sed 's|\\|/|g')

case "$ruta" in
  */novelas/*) ;;
  *) exit 0 ;;
esac

# regla: pasa | aprobacion | existencia. marca: clave del frontmatter que bloquea.
marca=
nombre=${ruta##*/}
case "$nombre" in
  libro-estado.md)                        regla=pasa ;;
  biblia.md|escaleta.md)                  regla=aprobacion; marca=aprobada ;;
  arco-[0-9]*.md)                         regla=aprobacion; marca=validada ;;
  informe-arco-[0-9]*.md|manuscrito.md)   regla=existencia ;;
  intento-[0-9]*.md|libro-estado-[0-9]*.md) regla=existencia ;;
  *) exit 0 ;;
esac

bloquea_write() {
  echo "story-maker: «$nombre» $1 (CLAUDE.md regla 2, specs/functional.md §3.1). El harness lo escribe una sola vez; sobrescribirlo perdería lo aprobado. Si de verdad hay que rehacerlo, es una decisión del usuario: que lo borre él primero." >&2
  exit 2
}

case "$herramienta" in

  Write)
    [ "$regla" = pasa ] && exit 0
    [ -e "$ruta" ] || exit 0

    if [ "$regla" = existencia ]; then
      bloquea_write "ya existe y se escribe una sola vez"
    fi

    # Frontmatter del fichero que YA está en disco: el bloque entre el `---` de la
    # primera línea y el `---` siguiente. Si no lo hay, o el fichero no se deja leer,
    # sale vacío y se deja pasar (falla en abierto).
    frontmatter=$(awk '
      NR == 1 && $0 !~ /^---[[:space:]]*$/ { exit }
      NR == 1 { next }
      /^---[[:space:]]*$/ { exit }
      { print }
    ' "$ruta" 2>/dev/null)

    if printf '%s\n' "$frontmatter" |
       grep -Eq "^[[:space:]]*$marca[[:space:]]*:[[:space:]]*true[[:space:]]*$"; then
      bloquea_write "ya está aprobado (\`$marca: true\`)"
    fi
    exit 0
    ;;

  Edit)
    echo "story-maker: «$nombre» no se edita en sitio (CLAUDE.md regla 2, specs/functional.md §3.1). El harness sustituye estos ficheros con una escritura completa, nunca con Edit." >&2
    exit 2
    ;;

  *)
    exit 0
    ;;

esac
