import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, readSession } from "../shared/lib";
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

function expectNoSession() {
  expect(readSession()).toBeNull();
  expect(storedValues()).toBe("");
}

// Cuerpo 422 de FastAPI: `loc` señala el campo que no tiene forma válida.
function invalid(field: "email" | "password") {
  return { detail: [{ type: "value_error", loc: ["body", field], msg: "no válido" }] };
}

const EMAIL = "persona@example.com";
const PASSWORD = "contrasena-de-prueba";
const TOKEN = "token-de-prueba";

beforeEach(() => {
  clearSession();
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
    expectNoSession();
  });

  it("022-C02: an email that already has an account keeps the registration form, says so next to the email and clears the password", async () => {
    fakeApi({ "POST /api/auth/register": () => ({ status: 409, body: { detail: "conflicto" } }) });
    const user = userEvent.setup();
    renderAt("/registro");

    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByLabelText("Email")).toHaveAccessibleDescription(
      "Ese email ya tiene cuenta.",
    );
    expect(screen.getByRole("heading", { name: "Crear cuenta" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveValue(EMAIL);
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    expectNoSession();
  });

  it("022-C03: an invalid registration shows the message next to the field the API pointed at, keeps the email, clears the password and can be resent", async () => {
    let attempts = 0;
    const sent = fakeApi({
      "POST /api/auth/register": () => {
        attempts += 1;
        return attempts === 1
          ? { status: 422, body: invalid("email") }
          : { status: 201, body: { id: "c1", email: EMAIL } };
      },
    });
    const user = userEvent.setup();
    renderAt("/registro");

    await user.type(screen.getByLabelText("Email"), "persona.example.com");
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByLabelText("Email")).toHaveAccessibleDescription(
      "Revisa el email: no tiene forma de email.",
    );
    expect(screen.getByLabelText("Email")).toHaveValue("persona.example.com");
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    expect(screen.getByLabelText("Contraseña")).not.toHaveAccessibleDescription();

    await user.clear(screen.getByLabelText("Email"));
    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expect(sent).toHaveLength(2);
  });

  it("022-C03: a password out of its limits is pointed at next to the password, and the email is kept", async () => {
    fakeApi({ "POST /api/auth/register": () => ({ status: 422, body: invalid("password") }) });
    const user = userEvent.setup();
    renderAt("/registro");

    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), "corta");
    await user.click(screen.getByRole("button", { name: "Crear cuenta" }));

    expect(await screen.findByLabelText("Contraseña")).toHaveAccessibleDescription(
      "La contraseña debe tener entre 8 caracteres y 72 bytes.",
    );
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    expect(screen.getByLabelText("Email")).toHaveValue(EMAIL);
    expect(screen.getByLabelText("Email")).not.toHaveAccessibleDescription();
  });
});

describe("022 acceso", () => {
  it("022-C03: an invalid login shows the message next to the field the API pointed at, keeps the email, clears the password and can be resent", async () => {
    const sent = fakeApi({ "POST /api/auth/login": () => ({ status: 422, body: invalid("password") }) });
    const user = userEvent.setup();
    renderAt("/acceso");

    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByLabelText("Contraseña")).toHaveAccessibleDescription(
      "Revisa la contraseña.",
    );
    expect(screen.getByLabelText("Email")).toHaveValue(EMAIL);
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");

    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    await vi.waitFor(() => expect(sent).toHaveLength(2));
    expectNoSession();
  });

  it("022-C04: a valid login stores the session with the token and leaves the access screen for the main screen", async () => {
    const sent = fakeApi({
      "POST /api/auth/login": () => ({ status: 200, body: { access_token: TOKEN } }),
    });
    const user = userEvent.setup();
    const router = renderAt("/acceso");

    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    await vi.waitFor(() => expect(router.state.location.pathname).toBe("/"));
    expect(screen.queryByRole("heading", { name: "Entrar" })).not.toBeInTheDocument();
    expect(readSession()).toBe(TOKEN);
    expect(sent[0]?.body).toEqual({ email: EMAIL, password: PASSWORD });
  });
});
