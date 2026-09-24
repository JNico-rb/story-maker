// PreToolUse hook (Edit|Write|MultiEdit) of the development harness: blocks writing new text that
// carries something shaped like a real API key (spec 000-C09; shape in architecture.md §18). Exit 2
// blocks the tool call; stderr is the reason Claude Code hands back to the model. It names the kind
// of key and the target file, never the value.
import { readFileSync } from "node:fs";

// A prefix "starts a word": at the beginning of the text or after a non [A-Za-z0-9_] character.
const key = (prefix) => new RegExp(`(?<![A-Za-z0-9_])${prefix}[A-Za-z0-9_-]{20}`);

const PATTERNS = [
  ["clave secreta de Langfuse", key("sk-lf-")],
  ["clave pública de Langfuse", key("pk-lf-")],
  ["clave de OpenRouter", key("sk-or-v1-")],
  ["clave de Anthropic", key("sk-ant-")],
  ["token clásico de GitHub", key("ghp_")],
  ["token de grano fino de GitHub", key("github_pat_")],
  ["credencial HTTP Basic", /Basic [A-Za-z0-9+/=]{40}/],
];

const input = JSON.parse(readFileSync(0, "utf8"));
const args = input.tool_input ?? {};
const texts = [args.content, args.new_string, ...(args.edits ?? []).map((e) => e.new_string)]
  .filter((t) => typeof t === "string");

for (const [kind, pattern] of PATTERNS) {
  if (texts.some((t) => pattern.test(t))) {
    process.stderr.write(
      `guard-secretos: bloqueado. El texto nuevo para ${args.file_path ?? "el fichero"} lleva algo con forma de ${kind}. ` +
        "Los secretos viven solo en .env, que escribe el usuario a mano; en código, docs y pruebas usa un " +
        "marcador como TU_CLAVE_AQUI.\n",
    );
    process.exit(2);
  }
}
