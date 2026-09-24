import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect, useState } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "../shared/api";
import { clearSession, readSession, saveSession } from "../shared/lib";
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

// Pantalla protegida de prueba: al abrirse pide dos datos a la API con el cliente compartido.
function ProbeScreen() {
  const [loaded, setLoaded] = useState(false);
  useEffect(() => {
    void Promise.all([apiFetch("/api/novels"), apiFetch("/api/banned-terms")]).then(() =>
      setLoaded(true),
    );
  }, []);
  return <p>{loaded ? "datos cargados" : "cargando"}</p>;
}

const probeRoutes = [
  { path: "/sonda", element: <ProbeScreen /> },
  { path: "/otra-sonda", element: <ProbeScreen /> },
];

function renderAt(path: string) {
  const router = createMemoryRouter(buildRoutes(probeRoutes), { initialEntries: [path] });
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

    expect(await screen.findByRole("button", { name: "Cerrar sesión" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
    expect(screen.queryByRole("heading", { name: "Entrar" })).not.toBeInTheDocument();
    expect(readSession()).toBe(TOKEN);
    expect(sent[0]?.body).toEqual({ email: EMAIL, password: PASSWORD });
  });

  it.each([
    ["an unknown email", "desconocida@example.com"],
    ["a registered email with a wrong password", EMAIL],
  ])(
    "022-C05: wrong credentials (%s) keep the access form with one generic message, clear the password and store no session",
    async (_case, email) => {
      fakeApi({
        "POST /api/auth/login": () => ({ status: 401, body: { detail: "Credenciales incorrectas" } }),
      });
      const user = userEvent.setup();
      const router = renderAt("/acceso");

      await user.type(screen.getByLabelText("Email"), email);
      await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
      await user.click(screen.getByRole("button", { name: "Entrar" }));

      expect(await screen.findByRole("alert")).toHaveTextContent("Email o contraseña incorrectos.");
      expect(router.state.location.pathname).toBe("/acceso");
      expect(screen.getByLabelText("Email")).toHaveValue(email);
      expect(screen.getByLabelText("Contraseña")).toHaveValue("");
      expectNoSession();
    },
  );
});

describe("022 rutas protegidas", () => {
  const protectedData = {
    "GET /api/novels": () => ({ status: 200, body: [] }),
    "GET /api/banned-terms": () => ({ status: 200, body: [] }),
  };

  it("022-C06: every request of a protected screen carries the stored session in the authorization header, never in the address", async () => {
    saveSession(TOKEN);
    const sent = fakeApi(protectedData);
    renderAt("/sonda");

    expect(await screen.findByText("datos cargados")).toBeInTheDocument();
    expect(sent.map((request) => request.url)).toEqual(["/api/novels", "/api/banned-terms"]);
    for (const request of sent) {
      expect(request.headers.get("Authorization")).toBe(`Bearer ${TOKEN}`);
      expect(request.url).not.toContain(TOKEN);
    }
  });

  it("022-C07: without a stored session, opening a protected screen shows the access screen without asking the API", async () => {
    const sent = fakeApi(protectedData);
    const router = renderAt("/sonda");

    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/acceso");
    expect(sent).toEqual([]);
  });

  it("022-C08: a session the server rejects is cleared and leads to the access screen; a later protected screen no longer sends that token", async () => {
    saveSession(TOKEN);
    const sent = fakeApi({
      "GET /api/novels": () => ({ status: 401, body: { detail: "No autenticado" } }),
      "GET /api/banned-terms": () => ({ status: 200, body: [] }),
    });
    const router = renderAt("/sonda");

    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expectNoSession();

    const before = sent.length;
    await router.navigate("/otra-sonda");

    await vi.waitFor(() => expect(router.state.location.pathname).toBe("/acceso"));
    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    const later = sent.slice(before);
    expect(later.filter((request) => request.headers.get("Authorization")?.includes(TOKEN))).toEqual([]);
  });
});

describe("022 cierre de sesión", () => {
  it("022-C09: logging out from the main screen clears the stored session and shows the access screen without calling the API", async () => {
    saveSession(TOKEN);
    const sent = fakeApi({});
    const user = userEvent.setup();
    const router = renderAt("/");

    await user.click(await screen.findByRole("button", { name: "Cerrar sesión" }));

    await vi.waitFor(() => expect(router.state.location.pathname).toBe("/acceso"));
    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expectNoSession();
    expect(sent).toEqual([]);
  });
});

describe("022 invariantes", () => {
  async function logIn(user: ReturnType<typeof userEvent.setup>) {
    await user.type(screen.getByLabelText("Email"), EMAIL);
    await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findByRole("button", { name: "Cerrar sesión" });
  }

  it("022-I1: after logging in, the token travels only in the authorization header: never in an address or a cookie", async () => {
    const sent = fakeApi({
      "POST /api/auth/login": () => ({ status: 200, body: { access_token: TOKEN } }),
      "GET /api/novels": () => ({ status: 200, body: [] }),
      "GET /api/banned-terms": () => ({ status: 200, body: [] }),
    });
    const user = userEvent.setup();
    const router = renderAt("/acceso");

    await logIn(user);
    await router.navigate("/sonda");
    expect(await screen.findByText("datos cargados")).toBeInTheDocument();

    const protectedRequests = sent.filter((request) => !request.url.startsWith("/api/auth/"));
    expect(protectedRequests).toHaveLength(2);
    for (const request of protectedRequests) {
      expect(request.headers.get("Authorization")).toBe(`Bearer ${TOKEN}`);
    }
    expect(sent.filter((request) => request.url.includes(TOKEN))).toEqual([]);
    expect(router.state.location.pathname + router.state.location.search).not.toContain(TOKEN);
    expect(document.cookie).not.toContain(TOKEN);
  });

  const register = { path: "/registro", button: "Crear cuenta", route: "POST /api/auth/register" };
  const login = { path: "/acceso", button: "Entrar", route: "POST /api/auth/login" };

  it.each([
    { form: register, status: 201, body: { id: "c1", email: EMAIL } },
    { form: register, status: 409, body: { detail: "conflicto" } },
    { form: register, status: 422, body: invalid("password") },
    { form: login, status: 200, body: { access_token: TOKEN } },
    { form: login, status: 401, body: { detail: "Credenciales incorrectas" } },
    { form: login, status: 422, body: invalid("email") },
  ])(
    "022-I2: after $form.path answers $status, the password is neither stored nor shown anywhere",
    async ({ form, status, body }) => {
      fakeApi({ [form.route]: () => ({ status, body }) });
      const user = userEvent.setup();
      renderAt(form.path);

      await user.type(screen.getByLabelText("Email"), EMAIL);
      await user.type(screen.getByLabelText("Contraseña"), PASSWORD);
      await user.click(screen.getByRole("button", { name: form.button }));

      await vi.waitFor(() => {
        const fieldValues = [...document.querySelectorAll("input")].map((input) => input.value);
        expect(fieldValues).not.toContain(PASSWORD);
      });
      expect(document.body.innerHTML).not.toContain(PASSWORD);
      expect(storedValues()).not.toContain(PASSWORD);
      expect(document.cookie).not.toContain(PASSWORD);
    },
  );

  it("022-I3: a stored session survives reloading the page, and protected requests keep carrying it", async () => {
    const sent = fakeApi({
      "POST /api/auth/login": () => ({ status: 200, body: { access_token: TOKEN } }),
      "GET /api/novels": () => ({ status: 200, body: [] }),
      "GET /api/banned-terms": () => ({ status: 200, body: [] }),
    });
    const user = userEvent.setup();
    renderAt("/acceso");
    await logIn(user);

    // Recarga: se desmonta la app y se vuelven a cargar sus módulos, sin memoria del proceso.
    cleanup();
    vi.resetModules();
    const fresh = await import("./router");
    const freshApi = await import("../shared/api");
    function FreshProbe() {
      const [loaded, setLoaded] = useState(false);
      useEffect(() => {
        void freshApi.apiFetch("/api/novels").then(() => setLoaded(true));
      }, []);
      return <p>{loaded ? "datos cargados" : "cargando"}</p>;
    }
    const router = createMemoryRouter(fresh.buildRoutes([{ path: "/sonda", element: <FreshProbe /> }]), {
      initialEntries: ["/sonda"],
    });
    render(<RouterProvider router={router} />);

    expect(await screen.findByText("datos cargados")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/sonda");
    expect(sent.at(-1)?.headers.get("Authorization")).toBe(`Bearer ${TOKEN}`);
  }, 15_000);
});
