// node --test: guard-secretos decide by the shape of the new text (spec 000-C09, 000-I5).
// Fake keys are built at run time so no key-shaped string is ever versioned (000-I4).
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const hook = fileURLToPath(new URL("./guard-secretos.mjs", import.meta.url));
const projectRoot = path.resolve(path.dirname(hook), "..", "..");

const body = (n) => "TEST".repeat(10).slice(0, n);
const PREFIXES = ["sk-lf-", "pk-lf-", "sk-or-v1-", "sk-ant-", "ghp_", "github_pat_"];

function run(toolInput, cwd = projectRoot) {
  const payload = { tool_name: "Write", tool_input: { file_path: "docs/x.md", ...toolInput } };
  return spawnSync(process.execPath, [hook], { cwd, input: JSON.stringify(payload), encoding: "utf8" });
}

for (const cwd of [projectRoot, path.join(projectRoot, "backend")]) {
  const where = cwd === projectRoot ? "" : " (cwd in backend/)";

  for (const prefix of PREFIXES) {
    test(`denies ${prefix} followed by 20 key characters, naming kind and file, never the key${where}`, () => {
      const key = prefix + body(20);
      const result = run({ content: `clave: ${key}` }, cwd);

      assert.equal(result.status, 2);
      assert.match(result.stderr, /docs\/x\.md/);
      assert.match(result.stderr, /forma de /);
      assert.ok(!result.stderr.includes(key));
      assert.ok(!result.stderr.includes(body(20)));
    });

    test(`lets ${prefix} followed by 19 characters through${where}`, () => {
      assert.equal(run({ content: `clave: ${prefix}${body(19)}` }, cwd).status, 0);
    });

    test(`lets the bare prefix ${prefix} quoted in a doc through${where}`, () => {
      assert.equal(run({ content: `Las claves empiezan por \`${prefix}\`.` }, cwd).status, 0);
    });

    test(`lets ${prefix} glued to a previous letter through${where}`, () => {
      assert.equal(run({ content: `x${prefix}${body(20)}` }, cwd).status, 0);
    });
  }

  test(`denies Basic followed by 40 base64 characters${where}`, () => {
    const result = run({ content: `Authorization: Basic ${"QUJD".repeat(10)}` }, cwd);
    assert.equal(result.status, 2);
    assert.ok(!result.stderr.includes("QUJD".repeat(10)));
  });

  test(`lets Basic followed by 39 base64 characters through${where}`, () => {
    assert.equal(run({ content: `Authorization: Basic ${"QUJD".repeat(10).slice(1)}` }, cwd).status, 0);
  });

  test(`lets an empty setting or the TU_CLAVE_AQUI placeholder through${where}`, () => {
    assert.equal(run({ content: "LANGFUSE_SECRET_KEY=\nLANGFUSE_SECRET_KEY=TU_CLAVE_AQUI\n" }, cwd).status, 0);
  });

  test(`denies a key only in the second edit of a MultiEdit${where}`, () => {
    const edits = [
      { old_string: "a", new_string: "b" },
      { old_string: "c", new_string: `sk-ant-${body(20)}` },
    ];
    assert.equal(run({ edits }, cwd).status, 2);
  });

  test(`lets an Edit that replaces a leaked key with a placeholder through${where}`, () => {
    assert.equal(run({ old_string: `sk-ant-${body(20)}`, new_string: "TU_CLAVE_AQUI" }, cwd).status, 0);
  });

  test(`denies a real-shaped key even when the target is .env${where}`, () => {
    assert.equal(run({ file_path: ".env", content: `OPENROUTER_API_KEY=sk-or-v1-${body(20)}` }, cwd).status, 2);
  });

  test(`lets text without keys through${where}`, () => {
    assert.equal(run({ content: "Texto corriente sin claves." }, cwd).status, 0);
  });
}
