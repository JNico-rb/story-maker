import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { apiFetch, errorMessage } from "../../shared/api";

// El intervalo fijo del sondeo (025-I1); el mismo valor que usan las pruebas.
const INTERVAL_MS = 5000;

// Modelo del backend (011-produccion-de-capitulos, 012-gate-de-publicacion); `schema.d.ts` no lo
// tiene todavía (025, alcance), así que se declara aquí igual, sin inventar campos.
type RunStatus = "queued" | "running" | "interrupted" | "published" | "failed";

type Progress = {
  run_id: number;
  type: string;
  status: RunStatus;
  phase: string | null;
  chapter: number | null;
  cost_usd: number;
  position: number | null;
  reason: string | null;
  reason_detail: string | null;
};

type Attempt = { evaluable: boolean; chapter: number | null; gate_cycle: number | null; number: number; outcome: string };
type UnresolvedDefect = { chapter: number | null; attempt: number | null } & Record<string, unknown>;

type Report = {
  run_id: number;
  status: string;
  reason: string | null;
  reason_detail: string | null;
  resumes: number;
  cost_usd: number;
  attempts: Attempt[];
  unresolved: UnresolvedDefect[];
};

type Load<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "error" };

function NoRun({ novelId }: { novelId: string }) {
  return (
    <>
      <p>Esta novela no tiene ninguna ejecución todavía.</p>
      <Link to={`/novelas/${novelId}/entrevista`} className="underline text-primary">
        Ir a la entrevista
      </Link>
    </>
  );
}

function ReportPanel({ report, onRetry }: { report: Load<Report>; onRetry: () => void }) {
  if (report.status === "loading") return <p role="status">Cargando el informe…</p>;
  if (report.status === "error") {
    return (
      <div>
        <p role="alert">No se pudo cargar el informe.</p>
        <button type="button" onClick={onRetry} className="underline">
          Reintentar
        </button>
      </div>
    );
  }
  const data = report.data;
  return (
    <section aria-label="Informe" className="rounded-lg border border-secondary/10 bg-white/60 p-5">
      <p>
        Motivo: {data.reason}
        {data.reason_detail ? ` (${data.reason_detail})` : ""}
      </p>
      <p>
        Reanudaciones: {data.resumes} · Coste: {data.cost_usd} USD
      </p>
      {data.unresolved.length > 0 && (
        <ul aria-label="Defectos sin resolver" className="mt-3 list-disc pl-5 text-sm">
          {data.unresolved.map((defect, index) => {
            const rest = Object.entries(defect).filter(([key]) => key !== "chapter" && key !== "attempt");
            return (
              <li key={index}>
                Capítulo {defect.chapter} · intento {defect.attempt}
                {rest.length > 0 && ": " + rest.map(([key, value]) => `${key}: ${String(value)}`).join(" · ")}
              </li>
            );
          })}
        </ul>
      )}
      {data.attempts.length > 0 && (
        <ul aria-label="Intentos" className="mt-3 list-disc pl-5 text-sm">
          {data.attempts.map((attempt, index) => (
            <li key={index}>
              Capítulo {attempt.chapter} · intento {attempt.number}: {attempt.outcome}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

type PollState = { kind: "pending" } | { kind: "ok"; data: Progress; pollError?: string } | { kind: "not_found" };

function RunProgress({ runId, novelId }: { runId: number; novelId: string }) {
  const navigate = useNavigate();
  const [state, setState] = useState<PollState>({ kind: "pending" });
  const [pollNonce, setPollNonce] = useState(0);
  const [resuming, setResuming] = useState(false);
  const [resumeError, setResumeError] = useState<string>();
  const [reportAttempt, setReportAttempt] = useState(0);
  const [report, setReport] = useState<Load<Report>>({ status: "loading" });

  const status = state.kind === "ok" ? state.data.status : undefined;
  const terminal = status === "published" || status === "failed";
  const notFound = state.kind === "not_found";

  // Sondeo periódico (025-C01 a 025-C03, 025-I1): mientras no sea un estado terminal ni un 404;
  // `pollNonce` fuerza un sondeo inmediato tras reanudar, sin esperar al intervalo (025-C08).
  useEffect(() => {
    if (terminal || notFound) return;
    let cancelled = false;
    async function poll() {
      const response = await apiFetch(`/api/runs/${runId}`);
      if (cancelled) return;
      if (response.status === 404) {
        setState({ kind: "not_found" });
        return;
      }
      if (!response.ok) {
        setState((current) => (current.kind === "ok" ? { ...current, pollError: "no se pudo actualizar el progreso" } : current));
        return;
      }
      const data = (await response.json()) as Progress;
      setState({ kind: "ok", data });
    }
    void poll();
    const id = setInterval(() => void poll(), INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [runId, terminal, notFound, pollNonce]);

  // Publicada, navega a su lectura (025-C04); nunca vuelve a sondear (`terminal`, arriba).
  useEffect(() => {
    if (status === "published") void navigate(`/novelas/${novelId}/lectura`);
  }, [status, novelId, navigate]);

  // Informe (025-C05, 025-C06): solo al fallar.
  useEffect(() => {
    if (status !== "failed") return;
    let current = true;
    void apiFetch(`/api/runs/${runId}/report`)
      .then((response) => {
        if (!response.ok) throw new Error("fallo al cargar el informe");
        return response.json() as Promise<Report>;
      })
      .then((data) => {
        if (current) setReport({ status: "ready", data });
      })
      .catch(() => {
        if (current) setReport({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, [status, runId, reportAttempt]);

  async function handleResume() {
    setResuming(true);
    setResumeError(undefined);
    const response = await apiFetch(`/api/runs/${runId}/resume`, { method: "POST" });
    if (response.status === 202) {
      setResuming(false);
      setPollNonce((n) => n + 1);
      return;
    }
    setResuming(false);
    setResumeError(await errorMessage(response));
  }

  if (notFound) return <p role="alert">No se encontró esa ejecución.</p>;
  if (state.kind === "pending") return <p role="status">Cargando el progreso…</p>;

  const data = state.data;
  return (
    <>
      {data.status === "queued" && <p>En cola: posición {data.position}</p>}
      {data.status === "running" && (
        <p>
          Fase: {data.phase}
          {data.chapter !== null ? ` · Capítulo ${data.chapter}` : ""} · Coste: {data.cost_usd} USD
        </p>
      )}
      {data.status === "interrupted" && (
        <div>
          <p>
            Interrumpida: {data.reason}
            {data.reason_detail ? ` — ${data.reason_detail}` : ""}
          </p>
          <button
            type="button"
            disabled={resuming}
            onClick={() => void handleResume()}
            className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
          >
            Reanudar
          </button>
          {resumeError && (
            <p role="alert" className="mt-2 text-sm">
              {resumeError}
            </p>
          )}
        </div>
      )}
      {data.status === "failed" && <ReportPanel report={report} onRetry={() => setReportAttempt((n) => n + 1)} />}
      {state.pollError && (
        <p role="alert" className="mt-3 text-sm">
          {state.pollError}
        </p>
      )}
    </>
  );
}

export function ProgresoPage() {
  const { novelId = "" } = useParams();
  const [load, setLoad] = useState<Load<{ latest_run_id: number | null }>>({ status: "loading" });

  useEffect(() => {
    let current = true;
    void apiFetch(`/api/novels/${novelId}`)
      .then((response) => {
        if (!response.ok) throw new Error("fallo al cargar la novela");
        return response.json() as Promise<{ latest_run_id: number | null }>;
      })
      .then((data) => {
        if (current) setLoad({ status: "ready", data });
      })
      .catch(() => {
        if (current) setLoad({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, [novelId]);

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Progreso</h2>
      {load.status === "loading" && <p role="status">Cargando…</p>}
      {load.status === "error" && <p role="alert">No se pudo cargar esta novela.</p>}
      {load.status === "ready" && load.data.latest_run_id === null && <NoRun novelId={novelId} />}
      {load.status === "ready" && load.data.latest_run_id !== null && (
        <RunProgress runId={load.data.latest_run_id} novelId={novelId} />
      )}
    </main>
  );
}
