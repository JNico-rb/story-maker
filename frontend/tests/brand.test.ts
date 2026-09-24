import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const frontend = path.resolve(import.meta.dirname, "..");
const src = path.join(frontend, "src");
const tokensFile = path.join(src, "app", "styles", "index.css");

function filesUnder(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    return statSync(full).isDirectory() ? filesUnder(full) : [full];
  });
}

describe("brand theme", () => {
  it("defines the seven brand tokens with their exact values", () => {
    const css = readFileSync(tokensFile, "utf8");
    const tokens = Object.fromEntries(
      [...css.matchAll(/^\s*(--[\w-]+):\s*([^;]+);/gm)].map(([, name, value]) => [name, value?.trim()]),
    );

    expect(tokens).toMatchObject({
      "--color-primary": "#ff7932",
      "--color-secondary": "#233441",
      "--color-background": "#faf8f5",
      "--color-text": "#233441",
      "--color-accent": "#ffe8da",
    });
    expect(tokens["--font-ui"]).toMatch(/^"Inter Tight"/);
    expect(tokens["--font-reading"]).toMatch(/^"Literata"/);
  });

  it("loads both typefaces from installed packages, never from a URL", () => {
    const sources = filesUnder(src)
      .filter((file) => /\.(css|tsx?)$/.test(file))
      .map((file) => readFileSync(file, "utf8"))
      .join("\n");

    expect(sources).toContain('import "@fontsource/inter-tight');
    expect(sources).toContain('import "@fontsource/literata');
    expect(sources).not.toMatch(/https?:\/\//);
  });

  it("has a single logo file, byte-identical to images/qaracter-logo.png", () => {
    const logos = filesUnder(src).filter((file) => /logo/i.test(path.basename(file)) && /\.(png|svg|jpe?g|webp)$/.test(file));
    const original = readFileSync(path.join(frontend, "..", "images", "qaracter-logo.png"));

    expect(logos).toHaveLength(1);
    expect(readFileSync(logos[0] ?? "").equals(original)).toBe(true);
  });
});

describe("brand usage", () => {
  it("no file of src/ outside the tokens has a hex colour or declares a typeface", () => {
    const offenders = filesUnder(src)
      .filter((file) => file !== tokensFile && /\.(css|tsx?|html)$/.test(file))
      .filter((file) => /#[0-9a-fA-F]{3,8}\b|font-family|fontFamily/.test(readFileSync(file, "utf8")))
      .map((file) => path.relative(frontend, file));

    expect(offenders).toEqual([]);
  });
});
