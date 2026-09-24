#!/usr/bin/env bash
# Veredictos de TLC sobre cada tla/*.cfg (spec 006), igual en el portátil y en la CI.
#
# - Config que pasa (sin línea «espera»): TLC termina sin error (C1, C2) y
#   cada acción del modelo se toma al menos una vez (C3).
# - Config de control (con «\* espera: <Propiedad>»): TLC da el contraejemplo
#   de esa propiedad, por su nombre (C6). Sin contraejemplo, con otra propiedad
#   o con otra causa (sintaxis, semántica, memoria), el control falla.
#
# Sin argumentos, todas las configs; con argumentos, solo esas.
# Sale con 0 solo si todas las configs dan su veredicto. JAVA y TLA2TOOLS_JAR
# permiten otro JDK u otro jar (por defecto, `java` y tla/tla2tools.jar).
set -uo pipefail
cd "$(dirname "$0")"

JAVA=${JAVA:-java}
JAR=${TLA2TOOLS_JAR:-tla2tools.jar}

acciones() {
  case "$1" in
    Harness) echo "Configurar Planificar Regenerar EscribirCapitulo Validar Reintentar Gate Publicar Fallar Caer Reanudar PedirCambio" ;;
    Regenerations) echo "PedirCambio Regenerar Fallar Publicar Caer Reanudar" ;;
    *) echo "" ;;
  esac
}

# Lo que comprueba una config de control, escrito en una sola línea.
comprobadas() {
  grep -E '^(INVARIANTS?|PROPERT(Y|IES)) ' "$1" | tr -d '\r' | cut -d' ' -f2-
}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fallos=0

fallo() {
  echo "FALLO $1: $2"
  fallos=$((fallos + 1))
}

cfgs=("$@")
[ ${#cfgs[@]} -eq 0 ] && cfgs=(*.cfg)
for cfg in "${cfgs[@]}"; do
  mod=${cfg%%.*}
  espera=$(sed -n 's/^\\\* espera: *//p' "$cfg" | tr -d '\r')
  out="$tmp/$cfg.out"
  opts=(-workers auto -lncheck final -metadir "$tmp/$cfg.states")
  [ -z "$espera" ] && opts+=(-coverage 1)

  inicio=$(date +%s)
  "$JAVA" -XX:+UseParallelGC -jar "$JAR" -config "$cfg" "${opts[@]}" "$mod.tla" > "$out" 2>&1
  rc=$?
  segundos=$(( $(date +%s) - inicio ))
  estados=$(grep -oE '[0-9.,]+ distinct states found' "$out" | tail -1)
  violada=$(grep -m1 -E '^Error: .* (is|are|were) violated' "$out" | tr -d '\r')

  if [ -z "$espera" ]; then
    if [ $rc -ne 0 ] || ! grep -q 'No error has been found' "$out"; then
      fallo "$cfg" "TLC no pasa (rc=$rc): ${violada:-$(grep -m1 -E '^Error' "$out" | tr -d '\r')}"
      tail -n 40 "$out"
      continue
    fi
    sin_disparar=""
    for a in $(acciones "$mod"); do
      total=$(grep -E "^<$a line " "$out" | tail -1 | sed -E 's/.*: [0-9]+:([0-9]+).*/\1/' | tr -d '\r')
      if [ -z "$total" ] || [ "$total" -eq 0 ]; then
        sin_disparar="$sin_disparar $a"
      fi
    done
    if [ -n "$sin_disparar" ]; then
      fallo "$cfg" "acciones sin disparar:$sin_disparar"
      continue
    fi
    echo "OK $cfg: sin error, todas las acciones disparadas; $estados; ${segundos}s"
  else
    if [ $rc -eq 0 ]; then
      fallo "$cfg" "control sin contraejemplo de $espera"
    elif echo "$violada" | grep -qE "(Invariant|property) $espera is violated"; then
      echo "OK $cfg: contraejemplo de $espera; ${segundos}s"
    elif echo "$violada" | grep -q 'Temporal properties were violated' &&
         [ "$(comprobadas "$cfg")" = "$espera" ]; then
      # TLC no nombra la propiedad temporal violada: la config de control
      # solo comprueba esa, así que el contraejemplo es suyo.
      echo "OK $cfg: contraejemplo de $espera (única propiedad temporal de la config); ${segundos}s"
    else
      fallo "$cfg" "se esperaba $espera y TLC dice: $(grep -m1 -E '^Error' "$out" | tr -d '\r')"
      tail -n 40 "$out"
    fi
  fi
done

exit $(( fallos > 0 ))
