import { useState } from "react";

import { requestChange, type ChangeRequestCreated, type Proposal, type Selection } from "../../shared/api";

type FormState = { step: "form"; text: string; submitting: boolean; error?: string };
type ProposalState = {
  step: "proposal";
  text: string;
  created: ChangeRequestCreated;
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
}: {
  novelId: string;
  selection: Selection;
  onDiscard: () => void;
}) {
  const [state, setState] = useState<State>({ step: "form", text: "", submitting: false });

  if (state.step === "proposal") {
    const { created } = state;
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
        <button type="button">Confirmar</button>
        <button type="button">Descartar</button>
      </section>
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (state.step !== "form" || state.text.trim() === "") return;
    setState({ ...state, submitting: true, error: undefined });
    const response = await requestChange(novelId, selection, state.text);
    const created = (await response.json()) as ChangeRequestCreated;
    setState({ step: "proposal", text: state.text, created });
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
      <button type="submit" disabled={state.text.trim() === "" || state.submitting}>
        Pedir el cambio
      </button>
    </form>
  );
}
