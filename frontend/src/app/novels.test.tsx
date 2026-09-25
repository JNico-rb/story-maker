import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

// API simulada en el límite del cliente (023-I3), mismo patrón que src/app/reading.test.tsx.
type Reply = () => Response | Promise<Response>;

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

function renderNovels() {
  const router = createMemoryRouter(buildRoutes(), { initialEntries: ["/"] });
  render(<RouterProvider router={router} />);
  return router;
}

function novel(overrides: Partial<{
  id: number;
  title: string;
  recipient_name: string;
  status: "interview" | "ready" | "in_progress" | "published";
  current_version: number | null;
  created_at: string;
}> = {}) {
  return {
    id: 1,
    title: "La casa del faro",
    recipient_name: "Ana",
    status: "published" as const,
    current_version: 2,
    created_at: "2026-09-20T10:00:00Z",
    ...overrides,
  };
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});

describe("023 mis novelas", () => {
  it("023-C01: an empty list shows that there are no novels yet, without a table", async () => {
    fakeApi({ "GET /api/novels": () => json(200, []) });
    renderNovels();

    expect(await screen.findByText(/aún no tienes ninguna novela/i)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Novelas" })).not.toBeInTheDocument();
  });

  it("023-C02: each derived status has its own label", async () => {
    fakeApi({
      "GET /api/novels": () =>
        json(200, [
          novel({ id: 1, status: "interview" }),
          novel({ id: 2, status: "ready", current_version: null }),
          novel({ id: 3, status: "in_progress", current_version: null }),
          novel({ id: 4, status: "published" }),
        ]),
    });
    renderNovels();

    const list = await screen.findByRole("list", { name: "Novelas" });
    expect(within(list).getByText("En entrevista")).toBeInTheDocument();
    expect(within(list).getByText("Lista para escribir")).toBeInTheDocument();
    expect(within(list).getByText("Escribiéndose")).toBeInTheDocument();
    expect(within(list).getByText("Publicada")).toBeInTheDocument();
    expect(within(list).queryByText(/desconocid/i)).not.toBeInTheDocument();
  });

  it("023-C03: a current version shows its number; without one, no version number is shown", async () => {
    fakeApi({
      "GET /api/novels": () =>
        json(200, [
          novel({ id: 1, status: "published", current_version: 2 }),
          novel({ id: 2, status: "ready", current_version: null }),
        ]),
    });
    renderNovels();

    const [first, second] = await screen.findAllByRole("listitem");
    if (!first || !second) throw new Error("no se encontraron las dos filas");
    expect(within(first).getByText("v2")).toBeInTheDocument();
    expect(within(second).queryByText(/^v\d+$/)).not.toBeInTheDocument();
  });

  it("023-C04: a novel with no title yet shows a placeholder instead of a blank", async () => {
    fakeApi({ "GET /api/novels": () => json(200, [novel({ title: "" })]) });
    renderNovels();

    expect(await screen.findByText("Sin título todavía")).toBeInTheDocument();
  });

  it("023-C05: the list keeps the order the API gives it", async () => {
    fakeApi({
      "GET /api/novels": () =>
        json(200, [
          novel({ id: 1, title: "Tercera", created_at: "2026-09-18T10:00:00Z" }),
          novel({ id: 2, title: "Primera", created_at: "2026-09-24T10:00:00Z" }),
          novel({ id: 3, title: "Segunda", created_at: "2026-09-20T10:00:00Z" }),
        ]),
    });
    renderNovels();

    const rows = await screen.findAllByRole("listitem");
    expect(rows.map((row) => row.textContent?.includes("Tercera") ? "Tercera" : row.textContent?.includes("Primera") ? "Primera" : "Segunda")).toEqual([
      "Tercera",
      "Primera",
      "Segunda",
    ]);
  });

  it("023-C06: failing to load the list shows an error with a retry, never an empty list", async () => {
    const user = userEvent.setup();
    let attempt = 0;
    fakeApi({
      "GET /api/novels": () => {
        attempt += 1;
        return attempt === 1 ? new Response(null, { status: 500 }) : json(200, [novel()]);
      },
    });
    renderNovels();

    expect(await screen.findByRole("alert")).toHaveTextContent(/no se pudo cargar/i);
    expect(screen.queryByText(/aún no tienes ninguna novela/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Novelas" })).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /reintentar/i }));

    expect(await screen.findByRole("list", { name: "Novelas" })).toBeInTheDocument();
  });

  it("023-C09: the destination depends on the status and the current version", async () => {
    fakeApi({
      "GET /api/novels": () =>
        json(200, [
          novel({ id: 5, status: "published", current_version: 3 }),
          novel({ id: 6, status: "interview", current_version: null }),
          novel({ id: 7, status: "ready", current_version: null }),
          novel({ id: 8, status: "in_progress", current_version: null }),
        ]),
    });
    renderNovels();

    const [withVersion, interview, ready, inProgress] = await screen.findAllByRole("listitem");
    if (!withVersion || !interview || !ready || !inProgress) {
      throw new Error("no se encontraron las cuatro filas");
    }
    expect(within(withVersion).getByRole("link")).toHaveAttribute("href", "/novelas/5/lectura");
    expect(within(interview).getByRole("link")).toHaveAttribute("href", "/novelas/6/entrevista");
    expect(within(ready).getByRole("link")).toHaveAttribute("href", "/novelas/7/entrevista");
    expect(within(inProgress).getByRole("link")).toHaveAttribute("href", "/novelas/8/progreso");
  });

  it("023-C07: creating a novel navigates to its interview", async () => {
    const user = userEvent.setup();
    let resolvePost!: (response: Response) => void;
    fakeApi({
      "GET /api/novels": () => json(200, []),
      "POST /api/novels": () => new Promise<Response>((resolve) => (resolvePost = resolve)),
    });
    const router = renderNovels();

    const button = await screen.findByRole("button", { name: "Crear novela" });
    await user.click(button);

    expect(button).toBeDisabled();
    resolvePost(json(201, novel({ id: 42, status: "interview", current_version: null })));

    await vi.waitFor(() => expect(router.state.location.pathname).toBe("/novelas/42/entrevista"));
  });

  it("023-C08: a failure creating a novel stays on \"mis novelas\" and re-enables the button", async () => {
    const user = userEvent.setup();
    fakeApi({
      "GET /api/novels": () => json(200, []),
      "POST /api/novels": () => new Response(null, { status: 503 }),
    });
    const router = renderNovels();

    const button = await screen.findByRole("button", { name: "Crear novela" });
    await user.click(button);

    expect(await screen.findByRole("alert")).toHaveTextContent(/no se pudo completar/i);
    expect(router.state.location.pathname).toBe("/");
    expect(screen.getByRole("button", { name: "Crear novela" })).not.toBeDisabled();
  });

  it("023-C17: a valid access ends up on \"mis novelas\" with the list", async () => {
    fakeApi({
      "POST /api/auth/login": () => json(200, { access_token: "token-de-prueba" }),
      "GET /api/novels": () => json(200, [novel({ id: 9, title: "Historia de Ana" })]),
    });
    const user = userEvent.setup();
    const router = createMemoryRouter(buildRoutes(), { initialEntries: ["/acceso"] });
    render(<RouterProvider router={router} />);

    await user.type(screen.getByLabelText("Email"), "persona@example.com");
    await user.type(screen.getByLabelText("Contraseña"), "contrasena-de-prueba");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("heading", { name: "Mis novelas" })).toBeInTheDocument();
    expect(await screen.findByText("Historia de Ana")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });
});
