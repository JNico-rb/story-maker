import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HomePage } from "./HomePage";

describe("HomePage", () => {
  it("shows the Qaracter logo and the product name", () => {
    render(<HomePage />);

    expect(screen.getByRole("img", { name: "Qaracter" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: "Qaracter · Story Maker" }),
    ).toBeInTheDocument();
  });
});
