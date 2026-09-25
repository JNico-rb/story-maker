import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

// API simulada en el límite del cliente (024-I2), mismo patrón que src/app/novels.test.tsx.
type Reply = () => Response | Promise<Response>;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const NOVEL = 12;
const BASE = `/api/novels/${NOVEL}`;

function emptyBrief(overrides: Record<string, unknown> = {}) {
  return {
    status: "draft",
    content: {
      recipient: { name: "", age: null, birth_date: null, traits: [], relation: null },
      close_ones: [],
      recollections: [],
      occasion: null,
      genre: null,
      tone: null,
      length: null,
      dedication: "",
      banned_asked: false,
      plot_wishes: [],
    },
    missing_fields: [],
    contradictions: [],
    schema_errors: [],
    mandatory_count: 0,
    max_mandatory_elements: 5,
    personal_elements: [],
    verified_facts: [],
    ...overrides,
  };
}

// Por defecto: historial e prohibidas vacías, un brief vacío en borrador; cada caso simula lo que
// necesita encima.
const DEFAULT_REPLIES: Record<string, Reply> = {
  [`GET ${BASE}/interview/messages`]: () => json(200, []),
  [`GET ${BASE}/brief`]: () => json(200, emptyBrief()),
  [`GET ${BASE}/banned-terms`]: () => json(200, []),
};

function fakeApi(replies: Record<string, Reply>): string[] {
  const sent: string[] = [];
  const all = { ...DEFAULT_REPLIES, ...replies };
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const key = `${init?.method ?? "GET"} ${String(input)}`;
      sent.push(key);
      const reply = all[key];
      if (!reply) throw new Error(`ruta no simulada: ${key}`);
      return reply();
    }),
  );
  return sent;
}

function renderEntrevista() {
  const router = createMemoryRouter(buildRoutes(), {
    initialEntries: [`/novelas/${NOVEL}/entrevista`],
  });
  render(<RouterProvider router={router} />);
  return router;
}

beforeEach(() => {
  localStorage.clear();
  saveSession("token-de-prueba");
});

afterEach(() => {
  clearSession();
  vi.unstubAllGlobals();
});

describe("024 entrevista: chat", () => {
  it("024-C01: an empty history offers writing the first message, brief shows nothing fixed yet", async () => {
    fakeApi({});
    renderEntrevista();

    expect(await screen.findByRole("form", { name: "Entrevista" })).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Historial" })).not.toBeInTheDocument();
    expect(screen.getByText(/todavía no hay nada fijado/i)).toBeInTheDocument();
  });

  it("024-C02: sending a message shows it followed by the interviewer's reply", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/interview/messages`]: () =>
        json(200, {
          reply: "¿Cuántos años cumple?",
          brief: emptyBrief(),
        }),
    });
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    await user.type(screen.getByLabelText("Mensaje"), "Se llama Marta y cumple 40");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    const history = await screen.findByRole("list", { name: "Historial" });
    const items = within(history).getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual([
      "Se llama Marta y cumple 40",
      "¿Cuántos años cumple?",
    ]);
  });

  it("024-C03: a failed message keeps it in the field and shows the reason, history unchanged", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/interview/messages`]: () => new Response(null, { status: 503 }),
    });
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    await user.type(screen.getByLabelText("Mensaje"), "Se llama Marta");
    await user.click(screen.getByRole("button", { name: "Enviar" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Historial" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("Mensaje")).toHaveValue("Se llama Marta");
  });

  it("024-C04: an empty or blank message is never sent", async () => {
    const user = userEvent.setup();
    const sent = fakeApi({});
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();
    await user.type(screen.getByLabelText("Mensaje"), "   ");
    expect(screen.getByRole("button", { name: "Enviar" })).toBeDisabled();

    expect(sent).not.toContain(`POST ${BASE}/interview/messages`);
  });
});

describe("024 entrevista: panel del brief", () => {
  it("024-C05: the panel distinguishes what's fixed from what's missing and shows contradictions", async () => {
    fakeApi({
      [`GET ${BASE}/brief`]: () =>
        json(
          200,
          emptyBrief({
            content: {
              recipient: { name: "Marta", age: null, birth_date: null, traits: [], relation: null },
              close_ones: [],
              recollections: [],
              occasion: null,
              genre: null,
              tone: null,
              length: null,
              dedication: "",
              banned_asked: false,
              plot_wishes: [],
            },
            missing_fields: ["age"],
            contradictions: [{ rule: "C1", fields: ["recipient.age", "recipient.birth_date"] }],
          }),
        ),
    });
    renderEntrevista();

    const panel = await screen.findByRole("region", { name: "Brief" });
    expect(within(panel).getByText("Marta")).toBeInTheDocument();
    expect(within(panel).getByText(/falta: age/i)).toBeInTheDocument();
    expect(within(panel).getByText(/contradicción c1/i)).toBeInTheDocument();
  });

  it("024-C06: shows the mandatory cap as the API gives it", async () => {
    fakeApi({
      [`GET ${BASE}/brief`]: () => json(200, emptyBrief({ mandatory_count: 3, max_mandatory_elements: 5 })),
    });
    renderEntrevista();

    const panel = await screen.findByRole("region", { name: "Brief" });
    expect(within(panel).getByText(/3\/5/)).toBeInTheDocument();
  });
});
