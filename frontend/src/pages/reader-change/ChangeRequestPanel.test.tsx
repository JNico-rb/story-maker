import { render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { clearSession, saveSession } from "../../shared/lib";
import type { Selection } from "../../shared/api";
import { ChangeRequestPanel } from "./ChangeRequestPanel";

const NOVEL = "7";

const FACT_SELECTION: Selection = {
  kind: "fact",
  fact_id: 1,
  label: "Nombre del perro",
  value: "Toby",
};

function renderPanel(onDiscard: () => void = () => undefined) {
  render(<ChangeRequestPanel novelId={NOVEL} selection={FACT_SELECTION} onDiscard={onDiscard} />);
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
  it("027-C01: selecting a fragment or a fact opens the request form", () => {
    renderPanel();

    const form = screen.getByRole("form", { name: "Petición de cambio" });
    expect(screen.getByText(/Nombre del perro/)).toBeInTheDocument();
    expect(screen.getByText(/Toby/)).toBeInTheDocument();
    expect(within(form).getByRole("textbox", { name: "Petición" })).toHaveValue("");
  });
});
