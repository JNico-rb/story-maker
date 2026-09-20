#!/usr/bin/env bash
# Comprueba que ningun puntero de la documentacion apunta a la nada:
#  1. enlaces markdown [x](y.md) a ficheros que no existen
#  2. referencias a specs/*.md borradas
#  3. referencias §n a una seccion que no existe en la spec que la contiene
#
# Fuera del harness: no lo llama /novela. Salida 1 si algo falla, 0 si todo esta bien.
#
# OJO al modificar: cada comprobacion tiene que poder marcar `fallos=1` en ESTE shell.
# Un `while` al final de una tuberia corre en un subshell y su asignacion se pierde,
# que es justamente el fallo que tenia la version anterior: imprimia los enlaces rotos
# y salia 0. Por eso las comprobaciones EMITEN texto y el padre decide con ese texto.
set -u
cd "$(dirname "$0")/.." || exit 2
fallos=0

# Que ficheros son "documentacion viva" (excluye salidas generadas)
ficheros() {
  git ls-files '*.md' '*.json' '*.py' '*.sh' \
    | grep -v '^novelas/' | grep -v '^optimizaciones/[a-z-]*-[0-9]' \
    | grep -v '^validaciones/' | grep -v '^pruebas/' \
    | grep -v '^herramientas/optimizacion/casos/' | grep -v '^.claude/skills/langfuse/' \
    | grep -v '^.claude/skills/feature-sliced-design/'
}

# ── 1. enlaces markdown rotos ────────────────────────────────────────────────
# El bucle interno corre en un subshell y solo puede emitir; quien decide es el padre.
echo "== 1. enlaces markdown rotos =="
rotos=$(
  while IFS= read -r f; do
    dir=$(dirname "$f")
    grep -o '](\([^)]*\.md\)[^)]*)' "$f" 2>/dev/null \
      | sed 's/^](//; s/[)#].*$//; s/#.*$//' \
      | while IFS= read -r destino; do
          case "$destino" in http*|"") continue;; esac
          [ -e "$dir/$destino" ] || echo "  ROTO  $f -> $destino"
        done
  done < <(ficheros | grep '\.md$')
)
if [ -n "$rotos" ]; then echo "$rotos"; fallos=1; else echo "  (ninguno)"; fi

# ── 2. specs retiradas todavia citadas ───────────────────────────────────────
echo "== 2. specs retiradas todavia citadas =="
muertas=$(
  for muerta in hallazgos.md inventario.md consolidacion-2026-09-18.md revision-harness-2026-09-17.md; do
    [ -e "specs/$muerta" ] && continue
    # El CHANGELOG cuenta la historia y el frontmatter `sustituye_a` la declara:
    # citarlas ahi es correcto, no un puntero roto.
    ficheros | grep -v '^CHANGELOG.md$' | grep -v '^herramientas/comprobar_punteros.sh$' \
      | while IFS= read -r h; do
          grep -n "$muerta" "$h" 2>/dev/null | grep -v 'sustituye_a' \
            | while IFS= read -r linea; do
                echo "  CITA MUERTA  $h:${linea%%:*} -> $muerta"
              done
        done
  done
)
if [ -n "$muertas" ]; then echo "$muertas"; fallos=1; else echo "  (ninguna)"; fi

# ── 3. secciones § inexistentes ──────────────────────────────────────────────
# Solo se comprueba lo que resuelve SIN ambiguedad: §9.x vive en technical.md y el
# resto en functional.md (CLAUDE.md, "Donde esta cada cosa"). Lo ambiguo se cuenta
# y se dice, no se da por bueno ni por roto: un comprobador que grita en falso se
# acaba ignorando, y entonces da igual que funcione.
echo "== 3. secciones § inexistentes =="

# Hasta ###### a proposito: §9.3.1 y §9.5.1 son encabezados de cuatro almohadillas.
# Con el patron #{2,3} de la version anterior toda la profundidad 3 salia como rota.
secciones_de() { grep -o '^#\{2,6\} [0-9]\+\(\.[0-9]\+\)*' "$1" | sed 's/^#* //'; }
SEC_FUNCIONAL=$(secciones_de specs/functional.md)
SEC_TECNICA=$(secciones_de specs/technical.md)

existe_seccion() { # $1 = numero, $2 = lista
  printf '%s\n' "$2" | grep -qx "$1"
}

huerfanas=$(
  # architecture.md tiene numeracion propia (§1-§5) y sus § no resuelven con esta
  # regla; el CHANGELOG cita secciones de versiones pasadas a proposito.
  ficheros | grep '\.md$' | grep -v '^CHANGELOG.md$' | grep -v '^specs/architecture.md$' \
    | while IFS= read -r f; do
        grep -o '§[0-9]\+\(\.[0-9]\+\)*' "$f" 2>/dev/null | sed 's/^§//' | sort -u \
          | while IFS= read -r ref; do
              case "$ref" in
                9|9.*) existe_seccion "$ref" "$SEC_TECNICA" \
                         || echo "  SIN DESTINO  $f -> §$ref (no esta en specs/technical.md)" ;;
                *)     existe_seccion "$ref" "$SEC_FUNCIONAL" \
                         || echo "  SIN DESTINO  $f -> §$ref (no esta en specs/functional.md)" ;;
              esac
            done
      done
)
if [ -n "$huerfanas" ]; then echo "$huerfanas"; fallos=1; else echo "  (ninguna)"; fi
echo "  no comprobadas: las § de specs/architecture.md y CHANGELOG.md (numeracion propia o historica)"

echo
if [ "$fallos" = 0 ]; then echo "OK: ningun puntero roto"; else echo "FALLOS: ver arriba"; fi
exit "$fallos"
