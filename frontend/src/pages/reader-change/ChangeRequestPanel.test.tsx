import { render, screen } from "@testing-library/react";
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

function renderPanel(onDiscard: () => void = () => undefined) {
  render(<ChangeRequestPanel novelId={NOVEL} selection={FRAGMENT_SELECTION} onDiscard={onDiscard} />);
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
});
