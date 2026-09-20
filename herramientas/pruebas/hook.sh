#!/usr/bin/env bash
# Fixtures de los dos hooks PreToolUse. Fuera del harness: no lo llama /novela.
#
#   .claude/hooks/inmutables.sh        una aprobacion no se toca (functional.md §3.1)
#   .claude/hooks/rutas-protegidas.sh  credenciales y conjunto etiquetado ilegibles
#                                      desde Bash (technical.md §9.3 regla 6, §9.5)
#
# Son las dos lineas rojas del sistema y hasta hoy no tenian ni una prueba. El curso
# lo llama «mega-hooks sin pruebas»: un hook de cien lineas de sh sin fixtures es un
# riesgo esperando un merge.
#
# Uso:  bash herramientas/pruebas/hook.sh      Salida 1 si algun caso falla.
#
# Convenio de los hooks PreToolUse: salida 0 = deja pasar, 2 = bloquea.
set -u
cd "$(dirname "$0")/../.." || exit 2

INMUTABLES=".claude/hooks/inmutables.sh"
PROTEGIDAS=".claude/hooks/rutas-protegidas.sh"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

fallos=0
total=0

# comprueba <hook> <esperado> <descripcion> <json-por-stdin>
comprueba() {
  hook=$1; esperado=$2; descripcion=$3; entrada=$4
  total=$((total + 1))
  printf '%s' "$entrada" | sh "$hook" >/dev/null 2>&1
  obtenido=$?
  if [ "$obtenido" = "$esperado" ]; then
    echo "  ok    $descripcion (salida $obtenido)"
  else
    echo "  FALLA $descripcion (esperado $esperado, obtenido $obtenido)"
    fallos=1
  fi
}

json_edit()  { printf '{"tool_name":"Edit","tool_input":{"file_path":"%s"}}' "$1"; }
json_write() { printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$1"; }
json_bash()  { printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$1"; }

# ── Escenario en disco para inmutables.sh ────────────────────────────────────
# El hook solo mira rutas que contengan /novelas/, y para la regla «por aprobacion»
# lee el frontmatter del fichero que YA esta en disco.
NOV="$TMP/novelas/prueba"
mkdir -p "$NOV/capitulos/01"

printf -- '---\ntitulo: X\naprobada: true\n---\n\nBiblia aprobada.\n'  > "$NOV/biblia.md"
printf -- '---\ntitulo: X\naprobada: false\n---\n\nPropuesta.\n'        > "$TMP/novelas/propuesta-biblia.md"
printf -- 'texto del intento\n'                                        > "$NOV/capitulos/01/intento-1.md"
printf -- '# libro de estado\n'                                        > "$NOV/libro-estado.md"
printf -- 'fuera del harness\n'                                        > "$TMP/notas.md"

# La propuesta sin marca tiene que llamarse biblia.md para caer en su rama.
mkdir -p "$TMP/novelas/propuesta"
printf -- '---\ntitulo: X\naprobada: false\n---\n\nPropuesta.\n'        > "$TMP/novelas/propuesta/biblia.md"

echo "== inmutables.sh =="
comprueba "$INMUTABLES" 2 "Edit sobre intento-1.md bloquea siempre" \
  "$(json_edit "$NOV/capitulos/01/intento-1.md")"
comprueba "$INMUTABLES" 2 "Edit sobre biblia.md bloquea siempre" \
  "$(json_edit "$NOV/biblia.md")"
comprueba "$INMUTABLES" 2 "Write sobre biblia.md con 'aprobada: true' bloquea" \
  "$(json_write "$NOV/biblia.md")"
comprueba "$INMUTABLES" 0 "Write sobre biblia.md sin la marca pasa (es una propuesta)" \
  "$(json_write "$TMP/novelas/propuesta/biblia.md")"
comprueba "$INMUTABLES" 2 "Write sobre intento-1.md existente bloquea (una sola vez)" \
  "$(json_write "$NOV/capitulos/01/intento-1.md")"
comprueba "$INMUTABLES" 0 "Write sobre intento-2.md inexistente pasa (lo esta creando)" \
  "$(json_write "$NOV/capitulos/01/intento-2.md")"
comprueba "$INMUTABLES" 0 "Write sobre libro-estado.md pasa (se sustituye cada capitulo)" \
  "$(json_write "$NOV/libro-estado.md")"
comprueba "$INMUTABLES" 0 "ruta fuera de novelas/ pasa" \
  "$(json_write "$TMP/notas.md")"
comprueba "$INMUTABLES" 0 "entrada ilegible pasa (falla en abierto, documentado)" \
  'esto no es json'

# ── rutas-protegidas.sh ──────────────────────────────────────────────────────
# Al reves que el anterior: falla en CERRADO.
echo "== rutas-protegidas.sh =="
comprueba "$PROTEGIDAS" 2 "cat de .env bloquea" \
  "$(json_bash 'cat .env')"
comprueba "$PROTEGIDAS" 2 "cat de frontend/.env bloquea" \
  "$(json_bash 'cat frontend/.env')"
comprueba "$PROTEGIDAS" 0 "cat de .env.example pasa (no es un secreto)" \
  "$(json_bash 'cat .env.example')"
comprueba "$PROTEGIDAS" 2 "cat del fichero de credenciales locales bloquea" \
  "$(json_bash 'cat .claude/settings.local.json')"
comprueba "$PROTEGIDAS" 2 "cat del conjunto etiquetado bloquea" \
  "$(json_bash 'cat herramientas/optimizacion/conjuntos/x.jsonl')"
comprueba "$PROTEGIDAS" 2 "head del conjunto etiquetado bloquea" \
  "$(json_bash 'head -3 herramientas/optimizacion/conjuntos/x.jsonl')"
comprueba "$PROTEGIDAS" 2 "redireccion desde .env bloquea" \
  "$(json_bash 'while read l; do echo $l; done < .env')"
comprueba "$PROTEGIDAS" 2 "ruta de Windows con barras invertidas bloquea" \
  '{"tool_name":"Bash","tool_input":{"command":"type C:\\\\repos\\\\story-maker\\\\.env"}}'
comprueba "$PROTEGIDAS" 2 "comilla escapada no abre el bloqueo" \
  '{"tool_name":"Bash","tool_input":{"command":"cat \"uno\" .env"}}'
comprueba "$PROTEGIDAS" 0 "lectura normal de una novela pasa" \
  "$(json_bash 'head -5 novelas/prueba/biblia.md')"
comprueba "$PROTEGIDAS" 0 "git status pasa" \
  "$(json_bash 'git status --porcelain')"
comprueba "$PROTEGIDAS" 2 "entrada vacia bloquea (falla en cerrado)" \
  ''


# ── permisos vs procedimientos ───────────────────────────────────────────────
# No es un hook: es la otra mitad de la contencion. Un procedimiento puede prescribir
# un comando que la lista `allow` de .claude/settings.json no cubre, y entonces el
# harness se para a pedir permiso justo donde no hay nadie mirando (R11 del TODO: el
# `git clean` de invocar.md:129 llevaba el `-e .descartado` que el permiso no tenia).
# Aqui se comprueba el literal exacto que cada procedimiento manda ejecutar.
#
# Motor de prefijos de Claude Code, version corta: "Bash(x *)" cubre todo comando que
# empiece por "x "; sin `*` final, tiene que ser exacto. Si el motor real cambia, esta
# prueba se queda corta pero nunca de mas: solo afirma que existe una entrada que empieza igual.
ALLOW=$(sed -n '/"allow"/,/\]/p' .claude/settings.json | sed -n 's/.*"Bash(\(.*\))".*/\1/p')

# cubre <descripcion> <comando prescrito>
cubre() {
  descripcion=$1; comando=$2
  total=$((total + 1))
  encontrado=0
  while IFS= read -r patron; do
    [ -z "$patron" ] && continue
    case $patron in
      *'*')
        prefijo=${patron%\*}
        case $comando in "$prefijo"*) encontrado=1 ;; esac
        ;;
      *)
        [ "$comando" = "$patron" ] && encontrado=1
        ;;
    esac
    [ "$encontrado" = 1 ] && break
  done <<EOF
$ALLOW
EOF
  if [ "$encontrado" = 1 ]; then
    echo "  ok    $descripcion"
  else
    echo "  FALLA $descripcion -> ningun Bash(...) de allow cubre: $comando"
    fallos=1
  fi
}

echo "== permisos vs procedimientos =="
cubre "invocar.md:104 commitear() anade la carpeta" \
  'git add -A novelas/mi-slug'
cubre "invocar.md:105 commitear() confirma" \
  'git commit -m "novela mi-slug: capitulo 01 aprobado"'
cubre "invocar.md:107 commitear() comprueba que quedo limpio" \
  'git status --porcelain novelas/mi-slug'
cubre "invocar.md:127 descartar() desindexa" \
  'git reset -q HEAD -- novelas/mi-slug'
cubre "invocar.md:128 descartar() revierte" \
  'git checkout -- novelas/mi-slug'
cubre "invocar.md:129 descartar() limpia SIN tocar .descartado" \
  'git clean -fdq -e .descartado novelas/mi-slug'
echo
if [ "$fallos" = 0 ]; then
  echo "OK: $total casos, ninguno falla"
else
  echo "FALLOS: ver arriba ($total casos)"
fi
exit "$fallos"
