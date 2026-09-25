import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, saveSession } from "../shared/lib";
import { buildRoutes } from "./router";

// API simulada en el límite del cliente (025-I4), mismo patrón que src/app/entrevista.test.tsx.
// El intervalo fijo del sondeo (025-I1), igual que el que usa `ProgresoPage`.
const INTERVAL_MS = 5000;

type Reply = () => Response | Promise<Response>;

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const NOVEL = 30;
const RUN = 77;

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

function novelWithRun(latestRunId: number | null) {
  return {
    id: NOVEL,
    title: "La casa del faro",
    recipient_name: "Ana",
    status: "in_progress",
    current_version: null,
    latest_run_id: latestRunId,
    created_at: "2026-09-20T10:00:00Z",
  };
}

function progress(overrides: Record<string, unknown> = {}) {
  return {
    run_id: RUN,
    type: "generation",
    status: "running",
    phase: "writing",
    chapter: 1,
    cost_usd: 0.5,
    position: null,
    reason: null,
    reason_detail: null,
    ...overrides,
  };
}

function renderProgreso() {
  const router = createMemoryRouter(buildRoutes(), {
    initialEntries: [`/novelas/${NOVEL}/progreso`],
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
  vi.useRealTimers();
});

describe("025 progreso: C00 resolver la ejecución", () => {
  it("025-C00: without any execution, shows so and links to the interview, without polling", async () => {
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(null)),
    });
    renderProgreso();

    expect(await screen.findByText(/no tiene ninguna ejecución/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /entrevista/i })).toHaveAttribute(
      "href",
      `/novelas/${NOVEL}/entrevista`,
    );
  });
});

describe("025 progreso: sondeo", () => {
  it("025-C01: reflects phase and chapter as the execution advances, polling at a fixed interval", async () => {
    vi.useFakeTimers();
    let call = 0;
    const responses = [
      progress({ phase: "planning", chapter: null }),
      progress({ phase: "writing", chapter: 1 }),
      progress({ phase: "writing", chapter: 4 }),
      progress({ phase: "gate", chapter: null }),
    ];
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => {
        const body = responses[call] ?? responses.at(-1);
        call += 1;
        return json(200, body);
      },
    });
    renderProgreso();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByText(/planning/)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(screen.getByText(/writing/)).toBeInTheDocument();
    expect(screen.getByText(/capítulo 1/i)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(screen.getByText(/capítulo 4/i)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(screen.getByText(/gate/)).toBeInTheDocument();
    expect(call).toBe(4);
  });

  it("025-C02: queued shows only the position, no phase or chapter", async () => {
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () =>
        json(200, progress({ status: "queued", phase: null, chapter: null, position: 2 })),
    });
    renderProgreso();

    expect(await screen.findByText(/en cola/i)).toBeInTheDocument();
    expect(screen.getByText(/posición 2/i)).toBeInTheDocument();
    expect(screen.queryByText(/writing|planning|gate/)).not.toBeInTheDocument();
  });

  it("025-C03: a poll failure shows so without stopping, recovering on the next one", async () => {
    vi.useFakeTimers();
    let call = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => {
        call += 1;
        if (call === 2) return new Response(null, { status: 500 });
        return json(200, progress());
      },
    });
    renderProgreso();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByText(/writing/)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/no se pudo actualizar/i);
    expect(screen.getByText(/writing/)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

describe("025 progreso: fin de la ejecución", () => {
  it("025-C04: published stops polling and navigates to the reading", async () => {
    vi.useFakeTimers();
    let calls = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => {
        calls += 1;
        return json(200, progress({ status: "published" }));
      },
    });
    const router = renderProgreso();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    await vi.waitFor(() => expect(router.state.location.pathname).toBe(`/novelas/${NOVEL}/lectura`));

    const callsAfterStop = calls;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS * 3);
    });
    expect(calls).toBe(callsAfterStop);
  });

  it("025-C05: failed stops polling and shows the report", async () => {
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () =>
        json(200, progress({ status: "failed", reason: "gate_exhausted", reason_detail: "capítulo 3" })),
      [`GET /api/runs/${RUN}/report`]: () =>
        json(200, {
          run_id: RUN,
          status: "failed",
          reason: "gate_exhausted",
          reason_detail: "capítulo 3",
          resumes: 1,
          cost_usd: 1.2,
          attempts: [{ evaluable: true, chapter: 3, gate_cycle: 1, number: 2, outcome: "rejected" }],
          validators: [],
          unresolved: [{ chapter: 3, attempt: 2, validator: "lean", passed: false }],
          policy_decisions: [],
        }),
    });
    renderProgreso();

    const report = await screen.findByRole("region", { name: "Informe" });
    expect(within(report).getByText(/gate_exhausted/)).toBeInTheDocument();
    expect(within(report).getByText(/capítulo 3/)).toBeInTheDocument();
    expect(within(report).getByText(/lean/)).toBeInTheDocument();
  });

  it("025-C06: a report failure shows so and offers a retry", async () => {
    let attempt = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => json(200, progress({ status: "failed", reason: "gate_exhausted" })),
      [`GET /api/runs/${RUN}/report`]: () => {
        attempt += 1;
        if (attempt === 1) return new Response(null, { status: 500 });
        return json(200, {
          run_id: RUN,
          status: "failed",
          reason: "gate_exhausted",
          reason_detail: null,
          resumes: 0,
          cost_usd: 0,
          attempts: [],
          validators: [],
          unresolved: [],
          policy_decisions: [],
        });
      },
    });
    renderProgreso();

    expect(await screen.findByText(/no se pudo cargar el informe/i)).toBeInTheDocument();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /reintentar/i }));
    });
    expect(await screen.findByRole("region", { name: "Informe" })).toBeInTheDocument();
  });
});

describe("025 progreso: reanudar", () => {
  it("025-C07: interrupted offers resuming with its reason, keeps polling", async () => {
    vi.useFakeTimers();
    let calls = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => {
        calls += 1;
        return json(
          200,
          progress({ status: "interrupted", reason: "provider_error", reason_detail: "timeout del proveedor" }),
        );
      },
    });
    renderProgreso();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByText(/provider_error/)).toBeInTheDocument();
    expect(screen.getByText(/timeout del proveedor/)).toBeInTheDocument();
    const before = calls;

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS);
    });
    expect(calls).toBeGreaterThan(before);
    expect(screen.getByRole("button", { name: "Reanudar" })).toBeInTheDocument();
  });

  it("025-C08: resuming shows the progress again, now with the queue position", async () => {
    let resumed = false;
    let resolveResume!: (response: Response) => void;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () =>
        json(200, resumed ? progress({ status: "queued", phase: null, chapter: null, position: 1 }) : progress({ status: "interrupted", reason: "provider_error" })),
      [`POST /api/runs/${RUN}/resume`]: () => new Promise<Response>((resolve) => (resolveResume = resolve)),
    });
    renderProgreso();

    const button = await screen.findByRole("button", { name: "Reanudar" });
    fireEvent.click(button);
    await vi.waitFor(() => expect(button).toBeDisabled());

    resumed = true;
    resolveResume(json(202, { run_id: RUN, position: 1 }));

    await vi.waitFor(() => expect(screen.getByText(/posición 1/i)).toBeInTheDocument());
  });

  it("025-C09: a rejected resume shows the reason and keeps what it already had", async () => {
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () =>
        json(200, progress({ status: "interrupted", reason: "provider_error", reason_detail: "detalle" })),
      [`POST /api/runs/${RUN}/resume`]: () => new Response(null, { status: 409 }),
    });
    renderProgreso();

    const button = await screen.findByRole("button", { name: "Reanudar" });
    await act(async () => {
      fireEvent.click(button);
    });

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reanudar" })).not.toBeDisabled();
    expect(screen.getByText(/provider_error/)).toBeInTheDocument();
  });
});

describe("025 progreso: acceso", () => {
  it("025-C10: someone else's or a non-existent execution shows so, without polling again", async () => {
    vi.useFakeTimers();
    let calls = 0;
    fakeApi({
      [`GET /api/novels/${NOVEL}`]: () => json(200, novelWithRun(RUN)),
      [`GET /api/runs/${RUN}`]: () => {
        calls += 1;
        return new Response(null, { status: 404 });
      },
    });
    renderProgreso();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByText(/no se encontró esa ejecución/i)).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(INTERVAL_MS * 2);
    });
    expect(calls).toBe(1);
  });
});
