// PreToolUse hook (Edit|Write|MultiEdit) of the development harness: tests and code need a TODO.md
// block whose plan is approved and still has a pending step (AGENTS.md, gate "Write tests or code";
// spec 000-C10). The project root is the one Claude Code gives the hook (CLAUDE_PROJECT_DIR), so a
// session opened in a lane worktree answers to that worktree's TODO.md. Exit 2 blocks the tool call;
// stderr is the reason handed back to the model. Any other failure would let the call through, which
// is why a missing TODO.md denies.
import { existsSync, readFileSync } from "node:fs";

const GUARDED = /^(backend\/src|backend\/tests|frontend\/src|frontend\/tests|lean|tla|\.github\/workflows)\//;

// Windows paths arrive with backslashes and either case of drive letter; compare them as a/b/c.
const normalize = (p) => p.replace(/\\/g, "/").replace(/^([a-z]):/, (_, d) => `${d.toUpperCase()}:`);
const isAbsolute = (p) => p.startsWith("/") || /^[A-Z]:\//.test(p);

const input = JSON.parse(readFileSync(0, "utf8"));
const target = input.tool_input?.file_path;
if (!target) process.exit(0);

const root = normalize(process.env.CLAUDE_PROJECT_DIR ?? input.cwd ?? process.cwd()).replace(/\/$/, "");
const cwd = normalize(input.cwd ?? process.cwd()).replace(/\/$/, "");
const file = isAbsolute(normalize(target)) ? normalize(target) : `${cwd}/${normalize(target)}`;
const inside = process.platform === "win32" ? file.toLowerCase().startsWith(`${root.toLowerCase()}/`) : file.startsWith(`${root}/`);
if (!inside) process.exit(0);

const rel = file.slice(root.length + 1);
if (!GUARDED.test(rel)) process.exit(0);

const todoPath = `${root}/TODO.md`;
const todo = existsSync(todoPath) ? readFileSync(todoPath, "utf8") : null;
const hasOpenPlan = (todo ?? "")
  .split(/^## /m)
  .slice(1)
  .some((block) => {
    if (!/^- \[[xX]\] Plan below approved/m.test(block)) return false;
    const steps = block.split(/^### Steps\s*$/m)[1]?.split(/^### /m)[0] ?? "";
    return /^- \[ \] /m.test(steps);
  });
if (hasOpenPlan) process.exit(0);

const missing = todo === null ? `no existe ${todoPath}` : `ningún bloque de ${todoPath} tiene "- [x] Plan below approved" con algún paso "- [ ]" pendiente bajo "### Steps"`;
process.stderr.write(
  `guard-plan: bloqueado ${rel}: ${missing}. Las pruebas y el código solo se escriben para un paso de un ` +
    "plan aprobado (AGENTS.md, Gates). Siguiente: si la spec no tiene plan aprobado, /plan NNN (lo aprueba " +
    "el auditor); si todos sus pasos están [x], ese código ya no lo pide ningún plan; en un worktree, " +
    "git rebase V2 por si el plan se aprobó en V2.\n",
);
process.exit(2);
