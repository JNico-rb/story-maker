import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { buildRoutes } from "./router";

// API simulada en el límite del cliente: cada prueba declara qué responde cada ruta (spec 002).
type Handler = (body: unknown) => { status: number; body?: unknown };
type SentRequest = { url: string; method: string; headers: Headers; body: unknown };

function fakeApi(handlers: Record<string, Handler>) {
  const sent: SentRequest[] = [];
  const fetchFake = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    const body = typeof init?.body === "string" ? (JSON.parse(init.body) as unknown) : undefined;
    sent.push({ url, method, headers: new Headers(init?.headers), body });
    const handler = handlers[`${method} ${url}`];
    if (!handler) throw new Error(`ruta no simulada: ${method} ${url}`);
    const reply = handler(body);
    return new Response(reply.body === undefined ? null : JSON.stringify(reply.body), {
      status: reply.status,
      headers: { "Content-Type": "application/json" },
    });
  });
  vi.stubGlobal("fetch", fetchFake);
  return sent;
}

function renderAt(path: string) {
  const router = createMemoryRouter(buildRoutes(), { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

function storedValues(): string {
  const all = [localStorage, sessionStorage].flatMap((storage) =>
    Object.keys(storage).map((key) => `${key}=${storage.getItem(key) ?? ""}`),
  );
  return all.join("\n");
}

const EMAIL = "persona@example.com";
const PASSWORD = "contrasena-de-prueba";

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("022 registro", () => {
  it("022-C01: a valid registration shows the access screen with a notice and the email already filled, without a session", async () => {
    const sent = fakeApi({
      "POST /api/auth/register": () => ({ status: 201, body: { id: "c1", email: EMAIL } }),
    });
    const user = userEvent.setup();
    renderAt("/registro");

    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByText("Cuenta creada. Ya puedes entrar.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveValue(EMAIL);
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    expect(sent).toHaveLength(1);
    expect(sent[0]?.body).toEqual({ email: EMAIL, password: PASSWORD });
    expect(storedValues()).toBe("");
  });
});
