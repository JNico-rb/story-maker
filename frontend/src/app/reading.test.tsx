import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("026-C03: the index lists the 10 chapters and links to each one, with no changed mark", async () => {
    apiAtV1();
    renderReading();

    const index = await screen.findByRole("navigation", { name: "Índice" });
    const links = within(index).getAllByRole("link");
    expect(links).toHaveLength(10);
    expect(links[2]).toHaveAccessibleName(/Título 3 v1/);
    expect(links[2]).toHaveAttribute("href", "#capitulo-3");

    const chapter = screen.getByRole("region", { name: /Capítulo 3/ });
    expect(within(chapter).getByText("Texto del capítulo 3 en v1.")).toBeInTheDocument();
    expect(chapter.id).toBe("capitulo-3");

    expect(screen.queryByText(/cambiado en v/i)).not.toBeInTheDocument();
  });

  it("026-C04: the news page links to the changed chapters and the index marks them", async () => {
    fakeApi({
      [`GET ${BASE}`]: () => json(200, { versions: LIST.versions }),
      [`GET ${BASE}/2`]: () => json(200, detail(2)),
    });
    renderReading();

    const news = await screen.findByRole("region", { name: "Novedades" });
    const newsLinks = within(news).getAllByRole("link");
    expect(newsLinks).toHaveLength(2);
    expect(newsLinks[0]).toHaveAttribute("href", "#capitulo-3");
    expect(newsLinks[1]).toHaveAttribute("href", "#capitulo-7");

    const index = screen.getByRole("navigation", { name: "Índice" });
    const indexLinks = within(index).getAllByRole("link");
    const markedLinks = indexLinks.filter((link) => /cambiado en v2/.test(link.textContent ?? ""));
    expect(markedLinks).toHaveLength(2);
    expect(within(index).getByRole("link", { name: /Título 3 v2.*cambiado en v2/s })).toBeInTheDocument();
    expect(within(index).getByRole("link", { name: /Título 7 v2.*cambiado en v2/s })).toBeInTheDocument();
  });

  it("026-C05: without changed chapters, there is no news page", async () => {
    apiAtV1();
    renderReading();

    await screen.findByRole("region", { name: "Portada" });
    expect(screen.queryByRole("region", { name: "Novedades" })).not.toBeInTheDocument();
  });

  it("026-C06: the cast sheet links to each chapter where the entity appears", async () => {
    apiAtV1();
    renderReading();

    const ficha = await screen.findByRole("region", { name: "Ficha" });
    const toby = within(ficha).getByText("Toby").closest("li");
    if (!toby) throw new Error("no se encontró la entrada de Toby");
    const links = within(toby).getAllByRole("link");
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute("href", "#capitulo-2");
    expect(links[1]).toHaveAttribute("href", "#capitulo-5");
  });

  it("026-C07: an entity with no chapters appears in the cast sheet without links", async () => {
    const withoutChapters = detail(1);
    withoutChapters.view.ficha = [{ name: "Faro Viejo", kind: "lugar", chapters: [] }];
    fakeApi({
      [`GET ${BASE}`]: () => json(200, { versions: LIST.versions.slice(0, 1) }),
      [`GET ${BASE}/1`]: () => json(200, withoutChapters),
    });
    renderReading();

    const ficha = await screen.findByRole("region", { name: "Ficha" });
    const entry = within(ficha).getByText("Faro Viejo").closest("li");
    if (!entry) throw new Error("no se encontró la entrada de Faro Viejo");
    expect(within(entry).queryAllByRole("link")).toHaveLength(0);
  });

  it("026-C08: the selector lists the published versions in the order the API gives them", async () => {
    const reversed: VersionsList = { versions: [...LIST.versions].reverse() };
    fakeApi({
      [`GET ${BASE}`]: () => json(200, reversed),
      [`GET ${BASE}/1`]: () => json(200, detail(1)),
      [`GET ${BASE}/2`]: () => json(200, detail(2)),
    });
    renderReading();

    const select = await screen.findByRole("combobox", { name: "Versión" });
    const options = within(select).getAllByRole("option");
    expect(options.map((option) => option.textContent)).toEqual(["v2", "v1"]);
  });

  it("026-C09: switching version reloads all the content with the chosen version's", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET ${BASE}`]: () => json(200, LIST),
      [`GET ${BASE}/1`]: () => json(200, detail(1)),
      [`GET ${BASE}/2`]: () => json(200, detail(2)),
    });
    renderReading();

    await screen.findByRole("region", { name: "Novedades" });
    expect(await screen.findByText("Nala")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: "Versión" }), "1");

    await screen.findByText("Toby");
    expect(screen.queryByText("Nala")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Novedades" })).not.toBeInTheDocument();
    expect(screen.queryByText(/cambiado en v/i)).not.toBeInTheDocument();
  });

  it("026-C10: downloads the PDF of the version being viewed", async () => {
    class FakeUrl extends URL {
      static createObjectURL = vi.fn<(blob: Blob) => string>(() => "blob:mock-url");
      static revokeObjectURL = vi.fn();
    }
    vi.stubGlobal("URL", FakeUrl);
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const pdfBytes = new Blob(["%PDF-1.4 contenido de prueba"], { type: "application/pdf" });
    apiAtV1({
      [`GET ${BASE}/1/pdf`]: () => new Response(pdfBytes, { status: 200, headers: { "Content-Type": "application/pdf" } }),
    });
    renderReading();

    await screen.findByRole("region", { name: "Portada" });
    await user.click(screen.getByRole("button", { name: "Descargar PDF" }));

    await vi.waitFor(() => expect(FakeUrl.createObjectURL).toHaveBeenCalledTimes(1));
    const [blobArg] = FakeUrl.createObjectURL.mock.calls[0] ?? [];
    expect(blobArg?.type).toBe("application/pdf");
    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(FakeUrl.revokeObjectURL).toHaveBeenCalledTimes(1);

    clickSpy.mockRestore();
  });

  it("026-C11: the PDF is not available yet", async () => {
    const user = userEvent.setup();
    apiAtV1({
      [`GET ${BASE}/1/pdf`]: () => new Response(null, { status: 404 }),
    });
    renderReading();

    await screen.findByRole("region", { name: "Portada" });
    await user.click(screen.getByRole("button", { name: "Descargar PDF" }));

    await screen.findByText(/el pdf.*no está disponible/i);
    expect(screen.getByRole("region", { name: "Portada" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Índice" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Ficha" })).toBeInTheDocument();
  });

  it("026-C12: failing to load the versions list shows an error with a retry", async () => {
    const user = userEvent.setup();
    let attempt = 0;
    fakeApi({
      [`GET ${BASE}`]: () => {
        attempt += 1;
        return attempt === 1 ? new Response(null, { status: 500 }) : json(200, LIST);
      },
      [`GET ${BASE}/2`]: () => json(200, detail(2)),
    });
    renderReading();

    await screen.findByText(/no se pudo cargar/i);
    expect(screen.queryByRole("combobox", { name: "Versión" })).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Portada" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /reintentar/i }));

    expect(await screen.findByRole("combobox", { name: "Versión" })).toBeInTheDocument();
    expect(await screen.findByRole("region", { name: "Portada" })).toBeInTheDocument();
  });
});
