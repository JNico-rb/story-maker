# Resumen de TODO.md por spec, sin leer el fichero entero:
#   git show V2:TODO.md | awk -f .claude/scripts/resumen-todo.awk
function p() { printf "%s  spec[%s] plan[%s]  pasos %d/%d (D pendientes %d)  cierre %d/3\n", n, sp, pl, x, t, d, c }
/^## [0-9][0-9][0-9] / { if (n) p(); n = $2; sp = pl = "-"; s = x = t = d = c = 0; next }
/^## / { if (n) p(); n = ""; next }
/^### Steps/ { s = 1; next }
/^### Closing/ { s = 2; next }
n && /^- \[[ x]\]/ {
  m = substr($0, 4, 1) == "x"
  if (s == 0) { if (sp == "-") sp = m ? "x" : " "; else pl = m ? "x" : " " }
  else if (s == 1) { t++; x += m; if (!m && /\(D, al final\)/) d++ }
  else c += m
}
END { if (n) p() }
