import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "../shared/api/schema";
import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

type VersionDetail = components["schemas"]["VersionDetailResponse"];
type VersionsList = components["schemas"]["VersionsListResponse"];

// Mismo patrón de API simulada que src/app/reading.test.tsx (026-I5).
type Reply = () => Response;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fakeApi(replies: Record<string, Reply>): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const key = `${init?.method ?? "GET"} ${String(input)}`;
      const reply = replies[key];
      if (!reply) throw new Error(`ruta no simulada: ${key}`);
      return reply();
    }),
  );
}

const NOVEL = 7;
const BASE = `/api/novels/${NOVEL}/versions`;
const CHAPTER_3_TEXT = "Texto del capítulo 3 en v1.";

const DETAIL: VersionDetail = {
  version: 1,
  view: {
    title: "La casa del faro",
    recipient: "Destinataria de prueba",
    dedication: "Para quien espera la luz.",
    version_number: 1,
    chapters: [1, 2, 3].map((n) => ({
      number: n,
      title: `Título ${n}`,
      text: n === 3 ? CHAPTER_3_TEXT : `Texto del capítulo ${n} en v1.`,
    })),
    changed_chapters: [],
    ficha: [{ name: "Toby", kind: "personaje", chapters: [2] }],
  },
};

const LIST: VersionsList = {
  versions: [{ number: 1, published_at: "2026-09-20T10:00:00Z", changed_chapters: [] }],
};

function renderReading() {
  const router = createMemoryRouter(buildRoutes(), {
    initialEntries: [`/novelas/${NOVEL}/lectura`],
  });
  render(<RouterProvider router={router} />);
}

// Selecciona todo el texto del párrafo del capítulo dado, como haría la persona con el ratón.
function selectChapterText(chapterSection: HTMLElement) {
  const textNode = chapterSection.querySelector("p")?.firstChild;
  if (!textNode) throw new Error("el capítulo no tiene texto");
  const range = document.createRange();
  range.setStart(textNode, 0);
  range.setEnd(textNode, textNode.textContent?.length ?? 0);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
  fireEvent.mouseUp(chapterSection);
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
  fakeApi({
    [`GET ${BASE}`]: () => json(200, LIST),
    [`GET ${BASE}/1`]: () => json(200, DETAIL),
  });
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});

describe("027 cambio del lector", () => {
  it("027-C01: selecting a fragment in a chapter and asking for a change opens the request form", async () => {
    const user = userEvent.setup();
    renderReading();

    const chapter = await screen.findByRole("region", { name: /Capítulo 3/ });
    selectChapterText(chapter);
    await user.click(screen.getByRole("button", { name: /pedir un cambio/i }));

    const form = screen.getByRole("form", { name: "Petición de cambio" });
    expect(within(form).getByText(CHAPTER_3_TEXT, { exact: false })).toBeInTheDocument();
    expect(within(form).getByRole("textbox", { name: "Petición" })).toHaveValue("");
  });
});
