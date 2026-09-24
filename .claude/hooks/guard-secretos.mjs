// PreToolUse hook (Edit|Write|MultiEdit) of the development harness: blocks writing content that
// carries something shaped like a real API key. Exit 2 blocks the tool call; stderr is the reason
// Claude Code hands back to the model. It names the kind of key, never the value.
import { readFileSync } from "node:fs";

const PATTERNS = [
  ["clave secreta de Langfuse", /sk-lf-[0-9a-f-]{20,}/],
  ["clave pública de Langfuse", /pk-lf-[0-9a-f-]{20,}/],
  ["clave de OpenRouter", /sk-or-v1-[0-9a-f]{20,}/],
  ["clave de Anthropic", /sk-ant-[A-Za-z0-9_-]{20,}/],
  ["token clásico de GitHub", /ghp_[A-Za-z0-9]{30,}/],
  ["token de grano fino de GitHub", /github_pat_[A-Za-z0-9_]{30,}/],
  ["credencial HTTP Basic", /Basic [A-Za-z0-9+/=]{40,}/],
];

const input = JSON.parse(readFileSync(0, "utf8"));
const args = input.tool_input ?? {};
const texts = [args.content, args.new_string, ...(args.edits ?? []).map((e) => e.new_string)]
  .filter((t) => typeof t === "string");

for (const [kind, pattern] of PATTERNS) {
  if (texts.some((t) => pattern.test(t))) {
    process.stderr.write(
      `guard-secretos: bloqueado. El contenido para ${args.file_path ?? "el fichero"} lleva algo con forma de ${kind}. ` +
        "Los secretos viven solo en .env (que nadie lee ni commitea); en código, docs y pruebas usa un " +
        "marcador como TU_CLAVE_AQUI o <OPENROUTER_API_KEY>.\n",
    );
    process.exit(2);
  }
}
