import { useState } from "react";

import type { Selection } from "../../shared/api";

type FormState = { step: "form"; text: string; submitting: boolean; error?: string };
type State = FormState;

function selectionPreview(selection: Selection): string {
  return selection.kind === "fragment" ? `«${selection.quote}»` : `${selection.label}: ${selection.value}`;
}

export function ChangeRequestPanel({
  selection,
}: {
  novelId: string;
  selection: Selection;
  onDiscard: () => void;
}) {
  const [state] = useState<State>({ step: "form", text: "", submitting: false });

  return (
    <form aria-label="Petición de cambio">
      <p>{selectionPreview(selection)}</p>
      <label htmlFor="change-request-text">Petición</label>
      <textarea id="change-request-text" value={state.text} onChange={() => undefined} />
    </form>
  );
}
