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

function verifiedFact(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    subject: "Marta",
    attribute: "age",
    value: "40",
    quote: "cumple 40",
    accepted: null,
    mandatory: false,
    ...overrides,
  };
}

describe("024 entrevista: texto libre y hechos extraídos", () => {
  it("024-C07: sending a free text shows its verified facts, and clears the field", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/free-texts`]: () =>
        json(201, { free_text_id: 1, verified_facts: [verifiedFact()] }),
    });
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    await user.type(screen.getByLabelText("Texto libre"), "Cumple 40 años");
    await user.click(screen.getByRole("button", { name: "Enviar texto" }));

    const facts = await screen.findByRole("list", { name: "Hechos" });
    expect(within(facts).getByText(/Marta/)).toBeInTheDocument();
    expect(within(facts).getByText(/age/)).toBeInTheDocument();
    expect(within(facts).getByText(/40/)).toBeInTheDocument();
    expect(screen.getByLabelText("Texto libre")).toHaveValue("");
  });

  it("024-C08: accepting and rejecting a fact updates it without a full reload", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/free-texts`]: () =>
        json(201, {
          free_text_id: 1,
          verified_facts: [verifiedFact({ id: 1 }), verifiedFact({ id: 2, attribute: "name", value: "Marta" })],
        }),
      [`PATCH ${BASE}/brief/extracted-facts/1`]: () =>
        json(200, emptyBrief({ verified_facts: [verifiedFact({ id: 1, accepted: true }), verifiedFact({ id: 2, attribute: "name", value: "Marta" })] })),
      [`PATCH ${BASE}/brief/extracted-facts/2`]: () =>
        json(200, emptyBrief({ verified_facts: [verifiedFact({ id: 1, accepted: true }), verifiedFact({ id: 2, attribute: "name", value: "Marta", accepted: false })] })),
    });
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });
    await user.type(screen.getByLabelText("Texto libre"), "Cumple 40 y se llama Marta");
    await user.click(screen.getByRole("button", { name: "Enviar texto" }));
    const facts = await screen.findByRole("list", { name: "Hechos" });
    const [first, second] = within(facts).getAllByRole("listitem");
    if (!first || !second) throw new Error("no se encontraron los dos hechos");

    await user.click(within(first).getByRole("button", { name: "Aceptar" }));
    expect(await within(first).findByText("Aceptado")).toBeInTheDocument();
    expect(within(first).queryByRole("button", { name: "Aceptar" })).not.toBeInTheDocument();

    await user.click(within(second).getByRole("button", { name: "Rechazar" }));
    expect(await within(second).findByText("Rechazado")).toBeInTheDocument();
    expect(within(second).queryByRole("button", { name: "Rechazar" })).not.toBeInTheDocument();
  });

  it("024-C09: marking an accepted fact mandatory works; on an unaccepted one it's rejected", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET ${BASE}/brief`]: () =>
        json(
          200,
          emptyBrief({
            verified_facts: [
              verifiedFact({ id: 1, accepted: true }),
              verifiedFact({ id: 2, attribute: "name", value: "Marta" }),
            ],
          }),
        ),
      [`PATCH ${BASE}/brief/extracted-facts/1`]: () =>
        json(200, emptyBrief({ verified_facts: [verifiedFact({ id: 1, accepted: true, mandatory: true }), verifiedFact({ id: 2, attribute: "name", value: "Marta" })] })),
      [`PATCH ${BASE}/brief/extracted-facts/2`]: () =>
        json(422, { detail: [{ loc: ["body", "mandatory"], msg: "un hecho sin aceptar no puede ser obligatorio", type: "value_error" }] }),
    });
    renderEntrevista();
    const facts = await screen.findByRole("list", { name: "Hechos" });
    const [first, second] = within(facts).getAllByRole("listitem");
    if (!first || !second) throw new Error("no se encontraron los dos hechos");

    await user.click(within(first).getByLabelText("Obligatorio"));
    expect(await within(first).findByLabelText("Obligatorio")).toBeChecked();

    await user.click(within(second).getByLabelText("Obligatorio"));
    expect(await within(second).findByRole("alert")).toHaveTextContent(/no puede ser obligatorio/i);
  });

  it("024-C10: a failed free text shows the reason, keeps the text, adds no fact", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/free-texts`]: () => new Response(null, { status: 503 }),
    });
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    await user.type(screen.getByLabelText("Texto libre"), "Cumple 40 años");
    await user.click(screen.getByRole("button", { name: "Enviar texto" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByLabelText("Texto libre")).toHaveValue("Cumple 40 años");
    expect(screen.queryByRole("list", { name: "Hechos" })).not.toBeInTheDocument();
  });

  it("024-C11: an empty or blank free text is never sent", async () => {
    const user = userEvent.setup();
    fakeApi({});
    renderEntrevista();
    await screen.findByRole("form", { name: "Entrevista" });

    expect(screen.getByRole("button", { name: "Enviar texto" })).toBeDisabled();
    await user.type(screen.getByLabelText("Texto libre"), "   ");
    expect(screen.getByRole("button", { name: "Enviar texto" })).toBeDisabled();
  });
});

function novelBannedTerm(overrides: Record<string, unknown> = {}) {
  return {
    id: 1,
    term: "Cristina",
    type: "word" as const,
    level: "novel" as const,
    keywords: [] as string[],
    normalized: "cristina",
    ...overrides,
  };
}

describe("024 entrevista: lista prohibida de nivel novel", () => {
  it("024-C12: shows the banned list, words and topics with their keywords", async () => {
    fakeApi({
      [`GET ${BASE}/banned-terms`]: () =>
        json(200, [
          novelBannedTerm({ id: 1, term: "Cristina" }),
          novelBannedTerm({ id: 2, term: "divorcio", type: "topic", keywords: ["separación", "custodia"] }),
        ]),
    });
    renderEntrevista();

    const list = await screen.findByRole("list", { name: "Prohibidas" });
    expect(within(list).getByText("Cristina")).toBeInTheDocument();
    expect(within(list).getByText("divorcio")).toBeInTheDocument();
    expect(within(list).getByText(/separación/)).toBeInTheDocument();
  });

  it("024-C13: adding a word or a topic shows up in the list right away", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/banned-terms`]: () => json(201, novelBannedTerm({ id: 5, term: "Cristina" })),
    });
    renderEntrevista();
    await screen.findByRole("list", { name: "Prohibidas" });

    await user.type(screen.getByLabelText("Término"), "Cristina");
    await user.click(screen.getByRole("button", { name: "Añadir" }));

    expect(await screen.findByText("Cristina")).toBeInTheDocument();
    expect(screen.getByLabelText("Término")).toHaveValue("");
  });

  it("024-C14: a rejected or repeated entry adds nothing and shows the reason", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/banned-terms`]: () => new Response(null, { status: 409 }),
    });
    renderEntrevista();
    await screen.findByRole("list", { name: "Prohibidas" });

    await user.type(screen.getByLabelText("Término"), "pedro");
    await user.click(screen.getByRole("button", { name: "Añadir" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/ya está en la lista/i);
  });

  it("024-C15: deleting an entry, including one the interviewer registered, removes it right away", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET ${BASE}/banned-terms`]: () => json(200, [novelBannedTerm({ id: 7, term: "Cristina" })]),
      [`DELETE ${BASE}/banned-terms/7`]: () => new Response(null, { status: 204 }),
    });
    renderEntrevista();

    await screen.findByText("Cristina");
    await user.click(screen.getByRole("button", { name: "Borrar Cristina" }));

    await vi.waitFor(() => expect(screen.queryByText("Cristina")).not.toBeInTheDocument());
  });
});

describe("024 entrevista: confirmación del brief", () => {
  it("024-C16: confirming is only available without problems", async () => {
    fakeApi({
      [`GET ${BASE}/brief`]: () => json(200, emptyBrief({ missing_fields: ["age"] })),
    });
    renderEntrevista();

    expect(await screen.findByRole("button", { name: "Confirmar" })).toBeDisabled();
  });

  it("024-C16b: confirming is available with no missing fields or contradictions", async () => {
    fakeApi({});
    renderEntrevista();

    expect(await screen.findByRole("button", { name: "Confirmar" })).not.toBeDisabled();
  });

  it("024-C17: confirming a valid brief goes read-only and offers writing the novel", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/brief/confirm`]: () => json(200, emptyBrief({ status: "confirmed" })),
    });
    const router = renderEntrevista();
    await user.click(await screen.findByRole("button", { name: "Confirmar" }));

    expect(await screen.findByRole("button", { name: "Escribir la novela" })).toBeInTheDocument();
    expect(screen.queryByRole("form", { name: "Entrevista" })).not.toBeInTheDocument();
    expect(router.state.location.pathname).toBe(`/novelas/${NOVEL}/entrevista`);
  });

  it("024-C18: a rejected confirmation stays editable and shows the problems", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`POST ${BASE}/brief/confirm`]: () =>
        json(422, {
          detail: [{ loc: ["body", "brief", "missing_fields", "age"], msg: "falta: age", type: "missing_field" }],
        }),
    });
    renderEntrevista();
    await user.click(await screen.findByRole("button", { name: "Confirmar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/falta: age/i);
    expect(screen.getByRole("form", { name: "Entrevista" })).toBeInTheDocument();
  });

  it("024-C19: entering a novel with an already-confirmed brief is read-only from the start", async () => {
    fakeApi({
      [`GET ${BASE}/brief`]: () => json(200, emptyBrief({ status: "confirmed" })),
      [`GET ${BASE}/interview/messages`]: () => json(200, [{ author: "user", text: "hola" }]),
    });
    renderEntrevista();

    expect(await screen.findByText("hola")).toBeInTheDocument();
    expect(screen.queryByRole("form", { name: "Entrevista" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Texto libre")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Término")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Escribir la novela" })).toBeInTheDocument();
  });

  it("024-C21: writing the novel launches the generation and navigates to its progress", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET ${BASE}/brief`]: () => json(200, emptyBrief({ status: "confirmed" })),
      [`POST ${BASE}/runs`]: () => json(202, { run_id: 9, position: 1 }),
    });
    const router = renderEntrevista();
    const button = await screen.findByRole("button", { name: "Escribir la novela" });
    await user.click(button);

    expect(button).toBeDisabled();
    await vi.waitFor(() => expect(router.state.location.pathname).toBe(`/novelas/${NOVEL}/progreso`));
  });

  it("024-C21b: writing the novela rejected shows the reason and a link to its progress", async () => {
    const user = userEvent.setup();
    fakeApi({
      [`GET ${BASE}/brief`]: () => json(200, emptyBrief({ status: "confirmed" })),
      [`POST ${BASE}/runs`]: () => new Response(JSON.stringify({ detail: "ya hay una ejecución en curso" }), { status: 409, headers: { "Content-Type": "application/json" } }),
    });
    renderEntrevista();
    await user.click(await screen.findByRole("button", { name: "Escribir la novela" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/ya hay una ejecución en curso/i);
    expect(screen.getByRole("link", { name: /progreso/i })).toHaveAttribute("href", `/novelas/${NOVEL}/progreso`);
  });
});
