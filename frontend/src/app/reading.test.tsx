import { render, screen, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "../shared/api/schema";
import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

type VersionDetail = components["schemas"]["VersionDetailResponse"];
type VersionsList = components["schemas"]["VersionsListResponse"];

// API simulada en el límite del cliente (026-I5): cada ruta responde lo que fija 013 para N.
type Reply = () => Response;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fakeApi(replies: Record<string, Reply>): string[] {
  const sent: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const key = `${init?.method ?? "GET"} ${String(input)}`;
      sent.push(key);
      const reply = replies[key];
      if (!reply) throw new Error(`ruta no simulada: ${key}`);
      return reply();
    }),
  );
  return sent;
}

const NOVEL = 7;
const BASE = `/api/novels/${NOVEL}/versions`;
const CHAPTERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// V1 sin capítulos cambiados, con Toby en la ficha; V2 cambia los capítulos 3 y 7 y nombra a Nala.
function detail(version: 1 | 2): VersionDetail {
  const changed = version === 2 ? [3, 7] : [];
  const tag = (n: number) => (changed.includes(n) ? `v${version}` : "v1");
  return {
    version,
    view: {
      title: "La casa del faro",
      recipient: "Destinataria de prueba",
      dedication: "Para quien espera la luz.",
      version_number: version,
      chapters: CHAPTERS.map((n) => ({
        number: n,
        title: `Título ${n} ${tag(n)}`,
        text: `Texto del capítulo ${n} en ${tag(n)}.`,
      })),
      changed_chapters: changed,
      ficha:
        version === 1
          ? [{ name: "Toby", kind: "personaje", chapters: [2, 5] }]
          : [{ name: "Nala", kind: "personaje", chapters: [3, 7] }],
    },
  };
}

const LIST: VersionsList = {
  versions: [
    { number: 1, published_at: "2026-09-20T10:00:00Z", changed_chapters: [] },
    { number: 2, published_at: "2026-09-22T10:00:00Z", changed_chapters: [3, 7] },
  ],
};

// N vista en V1: la lista publicada acaba en V1, así que es la vigente al entrar.
function apiAtV1(extra: Record<string, Reply> = {}): string[] {
  return fakeApi({
    [`GET ${BASE}`]: () => json(200, { versions: LIST.versions.slice(0, 1) }),
    [`GET ${BASE}/1`]: () => json(200, detail(1)),
    ...extra,
  });
}

function renderReading() {
  const router = createMemoryRouter(buildRoutes(), {
    initialEntries: [`/novelas/${NOVEL}/lectura`],
  });
  render(<RouterProvider router={router} />);
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});

describe("026 lectura", () => {
  it("026-C01: without a version indicated, the reading shows the current one (highest published)", async () => {
    const sent = fakeApi({
      [`GET ${BASE}`]: () => json(200, LIST),
      [`GET ${BASE}/2`]: () => json(200, detail(2)),
    });
    renderReading();

    const cover = await screen.findByRole("region", { name: "Portada" });
    expect(within(cover).getByRole("heading", { name: "La casa del faro" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Versión" })).toHaveValue("2");
    expect(sent).toEqual([`GET ${BASE}`, `GET ${BASE}/2`]);
  });

  it("026-C02: the cover shows the title, the recipient's name and the dedication", async () => {
    apiAtV1();
    renderReading();

    const cover = await screen.findByRole("region", { name: "Portada" });
    expect(within(cover).getByRole("heading", { name: "La casa del faro" })).toBeInTheDocument();
    expect(within(cover).getByText(/Destinataria de prueba/)).toBeInTheDocument();
    expect(within(cover).getByText("Para quien espera la luz.")).toBeInTheDocument();
  });
});
