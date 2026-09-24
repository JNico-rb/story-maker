import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, saveSession } from "../../shared/lib";
import type { Selection } from "../../shared/api";
import { ChangeRequestPanel } from "./ChangeRequestPanel";

const NOVEL = "7";

const FRAGMENT_SELECTION: Selection = {
  type: "fragment",
  version: 1,
  chapter: 3,
  quote: "Toby corría por la playa.",
};

function renderPanel(onDiscard: () => void = () => undefined, onConfirmed: (runId: string) => void = () => undefined) {
  render(
    <ChangeRequestPanel
      novelId={NOVEL}
      selection={FRAGMENT_SELECTION}
      onDiscard={onDiscard}
      onConfirmed={onConfirmed}
    />,
  );
}

// API simulada en el límite del cliente (frontend/AGENTS.md), mismo patrón que src/app/reading.test.tsx.
function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fakeApi(reply: () => Response): { calls: Array<{ url: string; body: unknown }> } {
  const calls: Array<{ url: string; body: unknown }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(input), body: init?.body ? JSON.parse(String(init.body)) : undefined });
      return reply();
    }),
  );
  return { calls };
}

async function sendRequest(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByRole("textbox", { name: "Petición" }), "el perro se llama Nala");
  await user.click(screen.getByRole("button", { name: "Pedir el cambio" }));
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
  it("027-C02: the empty request cannot be sent, typing enables it", async () => {
    const user = userEvent.setup();
    renderPanel();

    const submit = screen.getByRole("button", { name: "Pedir el cambio" });
    expect(submit).toBeDisabled();

    await user.type(screen.getByRole("textbox", { name: "Petición" }), "el perro se llama Nala");

    expect(submit).toBeEnabled();
  });

  it("027-C03: sending the request shows the proposal, the affected chapters and the expiry", async () => {
    const user = userEvent.setup();
    const { calls } = fakeApi(() =>
      json(201, {
        id: "req-1",
        proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
        affected_chapters: [2, 5, 7],
        code: "SECRETO-123",
        expires_at: "2026-09-25T12:00:00Z",
      }),
    );
    renderPanel();

    await sendRequest(user);

    expect(await screen.findByText(/Nombre del perro/)).toBeInTheDocument();
    expect(screen.getByText(/Toby/)).toBeInTheDocument();
    expect(screen.getByText(/Nala/)).toBeInTheDocument();
    const affected = screen.getByRole("list", { name: "Capítulos afectados" });
    expect(within(affected).getAllByRole("listitem").map((li) => li.textContent)).toEqual(["2", "5", "7"]);
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Descartar" })).toBeInTheDocument();
    expect(screen.queryByText("SECRETO-123")).not.toBeInTheDocument();

    expect(calls).toEqual([
      {
        url: `/api/novels/${NOVEL}/change-requests`,
        body: { selection: FRAGMENT_SELECTION, request: "el perro se llama Nala" },
      },
    ]);
  });

  it("027-C04: a proposal with no affected chapters shows the same, still with both actions", async () => {
    const user = userEvent.setup();
    fakeApi(() =>
      json(201, {
        id: "req-1",
        proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
        affected_chapters: [],
        code: "SECRETO-123",
        expires_at: "2026-09-25T12:00:00Z",
      }),
    );
    renderPanel();

    await sendRequest(user);

    expect(await screen.findByText(/Nombre del perro/)).toBeInTheDocument();
    expect(screen.getByText(/ningún capítulo cambiará/i)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Capítulos afectados" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Confirmar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Descartar" })).toBeInTheDocument();
  });

  it("027-C05: a request rejected by the policy or the proposal keeps the form with the reason", async () => {
    const user = userEvent.setup();
    fakeApi(() => json(422, { detail: "la petición está prohibida" }));
    renderPanel();

    await sendRequest(user);

    expect(await screen.findByText("la petición está prohibida")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Petición" })).toHaveValue("el perro se llama Nala");
    expect(screen.queryByRole("section", { name: "Propuesta de cambio" })).not.toBeInTheDocument();
  });

  it("027-C06: a request over a selection that is no longer valid asks to select again", async () => {
    const user = userEvent.setup();
    fakeApi(() => json(409, { detail: "stale_base" }));
    renderPanel();

    await sendRequest(user);

    expect(await screen.findByText(/la versión ha cambiado.*volver a seleccionar/i)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Petición" })).toHaveValue("el perro se llama Nala");
    expect(screen.queryByRole("section", { name: "Propuesta de cambio" })).not.toBeInTheDocument();
  });

  it("027-C07: a server failure while requesting the change offers a retry without losing what was written", async () => {
    const user = userEvent.setup();
    let attempt = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        attempt += 1;
        if (attempt === 1) return new Response(null, { status: 500 });
        return json(201, {
          id: "req-1",
          proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
          affected_chapters: [2],
          code: "SECRETO-123",
          expires_at: "2026-09-25T12:00:00Z",
        });
      }),
    );
    renderPanel();

    await sendRequest(user);

    expect(await screen.findByText(/no se pudo (enviar|completar)/i)).toBeInTheDocument();
    const textbox = screen.getByRole("textbox", { name: "Petición" });
    expect(textbox).toHaveValue("el perro se llama Nala");

    await user.click(screen.getByRole("button", { name: "Pedir el cambio" }));

    expect(await screen.findByText(/Nombre del perro/)).toBeInTheDocument();
  });

  it("027-C10: discarding the proposal calls onDiscard without confirming anything", async () => {
    const user = userEvent.setup();
    const onDiscard = vi.fn();
    const { calls } = fakeApi(() =>
      json(201, {
        id: "req-1",
        proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
        affected_chapters: [2, 5, 7],
        code: "SECRETO-123",
        expires_at: "2026-09-25T12:00:00Z",
      }),
    );
    renderPanel(onDiscard);

    await sendRequest(user);
    await user.click(screen.getByRole("button", { name: "Descartar" }));

    expect(onDiscard).toHaveBeenCalledTimes(1);
    expect(calls).toHaveLength(1);
  });

  it("027-C08: sending disables the action while it is in progress", async () => {
    const user = userEvent.setup();
    let resolveResponse: (response: Response) => void = () => undefined;
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>((resolve) => (resolveResponse = resolve))),
    );
    renderPanel();

    await user.type(screen.getByRole("textbox", { name: "Petición" }), "el perro se llama Nala");
    const submit = screen.getByRole("button", { name: "Pedir el cambio" });
    await user.click(submit);

    expect(submit).toBeDisabled();

    resolveResponse(
      json(201, {
        id: "req-1",
        proposal: { fact: "Nombre del perro", old_value: "Toby", new_value: "Nala" },
        affected_chapters: [2],
        code: "SECRETO-123",
        expires_at: "2026-09-25T12:00:00Z",
      }),
    );

    expect(await screen.findByText(/Nombre del perro/)).toBeInTheDocument();
  });
});
