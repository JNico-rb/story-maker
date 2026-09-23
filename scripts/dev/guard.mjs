// PreToolUse hook of the development harness (.claude/settings.json).
// Turns three CLAUDE.md rules into code:
//   1. only the user marks an approval box;
//   2. a lane edits backend/ or frontend/ only when its spec and plan are approved in V2-test
//      and its section of docs/relational-matrix.md has no open blocking difference;
//   3. a lane never edits docs/, workflow/, .claude/ or CLAUDE.md: the orchestrator is their single writer.
// Lanes are the worktrees on branches v2-test-NNN[-suffix]. Any other branch passes rules 2 and 3.
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const MAIN_BRANCH = "V2-test";
const APPROVED = /^- \[x\] (Spec|Plan) approved/im;
const LANE = /^v2-test-(\d{3})(?:-[\w-]+)?$/;
const ORCHESTRATOR_ONLY = ["docs/", "workflow/", ".claude/", "CLAUDE.md"];

const deny = (reason) => {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: reason },
  }));
  process.exit(0);
};

const input = JSON.parse(readFileSync(0, "utf8"));
const args = input.tool_input ?? {};
const target = args.file_path ?? args.notebook_path;
if (!target) process.exit(0);

const file = path.resolve(input.cwd ?? process.cwd(), target);
let dir = path.dirname(file);
while (!existsSync(dir) && path.dirname(dir) !== dir) dir = path.dirname(dir);
const git = (...a) => execFileSync("git", a, { cwd: dir, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();

let root, branch;
try {
  root = git("rev-parse", "--show-toplevel");
  branch = git("rev-parse", "--abbrev-ref", "HEAD");
} catch {
  process.exit(0); // outside a git checkout: nothing to guard
}
dir = root; // later git calls resolve paths from the checkout root
const rel = path.relative(root, file).split(path.sep).join("/");

// Rule 1: approval boxes.
if (/^specs\/[^/]+\/(spec|plan)\.md$/.test(rel)) {
  const edits = input.tool_name === "MultiEdit" ? args.edits ?? []
    : input.tool_name === "Edit" ? [args]
    : [{ old_string: existsSync(file) ? readFileSync(file, "utf8") : "", new_string: args.content ?? "" }];
  if (edits.some((e) => APPROVED.test(e.new_string ?? "") && !APPROVED.test(e.old_string ?? ""))) {
    deny("Only the user marks an approval box (CLAUDE.md). Leave it unmarked and hand the file to the user.");
  }
}

const lane = LANE.exec(branch);
if (!lane) process.exit(0);

// Rule 3: single writer of the reference and harness files.
if (ORCHESTRATOR_ONLY.some((p) => rel === p || rel.startsWith(p))) {
  deny(`${rel} has one writer, the orchestrator. Send it the change with SendMessage instead of editing it in lane ${branch}.`);
}

// Rule 2: the code gate.
if (rel.startsWith("backend/") || rel.startsWith("frontend/")) {
  const nnn = lane[1];
  try {
    const folder = git("ls-tree", "-d", "--name-only", `${MAIN_BRANCH}:specs`).split("\n").find((f) => f.startsWith(`${nnn}-`));
    if (!folder) deny(`Gate closed: ${MAIN_BRANCH} has no specs/${nnn}-*/.`);
    const show = (p) => git("show", `${MAIN_BRANCH}:${p}`);
    if (!/^- \[x\] Spec approved/m.test(show(`specs/${folder}/spec.md`))) deny(`Gate closed: specs/${folder}/spec.md is not approved in ${MAIN_BRANCH}.`);
    if (!/^- \[x\] Plan approved/m.test(show(`specs/${folder}/plan.md`))) deny(`Gate closed: specs/${folder}/plan.md is not approved in ${MAIN_BRANCH}.`);
    const matrix = show("docs/relational-matrix.md");
    const start = matrix.indexOf(`### ${folder}`);
    const section = start < 0 ? "" : matrix.slice(start).split(/\n### /)[0];
    const open = section.split("\n").filter((l) => /\|\s*bloqueante\s*\|/.test(l) && /\|\s*abierta\s*\|\s*$/.test(l));
    if (open.length) deny(`Gate closed: ${open.length} open blocking difference(s) for ${folder} in docs/relational-matrix.md.`);
  } catch (e) {
    deny(`Gate check failed (${e.message.split("\n")[0]}); ask the orchestrator.`);
  }
}
