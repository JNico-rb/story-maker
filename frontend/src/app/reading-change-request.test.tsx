import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "../shared/api/schema";
import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

// Caducidad relativa al reloj real: una fecha fija caduca sola (y una lejana desborda setTimeout).
const IN_ONE_HOUR = new Date(Date.now() + 3_600_000).toISOString();

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

function baseRoutes(): Record<string, Reply> {
  return {
    [`GET ${BASE}`]: () => json(200, LIST),
    [`GET ${BASE}/1`]: () => json(200, DETAIL),
  };
}

// Abre el panel desde la lectura: selecciona el texto del capítulo 3 y pulsa «pedir un cambio».
async function openChangeRequestForm(user: ReturnType<typeof userEvent.setup>) {
  renderReading();
  const chapter = await screen.findByRole("region", { name: /Capítulo 3/ });
  selectChapterText(chapter);
  await user.click(screen.getByRole("button", { name: /pedir un cambio/i }));
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});

describe("027 cambio del lector", () => {
  it("027-C01: selecting a fragment in a chapter and asking for a change opens the request form", async () => {
    const user = userEvent.setup();
    fakeApi(baseRoutes());

    await openChangeRequestForm(user);

    const form = screen.getByRole("form", { name: "Petición de cambio" });
    expect(within(form).getByText(CHAPTER_3_TEXT, { exact: false })).toBeInTheDocument();
    expect(within(form).getByRole("textbox", { name: "Petición" })).toHaveValue("");
  });

  it("027-C09: confirming queues the run and the reading shows it is in progress", async () => {
    const user = userEvent.setup();
    fakeApi({
      ...baseRoutes(),
      [`POST /api/novels/${NOVEL}/change-requests`]: () =>
        json(201, {
          id: "req-1",
          proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
          affected_chapters: [2],
          code: "SECRETO-123",
          expires_at: IN_ONE_HOUR,
        }),
      "POST /api/change-requests/req-1/confirm": () => json(202, { run_id: "run-9" }),
    });

    await openChangeRequestForm(user);
    await user.type(screen.getByRole("textbox", { name: "Petición" }), "el perro se llama Nala");
    await user.click(screen.getByRole("button", { name: "Pedir el cambio" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar" }));

    expect(await screen.findByText(/cambio.*en marcha/i)).toBeInTheDocument();
    expect(screen.getByText(/run-9/)).toBeInTheDocument();
    expect(screen.queryByText("SECRETO-123")).not.toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Portada" })).toBeInTheDocument();
  });
});
