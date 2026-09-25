import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { components } from "../shared/api/schema";
import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

type VersionDetail = components["schemas"]["VersionDetailResponse"];
type VersionsList = components["schemas"]["VersionsListResponse"];

// API simulada en el límite del cliente (frontend/AGENTS.md), igual que 027 se hizo contra 014:
// specs/backend/019-edicion-manual.md fija la ruta del lint, la del guardado y sus códigos; la
// carga del capítulo reutiliza la ruta real de 026 (`/versions/{version}`), ya generada.
type Reply = () => Response | Promise<Response>;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fakeApi(replies: Record<string, Reply>): Array<{ url: string; body: unknown }> {
  const calls: Array<{ url: string; body: unknown }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const key = `${init?.method ?? "GET"} ${String(input)}`;
      calls.push({ url: key, body: init?.body ? JSON.parse(String(init.body)) : undefined });
      const reply = replies[key];
      if (!reply) throw new Error(`ruta no simulada: ${key}`);
      return reply();
    }),
  );
  return calls;
}

const NOVEL = 7;
const CHAPTER = 3;
const CHAPTER_TEXT = "Toby corría por la playa mientras Marta miraba el mar.";
const EDITOR_PATH = `/novelas/${NOVEL}/versiones/2/capitulos/${CHAPTER}/editar`;
const LINT_DEBOUNCE_MS = 500;

function detail(version: number, chapterText: string = CHAPTER_TEXT): VersionDetail {
  return {
    version,
    view: {
      title: "La casa del faro",
      recipient: "Destinataria de prueba",
      dedication: "Para quien espera la luz.",
      version_number: version,
      chapters: [1, 2, 3].map((n) => ({
        number: n,
        title: `Título ${n}`,
        text: n === CHAPTER ? chapterText : `Texto del capítulo ${n}.`,
      })),
      changed_chapters: [],
      ficha: [],
    },
  };
}

const LIST_TWO: VersionsList = {
  versions: [
    { number: 1, published_at: "2026-09-20T10:00:00Z", changed_chapters: [] },
    { number: 2, published_at: "2026-09-22T10:00:00Z", changed_chapters: [] },
  ],
};

function renderReading() {
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [`/novelas/${NOVEL}/lectura`] });
  render(<RouterProvider router={router} />);
  return router;
}

function renderEditor(initialPath: string = EDITOR_PATH) {
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [initialPath] });
  render(<RouterProvider router={router} />);
  return router;
}

async function loadedTextarea() {
  const textarea = await screen.findByRole("textbox", { name: "Texto del capítulo" });
  await vi.waitFor(() => expect(textarea).toHaveValue(CHAPTER_TEXT));
  return textarea as HTMLTextAreaElement;
}

// `findBy*`/`waitFor` sondean con temporizadores reales: con el reloj controlado (028-C04 y
// siguientes) se vacía la cola de microtareas a mano y se consulta en síncrono.
async function flushMicrotasks() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
}

async function loadedTextareaWithFakeTimers(): Promise<HTMLTextAreaElement> {
  await flushMicrotasks();
  const textarea = screen.getByRole("textbox", { name: "Texto del capítulo" }) as HTMLTextAreaElement;
  expect(textarea).toHaveValue(CHAPTER_TEXT);
  return textarea;
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("028 edición manual", () => {
  it("028-C01: opening the editor from the current version's chapter preloads its text", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions`]: () => json(200, LIST_TWO),
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
    });
    renderReading();

    const chapter = await screen.findByRole("region", { name: /Capítulo 3/ });
    await user.click(within(chapter).getByRole("link", { name: /editar/i }));

    expect(await screen.findByRole("textbox", { name: "Texto del capítulo" })).toHaveValue(CHAPTER_TEXT);
  });

  it("028-C02: a version that is not the current one offers no editor", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions`]: () => json(200, LIST_TWO),
      [`GET /api/novels/${NOVEL}/versions/1`]: () => json(200, detail(1, "Texto v1.")),
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
    });
    renderReading();

    await screen.findByRole("region", { name: /Capítulo 3/ });
    await user.selectOptions(screen.getByRole("combobox", { name: "Versión" }), "1");

    await screen.findByText("Texto v1.");
    expect(screen.queryByRole("link", { name: /editar/i })).not.toBeInTheDocument();
  });

  it("028-C03: a failure loading the chapter can be retried, showing no editor meanwhile", async () => {
    let attempt = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => {
        attempt += 1;
        return attempt === 1 ? new Response(null, { status: 500 }) : json(200, detail(2));
      },
    });
    const user = userEvent.setup();
    renderEditor();

    await screen.findByText(/no se pudo cargar el capítulo/i);
    expect(screen.queryByRole("textbox", { name: "Texto del capítulo" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /reintentar/i }));

    expect(await screen.findByRole("textbox", { name: "Texto del capítulo" })).toHaveValue(CHAPTER_TEXT);
  });

  it("028-C04: diagnostics arrive after a writing pause, not on every keystroke", async () => {
    vi.useFakeTimers();
    const calls = fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`POST /api/novels/${NOVEL}/chapters/${CHAPTER}/lint`]: () => json(200, { diagnostics: [] }),
    });
    renderEditor();
    const textarea = await loadedTextareaWithFakeTimers();

    for (const ch of "abc") {
      fireEvent.change(textarea, { target: { value: textarea.value + ch } });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(200);
      });
    }
    expect(calls.filter((c) => c.url.endsWith("/lint"))).toHaveLength(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    const lintCalls = calls.filter((c) => c.url.endsWith("/lint"));
    expect(lintCalls).toHaveLength(1);
    expect(lintCalls[0]?.body).toEqual({ text: `${CHAPTER_TEXT}abc` });
  });

  it("028-C05: a positioned blocking diagnostic highlights its fragment and shows its message", async () => {
    vi.useFakeTimers();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`POST /api/novels/${NOVEL}/chapters/${CHAPTER}/lint`]: () =>
        json(200, {
          diagnostics: [
            {
              type: "forma_no_canonica",
              message: "forma no canónica: usa «Toby»",
              position: { start: 0, end: 4 },
              blocking: true,
            },
          ],
        }),
    });
    renderEditor();
    await loadedTextareaWithFakeTimers();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });

    const list = screen.getByRole("list", { name: "Avisos en el texto" });
    expect(within(list).getByText("Toby")).toBeInTheDocument();
    expect(within(list).getByText(/forma no canónica/)).toBeInTheDocument();
    expect(within(list).getByText(/bloqueará el guardado/)).toBeInTheDocument();
  });

  it("028-C06: a diagnostic with no position is shown apart from the text", async () => {
    vi.useFakeTimers();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`POST /api/novels/${NOVEL}/chapters/${CHAPTER}/lint`]: () =>
        json(200, { diagnostics: [{ type: "hecho", message: "el hecho «Toby» ya no aparece", blocking: false }] }),
    });
    renderEditor();
    await loadedTextareaWithFakeTimers();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });

    const list = screen.getByRole("list", { name: "Otros avisos" });
    expect(within(list).getByText(/el hecho «Toby» ya no aparece/)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Avisos en el texto" })).not.toBeInTheDocument();
  });

  it("028-C07: blocking and non-blocking diagnostics are told apart", async () => {
    vi.useFakeTimers();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`POST /api/novels/${NOVEL}/chapters/${CHAPTER}/lint`]: () =>
        json(200, {
          diagnostics: [
            { type: "linter", message: "repite mucho «mar»", blocking: false },
            { type: "prohibida", message: "«Jorge» está prohibida", blocking: true },
          ],
        }),
    });
    renderEditor();
    await loadedTextareaWithFakeTimers();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });

    const list = screen.getByRole("list", { name: "Otros avisos" });
    const items = within(list).getAllByRole("listitem");
    expect(items[0]).toHaveTextContent("repite mucho «mar»");
    expect(items[0]).not.toHaveTextContent("bloqueará el guardado");
    expect(items[1]).toHaveTextContent("«Jorge» está prohibida");
    expect(items[1]).toHaveTextContent("bloqueará el guardado");
  });

  it("028-C08: the last lint request sent wins, even if an earlier one answers later", async () => {
    vi.useFakeTimers();
    let resolveFirst: (response: Response) => void = () => undefined;
    let lintCall = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const key = `${init?.method ?? "GET"} ${String(input)}`;
        if (key === `GET /api/novels/${NOVEL}/versions/2`) return json(200, detail(2));
        if (key.endsWith("/lint")) {
          lintCall += 1;
          if (lintCall === 1) return new Promise<Response>((resolve) => (resolveFirst = resolve));
          return json(200, { diagnostics: [{ type: "linter", message: "B", blocking: false }] });
        }
        throw new Error(`ruta no simulada: ${key}`);
      }),
    );
    renderEditor();
    const textarea = await loadedTextareaWithFakeTimers();

    fireEvent.change(textarea, { target: { value: "texto A" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });
    fireEvent.change(textarea, { target: { value: "texto B" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });

    expect(screen.getByText("B")).toBeInTheDocument();

    resolveFirst(json(200, { diagnostics: [{ type: "linter", message: "A", blocking: false }] }));
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(screen.getByText("B")).toBeInTheDocument();
    expect(screen.queryByText("A")).not.toBeInTheDocument();
  });

  it("028-C09: a lint failure keeps prior diagnostics and lets editing and saving continue", async () => {
    vi.useFakeTimers();
    let lintCall = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const key = `${init?.method ?? "GET"} ${String(input)}`;
        if (key === `GET /api/novels/${NOVEL}/versions/2`) return json(200, detail(2));
        if (key.endsWith("/lint")) {
          lintCall += 1;
          if (lintCall === 1) return json(200, { diagnostics: [{ type: "linter", message: "aviso previo", blocking: false }] });
          return new Response(null, { status: 500 });
        }
        throw new Error(`ruta no simulada: ${key}`);
      }),
    );
    renderEditor();
    const textarea = await loadedTextareaWithFakeTimers();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });
    expect(screen.getByText("aviso previo")).toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: `${CHAPTER_TEXT} más` } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });

    expect(screen.getByText(/no se pudo comprobar el texto/i)).toBeInTheDocument();
    expect(screen.getByText("aviso previo")).toBeInTheDocument();
    expect(textarea).toHaveValue(`${CHAPTER_TEXT} más`);
    expect(screen.getByRole("button", { name: "Guardar" })).toBeEnabled();
  });

  it("028-C10: no diagnostic blocks writing in the editor", async () => {
    vi.useFakeTimers();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`POST /api/novels/${NOVEL}/chapters/${CHAPTER}/lint`]: () =>
        json(200, {
          diagnostics: [{ type: "prohibida", message: "bloqueante", position: { start: 0, end: 4 }, blocking: true }],
        }),
    });
    renderEditor();
    const textarea = await loadedTextareaWithFakeTimers();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(LINT_DEBOUNCE_MS);
    });
    expect(screen.getByText(/bloqueará el guardado/)).toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: "texto nuevo sin restricción" } });

    expect(textarea).toHaveValue("texto nuevo sin restricción");
    expect(textarea).not.toBeDisabled();
  });

  it("028-C11: an accepted save sends exactly the edited text and navigates to the progress screen", async () => {
    const user = userEvent.setup();
    const calls = fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`PUT /api/novels/${NOVEL}/chapters/${CHAPTER}`]: () => json(202, { run_id: "run-1" }),
    });
    const router = renderEditor();
    const textarea = await loadedTextarea();
    await user.clear(textarea);
    await user.type(textarea, "texto final editado");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await vi.waitFor(() => expect(router.state.location.pathname).toBe(`/novelas/${NOVEL}/progreso`));
    const put = calls.find((c) => c.url.startsWith("PUT"));
    expect(put?.body).toEqual({ text: "texto final editado", base_version: 2 });
  });

  it("028-C12: a save rejected by blocking diagnostics shows them next to the editor, keeping the text", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`PUT /api/novels/${NOVEL}/chapters/${CHAPTER}`]: () =>
        json(422, {
          detail: {
            diagnostics: [
              {
                type: "forma_no_canonica",
                message: "«Tobi» no es canónico",
                position: { start: 0, end: 4 },
                blocking: true,
              },
            ],
          },
        }),
    });
    renderEditor();
    const textarea = await loadedTextarea();
    await user.clear(textarea);
    await user.type(textarea, "Tobi corría.");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText(/«Tobi» no es canónico/)).toBeInTheDocument();
    expect(textarea).toHaveValue("Tobi corría.");
  });

  it("028-C13: saving against a stale base offers reloading the now-current chapter", async () => {
    const user = userEvent.setup();
    const LIST_THREE: VersionsList = {
      versions: [
        { number: 1, published_at: "2026-09-20T10:00:00Z", changed_chapters: [] },
        { number: 2, published_at: "2026-09-22T10:00:00Z", changed_chapters: [] },
        { number: 3, published_at: "2026-09-24T10:00:00Z", changed_chapters: [3] },
      ],
    };
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`PUT /api/novels/${NOVEL}/chapters/${CHAPTER}`]: () => json(409, { detail: "stale_base" }),
      [`GET /api/novels/${NOVEL}/versions`]: () => json(200, LIST_THREE),
      [`GET /api/novels/${NOVEL}/versions/3`]: () => json(200, detail(3, "Texto nuevo publicado.")),
    });
    renderEditor();
    const textarea = await loadedTextarea();
    await user.clear(textarea);
    await user.type(textarea, "mi edición en curso");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText(/versión más nueva/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /recargar/i }));

    await vi.waitFor(() =>
      expect(screen.getByRole("textbox", { name: "Texto del capítulo" })).toHaveValue("Texto nuevo publicado."),
    );
  });

  it("028-C14: a network failure while saving keeps the text and allows a retry", async () => {
    const user = userEvent.setup();
    let attempt = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}/versions/2`]: () => json(200, detail(2)),
      [`PUT /api/novels/${NOVEL}/chapters/${CHAPTER}`]: () => {
        attempt += 1;
        return attempt === 1 ? new Response(null, { status: 500 }) : json(202, { run_id: "run-2" });
      },
    });
    const router = renderEditor();
    const textarea = await loadedTextarea();
    await user.clear(textarea);
    await user.type(textarea, "texto que se intenta guardar");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByText(/no se pudo/i)).toBeInTheDocument();
    expect(textarea).toHaveValue("texto que se intenta guardar");

    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await vi.waitFor(() => expect(router.state.location.pathname).toBe(`/novelas/${NOVEL}/progreso`));
  });
});
