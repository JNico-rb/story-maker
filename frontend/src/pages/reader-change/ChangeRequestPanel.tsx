import { useEffect, useState } from "react";

import {
  confirmChange,
  errorMessage,
  requestChange,
  type ChangeRequestCreated,
  type Proposal,
  type Selection,
} from "../../shared/api";

type FormState = { step: "form"; text: string; submitting: boolean; error?: string };
type ProposalState = {
  step: "proposal";
  text: string;
  created: ChangeRequestCreated;
  confirming: boolean;
  expired: boolean;
  confirmError?: string;
};
type State = FormState | ProposalState;

function ProposalView({ proposal }: { proposal: Proposal }) {
  if ("new_fact" in proposal) return <p>{proposal.new_fact}</p>;
  return (
    <p>
      {proposal.fact}: {proposal.old_value} → {proposal.new_value}
    </p>
  );
}

export function ChangeRequestPanel({
  novelId,
  selection,
  onDiscard,
  onConfirmed,
}: {
  novelId: string;
  selection: Selection;
  onDiscard: () => void;
  onConfirmed: (runId: string) => void;
}) {
  const [state, setState] = useState<State>({ step: "form", text: "", submitting: false });

  // 027-C12: un temporizador basado en `expires_at` solo marca la propuesta como caducada para
  // que la pantalla lo muestre; nunca confirma por su cuenta (027-I2).
  const expiresAt = state.step === "proposal" ? state.created.expires_at : null;
  const expired = state.step === "proposal" && state.expired;
  useEffect(() => {
    if (!expiresAt || expired) return;
    const ms = Math.max(0, new Date(expiresAt).getTime() - Date.now());
    const timer = setTimeout(() => {
      setState((s) => (s.step === "proposal" ? { ...s, expired: true } : s));
    }, ms);
    return () => clearTimeout(timer);
  }, [expiresAt, expired]);

  if (state.step === "proposal") {
    const { created } = state;

    async function handleConfirm() {
      if (state.step !== "proposal" || state.confirming || state.expired) return;
      setState({ ...state, confirming: true, confirmError: undefined });
      const response = await confirmChange(created.id, created.code);
      // Un 409 al confirmar es siempre la propuesta ya caducada en el servidor
      // (specs/backend/014-cambios-del-lector.md, alcance): misma pantalla que 027-C12.
      if (response.status === 409) {
        setState((s) => (s.step === "proposal" ? { ...s, confirming: false, expired: true } : s));
        return;
      }
      if (response.status === 202) {
        const { run_id } = (await response.json()) as { run_id: string };
        onConfirmed(run_id);
        return;
      }
      const message = await errorMessage(response);
      setState((s) => (s.step === "proposal" ? { ...s, confirming: false, confirmError: message } : s));
    }

    return (
      <section aria-label="Propuesta de cambio">
        <ProposalView proposal={created.proposal} />
        {created.affected_chapters.length === 0 ? (
          <p>Ningún capítulo cambiará.</p>
        ) : (
          <ul aria-label="Capítulos afectados">
            {created.affected_chapters.map((chapter) => (
              <li key={chapter}>{chapter}</li>
            ))}
          </ul>
        )}
        {state.expired ? (
          <p role="alert">La propuesta ha caducado: pide el cambio otra vez.</p>
        ) : (
          <button type="button" disabled={state.confirming} onClick={() => void handleConfirm()}>
            Confirmar
          </button>
        )}
        {state.confirmError && <p role="alert">{state.confirmError}</p>}
        <button type="button" disabled={state.confirming} onClick={onDiscard}>
          Descartar
        </button>
      </section>
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (state.step !== "form" || state.text.trim() === "") return;
    setState({ ...state, submitting: true, error: undefined });
    const response = await requestChange(novelId, selection, state.text);
    if (response.status === 201) {
      const created = (await response.json()) as ChangeRequestCreated;
      setState({ step: "proposal", text: state.text, created, confirming: false, expired: false });
      return;
    }
    // Un 409 al pedir el cambio es siempre la versión de la selección ya no vigente
    // (specs/backend/014-cambios-del-lector.md, alcance): mensaje fijo, no el texto del servidor.
    const message =
      response.status === 409
        ? "La versión ha cambiado: hay que volver a seleccionar sobre la lectura vigente."
        : await errorMessage(response);
    setState({ step: "form", text: state.text, submitting: false, error: message });
  }

  return (
    <form aria-label="Petición de cambio" onSubmit={(event) => void handleSubmit(event)}>
      <p>«{selection.quote}»</p>
      <label htmlFor="change-request-text">Petición</label>
      <textarea
        id="change-request-text"
        value={state.text}
        onChange={(event) => setState({ ...state, text: event.target.value })}
      />
      {state.error && <p role="alert">{state.error}</p>}
      <button type="submit" disabled={state.text.trim() === "" || state.submitting}>
        Pedir el cambio
      </button>
    </form>
  );
}
