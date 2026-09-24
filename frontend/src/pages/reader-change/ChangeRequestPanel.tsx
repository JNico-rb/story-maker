import { useState } from "react";

import type { Selection } from "../../shared/api";

type FormState = { step: "form"; text: string; submitting: boolean; error?: string };
type State = FormState;

export function ChangeRequestPanel({
  selection,
}: {
  novelId: string;
  selection: Selection;
  onDiscard: () => void;
}) {
  const [state, setState] = useState<State>({ step: "form", text: "", submitting: false });

  return (
    <form aria-label="Petición de cambio">
      <p>«{selection.quote}»</p>
      <label htmlFor="change-request-text">Petición</label>
      <textarea
        id="change-request-text"
        value={state.text}
        onChange={(event) => setState({ ...state, text: event.target.value })}
      />
      <button type="submit" disabled={state.text.trim() === ""}>
        Pedir el cambio
      </button>
    </form>
  );
}
