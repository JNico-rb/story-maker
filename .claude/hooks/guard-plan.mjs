// PreToolUse hook (Edit|Write|MultiEdit) of the development harness: code under backend/src or
// frontend/src needs a TODO.md block whose plan is approved and still has a pending step
// (AGENTS.md, Gates). The checkout root is the nearest ancestor of the edited file holding `.git`
// (a directory in the main checkout, a file in a lane worktree), so each worktree answers to its
// own TODO.md. Exit 2 blocks the tool call; stderr is the reason handed back to the model.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const input = JSON.parse(readFileSync(0, "utf8"));
const target = input.tool_input?.file_path;
if (!target) process.exit(0);

const file = path.resolve(input.cwd ?? process.cwd(), target);
let root = path.dirname(file);
while (!existsSync(path.join(root, ".git"))) {
  const parent = path.dirname(root);
  if (parent === root) process.exit(0); // outside any checkout: nothing to guard
  root = parent;
}
const rel = path.relative(root, file).split(path.sep).join("/");
if (!/^(backend|frontend)\/src\//.test(rel)) process.exit(0);

const todoPath = path.join(root, "TODO.md");
const todo = existsSync(todoPath) ? readFileSync(todoPath, "utf8") : "";
const hasOpenPlan = todo
  .split(/^## /m)
  .slice(1)
  .some((block) => {
    if (!/^- \[[xX]\] Plan below approved/m.test(block)) return false;
    const steps = block.split(/^### Steps/m)[1]?.split(/^#{2,3} /m)[0] ?? "";
    return /^- \[ \] /m.test(steps);
  });
if (hasOpenPlan) process.exit(0);

process.stderr.write(
  `guard-plan: bloqueado ${rel}. Ningún bloque de ${todoPath} tiene "- [x] Plan below approved" ` +
    'con algún paso "- [ ]" pendiente, y el código solo se escribe para un paso de un plan aprobado ' +
    "(AGENTS.md, Gates). Siguiente: si la spec no tiene plan aprobado, /plan NNN (lo aprueba el " +
    "auditor); si todos sus pasos están [x], ese código ya no lo pide ningún plan; si estás en un " +
    "worktree, haz git rebase V2 por si el plan se aprobó en V2.\n",
);
process.exit(2);
