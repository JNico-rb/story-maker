#!/bin/sh
# Hook PreToolUse de Bash. Lo registra .claude/settings.json.
#
# Cierra el agujero que dejaba el `deny` de `Read`: en Claude Code ese deny gobierna
# la herramienta `Read`, NO lo que la herramienta `Bash` pueda leer. Con `Bash(cat *)`
# en el allow, `cat herramientas/optimizacion/conjuntos/<x>.jsonl` pasaba, y con el
# `cat .claude/settings.local.json`. Es decir: las tres rutas que la spec declara
# ilegibles desde la sesion eran legibles con un rodeo de una linea.
#
# Lo que protege (specs/technical.md §9.3 regla 6 y §9.5):
#   - .env y frontend/.env            credenciales
#   - .claude/settings.local.json     credenciales de Langfuse
#   - herramientas/optimizacion/conjuntos/   el conjunto etiquetado: si el optimizador
#     lo ve, la forma mas barata de subir la metrica es aprenderse el examen, y el
#     bucle /optimizar deja de medir nada (evidencia E5).
#
# FALLA EN CERRADO, al reves que inmutables.sh. Esa diferencia es deliberada: alli
# un bloqueo indebido parte el bucle de la novela a media ejecucion, aqui lo unico
# que pasa es que un comando se para y el usuario lo repite. Cuando el hook no
# entiende su entrada no puede afirmar que el comando es inocuo, y en una linea roja
# «no lo se» vale «no».
#
# NO es un sandbox contra un adversario: quien quiera saltarselo puede ofuscar la
# ruta (variables, base64, enlaces). Lo que impide es el camino barato, que es el
# unico que un agente va a tomar. El aislamiento fuerte del conjunto etiquetado es
# el de §9.5: el optimizador nunca lo recibe en su prompt.

entrada=$(cat)

rechaza() {
  echo "story-maker: comando bloqueado. $1 (specs/technical.md §9.3 regla 6 y §9.5, .claude/hooks/rutas-protegidas.sh). Estas rutas no se leen desde la sesion: contienen credenciales o el conjunto etiquetado que el optimizador no puede ver." >&2
  exit 2
}

# Falla en cerrado: sin entrada no hay nada que autorizar.
[ -n "$entrada" ] || rechaza "El hook no pudo leer su entrada, asi que no puede afirmar que el comando sea inocuo."

# Se mira la entrada CRUDA, no el valor extraido de `command`. Extraer el campo con
# grep/sed se corta en la primera comilla escapada, y un `cat "x" .env` quedaria en
# `cat ` — o sea, un bloqueo que se abre solo con poner una comilla. Para un hook que
# deniega, mirar de mas es seguro y mirar de menos no lo es. En una llamada a Bash la
# entrada solo trae `command` y `description`, asi que tampoco hay mucho de mas.
texto=$(printf '%s' "$entrada" | sed 's|\\\\|/|g; s|\\|/|g')

# .env y frontend/.env, pero NO .env.example: tras `.env` va un punto, que esta en la
# clase excluida, asi que `.env.example` no casa.
if printf '%s' "$texto" | grep -Eq '(^|[^A-Za-z0-9_.-])\.env([^A-Za-z0-9_.-]|$)'; then
  rechaza "Referencia a un fichero .env."
fi

if printf '%s' "$texto" | grep -q 'settings\.local\.json'; then
  rechaza "Referencia a .claude/settings.local.json."
fi

if printf '%s' "$texto" | grep -q 'optimizacion/conjuntos'; then
  rechaza "Referencia a herramientas/optimizacion/conjuntos/."
fi

exit 0
