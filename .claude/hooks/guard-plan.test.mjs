// node --test: guard-plan blocks tests and code without an approved plan with pending steps
// (spec 000-C10), and decides the same with the current directory in a subdirectory (000-I5).
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, test } from "node:test";
import { fileURLToPath } from "node:url";

const hook = fileURLToPath(new URL("./guard-plan.mjs", import.meta.url));
const scratch = mkdtempSync(path.join(tmpdir(), "guard-plan-"));
after(() => rmSync(scratch, { recursive: true, force: true }));

const block = (plan, steps, closing = "- [ ] Full suite green, type checks clean") =>
  `# TODO\n\n## Carriles\n\n## 001 — base\n\n- [x] Spec \`specs/backend/001-base.md\` approved\n${plan}\n\n### Steps\n${steps}\n\n### Closing\n${closing}\n`;

const TODOS = {
  none: block("- [ ] Plan below approved", "- [ ] 001-C01 · algo"),
  missing: null,
  unapproved: block("- [ ] Plan below approved", "- [ ] 001-C01 · algo\n- [ ] 001-C02 · otro"),
  allDone: block("- [x] Plan below approved", "- [x] 001-C01 · algo"),
  open: block("- [x] Plan below approved — auditor 2026-09-25: acta", "- [x] 001-C01 · algo\n- [ ] 001-C02 · otro"),
};

let n = 0;
function project(todo) {
  const root = path.join(scratch, `p${n++}`);
  mkdirSync(path.join(root, "backend"), { recursive: true });
  if (todo !== null) writeFileSync(path.join(root, "TODO.md"), todo);
  return root;
}

function run(root, filePath, cwd = root) {
  const payload = { cwd, tool_name: "Write", tool_input: { file_path: filePath, content: "x" } };
  return spawnSync(process.execPath, [hook], {
    cwd,
    input: JSON.stringify(payload),
    encoding: "utf8",
    env: { ...process.env, CLAUDE_PROJECT_DIR: root },
  });
}

const GUARDED = [
  "backend/tests/test_x.py",
  "backend/src/story_maker/domain/x.py",
  "frontend/src/app/x.tsx",
  "frontend/tests/x.test.ts",
  "lean/X.lean",
  "tla/Harness.tla",
  ".github/workflows/ci.yml",
];
const FREE = [
  "docs/x.md",
  "specs/backend/001-base.md",
  "TODO.md",
  "README.md",
  ".claude/hooks/x.mjs",
  "backend/pyproject.toml",
  "frontend/package.json",
  "backend/harness_workspace/CLAUDE.md",
];

// The same table from the project root and from backend/ (000-I5): relative paths are the
// session's, so from backend/ they are written relative to it, and absolute ones stay absolute.
for (const sub of ["", "backend"]) {
  const where = sub ? " (cwd in backend/)" : "";
  const target = (root, rel) => (sub ? path.join(root, rel) : rel);

  for (const rel of GUARDED) {
    test(`denies ${rel} when no block has an approved plan, naming path and what is missing${where}`, () => {
      const root = project(TODOS.none);
      const result = run(root, target(root, rel), path.join(root, sub));
      assert.equal(result.status, 2);
      assert.ok(result.stderr.includes(rel));
      assert.match(result.stderr, /Plan below approved/);
    });

    test(`denies ${rel} when TODO.md does not exist${where}`, () => {
      const root = project(TODOS.missing);
      assert.equal(run(root, target(root, rel), path.join(root, sub)).status, 2);
    });
  }

  test(`denies backend/src when the plan box is unmarked and steps are pending${where}`, () => {
    const root = project(TODOS.unapproved);
    assert.equal(run(root, target(root, "backend/src/x.py"), path.join(root, sub)).status, 2);
  });

  test(`denies backend/src when every step is done and only the closing is pending${where}`, () => {
    const root = project(TODOS.allDone);
    assert.equal(run(root, target(root, "backend/src/x.py"), path.join(root, sub)).status, 2);
  });

  test(`lets backend/src through with an approved plan and a pending step${where}`, () => {
    const root = project(TODOS.open);
    assert.equal(run(root, target(root, "backend/src/x.py"), path.join(root, sub)).status, 0);
  });

  test(`a relative path from backend/ resolves against it${where}`, () => {
    const root = project(TODOS.none);
    const rel = sub ? "tests/test_x.py" : "backend/tests/test_x.py";
    assert.equal(run(root, rel, path.join(root, sub)).status, 2);
  });

  for (const rel of FREE) {
    test(`lets ${rel} through whatever TODO.md says${where}`, () => {
      const root = project(TODOS.none);
      assert.equal(run(root, target(root, rel), path.join(root, sub)).status, 0);
    });
  }

  test(`lets a path outside the project through${where}`, () => {
    const root = project(TODOS.none);
    const outside = path.join(scratch, "otro", "backend", "tests", "test_x.py");
    assert.equal(run(root, outside, path.join(root, sub)).status, 0);
  });

  test(`denies a Windows-style absolute path with backslashes and a lowercase drive letter${where}`, () => {
    const root = project(TODOS.none);
    const abs = path.join(root, "backend", "tests", "test_x.py");
    const windowsStyle = abs.replace(/\//g, "\\").replace(/^([A-Z]):/, (_, d) => `${d.toLowerCase()}:`);
    assert.equal(run(root, windowsStyle, path.join(root, sub)).status, 2);
  });
}
